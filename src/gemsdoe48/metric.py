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

from dataclasses import dataclass
from functools import lru_cache
from math import ceil, hypot
from typing import ClassVar, Iterable

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
KERNEL_REACH_M = DEFAULT_RADIUS_M
PIXEL_SIZE_M = DEFAULT_PIXEL_SIZE_M
R_M = DEFAULT_RADIUS_M
PIXEL_M = DEFAULT_PIXEL_SIZE_M
R_PX = R_M / PIXEL_M


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


# Stable compatibility surface used by the earlier upstream implementation.
OFFSETS = _offsets(DEFAULT_RADIUS_M, DEFAULT_PIXEL_SIZE_M)
N_OFFSETS = len(OFFSETS)
K_VALUES = np.asarray([weight for _, _, weight in OFFSETS], dtype=np.float64)
DR = np.asarray([dy for dy, _, _ in OFFSETS], dtype=np.int64)
DC = np.asarray([dx for _, dx, _ in OFFSETS], dtype=np.int64)


def kernel_offsets(pixel_size_m: float = DEFAULT_PIXEL_SIZE_M, reach_m: float = DEFAULT_RADIUS_M):
    """Return all non-zero integer-grid offsets and their triangular weights."""
    return _offsets(float(reach_m), float(pixel_size_m))


def offsets_as_tuples() -> Iterable[tuple[int, int, float]]:
    """Compatibility helper returning the registered kernel offsets."""
    return tuple(OFFSETS)


def _shift(values: np.ndarray, dy: int, dx: int, fill: float = 0.0) -> np.ndarray:
    """Move an array by ``(+dy,+dx)`` with constant fill and no wraparound."""
    arr = np.asarray(values)
    if arr.ndim != 2:
        raise ValueError("shift input must be 2-D")
    h, w = arr.shape
    out = np.full(arr.shape, fill, dtype=np.float64)
    r0, r1 = max(dy, 0), min(h, h + dy)
    c0, c1 = max(dx, 0), min(w, w + dx)
    if r0 < r1 and c0 < c1:
        out[r0:r1, c0:c1] = arr[r0 - dy:r1 - dy, c0 - dx:c1 - dx]
    return out


def max_credit_field(field: np.ndarray) -> np.ndarray:
    """For every target pixel, maximum nearby prediction times kernel weight."""
    values = np.asarray(field, dtype=np.float64)
    if values.ndim != 2:
        raise ValueError("field must be 2-D")
    values = np.where(np.isfinite(values), values, 0.0)
    best = np.zeros(values.shape, dtype=np.float64)
    for dy, dx, weight in OFFSETS:
        np.maximum(best, _shift(values, dy, dx) * weight, out=best)
    return best


def max_kernel_to_truth(truth_mask: np.ndarray) -> np.ndarray:
    """Return max kernel credit from any truth pixel at every grid cell."""
    truth = np.asarray(truth_mask, dtype=bool)
    if truth.ndim != 2:
        raise ValueError("truth_mask must be 2-D")
    values = truth.astype(np.float64)
    best = np.zeros(values.shape, dtype=np.float64)
    for dy, dx, weight in OFFSETS:
        np.maximum(best, _shift(values, dy, dx) * weight, out=best)
    return best


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
    """Return maximum nearby prediction credit, optionally only at truth pixels.

    Without ``truth_mask`` this is the full per-cell max-credit field. With a mask,
    values away from truth pixels are zero, matching the upstream helper contract.
    """
    best = max_credit_field(prediction)
    if truth_mask is None:
        return best
    truth = np.asarray(truth_mask, dtype=bool)
    if truth.shape != best.shape:
        raise ValueError("truth_mask shape does not match prediction")
    return np.where(truth, best, 0.0)


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


@dataclass(frozen=True)
class DTIResult:
    """Metric components with attributes and a mapping-compatible legacy view."""

    dti: float
    tpw: float
    fpw: float
    fnw: float
    mass: float
    self_credit: float
    n_truth: int
    n_emitted: int
    coverage: float

    _ALIASES: ClassVar[dict[str, str]] = {
        "DTI": "dti", "dti": "dti", "TPw": "tpw", "tpw": "tpw",
        "FPw": "fpw", "fpw": "fpw", "FNw": "fnw", "fnw": "fnw",
        "S": "mass", "M": "self_credit", "mass": "mass",
        "self_credit": "self_credit", "n_truth": "n_truth",
        "n_emitted": "n_emitted", "n_pred_positive": "n_emitted", "coverage": "coverage",
    }

    def __getitem__(self, key: str):
        try:
            return getattr(self, self._ALIASES[key])
        except KeyError as exc:
            raise KeyError(f"{key!r} is not a metric component") from exc

    def keys(self) -> list[str]:
        return sorted(self._ALIASES)

    def as_dict(self) -> dict[str, float | int]:
        return {
            "dti": self.dti, "tpw": self.tpw, "fpw": self.fpw, "fnw": self.fnw,
            "mass": self.mass, "self_credit": self.self_credit,
            "n_truth": self.n_truth, "n_emitted": self.n_emitted,
            "coverage": self.coverage,
        }


def dti(
    prediction: np.ndarray,
    truth_mask: np.ndarray,
    footprint: np.ndarray | None = None,
    *,
    validate: bool = True,
    precomputed_max_kernel: np.ndarray | None = None,
) -> DTIResult:
    """Return exact official DTI components for a full-grid prediction surface."""
    p = np.asarray(prediction, dtype=np.float64)
    if p.ndim != 2:
        raise ValueError(f"prediction must be 2-D, got shape {p.shape}")
    p = np.where(np.isfinite(p), p, 0.0)
    truth = np.asarray(truth_mask).astype(bool, copy=True)
    if truth.shape != p.shape:
        raise ValueError(f"truth {truth.shape} != prediction {p.shape}")
    if validate and np.any((p < 0.0) | (p > 1.0)):
        bad = int(((p < 0.0) | (p > 1.0)).sum())
        raise ValueError(f"{bad} prediction values outside [0, 1]")
    if footprint is not None:
        active = np.asarray(footprint, dtype=bool)
        if active.shape != p.shape:
            raise ValueError("footprint shape mismatch")
        p = np.where(active, p, 0.0)
        truth &= active

    mass = float(p.sum(dtype=np.float64))
    n_emitted = int(np.count_nonzero(p > 0.0))
    n_truth = int(truth.sum())
    credit = max_credit_field(p)
    if precomputed_max_kernel is None:
        kernel_to_truth = max_kernel_to_truth(truth)
    else:
        kernel_to_truth = np.asarray(precomputed_max_kernel, dtype=np.float64)
        if kernel_to_truth.shape != p.shape:
            raise ValueError("precomputed_max_kernel shape mismatch")
    tpw = float(credit[truth].sum(dtype=np.float64))
    self_credit = float((p * kernel_to_truth).sum(dtype=np.float64))
    fpw = float(mass - self_credit)
    fnw = float(n_truth - tpw)
    denominator = tpw + ALPHA * fpw + BETA * fnw + EPSILON
    score = float(tpw / denominator) if denominator > 0.0 else 0.0
    return DTIResult(
        dti=score, tpw=tpw, fpw=fpw, fnw=fnw, mass=mass,
        self_credit=self_credit, n_truth=n_truth, n_emitted=n_emitted,
        coverage=float(tpw / n_truth) if n_truth else float("nan"),
    )


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


def dti_bruteforce(
    prediction: np.ndarray,
    truth_mask: np.ndarray,
    footprint: np.ndarray | None = None,
) -> DTIResult:
    """Literal pixel-pair transcription used as an independent reference oracle."""
    p = np.asarray(prediction, dtype=np.float64)
    if p.ndim != 2:
        raise ValueError("prediction must be 2-D")
    p = np.where(np.isfinite(p), p, 0.0)
    truth = np.asarray(truth_mask).astype(bool, copy=True)
    if truth.shape != p.shape:
        raise ValueError("truth shape mismatch")
    if footprint is not None:
        active = np.asarray(footprint, dtype=bool)
        if active.shape != p.shape:
            raise ValueError("footprint shape mismatch")
        p = np.where(active, p, 0.0)
        truth &= active

    gy, gx = np.nonzero(truth)
    py, px = np.nonzero(p > 0.0)
    if gy.size == 0:
        raise ValueError("no truth pixels")
    tpw = 0.0
    for r, c in zip(gy, gx):
        best = 0.0
        for pr, pc in zip(py, px):
            distance = hypot((pr - r) * PIXEL_M, (pc - c) * PIXEL_M)
            if distance < R_M:
                best = max(best, float(p[pr, pc]) * max(1.0 - distance / R_M, 0.0))
        tpw += best

    fpw = 0.0
    self_credit = 0.0
    for pr, pc in zip(py, px):
        nearest = 0.0
        for r, c in zip(gy, gx):
            distance = hypot((pr - r) * PIXEL_M, (pc - c) * PIXEL_M)
            if distance < R_M:
                nearest = max(nearest, max(1.0 - distance / R_M, 0.0))
        value = float(p[pr, pc])
        fpw += value * (1.0 - nearest)
        self_credit += value * nearest

    n_truth = int(gy.size)
    mass = float(p.sum(dtype=np.float64))
    fnw = float(n_truth - tpw)
    denominator = tpw + ALPHA * fpw + BETA * fnw + EPSILON
    return DTIResult(
        dti=float(tpw / denominator), tpw=float(tpw), fpw=float(fpw), fnw=fnw,
        mass=mass, self_credit=float(self_credit), n_truth=n_truth,
        n_emitted=int(py.size), coverage=float(tpw / n_truth),
    )


def credit_bar(dti_value: float) -> float:
    """Return ``alpha * DTI`` for the special one-pixel credit/cost case.

    This is a local algebraic boundary when changing one unit prediction changes
    weighted TP by ``k``, weighted FP by ``1-k``, and weighted FN by ``-k``.
    It is not a universal per-cell threshold for arbitrary raster additions.
    """
    return ALPHA * float(dti_value)


def optimal_value_is_binary() -> str:
    """Summarize the coordinate-wise endpoint result; no fixed threshold is implied."""
    return "a binary {0,1} maximizer exists; arbitrary thresholding is not guaranteed"


def dilate(mask: np.ndarray, radius_px: int) -> np.ndarray:
    """Boolean cross-structure dilation by ``radius_px`` iterations."""
    out = np.asarray(mask, dtype=bool).copy()
    for _ in range(int(radius_px)):
        current = out
        up = np.zeros_like(current); up[1:, :] = current[:-1, :]
        down = np.zeros_like(current); down[:-1, :] = current[1:, :]
        left = np.zeros_like(current); left[:, 1:] = current[:, :-1]
        right = np.zeros_like(current); right[:, :-1] = current[:, 1:]
        out = current | up | down | left | right
    return out
