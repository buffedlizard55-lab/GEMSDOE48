import numpy as np
import pytest

from gemsdoe48.h56 import (
    combine_open_world_dempster,
    deterministic_top_k,
    hessian_line_response,
    normalize_belief,
    robust_unit_scale,
    sparse_open_world_bpa,
)


def test_sparse_open_world_mass_assignment_keeps_most_absence_on_theta():
    support = np.array([0.0, 1.0], dtype=np.float64)
    fault, not_fault, ignorance = sparse_open_world_bpa(
        support, reliability=0.6, absence_informativeness=0.1
    )
    np.testing.assert_allclose(fault, [0.0, 0.6])
    np.testing.assert_allclose(not_fault, [0.06, 0.0])
    np.testing.assert_allclose(ignorance, [0.94, 0.4])
    np.testing.assert_allclose(fault + not_fault + ignorance, 1.0)


def test_zero_absence_informativeness_means_omission_is_ignorance():
    fault, not_fault, ignorance = sparse_open_world_bpa(
        np.array([0.0, 1.0]), reliability=0.6, absence_informativeness=0.0
    )
    np.testing.assert_array_equal(fault, [0.0, 0.6])
    np.testing.assert_array_equal(not_fault, [0.0, 0.0])
    np.testing.assert_allclose(ignorance, [1.0, 0.4])


def test_open_world_dempster_combination_normalizes_and_exposes_conflict():
    a = sparse_open_world_bpa(np.array([1.0, 1.0, 0.0]), reliability=0.6, absence_informativeness=0.1)
    b = sparse_open_world_bpa(np.array([1.0, 0.0, 0.0]), reliability=0.6, absence_informativeness=0.1)
    ab = combine_open_world_dempster(a, b)
    ba = combine_open_world_dempster(b, a)

    for field in ("fault", "not_fault", "ignorance", "conflict"):
        np.testing.assert_allclose(getattr(ab, field), getattr(ba, field), atol=1e-12)
    np.testing.assert_allclose(ab.fault + ab.not_fault + ab.ignorance, 1.0, atol=1e-12)
    assert ab.conflict[0] == pytest.approx(0.0)
    assert ab.conflict[1] > 0.0  # one source supports fault; the other's small negative mass conflicts
    assert ab.ignorance[1] > ab.ignorance[0]  # disagreement leaves more residual uncertainty
    assert np.all((ab.fault >= 0) & (ab.fault <= 1))
    assert np.all((ab.ignorance >= 0) & (ab.ignorance <= 1))


def test_open_world_dempster_rejects_invalid_masses_and_shapes():
    a = sparse_open_world_bpa(np.array([0.0, 1.0]))
    with pytest.raises(ValueError, match="shapes"):
        combine_open_world_dempster(a, tuple(np.zeros(3) for _ in range(3)))
    with pytest.raises(ValueError, match="sum to one"):
        combine_open_world_dempster((np.array([0.2]), np.array([0.2]), np.array([0.2])),
                                    (np.array([0.2]), np.array([0.2]), np.array([0.6])))
    with pytest.raises(ValueError):
        sparse_open_world_bpa(np.array([1.1]))


def test_belief_normalization_is_relative_and_zeroes_outside():
    footprint = np.array([[True, True], [False, True]])
    belief = np.array([[0.2, 0.4], [0.9, 0.1]])
    normalized = normalize_belief(belief, footprint)
    np.testing.assert_allclose(normalized, [[0.5, 1.0], [0.0, 0.25]])
    assert normalized.dtype == np.float32


def test_hessian_line_response_is_finite_nonnegative_and_scale_sensitive():
    image = np.zeros((41, 41), dtype=np.float32)
    image[:, 18:23] = 1.0
    response_small = hessian_line_response(image, 2.0)
    response_large = hessian_line_response(image, 5.0)
    assert response_small.shape == image.shape
    assert np.isfinite(response_small).all() and np.isfinite(response_large).all()
    assert np.all(response_small >= 0) and np.all(response_large >= 0)
    assert response_small.max() > 0
    assert response_large.max() > 0


def test_robust_unit_scale_clips_and_masks_invalid_cells():
    values = np.array([[0.0, 1.0], [2.0, 10.0]], dtype=np.float32)
    valid = np.array([[True, True], [True, False]])
    scaled, high = robust_unit_scale(values, valid, percentile=100)
    assert high == 2.0
    np.testing.assert_allclose(scaled, [[0.0, 0.5], [1.0, 0.0]])


def test_deterministic_top_k_uses_row_major_ties():
    values = np.array([[1.0, 2.0, 2.0], [0.0, 2.0, 1.0]], dtype=np.float32)
    valid = np.ones_like(values, dtype=bool)
    selected = deterministic_top_k(values, valid, 2)
    expected = np.zeros_like(valid)
    expected.ravel()[[1, 2]] = True
    np.testing.assert_array_equal(selected, expected)
    assert selected.sum() == 2


def test_total_conflict_raises_in_shared_h56_and_h56b_builders():
    """Normalized Dempster is undefined at K=1; never silently use vacuous mass."""
    from runpy import run_path
    from pathlib import Path

    from gemsdoe48.dempster_shafer import dempster_combine

    with pytest.raises(ValueError, match="total/numerical conflict"):
        dempster_combine(np.array([1.0]), np.array([0.0]), alpha1=1.0, alpha2=1.0)

    fault_only = (np.array([1.0]), np.array([0.0]), np.array([0.0]))
    not_fault_only = (np.array([0.0]), np.array([1.0]), np.array([0.0]))
    with pytest.raises(ValueError, match="total conflict"):
        combine_open_world_dempster(fault_only, not_fault_only)

    repo_root = Path(__file__).resolve().parents[1]
    builder = run_path(str(repo_root / "scripts/build_submission_h56_belief.py"))
    with pytest.raises(ValueError, match="total conflict"):
        builder["dempster"](fault_only, not_fault_only)
