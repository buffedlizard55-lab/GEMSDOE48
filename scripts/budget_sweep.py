#!/usr/bin/env python3
"""Find the emission budget at which marginal proxy credit meets the live bar.

The published metric accepts an extra unit of emitted mass iff the credit it
realises exceeds alpha*DTI.  Expressed in proxy credit units the bar is

        bar_proxy = alpha * DTI_live / transfer,      transfer = live credit / proxy credit

and the transfer bracket measured on group B is [0.12, 0.80] with the aggregate
(mean credit per dot) ratio at 0.90.  We sweep the budget of the fused,
spatially balanced emission and report the marginal proxy credit of each
increment, so the chosen budget is the largest one whose marginal increment
still clears the bar under the optimistic end of the bracket.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.evidence import (  # noqa: E402
    combine_yager,
    discounted_binary_mass,
    kernel_support,
    pignistic,
)
from gems48.emission import poisson_sample  # noqa: E402
from gems48.metric import ALPHA, dti_result as dti  # noqa: E402

R_DOTTED = 0.90
R_TIP = 0.90 * (0.11987588720357811 / 0.13446190223260976)
LIVE_DTI = 0.2778
TRANSFER_LOW, TRANSFER_HIGH = 0.756, 1.0

DOTTED = ROOT / "data/raw/dotted.tif"
TIP = ROOT / "data/raw/tip.tif"
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
SGMC = ROOT / "data/raw/external/derived_sgmc_faults_100m_u8.tif"
NB = 4

BUDGETS = [28000, 32000, 37654, 41000, 44000, 47905, 52000, 58000, 66000, 76000, 88000, 100000]


def rd(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)




def blocks(shape, n=NB):
    h, w = shape
    return [(slice(i * h // n, (i + 1) * h // n), slice(j * w // n, (j + 1) * w // n))
            for i in range(n) for j in range(n)]


def main() -> None:
    dotted = rd(DOTTED) > 0
    tip = rd(TIP) > 0
    labels = rd(LABELS) > 0
    sgmc = rd(SGMC) > 0
    footprint = np.isfinite(rd(TEMPLATE))
    d_cat = distance_transform_edt(~labels)
    truth = sgmc & footprint & (d_cat >= 3.0)

    sup_d = kernel_support(dotted.astype(np.float64))
    sup_t = kernel_support(tip.astype(np.float64))
    a = discounted_binary_mass(sup_d, R_DOTTED)
    b = discounted_binary_mass(sup_t, R_TIP)
    bel, dis, u, k = combine_yager(a, b)
    betp = pignistic(bel, dis)
    allowed = footprint & ((sup_d > 0) | (sup_t > 0))

    bar_low = ALPHA * LIVE_DTI / TRANSFER_HIGH   # optimistic (transfer 1.0)
    bar_high = ALPHA * LIVE_DTI / TRANSFER_LOW   # conservative (transfer 0.756)

    blks = blocks(truth.shape)
    # monotone nested samples: build once per spacing, take prefixes by re-running
    results = {}
    for spacing in (2.5,):
        rows = {}
        prev = None
        for n in BUDGETS:
            arr = poisson_sample(betp, spacing, n, allowed).astype(np.float64)
            r = dti(arr, truth)
            per = [dti(arr[ys, xs], truth[ys, xs]).dti for ys, xs in blks if truth[ys, xs].sum() >= 50]
            row = {"budget": n, "dots": float(arr.sum()), **r.as_dict(),
                   "block_dti_mean": float(np.mean(per)), "blocks": len(per)}
            if prev is not None:
                dn = row["dots"] - prev["dots"]
                dt = row["tp_w"] - prev["tp_w"]
                row["marginal_proxy_credit_per_dot"] = dt / dn if dn else None
                row["marginal_clears_optimistic_bar"] = (dt / dn) > bar_low if dn else None
                row["marginal_clears_conservative_bar"] = (dt / dn) > bar_high if dn else None
            rows[n] = row
            prev = row
        results[f"spacing_{spacing}"] = rows

    parent = dti(dotted.astype(np.float64), truth)
    out = {
        "schema": "GEMSDOE48-budget-sweep-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "bars": {"live_bar_live_units": ALPHA * LIVE_DTI,
                 "proxy_units_optimistic_transfer_1.0": bar_low,
                 "proxy_units_conservative_transfer_0.756": bar_high},
        "parent_reference": {"dti": parent.dti, "tp_w": parent.tp, "dots": float(dotted.sum())},
        "sweeps": results,
    }
    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "h49-budget-sweep.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out["bars"], indent=2))
    for n, r in results["spacing_2.5"].items():
        m = r.get("marginal_proxy_credit_per_dot")
        print(f"N={r['dots']:8.0f} dti={r['dti']:.6f} blk={r['block_dti_mean']:.6f} tp={r['tp_w']:8.1f} "
              f"marg={'-' if m is None else format(m, '.5f')} "
              f"opt={r.get('marginal_clears_optimistic_bar')} cons={r.get('marginal_clears_conservative_bar')}")


if __name__ == "__main__":
    main()
