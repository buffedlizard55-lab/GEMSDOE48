"""The competition metric, implemented exactly.

Official definition (DrivenData competition 306, problem-description page 967,
transcribed verbatim by two independent sibling repositories; see docs/sources):

    k(d)  = max(1 - d / 300 m, 0)                      triangular kernel, 300 m reach
    TPw   = sum over truth pixels g of  max over prediction pixels x of  p(x) * k(d(x, g))
    FPw   = sum over prediction pixels x of  p(x) * (1 - max over truth pixels g of k(d(x, g)))
    FNw   = sum over truth pixels g of  (1 - max over prediction pixels x of p(x) * k(d(x, g)))
    DTI   = TPw / (TPw + 0.2 * FPw + 0.8 * FNw + eps)

`p(x)` is the submitted value in [0, 1]; the raster is single-band float32 on
EPSG:32611, 100 m pixels.  This is the *Tversky index* with alpha = 0.2 (false
positives) and beta = 0.8 (false negatives) -- the organizers' own reference
solution trains with `TverskyLoss(alpha=0.2, beta=0.8)`, which is an independent
official corroboration of the weights (see docs/sources.html, fact `REF-LOSS`).

Two exact identities are used by the rest of the package and are asserted in
tests/test_metric.py:

    S  = sum_x p(x)                 total emitted mass
    M  = sum_x p(x) * max_g k(x, g) "self-credit" of the emitted mass
    FPw = S - M                     (holds exactly)
    FNw = |G| - TPw                 (holds exactly, because p <= 1 and k <= 1)
    DTI = TPw / (0.2*TPw + 0.2*FPw + 0.8*|G|)

Fast implementation
-------------------
On a 100 m grid every distance is 100 * sqrt(dr^2 + dc^2) metres, so the kernel
takes only 25 distinct non-zero values, one per integer offset (dr, dc) with
dr^2 + dc^2 < 9.  The `max` operators therefore collapse to 25 shifted-array
operations -- O(25 * N) instead of O(N * |G|) -- and are exact, not approximate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

# --- constants -------------------------------------------------------------

ALPHA = 0.2  # official false-positive weight
BETA = 0.8  # official false-negative weight
KERNEL_REACH_M = 300.0  # official kernel reach
PIXEL_SIZE_M = 100.0  # official grid resolution (EPSG:32611, 100 m)
EPS = 1e-9  # the "+ eps" in the official denominator


def kernel_offsets(pixel_size_m: float = PIXEL_SIZE_M, reach_m: float = KERNEL_REACH_M):
    """Return the exact set of (dr, dc, k) triples with k > 0.

    Only integer-pixel offsets can carry non-zero credit on a square grid whose
    pixel size divides the kernel reach, so this list is complete and exact.
    """
    offs = []
    rmax = int(np.floor(reach_m / pixel_size_m))
    for dr in range(-rmax, rmax + 1):
        for dc in range(-rmax, rmax + 1):
            d_m = pixel_size_m * float(np.hypot(dr, dc))
            k = max(1.0 - d_m / reach_m, 0.0)
            if k > 0.0:
                offs.append((dr, dc, k))
    return offs


OFFSETS = kernel_offsets()
N_OFFSETS = len(OFFSETS)
K_VALUES = np.array([k for _, _, k in OFFSETS], dtype=np.float64)
DR = np.array([dr for dr, _, _ in OFFSETS], dtype=np.int64)
DC = np.array([dc for _, dc, _ in OFFSETS], dtype=np.int64)


# --- helpers ---------------------------------------------------------------


def _shift(a: np.ndarray, dr: int, dc: int, fill: float = 0.0) -> np.ndarray:
    """`out[r, c] = a[r - dr, c - dc]`, zero-filled outside `a`.

    That is, `a` is moved by `(+dr, +dc)` in array coordinates: an impulse at
    `(r0, c0)` reappears at `(r0 + dr, c0 + dc)`.

    The sign is immaterial for every caller in this module: the offset set
    `OFFSETS` is closed under `(dr, dc) -> (-dr, -dc)` with equal weight, and the
    `k` used here is symmetric (`k(dr, dc) == k(-dr, -dc)`, verified in
    tests/test_metric.py::TestKernel::test_kernel_is_symmetric), so reducing with
    either sign yields the same `max`.  The convention is pinned by
    tests/test_metric.py::TestExactness::test_shift_convention_is_pinned.

    Using a `max` with `fill = 0.0` is safe: every kernel weight is >= 0 and the
    submitted values are >= 0, so a missing neighbour can never be the argmax.
    """
    out = np.full_like(a, fill, dtype=np.float64)
    h, w = a.shape
    r0, r1 = max(dr, 0), min(h, h + dr)
    c0, c1 = max(dc, 0), min(w, w + dc)
    if r0 >= r1 or c0 >= c1:
        return out
    out[r0:r1, c0:c1] = a[r0 - dr : r1 - dr, c0 - dc : c1 - dc]
    return out


def max_credit_field(field: np.ndarray) -> np.ndarray:
    """`max` over the 25 kernel offsets of `field` times the kernel weight.

    Invariant to the sign convention of `_shift`, because the offset set is
    symmetric and the kernel is symmetric; see `_shift`.

    With `field = p` this is, for every pixel x, `max_x' p(x') k(d(x, x'))` -- the
    quantity whose sum over truth pixels is `TPw` and whose sum weighted by `p`
    is `M`.
    """
    out = np.zeros(field.shape, dtype=np.float64)
    for dr, dc, k in OFFSETS:
        np.maximum(out, _shift(field, dr, dc) * k, out=out)
    return out


def max_kernel_to_truth(truth_mask: np.ndarray) -> np.ndarray:
    """`max_g k(d(x, g))` for every pixel x, given a boolean truth mask."""
    t = truth_mask.astype(np.float64)
    out = np.zeros(t.shape, dtype=np.float64)
    for dr, dc, k in OFFSETS:
        np.maximum(out, _shift(t, dr, dc) * k, out=out)
    return out


# --- the metric ------------------------------------------------------------


@dataclass(frozen=True)
class DTIResult:
    """Every quantity the official metric is built from, plus the score."""

    dti: float
    tpw: float
    fpw: float
    fnw: float
    mass: float  # S = sum of the prediction surface
    self_credit: float  # M = sum_x p(x) * max_g k
    n_truth: int  # |G|
    n_emitted: int  # count of positive pixels (regardless of value)
    coverage: float  # TPw / |G|, the weighted recall

    def as_dict(self) -> dict:
        return {
            "dti": self.dti,
            "tpw": self.tpw,
            "fpw": self.fpw,
            "fnw": self.fnw,
            "mass": self.mass,
            "self_credit": self.self_credit,
            "n_truth": self.n_truth,
            "n_emitted": self.n_emitted,
            "coverage": self.coverage,
        }


def dti(
    prediction: np.ndarray,
    truth_mask: np.ndarray,
    footprint: np.ndarray | None = None,
    *,
    validate: bool = True,
    precomputed_max_kernel: np.ndarray | None = None,
) -> DTIResult:
    """Score `prediction` against `truth_mask` with the official metric.

    Parameters
    ----------
    prediction : 2-D array, values in [0, 1].  NaN is treated as 0 (absent).
    truth_mask : 2-D boolean array, True where the ground truth is a fault.
    footprint : 2-D boolean array, the region the organizers score.  Predictions
        outside it are ignored (the organizers require a full-grid raster, and
        pixels outside the study area carry no truth and no penalty).
    """
    p = np.asarray(prediction, dtype=np.float64)
    if p.ndim != 2:
        raise ValueError(f"prediction must be 2-D, got shape {p.shape}")
    p = np.where(np.isfinite(p), p, 0.0)
    t = np.asarray(truth_mask).astype(bool)
    if t.shape != p.shape:
        raise ValueError(f"truth {t.shape} != prediction {p.shape}")
    if validate:
        bad = int(((p < 0.0) | (p > 1.0)).sum())
        if bad:
            raise ValueError(f"{bad} prediction values outside [0, 1]")

    if footprint is not None:
        fp = np.asarray(footprint).astype(bool)
        if fp.shape != p.shape:
            raise ValueError("footprint shape mismatch")
        p = np.where(fp, p, 0.0)
        t = t & fp

    mass = float(p.sum())
    n_emitted = int((p > 0).sum())
    n_truth = int(t.sum())

    mc = max_credit_field(p)  # for each x: max over x' of p*k
    kt = (
        max_kernel_to_truth(t)
        if precomputed_max_kernel is None
        else precomputed_max_kernel
    )  # for each x: max over g of k

    tpw = float(mc[t].sum())  # sum over truth pixels of max credit
    self_credit = float((p * kt).sum())  # M
    fpw = float(mass - self_credit)  # exact identity
    fnw = float(n_truth - tpw)  # exact identity
    denom = tpw + ALPHA * fpw + BETA * fnw + EPS
    return DTIResult(
        dti=float(tpw / denom),
        tpw=tpw,
        fpw=fpw,
        fnw=fnw,
        mass=mass,
        self_credit=self_credit,
        n_truth=n_truth,
        n_emitted=n_emitted,
        coverage=float(tpw / n_truth) if n_truth else float("nan"),
    )


def dti_bruteforce(
    prediction: np.ndarray,
    truth_mask: np.ndarray,
    footprint: np.ndarray | None = None,
) -> DTIResult:
    """Deliberately naive O(|G| * N) transcription of the official equations.

    Used only by tests, to prove the fast implementation above is exact.
    """
    p = np.asarray(prediction, dtype=np.float64)
    p = np.where(np.isfinite(p), p, 0.0)
    t = np.asarray(truth_mask).astype(bool)
    if footprint is not None:
        fp = np.asarray(footprint).astype(bool)
        p = np.where(fp, p, 0.0)
        t = t & fp

    h, w = p.shape
    gr, gc = np.nonzero(t)
    n_truth = int(gr.size)
    if n_truth == 0:
        raise ValueError("no truth pixels")

    ys, xs = np.nonzero(p > 0)
    pv = p[ys, xs]
    mass = float(pv.sum())

    # TPw: for every truth pixel, the single best weighted prediction nearby
    tpw = 0.0
    best_per_truth = np.zeros(n_truth)
    for i in range(n_truth):
        r, c = gr[i], gc[i]
        r0, r1 = max(0, r - 3), min(h, r + 4)
        c0, c1 = max(0, c - 3), min(w, c + 4)
        sub = p[r0:r1, c0:c1]
        if not sub.any():
            continue
        rr, cc = np.nonzero(sub)
        drr = rr + r0 - r
        dcc = cc + c0 - c
        d_m = PIXEL_SIZE_M * np.hypot(drr, dcc)
        k = np.maximum(1.0 - d_m / KERNEL_REACH_M, 0.0)
        best_per_truth[i] = float(np.max(sub[rr, cc] * k))
    tpw = float(best_per_truth.sum())

    # FPw: for every positive prediction pixel, full mass minus best kernel reach
    fpw = 0.0
    for i in range(ys.size):
        r, c = ys[i], xs[i]
        r0, r1 = max(0, r - 3), min(h, r + 4)
        c0, c1 = max(0, c - 3), min(w, c + 4)
        sub = t[r0:r1, c0:c1]
        if not sub.any():
            fpw += pv[i]
            continue
        rr, cc = np.nonzero(sub)
        d_m = PIXEL_SIZE_M * np.hypot(rr + r0 - r, cc + c0 - c)
        k = np.maximum(1.0 - d_m / KERNEL_REACH_M, 0.0)
        fpw += pv[i] * (1.0 - float(k.max()))

    fnw = float(n_truth) - tpw
    denom = tpw + ALPHA * fpw + BETA * fnw + EPS
    return DTIResult(
        dti=float(tpw / denom),
        tpw=tpw,
        fpw=float(fpw),
        fnw=fnw,
        mass=mass,
        self_credit=float(mass - fpw),
        n_truth=n_truth,
        n_emitted=int(ys.size),
        coverage=float(tpw / n_truth),
    )


def credit_bar(dti_value: float) -> float:
    """The marginal-credit bar: adding mass at realised kernel weight k raises the
    score iff k > 0.2 * DTI  (derivation in docs/research/).

    Proof: DTI = T / (0.2T + 0.2FP + 0.8|G|).  Adding one unit of mass p = 1 at a
    pixel that becomes the argmax of its truth pixel changes T by k and the
    denominator by exactly 0.2 (because dS = +1 and dM = +k, so dFP = 1 - k, and
    dBETA*FN cancels: 0.2k + 0.2(1-k) - 0.8k = 0.2 - 0.8k).  The score rises iff
    dT/dD > T/D, i.e. k/0.2 > DTI.
    """
    return ALPHA * float(dti_value)


def optimal_value_is_binary() -> str:
    """The submission-optimality result, stated for the record.

    For a single pixel whose realised kernel weight is k and whose value is v,
    the score is (T0 + v*k) / (D0 + 0.2*v) as long as the pixel remains the
    argmax of its truth pixel.  Its derivative in v is
        [k*D0 - 0.2*T0] / (D0 + 0.2 v)^2,
    which has the sign of (k - 0.2*DTI) and is independent of v.  Therefore
    every pixel is either pushed to the top of the legal range or to zero:
    the DTI-optimal submission is binary {0, 1}, not a graded probability
    surface.  Grading (including normalising a belief surface into [0, 1])
    strictly lowers the score whenever it puts mass on pixels below the bar.
    """
    return "binary {0,1} is DTI-optimal; graded surfaces lose"


def dilate(mask: np.ndarray, radius_px: int) -> np.ndarray:
    """Boolean Chebyshev dilation by `radius_px` (pure numpy, no scipy needed)."""
    out = mask.copy()
    for _ in range(int(radius_px)):
        cur = out
        up = np.zeros_like(cur)
        up[1:, :] = cur[:-1, :]
        dn = np.zeros_like(cur)
        dn[:-1, :] = cur[1:, :]
        lf = np.zeros_like(cur)
        lf[:, 1:] = cur[:, :-1]
        rt = np.zeros_like(cur)
        rt[:, :-1] = cur[:, 1:]
        out = cur | up | dn | lf | rt
    return out


def offsets_as_tuples() -> Iterable[tuple[int, int, float]]:
    return tuple(OFFSETS)
