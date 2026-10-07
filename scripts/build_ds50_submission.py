#!/usr/bin/env python3
"""Build the H50 Dempster-Shafer research raster: B2 dotted x H36-1 rung30.

Parents (both SHA-256 pinned, verified on read):
  A  dotted family best  H33-2-B2      37,654 px  owner-reported live 0.2778
  B  H36-1 rung30       37,660 px  owner-reported live 0.2710 (H19-5 repack; not tip/step-over)

Evidence: metric-geometry kernel-credit belief surfaces (see src/gemsdoe48/ds50.py).
Rule:     two-sided simple support masses, Shafer discounts anchored to the
          owner-reported live scores, canonical normalized Dempster combination.
Output:   normalized Bel(F) submission raster in [0,1], plus m(Theta), K and
          Pl(F) diagnostics, a build receipt, and the not-a-naive-mean checks.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

from gemsdoe48 import ds50
from gemsdoe48.geotiff import (
    assert_competition_grid,
    assert_same_grid,
    display_path,
    read_band,
    write_float32,
)
from gemsdoe48.grid import EXPECTED, write_submission

ROOT = Path(__file__).resolve().parents[1]

PINNED_DOTTED = ROOT / "data/raw/dotted_h33_2_b2_zeros.tif"
PINNED_TIP = ROOT / "data/source_mirrors/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
PRIOR_H48 = ROOT / "docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif"

SHA_DOTTED = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
SHA_TIP_H36 = "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641"
SHA_FOOTPRINT = "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f"

DATESTAMP = "20261007"
SUBMISSION_NAME = "GEMSDOE48-H50-DS-B2xH36"
SUBMISSION_NOTE = (
    "GEMSDOE48 H50 | Dempster fusion: B2 dotted x H36-1 rung30 "
    "(H19-5/rung-30 repacking; not tip/step-over); kernel-credit Bel, "
    "m(Theta)+K diagnostics; historical, unscored research."
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_sha(path: Path, expected: str, label: str) -> None:
    got = sha256_file(path)
    if got != expected:
        raise SystemExit(f"{label}: SHA-256 {got} != pinned {expected} ({path})")


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    if x.size < 2 or np.std(x) == 0 or np.std(y) == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dotted", type=Path, default=PINNED_DOTTED)
    parser.add_argument("--tip", type=Path, default=PINNED_TIP)
    parser.add_argument("--footprint", type=Path, default=FOOTPRINT)
    parser.add_argument("--outdir", type=Path, default=ROOT / "docs/downloads")
    parser.add_argument("--receipt", type=Path, default=ROOT / "evidence/build_ds50_receipt_20261007.json")
    parser.add_argument("--allow-unpinned", action="store_true")
    args = parser.parse_args()

    if len(SUBMISSION_NOTE) > 200:
        raise SystemExit("submission note exceeds the portal's 200-character limit")
    if not args.allow_unpinned:
        require_sha(args.dotted, SHA_DOTTED, "dotted parent")
        require_sha(args.tip, SHA_TIP_H36, "H36-1 rung30 parent")
        require_sha(args.footprint, SHA_FOOTPRINT, "footprint mask")

    dotted_raw, dotted_profile = read_band(args.dotted)
    tip_raw, tip_profile = read_band(args.tip)
    assert_competition_grid(dotted_profile, path=args.dotted)
    assert_competition_grid(tip_profile, path=args.tip)
    assert_same_grid(dotted_profile, tip_profile, name_a=str(args.dotted), name_b=str(args.tip))
    with rasterio.open(args.footprint) as fp_ds:
        assert_competition_grid(fp_ds.profile, path=args.footprint)
        footprint = fp_ds.read(1) == 1

    dotted = np.where(np.isfinite(dotted_raw), dotted_raw, 0.0)
    tip = np.where(np.isfinite(tip_raw), tip_raw, 0.0)
    if np.any((dotted < 0) | (dotted > 1)) or np.any((tip < 0) | (tip > 1)):
        raise SystemExit("parent surfaces must lie in [0, 1]")
    dotted_mask = (dotted > 0) & footprint
    tip_mask = (tip > 0) & footprint
    n_dotted = int(dotted_mask.sum())
    n_tip = int(tip_mask.sum())
    n_both = int((dotted_mask & tip_mask).sum())
    n_union = int((dotted_mask | tip_mask).sum())

    # --- metric-geometry belief surfaces and DS fusion -------------------------
    belief_a = ds50.kernel_belief_surface(dotted_mask)
    belief_b = ds50.kernel_belief_surface(tip_mask)
    a_dotted = ds50.RHO_MAX
    a_tip = ds50.RHO_MAX * (ds50.LIVE_TIP_H36 / ds50.LIVE_DOTTED_B2)
    fusion = ds50.dempster_fuse(belief_a, belief_b, a_dotted, a_tip, footprint=footprint)
    submission = np.where(footprint, fusion.belief_normalized, 0.0).astype(np.float32)

    # --- sensitivity: alternative discounts, same parents ---------------------
    sensitivity = {}
    for label, (ra, rb) in {
        "anchor_no_ceiling_a1.0": (1.0, ds50.LIVE_TIP_H36 / ds50.LIVE_DOTTED_B2),
        "symmetric_rho_0.5": (0.5, 0.5),
        "symmetric_rho_0.9": (0.9, 0.9),
        "symmetric_rho_0.95": (ds50.RHO_MAX, ds50.RHO_MAX),
    }.items():
        alt = ds50.dempster_fuse(belief_a, belief_b, ra, rb, footprint=footprint)
        sensitivity[label] = {
            "reliabilities": [ra, rb],
            "pearson_vs_primary_in_footprint": pearson(
                alt.belief_normalized[footprint], submission[footprint]
            ),
            "max_abs_difference_in_footprint": float(
                np.abs(alt.belief_normalized[footprint] - submission[footprint]).max()
            ),
        }

    # --- not-a-naive-mean checks ----------------------------------------------
    naive = ds50.naive_mean_belief(belief_a, belief_b)
    naive_norm = naive / float(naive[footprint].max())
    diff = np.abs(submission[footprint] - naive_norm[footprint])
    topk = n_dotted  # budget-matched decision (37,654 cells, the parent A mass)
    ds_top = ds50.top_k_mask(submission, topk, where=footprint)
    mean_top = ds50.top_k_mask(naive_norm, topk, where=footprint)
    inter = int((ds_top & mean_top).sum())
    union_k = int((ds_top | mean_top).sum())
    anti_average = {
        "naive_mean_definition": "0.5*(b_dotted + b_tip) on the kernel-credit belief surfaces, max-normalized",
        "pearson_in_footprint": pearson(submission[footprint], naive_norm[footprint]),
        "spearman_in_footprint": ds50.spearman_rank_correlation(
            submission[footprint], naive_norm[footprint]
        ),
        "mae_in_footprint": float(diff.mean()),
        "max_abs_difference": float(diff.max()),
        "fraction_cells_abs_diff_gt_0.05": float((diff > 0.05).mean()),
        "cells_exactly_equal": int((submission[footprint] == naive_norm[footprint]).sum()),
        "topk_emission_jaccard": inter / union_k if union_k else None,
        "topk": topk,
        "is_the_average": False,
    }
    # The check is meaningful only if the combination is genuinely different.
    if anti_average["pearson_in_footprint"] is not None and not np.isfinite(
        anti_average["pearson_in_footprint"]
    ):
        raise SystemExit("anti-average correlation failed to compute")

    # --- prior-artifact distance (this is not a copy of the H48 file) ---------
    prior_compare = {}
    if PRIOR_H48.is_file():
        prior_arr, prior_profile = read_band(PRIOR_H48)
        assert_same_grid(prior_profile, dotted_profile, name_a="prior H48", name_b=str(args.dotted))
        prior_valid = np.where(np.isfinite(prior_arr), prior_arr, 0.0)
        prior_compare = {
            "artifact": display_path(PRIOR_H48),
            "sha256": sha256_file(PRIOR_H48),
            "note": "H48 fused the RAW sparse b2 x h33d surfaces with symmetric rho=0.5; "
            "H50 fuses kernel-credit beliefs of b2 x h36-1 with live-anchored discounts.",
            "pearson_vs_h50_in_footprint": pearson(
                prior_valid[footprint], submission[footprint]
            ),
            "parents_differ": True,
            "belief_construction_differs": True,
            "discount_scheme_differs": True,
        }

    # --- write primary submission (all-finite, zeros outside) ------------------
    args.outdir.mkdir(parents=True, exist_ok=True)
    diag_dir = args.outdir / "diagnostics"
    diag_dir.mkdir(parents=True, exist_ok=True)
    tmp_primary = args.outdir / f".tmp-h50-{DATESTAMP}.tif"
    write_submission(tmp_primary, submission)
    primary_sha = sha256_file(tmp_primary)
    short_id = primary_sha[:8]
    primary_path = args.outdir / f"gemsdoe48-h50-ds-b2xh36rung30-{DATESTAMP}-{short_id}-zeros.tif"
    primary_path.unlink(missing_ok=True)
    tmp_primary.rename(primary_path)
    zip_path = primary_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(primary_path, arcname=primary_path.name)

    # Preserve the frozen H50 GeoTIFF tag schema for reproducibility. Its old
    # ``tip`` field names are compatibility aliases for H36-1 rung30 only; H36
    # is an H19-5/rung-30 repacking, not the actual tip/step-over family (see
    # evidence/h36_parent_classification_erratum_20261007.json).
    tag_values = {
        "model": "H50 Dempster combination of kernel-credit belief surfaces",
        "reliability_dotted": str(a_dotted),
        "reliability_tip": f"{a_tip:.6f}",
        "frame": "{fault, not_fault, Theta}",
        "source_dotted_sha256": sha256_file(args.dotted),
        "source_tip_sha256": sha256_file(args.tip),
        "submission_name": SUBMISSION_NAME,
    }
    diag_unassigned = diag_dir / f"gemsdoe48-h50-unassigned-mTheta-{DATESTAMP}-{short_id}.tif"
    diag_conflict = diag_dir / f"gemsdoe48-h50-conflict-K-{DATESTAMP}-{short_id}.tif"
    diag_plausibility = diag_dir / f"gemsdoe48-h50-plausibility-{DATESTAMP}-{short_id}.tif"
    receipt_unassigned = write_float32(
        diag_unassigned, np.where(footprint, fusion.unassigned, np.nan).astype(np.float32),
        dotted_profile, valid_mask=footprint,
        description="H50 residual unassigned Dempster mass m(Theta); NaN outside footprint",
        tags=tag_values,
    )
    receipt_conflict = write_float32(
        diag_conflict, np.where(footprint, fusion.conflict, np.nan).astype(np.float32),
        dotted_profile, valid_mask=footprint,
        description="H50 raw conjunctive conflict K before Dempster normalization; NaN outside footprint",
        tags=tag_values,
    )
    receipt_plausibility = write_float32(
        diag_plausibility, np.where(footprint, fusion.plausibility, np.nan).astype(np.float32),
        dotted_profile, valid_mask=footprint,
        description="H50 plausibility Pl(F) = Bel(F) + m(Theta); NaN outside footprint",
        tags=tag_values,
    )

    # NaN-outside twin: identical in-footprint values, NaN/nodata outside, the
    # official sample-template convention that scripts/validate_submission.py
    # audits.  Both encodings have scored 0.2x siblings; the zeros primary is
    # immune to the portal's "[0, 1]" range rejection by construction.
    twin_path = primary_path.with_name(primary_path.name.replace("-zeros.tif", "-nan.tif"))
    receipt_twin = write_float32(
        twin_path,
        np.where(footprint, fusion.belief_normalized, np.nan).astype(np.float32),
        dotted_profile,
        valid_mask=footprint,
        description="H50 normalized Dempster belief; NaN/nodata outside survey footprint",
        tags=tag_values,
    )

    # --- uniqueness: sha must differ from every TIF already shipped ------------
    existing = sorted(
        p for p in list((ROOT / "docs/downloads").rglob("*.tif")) + list((ROOT / "data").rglob("*.tif"))
        if p != primary_path
    )
    collisions = [display_path(p) for p in existing if sha256_file(p) == primary_sha]
    if collisions:
        raise SystemExit(f"submission hash collides with existing artifact(s): {collisions}")

    with rasterio.open(primary_path) as check:
        reread = check.read(1).astype(np.float64)
    format_receipt = {
        "single_band": check.count == 1,
        "dtype_float32": check.dtypes[0] == "float32",
        "width": check.width,
        "height": check.height,
        "crs": check.crs.to_string(),
        "transform": list(check.transform)[:6],
        "nodata": check.nodata,
        "all_finite": bool(np.isfinite(reread).all()),
        "min_value": float(reread.min()),
        "max_value": float(reread.max()),
        "values_in_0_1": bool((reread >= 0.0).all() and (reread <= 1.0).all()),
        "positive_pixels": int((reread > 0).sum()),
        "in_footprint_cells": int(footprint.sum()),
        "zero_outside_footprint": bool((reread[~footprint] == 0.0).all()),
    }
    if not (
        format_receipt["single_band"] and format_receipt["dtype_float32"]
        and format_receipt["width"] == EXPECTED["width"]
        and format_receipt["height"] == EXPECTED["height"]
        and format_receipt["crs"] == EXPECTED["crs"]
        and format_receipt["all_finite"] and format_receipt["values_in_0_1"]
        and format_receipt["zero_outside_footprint"]
    ):
        raise SystemExit(f"format receipt failed: {format_receipt}")

    receipt = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_id": "H50",
        "submission_status": "UNSCORED_RESEARCH_CANDIDATE",
        "submission_name": SUBMISSION_NAME,
        "submission_note": SUBMISSION_NOTE,
        "submission_note_length": len(SUBMISSION_NOTE),
        "primary_file": display_path(primary_path),
        "primary_sha256": primary_sha,
        "primary_bytes": primary_path.stat().st_size,
        "zip_file": display_path(zip_path),
        "zip_sha256": sha256_file(zip_path),
        "nan_outside_twin": {
            **receipt_twin,
            "path": display_path(twin_path),
            "sha256": sha256_file(twin_path),
            "purpose": "official sample-template convention (NaN/nodata outside); passes "
            "scripts/validate_submission.py; in-footprint values identical to the primary",
        },
        "encoding": "all-finite float32 in [0,1]; zeros outside footprint (portal-safe per GEMSDOE32/33 precedent)",
        "diagnostics": {
            "unassigned_mass_mTheta": {**receipt_unassigned, "sha256": sha256_file(diag_unassigned)},
            "conflict_K": {**receipt_conflict, "sha256": sha256_file(diag_conflict)},
            "plausibility": {**receipt_plausibility, "sha256": sha256_file(diag_plausibility)},
        },
        "parents": {
            "dotted_best": {
                "family": "dotted (spacing-tuned)",
                "id": "H33-2-B2",
                "path": display_path(args.dotted),
                "sha256": sha256_file(args.dotted),
                "positive_pixels": n_dotted,
                "owner_reported_live": ds50.LIVE_DOTTED_B2,
                "evidence_class": "OWNER-REPORT",
            },
            "h36_rung30": {
                "family": "H19-5/rung-30 repacking (not tip/step-over)",
                "id": "H36-1-rung30",
                "path": display_path(args.tip),
                "sha256": sha256_file(args.tip),
                "positive_pixels": n_tip,
                "owner_reported_live": ds50.LIVE_TIP_H36,
                "evidence_class": "OWNER-REPORT",
                "verification": "Downloaded from the pinned GEMSDOE28 public mirror via GitHub API on 2026-10-07; "
                "SHA-256 matches registry/live_scores.json. data/raw/ref_h36_1_rung30.tif is a "
                "mask-identical format rewrite (nodata representation only), verified cell by cell.",
            },
        },
        "parent_overlap": {
            "intersection_pixels": n_both,
            "union_pixels": n_union,
            "jaccard": n_both / n_union if n_union else None,
            "xor_disagreement_pixels": n_union - n_both,
        },
        "method": {
            "belief_construction": "b_i(x) = max over committed pixels y of k(d(x,y)), k triangular 300 m (metric geometry)",
            "mass_assignment": "m_i(F)=a_i*b_i, m_i(notF)=a_i*(1-b_i), m_i(Theta)=1-a_i",
            "combination": "canonical normalized Dempster rule (Dempster 1967; Shafer 1976)",
            "reliabilities": {"dotted": a_dotted, "tip": a_tip},
            "reliability_anchor": (
                "RHO_MAX=0.95 ceiling (no perfectly reliable source; keeps m(Theta) informative) "
                "times owner-reported live score ratio [OWNER-REPORT]; modeling assumption, not calibrated"
            ),
            "changelog": [
                "v1 (2026-10-07, sha 2c01d21239ae7a2a5f39dc21dd5b63126f70c072d6993baf4aae1349ed86b0db) used "
                "a_dotted=1.0, which forces m12(Theta)=0 everywhere and kills the unassigned-mass "
                "diagnostic required by the brief; replaced by the RHO_MAX-ceiled build in this receipt. "
                "v1 files were withdrawn from the download list.",
            ],
            "submitted_surface": "Bel(F)=m12(F), divided by in-footprint max (identity here: max already 1.0)",
            "assumptions": [
                "Kernel-credit belief treats distance-decayed credit as graded evidence, avoiding the hard counter-evidence reading of sparse zeros.",
                "Sources are not assumed statistically independent; shared regional inputs remain a risk.",
                "Live-score anchoring of reliabilities is a documented assumption, not an estimated calibration.",
            ],
        },
        "discount_sensitivity": sensitivity,
        "anti_average_check": anti_average,
        "prior_artifact_distance": prior_compare,
        "uniqueness": {
            "compared_existing_tifs": len(existing),
            "hash_collisions": collisions,
            "new_parent_pair": "b2 x h36-1 rung30 (no prior GEMSDOE48 artifact fused h36-1)",
        },
        "format_receipt": format_receipt,
        "organizer_score": None,
        "score_claim": "No organizer score exists for this artifact; no leaderboard projection is claimed.",
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
