"""The H49 format-only derivative is byte-audited independently from its receipt."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

import conftest  # noqa: F401 (path bootstrap)

ROOT = Path(__file__).resolve().parents[1]
ORIGINAL = ROOT / "docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-e6f08013888b.tif"
CONVERTED = ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif"
MASK_REFERENCE = ROOT / "docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif"
RECEIPT = ROOT / "evidence/h49_submission_validation_20261006.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def test_h49_format_copy_preserves_predictions_and_nulls_outside():
    assert ORIGINAL.is_file() and CONVERTED.is_file() and MASK_REFERENCE.is_file()
    with rasterio.open(MASK_REFERENCE) as ref:
        footprint = np.isfinite(ref.read(1))
        expected_grid = (ref.height, ref.width, ref.crs, ref.transform)
    with rasterio.open(ORIGINAL) as src:
        original = src.read(1)
    with rasterio.open(CONVERTED) as src:
        converted = src.read(1)
        assert src.count == 1
        assert src.dtypes == ("float32",)
        assert src.height == expected_grid[0] and src.width == expected_grid[1]
        assert src.crs == expected_grid[2] and src.transform == expected_grid[3]
        assert np.isnan(src.nodata)
    assert np.isfinite(converted[footprint]).all()
    assert np.isnan(converted[~footprint]).all()
    assert np.array_equal(converted[footprint], original[footprint])
    assert float(converted[footprint].min()) >= 0.0
    assert float(converted[footprint].max()) <= 1.0
    assert int(np.count_nonzero(converted[footprint] > 0.0)) == 47_905


def test_h49_local_validation_receipt_matches_converted_bytes():
    assert RECEIPT.is_file()
    receipt = json.loads(RECEIPT.read_text())
    assert receipt["status"] == "PASS_LOCAL_FORMAT_AUDIT_NOT_ORGANIZER_ACCEPTANCE"
    assert receipt["sha256"] == sha256_file(CONVERTED)
    assert receipt["nan_outside_footprint"] is True
    assert receipt["finite_inside_footprint"] is True
    assert receipt["all_in_footprint_range_0_1"] is True
