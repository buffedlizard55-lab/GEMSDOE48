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

from gems48.evidence import combine_yager, discounted_binary_mass, minmax_unit

def test_yager_preserves_conflict_as_unassigned_mass():
    dotted = discounted_binary_mass(np.array([[1.0, 0.0]]), 0.9)
    tip = discounted_binary_mass(np.array([[0.0, 1.0]]), 0.85)
    belief, disbelief, unassigned, conflict = combine_yager(dotted, tip)
    assert np.allclose(belief, [[0.135, 0.085]])
    assert np.allclose(disbelief, [[0.085, 0.135]])
    assert np.allclose(conflict, [[0.765, 0.765]])
    assert np.allclose(unassigned, [[0.78, 0.78]])
    assert np.allclose(belief + disbelief + unassigned, 1.0)


def test_agreement_has_no_conflict():
    confidence = np.array([[0.0, 1.0]])
    *_, conflict = combine_yager(
        discounted_binary_mass(confidence, 0.9),
        discounted_binary_mass(confidence, 0.8),
    )
    assert np.array_equal(conflict, np.zeros_like(conflict))


def test_normalization_respects_valid_footprint():
    values = np.array([[2.0, 4.0], [3.0, 99.0]])
    valid = np.array([[True, True], [True, False]])
    normalized = minmax_unit(values, valid)
    assert normalized.min() == 0.0
    assert normalized.max() == 1.0
    assert normalized[1, 1] == 0.0


def test_rejects_invalid_confidence_and_reliability():
    with pytest.raises(ValueError, match="confidence"):
        discounted_binary_mass(np.array([1.1]), 0.8)
    with pytest.raises(ValueError, match="reliability"):
        discounted_binary_mass(np.array([0.5]), 1.1)
