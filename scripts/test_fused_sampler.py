#!/usr/bin/env python3
"""Build a NEW emission from the fused evidence, not by copying a parent.

The plain "top-N by belief" emission fails (it clusters) because the published
metric rewards *coverage of distinct structures*, not the highest-scoring cells:
two dots 1 cell apart on the same structure compete for the same truth pixels.
The historical live record shows the winning emissions all enforce a minimum
spacing (Poisson-disk thinning at d = 2.8 px beat d = 1.5 px live).

So the candidate emitted here is a *spatially balanced* greedy sample of the
Dempster-Shafer fused field: walk the cells in descending pignistic order and
accept a cell only if no already-accepted cell lies within the tuned spacing.
That is a maximal-Poisson-disk sample of the fused belief, which is a new
geometry rather than a copy of either parent, and it is directly comparable to
the parents on the blocked proxy at matched mass.
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
from gems48.metric import ALPHA, dti  # noqa: E402

R_DOTTED = 0.90
R_TIP = 0.90 * (0.11987588720357811 / 0.13446190223260976)

DOTTED = ROOT / "data/raw/dotted.tif"
TIP = ROOT / "data/raw/tip.tif"
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
SGMC = ROOT / "data/raw/external/derived_sgmc_faults_100m_u8.tif"
NB = 4


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

    blks = blocks(truth.shape)
    cands = {
        "dotted_parent": dotted.astype(np.float64),
        "tip_parent": tip.astype(np.float64),
        "union_binary": (dotted | tip).astype(np.float64),
    }
    for spacing in (2.0, 2.5, 2.8, 3.2, 3.6):
        cands[f"betp_poisson_s{spacing}_n37654"] = poisson_sample(betp, spacing, 37654, allowed).astype(np.float64)
    for spacing in (2.5, 2.8):
        cands[f"betp_poisson_s{spacing}_n47905"] = poisson_sample(betp, spacing, 47905, allowed).astype(np.float64)
        cands[f"bel_poisson_s{spacing}_n37654"] = poisson_sample(bel, spacing, 37654, allowed).astype(np.float64)

    rows = {}
    for name, arr in cands.items():
        r = dti(arr, truth)
        per = [dti(arr[ys, xs], truth[ys, xs]).dti for ys, xs in blks if truth[ys, xs].sum() >= 50]
        rows[name] = {**r.as_dict(), "block_dti_mean": float(np.mean(per)), "blocks": len(per),
                      "dots": float((arr > 0).sum())}
    base = rows["dotted_parent"]["dti"]
    for v in rows.values():
        v["delta_vs_dotted_parent"] = v["dti"] - base

    out = {
        "schema": "GEMSDOE48-fused-sampler-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "method": "greedy maximal Poisson-disk sample of the fused pignistic field (or Yager belief), descending score, minimum separation = spacing, budget = N",
        "candidates": rows,
        "live_bar": ALPHA * 0.2778,
    }
    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "h49-fused-sampler.json").write_text(json.dumps(out, indent=2) + "\n")
    for k, v in sorted(rows.items(), key=lambda kv: -kv[1]["dti"]):
        print(f"{k:34s} dots={v['dots']:8.0f} dti={v['dti']:.6f} d={v['delta_vs_dotted_parent']:+.6f} "
              f"blk={v['block_dti_mean']:.6f} tp={v['tp_w']:.0f}")


if __name__ == "__main__":
    main()
