import numpy as np
import pytest

from gems48.emission import poisson_sample, soft_emission


def _pairwise_min_distance(mask: np.ndarray) -> float:
    ys, xs = np.nonzero(mask)
    if ys.size < 2:
        return np.inf
    d = np.hypot(ys[:, None] - ys[None, :], xs[:, None] - xs[None, :])
    np.fill_diagonal(d, np.inf)
    return float(d.min())


def test_respects_budget_and_allowed_mask():
    rng = np.random.default_rng(0)
    score = rng.random((40, 40))
    allowed = np.zeros((40, 40), bool)
    allowed[5:30, 5:30] = True
    m = poisson_sample(score, 2.0, 7, allowed)
    assert m.sum() == 7
    assert np.all(m[~allowed] == False)  # noqa: E712


def test_respects_minimum_separation():
    rng = np.random.default_rng(1)
    score = rng.random((60, 60))
    allowed = np.ones((60, 60), bool)
    m = poisson_sample(score, 2.5, 40, allowed)
    assert _pairwise_min_distance(m) >= 2.0


def test_is_deterministic():
    rng = np.random.default_rng(2)
    score = rng.random((30, 30))
    allowed = np.ones((30, 30), bool)
    assert np.array_equal(poisson_sample(score, 2.0, 10, allowed),
                          poisson_sample(score, 2.0, 10, allowed))


def test_picks_the_highest_scores_first_when_unconstrained():
    score = np.zeros((11, 11))
    score[5, 5] = 0.9
    score[0, 0] = 1.0
    score[10, 10] = 0.8
    allowed = np.ones((11, 11), bool)
    m = poisson_sample(score, 0.5, 2, allowed)   # spacing below one cell -> no blocking
    assert m[0, 0] and m[5, 5] and not m[10, 10]


def test_budget_larger_than_candidate_pool_is_safe():
    score = np.ones((10, 10))
    allowed = (np.arange(100).reshape(10, 10) % 3 == 0)
    m = poisson_sample(score, 1.0, 10_000, allowed)
    assert m.sum() <= allowed.sum()


def test_empty_inputs():
    score = np.zeros((5, 5))
    allowed = np.zeros((5, 5), bool)
    assert poisson_sample(score, 2.0, 10, allowed).sum() == 0
    assert poisson_sample(score, 2.0, 0, np.ones((5, 5), bool)).sum() == 0


def test_shape_and_value_validation():
    with pytest.raises(ValueError):
        poisson_sample(np.zeros((5, 5)), 2.0, 1, np.ones((4, 4), bool))
    with pytest.raises(ValueError):
        poisson_sample(np.zeros((5, 5)), 0.0, 1, np.ones((5, 5), bool))
    with pytest.raises(ValueError):
        poisson_sample(np.zeros((5, 5)), 2.0, -1, np.ones((5, 5), bool))


def test_soft_emission_hits_the_mass_budget_and_stays_in_range():
    rng = np.random.default_rng(3)
    score = rng.random((40, 40))
    allowed = score > 0.2
    out = soft_emission(score, 25.0, allowed)
    assert out.min() >= 0.0 and out.max() <= 1.0
    assert out.sum() == pytest.approx(25.0, abs=0.5)
    # monotone in the score: no cell with a lower score carries a higher value
    sel = out > 0
    assert np.all(out[sel] <= 1.0 + 1e-6)


def test_soft_emission_empty_mask():
    assert soft_emission(np.zeros((5, 5)), 1.0, np.zeros((5, 5), bool)).sum() == 0
