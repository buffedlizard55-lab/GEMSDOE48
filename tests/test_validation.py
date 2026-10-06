import numpy as np
import pytest

from gems48.validation import score_dti, score_dti_regions


def test_perfect_pixel_prediction_scores_one():
    truth = np.zeros((5, 5), dtype=bool)
    truth[2, 2] = True
    prediction = truth.astype(np.float32)
    result = score_dti(prediction, truth, np.ones_like(truth))
    assert result["tp"] == pytest.approx(1.0)
    assert result["fp"] == pytest.approx(0.0)
    assert result["fn"] == pytest.approx(0.0)
    assert result["dti"] == pytest.approx(1.0)


def test_100m_miss_uses_triangular_kernel_and_exact_dti_terms():
    truth = np.zeros((5, 5), dtype=bool)
    truth[2, 2] = True
    prediction = np.zeros_like(truth, dtype=np.float32)
    prediction[2, 3] = 1.0
    result = score_dti(prediction, truth, np.ones_like(truth))
    assert result["tp"] == pytest.approx(2.0 / 3.0)
    assert result["fp"] == pytest.approx(1.0 / 3.0)
    assert result["fn"] == pytest.approx(1.0 / 3.0)
    assert result["dti"] == pytest.approx(2.0 / 3.0)


def test_fractional_prediction_confidence_scales_tp_not_just_binary_support():
    truth = np.zeros((5, 5), dtype=bool)
    truth[2, 2] = True
    prediction = np.zeros_like(truth, dtype=np.float32)
    prediction[2, 2] = 0.5
    result = score_dti(prediction, truth, np.ones_like(truth))
    assert result["tp"] == pytest.approx(0.5)
    assert result["fp"] == pytest.approx(0.0)
    assert result["fn"] == pytest.approx(0.5)
    assert result["dti"] == pytest.approx(5.0 / 9.0)


def test_best_confidence_times_kernel_is_used_for_each_truth_pixel():
    truth = np.zeros((5, 5), dtype=bool)
    truth[2, 2] = True
    prediction = np.zeros_like(truth, dtype=np.float32)
    prediction[2, 2] = 0.3
    prediction[2, 3] = 0.9
    result = score_dti(prediction, truth, np.ones_like(truth))
    assert result["tp"] == pytest.approx(0.9 * (2.0 / 3.0))


def test_excluded_known_fault_prediction_cannot_score_or_match_nearby_truth():
    truth = np.zeros((5, 5), dtype=bool)
    truth[2, 2] = True
    prediction = np.zeros_like(truth, dtype=np.float32)
    prediction[2, 1] = 1.0
    evaluation = np.ones_like(truth)
    evaluation[2, 1] = False
    result = score_dti(prediction, truth, evaluation)
    assert result["tp"] == pytest.approx(0.0)
    assert result["fp"] == pytest.approx(0.0)
    assert result["fn"] == pytest.approx(1.0)
    assert result["dti"] == pytest.approx(0.0)


def test_region_score_keeps_full_scene_distance_neighborhood_at_block_edge():
    truth = np.zeros((4, 4), dtype=bool)
    truth[1, 1] = True
    prediction = np.zeros_like(truth, dtype=np.float32)
    prediction[1, 2] = 1.0
    valid = np.ones_like(truth)
    truth_region = np.zeros_like(truth)
    truth_region[1, 1] = True
    prediction_region = np.zeros_like(truth)
    prediction_region[1, 2] = True
    result = score_dti_regions(
        prediction,
        truth,
        valid,
        {"truth_block": truth_region, "prediction_block": prediction_region},
    )
    # The prediction immediately across the block boundary still contributes
    # to TP for the held-out truth cell. It is not an FP inside that first block.
    assert result["truth_block"]["tp"] == pytest.approx(2.0 / 3.0)
    assert result["truth_block"]["fp"] == pytest.approx(0.0)
    assert result["prediction_block"]["tp"] == pytest.approx(0.0)
    assert result["prediction_block"]["fp"] == pytest.approx(1.0 / 3.0)


def test_random_small_grid_matches_independent_brute_force():
    rng = np.random.default_rng(20261006)
    truth = rng.random((6, 7)) < 0.12
    prediction = rng.random((6, 7), dtype=np.float32)
    valid = rng.random((6, 7)) > 0.08
    height, width = truth.shape

    tp = 0.0
    fn = 0.0
    for gy, gx in zip(*np.nonzero(truth & valid)):
        nearby = []
        for py in range(height):
            for px in range(width):
                if not valid[py, px]:
                    continue
                distance = np.hypot((py - gy) * 100.0, (px - gx) * 100.0)
                if distance < 300.0:
                    nearby.append(float(prediction[py, px]) * (1.0 - distance / 300.0))
        hit = max(nearby, default=0.0)
        tp += hit
        fn += 1.0 - hit

    fp = 0.0
    for py in range(height):
        for px in range(width):
            if not valid[py, px]:
                continue
            distance = min(
                (np.hypot((py - gy) * 100.0, (px - gx) * 100.0)
                 for gy, gx in zip(*np.nonzero(truth & valid))),
                default=float("inf"),
            )
            nearest_kernel = max(1.0 - distance / 300.0, 0.0)
            fp += float(prediction[py, px]) * (1.0 - nearest_kernel)

    result = score_dti(prediction, truth, valid)
    assert result["tp"] == pytest.approx(tp)
    assert result["fp"] == pytest.approx(fp)
    assert result["fn"] == pytest.approx(fn)
    assert result["dti"] == pytest.approx(tp / (tp + 0.2 * fp + 0.8 * fn) if tp + fp + fn else 0.0)


def test_invalid_prediction_range_and_grid_shapes_fail_closed():
    truth = np.zeros((3, 3), dtype=bool)
    valid = np.ones_like(truth)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        score_dti(np.full((3, 3), 1.1), truth, valid)
    with pytest.raises(ValueError, match="grids must match"):
        score_dti(np.zeros((3, 2)), truth, valid)
