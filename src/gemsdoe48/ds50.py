"""H50 -- best-x-best Dempster-Shafer fusion with metric-geometry belief surfaces.

What is new relative to the earlier GEMSDOE48 fusion artifacts
---------------------------------------------------------------
The 2026-10-06 H48 candidate (``scripts/build_submission.py``) combined the
*raw sparse binary* dotted H33-2-B2 and tip H33-D surfaces with a fixed
symmetric discount rho = 0.5 and wrote the normalized m(F).  The H49 candidate
used a Yager conflict-transfer with a fixed budget.  Neither ever touched the
best-scoring tip/step-over surface, H36-1 rung-30 (owner-reported live 0.2710).

H50 differs on three axes:

1.  **Parents**: the best dotted-family surface (H33-2-B2, 37,654 px,
    owner-reported live 0.2778) crossed with the best tip/step-over-family
    surface (H36-1 rung-30, 37,660 px, owner-reported live 0.2710).  This pair
    has not been fused in this repository or any sibling campaign page reviewed
    on 2026-10-07.
2.  **Evidence construction**: each family's binary committed pixels are turned
    into a belief surface *in the metric's own geometry*::

        b_i(x) = max over committed pixels y of k(d(x, y)),   k(d) = max(1-d/300 m, 0)

    i.e. ``b_i(x)`` is the credit the family would earn if a truth pixel sat at
    ``x`` (``families.kernel_credit_surface``).  Belief therefore decays smoothly
    with distance from the committed dots instead of asserting hard counter-
    evidence ("not-fault") 100 m away from a dot, which is the semantic defect
    of fusing raw sparse emissions.
3.  **Reliability**: Shafer (1976, sec. 11.2) discounting with
    source-specific reliabilities anchored to the owner-reported live scores and
    capped below perfect reliability::

        a_dotted = RHO_MAX = 0.95,   a_tip = RHO_MAX * live_tip / live_dotted

    A first build used ``a_dotted = 1.0``; it was rejected because it forces the
    residual unassigned mass m12(Theta) to zero identically (``m12(Theta) =
    u1*u2/(1-K)`` with ``u1 = 0``), killing the brief's required disagreement
    diagnostic.  The RHO_MAX = 0.95 ceiling ("no source is perfectly reliable")
    is preregistered in the build receipt; the [OWNER-REPORT] live-score ratio
    supplies the ordering between sources.  The choice is a documented modeling
    assumption, not an estimated calibration, and a sensitivity sweep is stored
    in the same receipt.

Frame, masses and rule
----------------------
Per pixel, frame Theta = {F, notF}.  Two-sided simple support functions
(Dempster 1967; Shafer 1976; the standard evidential-belief construction in GIS
favourability mapping) with reliability ``a``::

    m({F}) = a * b,   m({notF}) = a * (1 - b),   m(Theta) = 1 - a

combined with the canonical normalized Dempster rule.  Carried forward
diagnostics:

* ``m12(Theta)`` -- residual unassigned belief; where the two strongest
  independent families neither agree enough to commit nor disagree enough to
  conflict.
* ``K`` -- raw conjunctive conflict before normalization; where the two
  families actively contradict each other (one commits to fault, the other to
  not-fault).  Canonical Dempster normalization redistributes K; the layer is
  reported separately so a geologist can see the disagreement itself.

The submission surface is ``Bel(F) = m12({F})`` divided by its in-footprint
maximum, i.e. normalized to [0, 1] as the brief requires.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from .metric import max_credit_field

# Owner-reported live scores [OWNER-REPORT] -- anchoring only, never receipts.
LIVE_DOTTED_B2 = 0.2778
LIVE_TIP_H36 = 0.2710

# Preregistered reliability ceiling: no source is treated as perfectly
# reliable.  Keeps m12(Theta) strictly positive so the unassigned-mass layer
# is an informative diagnostic instead of the zero field.
RHO_MAX = 0.95


@dataclass(frozen=True)
class H50Inputs:
    """Pinned inputs of the H50 build, all SHA-256 checked by the build script."""

    dotted_path: str
    dotted_sha256: str
    tip_path: str
    tip_sha256: str
    reliability_dotted: float = RHO_MAX
    reliability_tip: float = RHO_MAX * (LIVE_TIP_H36 / LIVE_DOTTED_B2)


def kernel_belief_surface(committed_pixels: np.ndarray) -> np.ndarray:
    """Belief surface b(x) = max_y k(d(x,y)) for a binary committed-pixel map."""
    mask = np.asarray(committed_pixels)
    if mask.ndim != 2:
        raise ValueError("committed pixel map must be 2-D")
    binary = np.where(np.isfinite(mask.astype(np.float64)), mask, 0.0)
    binary = (binary > 0.0).astype(np.float64)
    return max_credit_field(binary)


def discounted_mass(belief_surface: np.ndarray, reliability: float) -> np.ndarray:
    """Two-sided simple support mass function, shape (3, H, W): [F, notF, Theta]."""
    if not (0.0 < reliability <= 1.0):
        raise ValueError("reliability must be in (0, 1]")
    b = np.clip(np.asarray(belief_surface, dtype=np.float64), 0.0, 1.0)
    m = np.empty((3,) + b.shape, dtype=np.float64)
    m[0] = reliability * b
    m[1] = reliability * (1.0 - b)
    m[2] = 1.0 - reliability
    return m


@dataclass(frozen=True)
class H50Fusion:
    belief: np.ndarray          # m12({F}), normalized Dempster
    not_fault: np.ndarray       # m12({notF})
    unassigned: np.ndarray      # m12(Theta), post-normalization unassigned mass
    conflict: np.ndarray        # raw conjunctive conflict K (pre-normalization)
    plausibility: np.ndarray    # Bel + unassigned
    belief_normalized: np.ndarray  # belief / max(belief within footprint), in [0,1]


def dempster_fuse(
    belief_a: np.ndarray,
    belief_b: np.ndarray,
    reliability_a: float,
    reliability_b: float,
    footprint: np.ndarray | None = None,
) -> H50Fusion:
    """Normalized Dempster combination of two metric-geometry belief surfaces."""
    if np.asarray(belief_a).shape != np.asarray(belief_b).shape:
        raise ValueError("belief surfaces must share shape")
    m1 = discounted_mass(belief_a, reliability_a)
    m2 = discounted_mass(belief_b, reliability_b)

    conflict = m1[0] * m2[1] + m1[1] * m2[0]
    denom = 1.0 - conflict
    if np.any(denom <= 1e-12):
        raise ArithmeticError(
            "Dempster normalization undefined (total conflict); reliabilities must "
            "leave ignorance mass"
        )
    m_f = (m1[0] * m2[0] + m1[0] * m2[2] + m1[2] * m2[0]) / denom
    m_n = (m1[1] * m2[1] + m1[1] * m2[2] + m1[2] * m2[1]) / denom
    m_t = (m1[2] * m2[2]) / denom

    total = m_f + m_n + m_t
    if not np.allclose(total, 1.0, rtol=0.0, atol=1e-9):
        raise ArithmeticError("combined masses do not sum to one")
    if np.any((m_f < -1e-12) | (m_n < -1e-12) | (m_t < -1e-12)):
        raise ArithmeticError("negative combined mass")

    if footprint is None:
        ref_max = float(m_f.max())
    else:
        fp = np.asarray(footprint, dtype=bool)
        ref_max = float(m_f[fp].max())
    normalized = m_f / ref_max if ref_max > 0 else np.zeros_like(m_f)
    normalized = np.clip(normalized, 0.0, 1.0)

    return H50Fusion(
        belief=m_f,
        not_fault=m_n,
        unassigned=m_t,
        conflict=conflict,
        plausibility=m_f + m_t,
        belief_normalized=normalized,
    )


def naive_mean_belief(belief_a: np.ndarray, belief_b: np.ndarray) -> np.ndarray:
    """The averaging baseline the DS combination is contrasted against."""
    return 0.5 * (np.asarray(belief_a, np.float64) + np.asarray(belief_b, np.float64))


def spearman_rank_correlation(x: np.ndarray, y: np.ndarray) -> float:
    """Spearman rank correlation without a scipy dependency."""
    x = np.asarray(x, dtype=np.float64).ravel()
    y = np.asarray(y, dtype=np.float64).ravel()
    if x.size < 2:
        raise ValueError("need at least two values")

    def ranks(v: np.ndarray) -> np.ndarray:
        order = np.argsort(v, kind="mergesort")
        r = np.empty_like(order, dtype=np.float64)
        r[order] = np.arange(v.size, dtype=np.float64)
        return r

    rx, ry = ranks(x), ranks(y)
    sx, sy = float(rx.std()), float(ry.std())
    if sx == 0.0 or sy == 0.0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def top_k_mask(surface: np.ndarray, k: int, where: np.ndarray | None = None) -> np.ndarray:
    """Binary mask of the k highest-valued cells (optionally restricted)."""
    values = np.where(where, surface, -np.inf) if where is not None else surface
    if k <= 0:
        return np.zeros(surface.shape, dtype=bool)
    k = min(int(k), int(np.isfinite(values).sum()))
    idx = np.argpartition(-values.ravel(), k - 1)[:k]
    out = np.zeros(surface.size, dtype=bool)
    out[idx] = True
    return out.reshape(surface.shape)
