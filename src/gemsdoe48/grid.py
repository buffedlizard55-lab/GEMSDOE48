"""Grid I/O for the GEMS footprint.

The official grid is fixed and verified against the organizers' own rasters
(`data/official/labels.tif`, `data/official/existing_faults.tif`, both SHA-256
pinned in registry/inputs.json):

    CRS          EPSG:32611 (WGS 84 / UTM zone 11N)
    size         3292 columns x 3730 rows
    pixel size   100 m x 100 m
    transform    (100, 0, 243350), (0, -100, 4508550)
    dtype/value  single band; labels are int8, -1 = outside the study area
    footprint    5,167,373 pixels (7,111,787 pixels are -1 / outside)
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"

EXPECTED = {
    "width": 3292,
    "height": 3730,
    "crs": "EPSG:32611",
    "transform": (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0),
    "res": (100.0, 100.0),
}


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass
class Raster:
    path: Path
    array: np.ndarray
    profile: dict

    @property
    def shape(self) -> tuple[int, int]:
        return self.array.shape  # type: ignore[return-value]


def read_raster(path: str | Path) -> Raster:
    p = Path(path)
    with rasterio.open(p) as src:
        arr = src.read(1)
        profile = src.profile.copy()
    return Raster(path=p, array=arr, profile=profile)


def read_mask(path: str | Path) -> np.ndarray:
    """Read a raster and return a boolean 'is a fault / is present' mask."""
    r = read_raster(path)
    a = r.array
    if a.dtype.kind == "f":
        a = np.where(np.isfinite(a), a, 0.0)
    return a > 0


def read_surface(path: str | Path) -> np.ndarray:
    """Read a raster as a float64 [0, 1] surface (NaN -> 0)."""
    r = read_raster(path)
    a = r.array.astype(np.float64)
    return np.where(np.isfinite(a), a, 0.0)


def labels_path() -> Path:
    return DATA / "official" / "labels.tif"


def existing_faults_path() -> Path:
    return DATA / "official" / "existing_faults.tif"


def load_truth_and_footprint():
    """Return (cdtrue_mask, footprint_mask) from the official labels raster.

    `labels.tif` is byte-identical to `existing_faults.tif` in the official data
    drop; that identity is asserted by tests/test_metric.py and recorded as
    registry irregularity IR-48-01.
    """
    r = read_raster(labels_path())
    a = r.array
    footprint = a != -1
    truth = a == 1
    return truth, footprint


def assert_grid(path: str | Path) -> dict:
    with rasterio.open(path) as src:
        got = {
            "width": src.width,
            "height": src.height,
            "crs": src.crs.to_string() if src.crs else None,
            "transform": tuple(src.transform)[:6],
            "res": src.res,
        }
    for key in ("width", "height", "crs", "res"):
        if got[key] != EXPECTED[key]:
            raise ValueError(f"{path}: {key} = {got[key]!r}, expected {EXPECTED[key]!r}")
    if tuple(round(v, 6) for v in got["transform"]) != EXPECTED["transform"]:
        raise ValueError(f"{path}: transform {got['transform']} != {EXPECTED['transform']}")
    return got


def write_submission(path: str | Path, surface: np.ndarray, *, profile_from: str | Path | None = None) -> Path:
    """Write a single-band float32 GeoTIFF on the official grid.

    All values are finite and inside [0, 1]; NaN is never written.  The
    organizers' portal has rejected files with the message
    "Predicted values must be in range [0, 1]" for a user in this project, and a
    file with no NaN and no out-of-range value cannot trigger that check
    (repository irregularity IR-48-03).
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(surface, dtype=np.float64)
    if arr.shape != (EXPECTED["height"], EXPECTED["width"]):
        raise ValueError(f"surface shape {arr.shape} != official grid")
    if not np.isfinite(arr).all():
        raise ValueError("surface contains non-finite values; the submission must be all-finite")
    if arr.min() < 0.0 or arr.max() > 1.0:
        raise ValueError(f"surface range [{arr.min()}, {arr.max()}] outside [0, 1]")

    src_profile = None
    if profile_from is not None:
        with rasterio.open(profile_from) as s:
            src_profile = s.profile.copy()
    if src_profile is None:
        src_profile = {
            "driver": "GTiff",
            "height": EXPECTED["height"],
            "width": EXPECTED["width"],
            "count": 1,
            "dtype": "float32",
            "crs": rasterio.crs.CRS.from_string(EXPECTED["crs"]),
            "transform": rasterio.Affine(*EXPECTED["transform"]),
            "nodata": None,
            "compress": "deflate",
            "tiled": False,
        }
    else:
        src_profile.update(
            driver="GTiff", count=1, dtype="float32", nodata=None, compress="deflate"
        )
        src_profile.pop("photometric", None)
    with rasterio.open(p, "w", **src_profile) as dst:
        dst.write(arr.astype(np.float32), 1)
    return p


def write_float32(path: str | Path, surface: np.ndarray, *, nodata: float | None = None) -> Path:
    """Write a diagnostic float32 raster on the official grid (NaN allowed)."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    arr = np.asarray(surface, dtype=np.float32)
    profile = {
        "driver": "GTiff",
        "height": EXPECTED["height"],
        "width": EXPECTED["width"],
        "count": 1,
        "dtype": "float32",
        "crs": rasterio.crs.CRS.from_string(EXPECTED["crs"]),
        "transform": rasterio.Affine(*EXPECTED["transform"]),
        "nodata": nodata,
        "compress": "deflate",
    }
    with rasterio.open(p, "w", **profile) as dst:
        dst.write(arr, 1)
    return p


def write_json(path: str | Path, payload) -> Path:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w") as fh:
        json.dump(payload, fh, indent=2, sort_keys=False, default=str)
        fh.write("\n")
    return p
