#!/usr/bin/env python3
"""Build the unique GEMSDOE48 discounted-Dempster research candidate and diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

from gemsdoe48.evidence import arithmetic_mean, combine_dempster
from gemsdoe48.geotiff import assert_competition_grid, assert_same_grid, display_path, read_band, write_float32

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DOTTED = ROOT / "data/source_mirrors/gemsdoe32-h33-h33-2-b2.tif"
DEFAULT_TIP = ROOT / "data/source_mirrors/GEMSDOE33-h33d-tip-stepover.tif"
DEFAULT_FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
DEFAULT_OUTPUT = ROOT / "docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif"
DEFAULT_UNCERTAINTY = ROOT / "docs/downloads/GEMSDOE48-unassigned-mass-20261006.tif"
DEFAULT_CONFLICT = ROOT / "docs/downloads/GEMSDOE48-raw-conflict-K-20261006.tif"
DEFAULT_RECEIPT = ROOT / "evidence/build_receipt_20261006.json"
SUBMISSION_NAME = "GEMSDOE48-DS-FUSION-20261006"
PREREGISTERED_RHO = 0.5
EXPECTED_INPUTS = {
    "dotted": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "tip_stepover": "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
}
SUBMISSION_NOTE = (
    "GEMSDOE48 DS fusion | H33-2-B2 dotted + H33-D tip/step-over; rho=0.5; "
    "conflict/ignorance diagnostic; unscored research candidate."
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def correlation(x: np.ndarray, y: np.ndarray) -> float | None:
    x = np.asarray(x, dtype=np.float64).ravel()
    y = np.asarray(y, dtype=np.float64).ravel()
    if x.size < 2 or np.std(x) == 0 or np.std(y) == 0:
        return None
    return float(np.corrcoef(x, y)[0, 1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dotted", type=Path, default=DEFAULT_DOTTED)
    parser.add_argument("--tip", type=Path, default=DEFAULT_TIP)
    parser.add_argument("--footprint", type=Path, default=DEFAULT_FOOTPRINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--uncertainty", type=Path, default=DEFAULT_UNCERTAINTY)
    parser.add_argument("--conflict", type=Path, default=DEFAULT_CONFLICT)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--allow-unpinned-sources", action="store_true")
    args = parser.parse_args()

    dotted_hash = sha256_file(args.dotted)
    tip_hash = sha256_file(args.tip)
    if not args.allow_unpinned_sources:
        if dotted_hash != EXPECTED_INPUTS["dotted"]:
            raise SystemExit(f"Dotted input SHA-256 {dotted_hash} is not the preregistered source")
        if tip_hash != EXPECTED_INPUTS["tip_stepover"]:
            raise SystemExit(f"Tip/stepover input SHA-256 {tip_hash} is not the preregistered source")

    dotted, dotted_profile = read_band(args.dotted)
    tip, tip_profile = read_band(args.tip)
    assert_competition_grid(dotted_profile, path=args.dotted)
    assert_competition_grid(tip_profile, path=args.tip)
    assert_same_grid(dotted_profile, tip_profile, name_a=str(args.dotted), name_b=str(args.tip))
    with rasterio.open(args.footprint) as fp_ds:
        assert_competition_grid(fp_ds.profile, path=args.footprint)
        footprint_raw = fp_ds.read(1)
        footprint_profile = fp_ds.profile.copy()
    if footprint_raw.dtype != np.uint8:
        raise ValueError("footprint mask must be uint8")
    if not np.isin(footprint_raw, (0, 1)).all():
        raise ValueError("footprint mask must contain only 0/1")
    if dotted.shape != tip.shape or dotted.shape != footprint_raw.shape:
        raise ValueError("source surfaces and footprint mask have different dimensions")
    if not np.isfinite(dotted).all() or not np.isfinite(tip).all():
        raise ValueError("source surfaces must be all-finite")
    if np.any((dotted < 0) | (dotted > 1)) or np.any((tip < 0) | (tip > 1)):
        raise ValueError("source surfaces contain values outside [0, 1]")

    footprint = footprint_raw == 1
    dotted_inside = np.where(footprint, dotted, 0.0).astype(np.float32)
    tip_inside = np.where(footprint, tip, 0.0).astype(np.float32)
    result = combine_dempster(dotted_inside, tip_inside, reliability=PREREGISTERED_RHO)
    mean = arithmetic_mean(dotted_inside, tip_inside)

    # Match the official template convention: all cells outside the valid survey
    # footprint are NaN/nodata, not zero-valued predictions.
    submission = np.where(footprint, result.fault, np.nan).astype(np.float32)
    unassigned = np.where(footprint, result.ignorance, np.nan).astype(np.float32)
    conflict = np.where(footprint, result.conflict, np.nan).astype(np.float32)

    tag_values = {
        "model": "discounted Dempster combination",
        "reliability_discount": str(PREREGISTERED_RHO),
        "frame": "{fault, not_fault, Theta}",
        "source_dotted_sha256": sha256_file(args.dotted),
        "source_tip_sha256": sha256_file(args.tip),
        "footprint_mask_sha256": sha256_file(args.footprint),
        "submission_name": SUBMISSION_NAME,
    }
    out_receipts = {
        "submission": write_float32(
            args.output, submission, dotted_profile, valid_mask=footprint,
            description="Dempster combined fault belief m(F); in-footprint values in [0,1]",
            tags=tag_values,
        ),
        "unassigned": write_float32(
            args.uncertainty, unassigned, dotted_profile, valid_mask=footprint,
            description="Dempster residual unassigned mass m(Theta); NaN outside survey footprint",
            tags=tag_values,
        ),
        "raw_conflict": write_float32(
            args.conflict, conflict, dotted_profile, valid_mask=footprint,
            description="Raw conjunctive Dempster conflict K before normalization; NaN outside footprint",
            tags=tag_values,
        ),
    }

    valid_mean = mean[footprint]
    valid_combined = submission[footprint]
    union = footprint & ((dotted_inside > 0) | (tip_inside > 0))
    difference = np.abs(valid_combined - valid_mean)
    union_difference = np.abs(submission[union] - mean[union])
    overlap = footprint & (dotted_inside > 0) & (tip_inside > 0)
    disagree = footprint & ((dotted_inside > 0) ^ (tip_inside > 0))
    dotted_positive = int(np.count_nonzero(footprint & (dotted_inside > 0)))
    tip_positive = int(np.count_nonzero(footprint & (tip_inside > 0)))
    overlap_count = int(overlap.sum())
    union_count = int(union.sum())
    agreement_ratio = float(overlap_count / union_count) if union_count else 0.0
    if len(SUBMISSION_NOTE) > 200:
        raise ValueError("submission note exceeds the form's 200-character limit")

    receipt = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "submission_status": "UNSCORED_RESEARCH_CANDIDATE_NOT_SLOT_CLEARED",
        "submission_name": SUBMISSION_NAME,
        "submission_note": SUBMISSION_NOTE,
        "submission_note_length": len(SUBMISSION_NOTE),
        "submission_file": out_receipts["submission"],
        "submission_sha256": sha256_file(args.output),
        "diagnostic_files": {
            "unassigned_mass": {**out_receipts["unassigned"], "sha256": sha256_file(args.uncertainty)},
            "raw_conflict_K": {**out_receipts["raw_conflict"], "sha256": sha256_file(args.conflict)},
        },
        "inputs": {
            "dotted": {"path": display_path(args.dotted), "sha256": sha256_file(args.dotted), "positive_pixels_inside_footprint": dotted_positive},
            "tip_stepover": {"path": display_path(args.tip), "sha256": sha256_file(args.tip), "positive_pixels_inside_footprint": tip_positive},
            "footprint_mask": {"path": display_path(args.footprint), "sha256": sha256_file(args.footprint), "valid_cells": int(footprint.sum())},
        },
        "grid": {
            "crs": "EPSG:32611",
            "resolution_m": 100,
            "height": int(submission.shape[0]),
            "width": int(submission.shape[1]),
            "transform": list(dotted_profile["transform"])[:6],
        },
        "evidence_combination": {
            "rule": "Canonical Dempster combination after symmetric reliability discounting",
            "reliability_discount_rho": PREREGISTERED_RHO,
            "source_mass": {"m_fault": "rho*p", "m_not_fault": "rho*(1-p)", "m_Theta": "1-rho"},
            "combined_fault": "m(F) after normalized Dempster rule",
            "unassigned_layer": "normalized residual m(Theta) within footprint; NaN/nodata outside survey footprint",
            "raw_conflict_layer": "K=m1(F)m2(not_F)+m1(not_F)m2(F), before Dempster normalization",
            "assumptions": [
                "The owner-mirror input surfaces are binary sparse emissions; interpreting zero as evidence for not-fault is a modeling assumption, not calibrated probability semantics.",
                "rho=0.5 is a fixed symmetric discount chosen before holdout, not an empirically estimated source reliability.",
                "The sources are not assumed statistically independent; shared-backbone risk remains.",
            ],
            "range_normalization": "No min-max stretch; masses are already in [0,1] and are preserved.",
        },
        "anti_average_check": {
            "arithmetic_mean_equal_to_combination": bool(np.array_equal(mean[footprint], submission[footprint])),
            "different_cells_within_footprint": int(np.count_nonzero(mean[footprint] != submission[footprint])),
            "pearson_full_footprint": correlation(valid_mean, valid_combined),
            "pearson_on_union_only": correlation(mean[union], submission[union]),
            "mae_full_footprint": float(difference.mean()) if difference.size else 0.0,
            "mae_on_union_only": float(union_difference.mean()) if union_difference.size else 0.0,
            "max_abs_difference": float(difference.max()) if difference.size else 0.0,
            "note": "Because both source masks are binary and sparse, the union-only Pearson correlation is structurally uninformative; exact inequality, MAE, mass values, and conflict counts are reported as well.",
        },
        "surface_overlap": {
            "intersection_cells": overlap_count,
            "union_cells": union_count,
            "xor_disagreement_cells": int(disagree.sum()),
            "intersection_over_union": agreement_ratio,
            "dotted_fraction_also_in_tip": float(overlap_count / dotted_positive) if dotted_positive else 0.0,
            "tip_fraction_also_in_dotted": float(overlap_count / tip_positive) if tip_positive else 0.0,
        },
        "organizer_score": None,
        "score_claim": "No organizer score exists for this artifact. No projected leaderboard score is reported.",
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
