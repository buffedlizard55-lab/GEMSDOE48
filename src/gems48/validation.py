"""Exact raster implementation of the competition's distance-weighted Tversky index.

The organizer's metric weights each truth pixel by the maximum nearby
prediction *times* its triangular distance kernel, and weights each prediction
by its confidence times the complement of its nearest-truth kernel. Binary
Euclidean distance transforms alone are not sufficient for fractional
predictions.
"""
from __future__ import annotations

from collections.abc import Mapping
import math

import numpy as np
from scipy.ndimage import distance_transform_edt


def _validate_grid(
    prediction: np.ndarray,
    ground_truth: np.ndarray,
    evaluation_mask: np.ndarray,
    pixel_size_yx_m: tuple[float, float],
    radius_m: float,
    alpha: float,
    beta: float,
):
    pred = np.asarray(prediction, dtype=np.float32)
    truth_raw = np.asarray(ground_truth)
    valid = np.asarray(evaluation_mask, dtype=bool)
    if pred.ndim != 2 or truth_raw.ndim != 2 or valid.ndim != 2:
        raise ValueError("prediction, ground_truth, and evaluation_mask must be 2-D")
    if pred.shape != truth_raw.shape or pred.shape != valid.shape:
        raise ValueError("prediction, ground_truth, and evaluation_mask grids must match")
    if np.issubdtype(truth_raw.dtype, np.number):
        if not np.isfinite(truth_raw).all():
            raise ValueError("ground_truth must be finite")
        if np.any((truth_raw != 0) & (truth_raw != 1)):
            raise ValueError("ground_truth must be binary")
    truth = truth_raw.astype(bool, copy=False)
    if not np.isfinite(pred[valid]).all():
        raise ValueError("prediction must be finite on evaluated pixels")
    if np.any((pred[valid] < 0) | (pred[valid] > 1)):
        raise ValueError("prediction must be in [0, 1] on evaluated pixels")
    if len(pixel_size_yx_m) != 2:
        raise ValueError("pixel_size_yx_m must contain (row_size, column_size)")
    py, px = map(float, pixel_size_yx_m)
    if not (math.isfinite(py) and math.isfinite(px) and py > 0 and px > 0):
        raise ValueError("pixel sizes must be finite and positive")
    if not (math.isfinite(radius_m) and radius_m > 0):
        raise ValueError("radius_m must be finite and positive")
    if not (math.isfinite(alpha) and math.isfinite(beta) and alpha >= 0 and beta >= 0):
        raise ValueError("alpha and beta must be finite and non-negative")
    if alpha == 0 and beta == 0:
        raise ValueError("alpha and beta cannot both be zero")
    return pred, truth, valid, (py, px)


def _maximum_weighted_prediction(
    prediction: np.ndarray,
    radius_m: float,
    pixel_size_yx_m: tuple[float, float],
) -> np.ndarray:
    """At every truth-cell center, calculate max_x p(x) * k(distance(x, g)).

    Only offsets with non-zero triangular-kernel weight are visited. This
    implements the organizer's per-truth maximum exactly on a north-up regular
    raster, including fractional prediction values.
    """
    height, width = prediction.shape
    py, px = pixel_size_yx_m
    max_dy = int(math.ceil(radius_m / py))
    max_dx = int(math.ceil(radius_m / px))
    best = np.zeros(prediction.shape, dtype=np.float32)
    for dy in range(-max_dy, max_dy + 1):
        for dx in range(-max_dx, max_dx + 1):
            distance = math.hypot(dy * py, dx * px)
            if distance >= radius_m:
                continue
            weight = np.float32(1.0 - distance / radius_m)
            # A prediction at (truth_y + dy, truth_x + dx) contributes to the
            # truth pixel at (truth_y, truth_x).
            src_y0, src_y1 = max(0, dy), min(height, height + dy)
            src_x0, src_x1 = max(0, dx), min(width, width + dx)
            dst_y0, dst_y1 = max(0, -dy), min(height, height - dy)
            dst_x0, dst_x1 = max(0, -dx), min(width, width - dx)
            if src_y0 >= src_y1 or src_x0 >= src_x1:
                continue
            source = prediction[src_y0:src_y1, src_x0:src_x1]
            target = best[dst_y0:dst_y1, dst_x0:dst_x1]
            np.maximum(target, source * weight, out=target)
    return best


def _nearest_truth_kernel(
    truth: np.ndarray,
    radius_m: float,
    pixel_size_yx_m: tuple[float, float],
) -> np.ndarray:
    """Return max_g k(distance(x, g)) for every raster pixel x."""
    if not truth.any():
        return np.zeros(truth.shape, dtype=np.float32)
    distance = distance_transform_edt(~truth, sampling=pixel_size_yx_m)
    return np.maximum(1.0 - distance / radius_m, 0.0).astype(np.float32)


def score_dti_regions(
    prediction: np.ndarray,
    ground_truth: np.ndarray,
    evaluation_mask: np.ndarray,
    regions: Mapping[str, np.ndarray],
    *,
    radius_m: float = 300.0,
    pixel_size_yx_m: tuple[float, float] = (100.0, 100.0),
    alpha: float = 0.2,
    beta: float = 0.8,
) -> dict[str, dict[str, float | int]]:
    """Score named spatial regions using the official full-scene distances.

    Distance neighborhoods are calculated over the full valid raster, then TP,
    FP, and FN contributions are accumulated only in each named region. This
    avoids artificial distance truncation at a validation block boundary and
    applies an optional exclusion mask (e.g. known USGS/INGENIOUS fault pixels)
    to every metric term.
    """
    pred, truth, valid, spacing = _validate_grid(
        prediction, ground_truth, evaluation_mask, pixel_size_yx_m,
        radius_m, alpha, beta,
    )
    if not regions:
        raise ValueError("at least one scoring region is required")

    truth_eval = truth & valid
    # Predictions on excluded/out-of-footprint cells are not evaluated and
    # cannot provide TP credit to nearby labels.
    pred_eval = np.zeros(pred.shape, dtype=np.float32)
    pred_eval[valid] = pred[valid]
    tp_weight = _maximum_weighted_prediction(pred_eval, radius_m, spacing)
    truth_kernel = _nearest_truth_kernel(truth_eval, radius_m, spacing)

    results: dict[str, dict[str, float | int]] = {}
    for name, region_array in regions.items():
        region = np.asarray(region_array, dtype=bool)
        if region.shape != pred.shape:
            raise ValueError(f"region {name!r} grid does not match prediction")
        evaluated = valid & region
        local_truth = truth_eval & region
        truth_count = int(np.count_nonzero(local_truth))
        tp = float(np.sum(tp_weight[local_truth], dtype=np.float64))
        fn = float(truth_count - tp)
        fp = float(np.sum(
            pred_eval[evaluated] * (1.0 - truth_kernel[evaluated]),
            dtype=np.float64,
        ))
        mass = float(np.sum(pred_eval[evaluated], dtype=np.float64))
        denominator = tp + alpha * fp + beta * fn
        dti = tp / denominator if denominator > 0.0 else 0.0
        results[name] = {
            "dti": float(dti),
            "tp": tp,
            "fp": fp,
            "fn": fn,
            "truth_pixels": truth_count,
            "prediction_mass": mass,
            "evaluated_pixels": int(np.count_nonzero(evaluated)),
        }
    return results


def score_dti(
    prediction: np.ndarray,
    ground_truth: np.ndarray,
    evaluation_mask: np.ndarray,
    *,
    radius_m: float = 300.0,
    pixel_size_yx_m: tuple[float, float] = (100.0, 100.0),
    alpha: float = 0.2,
    beta: float = 0.8,
) -> dict[str, float | int]:
    """Return the organizer-defined distance-weighted Tversky score."""
    valid = np.asarray(evaluation_mask, dtype=bool)
    return score_dti_regions(
        prediction,
        ground_truth,
        valid,
        {"all": valid},
        radius_m=radius_m,
        pixel_size_yx_m=pixel_size_yx_m,
        alpha=alpha,
        beta=beta,
    )["all"]
