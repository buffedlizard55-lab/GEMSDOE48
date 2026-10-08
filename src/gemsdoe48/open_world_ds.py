"""Positive-only open-world Dempster--Shafer combination.

This module models sparse candidate rasters as *positive evidence only*. A zero
(or absent candidate) is not automatically evidence that a fault is absent:

    m_i(F)     = alpha_i * s_i
    m_i(N)     = 0
    m_i(Theta) = 1 - alpha_i * s_i

where ``s_i`` is a finite support surface in [0, 1]. Under normalized Dempster
combination there is no empty-set conflict because neither source assigns mass
to ``N``. For two sources the exact result is

    Bel(F) = f_1 + f_2 - f_1*f_2
    m(Theta) = u_1*u_2
    K = 0

Residual ``m(Theta)`` is unassigned/ignorance mass, not a direct disagreement
measure. Callers that need a direct disagreement diagnostic should also compare
the source-support surfaces (for example, ``abs(s_1 - s_2)``). This distinction
is especially important for sparse maps, where non-emission is not a measured
negative observation.

This assignment is a modelling choice, not calibrated probability, empirically
estimated source reliability, or proof of source independence. It is different
from ordinary symmetric Dempster assignments that allocate positive mass to
both ``F`` and ``N``.
"""
from __future__ import annotations

from typing import NamedTuple

import numpy as np


class PositiveOnlyCombination(NamedTuple):
    """Two-source D-S masses for a positive-only frame ``{F, N, Theta}``."""

    belief_fault: np.ndarray
    belief_not_fault: np.ndarray
    ignorance: np.ndarray
    conflict: np.ndarray


def positive_simple_support(
    support: np.ndarray, alpha: float = 0.6
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return ``(m(F), m(N), m(Theta))`` for one sparse positive-only source.

    ``support`` can be any shape but must be nonempty, finite, and in [0,1].
    ``alpha`` is a fixed discount in [0,1]; it is not automatically a calibrated
    empirical reliability. The no-fault mass is exactly zero by construction.
    """
    values = np.asarray(support, dtype=np.float32)
    discount = float(alpha)
    if values.size == 0:
        raise ValueError("support must be nonempty")
    if not np.isfinite(discount) or not (0.0 <= discount <= 1.0):
        raise ValueError("alpha must be finite and in [0, 1]")
    if not np.isfinite(values).all():
        raise ValueError("support must contain only finite values")
    if np.any((values < 0.0) | (values > 1.0)):
        raise ValueError("support values must be in [0, 1]")
    fault = np.multiply(values, np.float32(discount), dtype=np.float32)
    not_fault = np.zeros(values.shape, dtype=np.float32)
    ignorance = np.subtract(np.float32(1.0), fault, dtype=np.float32)
    return fault, not_fault, ignorance


def combine_positive_simple_supports(
    support1: np.ndarray,
    support2: np.ndarray,
    alpha1: float = 0.6,
    alpha2: float = 0.6,
) -> PositiveOnlyCombination:
    """Combine two positive-only simple-support sources with Dempster's rule.

    Inputs must have identical shapes. The result arrays are float32. The
    normalized denominator is exactly ``1 - K = 1`` because both not-fault
    masses are zero. Unit mass is checked after combination, with float32
    roundoff tolerance.
    """
    first = np.asarray(support1)
    second = np.asarray(support2)
    if first.shape != second.shape:
        raise ValueError("support arrays must have identical shapes")
    f1, n1, u1 = positive_simple_support(first, alpha1)
    f2, n2, u2 = positive_simple_support(second, alpha2)

    # Conjunctive conflict is f1*n2 + n1*f2 = 0. This is a model property,
    # not an assertion that the raw input surfaces agree spatially.
    conflict = np.zeros(f1.shape, dtype=np.float32)
    belief_fault = f1 + f2 - f1 * f2
    belief_not_fault = np.zeros(f1.shape, dtype=np.float32)
    ignorance = u1 * u2

    total = belief_fault + belief_not_fault + ignorance
    if not np.isfinite(total).all() or np.any(np.abs(total - 1.0) > 2e-6):
        raise ArithmeticError("positive-only Dempster masses failed the unit-sum invariant")
    if np.any((belief_fault < 0.0) | (belief_fault > 1.0)):
        raise ArithmeticError("combined fault belief escaped [0, 1]")
    if np.any((ignorance < 0.0) | (ignorance > 1.0)):
        raise ArithmeticError("combined ignorance escaped [0, 1]")
    return PositiveOnlyCombination(belief_fault, belief_not_fault, ignorance, conflict)


def normalize_relative_belief(
    belief_fault: np.ndarray, footprint: np.ndarray
) -> np.ndarray:
    """Max-normalize fault belief inside a nonempty footprint to float32 [0,1].

    This returns a relative favorability surface, **not** a calibrated
    probability or mass assignment. Values outside the supplied footprint are
    zero so the caller can write an all-finite range-safe GeoTIFF.
    """
    belief = np.asarray(belief_fault, dtype=np.float32)
    valid = np.asarray(footprint, dtype=bool)
    if belief.ndim != 2 or belief.shape != valid.shape:
        raise ValueError("belief and footprint must be matching 2-D arrays")
    if not valid.any():
        raise ValueError("footprint must contain at least one valid cell")
    if not np.isfinite(belief).all():
        raise ValueError("belief must be finite")
    if np.any((belief < 0.0) | (belief > 1.0)):
        raise ValueError("belief values must be in [0, 1]")
    maximum = float(belief[valid].max())
    if maximum <= 0.0:
        raise ValueError("belief has no positive support within the footprint")
    result = np.zeros(belief.shape, dtype=np.float32)
    result[valid] = belief[valid] / np.float32(maximum)
    np.clip(result, 0.0, 1.0, out=result)
    return result
