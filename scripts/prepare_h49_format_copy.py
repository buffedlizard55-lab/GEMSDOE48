#!/usr/bin/env python3
"""Copy H49's in-footprint predictions and encode the official outside-footprint nulls.

The upstream H49 artifact remains untouched. This format-only derivative takes its
valid-footprint mask from the tracked, locally audited H48 competition-grid TIFF,
checks that the grids match, and writes NaN/nodata outside the footprint. Organizer
portal acceptance is not inferred from these local checks.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

from gemsdoe48.geotiff import assert_competition_grid, assert_same_grid

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-e6f08013888b.tif"
DEFAULT_MASK_REFERENCE = ROOT / "docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif"
DEFAULT_OUTPUT = ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif"
DEFAULT_RECEIPT = ROOT / "evidence/h49_format_audit_20261006.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return path.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path.resolve())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--mask-reference", type=Path, default=DEFAULT_MASK_REFERENCE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    args = parser.parse_args()

    with rasterio.open(args.mask_reference) as reference:
        assert_competition_grid(reference.profile, path=args.mask_reference)
        if reference.count != 1 or reference.dtypes[0] != "float32":
            raise SystemExit("mask reference must be a single-band float32 GeoTIFF")
        reference_values = reference.read(1)
        footprint = np.isfinite(reference_values)
        reference_profile = reference.profile.copy()
        reference_nodata = reference.nodata
    if not footprint.any() or footprint.all():
        raise SystemExit("mask reference must encode a nonempty finite footprint and NaN outside")
    if not np.isnan(reference_values[~footprint]).all() or reference_nodata is None or not np.isnan(reference_nodata):
        raise SystemExit("mask reference must use both NaN outside cells and a NaN nodata tag")

    with rasterio.open(args.input) as source:
        assert_competition_grid(source.profile, path=args.input)
        assert_same_grid(reference_profile, source.profile, name_a=str(args.mask_reference), name_b=str(args.input))
        if source.count != 1 or source.dtypes[0] != "float32":
            raise SystemExit("H49 input must be a single-band float32 GeoTIFF")
        values = source.read(1)
        profile = source.profile.copy()
    if not np.isfinite(values).all():
        raise SystemExit("upstream H49 input must be all-finite before the format-only conversion")
    if np.any(values[~footprint] != 0.0):
        raise SystemExit("format-only conversion expects zero mass in every upstream outside-footprint cell")
    if values[footprint].min() < 0.0 or values[footprint].max() > 1.0:
        raise SystemExit("H49 in-footprint values are outside [0, 1]")

    converted = values.astype(np.float32, copy=True)
    converted[~footprint] = np.nan
    profile.update(dtype="float32", count=1, nodata=float("nan"), compress="deflate")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(args.output, "w", **profile) as destination:
        destination.write(converted, 1)

    with rasterio.open(args.output) as result:
        assert_competition_grid(result.profile, path=args.output)
        assert_same_grid(reference_profile, result.profile, name_a=str(args.mask_reference), name_b=str(args.output))
        audited = result.read(1)
        if result.count != 1 or result.dtypes[0] != "float32":
            raise SystemExit("converted file is not single-band float32")
        if not np.isfinite(audited[footprint]).all() or not np.isnan(audited[~footprint]).all():
            raise SystemExit("converted file does not have finite inside values and NaN outside")
        if audited[footprint].min() < 0.0 or audited[footprint].max() > 1.0:
            raise SystemExit("converted in-footprint values are outside [0, 1]")
        if not np.array_equal(audited[footprint], values[footprint]):
            raise SystemExit("format conversion changed an in-footprint prediction")
        nodata = result.nodata
        if nodata is None or not np.isnan(nodata):
            raise SystemExit("converted file is missing its NaN nodata tag")
        audit_profile = result.profile.copy()

    receipt = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "method": "format-only outside-footprint conversion; inside prediction pixels must be byte-value-identical",
        "input": {"path": rel(args.input), "sha256": sha256_file(args.input)},
        "mask_reference": {
            "path": rel(args.mask_reference),
            "sha256": sha256_file(args.mask_reference),
            "mask_rule": "finite values in the locally audited NaN-outside H48 TIFF define the valid footprint",
        },
        "output": {
            "path": rel(args.output),
            "sha256": sha256_file(args.output),
            "bytes": args.output.stat().st_size,
            "bands": int(audit_profile["count"]),
            "dtype": audit_profile["dtype"],
            "crs": str(audit_profile["crs"]),
            "shape": [int(audit_profile["height"]), int(audit_profile["width"])],
            "resolution": [float(abs(audit_profile["transform"].a)), float(abs(audit_profile["transform"].e))],
            "nodata": "NaN",
            "all_inside_finite": bool(np.isfinite(audited[footprint]).all()),
            "all_outside_nan": bool(np.isnan(audited[~footprint]).all()),
            "inside_min": float(audited[footprint].min()),
            "inside_max": float(audited[footprint].max()),
            "positive_inside_cells": int(np.count_nonzero(audited[footprint] > 0.0)),
            "same_inside_pixels_as_input": bool(np.array_equal(audited[footprint], values[footprint])),
            "organizer_portal_acceptance_tested": False,
        },
        "decision": "format checks passed locally; this does not clear a weekly submission slot or establish organizer acceptance",
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
