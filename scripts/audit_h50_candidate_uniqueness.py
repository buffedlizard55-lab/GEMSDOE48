#!/usr/bin/env python3
"""Compare H50-1 against local same-grid TIFF artifacts for exact duplication.

This is a bounded, local artifact audit—not proof of global uniqueness across
all GEMSDOE repositories or the organizer's submission store.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

from gemsdoe48.geotiff import assert_competition_grid, display_path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
DEFAULT_CANDIDATE = ROOT / "docs/downloads/GEMSDOE48-H50-2M-PERSIST-20261007-f12e5391bb9c-nan.tif"
DEFAULT_FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
DEFAULT_OUTPUT = ROOT / "evidence/h50_probe_uniqueness_20261007.json"
SEARCH_ROOTS = (ROOT / "docs/downloads", ROOT / "data/raw", ROOT / "data/official")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_grid(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as ds:
        assert_competition_grid(ds.profile, path=path)
        if ds.count != 1:
            raise ValueError(f"{path}: expected one band")
        return ds.read(1), ds.profile.copy()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=Path, nargs="?", default=DEFAULT_CANDIDATE)
    parser.add_argument("--footprint", type=Path, default=DEFAULT_FOOTPRINT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    candidate_path = args.candidate.resolve()
    candidate, candidate_profile = read_grid(candidate_path)
    if candidate_profile.get("dtype") != "float32" or candidate.dtype != np.float32:
        raise ValueError("Candidate is not float32")
    with rasterio.open(args.footprint) as mask_ds:
        assert_competition_grid(mask_ds.profile, path=args.footprint)
        footprint = mask_ds.read(1) == 1
    if not np.array_equal(np.isfinite(candidate), footprint):
        raise ValueError("Candidate finite mask differs from the finite footprint")
    candidate_support = (candidate > 0.0) & footprint

    paths = sorted(
        path
        for root in SEARCH_ROOTS
        if root.exists()
        for path in root.rglob("*.tif")
        if path.resolve() != candidate_path
    )
    comparisons = []
    for path in paths:
        try:
            values, profile = read_grid(path)
        except Exception as exc:
            comparisons.append(
                {"path": display_path(path), "comparable": False, "reason": str(exc)}
            )
            continue
        other = (values > 0.0) & footprint & np.isfinite(values)
        intersection = int(np.count_nonzero(candidate_support & other))
        union = int(np.count_nonzero(candidate_support | other))
        exact_support = bool(np.array_equal(candidate_support, other))
        exact_values = bool(np.array_equal(candidate[footprint], values[footprint]))
        comparisons.append(
            {
                "path": display_path(path),
                "sha256": sha256_file(path),
                "comparable": True,
                "positive_cells": int(other.sum()),
                "intersection": intersection,
                "union": union,
                "positive_support_jaccard": float(intersection / union) if union else 1.0,
                "exact_positive_support": exact_support,
                "exact_in_footprint_values": exact_values,
            }
        )
    comparable = [item for item in comparisons if item.get("comparable")]
    closest = max(comparable, key=lambda item: item["positive_support_jaccard"], default=None)
    result = {
        "schema_version": 1,
        "status": "PASS_BOUNDED_LOCAL_UNIQUENESS_NOT_GLOBAL_PROOF",
        "candidate": {
            "path": display_path(candidate_path),
            "sha256": sha256_file(candidate_path),
            "bytes": candidate_path.stat().st_size,
            "positive_cells": int(candidate_support.sum()),
        },
        "comparison_scope": [display_path(path) for path in SEARCH_ROOTS],
        "metric": "Exact in-footprint raster values and exact positive-support mask; support Jaccard is intersection/union.",
        "artifacts_attempted": len(paths),
        "comparable_artifacts": len(comparable),
        "noncomparable_artifacts": len(paths) - len(comparable),
        "exact_prediction_matches": sum(item.get("exact_in_footprint_values", False) for item in comparable),
        "exact_positive_support_matches": sum(item.get("exact_positive_support", False) for item in comparable),
        "maximum_positive_support_jaccard": (
            closest["positive_support_jaccard"] if closest is not None else None
        ),
        "closest_artifact": closest,
        "caveat": "This local check does not compare against every historical file in all GEMSDOE repositories, any DriveData submission store, or other participants' files. It establishes no organizer uniqueness or score attribution.",
        "per_artifact": comparisons,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({key: value for key, value in result.items() if key != "per_artifact"}, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
