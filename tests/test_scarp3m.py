"""Synthetic checks for the H50-1 linear scarp detector (src/gemsdoe48/scarp3m.py)."""
from __future__ import annotations

import numpy as np

from gemsdoe48 import scarp3m as S


def _plane(n: int, res: float, slope: float = 0.02):
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    return 1500.0 + slope * (n - yy) * res  # rising to the north


def test_step_in_smooth_plane_is_recovered_with_strike_and_facing():
    n, res = 400, 3.0
    z = _plane(n, res)
    # east-west striking 1.5 m scarp at row 200, upper block north: a step down to the south
    z[200:, :] -= 1.5
    rng = np.random.default_rng(0)
    z += rng.normal(0, 0.03, z.shape).astype(np.float32)
    out = S.detect(z, S.ScarpParams(res_m=res))
    core = out["height"][180:220, 150:250]
    # the 60 m regional detrend absorbs part of the step: expect ~0.7-0.8 of the true 1.5 m
    assert 0.9 < core.max() < 1.5, core.max()
    r, c = np.unravel_index(np.argmax(core), core.shape)
    strike = out["strike_deg"][180 + r, 150 + c]
    assert min(abs(strike - 90.0), abs(strike - 270.0)) < 10.0, strike
    assert out["facing"][180 + r, 150 + c] > 0.9
    assert out["sigma_ctx"][180 + r, 150 + c] < 0.7
    # far from the scarp the height is near zero
    assert out["height"][100, 200] < 0.2


def test_double_edged_road_has_small_far_field_offset():
    n, res = 400, 3.0
    z = _plane(n, res)
    z[200:201, :] -= 1.5  # 3 m wide, 1.5 m deep cut with the same level on both sides
    out = S.detect(z, S.ScarpParams(res_m=res))
    # v1 limitation (documented in the module): the far-field samples are single perpendicular
    # samples at +/-21 m, so a trench wider than ~6 m still registers when one sample falls in it.
    # A narrow track is suppressed by the 6 m local smoothing.
    assert out["height"][170:230, 150:250].max() < 0.5


def test_rough_terrain_gets_high_sigma_ctx_and_low_score():
    n, res = 400, 3.0
    yy, xx = np.mgrid[0:n, 0:n].astype(np.float32)
    z = 1500 + 8.0 * np.sin(xx / 6.0) * np.cos(yy / 7.0)
    out = S.detect(z, S.ScarpParams(res_m=res))
    v = out["valid"]
    assert np.median(out["sigma_ctx"][v]) > 2.0
    assert np.median(out["score"][v]) < 1.5


def test_aggregate_to_grid_max_and_cover():
    layer = np.arange(100, dtype=np.float32).reshape(10, 10)
    valid = np.ones_like(layer, dtype=bool)
    tile_tr = (10.0, 0.0, 1000.0, 0.0, -10.0, 2000.0)   # 10 m pixels, 100 m square
    grid_tr = (100.0, 0.0, 0.0, 0.0, -100.0, 5000.0)
    a, cover, (r0, c0) = S.aggregate_to_grid(layer, valid, tile_tr, grid_tr, (50, 50), "max")
    assert a.shape == (1, 1) and a[0, 0] == 99.0
    assert abs(cover[0, 0] - 1.0) < 1e-6
    assert (r0, c0) == (30, 10)
