"""Discounted Dempster-Shafer combination for two grid-aligned evidence surfaces.

The inputs are treated as source opinions over the binary frame {fault, not_fault}.
A symmetric reliability discount leaves the remainder on the full frame Theta.  The
canonical Dempster normalization is then applied.  Raw conflict K is returned
separately because canonical normalization redistributes conflict; it does not keep
K as unassigned mass.

For sparse emissions, zero may mean "not emitted" rather than evidence of no fault.
That semantic limitation is a scientific caveat, not something this function can fix.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class DempsterResult:
    """Masses after discounted Dempster combination and raw conjunctive conflict."""

    fault: np.ndarray
    not_fault: np.ndarray
    ignorance: np.ndarray
    conflict: np.ndarray


def _as_evidence(values: np.ndarray, name: str) -> np.ndarray:
    arr = np.asarray(values, dtype=np.float32)
    if arr.ndim < 1:
        raise ValueError(f"{name} must have at least one dimension")
    if not np.isfinite(arr).all():
        raise ValueError(f"{name} contains NaN or infinite values")
    if np.any((arr < 0.0) | (arr > 1.0)):
        raise ValueError(f"{name} must be in [0, 1]")
    return arr


def combine_dempster(
    source_a: np.ndarray,
    source_b: np.ndarray,
    *,
    reliability: float = 0.5,
    denominator_epsilon: float = 1e-8,
) -> DempsterResult:
    """Combine two per-cell opinions with Shafer discounting and Dempster's rule.

    For each input ``p`` and reliability ``r``:

    ``m(F) = r*p``; ``m(not_F) = r*(1-p)``; ``m(Theta) = 1-r``.

    Let ``K = m1(F)m2(not_F) + m1(not_F)m2(F)`` be the unnormalized conflict.
    The conjunctive masses for F, not-F and Theta are normalized by ``1-K``.
    The raw ``K`` is returned as a diagnostic layer. The caller must not describe
    ``K`` itself as mass preserved by the normalized Dempster rule.

    A reliability below 1 is needed for deterministic opposing inputs (0 versus 1),
    otherwise ``K == 1`` and the normalized rule is undefined.  The default 0.5 is
    an explicit symmetric discount for uncalibrated source opinions, not an estimated
    accuracy or probability calibration.
    """
    a = _as_evidence(source_a, "source_a")
    b = _as_evidence(source_b, "source_b")
    if a.shape != b.shape:
        raise ValueError(f"source shape mismatch: {a.shape} != {b.shape}")
    r = float(reliability)
    if not np.isfinite(r) or not (0.0 <= r <= 1.0):
        raise ValueError("reliability must be finite and in [0, 1]")
    if not np.isfinite(denominator_epsilon) or denominator_epsilon <= 0:
        raise ValueError("denominator_epsilon must be a positive finite number")

    ignorance_source = np.float32(1.0 - r)
    a_fault = np.float32(r) * a
    a_not_fault = np.float32(r) * (1.0 - a)
    b_fault = np.float32(r) * b
    b_not_fault = np.float32(r) * (1.0 - b)

    conflict = a_fault * b_not_fault + a_not_fault * b_fault
    denominator = 1.0 - conflict
    if np.any(denominator <= denominator_epsilon):
        raise ValueError(
            "Dempster normalization is undefined (total conflict); use an explicit "
            "conflict-preserving rule or discount the sources"
        )

    # Unnormalized conjunctive combination over {F}, {not-F}, and Theta.
    fault = (
        a_fault * b_fault
        + a_fault * ignorance_source
        + ignorance_source * b_fault
    )
    not_fault = (
        a_not_fault * b_not_fault
        + a_not_fault * ignorance_source
        + ignorance_source * b_not_fault
    )
    ignorance = ignorance_source * ignorance_source

    fault = (fault / denominator).astype(np.float32, copy=False)
    not_fault = (not_fault / denominator).astype(np.float32, copy=False)
    ignorance = (ignorance / denominator).astype(np.float32, copy=False)
    conflict = conflict.astype(np.float32, copy=False)

    # Guard against implementation drift and floating point overflow before writing.
    total = fault + not_fault + ignorance
    if not np.isfinite(total).all():
        raise ArithmeticError("non-finite combined mass")
    if np.any(fault < -1e-6) or np.any(not_fault < -1e-6) or np.any(ignorance < -1e-6):
        raise ArithmeticError("negative combined mass")
    if np.any(fault > 1.0 + 1e-6) or np.any(not_fault > 1.0 + 1e-6) or np.any(ignorance > 1.0 + 1e-6):
        raise ArithmeticError("combined mass exceeds one")
    if not np.allclose(total, 1.0, rtol=0.0, atol=2e-6):
        raise ArithmeticError("combined masses do not sum to one")

    return DempsterResult(fault=fault, not_fault=not_fault, ignorance=ignorance, conflict=conflict)


def arithmetic_mean(source_a: np.ndarray, source_b: np.ndarray) -> np.ndarray:
    """Return a simple arithmetic mean baseline after validating inputs and shape."""
    a = _as_evidence(source_a, "source_a")
    b = _as_evidence(source_b, "source_b")
    if a.shape != b.shape:
        raise ValueError(f"source shape mismatch: {a.shape} != {b.shape}")
    return ((a + b) * np.float32(0.5)).astype(np.float32, copy=False)
