"""Unit tests for the H50 best-x-best Dempster-Shafer fusion (src/gemsdoe48/ds50.py)."""
from __future__ import annotations

import numpy as np
import pytest

from gemsdoe48 import ds50


def make_grid(h: int = 15, w: int = 15) -> np.ndarray:
    return np.zeros((h, w), dtype=np.float64)


def test_kernel_belief_single_dot_triangular_decay():
    grid = make_grid()
    grid[7, 7] = 1.0
    belief = ds50.kernel_belief_surface(grid)
    assert belief[7, 7] == pytest.approx(1.0)
    # 100 m neighbour: k = 1 - 100/300
    assert belief[7, 8] == pytest.approx(1.0 - 100.0 / 300.0, rel=1e-12)
    # diagonal 100*sqrt(2) m
    assert belief[6, 6] == pytest.approx(1.0 - (100.0 * np.sqrt(2.0)) / 300.0, rel=1e-12)
    # 300 m away: zero credit
    assert belief[7, 10] == pytest.approx(0.0, abs=1e-15)
    assert belief[4, 7] == pytest.approx(0.0, abs=1e-15)
    # exactly on the 300 m support edge at 3 px offset along an axis
    assert belief[7, 4] == pytest.approx(0.0, abs=1e-15)
    assert belief.min() >= 0.0 and belief.max() <= 1.0


def test_kernel_belief_handles_nan_outside_footprint():
    grid = make_grid()
    grid[0, 0] = np.nan
    grid[7, 7] = 1.0
    belief = ds50.kernel_belief_surface(grid)
    assert np.isfinite(belief).all()
    assert belief[7, 7] == pytest.approx(1.0)


def test_discounted_mass_sums_to_one():
    b = np.linspace(0.0, 1.0, 25).reshape(5, 5)
    for a in (0.25, 0.5, 0.9755, 1.0):
        m = ds50.discounted_mass(b, a)
        assert m.shape == (3, 5, 5)
        assert np.allclose(m.sum(axis=0), 1.0, atol=1e-12)
        assert (m >= 0).all()
    with pytest.raises(ValueError):
        ds50.discounted_mass(b, 0.0)
    with pytest.raises(ValueError):
        ds50.discounted_mass(b, 1.5)


def test_full_agreement_gives_full_belief_zero_conflict():
    a1, a2 = 1.0, ds50.LIVE_TIP_H36 / ds50.LIVE_DOTTED_B2
    b1 = make_grid(); b2 = make_grid()
    b1[7, 7] = 1.0
    b2[7, 7] = 1.0
    fusion = ds50.dempster_fuse(b1, b2, a1, a2)
    assert fusion.belief[7, 7] == pytest.approx(1.0, abs=1e-12)
    assert fusion.conflict[7, 7] == pytest.approx(0.0, abs=1e-15)
    assert fusion.unassigned[7, 7] == pytest.approx(0.0, abs=1e-15)


def test_commutativity():
    rng = np.random.default_rng(7)
    b1 = rng.uniform(0.0, 1.0, (9, 9))
    b2 = rng.uniform(0.0, 1.0, (9, 9))
    f12 = ds50.dempster_fuse(b1, b2, 0.9, 0.8)
    f21 = ds50.dempster_fuse(b2, b1, 0.8, 0.9)
    assert np.allclose(f12.belief, f21.belief, atol=1e-12)
    assert np.allclose(f12.conflict, f21.conflict, atol=1e-12)
    assert np.allclose(f12.unassigned, f21.unassigned, atol=1e-12)


def test_mass_conservation_everywhere():
    rng = np.random.default_rng(11)
    b1 = rng.uniform(0.0, 1.0, (11, 11))
    b2 = rng.uniform(0.0, 1.0, (11, 11))
    fusion = ds50.dempster_fuse(b1, b2, 1.0, 0.9755)
    total = fusion.belief + fusion.not_fault + fusion.unassigned
    assert np.allclose(total, 1.0, atol=1e-9)


def test_opposed_commitment_conflict_is_carried_by_K_layer():
    """One source commits fault, the other commits not-fault: the raw conflict
    K must expose the disagreement (canonical normalization redistributes it,
    which is Zadeh's paradox territory) -- why K ships as its own diagnostic."""
    a1 = ds50.RHO_MAX
    a2 = ds50.RHO_MAX * (ds50.LIVE_TIP_H36 / ds50.LIVE_DOTTED_B2)
    b1 = make_grid(); b2 = make_grid()
    b1[7, 7] = 1.0
    b2[7, 7] = 0.0
    fusion = ds50.dempster_fuse(b1, b2, a1, a2)
    # Analytic closed forms for the fully opposed case.
    k_expected = a1 * a2
    bel_expected = a1 * (1.0 - a2) / (1.0 - k_expected)
    unc_expected = (1.0 - a1) * (1.0 - a2) / (1.0 - k_expected)
    assert fusion.conflict[7, 7] == pytest.approx(k_expected, rel=1e-12)
    assert fusion.belief[7, 7] == pytest.approx(bel_expected, rel=1e-9)
    assert fusion.unassigned[7, 7] == pytest.approx(unc_expected, rel=1e-9)
    # Unassigned mass is strictly positive at the conflict point (the diagnostic
    # the brief requires) -- this fails for a perfect-reliability anchor.
    assert fusion.unassigned[7, 7] > 0.0
    # Where both surfaces are zero both commit to not-fault: no conflict.
    assert fusion.conflict[0, 0] == pytest.approx(0.0, abs=1e-15)
    assert fusion.belief[0, 0] == pytest.approx(0.0, abs=1e-15)


def test_normalized_belief_in_unit_interval_and_reaches_one():
    b1 = make_grid(); b2 = make_grid()
    b1[7, 7] = 1.0
    b2[7, 7] = 1.0
    b1[3, 3] = 1.0  # single-family support elsewhere
    footprint = np.ones_like(b1, dtype=bool)
    fusion = ds50.dempster_fuse(b1, b2, 1.0, 0.9755, footprint=footprint)
    assert fusion.belief_normalized.min() >= 0.0
    assert fusion.belief_normalized.max() == pytest.approx(1.0)


def test_not_the_naive_mean_on_disagreement():
    b1 = make_grid(); b2 = make_grid()
    b1[7, 7] = 1.0
    b2[7, 7] = 0.0
    a1 = ds50.RHO_MAX
    a2 = ds50.RHO_MAX * (ds50.LIVE_TIP_H36 / ds50.LIVE_DOTTED_B2)
    fusion = ds50.dempster_fuse(b1, b2, a1, a2)
    naive = ds50.naive_mean_belief(b1, b2)
    assert naive[7, 7] == pytest.approx(0.5)
    expected = a1 * (1.0 - a2) / (1.0 - a1 * a2)
    assert fusion.belief[7, 7] == pytest.approx(expected, rel=1e-9)
    assert fusion.belief[7, 7] != naive[7, 7]


def test_top_k_mask_count_and_restriction():
    surface = np.arange(100.0).reshape(10, 10)
    where = np.zeros((10, 10), dtype=bool)
    where[:5, :] = True
    mask = ds50.top_k_mask(surface, 12, where=where)
    assert int(mask.sum()) == 12
    assert (mask & ~where).sum() == 0
    # the 12 largest values in the top half are 38..49
    assert mask.sum() == 12 and surface[mask].min() == pytest.approx(38.0)


def test_spearman_known_cases():
    x = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
    assert ds50.spearman_rank_correlation(x, x) == pytest.approx(1.0, abs=1e-12)
    assert ds50.spearman_rank_correlation(x, -x) == pytest.approx(-1.0, abs=1e-12)
    assert ds50.spearman_rank_correlation(x, np.array([5.0, 6.0, 7.0, 8.0, 9.0])) == pytest.approx(1.0)


def test_reliability_anchor_matches_documented_ratio():
    assert ds50.LIVE_TIP_H36 / ds50.LIVE_DOTTED_B2 == pytest.approx(0.2710 / 0.2778, rel=1e-12)
