import sys, pathlib, numpy as np
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from gems48.metric import components, dti_bruteforce, ALPHA, BETA, OFFSETS

def test_worked_example_arithmetic():
    # organiser page 967: TP_w=3.00, FP_w=1.89, FN_w=2.00 -> 0.60
    assert abs(3.0 / (3.0 + ALPHA * 1.89 + BETA * 2.0) - 0.6027) < 1e-3

def test_kernel_offsets():
    assert len(OFFSETS) == 25
    assert abs(sum(k for *_, k in OFFSETS) - 9.3802978105) < 1e-8

def test_fast_equals_bruteforce():
    rng = np.random.default_rng(0)
    for _ in range(20):
        g = rng.random((14, 15)) < 0.08
        p = np.where(rng.random((14, 15)) < 0.12, rng.random((14, 15)), 0.0)
        if not g.any(): g[3, 3] = True
        assert abs(components(p, g)["DTI"] - dti_bruteforce(p, g)) < 1e-9

def test_scale_monotone():
    rng = np.random.default_rng(1)
    g = rng.random((30, 30)) < 0.05
    p = (rng.random((30, 30)) < 0.05).astype(float)
    assert components(p, g)["DTI"] > components(0.5 * p, g)["DTI"]
