#!/usr/bin/env python3
"""Bounded exact-value/support comparison for the H53-A candidate.

Scans case-insensitive .tif/.tiff files below docs/downloads/ and data/, compares
only one-band rasters on the exact competition grid, and records non-comparable rasters. This
is not a global GEMSDOE-site or organizer-side uniqueness proof.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from affine import Affine

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CANDIDATE = ROOT / "docs/downloads/GEMSDOE48-H53-STRIKE-COHERENCE-20261007-de35531d3867-nan-outside.tif"
DEFAULT_FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
DEFAULT_OUTPUT = ROOT / "evidence/h53a_scarp_submission_identity_20261007.json"
EXPECTED_TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
EXPECTED_CRS = "EPSG:32611"
EXPECTED_SHAPE = (3730, 3292)
SEARCH_ROOTS = (ROOT / "docs/downloads", ROOT / "data")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def display_path(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def is_spatial_grid(ds: rasterio.io.DatasetReader) -> bool:
    return (
        ds.shape == EXPECTED_SHAPE
        and ds.crs is not None
        and ds.crs.to_string() == EXPECTED_CRS
        and ds.transform == EXPECTED_TRANSFORM
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, nargs="?", default=DEFAULT_CANDIDATE)
    parser.add_argument("--footprint", type=Path, default=DEFAULT_FOOTPRINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    candidate_path = args.candidate.resolve()
    with rasterio.open(candidate_path) as ds:
        if not is_spatial_grid(ds) or ds.count != 1 or ds.dtypes != ("float32",):
            raise SystemExit("candidate does not match the single-band competition raster profile")
        candidate = ds.read(1)
    with rasterio.open(args.footprint) as ds:
        if not is_spatial_grid(ds) or ds.count != 1:
            raise SystemExit("footprint mask does not match the competition grid")
        footprint = ds.read(1) == 1
    if not np.array_equal(np.isfinite(candidate), footprint):
        raise SystemExit("candidate finite mask does not match the official-grid footprint")
    candidate_support = (candidate > 0.0) & footprint

    paths = sorted(
        path.resolve()
        for root in SEARCH_ROOTS
        if root.exists()
        for path in root.rglob("*")
        if path.is_file() and path.suffix.lower() in {".tif", ".tiff"}
        if path.resolve() != candidate_path
    )
    comparisons: list[dict] = []
    for path in paths:
        try:
            with rasterio.open(path) as ds:
                if not is_spatial_grid(ds):
                    comparisons.append({"path": display_path(path), "comparable": False,
                                        "reason": "different shape, CRS, or affine transform"})
                    continue
                if ds.count != 1:
                    comparisons.append({"path": display_path(path), "comparable": False,
                                        "reason": f"same spatial grid but {ds.count} bands"})
                    continue
                values = ds.read(1)
        except Exception as exc:  # noqa: BLE001
            comparisons.append({"path": display_path(path), "comparable": False,
                                "reason": f"raster read failed: {exc!r}"})
            continue
        other_support = (np.isfinite(values) & (values > 0.0) & footprint)
        intersection = int(np.count_nonzero(candidate_support & other_support))
        union = int(np.count_nonzero(candidate_support | other_support))
        comparisons.append({
            "path": display_path(path),
            "sha256": sha256_file(path),
            "comparable": True,
            "positive_cells": int(other_support.sum()),
            "intersection": intersection,
            "union": union,
            "positive_support_jaccard": float(intersection / union) if union else 1.0,
            "exact_positive_support": bool(np.array_equal(candidate_support, other_support)),
            "exact_in_footprint_values": bool(np.array_equal(candidate[footprint], values[footprint])),
        })

    comparable = [item for item in comparisons if item.get("comparable")]
    closest = max(comparable, key=lambda item: item["positive_support_jaccard"], default=None)
    exact_values = sum(item.get("exact_in_footprint_values", False) for item in comparable)
    exact_support = sum(item.get("exact_positive_support", False) for item in comparable)
    result = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_BOUNDED_LOCAL_UNIQUENESS_NOT_GLOBAL_PROOF" if not exact_values and not exact_support else "EXACT_LOCAL_MATCH_FOUND",
        "candidate": {
            "path": display_path(candidate_path),
            "sha256": sha256_file(candidate_path),
            "bytes": candidate_path.stat().st_size,
            "positive_cells": int(candidate_support.sum()),
        },
        "comparison_scope": [root.relative_to(ROOT).as_posix() for root in SEARCH_ROOTS],
        "comparison_rule": "Exact in-footprint values and positive support; support Jaccard = intersection/union.",
        "artifacts_attempted": len(paths),
        "comparable_one_band_competition_grid_artifacts": len(comparable),
        "noncomparable_artifacts": len(paths) - len(comparable),
        "exact_prediction_matches": exact_values,
        "exact_positive_support_matches": exact_support,
        "maximum_positive_support_jaccard": closest["positive_support_jaccard"] if closest else None,
        "closest_artifact": closest,
        "per_artifact": comparisons,
        "caveat": "This local scan does not cover all historical files in all GEMSDOE sites, other participants' uploads, DrivenData's store, or organizer-side file/score attribution. No global uniqueness or acceptance is claimed.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "per_artifact"}, indent=2, sort_keys=True))
    return 0 if not exact_values and not exact_support else 2


if __name__ == "__main__":
    raise SystemExit(main())
