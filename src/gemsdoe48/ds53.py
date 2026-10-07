"""H53 -- three-source Dempster-Shafer fusion with terrain-adaptive reliability.

What is new relative to every prior GEMSDOE48 fusion artifact
--------------------------------------------------------------
All earlier fusions (H48 rho=0.5, Yager, DS48, H50, H51) combine exactly two
sources -- the dotted family and one tip/step-over surface -- with scalar
reliability discounts.  H53 adds a third, genuinely new-sensor source and a
per-pixel (context-dependent) discount map:

1.  **Sources**: (A) dotted H33-2-B2 kernel-credit belief, (B) tip H36-1
    rung-30 kernel-credit belief (the two best live parents, 0.2778 x 0.2710
    [OWNER-REPORT]), (L) native-lidar line-persistent scarp height
    ``h_gate12`` (3 m detector, sigma<1.2 m gate) ramped to a graded belief.
2.  **Reliability**: the two families keep scalar live-anchored discounts
    (H50 scheme, RHO_MAX = 0.95 ceiling); the lidar source uses a
    context-dependent discount map (contextual discounting, Mercier, Quost &
    Denoeux, ECSQARU 2005, https://link.springer.com/chapter/10.1007/11518655_47):
    0.75 in smooth covered
    terrain where the detector has measured 2.3-3.2x pilot lift, 0.25 in
    rough covered terrain where it is unproven, 0.05 where uncovered
    (near-vacuous: admits ignorance instead of asserting counter-evidence).
3.  **Rule**: canonical normalized Dempster (Dempster 1967; Shafer 1976),
    applied sequentially ``(A (+) B) (+) L``.  The rule is associative, so
    the order is documentation only (tested in ``tests/test_h53.py``).

Frame, masses and diagnostics
-----------------------------
Per pixel, frame Theta = {F, notF}.  Each source is a two-sided simple
support function with reliability ``a`` (scalar or per-pixel map)::

    m({F}) = a * b,   m({notF}) = a * (1 - b),   m(Theta) = 1 - a

Carried-forward diagnostics:

* ``m_ABC(Theta)`` -- residual unassigned belief after all three sources;
  where the families plus lidar neither agree enough to commit nor disagree
  enough to conflict.
* ``K_AB`` -- raw conjunctive conflict between the two families (the
  brief's "where the two strongest approaches actively disagree" layer).
* ``K_ABL`` -- raw conflict when the lidar source joins the family pair
  (where new-sensor evidence contradicts the family consensus).
* ``K_total = 1 - (1-K_AB)(1-K_ABL)`` -- conflict at either step.

The primary submission is ``Bel_ABC(F)`` divided by its in-footprint
maximum (graded, in [0,1]); the binary twin ranks pignistic
``BetP(F) = Bel(F) + m(Theta)/2`` at the parent-A-mass budget.

All H53-1 constants below are preregistered in
``docs/research/hypotheses-h53-20261007.md`` section 3 and frozen in
``evidence/hypothesis_slate_h53_20261007.json`` before any proxy scoring.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .ds50 import LIVE_DOTTED_B2, LIVE_TIP_H36, RHO_MAX, kernel_belief_surface

# --- preregistered H53-1 constants (do not tune after scoring) ----------------
A_DOTTED: float = RHO_MAX
A_TIP: float = RHO_MAX * (LIVE_TIP_H36 / LIVE_DOTTED_B2)
H_LO_M: float = 1.0   # ~q80 of covered h_gate12 (label-free anchor)
H_HI_M: float = 2.8   # q99 of covered h_gate12 (label-free anchor)
COVER_MIN: float = 0.9
SIGMA_SMOOTH_LT_M: float = 1.2
A_LIDAR_SMOOTH: float = 0.75
A_LIDAR_ROUGH: float = 0.25
A_LIDAR_UNCOVERED: float = 0.05
PARENT_A_BUDGET_PX: int = 37654

__all__ = [
    "A_DOTTED",
    "A_TIP",
    "H_LO_M",
    "H_HI_M",
    "COVER_MIN",
    "SIGMA_SMOOTH_LT_M",
    "A_LIDAR_SMOOTH",
    "A_LIDAR_ROUGH",
    "A_LIDAR_UNCOVERED",
    "PARENT_A_BUDGET_PX",
    "H53Fusion",
    "kernel_belief_surface",
    "lidar_belief_and_reliability",
    "discounted_mass",
    "dempster_combine_pair",
    "dempster_fuse_three",
    "naive_mean3_belief",
]


def lidar_belief_and_reliability(
    h_gate12_m: np.ndarray,
    sigma_mean_m: np.ndarray,
    cover: np.ndarray,
    *,
    h_lo: float = H_LO_M,
    h_hi: float = H_HI_M,
    cover_min: float = COVER_MIN,
    sigma_smooth_lt: float = SIGMA_SMOOTH_LT_M,
    a_smooth: float = A_LIDAR_SMOOTH,
    a_rough: float = A_LIDAR_ROUGH,
    a_uncovered: float = A_LIDAR_UNCOVERED,
) -> tuple[np.ndarray, np.ndarray]:
    """Map lidar layers to a graded belief surface and a reliability map.

    ``b_L = clip((h - h_lo) / (h_hi - h_lo))`` on covered cells, else 0.
    Reliability is  ``a_smooth`` / ``a_rough`` / ``a_uncovered`` by terrain
    class.  All inputs may contain NaN (treated as uncovered).
    """
    if not (h_hi > h_lo):
        raise ValueError("need h_hi > h_lo")
    for name, a in (("a_smooth", a_smooth), ("a_rough", a_rough), ("a_uncovered", a_uncovered)):
        if not (0.0 < float(a) <= 1.0):
            raise ValueError(f"{name} must be in (0, 1]")
    h = np.asarray(h_gate12_m, dtype=np.float64)
    sig = np.asarray(sigma_mean_m, dtype=np.float64)
    cov = np.asarray(cover, dtype=np.float64)
    if h.shape != sig.shape or h.shape != cov.shape:
        raise ValueError("lidar layers must share shape")
    covered = np.isfinite(cov) & (cov >= cover_min) & np.isfinite(h)
    smooth = covered & np.isfinite(sig) & (sig < sigma_smooth_lt)
    belief = np.zeros(h.shape, dtype=np.float64)
    belief[covered] = np.clip((h[covered] - h_lo) / (h_hi - h_lo), 0.0, 1.0)
    reliability = np.full(h.shape, float(a_uncovered), dtype=np.float64)
    reliability[covered & ~smooth] = float(a_rough)
    reliability[smooth] = float(a_smooth)
    return belief, reliability


def discounted_mass(
    belief_surface: np.ndarray, reliability: float | np.ndarray
) -> np.ndarray:
    """Two-sided simple support masses, shape (3, H, W): [F, notF, Theta].

    Reliability may be a scalar in (0, 1] or a per-pixel map in (0, 1].
    """
    b = np.clip(np.asarray(belief_surface, dtype=np.float64), 0.0, 1.0)
    a = np.asarray(reliability, dtype=np.float64)
    if a.ndim == 0:
        aval = float(a)
        if not (0.0 < aval <= 1.0):
            raise ValueError("scalar reliability must be in (0, 1]")
    else:
        if a.shape != b.shape:
            raise ValueError("reliability map shape must match belief surface")
        if not bool(np.isfinite(a).all()) or bool((a <= 0.0).any()) or bool((a > 1.0).any()):
            raise ValueError("reliability map must be finite and in (0, 1]")
    m = np.empty((3,) + b.shape, dtype=np.float64)
    m[0] = a * b
    m[1] = a * (1.0 - b)
    m[2] = 1.0 - a
    return m


@dataclass(frozen=True)
class H53Fusion:
    belief: np.ndarray            # m_ABC({F}), normalized Dempster
    not_fault: np.ndarray         # m_ABC({notF})
    unassigned: np.ndarray        # m_ABC(Theta)
    conflict_ab: np.ndarray       # raw K between the two families
    conflict_abl: np.ndarray      # raw K when lidar joins the family pair
    conflict_total: np.ndarray    # 1 - (1-K_AB)(1-K_ABL)
    plausibility: np.ndarray      # Bel + unassigned
    pignistic: np.ndarray         # Bel + unassigned/2
    belief_normalized: np.ndarray  # belief / max(belief within footprint)


def dempster_combine_pair(m1: np.ndarray, m2: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Canonical normalized Dempster combination of two mass triples.

    Inputs have shape (3, H, W) ordered [F, notF, Theta]; returns
    (mF, mN, mT, K) with K the raw pre-normalization conflict.
    """
    a1 = np.asarray(m1, dtype=np.float64)
    a2 = np.asarray(m2, dtype=np.float64)
    if a1.shape != a2.shape or a1.ndim != 3 or a1.shape[0] != 3:
        raise ValueError("mass triples must both have shape (3, H, W)")
    conflict = a1[0] * a2[1] + a1[1] * a2[0]
    denom = 1.0 - conflict
    if bool((denom <= 1e-12).any()):
        raise ArithmeticError(
            "Dempster normalization undefined (total conflict); reliabilities must leave ignorance mass"
        )
    m_f = (a1[0] * a2[0] + a1[0] * a2[2] + a1[2] * a2[0]) / denom
    m_n = (a1[1] * a2[1] + a1[1] * a2[2] + a1[2] * a2[1]) / denom
    m_t = (a1[2] * a2[2]) / denom
    total = m_f + m_n + m_t
    if not bool(np.allclose(total, 1.0, rtol=0.0, atol=1e-9)):
        raise ArithmeticError("combined masses do not sum to one")
    if bool((m_f < -1e-12).any()) or bool((m_n < -1e-12).any()) or bool((m_t < -1e-12).any()):
        raise ArithmeticError("negative combined mass")
    return m_f, m_n, m_t, conflict


def dempster_fuse_three(
    belief_a: np.ndarray,
    belief_b: np.ndarray,
    belief_l: np.ndarray,
    reliability_a: float,
    reliability_b: float,
    reliability_l: float | np.ndarray,
    footprint: np.ndarray | None = None,
) -> H53Fusion:
    """Normalized Dempster combination ``(A (+) B) (+) L`` of three beliefs."""
    shapes = {np.asarray(x).shape for x in (belief_a, belief_b, belief_l)}
    if len(shapes) != 1:
        raise ValueError("belief surfaces must share shape")
    m1 = discounted_mass(belief_a, reliability_a)
    m2 = discounted_mass(belief_b, reliability_b)
    m3 = discounted_mass(belief_l, reliability_l)
    ab_f, ab_n, ab_t, k_ab = dempster_combine_pair(m1, m2)
    m_ab = np.stack([ab_f, ab_n, ab_t])
    m_f, m_n, m_t, k_abl = dempster_combine_pair(m_ab, m3)
    k_total = 1.0 - (1.0 - k_ab) * (1.0 - k_abl)

    if footprint is None:
        ref_max = float(m_f.max())
    else:
        fp = np.asarray(footprint, dtype=bool)
        if fp.shape != m_f.shape:
            raise ValueError("footprint shape must match belief surfaces")
        if not bool(fp.any()):
            raise ValueError("footprint is empty")
        ref_max = float(m_f[fp].max())
    normalized = m_f / ref_max if ref_max > 0 else np.zeros_like(m_f)
    normalized = np.clip(normalized, 0.0, 1.0)
    return H53Fusion(
        belief=m_f,
        not_fault=m_n,
        unassigned=m_t,
        conflict_ab=k_ab,
        conflict_abl=k_abl,
        conflict_total=k_total,
        plausibility=m_f + m_t,
        pignistic=m_f + 0.5 * m_t,
        belief_normalized=normalized,
    )


def naive_mean3_belief(belief_a: np.ndarray, belief_b: np.ndarray, belief_l: np.ndarray) -> np.ndarray:
    """The three-way averaging baseline the DS combination is contrasted against."""
    return (
        np.asarray(belief_a, np.float64)
        + np.asarray(belief_b, np.float64)
        + np.asarray(belief_l, np.float64)
    ) / 3.0
