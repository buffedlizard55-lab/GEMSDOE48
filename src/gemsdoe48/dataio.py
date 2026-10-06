"""Raster I/O pinned to the official competition grid.

Grid provenance (see docs/sources.html):
  transform (100, 0, 243350, 0, -100, 4508550), shape 3730 x 3292,
  EPSG:32611, float32 -- pinned byte-for-byte by the sha256 of the
  owner-mirrored official sample_submission.tif
  (2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc).
"""
from __future__ import annotations

import numpy as np
import rasterio

EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
EXPECTED_SHAPE = (3730, 3292)
EXPECTED_EPSG = 32611


def load(path: str) -> np.ndarray:
    """Load a single-band raster; assert it is on the competition grid."""
    with rasterio.open(path) as ds:
        assert ds.count == 1, f"{path}: expected 1 band, got {ds.count}"
        assert (ds.height, ds.width) == EXPECTED_SHAPE, \
            f"{path}: shape {(ds.height, ds.width)} != {EXPECTED_SHAPE}"
        t = tuple(float(v) for v in tuple(ds.transform)[:6])
        assert t == EXPECTED_TRANSFORM, f"{path}: transform {t} mismatch"
        assert ds.crs is not None and ds.crs.to_epsg() == EXPECTED_EPSG, \
            f"{path}: CRS {ds.crs} != EPSG:{EXPECTED_EPSG}"
        return ds.read(1)


def footprint_from_template(path: str) -> np.ndarray:
    """Footprint = finite cells of the official sample_submission.tif."""
    with rasterio.open(path) as ds:
        a = ds.read(1)
    return np.isfinite(a)


def write_submission(path: str, arr: np.ndarray, footprint: np.ndarray | None = None):
    """Write a portal-safe submission GeoTIFF:
    single band, float32, EPSG:32611, competition transform, all cells finite
    in [0,1], zero outside the footprint, no nodata tag."""
    a = np.where(np.isfinite(arr), arr, 0.0).astype(np.float64)
    if footprint is not None:
        a = np.where(footprint, a, 0.0)
    a = np.clip(a, 0.0, 1.0).astype(np.float32)
    profile = dict(
        driver="GTiff", height=EXPECTED_SHAPE[0], width=EXPECTED_SHAPE[1],
        count=1, dtype="float32", crs=f"EPSG:{EXPECTED_EPSG}",
        transform=rasterio.Affine(*EXPECTED_TRANSFORM),
        compress="deflate", predictor=2, tiled=True, blockxsize=256, blockysize=256,
    )
    with rasterio.open(path, "w", **profile) as ds:
        ds.write(a, 1)
    return a
