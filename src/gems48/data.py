"""Grid / footprint / catalogue loaders (all paths relative to repo root)."""
from pathlib import Path
import numpy as np, rasterio
from scipy import ndimage as ndi
ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"

def read(path):
    with rasterio.open(path) as s:
        return s.read(1), s.profile

def grid():
    lab, prof = read(RAW / "existing_faults.tif")
    fp = lab != -1
    cat = lab == 1
    return dict(profile=prof, footprint=fp, catalogue=cat,
                mask=(~fp) | cat, dcat=ndi.distance_transform_edt(~cat))

def binary(path):
    a, _ = read(path)
    return np.nan_to_num(a.astype(np.float32), nan=0.0)

def sgmc_offcat(G, min_d=3.0):
    a, _ = read(RAW / "external" / "derived_sgmc_faults_100m_u8.tif")
    return (a > 0) & G["footprint"] & (G["dcat"] > min_d)

def quadrant_folds(G):
    """4 spatial folds = footprint quadrants split at the median footprint row/col."""
    ys, xs = np.nonzero(G["footprint"])
    ym, xm = int(np.median(ys)), int(np.median(xs))
    H, W = G["footprint"].shape
    yy, xx = np.mgrid[0:H, 0:W]
    q = (yy >= ym).astype(np.int8) * 2 + (xx >= xm).astype(np.int8)
    return [(q == i) & G["footprint"] for i in range(4)]
