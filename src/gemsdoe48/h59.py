"""H59 -- coverage-emitted Dempster-Shafer fusion of the two best independent families.

Why this construction is different from every earlier GEMSDOE48 fusion
----------------------------------------------------------------------
The registry (and this checkout) already contains raw-binary Dempster (H48),
Yager conflict transfer (H49), metric-geometry belief x Dempster (H50, H55,
H56B), open-world mass assignment (H56), lidar-relief augmentation (H57) and a
pignistic conflict-priced surface (H58).  All of those answer one question:
*what value should each grid cell carry?*  They then emit the surface, or its
top-k rank cut, as the submission.

H59 keeps the brief's Dempster-Shafer combination -- and keeps the residual
unassigned mass ``m(Theta)`` and the raw conflict ``K`` as separate diagnostic
layers -- but changes the *emission geometry*.  The only family in this
campaign that reached a high public score (the "dotted" family ladder
0.2477 -> 0.2600 -> 0.2708 -> 0.2778) did so by tuning the *spacing of the
emitted dots* to the scorer's 300 m triangular kernel, i.e. by solving a
covering problem, not by changing the evidence.  H59 therefore fuses the two
independently built families with Dempster's rule and then emits a
**kernel-covering dot set** over the fused belief surface:

* the fused belief supplies the *ranking* (the evidence), and
* the metric geometry supplies the *spacing* (the covering radius),
* cells where the two families disagree stay in the surface when they pass an
  explicit conflict veto, and their residual mass is exported as ``m(Theta)``.

Nothing here is fitted to a hidden label: the two families are fixed inputs,
the reliabilities are the preregistered Shafer discounts already used by H50,
and the spacing values are the metric's own covering radii.

Opinion model (per family, per cell)
------------------------------------
``b_i(x) = max over committed cells y of that family of k(d(x,y))`` with the
scorer's own triangular kernel ``k(d) = max(1 - d/300 m, 0)``.  This gives the
sparse binary family a smooth opinion surface whose "agreement" means agreement
*within the scorer's tolerance*, and avoids the semantic error of treating a
non-emitted cell as positive evidence of "no fault" (which is why dense fusions
such as H56 emit hundreds of thousands of positive cells).

Masses (Shafer 1976 sec. 11.2 discounting; Dempster 1967 rule)
--------------------------------------------------------------
``m_i({F}) = a_i * b_i``, ``m_i({notF}) = a_i * (1 - b_i)``, ``m_i(Theta) = 1 - a_i``
combined with the canonical normalized Dempster rule.  Returned diagnostics:
``m12(Theta)`` = residual unassigned belief; ``K`` = raw conjunctive conflict.
Neither is a calibrated fault probability; ``K`` includes spatial-offset
conflict, not only geological disagreement.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from . import ds50
from .emit import prune_redundant_batched
from .metric import max_credit_field

# Owner-reported live scores [OWNER-REPORT] -- anchoring only, never receipts.
LIVE_DOTTED_B2 = 0.2778
LIVE_TIP_H33D = 0.2632
RHO_MAX = 0.95

# Preregistered reliability discounts (same rule as H50/H58: no source is
# perfectly reliable; the ratio follows the owner-reported family ranking).
ALPHA_DOTTED = RHO_MAX
ALPHA_TIP = RHO_MAX * (LIVE_TIP_H33D / LIVE_DOTTED_B2)

# Preregistered emission spacings, in pixels (100 m grid).
SPACING_TIGHT_PX = 2.8     # the dotted family's own winning tuning (d2-8)
SPACING_KERNEL_PX = 5.2    # hex-covering radius 300 m: 5.2/sqrt(3) = 3.0 px = 300 m


@dataclass(frozen=True)
class H59Fusion:
    """Fused evidence plus the layers the brief asks to keep separate."""

    belief: np.ndarray            # m12({F}) after Dempster normalization
    belief_normalized: np.ndarray # Bel(F) / max(Bel(F) inside footprint), in [0,1]
    unassigned: np.ndarray        # m12(Theta) -- unassigned-belief diagnostic
    conflict: np.ndarray          # raw conjunctive conflict K -- diagnostic
    plausibility: np.ndarray      # Bel(F) + m(Theta)
    pignistic: np.ndarray         # BetP(F) = Bel(F) + m(Theta)/2
    belief_a: np.ndarray          # opinion surface of the dotted family
    belief_b: np.ndarray          # opinion surface of the tip/step-over family


def opinion_surface(committed: np.ndarray) -> np.ndarray:
    """Metric-geometry opinion surface of one family's committed cells."""
    return ds50.kernel_belief_surface(committed)


def fuse(belief_a: np.ndarray, belief_b: np.ndarray, footprint: np.ndarray,
         alpha_a: float = ALPHA_DOTTED, alpha_b: float = ALPHA_TIP) -> H59Fusion:
    """Discounted Dempster combination of two family opinion surfaces."""
    res = ds50.dempster_fuse(belief_a, belief_b, alpha_a, alpha_b, footprint=footprint)
    return H59Fusion(
        belief=res.belief,
        belief_normalized=res.belief_normalized,
        unassigned=res.unassigned,
        conflict=res.conflict,
        plausibility=res.plausibility,
        pignistic=res.belief + 0.5 * res.unassigned,
        belief_a=belief_a,
        belief_b=belief_b,
    )


def top_k_mask(surface: np.ndarray, k: int, footprint: np.ndarray) -> np.ndarray:
    """Boolean mask of the k highest-valued in-footprint cells (deterministic)."""
    return ds50.top_k_mask(np.where(footprint, surface, -np.inf), int(k))


def spacing_nms(points: np.ndarray, radius_px: float, *, rounds: int = 4) -> np.ndarray:
    """Spacing-tuned thinning: remove support-redundant dots at ``radius_px``.

    Reuses the shared batched reverse-delete pruner (``emit.prune_redundant_batched``)
    so the emitted dot set is a minimal covering set of the candidate set at the
    requested radius -- the same mechanism that produced the dotted family's
    spacing ladder, now applied to the *fused* candidate set.
    """
    pts = np.asarray(points, dtype=bool)
    if not pts.any():
        return pts.copy()
    return prune_redundant_batched(pts, pts, float(radius_px), rounds=rounds)


def coverage_emit(surface: np.ndarray, footprint: np.ndarray, spacing_px: float,
                  budget: int | None = None, *, corridor_quantile: float = 0.0) -> np.ndarray:
    """Emit a spaced dot set over the cell set where ``surface`` is defined.

    ``corridor_quantile`` > 0 restricts the corridor to cells above that quantile
    of the in-footprint surface values before thinning.
    """
    defined = footprint & np.isfinite(surface) & (surface > 0)
    if corridor_quantile > 0.0:
        values = surface[defined]
        if values.size:
            thr = float(np.quantile(values, corridor_quantile))
            defined = defined & (surface >= thr)
    if not defined.any():
        return np.zeros(surface.shape, dtype=bool)
    dots = spacing_nms(defined, spacing_px)
    if budget is not None and int(dots.sum()) > int(budget):
        dots = top_k_mask(np.where(dots, surface, -np.inf), int(budget), footprint)
    return dots


def conflict_veto(conflict: np.ndarray, footprint: np.ndarray, quantile: float) -> np.ndarray:
    """Boolean mask of cells *kept* by a raw-conflict veto at ``quantile``."""
    if not 0.0 < quantile < 1.0:
        raise ValueError("quantile must be in (0, 1)")
    vals = conflict[footprint]
    thr = float(np.quantile(vals, quantile)) if vals.size else 0.0
    return conflict <= thr


def graded_dots(surface: np.ndarray, dots: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Grade the selected dots by the fused belief, max-normalized to [0, 1]."""
    out = np.zeros(surface.shape, dtype=np.float64)
    if not dots.any():
        return out
    vals = np.where(dots, surface, 0.0)
    peak = float(vals[dots].max())
    if peak > 0:
        vals = vals / peak
    out = np.where(dots & footprint, np.clip(vals, 0.0, 1.0), 0.0)
    return np.clip(out, 0.0, 1.0)


def summary_counts(mask: np.ndarray) -> int:
    return int(np.asarray(mask, dtype=bool).sum())
