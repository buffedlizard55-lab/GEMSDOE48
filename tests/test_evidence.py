import numpy as np
import pytest

from gems48.evidence import (
    combine_dempster,
    combine_yager,
    discounted_binary_mass,
    kernel_support,
    minmax_unit,
    pignistic,
)
from gems48.metric import kernel_offsets


def test_yager_mass_conservation_and_conflict():
    a = discounted_binary_mass(np.array([[1.0, 0.0]]), 0.9)
    b = discounted_binary_mass(np.array([[0.0, 1.0]]), 0.8)
    f, n, u, k = combine_yager(a, b)
    assert np.allclose(f + n + u, 1)
    assert np.all(k > 0)
    assert np.all(u >= k)


def test_agreement_has_no_conflict():
    x = np.array([[0.0, 1.0]])
    *_, k = combine_yager(discounted_binary_mass(x, 0.9), discounted_binary_mass(x, 0.8))
    assert np.array_equal(k, np.zeros_like(k))


def test_yager_keeps_conflict_that_dempster_deletes():
    a = discounted_binary_mass(np.array([1.0]), 0.9)
    b = discounted_binary_mass(np.array([0.0]), 0.9)
    f_y, n_y, u_y, k = combine_yager(a, b)
    f_d, n_d, _ = combine_dempster(a, b)
    assert k[0] == pytest.approx(0.81)
    assert u_y[0] == pytest.approx(0.82)  # 0.01 theta + 0.81 conflict
    # Dempster normalisation redistributes the disagreement: with equal
    # reliabilities and flatly opposed opinions the two singleton masses come
    # out identical (0.09/0.19 each) and only m(Theta) keeps a residue, so the
    # conflict is no longer readable from the output at all.
    assert f_d[0] == pytest.approx(0.09 / 0.19, rel=1e-9)
    assert n_d[0] == pytest.approx(0.09 / 0.19, rel=1e-9)
    assert f_d[0] + n_d[0] + 0.01 / 0.19 == pytest.approx(1.0)
    # Yager leaves it visible as unassigned mass
    assert u_y[0] > 10 * abs(f_d[0] - 0.5)


def test_dempster_is_undefined_at_total_contradiction():
    a = discounted_binary_mass(np.array([1.0]), 1.0)
    b = discounted_binary_mass(np.array([0.0]), 1.0)
    f, n, k = combine_dempster(a, b)
    assert k[0] == pytest.approx(1.0)
    assert np.isnan(f[0]) and np.isnan(n[0])


def test_pignistic_splits_unassigned_mass():
    f, n, u, _ = combine_yager(discounted_binary_mass(np.array([1.0]), 0.9),
                               discounted_binary_mass(np.array([0.0]), 0.9))
    assert pignistic(f, n)[0] == pytest.approx(f[0] + u[0] / 2.0)
    assert pignistic(f, n)[0] == pytest.approx(0.5)  # total disagreement -> ignorance


def test_kernel_support_matches_kernel():
    dots = np.zeros((11, 11))
    dots[5, 5] = 1.0
    s = kernel_support(dots)
    assert s[5, 5] == pytest.approx(1.0)
    assert s[5, 6] == pytest.approx(2.0 / 3.0)
    assert s[5, 7] == pytest.approx(1.0 / 3.0)
    assert s[5, 8] == pytest.approx(0.0)
    assert s[3, 5] == pytest.approx(1.0 / 3.0)
    assert s.min() >= 0.0 and s.max() <= 1.0


def test_kernel_support_of_two_dots_takes_the_max():
    dots = np.zeros((11, 11))
    dots[5, 2] = 1.0
    dots[5, 6] = 1.0
    s = kernel_support(dots)
    assert s[5, 4] == pytest.approx(1.0 / 3.0)   # 2 cells from either dot
    assert s[5, 3] == pytest.approx(2.0 / 3.0)   # 1 cell from the first dot


def test_kernel_support_is_one_on_the_dot_set():
    rng = np.random.default_rng(5)
    dots = (rng.random((25, 25)) < 0.05).astype(np.float64)
    s = kernel_support(dots)
    assert np.allclose(s[dots > 0], 1.0)


def test_normalization_range():
    out = minmax_unit(np.array([[2.0, 4.0], [3.0, 99.0]]), np.array([[1, 1], [1, 0]], bool))
    assert out.min() == 0 and out.max() == 1 and out[1, 1] == 0


def test_rejects_invalid_confidence_and_reliability():
    with pytest.raises(ValueError):
        discounted_binary_mass(np.array([1.1]), 0.8)
    with pytest.raises(ValueError):
        discounted_binary_mass(np.array([0.5]), 1.1)


def test_combination_is_commutative():
    a = discounted_binary_mass(np.array([[0.2, 0.7]]), 0.9)
    b = discounted_binary_mass(np.array([[0.6, 0.1]]), 0.8)
    f1, n1, u1, k1 = combine_yager(a, b)
    f2, n2, u2, k2 = combine_yager(b, a)
    assert np.allclose(f1, f2) and np.allclose(n1, n2) and np.allclose(u1, u2) and np.allclose(k1, k2)


def test_belief_increases_with_source_support():
    low = discounted_binary_mass(np.array([0.1]), 0.9)
    high = discounted_binary_mass(np.array([0.9]), 0.9)
    other = discounted_binary_mass(np.array([0.5]), 0.8)
    assert combine_yager(high, other)[0] > combine_yager(low, other)[0]
