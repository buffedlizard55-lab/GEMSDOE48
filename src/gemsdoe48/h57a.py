"""Frozen H57-A radiometric-residual / magnetic-gradient screening helpers.

This module builds a deterministic feature ranking, not a fault probability. GeoDAWN
uint8 channels are ordinal, quantized mirror values; the robust K~Th residual and
TMI-up150 gradient are only relative anomaly indicators. The experiment's thresholds
and fixed addition budget live in ``docs/research/hypotheses-h57-20261007.md``.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi


@dataclass(frozen=True)
class HuberFit:
    intercept: float
    slope: float
    residual_center: float
    residual_scale: float
    iterations: int


def _matching_2d(*arrays: np.ndarray) -> tuple[np.ndarray, ...]:
    converted = tuple(np.asarray(array) for array in arrays)
    if not converted or any(array.ndim != 2 for array in converted):
        raise ValueError("all inputs must be 2-D arrays")
    if any(array.shape != converted[0].shape for array in converted[1:]):
        raise ValueError("all inputs must have matching shapes")
    return converted


def _weighted_line(x: np.ndarray, y: np.ndarray, weights: np.ndarray) -> tuple[float, float]:
    """Solve a weighted least-squares line without allocating a design matrix."""
    sw = float(weights.sum(dtype=np.float64))
    if not np.isfinite(sw) or sw <= 0.0:
        raise ValueError("Huber regression has no positive finite weights")
    swx = float(np.dot(weights, x))
    swy = float(np.dot(weights, y))
    swxx = float(np.dot(weights, x * x))
    swxy = float(np.dot(weights, x * y))
    determinant = sw * swxx - swx * swx
    if determinant <= np.finfo(np.float64).eps * max(sw * swxx, 1.0):
        # A constant Th channel carries no slope information; use a constant fit.
        return swy / sw, 0.0
    slope = (sw * swxy - swx * swy) / determinant
    intercept = (swy - slope * swx) / sw
    return float(intercept), float(slope)


def fit_huber_line(
    x: np.ndarray,
    y: np.ndarray,
    *,
    max_iter: int = 5,
    huber_c: float = 1.345,
) -> HuberFit:
    """Fit ``y = intercept + slope*x`` with deterministic Huber IRLS.

    The residual center/scale are the median and 1.4826*MAD of the final residuals.
    The Huber cutoff at each iteration is ``huber_c * 1.4826*MAD``. Inputs are
    flattened, finite paired samples; caller chooses the valid geographic domain.
    """
    xv = np.asarray(x, dtype=np.float64).reshape(-1)
    yv = np.asarray(y, dtype=np.float64).reshape(-1)
    if xv.size != yv.size or xv.size < 3:
        raise ValueError("x and y must have matching vectors with at least 3 samples")
    if not np.isfinite(xv).all() or not np.isfinite(yv).all():
        raise ValueError("Huber regression inputs must be finite")
    if not isinstance(max_iter, int) or max_iter < 1:
        raise ValueError("max_iter must be a positive integer")
    if not np.isfinite(huber_c) or huber_c <= 0.0:
        raise ValueError("huber_c must be positive and finite")

    weights = np.ones(xv.size, dtype=np.float64)
    intercept, slope = _weighted_line(xv, yv, weights)
    actual_iterations = 0
    for actual_iterations in range(1, max_iter + 1):
        residual = yv - (intercept + slope * xv)
        center = float(np.median(residual))
        scale = 1.4826 * float(np.median(np.abs(residual - center)))
        if not np.isfinite(scale) or scale <= np.finfo(np.float64).eps:
            break
        cutoff = huber_c * scale
        deviation = np.abs(residual - center)
        weights = np.ones_like(deviation)
        np.divide(cutoff, deviation, out=weights, where=deviation > cutoff)
        intercept, slope = _weighted_line(xv, yv, weights)

    final_residual = yv - (intercept + slope * xv)
    residual_center = float(np.median(final_residual))
    residual_scale = 1.4826 * float(np.median(np.abs(final_residual - residual_center)))
    return HuberFit(intercept, slope, residual_center, residual_scale, actual_iterations)


def robust_residual_z(
    x: np.ndarray,
    y: np.ndarray,
    fit: HuberFit,
    valid: np.ndarray,
) -> np.ndarray:
    """Return median/MAD-standardized K~Th residuals; invalid cells are zero."""
    x, y, mask = _matching_2d(x, y, valid)
    mask = mask.astype(bool, copy=False)
    if not mask.any():
        raise ValueError("valid mask is empty")
    xv = x.astype(np.float64, copy=False)
    yv = y.astype(np.float64, copy=False)
    if not np.isfinite(xv[mask]).all() or not np.isfinite(yv[mask]).all():
        raise ValueError("valid regression cells must be finite")
    residual = yv[mask] - (fit.intercept + fit.slope * xv[mask])
    center = float(np.median(residual))
    scale = 1.4826 * float(np.median(np.abs(residual - center)))
    if not np.isfinite(scale) or scale <= np.finfo(np.float64).eps:
        raise ValueError("robust residual MAD is zero or nonfinite")
    result = np.zeros(xv.shape, dtype=np.float32)
    result[mask] = ((yv[mask] - (fit.intercept + fit.slope * xv[mask]) - center) / scale).astype(np.float32)
    return result


def magnetic_gradient_magnitude(
    tmi: np.ndarray,
    valid: np.ndarray,
    *,
    pixel_size_m: float = 100.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Compute |∇TMI| and a one-cell-eroded validity mask.

    Eroding the mask before scoring prevents the uint8 nodata edge (zero) from
    becoming an artificial high-gradient line. Gradients are in quantized-value
    units per metre, not calibrated magnetic field units.
    """
    image, mask = _matching_2d(tmi, valid)
    mask = mask.astype(bool, copy=False)
    pixel = float(pixel_size_m)
    if not np.isfinite(pixel) or pixel <= 0.0:
        raise ValueError("pixel_size_m must be positive and finite")
    if not mask.any():
        raise ValueError("valid magnetic mask is empty")
    if not np.isfinite(image[mask]).all():
        raise ValueError("valid magnetic values must be finite")

    inner = ndi.binary_erosion(mask, structure=np.ones((3, 3), dtype=bool), border_value=0)
    surface = np.where(mask, image, 0).astype(np.float64, copy=False)
    gy, gx = np.gradient(surface, pixel, pixel)
    magnitude = np.hypot(gx, gy).astype(np.float32)
    magnitude[~inner] = 0.0
    return magnitude, inner


def deterministic_top_k(values: np.ndarray, valid: np.ndarray, k: int) -> np.ndarray:
    """Select up to k valid cells by descending value, then row-major tie break."""
    scores, mask = _matching_2d(values, valid)
    scores = scores.astype(np.float64, copy=False)
    mask = mask.astype(bool, copy=False)
    if not np.isfinite(scores).all():
        raise ValueError("ranking scores must be finite")
    count = int(k)
    if count < 0:
        raise ValueError("k must be nonnegative")
    indices = np.flatnonzero(mask.ravel())
    take = min(count, indices.size)
    selected = np.zeros(mask.size, dtype=bool)
    if take:
        local_scores = scores.ravel()[indices]
        order = np.lexsort((indices, -local_scores))
        selected[indices[order[:take]]] = True
    return selected.reshape(mask.shape)


def make_addition_surface(
    baseline: np.ndarray,
    additions: np.ndarray,
    footprint: np.ndarray,
) -> np.ndarray:
    """Preserve all baseline probabilities and set added cells to one."""
    base, add, mask = _matching_2d(baseline, additions, footprint)
    base = base.astype(np.float64, copy=False)
    add = add.astype(bool, copy=False)
    mask = mask.astype(bool, copy=False)
    if not np.isfinite(base).all() or np.any((base < 0.0) | (base > 1.0)):
        raise ValueError("baseline must be finite and in [0, 1]")
    if np.any(add & ~mask):
        raise ValueError("additions must be inside the footprint")
    result = np.where(mask, base, 0.0).astype(np.float32)
    result[add] = 1.0
    return result
