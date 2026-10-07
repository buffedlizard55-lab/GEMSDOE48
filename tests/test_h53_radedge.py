import numpy as np
import pytest

from gemsdoe48 import h53


def test_multiband_edge_coherence_detects_aligned_edges_and_masks_nodata():
    height, width = 64, 64
    yy, xx = np.mgrid[:height, :width]
    base = (xx >= 32).astype(np.float32) * 100.0
    bands = np.stack([base, base * 2.0 + yy * 0.01, base * 0.5 - yy * 0.01, base * 1.5])
    valid = np.ones((height, width), dtype=bool)
    valid[:, :3] = False
    bands[:, :, :3] = 0.0

    result = h53.multiband_edge_coherence(bands, valid, sigmas=(1.0, 3.0), min_mask_weight=0.99)

    assert result.score.shape == valid.shape
    assert np.isfinite(result.score).all()
    assert np.all((result.score >= 0.0) & (result.score <= 1.0))
    assert np.all(result.score[~valid] == 0.0)
    assert result.score[:, 28:36].max() > result.score[:, 10:20].max()
    assert result.coherence[:, 28:36].max() > 0.5
    assert len(result.band_scale_p99) == 2
    assert all(len(row) == 4 for row in result.band_scale_p99)


def test_multiband_edge_coherence_rejects_bad_shapes_and_parameters():
    bands = np.zeros((2, 8, 8), dtype=np.float32)
    valid = np.ones((8, 8), dtype=bool)
    with pytest.raises(ValueError, match="at least two bands"):
        h53.multiband_edge_coherence(bands[:1], valid)
    with pytest.raises(ValueError, match="valid_mask shape"):
        h53.multiband_edge_coherence(bands, np.ones((8, 7), dtype=bool))
    with pytest.raises(ValueError, match="sigmas"):
        h53.multiband_edge_coherence(bands, valid, sigmas=(0.0,))


def test_two_and_three_source_dempster_mass_and_conflict_diagnostics_are_separate():
    support_a = np.array([[1.0, 0.0, 0.8, 0.3]], dtype=np.float32)
    support_b = np.array([[0.0, 1.0, 0.7, 0.2]], dtype=np.float32)
    edge = np.array([[0.0, 0.0, 0.9, 0.4]], dtype=np.float32)
    a = h53.simple_support_bpa(support_a, 0.5)
    b = h53.simple_support_bpa(support_b, 0.5)
    c = h53.radiometric_bpa(edge, 0.25, 0.1)

    two = h53.dempster_two(a, b)
    three = h53.dempster_three(a, b, c)

    for masses in (two[:3], (three.fault, three.not_fault, three.unassigned_dempster)):
        total = sum(masses)
        assert np.allclose(total, 1.0, atol=2e-6)
        assert all(np.all((m >= 0.0) & (m <= 1.0)) for m in masses)
    assert np.any(three.conflict_ab > 0.0)
    assert np.any(three.conflict_total >= three.conflict_ab - 2e-6)
    assert np.any(three.unassigned_yager > three.unassigned_dempster)
    assert np.all((three.conflict_total >= 0.0) & (three.conflict_total <= 1.0))


def test_radiometric_non_edge_is_weak_not_fault_evidence():
    edge = np.array([[0.0, 1.0]], dtype=np.float32)
    fault, not_fault, ignorance = h53.radiometric_bpa(edge, 0.25, 0.1)
    assert fault.tolist() == [[0.0, 0.25]]
    assert not_fault.tolist() == [[0.02500000037252903, 0.0]]
    assert ignorance[0, 0] > 0.7
    assert np.allclose(fault + not_fault + ignorance, 1.0)
