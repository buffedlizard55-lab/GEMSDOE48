from __future__ import annotations

import numpy as np
import pytest

from scripts.build_h53_scarp_coherence import poisson_thin


def test_poisson_thin_enforces_euclidean_spacing_and_keeps_order():
    rows = np.array([10, 10, 10], dtype=np.int64)
    cols = np.array([10, 12, 13], dtype=np.int64)
    kept_rows, kept_cols = poisson_thin(rows, cols, np.zeros((24, 24), dtype=bool), 2, 2.828427)
    np.testing.assert_array_equal(kept_rows, [10, 10])
    np.testing.assert_array_equal(kept_cols, [10, 13])


def test_poisson_thin_respects_occupied_cells_and_zero_budget():
    occupied = np.zeros((12, 12), dtype=bool)
    occupied[5, 5] = True
    rows, cols = poisson_thin(np.array([5, 8]), np.array([6, 5]), occupied, 1, 2.0)
    np.testing.assert_array_equal(rows, [8])
    np.testing.assert_array_equal(cols, [5])

    rows, cols = poisson_thin(np.array([5]), np.array([6]), occupied, 0, 2.0)
    assert rows.size == cols.size == 0


def test_poisson_thin_rejects_malformed_or_out_of_bounds_coordinates():
    with pytest.raises(ValueError, match="same-shaped"):
        poisson_thin(np.array([0, 1]), np.array([0]), np.zeros((3, 3)), 1, 1.0)
    with pytest.raises(ValueError, match="within the occupied mask"):
        poisson_thin(np.array([-1]), np.array([0]), np.zeros((3, 3)), 1, 1.0)
    with pytest.raises(ValueError, match="coordinates must be integers"):
        poisson_thin(np.array([1.5]), np.array([0.0]), np.zeros((3, 3)), 1, 1.0)
    with pytest.raises(ValueError, match="nonnegative integer"):
        poisson_thin(np.array([1]), np.array([1]), np.zeros((3, 3)), 1.5, 1.0)
