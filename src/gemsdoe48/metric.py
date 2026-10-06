"""Exact distance-weighted Tversky index for the DOE GEMS grid.

The equations and coefficients follow the official competition problem description:
300 m triangular kernel, alpha=0.2, beta=0.8. Distances use the raster's 100 m
projected pixel spacing. This implementation supports both continuous and binary
prediction surfaces.
"""
from __future__ import annotations

from functools import lru_cache
from math import ceil, hypot

import numpy as np
from scipy.ndimage import distance_transform_edt

ALPHA = 0.2
BETA = 0.8
DEFAULT_RADIUS_M = 300.0
DEFAULT_PIXEL_SIZE_M = 100.0
EPSILON = 1e-12


def triangular_kernel(distance_m: np.ndarray | float, radius_m: float = DEFAULT_RADIUS_M) -> np.ndarray:
    """Compute ``max(1 - d/R, 0)`` using metric distances in metres."""
    if not np.isfinite(radius_m) or radius_m <= 0:
        raise ValueError("radius_m must be positive and finite")
    return np.maximum(1.0 - np.asarray(distance_m, dtype=np.float64) / radius_m, 0.0)


@lru_cache(maxsize=16)
def _offsets(radius_m: float, pixel_size_m: float) -> tuple[tuple[int, int, float], ...]:
    if not np.isfinite(pixel_size_m) or pixel_size_m <= 0:
        raise ValueError("pixel_size_m must be positive and finite")
    radius_px = radius_m / pixel_size_m
    max_offset = int(ceil(radius_px))
    offsets: list[tuple[int, int, float]] = []
    for dy in range(-max_offset, max_offset + 1):
        for dx in range(-max_offset, max_offset + 1):
            distance = hypot(dy * pixel_size_m, dx * pixel_size_m)
            weight = float(triangular_kernel(distance, radius_m))
            if weight > 0.0:
                offsets.append((dy, dx, weight))
    return tuple(offsets)


def _prediction_at_neighbor(values: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """At each target cell (y,x), return values[y+dy, x+dx], zero outside grid."""
    h, w = values.shape
    out = np.zeros_like(values)
    dst_y0 = max(0, -dy)
    dst_y1 = min(h, h - dy)
    dst_x0 = max(0, -dx)
    dst_x1 = min(w, w - dx)
    if dst_y0 >= dst_y1 or dst_x0 >= dst_x1:
        return out
    src_y0 = dst_y0 + dy
    src_y1 = dst_y1 + dy
    src_x0 = dst_x0 + dx
    src_x1 = dst_x1 + dx
    out[dst_y0:dst_y1, dst_x0:dst_x1] = values[src_y0:src_y1, src_x0:src_x1]
    return out


def distance_weighted_tversky(
    prediction: np.ndarray,
    truth: np.ndarray,
    *,
    valid: np.ndarray | None = None,
    radius_m: float = DEFAULT_RADIUS_M,
    pixel_size_m: float = DEFAULT_PIXEL_SIZE_M,
    alpha: float = ALPHA,
    beta: float = BETA,
) -> dict[str, float | int]:
    """Compute the published distance-weighted Tversky components and score.

    ``valid`` selects the spatial evaluation domain; prediction values outside it are
    ignored. Truth is boolean/nonzero within the domain. For a spatial-fold test, pass
    a fold-plus-halo mask so predictions in other folds are not counted as false
    positives and predictions within the 300 m tolerance of held-out truth are retained.
    """
    p_in = np.asarray(prediction)
    g_in = np.asarray(truth)
    if p_in.ndim != 2 or p_in.shape != g_in.shape:
        raise ValueError("prediction and truth must have the same 2-D shape")
    if valid is None:
        active = np.ones(p_in.shape, dtype=bool)
    else:
        active = np.asarray(valid, dtype=bool)
        if active.shape != p_in.shape:
            raise ValueError("valid mask shape does not match the raster")
    if not np.isfinite(radius_m) or radius_m <= 0:
        raise ValueError("radius_m must be positive and finite")
    if not np.isfinite(alpha) or alpha < 0 or not np.isfinite(beta) or beta < 0:
        raise ValueError("alpha and beta must be finite and nonnegative")

    active_values = np.asarray(p_in[active], dtype=np.float64)
    if not np.isfinite(active_values).all() or np.any((active_values < 0.0) | (active_values > 1.0)):
        raise ValueError("prediction values in the valid domain must be finite and in [0, 1]")
    p = np.zeros(p_in.shape, dtype=np.float32)
    p[active] = active_values.astype(np.float32, copy=False)
    g = active & np.asarray(g_in, dtype=bool)
    n_truth = int(g.sum())
    if n_truth == 0:
        return {"tp": 0.0, "fp": float(p.sum()), "fn": 0.0, "n_truth": 0, "dti": 0.0, "coverage": 0.0}

    # TP: for every truth pixel, maximize p(x)*k(d(x,g)) over all candidate pixels.
    best_credit = np.zeros(p.shape, dtype=np.float32)
    for dy, dx, weight in _offsets(float(radius_m), float(pixel_size_m)):
        candidate = _prediction_at_neighbor(p, dy, dx) * np.float32(weight)
        np.maximum(best_credit, candidate, out=best_credit)
    tp = float(best_credit[g].sum(dtype=np.float64))
    fn = float(n_truth) - tp

    # FP: for every positive prediction, charge the complement of the closest-truth kernel.
    distance_to_truth = distance_transform_edt(~g, sampling=(pixel_size_m, pixel_size_m))
    nearest_truth_credit = triangular_kernel(distance_to_truth, radius_m)
    fp = float((p[active].astype(np.float64) * (1.0 - nearest_truth_credit[active])).sum(dtype=np.float64))
    denominator = tp + alpha * fp + beta * fn
    dti = float(tp / (denominator + EPSILON))
    return {"tp": tp, "fp": fp, "fn": fn, "n_truth": n_truth, "dti": dti, "coverage": float(tp / n_truth)}
