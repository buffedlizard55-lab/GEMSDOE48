#!/usr/bin/env python3
"""Build H58-A: positive-only Dempster fusion of B2 dotted × H33-D tip.

This is a new, locally unique research candidate—not a copied prior TIFF and
not an authorization to submit. Sparse non-emission is treated as uncommitted
mass, not evidence of no-fault. The parent sources, support transform, mass
assignment, and output hashes are recorded in evidence/build_h58_receipt_20261008.json.

Run after reading the complete project README:
    .venv/bin/python scripts/build_submission_h58.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48.geotiff import (  # noqa: E402
    assert_competition_grid,
    assert_same_grid,
    display_path,
    write_float32,
    write_float32_zeros_outside,
)
from gemsdoe48.h56 import deterministic_top_k  # noqa: E402
from gemsdoe48.open_world_ds import (  # noqa: E402
    combine_positive_simple_supports,
    normalize_relative_belief,
)

INPUTS = {
    "dotted_b2": {
        "path": ROOT / "data/families/dotted_b2_prune_02778.tif",
        "sha256": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
        "family": "GEMSDOE32 H33-2-B2 spacing-tuned dotted",
        "owner_reported_score": 0.2778,
        "score_identity_status": "not organizer-verified for these exact local bytes; source receipt says UNSCORED",
        "source_url": "https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html",
    },
    "tip_h33d": {
        "path": ROOT / "data/families/tip_stepover_r30_02632.tif",
        "sha256": "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
        "family": "GEMSDOE33 H33-D analog tip/step-over",
        "owner_reported_score": 0.2632,
        "score_identity_status": "owner-reported family/file association; no organizer receipt links these exact bytes to a score",
        "source_url": "https://buffedlizard55-lab.github.io/GEMSDOE33/",
    },
    "footprint": {
        "path": ROOT / "data/source_mirrors/footprint-mask.tif",
        "sha256": "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
        "source_url": "local mask derived from the owner-mirrored sample_submission_template.tif; not organizer-authenticated",
    },
    "template": {
        "path": ROOT / "data/raw/sample_submission_template.tif",
        "sha256": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
        "source_url": "https://www.drivendata.org/competitions/306/competition-doe-gems/data/",
        "provenance": "owner mirror; not organizer-authenticated",
    },
}
ALPHA_DOTTED = 0.60
ALPHA_TIP = 0.60
RADIUS_M = 300.0
PIXEL_SIZE_M = 100.0
TOP_K = 37_654


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def read_single_band(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as dataset:
        if dataset.count != 1:
            raise ValueError(f"{path}: expected a single-band raster, got {dataset.count}")
        assert_competition_grid(dataset.profile, path=path)
        return dataset.read(1), dataset.profile.copy()


def support_from_mask(mask: np.ndarray) -> np.ndarray:
    """Apply the official 300 m triangular metric kernel on the 100 m grid."""
    dots = np.asarray(mask, dtype=bool)
    if dots.ndim != 2 or not dots.any():
        raise ValueError("source mask must be a nonempty 2-D array")
    distance_m = ndi.distance_transform_edt(~dots, sampling=(PIXEL_SIZE_M, PIXEL_SIZE_M))
    support = np.maximum(1.0 - distance_m / RADIUS_M, 0.0).astype(np.float32)
    if not np.isfinite(support).all() or np.any((support < 0.0) | (support > 1.0)):
        raise ArithmeticError("metric support escaped finite [0,1]")
    return support


def correlation_record(candidate: np.ndarray, reference: np.ndarray, footprint: np.ndarray) -> dict:
    """Compare value identity and rank association on the finite competition area."""
    x = candidate[footprint].astype(np.float64, copy=False)
    y = reference[footprint].astype(np.float64, copy=False)
    difference = np.abs(x - y)
    if x.std() == 0.0 or y.std() == 0.0:
        pearson = None
    else:
        pearson = float(np.corrcoef(x, y)[0, 1])

    ids = np.flatnonzero(footprint.ravel())
    step = max(1, int(math.ceil(ids.size / 100_000)))
    sample_ids = ids[::step]
    sample_candidate = candidate.ravel()[sample_ids].astype(np.float64, copy=False)
    sample_reference = reference.ravel()[sample_ids].astype(np.float64, copy=False)
    if sample_candidate.std() == 0.0 or sample_reference.std() == 0.0:
        spearman = None
    else:
        spearman = float(spearmanr(sample_candidate, sample_reference).statistic)

    k = min(TOP_K, int(footprint.sum()))
    left = deterministic_top_k(candidate, footprint, k)
    right = deterministic_top_k(reference, footprint, k)
    intersection = int((left & right).sum())
    union = int((left | right).sum())
    return {
        "definition": "candidate versus the stated naive arithmetic mean, footprint cells only",
        "pixelwise_identical": bool(np.array_equal(x, y)),
        "pearson_r_all_footprint_cells": pearson,
        "spearman_r_deterministic_sample": spearman,
        "spearman_sample_cells": int(sample_ids.size),
        "footprint_mae": float(difference.mean()),
        "footprint_max_abs_difference": float(difference.max()),
        "fraction_footprint_abs_difference_gt_0_05": float((difference > 0.05).mean()),
        "top_37654_rank_jaccard": float(intersection / union) if union else None,
    }


def save_zip_deterministic(zip_path: Path, tif_path: Path) -> None:
    """Write a one-TIFF zip with fixed metadata so repeated builds are byte-stable."""
    info = zipfile.ZipInfo(tif_path.name, date_time=(1980, 1, 1, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o600 << 16
    with zipfile.ZipFile(zip_path, "w") as archive:
        archive.writestr(info, tif_path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=ROOT / "docs/downloads")
    parser.add_argument("--force", action="store_true", help="replace an existing H58 artifact with identical recipe output")
    args = parser.parse_args()
    output_dir = args.output_dir.resolve()
    diagnostic_dir = output_dir / "diagnostics"
    receipt_path = ROOT / "evidence/build_h58_receipt_20261008.json"

    receipt: dict = {
        "schema_version": 1,
        "session": "H58-A",
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BUILT_LOCAL_FORMAT_VALIDATION_PASSED_NOT_PORTAL_TESTED",
        "decision": "Research-only artifact; the separate preregistered blocked-proxy gate failed, so do not spend a weekly submission slot. Neither local format checks nor proxy scores establish organizer acceptance or private-label performance.",
        "hypothesis_slate": "docs/research/hypotheses-h58-20261008.md",
        "frozen_slate_receipt": "evidence/hypothesis_slate_h58_20261008.json",
        "recipe": {
            "metric_support": "s_i(x)=max(1-EuclideanDistance(x,D_i)/300m,0), pixel size 100m",
            "alpha_dotted": ALPHA_DOTTED,
            "alpha_tip": ALPHA_TIP,
            "mass_assignment_each_source": {
                "m_fault": "alpha * support",
                "m_not_fault": 0.0,
                "m_theta": "1 - alpha * support",
            },
            "combination": "normalized Dempster rule; K is identically zero for this positive-only assignment",
            "unassigned_semantics": "m(Theta) is residual ignorance, not a direct disagreement map",
            "direct_disagreement_diagnostic": "absolute difference between the two 300m support surfaces; not a D-S mass",
            "primary": "Bel(F) divided by the footprint maximum; relative favorability, not a calibrated probability",
            "outside_encoding": "two clearly labelled variants are exported: finite zero outside is robust to a raw all-cell [0,1] check but differs from the official problem page's null/NaN outside convention; the NaN/nodata variant matches the published convention but can fail a naive unmasked range check. Neither variant has been tested in the organizer portal.",
            "parameters_are_calibrated": False,
            "source_independence_established": False,
        },
        "inputs": {},
    }

    # Verify byte pins and grid metadata before using any raster values.
    for key, metadata in INPUTS.items():
        path = Path(metadata["path"])
        if not path.exists():
            raise SystemExit(f"missing pinned input {path}")
        actual_sha = sha256_file(path)
        if actual_sha != metadata["sha256"]:
            raise SystemExit(f"SHA-256 mismatch for {key}: expected {metadata['sha256']}, got {actual_sha}")
        receipt["inputs"][key] = {
            **metadata,
            "path": display_path(path),
            "bytes": path.stat().st_size,
            "sha256_verified": True,
        }

    template, template_profile = read_single_band(Path(INPUTS["template"]["path"]))
    footprint_raw, footprint_profile = read_single_band(Path(INPUTS["footprint"]["path"]))
    footprint = footprint_raw == 1
    if footprint_raw.dtype != np.uint8 or not np.isin(footprint_raw, (0, 1)).all():
        raise SystemExit("footprint must be a uint8 mask containing only 0/1")
    if not np.array_equal(np.isfinite(template), footprint):
        raise SystemExit("template finite mask does not equal the pinned footprint mask")
    assert_same_grid(template_profile, footprint_profile, name_a="template", name_b="footprint")
    if not footprint.any():
        raise SystemExit("footprint mask is empty")

    parent_masks: dict[str, np.ndarray] = {}
    for key in ("dotted_b2", "tip_h33d"):
        band, profile = read_single_band(Path(INPUTS[key]["path"]))
        assert_same_grid(template_profile, profile, name_a="template", name_b=key)
        if not np.isfinite(band).all() or np.any((band < 0.0) | (band > 1.0)):
            raise SystemExit(f"{key} contains nonfinite or out-of-range values")
        if not np.all((band == 0.0) | (band == 1.0)):
            raise SystemExit(f"{key} is not the expected binary candidate mask")
        mask = (band > 0.0) & footprint
        outside_positives = int(np.count_nonzero((band > 0.0) & ~footprint))
        if outside_positives:
            raise SystemExit(f"{key} has {outside_positives} positive cells outside the footprint")
        parent_masks[key] = mask

    dotted_mask = parent_masks["dotted_b2"]
    tip_mask = parent_masks["tip_h33d"]
    counts = {
        "dotted_positive_cells": int(dotted_mask.sum()),
        "tip_positive_cells": int(tip_mask.sum()),
        "intersection_cells": int((dotted_mask & tip_mask).sum()),
        "union_cells": int((dotted_mask | tip_mask).sum()),
        "dotted_only_cells": int((dotted_mask & ~tip_mask).sum()),
        "tip_only_cells": int((tip_mask & ~dotted_mask).sum()),
        "footprint_cells": int(footprint.sum()),
        "positive_mask_jaccard": float((dotted_mask & tip_mask).sum() / (dotted_mask | tip_mask).sum()),
    }
    receipt["parent_counts"] = counts

    support_dot = support_from_mask(dotted_mask)
    support_tip = support_from_mask(tip_mask)
    combined = combine_positive_simple_supports(
        support_dot, support_tip, ALPHA_DOTTED, ALPHA_TIP
    )
    raw_belief = combined.belief_fault
    mtheta = combined.ignorance
    conflict = combined.conflict
    support_difference = np.abs(support_dot - support_tip).astype(np.float32)
    primary = normalize_relative_belief(raw_belief, footprint)

    # Explicit equality/correlation checks against both definitions of a naive mean.
    binary_mean = (0.5 * (dotted_mask.astype(np.float32) + tip_mask.astype(np.float32))).astype(np.float32)
    kernel_mean = (0.5 * (support_dot + support_tip)).astype(np.float32)
    kernel_mean_max = float(kernel_mean[footprint].max())
    if kernel_mean_max <= 0.0:
        raise SystemExit("naive kernel mean has no in-footprint support")
    normalized_kernel_mean = np.zeros(kernel_mean.shape, dtype=np.float32)
    normalized_kernel_mean[footprint] = kernel_mean[footprint] / np.float32(kernel_mean_max)
    not_the_average = {
        "vs_binary_parent_mean": correlation_record(primary, binary_mean, footprint),
        "vs_normalized_metric_support_mean": correlation_record(primary, normalized_kernel_mean, footprint),
        "primary_identical_to_binary_parent_mean": bool(np.array_equal(primary[footprint], binary_mean[footprint])),
        "primary_identical_to_normalized_metric_support_mean": bool(np.array_equal(primary[footprint], normalized_kernel_mean[footprint])),
        "interpretation": "Correlation/inequality is a construction check, not evidence of improved fault prediction. High correlation is possible because the parent maps overlap and share spatial geometry.",
    }
    receipt["not_the_naive_average"] = not_the_average

    def stats(layer: np.ndarray) -> dict:
        values = layer[footprint]
        return {
            "minimum_inside_footprint": float(values.min()),
            "maximum_inside_footprint": float(values.max()),
            "mean_inside_footprint": float(values.mean(dtype=np.float64)),
            "positive_cells_inside_footprint": int(np.count_nonzero(values > 0.0)),
            "all_finite_inside_footprint": bool(np.isfinite(values).all()),
        }

    mass_error = float(np.max(np.abs(
        raw_belief[footprint] + combined.belief_not_fault[footprint] + mtheta[footprint] - 1.0
    )))
    if mass_error > 2e-6:
        raise SystemExit(f"combined D-S masses do not sum to one; max error={mass_error}")
    receipt["layers"] = {
        "raw_belief_fault": {**stats(raw_belief), "meaning": "unnormalized combined Bel(F); not a calibrated probability"},
        "primary_relative_belief": {**stats(primary), "meaning": "raw Bel(F) divided by the footprint maximum"},
        "residual_m_theta": {**stats(mtheta), "meaning": "unassigned/ignorance mass; not a direct disagreement map"},
        "raw_conflict_K": {**stats(conflict), "meaning": "pre-normalization D-S conflict; identically zero because m(N)=0 in both sources"},
        "absolute_support_difference": {**stats(support_difference), "meaning": "direct difference between dotted and tip 300m supports; not a D-S mass"},
        "maximum_mass_sum_absolute_error": mass_error,
    }

    content_id = sha256_bytes(np.ascontiguousarray(primary, dtype=np.float32).tobytes())[:12]
    base_name = f"GEMSDOE48-H58-OWDS-POSONLY-B2xH33D-20261008-{content_id}"
    primary_path = output_dir / f"{base_name}-zeros-outside.tif"
    nan_variant_path = output_dir / f"{base_name}-nan-outside.tif"
    zip_path = output_dir / f"{base_name}-zeros-outside.zip"
    output_dir.mkdir(parents=True, exist_ok=True)
    diagnostic_dir.mkdir(parents=True, exist_ok=True)
    diag_paths = {
        "raw_belief": diagnostic_dir / f"{base_name}-belief-raw.tif",
        "m_theta": diagnostic_dir / f"{base_name}-unassigned-mtheta.tif",
        "conflict_k": diagnostic_dir / f"{base_name}-conflict-k.tif",
        "support_difference": diagnostic_dir / f"{base_name}-support-difference.tif",
    }
    planned = [primary_path, nan_variant_path, zip_path, *diag_paths.values()]
    existing = [path for path in planned if path.exists()]
    if existing and not args.force:
        raise SystemExit(f"refusing to overwrite H58 artifact; pass --force: {existing[0]}")

    tags = {
        "candidate": base_name,
        "method": "positive-only simple-support Dempster-Shafer fusion",
        "inputs": "H33-2-B2 dotted; H33-D tip-step-over",
        "alpha_dotted": str(ALPHA_DOTTED),
        "alpha_tip": str(ALPHA_TIP),
        "support_kernel": "max(1-distance/300m,0), 100m grid",
        "outside_encoding": "finite zero; no nodata tag; range-check workaround, not the official null/NaN outside convention", 
        "status": "research-only; not slot-cleared",
    }
    primary_format = write_float32_zeros_outside(
        primary_path,
        primary,
        template_profile,
        valid_mask=footprint,
        description="H58 relative positive-only Dempster belief Bel(F)",
        tags=tags,
    )
    nan_variant = primary.copy()
    nan_variant[~footprint] = np.nan
    nan_tags = {
        **tags,
        "outside_encoding": "NaN/nodata outside; matches published problem-page convention",
        "portal_range_caveat": "a raw unmasked all-cell [0,1] check may reject NaN outside",
    }
    nan_variant_format = write_float32(
        nan_variant_path,
        nan_variant,
        template_profile,
        valid_mask=footprint,
        description="H58 relative positive-only Dempster belief Bel(F); NaN/nodata outside",
        tags=nan_tags,
    )
    nan_variant_receipt = {
        **nan_variant_format,
        "path": display_path(nan_variant_path),
        "sha256": sha256_file(nan_variant_path),
        "outside_convention_matches_published_problem_page": True,
        "portal_range_error_immune": False,
        "local_portal_acceptance_tested": False,
    }
    diagnostics = {}
    diagnostic_layers = {
        "raw_belief": (raw_belief, "H58 unnormalized combined D-S Bel(F)"),
        "m_theta": (mtheta, "H58 residual D-S unassigned ignorance mass m(Theta)"),
        "conflict_k": (conflict, "H58 raw D-S conjunctive conflict K; identically zero for positive-only masses"),
        "support_difference": (support_difference, "H58 absolute dotted-tip support difference; not a D-S mass"),
    }
    for key, (values, description) in diagnostic_layers.items():
        record = write_float32_zeros_outside(
            diag_paths[key],
            values,
            template_profile,
            valid_mask=footprint,
            description=description,
            tags={**tags, "layer": key, "is_submission": "false"},
        )
        record["sha256"] = sha256_file(diag_paths[key])
        record["is_submission"] = False
        diagnostics[key] = record

    save_zip_deterministic(zip_path, primary_path)
    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        if names != [primary_path.name]:
            raise SystemExit(f"zip must contain exactly one GeoTIFF; got {names}")

    receipt["candidate"] = {
        "id": "H58-A",
        "unique_name": base_name,
        "paste_ready_portal_note": "H58 positive-only D-S (alpha=0.60), B2 x H33-D; separate mTheta/K/support-difference diagnostics; proxy gate failed, research only—not cleared to submit.", 
        "content_id": content_id,
        "content_id_definition": "first 12 hex characters of SHA-256 of the C-order float32 primary array bytes (including zero outside cells)",
        "primary": {
            **primary_format,
            "path": display_path(primary_path),
            "sha256": sha256_file(primary_path),
            "is_single_band_tif": True,
            "whole_grid_values_finite_in_0_1": True,
        },
        "zip": {
            "path": display_path(zip_path),
            "bytes": zip_path.stat().st_size,
            "sha256": sha256_file(zip_path),
            "contains_exactly_one_tif": True,
            "is_single_band_tif": True,
        },
        "published_format_alternative": nan_variant_receipt,
        "portal_acceptance_tested": False,
        "download_authorized": True,
        "submission_authorized": False,
        "format_choice_note": "The all-finite zero-outside TIFF addresses a naive raw-array range check but is not the official problem-page outside-bounds convention. The NaN-outside TIFF matches the published convention but is not guaranteed to pass an unmasked portal range check. No actual portal upload was made; user-reported failure cause remains unconfirmed.",
        "diagnostics": diagnostics,
        "diagnostics_are_submission_candidates": False,
    }
    receipt["status"] = "BUILT_LOCAL_FORMAT_VALIDATION_PASSED_NOT_PORTAL_TESTED"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, allow_nan=False) + "\n", encoding="utf-8")

    print(json.dumps({
        "status": receipt["status"],
        "candidate": receipt["candidate"],
        "parent_counts": counts,
        "layers": receipt["layers"],
        "not_the_naive_average": not_the_average,
        "receipt": display_path(receipt_path),
    }, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
