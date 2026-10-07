"""Dempster-Shafer combination of two fault-favorability surfaces.

References
----------
Dempster, A. P. (1967). "Upper and lower probabilities induced by a
multivalued mapping." Annals of Mathematical Statistics, 38(2), 325-339.
https://doi.org/10.1214/aoms/1177698950

Shafer, G. (1976). "A Mathematical Theory of Evidence." Princeton University
Press.

The method has precedent in GIS-based spatial-potential mapping (for example,
Mogaji, Lim & Abdullah, 2015, doi:10.1007/s12517-014-1391-1). That is related
methodological prior art, not evidence that this particular geothermal
fault-prediction surface is valid or better than weights-of-evidence.

Frame: Theta = {F, N}, where F means "fault present" and N means "fault absent".
For surface support s_i(x) in [0, 1] and discount parameter alpha_i in (0, 1]:

    m_i(F)     = alpha_i * s_i
    m_i(N)     = alpha_i * (1 - s_i)
    m_i(Theta) = 1 - alpha_i

Here `m(Theta)` is uncommitted / ignorance mass. It is not a direct measure of
source disagreement. Dempster's normalized rule computes the raw
pre-normalization conflict

    K = m1(F)m2(N) + m1(N)m2(F)

and divides each non-empty combined mass by 1-K. Therefore K is normalized
away; it is a separate diagnostic, not the resulting m(Theta). The combined
residual mass is m12(Theta) = m1(Theta)m2(Theta)/(1-K). A direct support
comparison such as abs(s1-s2) is a different diagnostic and is not a D-S mass.

Total conflict (K=1) makes Dempster's normalized rule undefined. This module
raises ValueError rather than silently substituting ignorance or clipping the
denominator. The alpha values in a particular application also require
justification: a mathematical discount parameter is not automatically a
calibrated empirical source reliability, and Dempster's rule's use does not
establish source independence.
"""
from __future__ import annotations

import numpy as np


def mass_from_surface(s: np.ndarray, alpha: float):
    """Return (m(F), m(N), m(Theta)) for a validated [0,1] surface."""
    if not np.isfinite(alpha) or not (0.0 < alpha <= 1.0):
        raise ValueError("alpha must be finite and in (0, 1]")
    values = np.asarray(s, dtype=np.float64)
    if not np.isfinite(values).all():
        raise ValueError("surface must contain only finite values")
    if np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("surface values must be in [0, 1]")
    f = alpha * values
    n = alpha * (1.0 - values)
    u = np.full_like(values, 1.0 - alpha)
    return f, n, u


def dempster_combine(s1: np.ndarray, s2: np.ndarray,
                     alpha1: float = 0.99, alpha2: float = 0.99) -> dict:
    """Combine two favorability surfaces pixelwise using Dempster's rule.

    Returns float64 arrays with the common input shape:
      bel       Bel(F), combined committed belief in fault
      pl        Pl(F) = Bel(F) + m(Theta)
      not_bel   Bel(N), committed belief in no-fault
      unc       m12(Theta), residual uncommitted/ignorance mass
      conflict  K, pre-normalization conflict (divided out by this rule)
      k_raw     compatibility alias for conflict

    Inputs must be finite, same-shape arrays in [0,1]. Total conflict or a
    denominator too close to zero raises ValueError.
    """
    s1 = np.asarray(s1)
    s2 = np.asarray(s2)
    if s1.shape != s2.shape:
        raise ValueError("surface arrays must have identical shapes")
    f1, n1, u1 = mass_from_surface(s1, alpha1)
    f2, n2, u2 = mass_from_surface(s2, alpha2)

    k_raw = f1 * n2 + n1 * f2
    denom = 1.0 - k_raw
    if not np.isfinite(denom).all() or np.any(denom <= 1e-15):
        raise ValueError("Dempster normalization is undefined at total/numerical conflict")

    m_f = (f1 * f2 + f1 * u2 + u1 * f2) / denom
    m_n = (n1 * n2 + n1 * u2 + u1 * n2) / denom
    m_u = (u1 * u2) / denom
    if np.any(np.abs(m_f + m_n + m_u - 1.0) > 1e-12):
        raise ArithmeticError("combined masses failed the unit-sum invariant")

    return {
        "bel": m_f,
        "pl": m_f + m_u,
        "not_bel": m_n,
        "unc": m_u,
        "conflict": k_raw,
        "k_raw": k_raw,
    }


def normalize_bel(bel: np.ndarray, footprint: np.ndarray | None = None) -> np.ndarray:
    """Scale finite nonnegative belief by its maximum; set outside to zero.

    This is relative normalization, not probability calibration. Callers that
    produce the official competition artifact should encode outside-footprint
    cells as NaN separately, as required by the task's file specification.
    """
    values = np.asarray(bel, dtype=np.float64)
    if not np.isfinite(values).all() or np.any(values < 0.0):
        raise ValueError("belief must be finite and nonnegative")
    if footprint is not None:
        footprint = np.asarray(footprint, dtype=bool)
        if footprint.shape != values.shape:
            raise ValueError("footprint shape must match belief shape")
        if not footprint.any():
            raise ValueError("footprint must contain at least one cell")
        ref = values[footprint]
    else:
        ref = values
    mx = float(ref.max())
    out = values / mx if mx > 0.0 else np.zeros_like(values)
    if footprint is not None:
        out = np.where(footprint, out, 0.0)
    return np.clip(out, 0.0, 1.0).astype(np.float32)
