from math import hypot

import numpy as np
import pytest

from gemsdoe48.metric import distance_weighted_tversky, triangular_kernel


def brute_force(prediction, truth, *, valid=None, radius_m=300.0, pixel_size_m=100.0, alpha=0.2, beta=0.8):
    p = np.asarray(prediction, dtype=float)
    g = np.asarray(truth, dtype=bool)
    active = np.ones(p.shape, dtype=bool) if valid is None else np.asarray(valid, dtype=bool)
    truth_coords = [tuple(x) for x in np.argwhere(g & active)]
    pred_coords = [tuple(x) for x in np.argwhere(active & (p > 0))]
    tp = 0.0
    for gy, gx in truth_coords:
        credits = []
        for py, px in pred_coords:
            d = hypot((py - gy) * pixel_size_m, (px - gx) * pixel_size_m)
            credits.append(p[py, px] * max(1.0 - d / radius_m, 0.0))
        tp += max(credits, default=0.0)
    fp = 0.0
    for py, px in pred_coords:
        distances = [hypot((py - gy) * pixel_size_m, (px - gx) * pixel_size_m) for gy, gx in truth_coords]
        nearest_credit = max((max(1.0 - d / radius_m, 0.0) for d in distances), default=0.0)
        fp += p[py, px] * (1.0 - nearest_credit)
    fn = len(truth_coords) - tp
    dti = tp / (tp + alpha * fp + beta * fn + 1e-12) if truth_coords else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "n_truth": len(truth_coords), "dti": dti}


def test_triangular_kernel_in_meters():
    np.testing.assert_allclose(triangular_kernel(np.array([0, 100, 200, 300, 400]), 300), [1, 2 / 3, 1 / 3, 0, 0])


def test_metric_matches_independent_brute_force():
    rng = np.random.default_rng(4608)
    prediction = np.zeros((9, 10), dtype=np.float32)
    prediction[1:8, 1:9] = rng.choice([0.0, 0.2, 0.6, 1.0], size=(7, 8))
    truth = np.zeros_like(prediction, dtype=bool)
    truth[2, 3] = True
    truth[6, 7] = True
    expected = brute_force(prediction, truth)
    actual = distance_weighted_tversky(prediction, truth)
    for key in ("tp", "fp", "fn", "n_truth", "dti"):
        # The production implementation intentionally stores per-offset credits as float32.
        assert actual[key] == pytest.approx(expected[key], abs=1e-6)


def test_valid_mask_ignores_predictions_outside_domain():
    prediction = np.zeros((7, 7), dtype=np.float32)
    prediction[0, 0] = 1.0
    prediction[3, 3] = 1.0
    truth = np.zeros_like(prediction, dtype=bool)
    truth[3, 3] = True
    valid = np.zeros_like(truth)
    valid[2:5, 2:5] = True
    actual = distance_weighted_tversky(prediction, truth, valid=valid)
    expected = brute_force(prediction, truth, valid=valid)
    for key in ("tp", "fp", "fn", "n_truth", "dti"):
        assert actual[key] == pytest.approx(expected[key], abs=1e-10)
    assert actual["dti"] == pytest.approx(1.0)


def test_metric_empty_truth_and_invalid_inputs():
    prediction = np.zeros((4, 4), dtype=np.float32)
    result = distance_weighted_tversky(prediction, np.zeros_like(prediction, dtype=bool))
    assert result["dti"] == 0.0
    assert result["n_truth"] == 0
    with pytest.raises(ValueError):
        distance_weighted_tversky(np.full((3, 3), 2.0), np.zeros((3, 3)))
    with pytest.raises(ValueError):
        distance_weighted_tversky(np.zeros((3, 3)), np.zeros((4, 4)))
