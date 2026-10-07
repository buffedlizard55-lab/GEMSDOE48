#!/usr/bin/env python3
"""Independently re-open and validate a submission GeoTIFF against the official grid."""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48.geotiff import assert_competition_grid, display_path  # noqa: E402
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
    parser.add_argument("--encoding", choices=("auto", "nan", "zeros"), default="auto",
                        help="outside-footprint encoding to require. 'auto' (default) accepts "
                             "either and reports which one was found.")
    args = parser.parse_args()
    with rasterio.open(args.submission) as ds:
        assert_competition_grid(ds.profile, path=args.submission)
        if ds.dtypes != ("float32",):
            raise SystemExit(f"Expected float32, got {ds.dtypes}")
        values = ds.read(1)
        tags = ds.tags()
        profile = ds.profile.copy()
        nodata = ds.nodata
    with rasterio.open(args.footprint) as ds:
        assert_competition_grid(ds.profile, path=args.footprint)
        foot_values = ds.read(1)
    if foot_values.dtype != np.uint8 or not np.isin(foot_values, (0, 1)).all():
        raise SystemExit("Footprint mask must be uint8 with only 0/1 values")
    foot = foot_values == 1
    finite = np.isfinite(values)

    # Two encodings are accepted by this project, and BOTH have owner-reported live
    # scores in the family tree:
    #   'nan'   -- NaN outside the footprint, nodata=NaN (the sample_submission convention)
    #   'zeros' -- all-finite, exactly 0.0 outside, nodata unset.  This is the encoding of
    #              the 0.2778 live-best artifact and of the organizers' own reference
    #              solution export cell, and it is immune to the portal rejection
    #              "Predicted values must be in range [0, 1]", which any NaN cell trips
    #              under a vectorised np.all((v >= 0) & (v <= 1)) test.
    if finite.all():
        encoding = "zeros"
        if nodata is not None:
            raise SystemExit(f"all-finite raster must leave nodata unset, got {nodata!r}")
        if not np.array_equal(values[~foot], np.zeros(int((~foot).sum()), dtype=values.dtype)):
            raise SystemExit("all-finite encoding requires exactly 0.0 outside the footprint")
    elif np.array_equal(finite, foot) and (nodata is None or np.isnan(nodata)):
        encoding = "nan"
        if nodata is None or not np.isnan(nodata):
            raise SystemExit(f"NaN-outside encoding should declare nodata=NaN, got {nodata!r}")
    else:
        raise SystemExit(
            f"outside-footprint encoding is neither all-finite-zeros nor NaN-outside: "
            f"finite cells={int(finite.sum())}, footprint cells={int(foot.sum())}, "
            f"differing={int(np.count_nonzero(finite ^ foot))}, nodata={nodata!r}")
    if args.encoding != "auto" and encoding != args.encoding:
        raise SystemExit(f"expected --encoding {args.encoding}, found {encoding}")
    if not np.isfinite(values[foot]).all():
        raise SystemExit("Output contains NaN or infinity inside the footprint")
    if np.any((values[foot] < 0.0) | (values[foot] > 1.0)):
        raise SystemExit("Output contains in-footprint values outside [0, 1]")
    if not np.isfinite(values).all() and np.any((values[foot] < 0.0) | (values[foot] > 1.0)):
        raise SystemExit("unreachable")
    whole_finite = bool(np.isfinite(values).all())
    whole_in_range = bool(whole_finite and values.min() >= 0.0 and values.max() <= 1.0)
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
        "outside_footprint_encoding": encoding,
        "nodata": "NaN" if encoding == "nan" else None,
        "finite_inside_footprint": bool(np.isfinite(values[foot]).all()),
        "nan_outside_footprint": bool(np.isnan(values[~foot]).all()) if encoding == "nan" else False,
        "zeros_outside_footprint": bool(np.all(values[~foot] == 0.0)) if encoding == "zeros" else False,
        "all_cells_finite": whole_finite,
        "all_cells_in_range_0_1": whole_in_range,
        "portal_range_error_immune": whole_in_range,
        "portal_range_error_note": (
            "the whole raster is finite and inside [0,1], so a vectorised "
            "np.all((v>=0)&(v<=1)) check cannot fail on a NaN comparison"
            if whole_in_range else
            "cells outside the footprint are NaN; a vectorised range check that does not "
            "mask nodata will report 'Predicted values must be in range [0, 1]'. Use the "
            "all-finite zeros-outside twin if the portal rejects this file."),
        "finite_footprint_cells": int(finite.sum()),
        "nan_outside_cells": int(np.isnan(values).sum()),
        "min_inside_footprint": float(values[foot].min()),
        "max_inside_footprint": float(values[foot].max()),
        "min_whole_raster": float(np.nanmin(values)),
        "max_whole_raster": float(np.nanmax(values)),
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
