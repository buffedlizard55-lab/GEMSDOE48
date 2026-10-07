#!/usr/bin/env python3
"""GEMSDOE48 H56 validation: format audit, uniqueness, blocked holdout, live-model
projection, and the pre-registered OK-to-submit verdict.

Instruments (each one documented with what it IS and IS NOT)
-------------------------------------------------------------
1. Format audit      - grid/CRS/transform/dtype/range checks against the pinned
                       sample template; the "Predicted values must be in range
                       [0,1]" rejection is re-derived from the organizer's words.
2. Uniqueness        - sha256 distinctness from every file in docs/downloads and
                       every registry mirror pin; nearest-neighbour correlation
                       against all prior downloads (bounded, local check only).
3. Blocked holdout   - H55 protocol (evidence/holdout_h55_spatial_20261007.json):
                       four fixed 2x2 quadrants; held-out quadrant + 300 m halo
                       clipped to the footprint; only core-quadrant truth scored;
                       two truth sources (catalogue; SGMC off-catalogue > 300 m).
                       PROXY ONLY: never an organizer score.
4. Live-model        - the two-constant forward model fitted to the eight
                       owner-reported live scores (evidence/live_model_calibration
                       _20261007.json): DTI = rho*Cov(X;B_elig)/(0.2*S + 0.8*|G|),
                       extended to graded surfaces by letting Cov and S be value
                       weighted. A PROJECTION with measured +/-2 % family error
                       and -38 % out-of-family transfer error; not a score.
5. Verdict           - pre-registered gates, computed after the numbers exist:
                       G1 format ok; G2 holdout beats BOTH parents on >=3/4 folds
                       for BOTH truths; G3 live-model projection >= 0.2778.
                       Banner = G1 AND G2 AND G3 -> "OK TO SUBMIT", else
                       "DOWNLOAD OK - SUBMIT NOT RECOMMENDED".

Usage: python scripts/validate_h56.py --primary <h56-zeros-outside.tif>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.metric import dti_result, kernel, weighted_tp_credit  # noqa: E402

ALPHA, BETA, R = 0.2, 0.8, 3.0
# live-model constants, copied from evidence/live_model_calibration_20261007.json
RHO = 0.06801513031394778
G_PX = 14027.470000000054
BREAK_EVEN_02778 = 0.05556
LIVE_PARENTS = {"dotted_c": 0.2778, "tip_h33d": 0.2632}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_band(path: Path):
    with rasterio.open(path) as s:
        return s.read(1), s


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--primary", required=True, type=Path)
    args = ap.parse_args()
    args.primary = args.primary.resolve()
    now = datetime.now(timezone.utc).isoformat()

    tmpl_arr, tmpl_src = read_band(ROOT / "data/raw/sample_submission_template.tif")
    lab, _ = read_band(ROOT / "data/raw/labels_catalogue.tif")
    footprint = lab != -1
    catalogue = lab == 1
    dcat = ndi.distance_transform_edt(~catalogue)
    bb, _ = read_band(ROOT / "data/raw/scored/h19_5_01922.tif")
    bb = np.nan_to_num(bb.astype(np.float32), nan=0.0) > 0

    dots_d, _ = read_band(ROOT / "data/families/dotted_b2_prune_02778.tif")
    dots_d = (dots_d > 0) & footprint
    dots_t, _ = read_band(ROOT / "data/families/tip_stepover_r30_02632.tif")
    dots_t = (dots_t > 0) & footprint
    union = (dots_d | dots_t).astype(np.float64)
    mean_bin = 0.5 * (dots_d.astype(np.float64) + dots_t.astype(np.float64))
    sgmc, _ = read_band(ROOT / "data/official/derived_sgmc_faults_100m.tif")
    sgmc_truth = (sgmc > 0) & footprint & (dcat > 3.0)

    # ------------------------------------------------------------------ 1. format
    with rasterio.open(args.primary) as s:
        prim = s.read(1).astype(np.float64)
        prim_prof = s.profile
    fa = {
        "generated_utc": now,
        "path": str(args.primary.relative_to(ROOT)),
        "sha256": sha256_file(args.primary),
    }
    checks = {}
    checks["crs_matches_template"] = str(prim_prof["crs"]) == str(tmpl_src.crs)
    checks["transform_matches_template"] = prim_prof["transform"] == tmpl_src.transform
    checks["shape_matches_template"] = (prim_prof["height"], prim_prof["width"]) == (
        tmpl_src.height, tmpl_src.width)
    checks["single_band_float32"] = prim_prof["count"] == 1 and prim_prof["dtype"] == "float32"
    checks["all_cells_finite"] = bool(np.isfinite(prim).all())
    checks["values_in_0_1"] = bool((prim.min() >= 0.0) and (prim.max() <= 1.0))
    checks["max_equals_one"] = bool(abs(prim.max() - 1.0) < 1e-6)
    checks["nodata_unset"] = prim_prof.get("nodata") is None
    checks["outside_footprint_is_zero"] = bool((prim[~footprint] == 0).all())
    checks["organizer_rule_values_in_range_0_1"] = checks["all_cells_finite"] and checks["values_in_0_1"]
    fa["checks"] = checks
    fa["all_passed"] = bool(all(checks.values()))
    (ROOT / "evidence/h56_format_audit_20261007.json").write_text(json.dumps(fa, indent=1))
    print(f"[format] all_passed={fa['all_passed']}")

    # ---------------------------------------------------------------- 2. uniqueness
    uniq = {"generated_utc": now, "sha256": fa["sha256"]}
    seen = {}
    nearest = []
    subs = footprint.copy()
    ys, xs = np.nonzero(subs)
    sel = np.zeros_like(subs, bool)
    sel[ys[::5], xs[::5]] = True  # 1/25 subsample of footprint for speed
    pf = prim[sel]
    for p in sorted((ROOT / "docs/downloads").rglob("*.tif")):
        if p.resolve() == args.primary.resolve():
            continue
        h = sha256_file(p)
        seen[str(p.relative_to(ROOT))] = h
        if h == fa["sha256"]:
            uniq["collision"] = str(p)
        try:
            a, _ = read_band(p)
            a = np.nan_to_num(a.astype(np.float64), nan=0.0)
            af = a[sel]
            if np.std(pf) > 0 and np.std(af) > 0:
                r = float(np.corrcoef(pf, af)[0, 1])
            else:
                r = None
            nearest.append({"file": str(p.relative_to(ROOT)), "pearson_r_subsampled": r,
                            "positive_cells": int((a > 0).sum())})
        except Exception as exc:  # unreadable diagnostic twin etc.
            nearest.append({"file": str(p.relative_to(ROOT)), "error": str(exc)})
    uniq["n_compared"] = len(seen)
    uniq["byte_distinct_from_all_downloads"] = "collision" not in uniq
    reg = json.load(open(ROOT / "registry/live_scores.json"))
    reg_shas = {r.get("sha256", ""): r["id"] for r in reg["rasters"]}
    uniq["matches_registry_mirror_pin"] = fa["sha256"] in reg_shas
    nearest.sort(key=lambda d: -(d.get("pearson_r_subsampled") or -2))
    uniq["nearest_neighbours_top5"] = nearest[:5]
    jsup = (prim > 0) & footprint
    uniq["support_jaccard_vs_dotted"] = float((jsup & dots_d).sum() / (jsup | dots_d).sum())
    uniq["support_jaccard_vs_tip"] = float((jsup & dots_t).sum() / (jsup | dots_t).sum())
    uniq["support_jaccard_vs_union"] = float((jsup & (union > 0)).sum() / (jsup | (union > 0)).sum())
    (ROOT / "evidence/h56_uniqueness_20261007.json").write_text(json.dumps(uniq, indent=1))
    print(f"[uniqueness] distinct={uniq['byte_distinct_from_all_downloads']} "
          f"n={uniq['n_compared']} nearest={nearest[0]['file'] if nearest else '-'} "
          f"r={nearest[0].get('pearson_r_subsampled') if nearest else '-'}")

    # ---------------------------------------------------------------- 3. holdout
    ys, xs = np.nonzero(footprint)
    ym, xm = int(np.median(ys)), int(np.median(xs))
    H, W = footprint.shape
    yy, xx = np.mgrid[0:H, 0:W]
    qmask = (yy >= ym).astype(np.int8) * 2 + (xx >= xm).astype(np.int8)
    folds = [(qmask == i) & footprint for i in range(4)]
    fold_names = ["NW", "NE", "SW", "SE"]

    candidates = {
        "h56_belief": prim,
        "dotted_c": dots_d.astype(np.float64),
        "tip_h33d": dots_t.astype(np.float64),
        "union_binary": union,
        "naive_mean_binary": mean_bin,
    }
    truths = {"catalogue": catalogue, "sgmc_offcat_gt300m": sgmc_truth}
    hold = {"generated_utc": now,
            "protocol": ("H55 protocol: 4 fixed quadrants at footprint median row/col; "
                         "domain = held-out quadrant + 3 px (300 m) halo clipped to the "
                         "footprint; only core-quadrant truth scored; official DTI "
                         "(alpha=0.2, beta=0.8, triangular R=300 m)."),
            "truths": {k: int(v.sum()) for k, v in truths.items()},
            "results": {}}
    for tname, truth in truths.items():
        hold["results"][tname] = {}
        for cname, cand in candidates.items():
            per = {}
            for fname, core in zip(fold_names, folds):
                dom = core | (ndi.distance_transform_edt(~core) <= R)
                dom &= footprint
                r0, r1 = np.nonzero(dom)[0].min(), np.nonzero(dom)[0].max() + 1
                c0, c1 = np.nonzero(dom)[1].min(), np.nonzero(dom)[1].max() + 1
                sl = (slice(r0, r1), slice(c0, c1))
                res = dti_result(cand[sl] * dom[sl], truth[sl] & core[sl], ALPHA, BETA, R)
                per[fname] = {"dti": res.dti, "tp": res.tp, "fp": res.fp, "fn": res.fn,
                              "n_truth": res.truth_pixels, "mass": res.mass}
            dts = [per[f]["dti"] for f in fold_names]
            per["mean_dti"] = float(np.mean(dts))
            hold["results"][tname][cname] = per

    # paired summary: candidate vs each parent, per truth
    hold["paired_vs_parents"] = {}
    for tname in truths:
        row = {}
        for parent in LIVE_PARENTS:
            wins = sum(1 for f in fold_names if
                       hold["results"][tname]["h56_belief"][f]["dti"] >
                       hold["results"][tname][parent][f]["dti"])
            row[parent] = {
                "candidate_mean": hold["results"][tname]["h56_belief"]["mean_dti"],
                "parent_mean": hold["results"][tname][parent]["mean_dti"],
                "delta_mean": (hold["results"][tname]["h56_belief"]["mean_dti"] -
                               hold["results"][tname][parent]["mean_dti"]),
                "folds_won_of_4": wins,
            }
        hold["paired_vs_parents"][tname] = row
    (ROOT / "evidence/holdout_h56_spatial_20261007.json").write_text(json.dumps(hold, indent=1))
    print("[holdout] catalogue:", {k: round(v, 5) for k, v in
          {c: hold["results"]["catalogue"][c]["mean_dti"] for c in candidates}.items()})
    print("[holdout] sgmc:", {k: round(v, 5) for k, v in
          {c: hold["results"]["sgmc_offcat_gt300m"][c]["mean_dti"] for c in candidates}.items()})

    # ----------------------------------------------------------- 4. live model
    belig = bb & (dcat > 2.0) & footprint
    # Cov(X; B_elig) is the metric's own kernel-weighted truth credit: each
    # eligible-backbone pixel contributes max_x p(x) k(d(x,g)). For binary
    # emissions this is exactly the calibration's cov_eligible_backbone.
    def project(p: np.ndarray) -> dict:
        pw = np.where(footprint, p, 0.0).astype(np.float64)
        S = float(pw.sum())
        credit, _ = weighted_tp_credit(pw, belig, R)
        cov = float(credit.sum())
        dti_pred = RHO * cov / (0.2 * S + 0.8 * G_PX) if S > 0 else 0.0
        return {"mass_S": S, "cov_elig": cov, "dti_projection": dti_pred}

    proj = {"generated_utc": now,
            "model": "DTI = rho*Cov(X;B_elig)/(0.2*S + 0.8*|G|), graded extension: "
                     "Cov and S value-weighted",
            "rho": RHO, "hidden_truth_px": G_PX, "eligible_backbone_px": int(belig.sum()),
            "break_even_credit_at_0.2778": BREAK_EVEN_02778,
            "projection_note": ("In-family fitted RMS 1.76% on binary artifacts; graded "
                                "surfaces extrapolate the same forward model - an "
                                "extrapolation, not a measurement."),
            "surfaces": {}}
    proj["surfaces"]["h56_belief"] = project(prim)
    proj["surfaces"]["dotted_c_binary"] = project(dots_d.astype(np.float64))
    proj["surfaces"]["tip_h33d_binary"] = project(dots_t.astype(np.float64))
    proj["surfaces"]["union_binary"] = project(union)
    proj["surfaces"]["naive_mean_binary"] = project(mean_bin)
    # graded diagnostic: what would the DS surface score if threshold-binarized
    # at the metric's own break-even bar? (NOT a submission; informs next session)
    proj["surfaces"]["h56_belief_binarized_at_breakeven"] = project((prim > BREAK_EVEN_02778).astype(np.float64))
    proj["surfaces"]["h56_belief_binarized_at_pignistic_0.5"] = project((prim > 0.5).astype(np.float64))
    belig_cov_check = proj["surfaces"]["dotted_c_binary"]["cov_elig"]
    proj["sanity_check_vs_calibration"] = {
        "calibrated_cov_dotted_c": 75206.82023682503,
        "recomputed_cov_dotted_c": belig_cov_check,
        "rel_diff_pct": 100.0 * (belig_cov_check - 75206.82023682503) / 75206.82023682503,
    }
    mass_below = float((prim[(prim > 0) & footprint] <= BREAK_EVEN_02778).sum())
    proj["h56_mass_below_breakeven_px"] = mass_below
    (ROOT / "evidence/h56_live_model_projection_20261007.json").write_text(json.dumps(proj, indent=1))
    print("[live-model]", {k: round(v["dti_projection"], 4) for k, v in proj["surfaces"].items()})

    # ---------------------------------------------------------------- 5. verdict
    g1 = fa["all_passed"]
    g2 = all(hold["paired_vs_parents"][t][p]["folds_won_of_4"] >= 3
             for t in truths for p in LIVE_PARENTS) and all(
        hold["paired_vs_parents"][t][p]["delta_mean"] > 0 for t in truths for p in LIVE_PARENTS)
    g3 = proj["surfaces"]["h56_belief"]["dti_projection"] >= LIVE_PARENTS["dotted_c"]
    verdict = {
        "generated_utc": now,
        "gate_1_format": g1,
        "gate_2_holdout_beats_both_parents_3_of_4_both_truths": g2,
        "gate_3_live_model_projection_ge_0.2778": g3,
        "ok_to_download": g1,
        "submit_recommended": bool(g1 and g2 and g3),
        "banner": ("OK TO DOWNLOAD AND SUBMIT" if (g1 and g2 and g3)
                   else "DOWNLOAD OK - SUBMIT NOT RECOMMENDED"),
        "reasons": {
            "holdout_means": {t: {c: hold["results"][t][c]["mean_dti"] for c in
                                  ["h56_belief", "dotted_c", "tip_h33d"]} for t in truths},
            "live_projection": proj["surfaces"]["h56_belief"]["dti_projection"],
            "incumbent_live": 0.2778,
        },
    }
    fa["verdict"] = verdict
    (ROOT / "evidence/h56_format_audit_20261007.json").write_text(json.dumps(fa, indent=1))
    print("[verdict]", verdict["banner"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
