"""H56 methods: open-world D-S mass assignment and strain-ridge screening.

The H56 sparse-family rule treats an omitted prediction as *mostly ignorance*,
not as a confident assertion of no fault. This is a modeling assumption, not
calibration. The deterministic, label-free strain-ridge transform follows the
explicit machine-readable H56-A frozen test; see the slate erratum for its prose
mismatch about an unspecified structure-tensor term.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi


@dataclass(frozen=True)
class DempsterMasses:
    """Normalized conjunctive masses and pre-normalization conflict."""

    fault: np.ndarray
    not_fault: np.ndarray
    ignorance: np.ndarray
    conflict: np.ndarray


def _surface(values: np.ndarray, name: str) -> np.ndarray:
    result = np.asarray(values, dtype=np.float64)
    if result.ndim < 1:
        raise ValueError(f"{name} must have at least one dimension")
    if not np.isfinite(result).all():
        raise ValueError(f"{name} contains nonfinite values")
    if np.any((result < 0.0) | (result > 1.0)):
        raise ValueError(f"{name} must be in [0, 1]")
    return result


def sparse_open_world_bpa(
    support: np.ndarray,
    *,
    reliability: float = 0.6,
    absence_informativeness: float = 0.1,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Assign fault, not-fault, and ignorance mass to a sparse-source surface.

    ``b`` is a [0, 1] support surface, ``r`` is an explicit source discount,
    and ``q`` is the fraction of the source's *lack of support* treated as
    evidence for no fault. The remaining lack-of-support mass stays on Theta::

        m(F)     = r * b
        m(not F) = r * q * (1 - b)
        m(Theta) = 1 - m(F) - m(not F)

    With the preregistered q=0.10, a zero-valued sparse cell is not treated as
    equivalent to a confident no-fault observation. q is not learned from the
    public proxies and is not an empirically calibrated probability.
    """
    b = _surface(support, "support")
    r = float(reliability)
    q = float(absence_informativeness)
    if not np.isfinite(r) or not (0.0 < r <= 1.0):
        raise ValueError("reliability must be finite and in (0, 1]")
    if not np.isfinite(q) or not (0.0 <= q <= 1.0):
        raise ValueError("absence_informativeness must be finite and in [0, 1]")

    fault = r * b
    not_fault = r * q * (1.0 - b)
    ignorance = 1.0 - fault - not_fault
    if np.any(ignorance < -1e-12) or np.any(ignorance > 1.0 + 1e-12):
        raise ArithmeticError("open-world BPA produced invalid ignorance mass")
    ignorance = np.clip(ignorance, 0.0, 1.0)
    return fault, not_fault, ignorance


def combine_open_world_dempster(
    source_a: tuple[np.ndarray, np.ndarray, np.ndarray],
    source_b: tuple[np.ndarray, np.ndarray, np.ndarray],
    *,
    denominator_epsilon: float = 1e-12,
) -> DempsterMasses:
    """Combine two [fault, not-fault, Theta] BPAs by normalized Dempster rule."""
    if len(source_a) != 3 or len(source_b) != 3:
        raise ValueError("each source must contain [fault, not_fault, ignorance]")
    a = tuple(np.asarray(v, dtype=np.float64) for v in source_a)
    b = tuple(np.asarray(v, dtype=np.float64) for v in source_b)
    if any(x.shape != y.shape for x, y in zip(a, b)):
        raise ValueError("source BPA shapes must match")
    if not a[0].ndim or any(not np.isfinite(v).all() or np.any(v < 0.0) for v in (*a, *b)):
        raise ValueError("source BPAs must be finite and nonnegative")
    for label, masses in (("a", a), ("b", b)):
        if not np.allclose(sum(masses), 1.0, rtol=0.0, atol=2e-10):
            raise ValueError(f"source {label} masses do not sum to one")

    f1, n1, u1 = a
    f2, n2, u2 = b
    conflict = f1 * n2 + n1 * f2
    denominator = 1.0 - conflict
    if np.any(denominator <= denominator_epsilon):
        raise ValueError("Dempster normalization is undefined at total conflict")

    fault = (f1 * f2 + f1 * u2 + u1 * f2) / denominator
    not_fault = (n1 * n2 + n1 * u2 + u1 * n2) / denominator
    ignorance = (u1 * u2) / denominator
    total = fault + not_fault + ignorance
    if not np.isfinite(total).all() or not np.allclose(total, 1.0, rtol=0.0, atol=2e-8):
        raise ArithmeticError("combined Dempster masses are not finite and normalized")
    for label, values in (("fault", fault), ("not-fault", not_fault), ("ignorance", ignorance), ("conflict", conflict)):
        if np.any(values < -1e-10) or np.any(values > 1.0 + 1e-10):
            raise ArithmeticError(f"combined {label} mass is outside [0, 1]")
    return DempsterMasses(
        fault=np.clip(fault, 0.0, 1.0),
        not_fault=np.clip(not_fault, 0.0, 1.0),
        ignorance=np.clip(ignorance, 0.0, 1.0),
        conflict=np.clip(conflict, 0.0, 1.0),
    )


def normalize_belief(belief: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Scale Bel(F) by its valid-domain maximum for a relative [0,1] surface."""
    bel = np.asarray(belief, dtype=np.float64)
    mask = np.asarray(footprint, dtype=bool)
    if bel.ndim != 2 or bel.shape != mask.shape:
        raise ValueError("belief and footprint must be matching 2-D arrays")
    if not mask.any() or not np.isfinite(bel).all():
        raise ValueError("belief must be finite and footprint nonempty")
    if np.any((bel < -1e-10) | (bel > 1.0 + 1e-10)):
        raise ValueError("belief must be in [0, 1]")
    scale = float(bel[mask].max())
    if scale <= 0.0:
        raise ValueError("belief has no positive in-footprint support")
    output = np.zeros(bel.shape, dtype=np.float32)
    output[mask] = np.clip(bel[mask] / scale, 0.0, 1.0).astype(np.float32)
    return output


def hessian_line_response(image: np.ndarray, sigma_px: float) -> np.ndarray:
    """Return a scale-normalized, polarity-invariant Hessian line response.

    The response is strongest when one Hessian eigenvalue dominates the other,
    i.e. curvature is concentrated across a line rather than an isotropic blob.
    It is an exploratory transform, not a calibrated fault probability.
    """
    x = np.asarray(image, dtype=np.float32)
    sigma = float(sigma_px)
    if x.ndim != 2 or min(x.shape) < 3:
        raise ValueError("image must be a 2-D grid at least 3 by 3")
    if not np.isfinite(x).all():
        raise ValueError("image must be finite; mask/nodata must be handled first")
    if not np.isfinite(sigma) or sigma <= 0:
        raise ValueError("sigma_px must be positive and finite")

    scale = np.float32(sigma * sigma)
    hxx = ndi.gaussian_filter(x, sigma=sigma, order=(0, 2), mode="nearest") * scale
    hxy = ndi.gaussian_filter(x, sigma=sigma, order=(1, 1), mode="nearest") * scale
    hyy = ndi.gaussian_filter(x, sigma=sigma, order=(2, 0), mode="nearest") * scale
    trace = hxx + hyy
    discriminant = np.sqrt(np.maximum((hxx - hyy) ** 2 + np.float32(4.0) * hxy ** 2, 0.0))
    eig1 = np.float32(0.5) * (trace + discriminant)
    eig2 = np.float32(0.5) * (trace - discriminant)
    abs1 = np.abs(eig1)
    abs2 = np.abs(eig2)
    large = np.maximum(abs1, abs2)
    small = np.minimum(abs1, abs2)
    ratio = np.zeros_like(large)
    np.divide(small, large, out=ratio, where=large > np.finfo(np.float32).eps)
    response = large * np.exp(np.float32(-0.5) * ratio * ratio)
    response[~np.isfinite(response)] = 0.0
    return response.astype(np.float32, copy=False)


def robust_unit_scale(values: np.ndarray, valid: np.ndarray, percentile: float = 99.5) -> tuple[np.ndarray, float]:
    """Clip a nonnegative field at a valid-domain quantile and map to [0,1]."""
    x = np.asarray(values, dtype=np.float32)
    mask = np.asarray(valid, dtype=bool)
    p = float(percentile)
    if x.ndim != 2 or x.shape != mask.shape:
        raise ValueError("values and valid must be matching 2-D arrays")
    if not np.isfinite(x).all() or np.any(x < 0.0):
        raise ValueError("values must be finite and nonnegative")
    if not mask.any() or not (0.0 < p <= 100.0):
        raise ValueError("valid must be nonempty and percentile must be in (0, 100]")
    high = float(np.percentile(x[mask], p))
    if not np.isfinite(high) or high <= 0.0:
        return np.zeros_like(x), high
    output = np.zeros_like(x)
    np.clip(x / np.float32(high), 0.0, 1.0, out=output)
    output[~mask] = 0.0
    return output, high


def deterministic_top_k(values: np.ndarray, valid: np.ndarray, k: int) -> np.ndarray:
    """Return exactly k valid cells, descending score then ascending flat index."""
    x = np.asarray(values, dtype=np.float32)
    mask = np.asarray(valid, dtype=bool)
    if x.ndim != 2 or x.shape != mask.shape or not np.isfinite(x).all():
        raise ValueError("values and valid must be matching finite 2-D arrays")
    indices = np.flatnonzero(mask.ravel())
    count = int(k)
    if count < 0 or count > indices.size:
        raise ValueError("k must be between zero and the number of valid cells")
    out = np.zeros(x.size, dtype=bool)
    if count == 0:
        return out.reshape(x.shape)
    flat = x.ravel()
    scores = flat[indices]
    threshold = np.partition(scores, scores.size - count)[scores.size - count]
    above = indices[scores > threshold]
    tied = indices[scores == threshold]
    remaining = count - above.size
    chosen = np.concatenate((above, tied[:remaining]))
    out[chosen] = True
    return out.reshape(x.shape)
