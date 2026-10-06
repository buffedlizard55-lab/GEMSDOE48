"""Official competition metric: distance-weighted Tversky index (DTI).

Implemented VERBATIM from the competition problem statement
(https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/,
fetched 2026-10-06):

    k(d)  = (1 - d/R)+        triangular kernel, R = 300 m
    TPw   = sum_{g in G} max_{x: d(x,g) <= R} p(x) * k(d(x,g))
    FPw   = sum_{x: p(x) > 0} p(x) * [1 - max_{g in G} k(d(x,g))]
    FNw   = sum_{g in G} [1 - max_{x: d(x,g) <= R} p(x) * k(d(x,g))]
    DTI   = TPw / (TPw + 0.2*FPw + 0.8*FNw + eps)

Distances are Euclidean.  The grid is 100 m, so R = 3 pixels.
alpha = 0.2 (false positives), beta = 0.8 (false negatives), as stated.

Two implementations are provided and cross-verified in tests/:
  * dti_bruteforce  -- literal loops over the definitions (reference)
  * dti_fast        -- vectorized version used at full-grid scale
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA = 0.2
BETA = 0.8
R_M = 300.0          # kernel support in metres
PIXEL_M = 100.0      # grid cell size in metres
R_PX = R_M / PIXEL_M # = 3.0 pixels
EPS = 1e-12


def _offsets_within(radius_px: float):
    """All integer pixel offsets with Euclidean norm <= radius_px, with kernel weights."""
    r = int(np.floor(radius_px))
    out = []
    for di in range(-r, r + 1):
        for dj in range(-r, r + 1):
            d = float(np.hypot(di, dj))
            if d <= radius_px:
                w = 1.0 - d / radius_px   # k(d), d in px units (linear scale)
                out.append((di, dj, d, w))
    return out


def _shift_fill(a: np.ndarray, di: int, dj: int) -> np.ndarray:
    """Shift array by (di, dj) = (row, col); zero-fill the vacated border (no wrap)."""
    out = np.zeros_like(a)
    h, w = a.shape
    # source rows r map to r+di in the output
    rs0, rs1 = max(0, -di), min(h, h - di)
    cs0, cs1 = max(0, -dj), min(w, w - dj)
    if rs1 <= rs0 or cs1 <= cs0:
        return out
    out[rs0 + di:rs1 + di, cs0 + dj:cs1 + dj] = a[rs0:rs1, cs0:cs1]
    return out


def coverage_field(pred: np.ndarray, truth_mask: np.ndarray | None = None) -> np.ndarray:
    """Per-truth-pixel cover value c(g) = max_{x: d<=R} p(x) k(d(x,g)), broadcast to the grid.

    Returns an array of shape pred.shape whose value at cell z equals
    max over prediction pixels x within R of z of p(x)*k(d(x,z)).
    (Cells that are not truth pixels are simply unused by the caller.)
    """
    cover = np.zeros(pred.shape, dtype=np.float64)
    for di, dj, _d, w in _offsets_within(R_PX):
        shifted = _shift_fill(pred.astype(np.float64), di, dj) * w
        np.maximum(cover, shifted, out=cover)
    return cover


def dti_components_fast(pred: np.ndarray, truth: np.ndarray):
    """Vectorized DTI components.

    pred  : float array in [0,1] (graded predictions), any NaNs treated as 0 support
    truth : binary array, 1 = ground-truth fault pixel
    Returns dict with TPw, FPw, FNw, DTI, n_truth, n_pred_positive.
    """
    pred = np.where(np.isfinite(pred), pred, 0.0).astype(np.float64)
    truth_mask = truth > 0
    n_truth = int(truth_mask.sum())
    pos = pred > 0
    n_pos = int(pos.sum())
    if n_truth == 0:
        fpw = float((pred[pos]).sum()) if n_pos else 0.0
        return {"TPw": 0.0, "FPw": fpw, "FNw": 0.0,
                "DTI": 0.0 / (0.0 + ALPHA * fpw + 0.0 + EPS),
                "n_truth": 0, "n_pred_positive": n_pos}

    # --- TPw / FNw: per truth pixel, best kernel-weighted prediction cover
    cover = coverage_field(pred)
    cover_g = cover[truth_mask]
    tpw = float(cover_g.sum())
    fnw = float((1.0 - cover_g).sum())

    # --- FPw: per positive prediction pixel, distance to nearest truth pixel
    d_truth_px = distance_transform_edt(~truth_mask)  # px units
    k_nearest = np.clip(1.0 - d_truth_px / R_PX, 0.0, 1.0)
    fpw = float((pred[pos] * (1.0 - k_nearest[pos])).sum())

    dti = tpw / (tpw + ALPHA * fpw + BETA * fnw + EPS)
    return {"TPw": tpw, "FPw": fpw, "FNw": fnw, "DTI": float(dti),
            "n_truth": n_truth, "n_pred_positive": n_pos}


def dti_fast(pred: np.ndarray, truth: np.ndarray) -> float:
    return dti_components_fast(pred, truth)["DTI"]


def dti_bruteforce(pred: np.ndarray, truth: np.ndarray):
    """Literal transcription of the definitions (slow; for verification only)."""
    pred = np.where(np.isfinite(pred), pred, 0.0).astype(np.float64)
    truth_mask = truth > 0
    gy, gx = np.nonzero(truth_mask)
    py, px = np.nonzero(pred > 0)
    n_truth = len(gy)
    n_pos = len(py)

    tpw = 0.0
    fnw = 0.0
    for i in range(n_truth):
        best = 0.0
        for j in range(n_pos):
            d_m = float(np.hypot(py[j] - gy[i], px[j] - gx[i])) * PIXEL_M
            if d_m <= R_M:
                v = pred[py[j], px[j]] * max(1.0 - d_m / R_M, 0.0)
                if v > best:
                    best = v
        tpw += best
        fnw += 1.0 - best

    fpw = 0.0
    for j in range(n_pos):
        best_k = 0.0
        for i in range(n_truth):
            d_m = float(np.hypot(py[j] - gy[i], px[j] - gx[i])) * PIXEL_M
            if d_m <= R_M:
                k = 1.0 - d_m / R_M
                if k > best_k:
                    best_k = k
        fpw += pred[py[j], px[j]] * (1.0 - best_k)

    dti = tpw / (tpw + ALPHA * fpw + BETA * fnw + EPS) if n_truth else 0.0
    return {"TPw": tpw, "FPw": fpw, "FNw": fnw, "DTI": float(dti),
            "n_truth": n_truth, "n_pred_positive": n_pos}
