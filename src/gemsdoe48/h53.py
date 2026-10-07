"""H53 research utilities: multiband radiometric edges and three-source D-S fusion.

This module is deliberately label-free. Its radiometric edge field is an indirect
structural proxy, not a fault probability; the Dempster result is not calibrated.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy import ndimage as ndi


@dataclass(frozen=True)
class EdgeResult:
    score: np.ndarray
    strength: np.ndarray
    coherence: np.ndarray
    band_scale_p99: tuple[tuple[float, ...], ...]
    valid_edge_cells: int


def multiband_edge_coherence(
    bands: np.ndarray,
    valid_mask: np.ndarray,
    *,
    sigmas: tuple[float, ...] = (1.0, 3.0),
    pctl: float = 99.0,
    min_mask_weight: float = 0.99,
) -> EdgeResult:
    """Compute an unsupervised, multiscale, cross-band edge-coherence score.

    Parameters
    ----------
    bands:
        Array shaped ``(n_bands, height, width)``. Bands may have different
        value ranges; each band/scale's gradient magnitude is normalized by its
        own P99 over cells with complete mask support.
    valid_mask:
        True where all input bands are valid. Invalid cells are masked during
        Gaussian smoothing and are zeroed in the output.
    sigmas:
        Gaussian smoothing scales in pixels. The competition grid is 100 m, so
        the default scales correspond to approximately 100 m and 300 m.
    pctl:
        Fixed per-band/per-scale magnitude percentile used for robust clipping.
    min_mask_weight:
        Minimum Gaussian support fraction for computing a derivative, avoiding
        artificial gradients at nodata boundaries.

    Returns
    -------
    EdgeResult
        ``score = mean(clipped magnitude) * doubled-angle coherence``. Coherence
        treats opposite gradient signs as the same edge orientation. Scores are
        clipped to [0, 1]; no catalogue, SGMC, or competition labels are read.
    """
    values = np.asarray(bands)
    valid = np.asarray(valid_mask, dtype=bool)
    if values.ndim != 3:
        raise ValueError("bands must have shape (n_bands, height, width)")
    if valid.shape != values.shape[1:]:
        raise ValueError("valid_mask shape must match the band raster dimensions")
    if values.shape[0] < 2:
        raise ValueError("at least two bands are required for cross-band coherence")
    if not np.isfinite(values[:, valid]).all():
        raise ValueError("valid radiometric samples must be finite")
    if not sigmas or any((not np.isfinite(s) or s <= 0) for s in sigmas):
        raise ValueError("sigmas must be a nonempty sequence of positive finite values")
    if not (0.0 < pctl < 100.0):
        raise ValueError("pctl must be strictly between 0 and 100")
    if not (0.0 < min_mask_weight <= 1.0):
        raise ValueError("min_mask_weight must be in (0, 1]")

    n_bands, height, width = values.shape
    n_passes = n_bands * len(sigmas)
    sum_magnitude = np.zeros((height, width), dtype=np.float32)
    sum_cos2 = np.zeros_like(sum_magnitude)
    sum_sin2 = np.zeros_like(sum_magnitude)
    p99_values: list[tuple[float, ...]] = []
    valid_edge = np.zeros((height, width), dtype=bool)
    valid_float = valid.astype(np.float32)
    eps = np.float32(1e-12)

    for sigma in sigmas:
        weight = ndi.gaussian_filter(valid_float, sigma=float(sigma), mode="nearest")
        usable = valid & (weight >= min_mask_weight)
        valid_edge |= usable
        per_band: list[float] = []
        for band_index in range(n_bands):
            source = np.asarray(values[band_index], dtype=np.float32)
            weighted_source = np.where(valid, source, 0.0).astype(np.float32, copy=False)
            smooth = ndi.gaussian_filter(weighted_source, sigma=float(sigma), mode="nearest")
            np.divide(smooth, weight, out=smooth, where=weight > 1e-8)
            smooth[weight <= 1e-8] = 0.0

            # Sobel divided by 8 is a central-difference-scale derivative in
            # source-value units per pixel. Axis 1 is easting; axis 0 is northing.
            gx = ndi.sobel(smooth, axis=1, mode="nearest")
            gy = ndi.sobel(smooth, axis=0, mode="nearest")
            gx *= np.float32(0.125)
            gy *= np.float32(0.125)
            magnitude = np.hypot(gx, gy).astype(np.float32, copy=False)
            if usable.any():
                p99 = float(np.percentile(magnitude[usable], pctl))
            else:
                p99 = 0.0
            per_band.append(p99)

            if p99 > 0.0 and np.isfinite(p99):
                magnitude /= np.float32(p99)
                np.clip(magnitude, 0.0, 1.0, out=magnitude)
            else:
                magnitude.fill(0.0)

            # cos(2 theta) and sin(2 theta) make the orientation invariant to
            # reversing an edge's gradient direction (theta and theta+pi).
            gx2 = gx * gx
            gy2 = gy * gy
            denominator = gx2 + gy2
            cos2 = np.zeros_like(magnitude)
            sin2 = np.zeros_like(magnitude)
            np.divide(gx2 - gy2, denominator, out=cos2, where=denominator > eps)
            np.divide(2.0 * gx * gy, denominator, out=sin2, where=denominator > eps)
            magnitude[~usable] = 0.0
            cos2[~usable] = 0.0
            sin2[~usable] = 0.0
            sum_magnitude += magnitude
            sum_cos2 += magnitude * cos2
            sum_sin2 += magnitude * sin2
            del weighted_source, smooth, gx, gy, magnitude, gx2, gy2, denominator, cos2, sin2
        p99_values.append(tuple(per_band))
        del weight, usable

    strength = sum_magnitude / np.float32(n_passes)
    coherence = np.zeros_like(strength)
    np.divide(
        np.hypot(sum_cos2, sum_sin2),
        sum_magnitude,
        out=coherence,
        where=sum_magnitude > eps,
    )
    np.clip(coherence, 0.0, 1.0, out=coherence)
    score = strength * coherence
    np.clip(score, 0.0, 1.0, out=score)
    score[~valid] = 0.0
    strength[~valid] = 0.0
    coherence[~valid] = 0.0
    return EdgeResult(
        score=score.astype(np.float32, copy=False),
        strength=strength.astype(np.float32, copy=False),
        coherence=coherence.astype(np.float32, copy=False),
        band_scale_p99=tuple(p99_values),
        valid_edge_cells=int(valid_edge.sum()),
    )


def simple_support_bpa(belief: np.ndarray, reliability: float) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return two-sided simple-support masses (fault, not-fault, ignorance)."""
    if not np.isfinite(reliability) or not (0.0 < reliability <= 1.0):
        raise ValueError("reliability must be in (0, 1]")
    support = np.clip(np.asarray(belief, dtype=np.float32), 0.0, 1.0)
    fault = np.float32(reliability) * support
    not_fault = np.float32(reliability) * (1.0 - support)
    ignorance = np.float32(1.0) - fault - not_fault
    return fault, not_fault, ignorance


def radiometric_bpa(
    edge: np.ndarray,
    reliability: float = 0.25,
    absence_informativeness: float = 0.10,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """A weak, asymmetric radiometric BPA; lack of an edge is mostly ignorance."""
    if not np.isfinite(reliability) or not (0.0 < reliability <= 1.0):
        raise ValueError("reliability must be in (0, 1]")
    if not np.isfinite(absence_informativeness) or not (0.0 <= absence_informativeness <= 1.0):
        raise ValueError("absence_informativeness must be in [0, 1]")
    support = np.clip(np.asarray(edge, dtype=np.float32), 0.0, 1.0)
    rho = np.float32(reliability)
    absence = np.float32(absence_informativeness)
    fault = rho * support
    not_fault = rho * (1.0 - support) * absence
    ignorance = np.float32(1.0) - fault - not_fault
    return fault, not_fault, ignorance


def dempster_two(
    a: tuple[np.ndarray, np.ndarray, np.ndarray],
    b: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Combine two BPAs; return normalized masses and raw conjunctive conflict."""
    if any(np.asarray(x).shape != np.asarray(y).shape for x, y in zip(a, b)):
        raise ValueError("two BPA sources must have matching array shapes")
    f1, n1, u1 = (np.asarray(v, dtype=np.float32) for v in a)
    f2, n2, u2 = (np.asarray(v, dtype=np.float32) for v in b)
    conflict = f1 * n2 + n1 * f2
    denominator = np.maximum(np.float32(1.0) - conflict, np.float32(1e-7))
    fault = (f1 * f2 + f1 * u2 + u1 * f2) / denominator
    not_fault = (n1 * n2 + n1 * u2 + u1 * n2) / denominator
    unassigned = (u1 * u2) / denominator
    if not np.allclose(fault + not_fault + unassigned, 1.0, rtol=0.0, atol=2e-6):
        raise ArithmeticError("two-source Dempster masses do not sum to one")
    return fault, not_fault, unassigned, np.clip(conflict, 0.0, 1.0)


@dataclass(frozen=True)
class ThreeSourceFusion:
    fault: np.ndarray
    not_fault: np.ndarray
    unassigned_dempster: np.ndarray
    conflict_ab: np.ndarray
    conflict_ab_vs_c: np.ndarray
    conflict_total: np.ndarray
    unassigned_yager: np.ndarray


def dempster_three(
    a: tuple[np.ndarray, np.ndarray, np.ndarray],
    b: tuple[np.ndarray, np.ndarray, np.ndarray],
    c: tuple[np.ndarray, np.ndarray, np.ndarray],
) -> ThreeSourceFusion:
    """Combine three BPAs by sequential normalized Dempster's rule.

    ``conflict_ab`` and ``conflict_ab_vs_c`` are raw conflicts at each stage;
    ``conflict_total`` is the cumulative conjunctive conflict. The returned
    ``unassigned_dempster`` excludes that conflict. ``unassigned_yager`` is the
    separate Yager-style diagnostic that transfers total conflict to Theta.
    """
    shapes = [np.asarray(m).shape for group in (a, b, c) for m in group]
    if any(len(shape) != 2 for shape in shapes) or len(set(shapes)) != 1:
        raise ValueError("all nine BPA mass arrays must share a 2-D shape")
    f1, n1, u1 = (np.asarray(v, dtype=np.float32) for v in a)
    f2, n2, u2 = (np.asarray(v, dtype=np.float32) for v in b)
    f3, n3, u3 = (np.asarray(v, dtype=np.float32) for v in c)
    for label, masses in (("a", (f1, n1, u1)), ("b", (f2, n2, u2)), ("c", (f3, n3, u3))):
        if any(not np.isfinite(m).all() or np.any(m < -1e-6) for m in masses):
            raise ValueError(f"BPA {label} contains nonfinite or negative mass")
        total = masses[0] + masses[1] + masses[2]
        if not np.allclose(total, 1.0, rtol=0.0, atol=2e-6):
            raise ValueError(f"BPA {label} masses do not sum to one")

    eps = np.float32(1e-7)
    conflict_ab = f1 * n2 + n1 * f2
    denom_ab = np.maximum(np.float32(1.0) - conflict_ab, eps)
    raw_ab_f = f1 * f2 + f1 * u2 + u1 * f2
    raw_ab_n = n1 * n2 + n1 * u2 + u1 * n2
    raw_ab_u = u1 * u2
    ab_f = raw_ab_f / denom_ab
    ab_n = raw_ab_n / denom_ab
    ab_u = raw_ab_u / denom_ab

    conflict_ab_vs_c = ab_f * n3 + ab_n * f3
    denom_c = np.maximum(np.float32(1.0) - conflict_ab_vs_c, eps)
    conflict_total = np.float32(1.0) - denom_ab * denom_c

    # Conjunctive (not yet normalized) masses of all three sources. These make
    # the cumulative Dempster denominator and Yager diagnostic auditable.
    raw_f = raw_ab_f * f3 + raw_ab_f * u3 + raw_ab_u * f3
    raw_n = raw_ab_n * n3 + raw_ab_n * u3 + raw_ab_u * n3
    raw_u = raw_ab_u * u3
    denom_total = np.maximum(np.float32(1.0) - conflict_total, eps)
    fault = raw_f / denom_total
    not_fault = raw_n / denom_total
    unassigned = raw_u / denom_total
    yager_unassigned = raw_u + conflict_total

    # Floating-point roundoff is tiny; fail on material violations and clip only
    # sub-ulp boundary noise before export.
    if any(np.any(m < -2e-5) or np.any(m > 1.00002) for m in (fault, not_fault, unassigned, conflict_total, yager_unassigned)):
        raise ArithmeticError("Dempster fusion produced out-of-range mass")
    np.clip(fault, 0.0, 1.0, out=fault)
    np.clip(not_fault, 0.0, 1.0, out=not_fault)
    np.clip(unassigned, 0.0, 1.0, out=unassigned)
    np.clip(conflict_total, 0.0, 1.0, out=conflict_total)
    np.clip(yager_unassigned, 0.0, 1.0, out=yager_unassigned)
    return ThreeSourceFusion(
        fault=fault,
        not_fault=not_fault,
        unassigned_dempster=unassigned,
        conflict_ab=np.clip(conflict_ab, 0.0, 1.0),
        conflict_ab_vs_c=np.clip(conflict_ab_vs_c, 0.0, 1.0),
        conflict_total=conflict_total,
        unassigned_yager=yager_unassigned,
    )
