#!/usr/bin/env python3
"""Audit H56B byte and in-footprint pixel uniqueness against local rasters.

The output is a continuous surface, so equal positive support is reported as an
overlap fact, not automatically treated as byte/pixel identity. This local search
cannot establish uniqueness outside the checked repository or against organizer
submissions.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
PRIMARY = ROOT / "docs/downloads/GEMSDOE48-H56B-ds-belief-dotted-x-tip-20261007-126ca59c2801-nan-outside.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
OUT = ROOT / "evidence/h56b_uniqueness_audit_20261007.json"
TOP_K = 37_654


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary", type=Path, default=PRIMARY)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    primary_path = args.primary.resolve()
    output_path = args.output.resolve()
    with rasterio.open(FOOTPRINT) as src:
        footprint = src.read(1) == 1
        grid = (src.height, src.width, src.crs.to_string(), tuple(src.transform)[:6])
    with rasterio.open(primary_path) as src:
        candidate = src.read(1).astype(np.float32, copy=False)
        primary_grid = (src.height, src.width, src.crs.to_string(), tuple(src.transform)[:6])
        nodata = src.nodata
    if primary_grid != grid:
        raise SystemExit("H56B primary does not match the pinned competition grid")
    if not np.isfinite(candidate[footprint]).all() or not np.isnan(candidate[~footprint]).all():
        raise SystemExit("H56B must be finite inside and NaN outside the footprint")
    if np.any((candidate[footprint] < 0) | (candidate[footprint] > 1)) or not (nodata is not None and np.isnan(nodata)):
        raise SystemExit("H56B values or nodata do not meet the expected NaN-outside encoding")

    candidate_sha = sha256(primary_path)
    candidate_values = candidate[footprint].astype(np.float64)
    candidate_support = candidate_values > 0
    candidates = sorted({p.resolve() for base in (ROOT / "data", ROOT / "docs/downloads")
                         for p in base.rglob("*.tif") if p.resolve() != primary_path.resolve()})
    hash_matches: list[str] = []
    exact_pixel_matches: list[str] = []
    same_grid_count = 0
    skipped_count = 0
    support_matches: list[str] = []
    near_prior = []
    primary_transform = grid[3]
    primary_crs = grid[2]

    for path in candidates:
        if sha256(path) == candidate_sha:
            hash_matches.append(path.relative_to(ROOT).as_posix())
        try:
            with rasterio.open(path) as src:
                if (src.count != 1 or src.height != grid[0] or src.width != grid[1]
                        or src.crs is None or src.crs.to_string() != primary_crs
                        or tuple(src.transform)[:6] != primary_transform):
                    skipped_count += 1
                    continue
                other = src.read(1).astype(np.float32, copy=False)
                other_nodata = src.nodata
        except (rasterio.errors.RasterioIOError, OSError, ValueError):
            skipped_count += 1
            continue
        same_grid_count += 1
        if other_nodata is not None and np.isfinite(other_nodata):
            other = np.where(other == other_nodata, 0.0, other)
        other = np.where(np.isfinite(other), other, 0.0).astype(np.float32, copy=False)
        q = other[footprint].astype(np.float64)
        p = path.relative_to(ROOT).as_posix()
        exact = bool(np.array_equal(candidate_values, q))
        if exact:
            exact_pixel_matches.append(p)
        support = q > 0
        if np.array_equal(candidate_support, support):
            support_matches.append(p)
        inter = int(np.count_nonzero(candidate_support & support))
        union = int(np.count_nonzero(candidate_support | support))
        # Keep detailed numeric comparison for key prior-art paths and any exact
        # support match; that is where a superficial "unique" claim needs care.
        lower = p.lower()
        relevant = any(token in lower for token in ("h56", "h53", "h49", "h55", "h48", "dempster", "yager"))
        if relevant or exact or np.array_equal(candidate_support, support):
            delta = np.abs(candidate_values - q)
            r = float(np.corrcoef(candidate_values, q)[0, 1]) if candidate_values.std() and q.std() else None
            order = np.argsort(-candidate_values, kind="stable")[:TOP_K]
            other_order = np.argsort(-q, kind="stable")[:TOP_K]
            top_a = np.zeros(candidate_values.size, dtype=bool)
            top_b = np.zeros(candidate_values.size, dtype=bool)
            top_a[order] = True
            top_b[other_order] = True
            top_union = int(np.count_nonzero(top_a | top_b))
            near_prior.append({
                "path": p,
                "sha256": sha256(path),
                "in_footprint_exactly_equal": exact,
                "same_positive_support": bool(np.array_equal(candidate_support, support)),
                "positive_support_jaccard": inter / union if union else None,
                "pearson_r": r,
                "mae": float(delta.mean()),
                "max_abs_difference": float(delta.max()),
                "top_37654_jaccard": int(np.count_nonzero(top_a & top_b)) / top_union if top_union else None,
            })

    near_prior.sort(key=lambda row: (
        row["in_footprint_exactly_equal"],
        row["same_positive_support"],
        row["pearson_r"] if row["pearson_r"] is not None else -2.0,
    ), reverse=True)
    old_h56 = next((row for row in near_prior if row["path"].endswith(
        "GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif")), None)
    near_identical_to_old_h56 = bool(
        old_h56 and old_h56["max_abs_difference"] <= 1e-6
        and old_h56["top_37654_jaccard"] == 1.0
    )
    interpretation = (
        "Distinct bytes and not exactly pixel-identical, but effectively a precision/encoding rebuild of the prior H56 surface; not a meaningfully new model or submission candidate."
        if near_identical_to_old_h56 else
        "No exact byte or in-footprint pixel copy found in the local search. The surface is a distinct post-hoc mass-assignment ablation, but local numeric distinction does not establish geological novelty, private-label value, or organizer acceptance."
    )
    report = {
        "schema_version": 1,
        "audited_utc": datetime.now(timezone.utc).isoformat(),
        "status": "NEAR_IDENTICAL_TO_PRIOR_H56_NOT_A_NOVEL_CANDIDATE" if near_identical_to_old_h56 else "DISTINCT_BYTES_AND_PIXELS_NOT_GLOBAL_OR_METHOD_NOVELTY_PROOF",
        "primary": {
            "path": primary_path.relative_to(ROOT).as_posix(),
            "sha256": candidate_sha,
            "bytes": primary_path.stat().st_size,
            "positive_cells": int(candidate_support.sum()),
        },
        "search_scope": {
            "directories": ["data/", "docs/downloads/"],
            "tiffs_examined_for_byte_hash": len(candidates),
            "same_grid_one_band_rasters_compared_in_footprint": same_grid_count,
            "different_grid_or_multiband_files_skipped_for_pixel_comparison": skipped_count,
            "outside_scope": "Other repositories, other GEMSDOE sites, and organizer-held submissions are not searched.",
        },
        "result": {
            "same_sha256_as_any_searched_raster": bool(hash_matches),
            "sha256_matches": hash_matches,
            "exact_in_footprint_pixel_match": bool(exact_pixel_matches),
            "exact_pixel_matches": exact_pixel_matches,
            "same_positive_support_as_prior_rasters": support_matches,
            "prior_h56_zero_outside_comparison": old_h56,
            "interpretation": interpretation,
            "near_identical_to_prior_h56": near_identical_to_old_h56,
        },
        "closest_prior_art_comparisons": near_prior[:15],
        "limits": [
            "This is a repository-local search, not global uniqueness or organizer-side deduplication.",
            "Equal positive support alone does not prove equality of continuous probability/favorability values.",
            "Different bytes, names, or sub-ULP/one-ULP differences do not establish methodological novelty.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "output": output_path.relative_to(ROOT).as_posix(),
        "status": report["status"],
        "primary_sha256": candidate_sha,
        "same_grid_compared": same_grid_count,
        "hash_matches": hash_matches,
        "pixel_matches": exact_pixel_matches,
        "prior_h56_comparison": old_h56,
    }, indent=2))
    return 0 if not hash_matches and not exact_pixel_matches else 2


if __name__ == "__main__":
    raise SystemExit(main())
