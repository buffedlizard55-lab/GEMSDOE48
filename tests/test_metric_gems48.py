"""Tests for gems48.metric (this session's exact DTI implementation).

Renamed from tests/test_metric.py so that it can live beside the parallel
session's tests of gemsdoe48.metric, which is a separate module.
"""
import numpy as np
import pytest

from gems48.metric import (
    ALPHA,
    BETA,
    credit_per_dot,
    dti_result as dti,
    kernel_offsets,
    truth_kernel_max,
    weighted_tp_credit,
)


def _brute(pred, truth, alpha=ALPHA, beta=BETA, radius=3.0):
    """Literal transcription of the published formulas, loops and all."""
    import math

    pred = np.asarray(pred, dtype=np.float64)
    truth = np.asarray(truth, dtype=bool)
    h, w = pred.shape
    gs = [(y, x) for y in range(h) for x in range(w) if truth[y, x]]
    offs = [
        (dy, dx)
        for dy in range(-int(radius), int(radius) + 1)
        for dx in range(-int(radius), int(radius) + 1)
        if math.hypot(dy, dx) <= radius + 1e-12
    ]
    tp = 0.0
    fn = 0.0
    for gy, gx in gs:
        best = 0.0
        for dy, dx in offs:
            y, x = gy + dy, gx + dx
            if 0 <= y < h and 0 <= x < w:
                k = max(1.0 - math.hypot(dy, dx) / radius, 0.0)
                best = max(best, pred[y, x] * k)
        tp += best
        fn += 1.0 - best
    fp = 0.0
    for y in range(h):
        for x in range(w):
            if pred[y, x] > 0:
                kbest = 0.0
                for gy, gx in gs:
                    k = max(1.0 - math.hypot(y - gy, x - gx) / radius, 0.0)
                    kbest = max(kbest, k)
                fp += pred[y, x] * (1.0 - kbest)
    return tp / (tp + alpha * fp + beta * fn + 1e-12), tp, fp, fn


def test_kernel_offsets_metric_properties():
    offs, w = kernel_offsets(3.0)
    assert (0, 0) in offs
    assert len(offs) == 29  # closed Euclidean disc of radius 3
    d = {o: k for o, k in zip(offs, w)}
    assert d[(0, 0)] == pytest.approx(1.0)
    assert d[(1, 0)] == pytest.approx(2.0 / 3.0)
    assert d[(2, 0)] == pytest.approx(1.0 / 3.0)
    assert d[(3, 0)] == pytest.approx(0.0)
    assert d[(2, 2)] == pytest.approx(1.0 - np.hypot(2, 2) / 3.0)


def test_matches_bruteforce_on_random_fields():
    rng = np.random.default_rng(20261006)
    for trial in range(6):
        h, w = 22, 25
        truth = rng.random((h, w)) < 0.08
        if not truth.any():
            continue
        pred = (rng.random((h, w)) < 0.25) * rng.random((h, w))
        got = dti(pred, truth)
        exp_dti, exp_tp, exp_fp, exp_fn = _brute(pred, truth)
        assert got.tp == pytest.approx(exp_tp, abs=1e-9)
        assert got.fp == pytest.approx(exp_fp, abs=1e-9)
        assert got.fn == pytest.approx(exp_fn, abs=1e-9)
        assert got.dti == pytest.approx(exp_dti, abs=1e-9)


def test_official_worked_example_is_reproducible_when_fully_specified():
    """The published example (TP=3.00, FP=1.89, FN=2.00 -> 0.60) is a figure.

    The page does not publish the pixel values behind the figure, so the exact
    triple cannot be reconstructed from the official text alone.  What *is*
    checkable is the arithmetic: with those three components the published
    index follows from the published formula.
    """
    tp, fp, fn = 3.00, 1.89, 2.00
    assert tp / (tp + ALPHA * fp + BETA * fn) == pytest.approx(0.60, abs=0.005)


def test_tp_plus_fn_equals_truth_count():
    rng = np.random.default_rng(7)
    truth = rng.random((30, 30)) < 0.1
    pred = (rng.random((30, 30)) < 0.3).astype(np.float64)
    r = dti(pred, truth)
    assert r.tp + r.fn == pytest.approx(r.truth_pixels, abs=1e-9)


def test_continuous_magnitude_matters_in_tp():
    """Halving every value halves TP (the previous proxy treated TP as binary)."""
    truth = np.zeros((21, 21), bool)
    truth[10, :] = True
    pred = np.zeros((21, 21))
    pred[10, :] = 1.0
    full = dti(pred, truth)
    half = dti(pred * 0.5, truth)
    assert half.tp == pytest.approx(0.5 * full.tp, rel=1e-9)
    assert half.dti < full.dti


def test_perfect_overlap_scores_one_and_isolated_prediction_scores_zero():
    truth = np.zeros((21, 21), bool)
    truth[10, :] = True
    pred = np.zeros((21, 21))
    pred[10, :] = 1.0
    assert dti(pred, truth).dti == pytest.approx(1.0, abs=1e-9)
    far = np.zeros((21, 21))
    far[0, 0] = 1.0
    assert dti(far, truth).dti == pytest.approx(0.0, abs=1e-12)


def test_offset_prediction_loses_kernel_weight():
    truth = np.zeros((41, 41), bool)
    truth[20, :] = True
    pred = np.zeros((41, 41))
    pred[20, :] = 1.0
    on_line = dti(pred, truth).dti
    off1 = np.zeros((41, 41))
    off1[21, :] = 1.0
    assert dti(off1, truth).dti == pytest.approx(2.0 / 3.0, abs=1e-9)
    assert on_line == pytest.approx(1.0, abs=1e-9)


def test_credit_per_dot_sums_to_tp():
    rng = np.random.default_rng(11)
    truth = rng.random((40, 40)) < 0.05
    pred = (rng.random((40, 40)) < 0.2).astype(np.float64)
    res = dti(pred, truth)
    tot, cnt, _ = credit_per_dot(pred, truth)
    assert tot.sum() == pytest.approx(res.tp, abs=1e-9)
    # every credit is assigned to a predicted cell
    assert np.all((tot == 0) | (pred > 0))


def test_exact_metric_prediction_scaling_identity_is_not_a_live_inverse():
    """Check an algebraic identity; it does not identify hidden truth from owner scores.

    Scaling p by lambda scales both TPw and FPw linearly while FNw changes as
    N-lambda*TPw. Thus 1/DTI(lambda*p) = alpha*(1+FPw/TPw) +
    (beta/lambda)*(N/TPw). For a known synthetic truth mask this implies
    1/DTI(p/2)-1/DTI(p)=beta*N/TPw. No claim is made that owner-reported scores
    plus emitted counts invert the organizer's hidden truth or local file linkage.
    """
    rng = np.random.default_rng(3)
    truth = rng.random((35, 35)) < 0.08
    pred = (rng.random((35, 35)) < 0.3).astype(np.float64)
    base = dti(pred, truth)
    half = dti(pred * 0.5, truth)
    assert half.tp == pytest.approx(0.5 * base.tp, rel=1e-12)
    lhs = 1.0 / half.dti - 1.0 / base.dti
    rhs = BETA * base.truth_pixels / base.tp
    assert lhs == pytest.approx(rhs, rel=1e-9)


def test_added_mass_raises_denominator_by_alpha_regardless_of_place():
    """A prediction unit that earns zero credit costs exactly alpha per unit."""
    truth = np.zeros((41, 41), bool)
    truth[20, :] = True
    pred = np.zeros((41, 41))
    pred[20, :] = 1.0
    base = dti(pred, truth)
    junk = pred.copy()
    junk[40, 40] = 1.0  # > 300 m from any truth pixel
    with_junk = dti(junk, truth)
    assert with_junk.tp == pytest.approx(base.tp, abs=1e-12)
    assert with_junk.fp == pytest.approx(base.fp + 1.0, abs=1e-12)
    delta = 1.0 / with_junk.dti - 1.0 / base.dti
    assert delta == pytest.approx(ALPHA * 1.0 / base.tp, rel=1e-9)


def test_rejects_out_of_range_prediction():
    with pytest.raises(ValueError):
        dti(np.full((5, 5), 1.2), np.zeros((5, 5), bool))
    with pytest.raises(ValueError):
        dti(np.full((5, 5), -0.1), np.zeros((5, 5), bool))


def test_truth_kernel_max_is_a_dilation():
    truth = np.zeros((15, 15), bool)
    truth[7, 7] = True
    g = truth_kernel_max(truth)
    assert g[7, 7] == pytest.approx(1.0)
    assert g[7, 9] == pytest.approx(1.0 / 3.0)
    assert g[7, 11] == pytest.approx(0.0)


def test_weighted_tp_credit_uses_max_not_nearest():
    """A weak near prediction must not beat a strong slightly further one."""
    truth = np.zeros((11, 11), bool)
    truth[5, 5] = True
    pred = np.zeros((11, 11))
    pred[5, 6] = 0.10   # distance 1, k = 2/3 -> 0.0667
    pred[5, 8] = 1.00   # distance 3, k = 0    -> excluded
    pred[3, 5] = 1.00   # distance 2, k = 1/3  -> 0.3333
    credit, _ = weighted_tp_credit(pred, truth)
    assert credit[5, 5] == pytest.approx(1.0 / 3.0, abs=1e-9)
