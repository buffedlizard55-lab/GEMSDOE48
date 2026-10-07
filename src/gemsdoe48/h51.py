"""H51 -- plausibility-budget emission: the decision layer of the H50 fusion.

Why H51 exists
--------------
The H50 analysis (``docs/research/h50-method-20261007.md``) showed that the
normalized Dempster *belief* surface Bel(F) is intersection-like: it is high
only where both parent surfaces agree, so a Bel-ranked fixed-budget emission sheds
parent-only supported cells and loses to both parents and to the plain
union on the blocked public proxies.  The official metric,

    DTI = TPw / (TPw + 0.2*FPw + 0.8*FNw),   k(d) = max(1 - d/300 m, 0),

is a budget metric for which binary {0, 1} emission on a fixed support is
optimal (credit and FP cost are both linear in the emitted value while the FN
term is independent of it, so the ratio is strictly increasing in every
emitted value).  Score gains can therefore only come from choosing a better
*set* of cells at a matched emitted mass.

H51 keeps the exact H50 evidential construction (kernel-credit belief
surfaces, two-sided simple support masses with the RHO_MAX-ceiled live-anchored
reliabilities, canonical normalized Dempster rule) but changes the decision
rule from "rank by Bel(F)" to "rank by Pl(F)":

    Pl(F) = Bel(F) + m(Theta) = 1 - m(notF)

Plausibility is the upper bound of the Dempster-Shafer belief interval
[Bel, Pl] (Shafer 1976, sec. 2.1).  Emitting the budget on the highest-
plausibility cells is the optimistic / interval-dominance decision rule:
commit exactly where the hypothesis "fault" has not been positively refuted by
the combined evidence.  Operationally, Pl(F) stays high wherever *either*
parent surface has support (restoring the union-like coverage that made the union
decision beat both parents on the proxies) while doubly supported cells still
outrank single-family cells (credit-density ordering).

What is new relative to everything in this repository
-----------------------------------------------------
*  H48 fused raw-sparse b2 x h33d at rho = 0.5 and emitted graded m(F).
*  H49 fused b2 x h33d with Yager conflict transfer and ranked by the
   *pignistic* probability BetP = Bel + m(Theta)/2 (interval midpoint) with a
   2.5-cell minimum separation and a 47,905-cell budget.
*  H50 fused b2 x h36-1 with canonical Dempster and emitted graded Bel(F).
*  H51 fuses b2 x h36-1 with canonical Dempster and emits *binary* on the
   top-B cells ranked by the *upper* interval bound Pl(F) = Bel + m(Theta),
   with B = 37,654 mass-matched to the dotted parent (the owner-reported
   0.2778 live artifact's cell count).  No prior GEMSDOE48 artifact ranked an
   emission by plausibility, and no sibling campaign page reviewed on
   2026-10-07 lists a plausibility-ranked emission.

Determinism
-----------
Selection sorts by (descending Pl, ascending row-major index) with a stable
lexsort, so ties break identically on every run and platform.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def plausibility_ranked_indices(plausibility: np.ndarray, where: np.ndarray | None = None) -> np.ndarray:
    """Row-major indices of all admissible cells ordered by descending Pl.

    Ties break toward the lower row-major index (stable, platform-independent).
    """
    pl = np.asarray(plausibility, dtype=np.float64)
    if pl.ndim != 2:
        raise ValueError("plausibility field must be 2-D")
    if not np.isfinite(pl).all():
        raise ValueError("plausibility field must be all-finite (use the footprint mask separately)")
    if where is not None:
        mask = np.asarray(where, dtype=bool)
        if mask.shape != pl.shape:
            raise ValueError("where mask must match plausibility shape")
        admissible = np.flatnonzero(mask.ravel())
        if admissible.size == 0:
            return admissible
        keys = -pl.ravel()[admissible]
        order = np.lexsort((admissible, keys))
        return admissible[order]
    flat = pl.ravel()
    order = np.lexsort((np.arange(flat.size), -flat))
    return order


def plausibility_emission(
    plausibility: np.ndarray,
    budget: int,
    where: np.ndarray | None = None,
) -> np.ndarray:
    """Binary {0.0, 1.0} emission on the ``budget`` highest-plausibility cells.

    Returns a float64 array of the same shape as ``plausibility``.  If fewer
    than ``budget`` cells are admissible, every admissible cell is emitted.
    """
    if int(budget) < 0:
        raise ValueError("budget must be non-negative")
    idx = plausibility_ranked_indices(plausibility, where)
    take = min(int(budget), idx.size)
    out = np.zeros(plausibility.shape, dtype=np.float64)
    if take:
        flat = out.ravel()
        flat[idx[:take]] = 1.0
    return out


@dataclass(frozen=True)
class H51Preregistration:
    """Every constant of the H51 construction, frozen before any holdout run."""

    budget: int
    dotted_reliability: float
    # Compatibility field names: ``tip_*`` refer to H36-1 rung30, not a
    # tip/step-over family. Frozen H51 receipts retain the legacy schema.
    tip_reliability: float
    dotted_sha256: str
    tip_sha256: str
    rule: str = (
        "binary 1 on the top-B cells ranked by combined plausibility "
        "Pl(F) = Bel(F) + m(Theta) of the canonical normalized Dempster "
        "combination of the two kernel-credit belief surfaces; 0 elsewhere"
    )


def jaccard(mask_a: np.ndarray, mask_b: np.ndarray) -> float:
    """Jaccard similarity of two boolean masks (0.0 when both are empty)."""
    a = np.asarray(mask_a, dtype=bool)
    b = np.asarray(mask_b, dtype=bool)
    inter = int(np.count_nonzero(a & b))
    union = int(np.count_nonzero(a | b))
    return inter / union if union else 0.0
