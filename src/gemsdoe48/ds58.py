"""H58 -- dot-supported Dempster-Shafer fusion of the dotted B2 and tip/Euler H32-1 families.

Why a new variant (2026-10-08)
------------------------------
The H50 belief (``ds50.dempster_fuse``) evaluates the Dempster rule on
metric-kernel credit fields over the *whole* footprint.  Under the official
metric every unit of submitted mass that is not within 300 m of a truth pixel
costs ``alpha = 0.2`` in the denominator, so a 300 m halo around every dot adds
false-positive mass.  Local measurement (scratch receipt
``evidence/build_h58_receipt_20261008.json``) shows the smeared H50-style belief
totals ~288,000 mass against 43,000 for the committed dots and scores 0.0766
versus 0.0954 for the parents on the SGMC off-catalogue proxy.

H58 keeps the identical two-sided simple-support frame, the same
reliability discounts, and the canonical normalized Dempster rule, but it
**emits only on the union of committed dots**.  Kernel credit is still used as
the evidence for each source (agreement within the metric's own 300 m tolerance),
so the output is zero wherever neither parent commits a dot.

Frame, masses and rule (unchanged from H50)
-------------------------------------------
Per cell, frame Theta = {F, notF}; source i with discount a_i and credit b_i:

    m_i({F}) = a_i * b_i,   m_i({notF}) = a_i * (1 - b_i),   m_i(Theta) = 1 - a_i

combined with normalized Dempster:  K = m1(F)m2(notF) + m1(notF)m2(F),
m12(F) = [m1(F)m2(F) + m1(F)m2(Theta) + m1(Theta)m2(F)] / (1-K), and
m12(Theta) = m1(Theta)m2(Theta)/(1-K).

Outputs
-------
* ``belief``      -- m12(F) divided by its maximum on the support, in [0, 1],
                     zero outside the support (the submission surface).
* ``conflict``    -- raw K on the support (disagreement layer).
* ``m_theta``     -- residual unassigned mass m12(Theta) on the support.
* ``plausibility``-- m12(F) + m12(Theta) on the support.

Limits: the discounts are owner-score heuristics, not calibrated reliabilities;
for two binary parents the output is a monotone transform of the average within
the support (see the receipt's rank-correlation check), so the disagreement
information lives mainly in ``conflict`` and ``m_theta``.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .ds50 import LIVE_DOTTED_B2, RHO_MAX, discounted_mass
from .metric import max_credit_field

# Owner-reported public scores [OWNER-REPORT]; used only as ordering heuristics.
LIVE_TIP_H32_EULER = 0.2649


def reliabilities() -> tuple[float, float]:
    """Return (a_dotted, a_tip) = (RHO_MAX, RHO_MAX * live_tip / live_dotted)."""
    return RHO_MAX, RHO_MAX * (LIVE_TIP_H32_EULER / LIVE_DOTTED_B2)


@dataclass(frozen=True)
class DotSupportedFusion:
    support: np.ndarray        # bool: footprint cells where at least one parent commits a dot
    belief: np.ndarray         # float64 in [0,1], zero outside support
    m_fault: np.ndarray        # raw m12(F) (before dividing by its support maximum)
    conflict: np.ndarray       # raw K on support, zero outside
    m_theta: np.ndarray        # m12(Theta) on support, zero outside
    plausibility: np.ndarray   # m12(F) + m12(Theta) on support, zero outside
    max_m_fault: float         # the divisor used for normalization


def dempster_masks(b_a: np.ndarray, b_b: np.ndarray, ra: float, rb: float):
    """Return (mF, mNotF, mTheta, K) of the normalized Dempster rule for two credit fields."""
    m1 = discounted_mass(b_a, ra)
    m2 = discounted_mass(b_b, rb)
    conflict = m1[0] * m2[1] + m1[1] * m2[0]
    denom = 1.0 - conflict
    if np.any(denom <= 1e-12):
        raise ArithmeticError("Dempster normalization undefined (total conflict)")
    m_f = (m1[0] * m2[0] + m1[0] * m2[2] + m1[2] * m2[0]) / denom
    m_n = (m1[1] * m2[1] + m1[1] * m2[2] + m1[2] * m2[1]) / denom
    m_t = (m1[2] * m2[2]) / denom
    return m_f, m_n, m_t, conflict


def fuse_dots(
    dots_a: np.ndarray,
    dots_b: np.ndarray,
    footprint: np.ndarray,
    ra: float,
    rb: float,
) -> DotSupportedFusion:
    """Dot-supported Dempster fusion of two binary committed-dot maps."""
    fp = np.asarray(footprint, dtype=bool)
    a = np.asarray(dots_a, dtype=bool) & fp
    b = np.asarray(dots_b, dtype=bool) & fp
    if a.shape != fp.shape or b.shape != fp.shape:
        raise ValueError("dot maps and footprint must share shape")
    support = (a | b) & fp
    if not support.any():
        raise ValueError("empty support: neither parent commits a dot in the footprint")

    b_a = max_credit_field(a.astype(np.float64))
    b_b = max_credit_field(b.astype(np.float64))
    m_f, _m_n, m_t, conflict = dempster_masks(b_a, b_b, ra, rb)

    max_mf = float(m_f[support].max())
    if max_mf <= 0.0:
        raise ArithmeticError("no positive fault mass on the support")
    zero = np.zeros(fp.shape, dtype=np.float64)
    belief = zero.copy()
    belief[support] = np.clip(m_f[support] / max_mf, 0.0, 1.0)
    conflict_out = zero.copy()
    conflict_out[support] = conflict[support]
    m_theta_out = zero.copy()
    m_theta_out[support] = m_t[support]
    plaus = zero.copy()
    plaus[support] = (m_f + m_t)[support]
    return DotSupportedFusion(
        support=support,
        belief=belief,
        m_fault=np.where(support, m_f, 0.0),
        conflict=conflict_out,
        m_theta=m_theta_out,
        plausibility=plaus,
        max_m_fault=max_mf,
    )


def naive_kernel_mean(dots_a: np.ndarray, dots_b: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Repository naive-mean baseline on kernel credit fields, max-normalized in the footprint."""
    fp = np.asarray(footprint, dtype=bool)
    b_a = max_credit_field((np.asarray(dots_a, dtype=bool) & fp).astype(np.float64))
    b_b = max_credit_field((np.asarray(dots_b, dtype=bool) & fp).astype(np.float64))
    mean = 0.5 * (b_a + b_b)
    return mean / float(mean[fp].max())
