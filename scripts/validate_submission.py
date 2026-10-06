#!/usr/bin/env python3
"""Independently re-open and validate a submission GeoTIFF against the official grid."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

from gemsdoe48.geotiff import assert_competition_grid, display_path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SUBMISSION = ROOT / "docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif"
DEFAULT_FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("submission", nargs="?", type=Path, default=DEFAULT_SUBMISSION)
    parser.add_argument("--footprint", type=Path, default=DEFAULT_FOOTPRINT)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()
    with rasterio.open(args.submission) as ds:
        assert_competition_grid(ds.profile, path=args.submission)
        if ds.dtypes != ("float32",):
            raise SystemExit(f"Expected float32, got {ds.dtypes}")
        if ds.nodata is None or not np.isnan(ds.nodata):
            raise SystemExit(f"Expected NaN nodata to match the official sample convention, got {ds.nodata!r}")
        values = ds.read(1)
        tags = ds.tags()
        profile = ds.profile.copy()
    with rasterio.open(args.footprint) as ds:
        assert_competition_grid(ds.profile, path=args.footprint)
        foot_values = ds.read(1)
    if foot_values.dtype != np.uint8 or not np.isin(foot_values, (0, 1)).all():
        raise SystemExit("Footprint mask must be uint8 with only 0/1 values")
    foot = foot_values == 1
    finite = np.isfinite(values)
    if not np.array_equal(finite, foot):
        raise SystemExit(
            f"NaN footprint mismatch: finite submission cells={finite.sum()}, "
            f"mask cells={foot.sum()}, differing={np.count_nonzero(finite ^ foot)}"
        )
    if not np.isfinite(values[foot]).all():
        raise SystemExit("Output contains NaN or infinity inside the footprint")
    if np.any((values[foot] < 0.0) | (values[foot] > 1.0)):
        raise SystemExit("Output contains in-footprint values outside [0, 1]")
    result = {
        "status": "PASS_LOCAL_FORMAT_AUDIT_NOT_ORGANIZER_ACCEPTANCE",
        "file": display_path(args.submission),
        "sha256": sha256_file(args.submission),
        "bytes": args.submission.stat().st_size,
        "dtype": "float32",
        "bands": 1,
        "shape": list(values.shape),
        "crs": "EPSG:32611",
        "resolution_m": [100.0, 100.0],
        "nodata": "NaN",
        "finite_inside_footprint": bool(np.isfinite(values[foot]).all()),
        "nan_outside_footprint": bool(np.isnan(values[~foot]).all()),
        "finite_footprint_cells": int(finite.sum()),
        "nan_outside_cells": int(np.isnan(values).sum()),
        "min_inside_footprint": float(values[foot].min()),
        "max_inside_footprint": float(values[foot].max()),
        "all_in_footprint_range_0_1": bool(values[foot].min() >= 0.0 and values[foot].max() <= 1.0),
        "positive_cells": int(np.count_nonzero(values[foot] > 0.0)),
        "positive_mass": float(values[foot].sum(dtype=np.float64)),
        "grid_profile": {
            "width": profile["width"],
            "height": profile["height"],
            "transform": list(profile["transform"])[:6],
        },
        "tags": tags,
    }
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
