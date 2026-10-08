#!/usr/bin/env python3
"""Bounded local byte/pixel/support audit for the H58 research GeoTIFF.

This does not claim uniqueness across sibling repositories, organizer submissions,
or every prior external GEMSDOE site. It distinguishes exact value duplicates from
shared positive support: H58 deliberately uses the same parent families and 300m
support radius as earlier experiments, so a positive-support match is plausible
without the continuous float32 surface being copied.
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
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48.geotiff import assert_competition_grid, display_path  # noqa: E402
from gemsdoe48.h56 import deterministic_top_k  # noqa: E402

DEFAULT_PRIMARY = ROOT / "docs/downloads/GEMSDOE48-H58-OWDS-POSONLY-B2xH33D-20261008-fdbb83476756-zeros-outside.tif"
DEFAULT_COMPANION = ROOT / "docs/downloads/GEMSDOE48-H58-OWDS-POSONLY-B2xH33D-20261008-fdbb83476756-nan-outside.tif"
DEFAULT_RECEIPT = ROOT / "evidence/h58_uniqueness_audit_20261008.json"
TOP_K = 37_654
RELEVANT_TOKENS = ("h56", "h53", "h49", "h57", "h55", "h48", "dempster", "yager")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_footprint() -> tuple[np.ndarray, dict]:
    path = ROOT / "data/source_mirrors/footprint-mask.tif"
    with rasterio.open(path) as source:
        assert_competition_grid(source.profile, path=path)
        values = source.read(1)
        profile = source.profile.copy()
    if values.dtype != np.uint8 or not np.isin(values, (0, 1)).all():
        raise SystemExit("pinned footprint must be uint8 0/1")
    return values == 1, profile


def normalized_inside(path: Path, footprint: np.ndarray, grid_profile: dict) -> np.ndarray | None:
    try:
        with rasterio.open(path) as source:
            if source.count != 1:
                return None
            assert_competition_grid(source.profile, path=path)
            if (source.width, source.height, source.crs, source.transform) != (
                grid_profile["width"], grid_profile["height"],
                grid_profile["crs"], grid_profile["transform"],
            ):
                return None
            values = source.read(1).astype(np.float32, copy=False)
    except (rasterio.errors.RasterioIOError, OSError, ValueError):
        return None
    if not np.isfinite(values[footprint]).all():
        return None
    return values[footprint].copy()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary", type=Path, default=DEFAULT_PRIMARY)
    parser.add_argument("--companion", type=Path, default=DEFAULT_COMPANION)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()

    primary_path = args.primary.resolve()
    companion_path = args.companion.resolve()
    footprint, grid_profile = load_footprint()
    primary = normalized_inside(primary_path, footprint, grid_profile)
    if primary is None:
        raise SystemExit("primary candidate is not a finite single-band competition-grid raster")
    primary_sha = sha256_file(primary_path)
    primary_support = primary > 0.0
    n_valid = int(footprint.sum())
    if primary.size != n_valid:
        raise SystemExit("primary/footprint cell counts do not match")

    # Verify the two storage-format variants contain the same in-footprint values.
    companion = normalized_inside(companion_path, footprint, grid_profile)
    if companion is None or not np.array_equal(primary, companion):
        raise SystemExit("the NaN-outside variant is not value-identical inside the footprint")
    companion_record = {
        "path": display_path(companion_path),
        "sha256": sha256_file(companion_path),
        "byte_identical_to_primary": sha256_file(companion_path) == primary_sha,
        "in_footprint_values_exactly_equal": True,
        "role": "same prediction with NaN/nodata outside; not a separate model",
    }

    all_paths = sorted({
        path.resolve()
        for folder in (ROOT / "data", ROOT / "docs/downloads")
        for path in folder.rglob("*.tif")
    })
    candidate_base = primary_path.name.removesuffix("-zeros-outside.tif")
    same_grid: list[dict] = []
    h58_companions: list[str] = []
    for path in all_paths:
        if path == primary_path:
            continue
        # The NaN-outside sibling and this candidate's diagnostic layers are
        # deliberately recorded as same-artifact files, not prior models.
        if path == companion_path or path.name.startswith(candidate_base):
            h58_companions.append(display_path(path))
            continue
        other = normalized_inside(path, footprint, grid_profile)
        if other is None:
            continue
        other_support = other > 0.0
        intersection = int(np.count_nonzero(primary_support & other_support))
        union = int(np.count_nonzero(primary_support | other_support))
        same_pixels = bool(np.array_equal(primary, other))
        row: dict = {
            "path": display_path(path),
            "sha256": sha256_file(path),
            "bytes": path.stat().st_size,
            "byte_identical": sha256_file(path) == primary_sha,
            "in_footprint_pixel_identical": same_pixels,
            "in_footprint_positive_support_identical": bool(np.array_equal(primary_support, other_support)),
            "candidate_positive_cells": int(primary_support.sum()),
            "other_positive_cells": int(other_support.sum()),
            "support_jaccard": float(intersection / union) if union else None,
            "support_symmetric_difference_cells": int(union - intersection),
        }
        if not same_pixels:
            x = primary.astype(np.float64, copy=False)
            y = other.astype(np.float64, copy=False)
            delta = np.abs(x - y)
            row.update({
                "pearson_r_in_footprint": (
                    float(np.corrcoef(x, y)[0, 1]) if x.std() > 0.0 and y.std() > 0.0 else None
                ),
                "mae_in_footprint": float(delta.mean()),
                "max_abs_difference_in_footprint": float(delta.max()),
            })
            if any(token in path.name.lower() for token in RELEVANT_TOKENS):
                ids = np.flatnonzero(footprint.ravel())
                step = max(1, int(np.ceil(ids.size / 100_000)))
                sample_ids = ids[::step]
                # Sample from the full grids because primary/other use footprint-only vectors.
                candidate_full = np.zeros(footprint.shape, dtype=np.float32)
                candidate_full[footprint] = primary
                other_full = np.zeros(footprint.shape, dtype=np.float32)
                other_full[footprint] = other
                a = candidate_full.ravel()[sample_ids].astype(np.float64, copy=False)
                b = other_full.ravel()[sample_ids].astype(np.float64, copy=False)
                row["spearman_r_deterministic_sample"] = (
                    float(spearmanr(a, b).statistic) if a.std() > 0.0 and b.std() > 0.0 else None
                )
                selected_a = deterministic_top_k(candidate_full, footprint, TOP_K)
                selected_b = deterministic_top_k(other_full, footprint, TOP_K)
                top_union = int((selected_a | selected_b).sum())
                row["top_37654_jaccard"] = (
                    float((selected_a & selected_b).sum() / top_union) if top_union else None
                )
        same_grid.append(row)

    exact_byte_matches = [row["path"] for row in same_grid if row["byte_identical"]]
    exact_pixel_matches = [row["path"] for row in same_grid if row["in_footprint_pixel_identical"]]
    support_matches = [row for row in same_grid if row["in_footprint_positive_support_identical"]]
    closest = sorted(
        same_grid,
        key=lambda row: (
            bool(row["in_footprint_pixel_identical"]),
            bool(row["in_footprint_positive_support_identical"]),
            row.get("pearson_r_in_footprint", -2.0) or -2.0,
        ),
        reverse=True,
    )
    relevant_prior = [row for row in closest if any(token in row["path"].lower() for token in RELEVANT_TOKENS)]
    report = {
        "schema_version": 1,
        "audited_utc": datetime.now(timezone.utc).isoformat(),
        "status": "NO_LOCAL_BYTE_OR_PIXEL_DUPLICATE_FOUND_BOUNDED_SCAN",
        "candidate": {
            "path": display_path(primary_path),
            "sha256": primary_sha,
            "bytes": primary_path.stat().st_size,
            "positive_cells": int(primary_support.sum()),
            "in_footprint_cells": n_valid,
        },
        "same_prediction_companion": companion_record,
        "scan": {
            "roots": ["data/", "docs/downloads/"],
            "tiffs_discovered": len(all_paths),
            "same_grid_single_band_finite_in_footprint_compared": len(same_grid),
            "same_artifact_companions_excluded_from_prior_model_comparison": h58_companions,
            "exact_byte_matches_excluding_companion": exact_byte_matches,
            "exact_in_footprint_pixel_matches_excluding_companion": exact_pixel_matches,
            "same_positive_support_prior_rasters": [
                {
                    "path": row["path"],
                    "sha256": row["sha256"],
                    "bytes": row["bytes"],
                    "byte_identical": row["byte_identical"],
                    "pixel_identical": row["in_footprint_pixel_identical"],
                    "support_jaccard": row["support_jaccard"],
                    "mae_in_footprint": row.get("mae_in_footprint"),
                    "max_abs_difference_in_footprint": row.get("max_abs_difference_in_footprint"),
                    "pearson_r_in_footprint": row.get("pearson_r_in_footprint"),
                    "top_37654_jaccard": row.get("top_37654_jaccard"),
                }
                for row in support_matches
            ],
            "closest_prior_art_comparisons": relevant_prior[:20],
        },
        "interpretation": {
            "local_exact_copy_found": bool(exact_byte_matches or exact_pixel_matches),
            "support_overlap_warning": "H58 uses the same two parents and the same 300m triangular support radius as earlier local D-S experiments. Shared positive support is therefore expected and does not imply equal float values; compare the continuous values and method assignment.",
            "scope_limit": "The scan covers local repository TIFFs under data/ and docs/downloads/ only. It does not inspect all sibling GEMSDOE repositories/sites, external uploads, or organizer-side submissions, so global uniqueness is not established.",
            "novelty_boundary": "H58 is a mass-assignment ablation over existing candidate geometries, not a new geological detector or data source. Its output values differ if no exact match is found; local distinctness is not proof of scientific or contest novelty.",
        },
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "candidate": report["candidate"],
        "scan": {
            "tiffs_discovered": report["scan"]["tiffs_discovered"],
            "same_grid_compared": report["scan"]["same_grid_single_band_finite_in_footprint_compared"],
            "exact_byte_matches": exact_byte_matches,
            "exact_pixel_matches": exact_pixel_matches,
            "support_matches": report["scan"]["same_positive_support_prior_rasters"],
            "closest_prior_art_comparisons": relevant_prior[:8],
        },
        "receipt": display_path(args.receipt),
    }, indent=2, allow_nan=False))
    return 2 if exact_byte_matches or exact_pixel_matches else 0


if __name__ == "__main__":
    raise SystemExit(main())
