#!/usr/bin/env python3
"""Build the H53 unique submission: conduit-anchored, conflict-priced extension of C.

Run from the repository root:

    python scripts/build_submission_h53.py

Writes (all under ``docs/downloads/``):
  * ``GEMSDOE48-H53-...-zeros-outside.tif``   -- PRIMARY, all-finite, portal-range-immune
  * ``GEMSDOE48-H53-...-zeros-outside.zip``   -- PRIMARY zipped (portal accepts either)
  * ``GEMSDOE48-H53-...-nan-outside.tif``     -- NaN-outside twin, sample-template convention
  * ``diagnostics/gemsdoe48-h53-{bel,plausibility,mtheta,conflict}-<id>.tif``
and receipts under ``evidence/`` and ``registry/``.

Every number in the receipt is computed here; nothing is transcribed.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48 import conduit as conduit_mod                      # noqa: E402
from gemsdoe48 import h53 as h53_mod                               # noqa: E402
from gemsdoe48.dempster_shafer import dempster_combine             # noqa: E402
from gemsdoe48.geotiff import (HEIGHT, TRANSFORM, WIDTH,           # noqa: E402
                               assert_competition_grid, display_path,
                               write_float32, write_float32_zeros_outside)
from gemsdoe48.live_model import (LIVE_ARTIFACTS, OUT_OF_FAMILY,    # noqa: E402
                                  ForwardModel, calibrate, coverage,
                                  invert_truth, load_binary,
                                  max_credit_field)

SESSION = "H53"
BUILD_DATE = "20261007"
LIVE_C = 0.2778                # owner-reported live score of the untouched dotted core
ALPHA1 = ALPHA2 = 0.6          # symmetric Shafer reliability discount (pre-registered)
SAFETY_FACTOR = 1.25           # break-even bar multiplier for A2 (pre-registered)
MAX_MODELLED_DOWNSIDE = 0.0100 # worst-case loss floor for the total addition (pre-registered)
MIN_TIER = 2                   # conduit tier floor for A1 (pre-registered)

INPUTS = {
    "core_dotted_live_best": ("data/families/dotted_b2_prune_02778.tif",
                              "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "tip_family_live_best": ("data/raw/tip_h33d_stepover.tif",
                             "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"),
    "public_catalogue": ("data/official/labels.tif",
                         "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    "footprint_mask": ("data/source_mirrors/footprint-mask.tif",
                       "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f"),
    "sgmc_proxy": ("data/official/derived_sgmc_faults_100m.tif",
                   "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"),
    "conduit_csv": ("data/raw/external/gdr_wellspring_in_footprint.csv",
                    "122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea"),
    "backbone_dense": ("data/raw/scored/h19_5_01922.tif",
                       "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d"),
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_mask(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        assert_competition_grid(ds.profile, path=path)
        return np.nan_to_num(ds.read(1).astype(np.float64), nan=0.0) > 0.5


def read_float(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        assert_competition_grid(ds.profile, path=path)
        return np.nan_to_num(ds.read(1).astype(np.float64), nan=0.0)


def verify_inputs() -> dict:
    out = {}
    for role, (rel, want) in INPUTS.items():
        path = ROOT / rel
        if not path.exists():
            raise SystemExit(
                f"MISSING INPUT {rel} ({role}). Restore the hash-pinned public mirrors first:\n"
                f"  python scripts/fetch_mirrors.py            # labels/template/scored family\n"
                f"  python scripts/restore_h53_inputs.py       # backbone + conduit CSV\n")
        got = sha256_file(path)
        if want and got != want:
            raise SystemExit(f"SHA-256 MISMATCH for {rel}: expected {want}, got {got}")
        out[role] = {"path": rel, "sha256": got, "bytes": path.stat().st_size,
                     "pinned": bool(want), "pin_matched": (got == want) if want else None}
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/downloads")
    parser.add_argument("--receipt", type=Path,
                        default=ROOT / f"evidence/build_h53_receipt_{BUILD_DATE}.json")
    parser.add_argument("--calibration", type=Path,
                        default=ROOT / f"evidence/h53_build_live_model_{BUILD_DATE}.json",
                        help="build-time copy of the calibration. scripts/calibrate_live_model.py "
                             "owns evidence/live_model_calibration_<date>.json and adds the "
                             "coverage frontier and ceiling table; do not point this at that file")
    parser.add_argument("--tag", default=None, help="override the content id used in filenames")
    args = parser.parse_args()

    print("[1/8] verifying hash-pinned inputs (fail closed)")
    inputs = verify_inputs()
    for role, info in inputs.items():
        print(f"      {role:22s} {info['sha256'][:12]} {'PIN-OK' if info['pin_matched'] else 'unpinned'}")

    core = read_mask(ROOT / INPUTS["core_dotted_live_best"][0])
    tip = read_mask(ROOT / INPUTS["tip_family_live_best"][0])
    catalogue = read_mask(ROOT / INPUTS["public_catalogue"][0])
    footprint = read_mask(ROOT / INPUTS["footprint_mask"][0])
    backbone = read_mask(ROOT / INPUTS["backbone_dense"][0])
    s_core = int(core.sum())
    print(f"[2/8] core C={s_core}  tip={int(tip.sum())}  backbone={int(backbone.sum())}  "
          f"catalogue={int(catalogue.sum())}  footprint={int(footprint.sum())}")
    if s_core != 37654:
        raise SystemExit(f"core artifact must be the 37,654 px live-best; got {s_core}")

    catalogue_distance_m = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    eligible_backbone = backbone & (catalogue_distance_m > h53_mod.CATALOGUE_BUFFER_M)
    print(f"      eligible backbone (>200 m off-catalogue) = {int(eligible_backbone.sum())}")

    print("[3/8] calibrating the live-anchored forward model")
    calib = calibrate(backbone, catalogue_distance_m)
    model = ForwardModel(calib["hidden_truth_fit"]["hidden_truth_px"],
                         calib["rho_fit"]["rho"],
                         calib["eligible_backbone_px"])
    cov_core = coverage(core, eligible_backbone)
    t_core = invert_truth(0.2778, s_core, model.hidden_truth_px)
    dti_core_pred = model.dti(cov_core, s_core)
    dti_core_model = dti_core_pred          # the model's own prediction for the untouched core
    bias = LIVE_C - dti_core_model          # constant offset; only model DELTAS are reported
    print(f"      |G|={model.hidden_truth_px:,.1f}  rho={model.rho:.6f}  "
          f"RMS rel err={calib['rho_fit']['rms_relative_error_pct']:.3f}%")
    print(f"      Cov(C)={cov_core:,.1f}  T(C) inverted={t_core:,.1f}  DTI_pred(C)={dti_core_pred:.4f}")

    # Pre-registered budget: the TOTAL addition may not cost more than
    # MAX_MODELLED_DOWNSIDE in the worst case where every added pixel earns
    # exactly zero credit.  Adding a pixel can never lower TPw (it is a maximum
    # over emitted pixels), so this is an exact bound, not an estimate.
    floor_model_dti = dti_core_pred - MAX_MODELLED_DOWNSIDE
    n_max = int((model.tpw(cov_core) / floor_model_dti
                 - 0.2 * s_core - 0.8 * model.hidden_truth_px) / 0.2)
    n_max = max(0, n_max)
    print(f"      pre-registered budget: worst-case loss <= {MAX_MODELLED_DOWNSIDE} -> n_max = {n_max}")

    print("[4/8] Dempster-Shafer combination of the two best families")
    fav_dotted = np.clip(max_credit_field(core), 0.0, 1.0) * footprint
    fav_tip = np.clip(max_credit_field(tip), 0.0, 1.0) * footprint
    ds = dempster_combine(fav_dotted, fav_tip, alpha1=ALPHA1, alpha2=ALPHA2)
    bel, pl, unc, conflict = ds["bel"], ds["pl"], ds["unc"], ds["conflict"]
    naive = 0.5 * (fav_dotted + fav_tip)
    inside = footprint
    pearson = float(pearsonr(bel[inside], naive[inside]).statistic)
    stride = np.nonzero(inside.ravel())[0][::97]
    spear = float(spearmanr(bel.ravel()[stride], naive.ravel()[stride]).statistic)
    absd = np.abs(bel[inside] - naive[inside])
    slope, intercept = np.polyfit(naive[inside], bel[inside], 1)
    affine_resid = float(np.abs(bel[inside] - (slope * naive[inside] + intercept)).mean())
    mean_check = {
        "pearson_bel_vs_naive_mean": pearson,
        "spearman_bel_vs_naive_mean_subsampled": spear,
        "mean_abs_difference": float(absd.mean()),
        "max_abs_difference": float(absd.max()),
        "share_of_footprint_differing_by_gt_0p05": float((absd > 0.05).mean()),
        "best_affine_fit_mean_abs_residual": affine_resid,
        "best_affine_fit_slope": float(slope),
        "best_affine_fit_intercept": float(intercept),
        "is_the_naive_mean": bool(affine_resid < 1e-6 and float(absd.max()) < 1e-9),
        "interpretation": ("Bel(F) is NOT the naive mean: the best affine fit of Bel on 0.5(b1+b2) "
                           "leaves a mean residual of %.4f and the two differ by up to %.3f. The high "
                           "rank correlation is expected and is not evidence of equivalence: on this "
                           "support both statistics are monotone in the same coverage field, so only "
                           "the affine residual and the difference distribution are informative."
                           % (affine_resid, float(absd.max()))),
    }
    print(f"      pearson(Bel, mean)={pearson:.6f}  mean|d|={mean_check['mean_abs_difference']:.6f}  "
          f"max|d|={mean_check['max_abs_difference']:.4f}  affine resid={affine_resid:.6f}")

    print("[5/8] A1 -- hydrothermal conduit anchors (GDR/INGENIOUS wells & springs)")
    sites = conduit_mod.read_sites(ROOT / INPUTS["conduit_csv"][0])
    tier, score = conduit_mod.site_arrays(sites, (HEIGHT, WIDTH), min_tier=MIN_TIER)
    a1_rows, a1_scores, a1_audit = h53_mod.conduit_anchors(
        tier, score, emitted=core, footprint=footprint, catalogue=catalogue,
        catalogue_distance_m=catalogue_distance_m, conflict=conflict,
        min_tier=MIN_TIER, max_points=n_max)
    a1_audit["conduit_source_summary"] = conduit_mod.summarize(sites)
    a1_audit["pre_registered_cap"] = n_max
    n1 = int(len(a1_rows))
    print(f"      {json.dumps({k: v for k, v in a1_audit.items() if k != 'conduit_source_summary'})}")

    print("[6/8] A2 -- conflict-priced gap closure over the two families' union pool")
    pool = (eligible_backbone | tip) & ~core & footprint & (catalogue_distance_m > h53_mod.CATALOGUE_BUFFER_M)
    interim = core.copy()
    if n1:
        interim[a1_rows[:, 0], a1_rows[:, 1]] = True
    break_even_bar = 0.2 * 0.2778 / model.rho
    priced = h53_mod.price_addition_path(interim, pool, eligible_backbone,
                                         break_even_bar=break_even_bar,
                                         max_add=max(0, n_max - n1), model=model,
                                         safety_factor=SAFETY_FACTOR)
    n2 = int(priced["robust_prefix"]["n"])
    a2_rows = priced["rows"][:n2]
    a2_gains = priced["gains"][:n2]
    cov_after_a2 = float(priced["robust_prefix"]["coverage"])
    dti_after_a2 = float(priced["robust_prefix"]["dti_pred"])
    argmax_n = int(priced["argmax_prefix"]["n"])
    argmax_dti = float(priced["argmax_prefix"]["dti_pred"])
    a2_above_safety = int((a2_gains >= SAFETY_FACTOR * break_even_bar).sum()) if n2 else 0
    print(f"      pool={int(pool.sum())}  admitted A2={n2} (safety {SAFETY_FACTOR}x prefix; "
          f"unconstrained argmax would be {argmax_n} at {LIVE_C + (argmax_dti - dti_core_model):.4f})  "
          f"gain range=[{a2_gains.min() if n2 else 0:.3f},{a2_gains.max() if n2 else 0:.3f}]  "
          f"of which >= {SAFETY_FACTOR}x break-even: {a2_above_safety}")
    a2_from_tip = int(sum(1 for r, c in a2_rows.reshape(-1, 2) if tip[r, c])) if n2 else 0

    emission = interim.copy()
    if n2:
        emission[a2_rows[:, 0], a2_rows[:, 1]] = True
    n_added = int(emission.sum()) - s_core
    cov_new = coverage(emission, eligible_backbone)
    dti_pred = model.dti(cov_new, int(emission.sum()))

    # --- decomposition.  dti_after_a2 is priced on a base that already carries A1's
    # dead mass, so A2's own contribution must be priced separately.
    a2_only = core.copy()
    if n2:
        a2_only[a2_rows[:, 0], a2_rows[:, 1]] = True
    cov_a2_only = coverage(a2_only, eligible_backbone)
    dti_a2_only = model.dti(cov_a2_only, s_core + n2)
    live_equiv_a2 = LIVE_C + (dti_a2_only - dti_core_model)
    dti_a1_zero_only = model.dti(cov_core, s_core + n1)
    live_equiv_a1_zero = LIVE_C + (dti_a1_zero_only - dti_core_model)

    print("[7/8] risk accounting and scenario band (anchored on C's live 0.2778)")
    # The model under-predicts C by (LIVE_C - dti_core_model).  Every candidate
    # number is therefore reported as a LIVE-EQUIVALENT: the model's own delta
    # against its own C prediction, applied to C's owner-reported live score.
    s_total = int(emission.sum())
    denom_total = 0.2 * s_total + 0.8 * model.hidden_truth_px
    # Case 1: EVERY added pixel (A1 and A2) earns exactly zero credit.  This is the
    # bound the pre-registered budget n_max was solved for.
    floor_model = model.tpw(cov_core) / denom_total
    floor_live_equiv = LIVE_C + (floor_model - dti_core_model)
    # Case 2: A2 pays exactly as the live-calibrated model prices it (it is in-family
    # and the model is calibrated on this family) while A1 earns zero.  Because A1
    # sits off the eligible backbone the model already prices it at zero, so this
    # case equals the model prediction.
    worst_model = model.tpw(cov_after_a2) / denom_total
    worst_live_equiv = LIVE_C + (worst_model - dti_core_model)
    scenarios = []
    for credit in (0.0, 0.0278, 0.0556, 0.0800, 0.1000, 0.1383, 0.2000, 0.3000):
        t_total = model.tpw(cov_new) + credit * n1
        dti_model = t_total / (0.2 * int(emission.sum()) + 0.8 * model.hidden_truth_px)
        scenarios.append({
            "credit_per_conduit_anchor": credit,
            "tpw_model": t_total,
            "note": "cov_new already includes any eligible-backbone coverage the anchors add",
            "dti_model": dti_model,
            "dti_live_equivalent": LIVE_C + (dti_model - dti_core_model),
            "delta_vs_C_live_equivalent": dti_model - dti_core_model,
        })
    cov_drift = abs(cov_after_a2 - cov_new)
    if cov_drift > 1e-6 * max(1.0, cov_new):
        raise SystemExit(f"coverage bookkeeping mismatch: incremental {cov_after_a2} vs exact {cov_new}")
    print(f"      model bias on C (live - pred) = {bias:+.4f}; only model DELTAS are added to 0.2778")
    print(f"      S={s_total} (C {s_core} + A1 {n1} + A2 {n2})")
    print(f"      FLOOR  every added pixel earns 0 : {floor_live_equiv:.4f} ({floor_live_equiv - LIVE_C:+.4f})")
    print(f"      A2 pays as modelled, A1 earns 0  : {worst_live_equiv:.4f} ({worst_live_equiv - LIVE_C:+.4f})")
    print(f"      decomposition  A2 alone          : {live_equiv_a2:.4f} ({live_equiv_a2 - LIVE_C:+.4f})")
    print(f"      decomposition  A1 alone at 0     : {live_equiv_a1_zero:.4f} ({live_equiv_a1_zero - LIVE_C:+.4f})")
    print(f"      design check A2 gain + A1 cost   : "
          f"{(live_equiv_a2 - LIVE_C) + (live_equiv_a1_zero - LIVE_C):+.5f} net")
    for s in scenarios:
        if s["credit_per_conduit_anchor"] in (0.0556, 0.1383, 0.2, 0.3):
            print(f"      A1 credit {s['credit_per_conduit_anchor']:.4f} -> {s['dti_live_equivalent']:.4f} "
                  f"({s['delta_vs_C_live_equivalent']:+.4f})")
    union_dti = model.dti(coverage(core | tip, eligible_backbone), int((core | tip).sum()))
    print(f"      reference: naive union of both families priced at {union_dti:.4f} "
          f"(live-equivalent {LIVE_C + (union_dti - dti_core_model):.4f})")

    print("[8/8] writing artifacts")
    digest_src = json.dumps({
        "core": sorted(map(int, np.flatnonzero(core.ravel()))),
        "a2": sorted(map(int, (a2_rows[:, 0] * WIDTH + a2_rows[:, 1]))) if len(a2_rows) else [],
        "a1": sorted(map(int, (a1_rows[:, 0] * WIDTH + a1_rows[:, 1]))) if len(a1_rows) else [],
    }, sort_keys=True).encode()
    content_id = hashlib.sha256(digest_src).hexdigest()[:12]
    if args.tag:
        content_id = args.tag
    band_lo = worst_live_equiv
    band_hi = scenarios[-1]["dti_live_equivalent"]
    note = (f"GEMSDOE48-{SESSION} | 0.2778 core untouched + {n2} conflict-priced gap dots "
            f"+ {n1} GDR hot-spring/well conduit anchors >300 m off-catalogue | "
            f"model band {band_lo:.4f}-{band_hi:.4f}, floor {floor_live_equiv:.4f} | "
            f"unscored | id {content_id}")
    if len(note) > 300:
        note = note[:297] + "..."
    stem = (f"GEMSDOE48-{SESSION}-conduit-conflict-priced-{BUILD_DATE}-{content_id}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "diagnostics").mkdir(parents=True, exist_ok=True)

    values = emission.astype(np.float32)
    profile = {"driver": "GTiff", "width": WIDTH, "height": HEIGHT, "count": 1,
               "dtype": "float32", "crs": "EPSG:32611", "transform": TRANSFORM}
    tags = {
        "candidate_id": f"GEMSDOE48-{SESSION}",
        "content_id": content_id,
        "construction": "C (37,654 live-best dots, untouched) + conflict-priced gap closure + "
                        "GDR hydrothermal conduit anchors",
        "encoding": "all-finite float32 in [0,1]; 0.0 outside the survey footprint; nodata unset",
        "provenance": "GEMSDOE48 H53 session; inputs hash-pinned in the build receipt",
        "status": "RESEARCH CANDIDATE - no organizer score exists for this file",
    }
    zeros_path = args.output_dir / f"{stem}-zeros-outside.tif"
    zeros_info = write_float32_zeros_outside(
        zeros_path, values, profile, valid_mask=footprint,
        description="gems_h53_emission_binary_0_1_all_finite_zeros_outside", tags=tags)
    zeros_info["sha256"] = sha256_file(zeros_path)

    nan_path = args.output_dir / f"{stem}-nan-outside.tif"
    nan_values = np.where(footprint, values, np.nan).astype(np.float32)
    nan_info = write_float32(
        nan_path, nan_values, profile, valid_mask=footprint,
        description="gems_h53_emission_binary_0_1_nan_outside", tags=dict(tags, encoding=(
            "in-footprint finite float32 in [0,1]; NaN outside; nodata=NaN")))
    nan_info["sha256"] = sha256_file(nan_path)

    zip_path = args.output_dir / f"{stem}-zeros-outside.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(zeros_path, arcname=zeros_path.name)

    diagnostics = {}
    for name, layer, desc in (
            ("bel", bel, "dempster_shafer_belief_fault_normalized_0_1"),
            ("plausibility", pl, "dempster_shafer_plausibility_fault_0_1"),
            ("mtheta", unc, "dempster_shafer_unassigned_mass_mTheta_0_1_disagreement_diagnostic"),
            ("conflict", conflict, "dempster_shafer_raw_conflict_K_0_1_disagreement_diagnostic")):
        path = args.output_dir / "diagnostics" / f"gemsdoe48-h53-{name}-{content_id}.tif"
        layer01 = np.clip(np.where(footprint, layer, 0.0), 0.0, 1.0).astype(np.float32)
        info = write_float32_zeros_outside(
            path, layer01, profile, valid_mask=footprint, description=desc,
            tags=dict(tags, layer=name, role="diagnostic_not_a_submission"))
        info["sha256"] = sha256_file(path)
        info["min"] = float(layer01[footprint].min())
        info["max"] = float(layer01[footprint].max())
        diagnostics[name] = info

    receipt = {
        "candidate_id": f"GEMSDOE48-{SESSION}",
        "session": SESSION,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "builder": display_path(Path(__file__)),
        "submission_name": stem,
        "content_id": content_id,
        "paste_ready_note": note,
        "paste_ready_note_length": len(note),
        "status": ("RESEARCH CANDIDATE. No organizer score exists for this file. "
                   "Weekly-slot decision is the owner's; see the scenario band below."),
        "inputs": inputs,
        "construction": {
            "core": {"source": INPUTS["core_dotted_live_best"][0], "px": s_core,
                     "owner_reported_live": 0.2778, "modified": False},
            "a2_conflict_priced_gap_closure": {
                "pool": "(eligible_backbone OR tip) AND NOT core AND footprint AND >200 m off-catalogue",
                "pool_px": int(pool.sum()),
                "objective": "greedy marginal coverage of the eligible backbone (max-coverage)",
                "break_even_bar_coverage_units": break_even_bar,
                "safety_factor_audit": SAFETY_FACTOR,
                "admitted_clearing_safety_factor": a2_above_safety,
                "robust_prefix_n": n2,
                "unconstrained_argmax_prefix_n": argmax_n,
                "unconstrained_argmax_live_equivalent": LIVE_C + (argmax_dti - dti_core_model),
                "path_len": len(priced["path"]),
                "admitted": int(len(a2_rows)),
                "admitted_from_tip_family": a2_from_tip,
                "admitted_from_backbone_only": int(len(a2_rows)) - a2_from_tip,
                "gain_min": float(a2_gains.min()) if len(a2_gains) else None,
                "gain_max": float(a2_gains.max()) if len(a2_gains) else None,
                "coverage_after": cov_after_a2,
                "dti_pred_after_on_base_including_a1_mass": dti_after_a2,
                "a2_alone_without_a1_mass": {
                    "coverage": cov_a2_only, "emitted": s_core + n2,
                    "model_dti": dti_a2_only, "live_equivalent": live_equiv_a2,
                    "delta_vs_C": live_equiv_a2 - LIVE_C},
                "a1_alone_at_zero_credit": {
                    "emitted": s_core + n1, "model_dti": dti_a1_zero_only,
                    "live_equivalent": live_equiv_a1_zero,
                    "delta_vs_C": live_equiv_a1_zero - LIVE_C},
                "a2_gain_minus_a1_zero_credit_cost": (
                    (live_equiv_a2 - LIVE_C) + (live_equiv_a1_zero - LIVE_C)),
            },
            "a1_conduit_anchors": a1_audit,
            "budget_rule": {
                "max_modelled_downside": MAX_MODELLED_DOWNSIDE,
                "n_max": n_max,
                "n_used": n_added,
                "n_a1_out_of_family": n1,
                "n_a2_in_family": n2,
            },
        },
        "dempster_shafer": {
            "frame": "Theta = {F, not F}",
            "reliability_alpha1_dotted": ALPHA1,
            "reliability_alpha2_tip": ALPHA2,
            "favorability_inputs": {
                "b1": "max_credit_field(core) clipped to [0,1], zeroed outside the footprint",
                "b2": "max_credit_field(tip) clipped to [0,1], zeroed outside the footprint",
            },
            "bel_min": float(bel[inside].min()), "bel_max": float(bel[inside].max()),
            "pl_min": float(pl[inside].min()), "pl_max": float(pl[inside].max()),
            "mtheta_min": float(unc[inside].min()), "mtheta_max": float(unc[inside].max()),
            "conflict_K_min": float(conflict[inside].min()),
            "conflict_K_max": float(conflict[inside].max()),
            "share_of_footprint_with_K_gt_0": float((conflict[inside] > 0).mean()),
            "not_the_naive_mean": mean_check,
            "why_the_emission_is_binary": (
                "d/dv[(T0+v k)/(D0+0.2 v)] has the sign of k - 0.2*DTI and is independent of v, "
                "so every pixel of a graded belief surface is pushed to 0 or 1. The graded Bel/Pl/"
                "mTheta/K layers are therefore shipped as diagnostics and the submission is binary."),
        },
        "live_model": {
            "hidden_truth_px": model.hidden_truth_px,
            "rho": model.rho,
            "target_eligible_backbone_px": model.target_px,
            "rms_relative_error_pct": calib["rho_fit"]["rms_relative_error_pct"],
            "max_abs_relative_error_pct": calib["rho_fit"]["max_abs_relative_error_pct"],
            "per_artifact": calib["artifacts"],
            "rho_fit": calib["rho_fit"],
            "hidden_truth_fit": calib["hidden_truth_fit"],
            "out_of_family_transfer_check": calib["out_of_family_transfer_check"],
            "cov_core": cov_core,
            "cov_candidate": cov_new,
            "tpw_core_inverted_from_live": t_core,
            "dti_pred_core": dti_core_pred,
            "dti_pred_candidate": dti_pred,
            "dti_pred_delta": dti_pred - dti_core_pred,
            "model_bias_on_core_live_minus_pred": bias,
            "live_equivalent_a2_only": live_equiv_a2,
            "live_equivalent_candidate": LIVE_C + (dti_pred - dti_core_model),
            "union_of_both_families_priced": {
                "px": int((core | tip).sum()),
                "cov": coverage(core | tip, eligible_backbone),
                "dti_pred": union_dti,
                "delta_vs_C_model": union_dti - dti_core_model,
                "live_equivalent": LIVE_C + (union_dti - dti_core_model),
            },
        },
        "risk": {
            "floor_all_added_pixels_zero_credit": {
                "model_dti": floor_model, "live_equivalent": floor_live_equiv,
                "delta_vs_C": floor_live_equiv - LIVE_C,
                "within_pre_registered_floor": bool(floor_live_equiv >= LIVE_C - MAX_MODELLED_DOWNSIDE - 1e-9),
                "pre_registered_floor": LIVE_C - MAX_MODELLED_DOWNSIDE,
            },
            "a2_priced_a1_zero_credit": {
                "model_dti": worst_model, "live_equivalent": worst_live_equiv,
                "delta_vs_C": worst_live_equiv - LIVE_C,
            },
            "coverage_bookkeeping_check_incremental_vs_exact": {
                "incremental": cov_after_a2, "exact": cov_new, "abs_drift": cov_drift,
                "match": bool(cov_drift <= 1e-6 * max(1.0, cov_new))},
            "anchoring_rule": ("live_equivalent = 0.2778 + (model_dti(candidate) - model_dti(C)); "
                               "the model's constant bias on C is cancelled, so only model DELTAS "
                               "are ever added to the owner-reported live score"),
            "scenario_band": scenarios,
            "why_additions_cannot_reduce_tpw": (
                "TPw = sum_g max_x p(x) k(d(x,g)); adding a pixel can only raise or hold the inner "
                "maximum, so T is monotone non-decreasing in the emitted set. The only risk of an "
                "addition is the 0.2 denominator cost."),
        },
        "emission": {
            "positive_pixels": int(emission.sum()),
            "core_px": s_core, "a2_px": int(len(a2_rows)), "a1_px": int(len(a1_rows)),
            "core_preserved_exactly": bool((emission & core).sum() == s_core),
            "on_catalogue_positive_pixels": int((emission & catalogue).sum()),
            "within_200m_of_catalogue_positive_pixels": int(
                (emission & (catalogue_distance_m <= 200.0)).sum()),
            "outside_footprint_positive_pixels": int((emission & ~footprint).sum()),
            "unique_values": [float(v) for v in np.unique(values)],
        },
        "files": {"primary_zeros_outside": zeros_info, "primary_zip": {
                      "path": display_path(zip_path), "bytes": zip_path.stat().st_size,
                      "sha256": sha256_file(zip_path)},
                  "nan_outside_twin": nan_info, "diagnostics": diagnostics},
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    args.calibration.parent.mkdir(parents=True, exist_ok=True)
    args.calibration.write_text(json.dumps(calib, indent=2) + "\n", encoding="utf-8")

    print(f"\nPRIMARY  {display_path(zeros_path)}  {zeros_info['bytes']} bytes  {zeros_info['sha256']}")
    print(f"ZIP      {display_path(zip_path)}")
    print(f"NAN TWIN {display_path(nan_path)}  {nan_info['sha256']}")
    print(f"NOTE     {note}")
    print(f"RECEIPT  {display_path(args.receipt)}")
    print(f"CALIB    {display_path(args.calibration)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
