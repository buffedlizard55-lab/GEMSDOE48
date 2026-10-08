"""Tests for the H58 dot-supported Dempster-Shafer fusion (src/gemsdoe48/ds58.py) and its artifacts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import rasterio

from gemsdoe48 import ds58

ROOT = Path(__file__).resolve().parents[1]


def _grid(shape=(40, 40)):
    fp = np.zeros(shape, dtype=bool)
    fp[5:35, 5:35] = True
    return fp


def test_reliabilities_are_owner_ratio_anchored_and_below_ceiling():
    ra, rb = ds58.reliabilities()
    assert ra == pytest.approx(ds58.RHO_MAX)
    assert 0.0 < rb < ra <= 1.0
    assert rb == pytest.approx(ds58.RHO_MAX * 0.2649 / 0.2778)


def test_dempster_masses_sum_to_one_on_random_inputs():
    rng = np.random.default_rng(0)
    b_a = rng.uniform(0, 1, (30, 30))
    b_b = rng.uniform(0, 1, (30, 30))
    m_f, m_n, m_t, k = ds58.dempster_masks(b_a, b_b, 0.95, 0.9)
    assert np.allclose(m_f + m_n + m_t, 1.0, atol=1e-12)
    assert np.all((k >= 0) & (k < 1))


def test_identical_dot_maps_agree_fully_and_have_zero_conflict():
    fp = _grid()
    dots = np.zeros_like(fp)
    dots[10, 10] = dots[20, 20] = True
    fus = ds58.fuse_dots(dots, dots, fp, 0.95, 0.9)
    assert np.allclose(fus.belief[fus.support], 1.0)
    assert np.allclose(fus.conflict[fus.support], 0.0)
    assert fus.support.sum() == 2


def test_disjoint_dots_disagree_and_single_source_is_discounted():
    fp = _grid()
    a = np.zeros_like(fp); a[10, 10] = True
    b = np.zeros_like(fp); b[30, 30] = True  # 2000 m away: beyond the 300 m kernel of a
    a[20, 20] = b[20, 20] = True             # one agreement cell sets the normalization maximum
    fus = ds58.fuse_dots(a, b, fp, 0.95, 0.9)
    assert fus.support[10, 10] and fus.support[30, 30]
    assert fus.conflict[10, 10] > 0.0 and fus.conflict[20, 20] == 0.0
    assert fus.belief[20, 20] == pytest.approx(1.0)
    assert fus.belief[10, 10] < 1.0 and fus.belief[30, 30] < 1.0
    # single-source belief follows the source discounts: the more reliable source (a) wins
    assert fus.belief[10, 10] > fus.belief[30, 30] > 0.0


def test_max_normalization_makes_strongest_single_source_cell_one_without_agreement():
    # documented behaviour: normalization is by the support maximum, so with no agreement cell
    # the strongest single-source cell is rescaled to 1 (the H50 convention)
    fp = _grid()
    a = np.zeros_like(fp); a[10, 10] = True
    b = np.zeros_like(fp); b[30, 30] = True
    fus = ds58.fuse_dots(a, b, fp, 0.95, 0.9)
    assert np.isclose(fus.belief.max(), 1.0)


def test_belief_is_zero_outside_support_and_in_unit_interval():
    fp = _grid()
    a = np.zeros_like(fp); a[12:15, 12:15] = True
    b = np.zeros_like(fp); b[18, 18] = True
    fus = ds58.fuse_dots(a, b, fp, 0.95, 0.9)
    outside = ~fus.support
    assert np.all(fus.belief[outside] == 0.0)
    assert np.isfinite(fus.belief).all()
    assert fus.belief.min() >= 0.0 and fus.belief.max() <= 1.0
    assert fus.belief.max() == pytest.approx(1.0)


def test_empty_support_is_rejected():
    fp = _grid()
    empty = np.zeros_like(fp)
    with pytest.raises(ValueError):
        ds58.fuse_dots(empty, empty, fp, 0.95, 0.9)


def test_naive_kernel_mean_is_not_the_dempster_output():
    fp = _grid()
    a = np.zeros_like(fp); a[10, 10] = True
    b = np.zeros_like(fp); b[30, 30] = True
    naive = ds58.naive_kernel_mean(a, b, fp)
    fus = ds58.fuse_dots(a, b, fp, 0.95, 0.9)
    assert not np.allclose(naive[fus.support], fus.belief[fus.support])


def _receipt_path():
    return ROOT / "evidence/build_h58_receipt_20261008.json"


@pytest.mark.skipif(not _receipt_path().exists(), reason="H58 build receipt not present")
def test_shipped_primary_matches_receipt_and_format():
    receipt = json.loads(_receipt_path().read_text())
    primary = ROOT / receipt["primary_file"]
    assert primary.exists()
    assert hashlib.sha256(primary.read_bytes()).hexdigest() == receipt["primary_sha256"]
    with rasterio.open(primary) as ds:
        arr = ds.read(1)
        assert ds.count == 1 and ds.dtypes[0] == "float32"
        assert ds.crs.to_epsg() == 32611 and (ds.height, ds.width) == (3730, 3292)
        assert ds.res == (100.0, 100.0) and ds.nodata is None
    assert np.isfinite(arr).all()
    assert arr.min() >= 0.0 and arr.max() <= 1.0
    assert int((arr > 0).sum()) == receipt["counts"]["primary_positive_cells"]
    assert receipt["verdict"]["submit_cleared"] is False
    assert len(receipt["submission_note"]) <= 200
