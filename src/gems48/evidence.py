"""Conflict-preserving evidence fusion for two fault-confidence rasters.

The frame is Θ={fault, no-fault}. Each source is reliability-discounted into
m({F}), m({N}), and m(Θ). The conjunctive product's empty-set mass K measures
source conflict. Classical normalized Dempster combination divides non-empty
masses by 1-K and therefore does *not* retain K. Because this project explicitly
requires disagreement to remain visible, ``combine_yager`` uses Yager's modified
Dempster rule and transfers K to m(Θ).

Reference: Sentz & Ferson (2002), SAND2002-0835, sections 2.2.1–2.2.3.
https://www.stat.berkeley.edu/~aldous/Real_World/dempster_shafer.pdf
"""
from __future__ import annotations

import numpy as np


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

    Returns belief(F), disbelief(F), unassigned mass, and conflict. Under
    Yager's rule, unassigned = conjunctive m(Θ) + K.
    """
    fault, not_fault, theta, conflict = conjunctive_components(a, b)
    unassigned = theta + conflict
    total = fault + not_fault + unassigned
    if not np.allclose(total, 1.0, atol=2e-7):
        raise ArithmeticError("combined basic probability assignments do not sum to one")
    return fault, not_fault, unassigned, conflict


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
