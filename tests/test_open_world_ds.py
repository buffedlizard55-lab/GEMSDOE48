import numpy as np
import pytest

from gemsdoe48.open_world_ds import (
    combine_positive_simple_supports,
    normalize_relative_belief,
    positive_simple_support,
)


def test_positive_simple_support_treats_non_emission_as_ignorance():
    support = np.array([0.0, 0.5, 1.0], dtype=np.float32)
    fault, not_fault, ignorance = positive_simple_support(support, alpha=0.6)
    np.testing.assert_allclose(fault, [0.0, 0.3, 0.6], atol=1e-7)
    np.testing.assert_array_equal(not_fault, np.zeros(3, dtype=np.float32))
    np.testing.assert_allclose(ignorance, [1.0, 0.7, 0.4], atol=1e-7)
    np.testing.assert_allclose(fault + not_fault + ignorance, 1.0, atol=1e-7)


def test_positive_only_dempster_combination_obeys_mass_identities():
    support1 = np.array([[1.0, 1.0, 0.0, 0.2]], dtype=np.float32)
    support2 = np.array([[1.0, 0.0, 0.0, 0.8]], dtype=np.float32)
    result = combine_positive_simple_supports(support1, support2, 0.6, 0.6)

    # Both sources support F: 1 - (1 - .6)^2 = .84; residual ignorance .16.
    assert result.belief_fault[0, 0] == pytest.approx(0.84, abs=1e-6)
    assert result.ignorance[0, 0] == pytest.approx(0.16, abs=1e-6)
    # One source supports F: .6; the other contributes only ignorance.
    assert result.belief_fault[0, 1] == pytest.approx(0.6, abs=1e-6)
    assert result.ignorance[0, 1] == pytest.approx(0.4, abs=1e-6)
    # Neither source supports F: all mass remains unassigned.
    assert result.belief_fault[0, 2] == pytest.approx(0.0, abs=1e-7)
    assert result.ignorance[0, 2] == pytest.approx(1.0, abs=1e-7)
    # Fractional independent supports are preserved by the exact rule.
    f1 = np.float32(0.6 * 0.2)
    f2 = np.float32(0.6 * 0.8)
    assert result.belief_fault[0, 3] == pytest.approx(f1 + f2 - f1 * f2, abs=1e-7)
    np.testing.assert_array_equal(result.belief_not_fault, np.zeros_like(support1))
    np.testing.assert_array_equal(result.conflict, np.zeros_like(support1))
    np.testing.assert_allclose(
        result.belief_fault + result.belief_not_fault + result.ignorance,
        1.0,
        atol=2e-6,
    )


def test_combination_is_symmetric_and_validates_inputs():
    a = np.array([[0.1, 0.4], [0.8, 1.0]], dtype=np.float32)
    b = np.array([[0.9, 0.6], [0.2, 0.0]], dtype=np.float32)
    ab = combine_positive_simple_supports(a, b, 0.7, 0.4)
    ba = combine_positive_simple_supports(b, a, 0.4, 0.7)
    for field in ("belief_fault", "belief_not_fault", "ignorance", "conflict"):
        np.testing.assert_allclose(getattr(ab, field), getattr(ba, field), atol=2e-7)

    with pytest.raises(ValueError, match="identical shapes"):
        combine_positive_simple_supports(np.zeros((2,)), np.zeros((3,)))
    with pytest.raises(ValueError, match="finite"):
        positive_simple_support(np.array([np.nan]))
    with pytest.raises(ValueError, match="finite"):
        positive_simple_support(np.array([np.inf]))
    with pytest.raises(ValueError, match="support values"):
        positive_simple_support(np.array([-0.1]))
    with pytest.raises(ValueError, match="support values"):
        positive_simple_support(np.array([1.1]))
    for alpha in (-0.1, 1.1, np.nan, np.inf):
        with pytest.raises(ValueError, match="alpha"):
            positive_simple_support(np.array([0.5]), alpha)


def test_relative_normalization_masks_outside_and_rejects_empty_or_zero():
    belief = np.array([[0.2, 0.4], [0.9, 0.1]], dtype=np.float32)
    footprint = np.array([[True, True], [False, True]])
    out = normalize_relative_belief(belief, footprint)
    np.testing.assert_allclose(out, [[0.5, 1.0], [0.0, 0.25]])
    assert out.dtype == np.float32
    assert np.isfinite(out).all()
    assert np.all((out >= 0.0) & (out <= 1.0))

    with pytest.raises(ValueError, match="at least one"):
        normalize_relative_belief(belief, np.zeros_like(footprint))
    with pytest.raises(ValueError, match="positive support"):
        normalize_relative_belief(np.zeros_like(belief), footprint)
    with pytest.raises(ValueError, match="matching 2-D"):
        normalize_relative_belief(np.zeros((2, 2, 1)), np.ones((2, 2), dtype=bool))
