"""Verification of the DTI metric implementation.

1. Hand-computed cases derived directly from the problem statement formulas.
2. The worked-example arithmetic from the problem statement:
   TPw=3.00, FPw=1.89, FNw=2.00 -> TI = 0.60.
3. Cross-validation: vectorized dti_fast == literal dti_bruteforce on
   random sparse scenes with graded predictions.
Run:  python3 -m pytest tests/test_metric.py -q
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gemsdoe48.metric import (ALPHA, BETA, dti_bruteforce, dti_components_fast,
                               dti_fast)


def test_perfect_single_pixel():
    """One truth pixel, one prediction of 1.0 exactly on it -> DTI = 1."""
    truth = np.zeros((11, 11)); truth[5, 5] = 1
    pred = np.zeros((11, 11)); pred[5, 5] = 1.0
    c = dti_components_fast(pred, truth)
    assert abs(c["TPw"] - 1.0) < 1e-12
    assert abs(c["FPw"]) < 1e-12
    assert abs(c["FNw"]) < 1e-12
    assert abs(c["DTI"] - 1.0) < 1e-9
    assert abs(dti_bruteforce(pred, truth)["DTI"] - 1.0) < 1e-9


def test_hand_computed_off_center_half_value():
    """Truth at (5,5); prediction p=0.5 at (5,7): d=2 px=200 m, k=1-2/3=1/3.
    TPw = 0.5/3 = 1/6; FNw = 5/6; FPw = 0.5*(1-1/3) = 1/3.
    DTI = (1/6) / (1/6 + 0.2/3 + 0.8*5/6) = 0.185185..."""
    truth = np.zeros((11, 11)); truth[5, 5] = 1
    pred = np.zeros((11, 11)); pred[5, 7] = 0.5
    c = dti_components_fast(pred, truth)
    assert abs(c["TPw"] - 1.0 / 6.0) < 1e-12, c["TPw"]
    assert abs(c["FNw"] - 5.0 / 6.0) < 1e-12, c["FNw"]
    assert abs(c["FPw"] - 1.0 / 3.0) < 1e-12, c["FPw"]
    assert abs(c["DTI"] - 0.18518518518518517) < 1e-9, c["DTI"]
    b = dti_bruteforce(pred, truth)
    assert abs(b["DTI"] - c["DTI"]) < 1e-12


def test_outside_kernel_full_fn_and_fp():
    """Prediction 4 px away (400 m > 300 m support): zero credit.
    TPw=0, FNw=1, FPw=1*1=1 -> DTI=0."""
    truth = np.zeros((13, 13)); truth[6, 2] = 1
    pred = np.zeros((13, 13)); pred[6, 6] = 1.0
    c = dti_components_fast(pred, truth)
    assert c["TPw"] == 0.0
    assert abs(c["FNw"] - 1.0) < 1e-12
    assert abs(c["FPw"] - 1.0) < 1e-12
    assert c["DTI"] < 1e-9
    assert abs(dti_bruteforce(pred, truth)["DTI"] - c["DTI"]) < 1e-12


def test_kernel_boundary_exact_300m():
    """Prediction exactly 3 px (300 m) from truth: k=0 -> no credit, FP full."""
    truth = np.zeros((11, 11)); truth[5, 2] = 1
    pred = np.zeros((11, 11)); pred[5, 5] = 1.0
    c = dti_components_fast(pred, truth)
    assert c["TPw"] == 0.0
    assert abs(c["FNw"] - 1.0) < 1e-12
    assert abs(c["FPw"] - 1.0) < 1e-12


def test_worked_example_arithmetic():
    """Problem statement worked example: TPw=3.00, FPw=1.89, FNw=2.00 -> 0.60."""
    tpw, fpw, fnw = 3.00, 1.89, 2.00
    ti = tpw / (tpw + ALPHA * fpw + BETA * fnw)
    assert abs(ti - 0.60) < 0.005, ti  # statement prints 0.60 (rounded)


def test_fast_matches_bruteforce_random():
    """Vectorized implementation must equal the literal one on random scenes."""
    rng = np.random.default_rng(20261006)
    for trial in range(8):
        h, w = 24, 26
        truth = (rng.random((h, w)) < 0.04).astype(np.float64)
        pred = np.zeros((h, w))
        mask = rng.random((h, w)) < 0.06
        pred[mask] = rng.random(mask.sum())
        f = dti_components_fast(pred, truth)
        b = dti_bruteforce(pred, truth)
        for key in ("TPw", "FPw", "FNw", "DTI"):
            assert abs(f[key] - b[key]) < 1e-9 * max(1.0, abs(b[key])), \
                (trial, key, f[key], b[key])


def test_no_wraparound_at_border():
    """Kernel shifts must zero-fill, never wrap: truth at left border must not
    receive credit from a prediction at the right border of the same row."""
    truth = np.zeros((9, 40)); truth[4, 0] = 1
    pred = np.zeros((9, 40)); pred[4, 39] = 1.0
    c = dti_components_fast(pred, truth)
    assert c["TPw"] == 0.0
    assert abs(c["FNw"] - 1.0) < 1e-12
    assert abs(c["FPw"] - 1.0) < 1e-12


def test_graded_domination():
    """For a single truth pixel, TPw takes the MAX of p*k, not the sum."""
    truth = np.zeros((11, 11)); truth[5, 5] = 1
    pred = np.zeros((11, 11))
    pred[5, 5] = 0.4          # k=1     -> 0.4
    pred[5, 6] = 0.9          # k=2/3   -> 0.6  (max)
    c = dti_components_fast(pred, truth)
    assert abs(c["TPw"] - 0.6) < 1e-12
    # FP: (5,5) d=0 -> 0; (5,6) d=1px -> 0.9*(1-2/3)=0.3
    assert abs(c["FPw"] - 0.3) < 1e-12
    assert abs(c["FNw"] - 0.4) < 1e-12


if __name__ == "__main__":
    import traceback
    fns = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    fails = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except Exception:
            fails += 1
            print(f"FAIL {fn.__name__}")
            traceback.print_exc()
    print(f"{len(fns) - fails}/{len(fns)} passed")
    sys.exit(1 if fails else 0)
