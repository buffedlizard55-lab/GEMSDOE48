#!/usr/bin/env python3
"""Round 2: tier-value sweep + union variants + catalogue-leakage audit.

Question 1: is the singleton tier value monotone in off-catalogue DTI?
Question 2: does adding h32-1 (the other tip-family artifact, 0.2649) to the
            union help or hurt?
Question 3: is the union strictly off-catalogue (no wasted FP on known faults)?
"""
import datetime as dt
import json
import os
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gemsdoe48 import dataio
from gemsdoe48.dempster_shafer import dempster_combine
from gemsdoe48.format_checks import dump_json
from gemsdoe48.metric import dti_components_fast

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "raw")
EVIDENCE = os.path.join(ROOT, "evidence")


def tiered(both, single, v_single):
    out = np.zeros(both.shape)
    out[both] = 1.0
    out[single] = v_single
    return out


def main():
    out = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat()}
    footprint = dataio.footprint_from_template(os.path.join(RAW, "sample_submission_template.tif"))
    cat = (dataio.load(os.path.join(RAW, "labels_catalogue.tif")) > 0)
    sgmc = (dataio.load(os.path.join(RAW, "sgmc_faults_100m.tif")) > 0)
    d_cat = distance_transform_edt(~cat)
    offcat = sgmc & footprint & (d_cat > 3.0)

    s_dot = dataio.load(os.path.join(RAW, "dotted_h33_2_b2_zeros.tif")) > 0
    s_tip = dataio.load(os.path.join(RAW, "tip_h33d_stepover.tif")) > 0
    s_h32 = dataio.load(os.path.join(RAW, "tip_h32_1_prethin_tip_euler.tif")) > 0

    both = s_dot & s_tip
    single = (s_dot ^ s_tip)
    union = s_dot | s_tip

    # ---- catalogue leakage audit ----------------------------------------
    leak = {
        "union_on_catalogue": int((union & cat).sum()),
        "union_min_dist_to_cat_px": float(d_cat[union].min()) if union.any() else None,
        "union_within_300m_of_cat": int((union & (d_cat <= 3.0)).sum()),
        "triple_union_on_catalogue": int(((union | s_h32) & cat).sum()),
        "h32_extra_on_catalogue": int(((s_h32 & ~union) & cat).sum()),
        "h32_extra_count": int((s_h32 & ~union).sum()),
    }
    out["leakage"] = leak
    print("leakage:", json.dumps(leak, indent=1))

    # ---- arms -------------------------------------------------------------
    arms = {}
    for v in (0.25, 0.5, 0.66, 0.75, 0.9, 1.0):
        arms[f"tier_{v:.2f}"] = tiered(both, single, v)
    arms["union_dot_h32"] = (s_dot | s_h32).astype(np.float64)
    arms["triple_union"] = (s_dot | s_tip | s_h32).astype(np.float64)
    arms["A_dotted"] = s_dot.astype(np.float64)
    arms["B_tip"] = s_tip.astype(np.float64)

    res_offcat, res_cat = {}, {}
    for name, pred in arms.items():
        r1 = dti_components_fast(pred, offcat)
        r2 = dti_components_fast(pred, cat & footprint)
        res_offcat[name] = r1["DTI"]
        res_cat[name] = r2["DTI"]
        print(f"{name:16s} offcat={r1['DTI']:.4f}  cat={r2['DTI']:.4f}  "
              f"n_pos={r1['n_pred_positive']}")

    out["offcat_dti"] = res_offcat
    out["cat_dti"] = res_cat

    best = max(res_offcat, key=res_offcat.get)
    out["best_arm_offcat"] = best
    print("\nbest arm (pooled off-catalogue):", best, res_offcat[best])
    dump_json(out, os.path.join(EVIDENCE, "round2_tier_sweep.json"))
    print("wrote evidence/round2_tier_sweep.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
