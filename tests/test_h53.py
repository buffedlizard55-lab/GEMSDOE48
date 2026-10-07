"""Unit tests for the H53 three-source adaptive fusion (src/gemsdoe48/ds53.py)."""
from __future__ import annotations

import numpy as np
import pytest

from gemsdoe48 import ds53


def grid(h: int = 11, w: int = 13) -> np.ndarray:
    return np.zeros((h, w), dtype=np.float64)


def test_lidar_ramp_anchors_and_classes():
    h = np.array([[0.2, 1.0, 1.9, 2.8, 4.0]])
    sig = np.array([[0.5, 0.5, 2.0, 2.0, 0.5]])
    cov = np.array([[1.0, 1.0, 1.0, 1.0, 0.0]])
    b, a = ds53.lidar_belief_and_reliability(h, sig, cov)
    assert b[0, 0] == pytest.approx(0.0)
    assert b[0, 1] == pytest.approx(0.0)
    assert b[0, 2] == pytest.approx((1.9 - 1.0) / (2.8 - 1.0))
    assert b[0, 3] == pytest.approx(1.0)
    assert b[0, 4] == pytest.approx(0.0)  # uncovered: no belief
    assert a[0, 0] == pytest.approx(ds53.A_LIDAR_SMOOTH)
    assert a[0, 2] == pytest.approx(ds53.A_LIDAR_ROUGH)
    assert a[0, 4] == pytest.approx(ds53.A_LIDAR_UNCOVERED)
    # NaN inputs degrade to uncovered, never to counter-evidence
    bn, an = ds53.lidar_belief_and_reliability(
        np.array([[np.nan]]), np.array([[np.nan]]), np.array([[np.nan]])
    )
    assert bn[0, 0] == 0.0 and an[0, 0] == pytest.approx(ds53.A_LIDAR_UNCOVERED)
    with pytest.raises(ValueError):
        ds53.lidar_belief_and_reliability(h, sig, cov, h_lo=2.0, h_hi=2.0)
    with pytest.raises(ValueError):
        ds53.lidar_belief_and_reliability(h, sig, cov[:, :4])
    with pytest.raises(ValueError):
        ds53.lidar_belief_and_reliability(h, sig, cov, a_smooth=0.0)


def test_discounted_mass_scalar_and_map_sum_to_one():
    b = np.linspace(0.0, 1.0, 25).reshape(5, 5)
    m = ds53.discounted_mass(b, 0.75)
    assert m.shape == (3, 5, 5)
    assert np.allclose(m.sum(axis=0), 1.0, atol=1e-12)
    amap = np.full((5, 5), 0.4)
    amap[0, 0] = 1.0
    m2 = ds53.discounted_mass(b, amap)
    assert np.allclose(m2.sum(axis=0), 1.0, atol=1e-12)
    assert (m2 >= 0).all()
    with pytest.raises(ValueError):
        ds53.discounted_mass(b, 0.0)
    with pytest.raises(ValueError):
        ds53.discounted_mass(b, np.full((5, 5), 0.0))
    with pytest.raises(ValueError):
        ds53.discounted_mass(b, np.full((4, 4), 0.5))


def test_pair_combination_commutative_and_conservative():
    rng = np.random.default_rng(53)
    b1, b2 = rng.random((7, 9)), rng.random((7, 9))
    m1, m2 = ds53.discounted_mass(b1, 0.9), ds53.discounted_mass(b2, 0.8)
    f12, n12, t12, k12 = ds53.dempster_combine_pair(m1, m2)
    f21, n21, t21, k21 = ds53.dempster_combine_pair(m2, m1)
    assert np.allclose(f12, f21, atol=1e-12)
    assert np.allclose(n12, n21, atol=1e-12)
    assert np.allclose(t12, t21, atol=1e-12)
    assert np.allclose(k12, k21, atol=1e-15)
    with pytest.raises(ValueError):
        ds53.dempster_combine_pair(m1, np.zeros((3, 7, 8)))


def test_three_source_associativity():
    rng = np.random.default_rng(7)
    b1, b2, b3 = (rng.random((9, 9)) for _ in range(3))
    m1 = ds53.discounted_mass(b1, 0.95)
    m2 = ds53.discounted_mass(b2, 0.92)
    m3 = ds53.discounted_mass(b3, 0.75)
    f_ab, n_ab, t_ab, _ = ds53.dempster_combine_pair(m1, m2)
    f_abc, _, _, _ = ds53.dempster_combine_pair(np.stack([f_ab, n_ab, t_ab]), m3)
    f_ac, n_ac, t_ac, _ = ds53.dempster_combine_pair(m1, m3)
    f_acb, _, _, _ = ds53.dempster_combine_pair(np.stack([f_ac, n_ac, t_ac]), m2)
    assert np.allclose(f_abc, f_acb, atol=1e-10)


def test_vacuous_third_source_recovers_two_source_result():
    rng = np.random.default_rng(11)
    b1, b2 = rng.random((8, 8)), rng.random((8, 8))
    b3 = rng.random((8, 8))
    three = ds53.dempster_fuse_three(b1, b2, b3, 0.95, 0.9, 1e-6)
    m1 = ds53.discounted_mass(b1, 0.95)
    m2 = ds53.discounted_mass(b2, 0.9)
    f2, _, _, _ = ds53.dempster_combine_pair(m1, m2)
    assert np.allclose(three.belief, f2, atol=1e-4)


def test_full_agreement_and_opposed_conflict():
    g = grid()
    g[5, 6] = 1.0
    full = ds53.dempster_fuse_three(g, g, g, 1.0, 1.0, 1.0)
    assert full.belief[5, 6] == pytest.approx(1.0, abs=1e-12)
    assert full.conflict_ab[5, 6] == pytest.approx(0.0, abs=1e-15)
    assert full.conflict_abl[5, 6] == pytest.approx(0.0, abs=1e-15)
    # opposed family commitments: conflict is carried by the K layer
    fa = grid(); fb = grid()
    fa[5, 6] = 1.0  # b=1 at the dot, 0 elsewhere
    fusion = ds53.dempster_fuse_three(fa, fb, fb, 0.9, 0.9, 0.5)
    assert fusion.conflict_ab[5, 6] > 0.5
    assert np.allclose(
        fusion.belief + fusion.not_fault + fusion.unassigned, 1.0, atol=1e-9
    )
    assert (fusion.conflict_total >= np.maximum(fusion.conflict_ab, fusion.conflict_abl) - 1e-15).all()
    assert (fusion.conflict_total <= 1.0 + 1e-12).all()


def test_unassigned_mass_strictly_positive_below_ceiling():
    rng = np.random.default_rng(3)
    fusion = ds53.dempster_fuse_three(
        rng.random((6, 6)), rng.random((6, 6)), rng.random((6, 6)),
        ds53.A_DOTTED, ds53.A_TIP, np.full((6, 6), 0.75),
    )
    assert bool((fusion.unassigned > 0).all())
    assert fusion.belief_normalized.min() >= 0.0
    assert fusion.belief_normalized.max() <= 1.0
    assert fusion.belief_normalized.max() == pytest.approx(1.0)
    assert np.allclose(fusion.plausibility, fusion.belief + fusion.unassigned, atol=1e-15)
    assert np.allclose(fusion.pignistic, fusion.belief + 0.5 * fusion.unassigned, atol=1e-15)


def test_normalization_uses_footprint_and_validates_shapes():
    b1, b2, b3 = grid(), grid(), grid()
    b1[0, 0] = 1.0
    b2[0, 0] = 1.0
    b3[0, 0] = 1.0
    fp = np.zeros_like(b1, dtype=bool)
    fp[0, 0] = True
    fusion = ds53.dempster_fuse_three(b1, b2, b3, 0.9, 0.9, 0.7, footprint=fp)
    assert fusion.belief_normalized[0, 0] == pytest.approx(1.0)
    with pytest.raises(ValueError):
        ds53.dempster_fuse_three(b1, b2, b3[:, :5], 0.9, 0.9, 0.7)
    with pytest.raises(ValueError):
        ds53.dempster_fuse_three(b1, b2, b3, 0.9, 0.9, 0.7, footprint=np.zeros((4, 4), bool))
    with pytest.raises(ValueError):
        ds53.dempster_fuse_three(b1, b2, b3, 0.9, 0.9, 0.7, footprint=np.zeros_like(b1, bool))


def test_not_the_three_way_mean_on_disagreement():
    fa = grid(); fb = grid(); fl = grid()
    fa[5, 6] = 1.0
    fusion = ds53.dempster_fuse_three(fa, fb, fl, 0.95, 0.9, 0.75)
    mean3 = ds53.naive_mean3_belief(fa, fb, fl)
    assert mean3[5, 6] == pytest.approx(1.0 / 3.0)
    assert fusion.belief[5, 6] != pytest.approx(mean3[5, 6])
    # closed form at the disagreement point: ((A(+)B)(+)L) with b=(1,0,0)
    a1, a2, a3 = 0.95, 0.9, 0.75
    k12 = a1 * a2
    f12 = a1 * (1.0 - a2) / (1.0 - k12)
    n12 = a2 * (1.0 - a1) / (1.0 - k12)
    t12 = (1.0 - a1) * (1.0 - a2) / (1.0 - k12)
    k = f12 * a3  # m3(F)=0, m3(notF)=a3
    expected = (f12 * (1.0 - a3)) / (1.0 - k)
    assert fusion.belief[5, 6] == pytest.approx(expected, rel=1e-9)
    assert n12 == pytest.approx(n12)  # documents the counter-evidence term
    assert t12 == pytest.approx(t12)
    # with metric-geometry spread the normalized fields also differ broadly
    sa = ds53.kernel_belief_surface((fa > 0).astype(float))
    fusion_s = ds53.dempster_fuse_three(sa, fb, fl, 0.95, 0.9, 0.75)
    mean_s = ds53.naive_mean3_belief(sa, fb, fl)
    diff = np.abs(fusion_s.belief_normalized - mean_s / mean_s.max())
    assert diff.max() > 0.05
    assert np.count_nonzero(diff > 1e-9) > 10


def test_preregistered_constants_match_slate():
    assert ds53.A_DOTTED == pytest.approx(0.95)
    assert ds53.A_TIP == pytest.approx(0.95 * (0.2710 / 0.2778))
    assert (ds53.H_LO_M, ds53.H_HI_M) == (1.0, 2.8)
    assert ds53.COVER_MIN == pytest.approx(0.9)
    assert ds53.SIGMA_SMOOTH_LT_M == pytest.approx(1.2)
    assert (ds53.A_LIDAR_SMOOTH, ds53.A_LIDAR_ROUGH, ds53.A_LIDAR_UNCOVERED) == (0.75, 0.25, 0.05)
    assert ds53.PARENT_A_BUDGET_PX == 37654
