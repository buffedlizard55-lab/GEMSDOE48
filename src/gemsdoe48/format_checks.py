"""Portal-compliance audit for a written GeoTIFF, re-read from disk.

Reproduces the checks behind the DrivenData rejection message
"Predicted values must be in range [0, 1]":
  * single band, float32, EPSG:32611, exact shape + geotransform
  * every one of the 12,279,160 cells finite (no NaN, no inf)
  * min >= 0, max <= 1
  * no nodata tag (a nodata sentinel outside [0,1] is itself rejected)
"""
from __future__ import annotations

import hashlib
import json
import os

import numpy as np
import rasterio

from .dataio import EXPECTED_EPSG, EXPECTED_SHAPE, EXPECTED_TRANSFORM


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def audit_submission(path: str, footprint: np.ndarray | None = None) -> dict:
    with rasterio.open(path) as ds:
        a = ds.read(1)
        t = tuple(float(v) for v in tuple(ds.transform)[:6])
        receipt = {
            "file": os.path.basename(path),
            "size_bytes": os.path.getsize(path),
            "sha256": sha256_file(path),
            "bands": ds.count,
            "dtype": str(a.dtype),
            "crs": ds.crs.to_string() if ds.crs else None,
            "epsg": ds.crs.to_epsg() if ds.crs else None,
            "shape": [ds.height, ds.width],
            "transform": list(t),
            "nodata": ds.nodata,
            "total_cells": int(a.size),
            "finite_cells": int(np.isfinite(a).sum()),
            "nan_cells": int(np.isnan(a).sum()),
            "inf_cells": int(np.isinf(a).sum()),
            "min": float(np.nanmin(a)) if np.isfinite(a).any() else None,
            "max": float(np.nanmax(a)) if np.isfinite(a).any() else None,
            "positive_cells": int((a > 0).sum()),
        }
    if footprint is not None:
        receipt["positive_cells_in_footprint"] = int((a[footprint] > 0).sum())
        receipt["outside_footprint_all_zero"] = bool((a[~footprint] == 0).all())
        receipt["footprint_min"] = float(a[footprint].min())
        receipt["footprint_max"] = float(a[footprint].max())
    receipt["checks"] = {
        "single_band": receipt["bands"] == 1,
        "dtype_float32": receipt["dtype"] == "float32",
        "shape_3730x3292": tuple(receipt["shape"]) == EXPECTED_SHAPE,
        "crs_epsg32611": receipt["epsg"] == EXPECTED_EPSG,
        "transform_matches_template": t == EXPECTED_TRANSFORM,
        "all_cells_finite": receipt["finite_cells"] == receipt["total_cells"],
        "range_0_1": (receipt["min"] is not None and receipt["min"] >= 0.0
                      and receipt["max"] is not None and receipt["max"] <= 1.0),
        "no_nodata_tag": receipt["nodata"] is None,
    }
    receipt["all_checks_passed"] = all(receipt["checks"].values())
    return receipt


def dump_json(obj, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f, indent=1)
