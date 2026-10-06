"""Dempster-Shafer combination of two fault-favorability surfaces.

References
----------
Dempster, A. P. (1967). "A generalization of Bayesian inference."
Journal of the Royal Statistical Society, Series B, 30(2), 205-247.

Shafer, G. (1976). "A Mathematical Theory of Evidence."
Princeton University Press.

Dempster-Shafer theory is an established tool for GIS favorability mapping
and mineral/feature prospectivity as an alternative to weights-of-evidence;
see e.g. the discussion in Carranza, E. J. M. (2008), "Geochemical anomaly
modelling for mineral favourability mapping", and applications of
Dempster's rule of combination to evidential belief functions in spatial
analysis (e.g. Al-Hanbali & Ehlers, 2011, J. GIS).

Frame of discernment:  Theta = {F, N}  (fault present / fault absent).

Each source i provides a favorability surface s_i(x) in [0, 1].  We convert
it to a discounted simple mass function with discount (source reliability)
alpha_i in (0, 1]:

    m_i({F})     = alpha_i * s_i
    m_i({N})     = alpha_i * (1 - s_i)
    m_i({Theta}) = 1 - alpha_i          ("uncommitted" / ignorance mass)

Dempster's rule of combination (normalized orthogonal sum) for
m1 = (f1, n1, u1), m2 = (f2, n2, u2):

    K        = f1*n2 + n1*f2                       (conflict mass)
    m12(F)   = (f1*f2 + f1*u2 + u1*f2) / (1 - K)
    m12(N)   = (n1*n2 + n1*u2 + u1*n2) / (1 - K)
    m12(Theta) = (u1*u2) / (1 - K)                 (unassigned mass carried
                                                    forward after combination)

    Bel(F)  = m12(F)               (committed belief in fault)
    Pl(F)   = m12(F) + m12(Theta)  (plausibility: belief + unassigned)

The unassigned mass m12(Theta) is the diagnostic disagreement layer: it
remains explicitly represented wherever the sources do not force a
decision, instead of being averaged away.  Conflict K marks where the two
sources actively contradict one another (one says fault, the other says
no-fault with committed mass).
"""
from __future__ import annotations

import numpy as np


def mass_from_surface(s: np.ndarray, alpha: float):
    """Discounted Bayesian mass function from a [0,1] favorability surface."""
    s = np.clip(np.where(np.isfinite(s), s, 0.0), 0.0, 1.0).astype(np.float64)
    f = alpha * s
    n = alpha * (1.0 - s)
    u = np.full_like(s, 1.0 - alpha)
    return f, n, u


def dempster_combine(s1: np.ndarray, s2: np.ndarray,
                     alpha1: float = 0.99, alpha2: float = 0.99) -> dict:
    """Combine two favorability surfaces with Dempster's rule, pixelwise.

    Returns dict with arrays (float64, same shape as inputs):
      bel      Bel(F), combined committed belief in fault
      pl       Pl(F) = Bel + unassigned
      not_bel  Bel(N), committed belief in no-fault
      unc      m12(Theta), unassigned / ignorance mass after combination
      conflict K, the normalized-away conflict (active disagreement)
      k_raw    unnormalized conflict numerator (for diagnostics)
    All outputs are in [0, 1].
    """
    f1, n1, u1 = mass_from_surface(s1, alpha1)
    f2, n2, u2 = mass_from_surface(s2, alpha2)

    k_raw = f1 * n2 + n1 * f2
    denom = 1.0 - k_raw
    # denom > 0 strictly when alpha1, alpha2 < 1; guard numerically anyway
    denom_safe = np.where(denom <= 1e-15, 1e-15, denom)

    m_f = (f1 * f2 + f1 * u2 + u1 * f2) / denom_safe
    m_n = (n1 * n2 + n1 * u2 + u1 * n2) / denom_safe
    m_u = (u1 * u2) / denom_safe
    # Where denom was ~0 (pathological full conflict, only if alpha==1 and
    # s1 != s2 exactly), Dempster's rule is undefined; assign pure ignorance.
    bad = denom <= 1e-15
    m_f = np.where(bad, 0.0, m_f)
    m_n = np.where(bad, 0.0, m_n)
    m_u = np.where(bad, 1.0, m_u)

    return {
        "bel": m_f,
        "pl": m_f + m_u,
        "not_bel": m_n,
        "unc": m_u,
        "conflict": k_raw,
    }


def normalize_bel(bel: np.ndarray, footprint: np.ndarray | None = None) -> np.ndarray:
    """Normalize combined belief to [0, 1] by dividing by its maximum
    (equivalent to min-max here because Bel >= 0 with 0 attained at
    no-evidence cells).  Outside the footprint the result is forced to 0."""
    bel = np.where(np.isfinite(bel), bel, 0.0)
    ref = bel[footprint] if footprint is not None else bel
    mx = float(ref.max())
    out = bel / mx if mx > 0 else np.zeros_like(bel)
    if footprint is not None:
        out = np.where(footprint, out, 0.0)
    return np.clip(out, 0.0, 1.0).astype(np.float32)
