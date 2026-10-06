#!/usr/bin/env python3
"""Spatially-blocked holdout validation of the Dempster-Shafer fusion.

Truth proxies (both derived from official/public data, never from the hidden set):
  CATALOGUE      : official label raster (owner mirror sha256 7ba308cc...),
                   60,988 px.  Blocked into 4 spatial quadrants.
  SGMC off-cat   : USGS State Geologic Map Compilation faults rasterized to
                   the grid (owner mirror of the GEMSDOE30 derivation from
                   mrdata.usgs.gov, sha256 26d142c4...), restricted to cells
                   > 300 m from the catalogue.  This is the only populated
                   fault population in reach that is off-catalogue by
                   construction -- the population that resembles the hidden
                   expert-mapped truth.  Also blocked into 4 quadrants.

Arms (all are FIXED surfaces; nothing is fit to any truth here):
  A  dotted h33-2-b2                       (owner-reported live 0.2778)
  B  tip h33d analog tip-stepover          (owner-reported live 0.2632)
  C  naive mean (A+B)/2 graded             (support = union)
  D  union binary (value 1 on A|B)
  E  intersection binary (value 1 on A&B)
  F  DS combined belief, normalized        (THE submission candidate)
  G  DS belief thresholded > 0.5           (intersection-support variant)

Gate (adapted from the group's preregistered promotion style):
  F must beat BOTH A and B in >= 3 of 4 quadrants on the blocked SGMC
  off-catalogue proxy, and must not degrade vs D (plain union) there.
"""
import datetime as dt
import json
import os
import sys

import numpy as np
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gemsdoe48 import dataio
from gemsdoe48.dempster_shafer import dempster_combine, normalize_bel
from gemsdoe48.format_checks import dump_json
from gemsdoe48.metric import ALPHA, BETA, EPS, coverage_field

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "raw")
EVIDENCE = os.path.join(ROOT, "evidence")

ALPHA_DS = 0.99
CAT_GAP_PX = 3.0  # 300 m in pixels


def blocks_quadrants(shape):
    h, w = shape
    mid_r, mid_c = h // 2, w // 2
    return {
        "Q_NW": (np.s_[:mid_r, :mid_c]),
        "Q_NE": (np.s_[:mid_r, mid_c:]),
        "Q_SW": (np.s_[mid_r:, :mid_c]),
        "Q_SE": (np.s_[mid_r:, mid_c:]),
    }


def score_arm(pred: np.ndarray, truth_mask: np.ndarray, cover_cache: dict, key):
    """DTI of pred against truth_mask; coverage field cached per arm."""
    if key not in cover_cache:
        cover_cache[key] = coverage_field(pred)
    cover = cover_cache[key]
    n_truth = int(truth_mask.sum())
    if n_truth == 0:
        return None
    cover_g = cover[truth_mask]
    tpw = float(cover_g.sum())
    fnw = float((1.0 - cover_g).sum())
    d_truth = distance_transform_edt(~truth_mask)
    k_nearest = np.clip(1.0 - d_truth / 3.0, 0.0, 1.0)
    pos = pred > 0
    fpw = float((pred[pos] * (1.0 - k_nearest[pos])).sum())
    return {"DTI": tpw / (tpw + ALPHA * fpw + BETA * fnw + EPS),
            "TPw": tpw, "FPw": fpw, "FNw": fnw,
            "n_truth": n_truth, "n_pred_positive": int(pos.sum())}


def main():
    out = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
           "alpha_ds": ALPHA_DS, "metric": {"alpha": ALPHA, "beta": BETA,
                                             "R_m": 300.0, "grid_m": 100.0}}

    footprint = dataio.footprint_from_template(os.path.join(RAW, "sample_submission_template.tif"))
    cat = (dataio.load(os.path.join(RAW, "labels_catalogue.tif")) > 0)
    sgmc = (dataio.load(os.path.join(RAW, "sgmc_faults_100m.tif")) > 0)
    s_dot = (dataio.load(os.path.join(RAW, "dotted_h33_2_b2_zeros.tif")) > 0).astype(np.float64)
    s_tip = (dataio.load(os.path.join(RAW, "tip_h33d_stepover.tif")) > 0).astype(np.float64)

    # off-catalogue SGMC proxy: SGMC cells strictly more than 300 m from catalogue
    d_cat = distance_transform_edt(~cat)  # px
    offcat = sgmc & footprint & (d_cat > CAT_GAP_PX)
    out["truth_sizes"] = {
        "catalogue": int(cat.sum()),
        "sgmc_in_footprint": int((sgmc & footprint).sum()),
        "sgmc_offcat_gt_300m": int(offcat.sum()),
    }
    print("[ok] truth sizes:", json.dumps(out["truth_sizes"]))
    print("     (published reference: 60988 / 82151 / 61664)")

    # ---- arms -------------------------------------------------------------
    ds = dempster_combine(s_dot, s_tip, ALPHA_DS, ALPHA_DS)
    bel = normalize_bel(ds["bel"], footprint)
    arms = {
        "A_dotted": s_dot,
        "B_tip": s_tip,
        "C_naive_mean": 0.5 * (s_dot + s_tip),
        "D_union_binary": ((s_dot > 0) | (s_tip > 0)).astype(np.float64),
        "E_intersection_binary": ((s_dot > 0) & (s_tip > 0)).astype(np.float64),
        "F_DS_bel": bel.astype(np.float64),
        "G_DS_bel_gt_half": ((bel > 0.5) & footprint).astype(np.float64),
    }

    blocks = blocks_quadrants(s_dot.shape)
    truths = {}
    for b, sl in blocks.items():
        m = np.zeros_like(cat); m[sl] = cat[sl]
        truths[f"catalogue_{b}"] = m
        m2 = np.zeros_like(cat); m2[sl] = offcat[sl]
        truths[f"sgmcoffcat_{b}"] = m2
    truths["catalogue_full"] = cat & footprint
    truths["sgmcoffcat_full"] = offcat

    cover_cache = {}
    results = {}
    for tname, tmask in truths.items():
        results[tname] = {}
        for aname, pred in arms.items():
            r = score_arm(pred, tmask, cover_cache, aname)
            results[tname][aname] = r
        line = " | ".join(f"{a[:7]}={r['DTI']:.4f}" if r else f"{a[:7]}=NA"
                          for a, r in results[tname].items())
        print(f"[{tname:20s}] {line}")

    # ---- gate evaluation ----------------------------------------------------
    gate = {}
    for proxy in ("sgmcoffcat", "catalogue"):
        qs = [f"{proxy}_{b}" for b in blocks]
        f_beats_a = sum(1 for q in qs
                        if results[q]["F_DS_bel"] and results[q]["A_dotted"]
                        and results[q]["F_DS_bel"]["DTI"] > results[q]["A_dotted"]["DTI"])
        f_beats_b = sum(1 for q in qs
                        if results[q]["F_DS_bel"] and results[q]["B_tip"]
                        and results[q]["F_DS_bel"]["DTI"] > results[q]["B_tip"]["DTI"])
        f_beats_d = sum(1 for q in qs
                        if results[q]["F_DS_bel"] and results[q]["D_union_binary"]
                        and results[q]["F_DS_bel"]["DTI"] >= results[q]["D_union_binary"]["DTI"])
        gate[proxy] = {"F_beats_A_folds": f_beats_a, "F_beats_B_folds": f_beats_b,
                       "F_geq_D_folds": f_beats_d}
    full_sg = results["sgmcoffcat_full"]
    gate["sgmcoffcat_full"] = {
        a: full_sg[a]["DTI"] for a in arms if full_sg.get(a)
    }
    gate["PASS_offcat_blocked"] = (gate["sgmcoffcat"]["F_beats_A_folds"] >= 3
                                   and gate["sgmcoffcat"]["F_beats_B_folds"] >= 3)
    out["gate"] = gate
    out["results"] = results
    print("\nGATE:", json.dumps(gate, indent=1))

    # persist the core receipt before the extra sensitivity pass
    dump_json(out, os.path.join(EVIDENCE, "holdout_validation.json"))

    # free the per-arm coverage caches before allocating more
    cover_cache.clear()
    import gc
    gc.collect()

    # ---- alpha sensitivity on full off-catalogue truth -----------------------
    sens = {}
    for a1 in (0.80, 0.90, 0.95, 0.99):
        d2 = dempster_combine(s_dot, s_tip, a1, a1)
        b2 = normalize_bel(d2["bel"], footprint).astype(np.float64)
        r = score_arm(b2, offcat, {}, f"sens_{a1}")
        sens[str(a1)] = r["DTI"]
    out["alpha_sensitivity_offcat_full"] = sens
    print("alpha sensitivity (offcat full):", sens)

    dump_json(out, os.path.join(EVIDENCE, "holdout_validation.json"))
    print("\nwrote evidence/holdout_validation.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
