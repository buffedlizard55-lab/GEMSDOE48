"""Conflict-preserving evidence fusion for two fault-confidence rasters.

Frame of discernment
--------------------
Theta = {F, N} where F = "a fault lies within the metric's 300 m support of this
cell" and N = its negation.  Each source is reliability-discounted (Shafer's
discounting of a categorical/bayesian belief function)::

    m_s({F}) = r_s * s_s        m_s({N}) = r_s * (1 - s_s)      m_s(Theta) = 1 - r_s

where ``s_s`` is the source's graded support field and ``r_s`` in [0,1] is its
reliability.  The conjunctive product yields

    m({F})     = a_F b_F + a_F b_T + a_T b_F
    m({N})     = a_N b_N + a_N b_T + a_T b_N
    m(Theta)   = a_T b_T
    K          = a_F b_N + a_N b_F          (empty-set mass = conflict)

Classical normalised Dempster combination divides the non-empty masses by
``1 - K`` and therefore *deletes* the conflict: two sources that flatly
contradict each other still return a crisp answer.  Because this project
requires disagreement to stay visible, ``combine_yager`` uses Yager's modified
Dempster rule, which transfers K to m(Theta).  For a binary frame Yager's rule
and the Dubois-Prade disjunctive rule coincide.

Reference: Sentz & Ferson (2002), *Combination of Evidence in Dempster-Shafer
Theory*, SAND2002-0835, sections 2.2.1-2.2.3.
https://www.osti.gov/biblio/800792

Evidence fields
---------------
``kernel_support`` converts a *sparse dot emission* into the graded field
``s(x) = max_{y in dots} k(d(x, y))`` using exactly the competition's own
triangular kernel ``k(d) = max(1 - d/R, 0)`` with R = 3 cells (300 m).  s(x) is
therefore directly interpretable as "the credit this cell would realise if a
truth pixel sat on it", i.e. the natural currency of the published metric.  It
also lets two families that were emitted as sparse, non-coincident dots be
compared cell by cell without throwing away either family's geometry.
"""
from __future__ import annotations

import numpy as np

from .metric import RADIUS_CELLS, kernel_offsets


def discounted_binary_mass(confidence: np.ndarray, reliability: float):
    """Return (m_fault, m_not_fault, m_theta) for confidence in [0,1].

    This Bayesian-assignment conversion treats confidence zero as positive
    support for ``not-fault``. That is a substantive assumption, not a neutral
    default. It may be inappropriate for sparse detectors where zero means
    "not emitted" rather than "evidence of absence"; callers must document
    and validate that interpretation.
    """
    x = np.asarray(confidence, dtype=np.float64)
    if not np.isfinite(x).all() or np.any((x < 0) | (x > 1)):
        raise ValueError("confidence must be finite and in [0,1]")
    if not 0.0 <= reliability <= 1.0:
        raise ValueError("reliability must be in [0,1]")
    return reliability * x, reliability * (1.0 - x), np.full_like(x, 1.0 - reliability)


def conjunctive_components(a, b):
    """Return unnormalised conjunctive masses and empty-set conflict K."""
    af, an, au = a
    bf, bn, bu = b
    fault = af * bf + af * bu + au * bf
    not_fault = an * bn + an * bu + au * bn
    theta = au * bu
    conflict = af * bn + an * bf
    return fault, not_fault, theta, conflict


def combine_yager(a, b):
    """Conflict-preserving modified Dempster combination.

    Returns belief(F), disbelief(F), unassigned mass, and conflict.  Under
    Yager's rule, unassigned = conjunctive m(Theta) + K.
    """
    fault, not_fault, theta, conflict = conjunctive_components(a, b)
    unassigned = theta + conflict
    total = fault + not_fault + unassigned
    if not np.allclose(total, 1.0, atol=2e-7):
        raise ArithmeticError("combined basic probability assignments do not sum to one")
    return fault, not_fault, unassigned, conflict


def combine_dempster(a, b):
    """Classical normalised Dempster combination (conflict removed by 1-K).

    Kept so the report can *show* the difference between the two rules instead
    of asserting it.  Undefined (NaN) where K == 1 (total contradiction).
    """
    fault, not_fault, theta, conflict = conjunctive_components(a, b)
    with np.errstate(divide="ignore", invalid="ignore"):
        norm = np.where(conflict >= 1.0, np.nan, 1.0 / (1.0 - conflict))
    return fault * norm, not_fault * norm, conflict


def pignistic(fault: np.ndarray, not_fault: np.ndarray) -> np.ndarray:
    """Smets' pignistic (betting) probability: Bel(F) + m(Theta)/2."""
    return fault + (1.0 - fault - not_fault) / 2.0


def kernel_support(dots: np.ndarray, radius: float = RADIUS_CELLS) -> np.ndarray:
    """Graded support field s(x) = max_{y in dots} k(d(x, y)) in [0,1]."""
    d = np.asarray(dots, dtype=np.float64)
    offs, w = kernel_offsets(radius)
    out = np.zeros(d.shape, dtype=np.float64)
    for (dy, dx), kk in zip(offs, w):
        if kk <= 0:
            continue
        out = np.maximum(out, _shift(d, dy, dx) * kk)
    return np.clip(out, 0.0, 1.0)


def _shift(a: np.ndarray, dy: int, dx: int, fill: float = 0.0) -> np.ndarray:
    out = np.full(a.shape, fill, dtype=np.float64)
    ys_src = slice(max(0, dy), max(0, dy) + a.shape[0] - abs(dy)) if dy >= 0 else slice(0, a.shape[0] + dy)
    xs_src = slice(max(0, dx), max(0, dx) + a.shape[1] - abs(dx)) if dx >= 0 else slice(0, a.shape[1] + dx)
    ys_dst = slice(max(0, -dy), max(0, -dy) + a.shape[0] - abs(dy)) if dy <= 0 else slice(0, a.shape[0] - dy)
    xs_dst = slice(max(0, -dx), max(0, -dx) + a.shape[1] - abs(dx)) if dx <= 0 else slice(0, a.shape[1] - dx)
    out[ys_dst, xs_dst] = a[ys_src, xs_src]
    return out


def reliability_from_live_rate(credit_per_dot: float, reference: float, ceiling: float = 0.90) -> float:
    """Preregistered reliability rule: discount is proportional to measured
    live credit efficiency (weighted true positives per emitted dot).

    The parent with the higher measured credit-per-dot gets ``ceiling``; the
    other is scaled by the ratio of their efficiencies and clipped to [0, 1].
    """
    if reference <= 0:
        raise ValueError("reference credit rate must be positive")
    return float(np.clip(ceiling * credit_per_dot / reference, 0.0, 1.0))


def minmax_unit(values: np.ndarray, valid: np.ndarray | None = None) -> np.ndarray:
    """Min-max normalize to [0,1], keeping invalid cells at zero."""
    x = np.asarray(values, dtype=np.float64)
    m = np.ones(x.shape, bool) if valid is None else np.asarray(valid, bool)
    out = np.zeros(x.shape, dtype=np.float32)
    if not m.any():
        return out
    lo, hi = float(x[m].min()), float(x[m].max())
    if hi > lo:
        out[m] = ((x[m] - lo) / (hi - lo)).astype(np.float32)
    return out
