#!/usr/bin/env python3
"""Calibrate the proxy instrument against the two live decisions whose outcome is known.

The emission lineage is exactly nested (verified by set comparison):

    d28 (44,090 dots, live 0.2600)
      \\- A = 3,891 dots removed  -> h27_4 (40,199 dots, live 0.2708)   [+0.0108 live]
        \\- B = 2,545 dots removed -> h33-2-b2 (37,654 dots, live 0.2778) [+0.0049 live]

Both A and B were *removals that raised the live score*, so their true live
credit per dot is known to sit below the acceptance bar.  A lives entirely
within 100 m of the public catalogue; B is the "flank B = 2" ring.  If the SGMC
off-catalogue proxy also ranks them below the bar -- and in the same order --
the instrument is calibrated and can be trusted for the tip-only decision, for
which no live outcome exists.
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
from gems48.metric import ALPHA, dti  # noqa: E402

R_DOTTED = 0.90
R_TIP = 0.90 * (0.11987588720357811 / 0.13446190223260976)
LIVE_DTI = 0.2778
LIVE_CREDIT_PER_DOT = 0.13446190223260976

DOTTED = ROOT / "data/raw/dotted.tif"
TIP = ROOT / "data/raw/tip.tif"
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
SGMC = ROOT / "data/raw/external/derived_sgmc_faults_100m_u8.tif"
H27 = ROOT / "data/raw/calib/h27_4.tif"
D28 = ROOT / "data/raw/calib/d28.tif"


def rd(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)


def pos(p: Path) -> np.ndarray:
    a = rd(p)
    if a.dtype.kind == "f":
        return np.isfinite(a) & (a > 0)
    return a > 0


def main() -> None:
    h33 = pos(DOTTED)
    h27 = pos(H27)
    d28 = pos(D28)
    tip = pos(TIP)
    labels = rd(LABELS) > 0
    sgmc = rd(SGMC) > 0
    footprint = np.isfinite(rd(TEMPLATE))
    d_cat = distance_transform_edt(~labels)
    truth = sgmc & footprint & (d_cat >= 3.0)

    A = d28 & ~h27          # removed at 0.2600 -> 0.2708
    B = h27 & ~h33          # removed at 0.2708 -> 0.2778
    assert A.sum() == 3891 and B.sum() == 2545

    base_dti = dti(h33.astype(np.float64), truth)
    scale = LIVE_CREDIT_PER_DOT / (base_dti.tp / h33.sum())
    live_bar_proxy = ALPHA * LIVE_DTI / scale

    rows = {}
    for tag, group, base in [
        ("A_catalogue_flank_B1", A, h27),
        ("B_catalogue_flank_B2", B, h33),
    ]:
        tb = dti(base.astype(np.float64), truth)
        tg = dti(np.maximum(base, group).astype(np.float64), truth)
        n = float(group.sum())
        rows[tag] = {
            "dots": n,
            "marginal_proxy_tp": tg.tp - tb.tp,
            "marginal_proxy_credit_per_dot": (tg.tp - tb.tp) / n,
            "live_credit_per_dot_from_leaderboard": {"A_catalogue_flank_B1": 0.0, "B_catalogue_flank_B2": 58.6 / 2545}[tag],
            "live_bar_in_proxy_units": live_bar_proxy,
            "below_live_bar": bool(((tg.tp - tb.tp) / n) < live_bar_proxy),
        }

    # the group we actually have to decide on
    sup_d = kernel_support(h33.astype(np.float64))
    t_only = tip & ~h33
    for tag, m in [
        ("tip_only_all", t_only),
        ("tip_only_dcat_ge_2px", t_only & (d_cat >= 2.0)),
        ("tip_only_dcat_ge_3px", t_only & (d_cat >= 3.0)),
        ("tip_only_sup_d_gt_033", t_only & (sup_d > 1.0 / 3.0)),
    ]:
        tb = dti(h33.astype(np.float64), truth)
        tg = dti(np.maximum(h33, m).astype(np.float64), truth)
        n = float(m.sum())
        rows[tag] = {
            "dots": n,
            "marginal_proxy_tp": tg.tp - tb.tp,
            "marginal_proxy_credit_per_dot": (tg.tp - tb.tp) / n,
            "live_bar_in_proxy_units": live_bar_proxy,
            "below_live_bar": bool(((tg.tp - tb.tp) / n) < live_bar_proxy),
        }

    # transfer coefficient: live credit per dot vs proxy credit per dot for A and B
    transfer = {}
    for tag, live_e in [("A_catalogue_flank_B1", 0.0), ("B_catalogue_flank_B2", 58.6 / 2545)]:
        pe = rows[tag]["marginal_proxy_credit_per_dot"]
        transfer[tag] = {"proxy_credit_per_dot": pe, "live_credit_per_dot": live_e,
                         "live_over_proxy": (live_e / pe) if pe > 0 else None}
    implied = {}
    for tag in ["tip_only_all", "tip_only_dcat_ge_2px", "tip_only_dcat_ge_3px", "tip_only_sup_d_gt_033"]:
        pe = rows[tag]["marginal_proxy_credit_per_dot"]
        ratios = [v["live_over_proxy"] for v in transfer.values() if v["live_over_proxy"] is not None]
        implied[tag] = {"proxy_credit_per_dot": pe,
                        "live_credit_per_dot_if_ratio_1": pe * scale,
                        "live_credit_per_dot_using_B_ratio": pe * (transfer["B_catalogue_flank_B2"]["live_over_proxy"] or 0),
                        "notes": "[MODEL] A's live credit is only known to be ~0 (it is the zero-credit-pair assumption), so only B gives a usable ratio."}

    out = {
        "schema": "GEMSDOE48-instrument-calibration-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "lineage_check": {"d28": int(d28.sum()), "h27_4": int(h27.sum()), "h33_2_b2": int(h33.sum()),
                          "A": int(A.sum()), "B": int(B.sum()),
                          "nested": bool(bool((h33 & ~h27).sum() == 0) and bool((h27 & ~d28).sum() == 0))},
        "proxy_truth_pixels": int(truth.sum()),
        "scale_live_over_proxy_mean_credit": scale,
        "live_bar_in_proxy_units": live_bar_proxy,
        "groups": rows,
        "transfer": transfer,
        "implied_live_credit_for_tip_only": implied,
        "note": "A and B are [ANCHOR]-backed live outcomes (owner-reported scores). Their proxy credit is [MEASURED].",
    }
    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "h49-instrument-calibration.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
