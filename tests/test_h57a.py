from __future__ import annotations

import numpy as np
import pytest

from gemsdoe48.h57a import (
    deterministic_top_k,
    fit_huber_line,
    magnetic_gradient_magnitude,
    make_addition_surface,
    robust_residual_z,
)


def test_huber_fit_resists_a_large_outlier():
    x = np.arange(21, dtype=float)
    y = 5.0 + 2.0 * x
    y[-1] += 100.0
    fit = fit_huber_line(x, y)
    assert fit.intercept == pytest.approx(5.0, abs=2.0)
    assert fit.slope == pytest.approx(2.0, abs=0.15)
    assert fit.residual_scale > 0.0


def test_huber_rejects_invalid_or_degenerate_input():
    with pytest.raises(ValueError, match="at least 3"):
        fit_huber_line(np.array([1.0, 2.0]), np.array([2.0, 4.0]))
    with pytest.raises(ValueError, match="finite"):
        fit_huber_line(np.array([1.0, 2.0, np.nan]), np.array([2.0, 4.0, 6.0]))
    fit = fit_huber_line(np.ones(5), np.array([1.0, 2.0, 3.0, 4.0, 5.0]))
    assert fit.slope == 0.0
    assert fit.intercept == pytest.approx(3.0)


def test_residual_z_uses_valid_cells_and_zeroes_invalid_cells():
    th = np.arange(12, dtype=np.float32).reshape(3, 4)
    k = 10.0 + 3.0 * th
    k[1, 1] += 20.0
    valid = np.ones_like(th, dtype=bool)
    valid[0, 0] = False
    fit = fit_huber_line(th[valid], k[valid])
    z = robust_residual_z(th, k, fit, valid)
    assert z.shape == th.shape
    assert z.dtype == np.float32
    assert z[0, 0] == 0.0
    assert z[1, 1] > 2.0
    assert np.median(z[valid]) == pytest.approx(0.0, abs=1e-6)


def test_magnetic_gradient_erodes_nodata_edges():
    tmi = np.zeros((9, 9), dtype=np.uint8)
    valid = np.zeros((9, 9), dtype=bool)
    valid[1:8, 1:8] = True
    tmi[1:8, 1:8] = 20
    tmi[1:8, 4:8] = 100
    magnitude, inner = magnetic_gradient_magnitude(tmi, valid, pixel_size_m=1.0)
    assert inner.sum() == 25  # 5x5 after 3x3 erosion
    assert np.all(magnitude[~inner] == 0.0)
    assert np.all(magnitude[inner] >= 0.0)
    assert magnitude[4, 3] > 0.0


def test_deterministic_top_k_uses_row_major_ties_and_clamps_to_pool():
    values = np.array([[3.0, 4.0, 4.0], [0.0, 4.0, 1.0]])
    valid = np.ones_like(values, dtype=bool)
    chosen = deterministic_top_k(values, valid, 2)
    expected = np.zeros_like(valid)
    expected.ravel()[[1, 2]] = True
    np.testing.assert_array_equal(chosen, expected)
    assert deterministic_top_k(values, valid, 100).sum() == valid.sum()
    with pytest.raises(ValueError, match="nonnegative"):
        deterministic_top_k(values, valid, -1)


def test_make_addition_surface_preserves_baseline_and_zeros_outside():
    baseline = np.array([[0.2, 0.4], [0.8, 0.0]])
    additions = np.array([[False, True], [False, False]])
    footprint = np.array([[True, True], [False, True]])
    result = make_addition_surface(baseline, additions, footprint)
    np.testing.assert_allclose(result, [[0.2, 1.0], [0.0, 0.0]], rtol=0.0, atol=1e-7)
    assert result.dtype == np.float32
    with pytest.raises(ValueError, match="inside the footprint"):
        make_addition_surface(baseline, np.array([[False, False], [True, False]]), footprint)
    with pytest.raises(ValueError, match="finite and in \\[0, 1\\]"):
        make_addition_surface(np.array([[np.nan, 0.0], [0.0, 0.0]]), additions, footprint)
