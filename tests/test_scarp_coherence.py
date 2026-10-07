from __future__ import annotations

import numpy as np
import pytest

from gemsdoe48.scarp_coherence import (
    circular_strike_difference,
    strike_coherent_scarp_score,
    strike_sample_offsets,
)


@pytest.mark.parametrize("strike", range(0, 180, 15))
def test_each_strike_bin_has_four_distinct_on_line_samples(strike: int):
    offsets = strike_sample_offsets(strike)
    assert len(offsets) == 4
    assert len(set(offsets)) == 4
    assert all(max(abs(dr), abs(dc)) <= 3 for dr, dc in offsets)


def _line_arrays(strike: int, center: tuple[int, int] = (10, 10)):
    h = np.zeros((21, 21), dtype=np.float32)
    bearing = np.zeros_like(h)
    cover = np.ones_like(h, dtype=np.float32)
    r, c = center
    h[r, c] = 1.0
    bearing[r, c] = strike
    for dr, dc in strike_sample_offsets(strike):
        rr, cc = r + dr, c + dc
        if 0 <= rr < h.shape[0] and 0 <= cc < h.shape[1]:
            h[rr, cc] = 1.0
            bearing[rr, cc] = strike
    return h, bearing, cover


def test_a_five_point_coherent_step_is_accepted_at_full_support():
    h, bearing, cover = _line_arrays(45)
    coherent, support, score = strike_coherent_scarp_score(h, bearing, cover)
    assert coherent[10, 10]
    assert support[10, 10] == 5
    assert score[10, 10] == pytest.approx(1.0)


def test_four_of_five_is_accepted_but_three_of_five_is_not():
    h, bearing, cover = _line_arrays(90)
    dr, dc = strike_sample_offsets(90)[0]
    h[10 + dr, 10 + dc] = 0.0
    coherent, support, score = strike_coherent_scarp_score(h, bearing, cover)
    assert coherent[10, 10]
    assert support[10, 10] == 4
    assert score[10, 10] == pytest.approx(0.8)

    dr, dc = strike_sample_offsets(90)[1]
    h[10 + dr, 10 + dc] = 0.0
    coherent, support, score = strike_coherent_scarp_score(h, bearing, cover)
    assert not coherent[10, 10]
    assert support[10, 10] == 0
    assert score[10, 10] == 0.0


def test_unoriented_strikes_wrap_at_zero_and_180_degrees():
    assert circular_strike_difference(0.0, 165.0) == pytest.approx(15.0)
    h, bearing, cover = _line_arrays(0)
    for dr, dc in strike_sample_offsets(0)[:2]:
        bearing[10 + dr, 10 + dc] = 165.0
    coherent, support, _ = strike_coherent_scarp_score(h, bearing, cover)
    assert coherent[10, 10]
    assert support[10, 10] == 5


def test_low_step_and_low_cover_samples_do_not_support_a_trace():
    h, bearing, cover = _line_arrays(0)
    offsets = strike_sample_offsets(0)
    for dr, dc in offsets[:2]:
        h[10 + dr, 10 + dc] = 0.29
    for dr, dc in offsets[2:]:
        cover[10 + dr, 10 + dc] = 0.89
    coherent, support, _ = strike_coherent_scarp_score(h, bearing, cover)
    assert not coherent[10, 10]
    assert support[10, 10] == 0


def test_no_wraparound_at_grid_edges():
    h, bearing, cover = _line_arrays(90, center=(10, 0))
    # Keep the center and samples that lie inside the raster; no data at the far edge.
    coherent, support, _ = strike_coherent_scarp_score(h, bearing, cover)
    assert not coherent[10, 0]
    assert support[10, 0] == 0


def test_shape_and_parameter_validation():
    h = np.ones((4, 4), dtype=np.float32)
    with pytest.raises(ValueError, match="same-shaped"):
        strike_coherent_scarp_score(h, np.ones((3, 4)), h)
    with pytest.raises(ValueError, match="min_cover"):
        strike_coherent_scarp_score(h, h, h, min_cover=1.1)
    with pytest.raises(ValueError, match="min_supported_samples"):
        strike_coherent_scarp_score(h, h, h, min_supported_samples=6)
