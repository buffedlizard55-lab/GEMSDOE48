"""Official distance-weighted Tversky metric and compatibility helpers.

The equations follow the DrivenData challenge page (fetched 2026-10-06):

    k(d) = max(1 - d / 300 m, 0)
    TPw = sum_g max_x p(x) k(d(x,g))
    FPw = sum_x p(x) [1 - max_g k(d(x,g))]
    FNw = sum_g [1 - max_x p(x) k(d(x,g))]
    DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw + eps)

The public API retains the helpers used by the earlier main-branch validation
(``coverage_field``, ``dti_components_fast``, ``dti_fast`` and ``dti_bruteforce``)
and also provides a validity-mask-aware function for spatial subdomains.
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
R_M = DEFAULT_RADIUS_M
PIXEL_M = DEFAULT_PIXEL_SIZE_M
R_PX = R_M / PIXEL_M
EPSILON = 1e-12
EPS = EPSILON


def triangular_kernel(distance_m: np.ndarray | float, radius_m: float = DEFAULT_RADIUS_M) -> np.ndarray:
    """Triangular distance credit ``max(1 - distance/radius, 0)``."""
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
    """At target (y,x), return values[y+dy,x+dx], zero outside the grid."""
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


def coverage_field(prediction: np.ndarray, truth_mask: np.ndarray | None = None) -> np.ndarray:
    """Return per-cell max kernel-weighted prediction credit.

    ``truth_mask`` is accepted for compatibility with the earlier implementation;
    coverage is computed over the full raster and callers select truth cells afterward.
    """
    p = np.asarray(prediction, dtype=np.float64)
    if p.ndim != 2:
        raise ValueError("prediction must be a 2-D array")
    p = np.where(np.isfinite(p), p, 0.0)
    best = np.zeros(p.shape, dtype=np.float64)
    for dy, dx, weight in _offsets(DEFAULT_RADIUS_M, DEFAULT_PIXEL_SIZE_M):
        candidate = _prediction_at_neighbor(p, dy, dx) * weight
        np.maximum(best, candidate, out=best)
    return best


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
    """Compute DTI components on a raster or a spatial evaluation domain.

    ``valid`` selects the evaluation domain. Predictions outside it are ignored;
    truth values outside it are ignored. For blocked tests, use a held-out block plus
    a kernel-radius halo so nearby predictions are included without counting distant
    predictions from other blocks as false positives.
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
    if not np.isfinite(pixel_size_m) or pixel_size_m <= 0:
        raise ValueError("pixel_size_m must be positive and finite")
    if not np.isfinite(alpha) or alpha < 0 or not np.isfinite(beta) or beta < 0:
        raise ValueError("alpha and beta must be finite and nonnegative")

    active_values = np.asarray(p_in[active], dtype=np.float64)
    if not np.isfinite(active_values).all() or np.any((active_values < 0.0) | (active_values > 1.0)):
        raise ValueError("prediction values in the valid domain must be finite and in [0, 1]")
    p = np.zeros(p_in.shape, dtype=np.float64)
    p[active] = active_values
    g = active & np.asarray(g_in, dtype=bool)
    n_truth = int(g.sum())
    if n_truth == 0:
        fp = float(p[active].sum(dtype=np.float64))
        return {"tp": 0.0, "fp": fp, "fn": 0.0, "n_truth": 0, "dti": 0.0, "coverage": 0.0}

    best_credit = np.zeros(p.shape, dtype=np.float64)
    for dy, dx, weight in _offsets(float(radius_m), float(pixel_size_m)):
        candidate = _prediction_at_neighbor(p, dy, dx) * weight
        np.maximum(best_credit, candidate, out=best_credit)
    tp = float(best_credit[g].sum(dtype=np.float64))
    fn = float(n_truth) - tp

    distance_to_truth = distance_transform_edt(~g, sampling=(pixel_size_m, pixel_size_m))
    nearest_truth_credit = triangular_kernel(distance_to_truth, radius_m)
    fp = float((p[active] * (1.0 - nearest_truth_credit[active])).sum(dtype=np.float64))
    denominator = tp + alpha * fp + beta * fn
    dti = float(tp / (denominator + EPSILON))
    return {"tp": tp, "fp": fp, "fn": fn, "n_truth": n_truth, "dti": dti, "coverage": float(tp / n_truth)}


def dti_components_fast(pred: np.ndarray, truth: np.ndarray) -> dict[str, float | int]:
    """Compatibility wrapper returning the previous project key names."""
    pred_array = np.asarray(pred)
    result = distance_weighted_tversky(pred_array, truth)
    return {
        "TPw": float(result["tp"]),
        "FPw": float(result["fp"]),
        "FNw": float(result["fn"]),
        "DTI": float(result["dti"]),
        "n_truth": int(result["n_truth"]),
        "n_pred_positive": int(np.count_nonzero(np.isfinite(pred_array) & (pred_array > 0))),
    }


def dti_fast(pred: np.ndarray, truth: np.ndarray) -> float:
    """Return only the competition DTI."""
    return float(dti_components_fast(pred, truth)["DTI"])


def dti_bruteforce(pred: np.ndarray, truth: np.ndarray) -> dict[str, float | int]:
    """Literal pixel-pair transcription used as an independent reference oracle."""
    p = np.where(np.isfinite(pred), pred, 0.0).astype(np.float64)
    g = np.asarray(truth) > 0
    gy, gx = np.nonzero(g)
    py, px = np.nonzero(p > 0)
    tp = 0.0
    fn = 0.0
    for i in range(len(gy)):
        best = 0.0
        for j in range(len(py)):
            distance = hypot((py[j] - gy[i]) * PIXEL_M, (px[j] - gx[i]) * PIXEL_M)
            if distance <= R_M:
                best = max(best, p[py[j], px[j]] * max(1.0 - distance / R_M, 0.0))
        tp += best
        fn += 1.0 - best
    fp = 0.0
    for j in range(len(py)):
        nearest_credit = 0.0
        for i in range(len(gy)):
            distance = hypot((py[j] - gy[i]) * PIXEL_M, (px[j] - gx[i]) * PIXEL_M)
            if distance <= R_M:
                nearest_credit = max(nearest_credit, max(1.0 - distance / R_M, 0.0))
        fp += p[py[j], px[j]] * (1.0 - nearest_credit)
    denominator = tp + ALPHA * fp + BETA * fn
    dti = float(tp / (denominator + EPSILON)) if len(gy) else 0.0
    return {"TPw": tp, "FPw": fp, "FNw": fn, "DTI": dti,
            "n_truth": int(len(gy)), "n_pred_positive": int(len(py))}
