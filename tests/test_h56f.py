import numpy as np
import pytest

from gemsdoe48.h56f import prune_dotted


def test_pruning_ladder_only_removes_parent_cells():
    dotted = np.array([[1, 1, 0], [1, 0, 1]], dtype=bool)
    belief = np.array([[0.99, 0.95, 1.0], [0.90, 0.99, 0.94]], dtype=np.float32)
    expected = np.array([[True, True, False], [False, False, False]])
    np.testing.assert_array_equal(prune_dotted(dotted, belief, 0.95), expected)
    assert np.all(~prune_dotted(dotted, belief, 0.95) | dotted)
    assert prune_dotted(dotted, belief, 0.90).sum() >= prune_dotted(dotted, belief, 0.95).sum()
    assert prune_dotted(dotted, belief, 0.95).sum() >= prune_dotted(dotted, belief, 0.99).sum()


def test_pruning_rejects_invalid_shapes_thresholds_and_beliefs():
    parent = np.ones((2, 2), dtype=bool)
    values = np.ones((2, 2), dtype=np.float32)
    with pytest.raises(ValueError, match="identical shapes"):
        prune_dotted(parent, np.ones((1, 2)), 0.5)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        prune_dotted(parent, values, 1.01)
    with pytest.raises(ValueError, match="numeric"):
        prune_dotted(parent, values, "not-a-threshold")
    values[0, 0] = np.nan
    with pytest.raises(ValueError, match="finite"):
        prune_dotted(parent, values, 0.5)
    bad_parent = np.array([[1.0, 0.0], [np.nan, 1.0]])
    with pytest.raises(ValueError, match="binary"):
        prune_dotted(bad_parent, np.ones((2, 2)), 0.5)
    with pytest.raises(ValueError, match="binary"):
        prune_dotted(np.array([[0, 2], [1, 0]]), np.ones((2, 2)), 0.5)
