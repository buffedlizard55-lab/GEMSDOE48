import numpy as np
import pytest

from gemsdoe48.evidence import arithmetic_mean, combine_dempster


def test_dempster_agreement_and_disagreement_masses():
    result = combine_dempster(
        np.array([1.0, 0.0, 1.0], dtype=np.float32),
        np.array([1.0, 0.0, 0.0], dtype=np.float32),
        reliability=0.5,
    )
    np.testing.assert_allclose(result.fault, [0.75, 0.0, 1.0 / 3.0], atol=1e-7)
    np.testing.assert_allclose(result.not_fault, [0.0, 0.75, 1.0 / 3.0], atol=1e-7)
    np.testing.assert_allclose(result.ignorance, [0.25, 0.25, 1.0 / 3.0], atol=1e-7)
    np.testing.assert_allclose(result.conflict, [0.0, 0.0, 0.25], atol=1e-7)
    np.testing.assert_allclose(result.fault + result.not_fault + result.ignorance, 1.0, atol=1e-7)


def test_combination_is_symmetric_and_preserves_fractional_input():
    a = np.array([[0.2, 0.75], [0.0, 1.0]], dtype=np.float32)
    b = np.array([[0.8, 0.25], [0.4, 1.0]], dtype=np.float32)
    ab = combine_dempster(a, b, reliability=0.37)
    ba = combine_dempster(b, a, reliability=0.37)
    for field in ("fault", "not_fault", "ignorance", "conflict"):
        np.testing.assert_allclose(getattr(ab, field), getattr(ba, field), atol=2e-7)
    assert np.all(ab.fault >= 0) and np.all(ab.fault <= 1)
    assert np.all(ab.ignorance >= 0) and np.all(ab.ignorance <= 1)


def test_zero_reliability_is_total_ignorance():
    result = combine_dempster(np.array([0.0, 1.0]), np.array([1.0, 0.0]), reliability=0.0)
    np.testing.assert_array_equal(result.fault, [0.0, 0.0])
    np.testing.assert_array_equal(result.not_fault, [0.0, 0.0])
    np.testing.assert_array_equal(result.ignorance, [1.0, 1.0])
    np.testing.assert_array_equal(result.conflict, [0.0, 0.0])


def test_undiscounted_total_conflict_fails_closed():
    with pytest.raises(ValueError, match="total conflict"):
        combine_dempster(np.array([1.0]), np.array([0.0]), reliability=1.0)


@pytest.mark.parametrize(
    "a,b,reliability",
    [
        (np.array([np.nan]), np.array([0.0]), 0.5),
        (np.array([np.inf]), np.array([0.0]), 0.5),
        (np.array([-0.1]), np.array([0.0]), 0.5),
        (np.array([0.0]), np.array([1.1]), 0.5),
        (np.array([0.0]), np.array([0.0, 1.0]), 0.5),
        (np.array([0.0]), np.array([0.0]), -0.1),
        (np.array([0.0]), np.array([0.0]), 1.1),
    ],
)
def test_invalid_combination_inputs_raise(a, b, reliability):
    with pytest.raises(ValueError):
        combine_dempster(a, b, reliability=reliability)


def test_arithmetic_mean_baseline():
    np.testing.assert_array_equal(
        arithmetic_mean(np.array([0.0, 1.0]), np.array([1.0, 0.25])),
        np.array([0.5, 0.625], dtype=np.float32),
    )
