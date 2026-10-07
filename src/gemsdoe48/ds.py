"""Dempster-Shafer evidence combination for two detector-family surfaces.

This is a mathematical combination rule, not evidence that the source layers
are statistically independent or that the resulting map is better. The dotted
and tip/step-over parents share substantial positive-cell overlap (measured in
evidence/family_agreement.json); source independence is not established.
Dempster's normalized rule (Dempster 1967; Shafer 1976) divides out raw
conflict K. The resulting m(Theta) is residual uncommitted/ignorance mass under
the chosen basic probability assignments, not a direct disagreement map. K is
a separate pre-normalization diagnostic; abs(s1-s2) is another, non-mass
support-difference diagnostic.

Frame and mass functions
------------------------
Frame of discernment: `Theta = {F, notF}` -- "a fault is present at this pixel"
vs "it is not", one frame per pixel (the standard per-pixel construction in GIS
favorability mapping; Carranza 2008, *Geochemical Anomaly and Mineral
Prospectivity Mapping in GIS*, ch. 4; Tangestani & Moore 2001).

Each family i supplies a **belief surface** `b_i(x) in [0, 1]` built natively in
the metric's own geometry (see `families.kernel_credit_surface`): `b_i(x)` is the
credit the family's own committed pixels would earn if a truth pixel sat exactly
at x, i.e. `max over family pixels y of k(d(x, y))`. For this generic helper, a
per-source discount parameter `a_i in (0, 1]` yields a two-sided simple support
function. A caller must justify or calibrate `a_i`; the parameter is not
empirical reliability merely because it is named a discount.

    m_i({F})    = a_i * b_i(x)
    m_i({notF}) = a_i * (1 - b_i(x))
    m_i(Theta)  = 1 - a_i

The three masses sum to 1 for every x. `m(Theta)` is the source's uncommitted
mass induced by this assignment; it is not a measure of disagreement between
sources and does not by itself establish calibrated uncertainty.

Dempster's rule and the two diagnostic layers
---------------------------------------------
    K(x)      = m_1({F}) m_2({notF}) + m_1({notF}) m_2({F})
    m_12(A)   = [ sum over A1 cap A2 = A of m_1(A1) m_2(A2) ] / (1 - K(x))

`K` is the pre-normalization conflict. Dempster's normalized rule divides the
non-empty combined masses by `1-K`; it does not retain K as a mass in the
result. Consequently:

  1. `m_12(Theta) = m_1(Theta) m_2(Theta) / (1-K)` is residual uncommitted mass
     under the selected assignments. The worked values (0.16 at K=0 and 0.25
     at K=0.36 for a=0.6) demonstrate the formula, not a direct disagreement
     interpretation or a calibrated uncertainty interval.
  2. `K` is exported separately when needed as the pre-normalization conflict.
     It is not a probability of contradiction. A raw support comparison such
     as `abs(s1-s2)` is a different diagnostic and is not a D-S mass.

`Bel(F) = m_12({F})` and `Pl(F) = m_12({F}) + m_12(Theta)` are outputs
conditional on the chosen frame, assignments, discount values, and combination
rule; they are not automatically calibrated probabilities or coverage bounds.

Sensitivity / combination algebra
---------------------------------
`tests/test_ds.py` verifies mass-sum invariants, commutativity, associativity,
closed-form examples, the distinction from an arithmetic mean, input validation,
and that total conflict raises because the normalized rule is undefined there.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

NF = 0  # index of {F}
NN = 1  # index of {not F}
NT = 2  # index of Theta


@dataclass
class DSResult:
    m_F: np.ndarray
    m_notF: np.ndarray
    m_theta: np.ndarray
    conflict: np.ndarray
    bel_F: np.ndarray
    pl_F: np.ndarray

    def as_dict(self):
        return {
            "bel_F": self.bel_F,
            "pl_F": self.pl_F,
            "m_theta": self.m_theta,
            "conflict": self.conflict,
        }


def mass_function(belief_surface: np.ndarray, reliability: float) -> np.ndarray:
    """Return a validated (3, ...) simple-support mass function."""
    if not np.isfinite(reliability) or not (0.0 < reliability <= 1.0):
        raise ValueError("discount parameter must be finite and in (0, 1]")
    b = np.asarray(belief_surface, dtype=np.float64)
    if not np.isfinite(b).all():
        raise ValueError("belief surface must contain only finite values")
    if np.any((b < 0.0) | (b > 1.0)):
        raise ValueError("belief surface values must be in [0, 1]")
    m = np.empty((3,) + b.shape, dtype=np.float64)
    m[NF] = reliability * b
    m[NN] = reliability * (1.0 - b)
    m[NT] = 1.0 - reliability
    return m


def combine_two(m1: np.ndarray, m2: np.ndarray, *, eps: float = 1e-12) -> DSResult:
    """Apply Dempster's normalized rule; reject invalid masses and total conflict.

    `conflict` in the result is raw K before normalization. Dempster's rule
    divides it out, so it is not retained in m(Theta). A denominator at or
    below `eps` is rejected rather than replaced by an invented fallback.
    """
    m1 = np.asarray(m1, dtype=np.float64)
    m2 = np.asarray(m2, dtype=np.float64)
    if m1.ndim < 1 or m2.ndim < 1 or m1.shape[0] != 3 or m2.shape[0] != 3:
        raise ValueError("mass functions must have shape (3, ...)")
    if m1.shape != m2.shape:
        raise ValueError("mass functions must have identical shapes")
    if not np.isfinite(eps) or eps <= 0.0:
        raise ValueError("eps must be finite and positive")
    for masses in (m1, m2):
        if not np.isfinite(masses).all():
            raise ValueError("mass functions must be finite")
        if np.any((masses < 0.0) | (masses > 1.0)):
            raise ValueError("each mass must be in [0, 1]")
        if np.any(np.abs(masses.sum(axis=0) - 1.0) > 1e-10):
            raise ValueError("mass functions must sum to one at every cell")

    conflict = m1[NF] * m2[NN] + m1[NN] * m2[NF]
    norm = 1.0 - conflict
    if not np.isfinite(norm).all() or np.any(norm <= eps):
        raise ValueError("Dempster normalization is undefined at total/numerical conflict")

    m_F = (m1[NF] * m2[NF] + m1[NF] * m2[NT] + m1[NT] * m2[NF]) / norm
    m_notF = (m1[NN] * m2[NN] + m1[NN] * m2[NT] + m1[NT] * m2[NN]) / norm
    m_theta = (m1[NT] * m2[NT]) / norm
    if np.any(np.abs(m_F + m_notF + m_theta - 1.0) > 1e-10):
        raise ArithmeticError("combined mass function failed its unit-sum invariant")
    return DSResult(
        m_F=m_F,
        m_notF=m_notF,
        m_theta=m_theta,
        conflict=conflict,
        bel_F=m_F,
        pl_F=m_F + m_theta,
    )


def combine_pair(
    b1: np.ndarray,
    b2: np.ndarray,
    a1: float,
    a2: float,
) -> DSResult:
    """Convenience wrapper: build both mass functions and combine."""
    return combine_two(mass_function(b1, a1), mass_function(b2, a2))


def result_to_mass(r: DSResult) -> np.ndarray:
    """The combined mass function as a (3, H, W) array, so it can feed a third
    combination (Dempster's rule is associative on mass functions)."""
    return np.stack([r.m_F, r.m_notF, r.m_theta], axis=0)


def naive_mean(b1: np.ndarray, b2: np.ndarray) -> np.ndarray:
    """The averaging rule Dempster-Shafer is being contrasted with."""
    return 0.5 * (np.asarray(b1, dtype=np.float64) + np.asarray(b2, dtype=np.float64))


def weighted_mean(b1: np.ndarray, b2: np.ndarray, w: float) -> np.ndarray:
    return w * np.asarray(b1, dtype=np.float64) + (1.0 - w) * np.asarray(b2, dtype=np.float64)
