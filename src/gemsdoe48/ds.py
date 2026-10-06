"""Dempster-Shafer evidence combination of two independent detector families.

Why Dempster-Shafer here
------------------------
The two detector families in this project were built independently
(spacing-tuned "dotted" emission; tip / step-over emission) and they agree on
69.6 % of their pixels and disagree on ~14,700 pixels (measured, see
evidence/family_agreement.json).  A weighted average of the two *surfaces* would
move mass into exactly those 14,700 pixels, i.e. it would turn the one piece of
information the two families carry -- **where they disagree** -- into a single
blended number.  Dempster-Shafer instead keeps the two bodies of evidence
separate and combines them through Dempster's rule of combination (Dempster,
1967; Shafer, *A Mathematical Theory of Evidence*, 1976, ch. 3), which
renormalises only the *conflicting* mass and leaves an explicit mass of
unassigned belief, `m(Theta)`, on the frame itself.

Frame and mass functions
------------------------
Frame of discernment: `Theta = {F, notF}` -- "a fault is present at this pixel"
vs "it is not", one frame per pixel (the standard per-pixel construction in GIS
favorability mapping; Carranza 2008, *Geochemical Anomaly and Mineral
Prospectivity Mapping in GIS*, ch. 4; Tangestani & Moore 2001).

Each family i supplies a **belief surface** `b_i(x) in [0, 1]` built natively in
the metric's own geometry (see `families.kernel_credit_surface`): `b_i(x)` is the
credit the family's own committed pixels would earn if a truth pixel sat exactly
at x, i.e. `max over family pixels y of k(d(x, y))`.  With a per-source
reliability (discount) `a_i in (0, 1]` the mass function is the classic
two-sided simple support function

    m_i({F})    = a_i * b_i(x)
    m_i({notF}) = a_i * (1 - b_i(x))
    m_i(Theta)  = 1 - a_i

which is well formed: the three masses sum to 1 for every x.  `a_i` is the
discounting operator of Shafer (1976) section 11.2: it encodes "source i is
reliable to degree a_i".

Dempster's rule and the two diagnostic layers
---------------------------------------------
    K(x)      = m_1({F}) m_2({notF}) + m_1({notF}) m_2({F})
    m_12(A)   = [ sum over A1 cap A2 = A of m_1(A1) m_2(A2) ] / (1 - K(x))

`K` is Shafer's **conflict**.  Two consequences matter and both are reported:

  1. `m_12(Theta) = m_1(Theta) m_2(Theta) / (1 - K)` is the residual
     **unassigned belief**.  It is 0.16 at zero conflict and rises to 0.25 at
     K = 0.36 with a = 0.6 (worked numbers in tests/test_ds.py): dropping the
     two families' opinion of F and of notF in equal measure.  It is therefore a
     genuine "the two approaches do not agree here" layer, and it is shipped as
     its own raster.
  2. `K` itself is the *unnormalised* disagreement.  Under Smets' Transferable
     Belief Model (Smets & Kennes 1994) Dempster's normalisation is dropped and
     `K` is kept explicitly as the mass on the empty set; Sentz & Ferson (2002,
     Sandia SAND2002-0835) show that the normalisation is exactly where Zadeh's
     (1984) paradox comes from.  We therefore ship BOTH layers: `m_12(Theta)`
     (post-normalisation unassigned belief) and `K` (pre-normalisation
     conflict), and we say in the documentation which is which.

`Bel(F) = m_12({F})` and `Pl(F) = m_12({F}) + m_12(Theta)`; the belief interval
`[Bel, Pl]` is the honest uncertainty of the combination.

Sensitivity / combination algebra
---------------------------------
`tests/test_ds.py` verifies: masses sum to 1; commutativity (`m_12 = m_21`);
associativity across three sources; `K = 0` and `a_i = 1` reduces exactly to
Bayesian normalisation of `b_1 b_2`; the `(b_1, b_2) = (1, 0)` worked example;
and monotonicity of `m_12(Theta)` in K.
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
    """Return the (3, H, W) mass function of a two-sided simple support function."""
    if not (0.0 < reliability <= 1.0):
        raise ValueError("reliability must be in (0, 1]")
    b = np.clip(np.asarray(belief_surface, dtype=np.float64), 0.0, 1.0)
    m = np.empty((3,) + b.shape, dtype=np.float64)
    m[NF] = reliability * b
    m[NN] = reliability * (1.0 - b)
    m[NT] = 1.0 - reliability
    return m


def combine_two(m1: np.ndarray, m2: np.ndarray, *, eps: float = 1e-12) -> DSResult:
    """Dempster's rule of combination for two mass functions on {F, notF, Theta}.

    Exact and vectorised.  Only the four intersections that yield a non-empty
    set are summed; the four that yield the empty set (m1({F})m2({notF}) and
    m1({notF})m2({F}), doubled) form the conflict K.
    """
    if m1.shape[0] != 3 or m2.shape[0] != 3:
        raise ValueError("mass functions must have shape (3, ...)")

    conflict = m1[NF] * m2[NN] + m1[NN] * m2[NF]
    norm = 1.0 - conflict
    if np.any(norm <= 0.0):
        # Dempster's rule is undefined for total conflict; fall back to the
        # vacuous mass on exactly those pixels and record it.
        norm = np.where(norm <= 0.0, eps, norm)

    m_F = (m1[NF] * m2[NF] + m1[NF] * m2[NT] + m1[NT] * m2[NF]) / norm
    m_notF = (m1[NN] * m2[NN] + m1[NN] * m2[NT] + m1[NT] * m2[NN]) / norm
    m_theta = (m1[NT] * m2[NT]) / norm
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
