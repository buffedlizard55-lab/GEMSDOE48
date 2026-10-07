"""Property tests for the H51 plausibility-budget emission rule."""
from __future__ import annotations

import numpy as np
import pytest

from gemsdoe48.h51 import (
    H51Preregistration,
    jaccard,
    plausibility_emission,
    plausibility_ranked_indices,
)


def test_emission_is_binary_and_budget_exact() -> None:
    rng = np.random.default_rng(51)
    pl = rng.random((40, 37))
    out = plausibility_emission(pl, budget=100)
    values = np.unique(out)
    assert np.all(np.isin(values, [0.0, 1.0]))
    assert int(out.sum()) == 100


def test_emitted_cells_dominate_non_emitted() -> None:
    rng = np.random.default_rng(52)
    pl = rng.random((25, 31))
    budget = 120
    out = plausibility_emission(pl, budget=budget)
    emitted_min = pl[out > 0].min()
    withheld_max = pl[out == 0].max()
    assert emitted_min >= withheld_max


def test_tie_break_is_low_row_major_index_and_deterministic() -> None:
    pl = np.ones((6, 7))  # every cell tied
    out1 = plausibility_emission(pl, budget=5)
    out2 = plausibility_emission(pl, budget=5)
    assert np.array_equal(out1, out2)
    idx = np.flatnonzero(out1.ravel() > 0)
    assert list(idx) == [0, 1, 2, 3, 4]


def test_where_mask_is_respected() -> None:
    rng = np.random.default_rng(53)
    pl = rng.random((20, 20))
    where = np.zeros_like(pl, dtype=bool)
    where[10:, 10:] = True
    out = plausibility_emission(pl, budget=37, where=where)
    assert int(out.sum()) == 37
    assert not np.any(out[~where] > 0)


def test_budget_larger_than_admissible_emits_all() -> None:
    pl = np.ones((4, 5))
    where = np.zeros_like(pl, dtype=bool)
    where[:2, :2] = True
    out = plausibility_emission(pl, budget=99, where=where)
    assert int(out.sum()) == 4


def test_invalid_inputs_raise() -> None:
    pl = np.ones((3, 3))
    with pytest.raises(ValueError):
        plausibility_emission(pl, budget=-1)
    bad = pl.copy()
    bad[0, 0] = np.nan
    with pytest.raises(ValueError):
        plausibility_emission(bad, budget=1)
    with pytest.raises(ValueError):
        plausibility_ranked_indices(np.ones(5))


def test_ranked_indices_cover_admissible_cells_once() -> None:
    rng = np.random.default_rng(54)
    pl = rng.random((9, 11))
    where = rng.random((9, 11)) < 0.5
    idx = plausibility_ranked_indices(pl, where)
    assert idx.size == int(where.sum())
    assert len(set(idx.tolist())) == idx.size
    assert np.all(where.ravel()[idx])


def test_jaccard() -> None:
    a = np.array([[1, 1, 0]], dtype=bool)
    b = np.array([[0, 1, 1]], dtype=bool)
    assert jaccard(a, b) == pytest.approx(1 / 3)
    assert jaccard(a, a) == pytest.approx(1.0)
    z = np.zeros(3, dtype=bool)
    assert jaccard(z, z) == 0.0


def test_preregistration_defaults_frozen() -> None:
    pre = H51Preregistration(
        budget=37_654,
        dotted_reliability=0.95,
        tip_reliability=0.926746,
        dotted_sha256="c55bafc4",
        tip_sha256="5556aa14",
    )
    assert pre.budget == 37_654
    assert "Pl(F) = Bel(F) + m(Theta)" in pre.rule
    with pytest.raises(Exception):
        pre.budget = 1  # frozen dataclass
