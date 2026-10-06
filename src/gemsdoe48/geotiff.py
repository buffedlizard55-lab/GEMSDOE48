"""Grid assertions and safe single-band GeoTIFF I/O for competition artifacts."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import rasterio
from affine import Affine

EPSG = "EPSG:32611"
HEIGHT = 3730
WIDTH = 3292
PIXEL_SIZE_M = 100.0
TRANSFORM = Affine(100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


def display_path(path: str | Path) -> str:
    """Return a repository-relative path when possible for portable receipts."""
    resolved = Path(path).resolve()
    try:
        return resolved.relative_to(REPOSITORY_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def read_band(path: str | Path) -> tuple[np.ndarray, dict[str, Any]]:
    """Read a single-band raster and return its first band and profile."""
    source = Path(path)
    with rasterio.open(source) as dataset:
        if dataset.count != 1:
            raise ValueError(f"{source} has {dataset.count} bands; expected one")
        return dataset.read(1), dataset.profile.copy()


def assert_competition_grid(profile: dict[str, Any], *, path: str | Path = "raster") -> None:
    """Fail closed unless raster grid equals the documented 100 m UTM 11N grid."""
    if int(profile.get("width", -1)) != WIDTH or int(profile.get("height", -1)) != HEIGHT:
        raise ValueError(
            f"{path}: expected width/height {WIDTH}x{HEIGHT}, got "
            f"{profile.get('width')}x{profile.get('height')}"
        )
    crs = profile.get("crs")
    if crs is None or crs.to_string() != EPSG:
        raise ValueError(f"{path}: expected {EPSG}, got {crs}")
    transform = profile.get("transform")
    if transform != TRANSFORM:
        raise ValueError(f"{path}: geotransform mismatch: {transform!r}")
    if profile.get("count") != 1:
        raise ValueError(f"{path}: expected one raster band")


def assert_same_grid(profile_a: dict[str, Any], profile_b: dict[str, Any], *, name_a: str, name_b: str) -> None:
    """Require two source rasters to share dimensions, CRS, and affine transform."""
    keys = ("width", "height", "crs", "transform", "count")
    differences = [key for key in keys if profile_a.get(key) != profile_b.get(key)]
    if differences:
        raise ValueError(f"grid mismatch between {name_a} and {name_b}: {', '.join(differences)}")


def write_float32(
    path: str | Path,
    values: np.ndarray,
    reference_profile: dict[str, Any],
    *,
    valid_mask: np.ndarray,
    description: str,
    tags: dict[str, str] | None = None,
) -> dict[str, object]:
    """Write a one-band float32 GeoTIFF with NaN/nodata outside the footprint.

    The challenge page requires cells outside the training-data bounds to be null or
    NaN. To follow its sample-template convention, every in-footprint cell must be
    finite in [0,1], every out-of-footprint cell is NaN, and the GeoTIFF nodata value
    is NaN. The validity mask is mandatory so a caller cannot silently emit zeros
    outside the survey footprint.
    """
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    a = np.asarray(values, dtype=np.float32)
    raw_valid = np.asarray(valid_mask)
    if not np.isin(raw_valid, (False, True, 0, 1)).all():
        raise ValueError(f"{output}: valid mask must contain only boolean/0/1 values")
    valid = raw_valid.astype(bool, copy=False)
    if a.shape != (HEIGHT, WIDTH):
        raise ValueError(f"{output}: expected array shape {(HEIGHT, WIDTH)}, got {a.shape}")
    if valid.shape != a.shape:
        raise ValueError(f"{output}: valid mask shape {valid.shape} does not match {a.shape}")
    if not valid.any():
        raise ValueError(f"{output}: valid mask is empty")
    if not np.isfinite(a[valid]).all():
        raise ValueError(f"{output}: in-footprint values contain NaN or infinity")
    if np.any((a[valid] < 0.0) | (a[valid] > 1.0)):
        raise ValueError(f"{output}: in-footprint values outside [0, 1]")
    if np.isinf(a[~valid]).any() or np.any(~np.isnan(a[~valid])):
        raise ValueError(f"{output}: all outside-footprint cells must be NaN, not numeric values")

    profile = reference_profile.copy()
    profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        width=WIDTH,
        height=HEIGHT,
        crs=EPSG,
        transform=TRANSFORM,
        nodata=np.nan,
        compress="deflate",
        predictor=3,
        zlevel=6,
        tiled=True,
        blockxsize=256,
        blockysize=256,
        interleave="band",
        BIGTIFF="IF_SAFER",
    )
    with rasterio.open(output, "w", **profile) as dataset:
        dataset.write(a, 1)
        dataset.set_band_description(1, description)
        dataset.update_tags(AREA_OR_POINT="Area", **(tags or {}))

    # Re-read the actual output bytes; validate NaN/nodata behavior, not just input arrays.
    with rasterio.open(output) as dataset:
        reread = dataset.read(1)
        assert_competition_grid(dataset.profile, path=output)
        if dataset.dtypes != ("float32",) or dataset.nodata is None or not np.isnan(dataset.nodata):
            raise ValueError(f"{output}: output dtype or NaN nodata metadata changed unexpectedly")
        if not np.isfinite(reread[valid]).all() or np.any(~np.isnan(reread[~valid])):
            raise ValueError(f"{output}: re-read found invalid footprint/nodata values")
        if np.any((reread[valid] < 0.0) | (reread[valid] > 1.0)):
            raise ValueError(f"{output}: re-read found in-footprint values outside [0,1]")
        return {
            "path": display_path(output),
            "bytes": output.stat().st_size,
            "dtype": dataset.dtypes[0],
            "bands": dataset.count,
            "width": dataset.width,
            "height": dataset.height,
            "crs": dataset.crs.to_string(),
            "transform": tuple(dataset.transform)[:6],
            "nodata": "NaN",
            "finite_cells": int(np.isfinite(reread).sum()),
            "nodata_cells": int(np.count_nonzero(np.isnan(reread))),
            "min": float(reread[valid].min()),
            "max": float(reread[valid].max()),
            "range_0_1_with_nan_outside": True,
        }


def write_mask(path: str | Path, values: np.ndarray, reference_profile: dict[str, Any]) -> None:
    """Write a compact uint8 footprint mask (1=in-footprint, 0=outside)."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    raw_mask = np.asarray(values)
    if raw_mask.shape != (HEIGHT, WIDTH) or not np.isin(raw_mask, (0, 1, False, True)).all():
        raise ValueError("footprint mask must be a 0/1 array on the competition grid")
    mask = raw_mask.astype(np.uint8, copy=False)
    profile = reference_profile.copy()
    profile.update(
        driver="GTiff", dtype="uint8", count=1, width=WIDTH, height=HEIGHT,
        crs=EPSG, transform=TRANSFORM, nodata=None, compress="deflate",
        tiled=True, blockxsize=256, blockysize=256, interleave="band",
        BIGTIFF="IF_SAFER",
    )
    with rasterio.open(output, "w", **profile) as dataset:
        dataset.write(mask, 1)
        dataset.set_band_description(1, "survey_footprint_mask: 1=in-footprint, 0=outside")
        dataset.update_tags(
            AREA_OR_POINT="Area",
            source="Derived from the finite mask of the public owner-mirror sample_submission.tif; values were not copied.",
        )
    with rasterio.open(output) as dataset:
        assert_competition_grid(dataset.profile, path=output)
        if dataset.dtypes != ("uint8",) or dataset.nodata is not None:
            raise ValueError(f"{output}: footprint mask dtype/nodata changed unexpectedly")
        if not np.array_equal(dataset.read(1), mask):
            raise ValueError(f"{output}: footprint mask changed during GeoTIFF write")
