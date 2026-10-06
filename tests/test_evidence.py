import numpy as np
import pytest

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
