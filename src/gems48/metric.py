"""Official distance-weighted Tversky index (DrivenData #306 / DOE GEMS Prize).

Implements the metric exactly as published on the official problem description
page (https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/):

    k(d)    = max(1 - d/R, 0)                        (triangular kernel, R = 300 m)
    TP_w    = sum_{g in G}        max_{x: d(x,g) <= R} p(x) k(d(x,g))
    FP_w    = sum_{x: p(x) > 0}   p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w    = sum_{g in G}        [1 - max_{x: d(x,g) <= R} p(x) k(d(x,g))]
    DTI(a,b)= TP_w / (TP_w + a FP_w + b FN_w + eps)  with a = 0.2, b = 0.8

Distances are Euclidean and measured in grid cells; at the competition's 100 m
resolution the published support R = 300 m is exactly R = 3 cells.

The previous session in this repository scored candidates with an approximation
that (i) used a *nearest-positive* distance transform for TP instead of the
published max over the kernel support, (ii) ignored the magnitude of p in TP
(binary support), and (iii) evaluated FN as |G| - TP from that same binary
support.  Those three differences matter for continuous emissions, which is why
this module implements the published formulas literally and is verified against
a brute-force reference in ``tests/test_metric.py``.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ALPHA = 0.2
BETA = 0.8
RADIUS_CELLS = 3.0


def kernel_offsets(radius: float = RADIUS_CELLS):
    """Return (offsets, weights) for every cell with Euclidean distance <= radius.

    Offsets are (dy, dx) integer pairs; weights are k(d) = max(1 - d/R, 0).
    """
    r = int(np.floor(radius))
    dy, dx = np.mgrid[-r : r + 1, -r : r + 1]
    d = np.hypot(dy, dx)
    keep = d <= radius + 1e-12
    offs = list(zip(dy[keep].ravel().tolist(), dx[keep].ravel().tolist()))
    w = np.maximum(1.0 - d[keep] / radius, 0.0).ravel()
    return offs, w.astype(np.float64)


def _shift(a: np.ndarray, dy: int, dx: int, fill: float = 0.0) -> np.ndarray:
    """Shift ``a`` so that out[0,0] = a[dy, dx]; outside is filled."""
    out = np.full(a.shape, fill, dtype=np.float64)
    ys_src = slice(max(0, dy), max(0, dy) + a.shape[0] - abs(dy)) if dy >= 0 else slice(0, a.shape[0] + dy)
    xs_src = slice(max(0, dx), max(0, dx) + a.shape[1] - abs(dx)) if dx >= 0 else slice(0, a.shape[1] + dx)
    ys_dst = slice(max(0, -dy), max(0, -dy) + a.shape[0] - abs(dy)) if dy <= 0 else slice(0, a.shape[0] - dy)
    xs_dst = slice(max(0, -dx), max(0, -dx) + a.shape[1] - abs(dx)) if dx <= 0 else slice(0, a.shape[1] - dx)
    out[ys_dst, xs_dst] = a[ys_src, xs_src]
    return out


def weighted_tp_credit(pred: np.ndarray, truth: np.ndarray, radius: float = RADIUS_CELLS):
    """Per-truth-pixel credit ``max_{x: d(x,g) <= R} p(x) k(d(x,g))``.

    Returns (credit_map, best_index_map).  ``credit_map`` is non-zero only on
    truth pixels; ``best_index_map`` holds the flat index of the predicted cell
    that supplied each truth pixel's maximum (ties keep the lowest flat index).
    """
    pred = np.asarray(pred, dtype=np.float64)
    truth = np.asarray(truth, dtype=bool)
    offs, w = kernel_offsets(radius)
    h, wd = pred.shape
    best_val = np.zeros(pred.shape, dtype=np.float64)
    best_idx = np.full(pred.shape, -1, dtype=np.int64)
    flat = np.arange(pred.size).reshape(pred.shape)
    for (dy, dx), kk in zip(offs, w):
        if kk <= 0:
            continue
        # predicted cell (y+dy, x+dx) sits at offset distance from (y, x)
        cand = _shift(pred, dy, dx) * kk
        src = _shift(flat, dy, dx, fill=-1).astype(np.int64)
        better = cand > best_val
        # deterministic tie-break: keep the previously stored (lower flat) index
        best_val = np.where(better, cand, best_val)
        best_idx = np.where(better, src, best_idx)
    credit = np.where(truth, best_val, 0.0)
    return credit, best_idx


def truth_kernel_max(truth: np.ndarray, radius: float = RADIUS_CELLS) -> np.ndarray:
    """``max_{g in G} k(d(x,g))`` for every pixel x (grayscale dilation by k)."""
    truth = np.asarray(truth, dtype=bool)
    offs, w = kernel_offsets(radius)
    out = np.zeros(truth.shape, dtype=np.float64)
    tf = truth.astype(np.float64)
    for (dy, dx), kk in zip(offs, w):
        out = np.maximum(out, _shift(tf, dy, dx) * kk)
    return out


@dataclass
class DTIResult:
    tp: float
    fp: float
    fn: float
    dti: float
    truth_pixels: int
    mass: float

    def as_dict(self) -> dict:
        return {
            "tp_w": self.tp,
            "fp_w": self.fp,
            "fn_w": self.fn,
            "dti": self.dti,
            "truth_pixels": self.truth_pixels,
            "emitted_mass": self.mass,
        }


def dti_result(pred: np.ndarray, truth: np.ndarray, alpha: float = ALPHA, beta: float = BETA,
               radius: float = RADIUS_CELLS, eps: float = 1e-12) -> DTIResult:
    """Full DTI breakdown for a (possibly continuous) prediction.

    ``dti()`` returns the scalar; this returns the TP/FP/FN/mass breakdown too.
    """
    pred = np.asarray(pred, dtype=np.float64)
    truth = np.asarray(truth, dtype=bool)
    if pred.shape != truth.shape:
        raise ValueError("prediction and truth must share a shape")
    if np.any(pred < 0) or np.any(pred > 1):
        raise ValueError("prediction values must lie in [0, 1]")
    credit, _ = weighted_tp_credit(pred, truth, radius)
    tp = float(credit.sum())
    n_truth = int(truth.sum())
    fn = float(n_truth - tp)  # == sum_g [1 - max_x p k] by construction
    gmax = truth_kernel_max(truth, radius)
    fp = float((pred * (1.0 - gmax)).sum())
    denom = tp + alpha * fp + beta * fn + eps
    return DTIResult(tp=tp, fp=fp, fn=fn, dti=tp / denom, truth_pixels=n_truth,
                     mass=float(pred.sum()))


def credit_per_dot(pred: np.ndarray, truth: np.ndarray, radius: float = RADIUS_CELLS):
    """Attribute TP_w to individual predicted cells.

    Returns (credit_by_flat_index, counts_by_flat_index): for binary emissions
    every truth pixel's realised credit is assigned to the flat index of the
    predicted cell that achieved its maximum, so the total equals TP_w exactly.
    """
    pred = np.asarray(pred, dtype=np.float64)
    truth = np.asarray(truth, dtype=bool)
    credit_map, best_idx = weighted_tp_credit(pred, truth, radius)
    sel = truth & (best_idx >= 0) & (credit_map > 0)
    idx = best_idx[sel]
    val = credit_map[sel]
    n = pred.size
    tot = np.bincount(idx, weights=val, minlength=n).reshape(pred.shape)
    cnt = np.bincount(idx, minlength=n).reshape(pred.shape).astype(np.int64)
    return tot, cnt, credit_map

# --------------------------------------------------------------------------
# API contributed by the parallel DS48 session: a scalar ``dti``, the
# ``components`` dictionary, the raw ``OFFSETS`` table and a brute-force
# reference.  Both this module and ``gemsdoe48.metric`` implement the same
# published formulas; cross-checking them is deliberate.
# --------------------------------------------------------------------------
R_PX = RADIUS_CELLS
_EPS = 1e-12
OFFSETS = [(dy, dx, float(k)) for (dy, dx), k in zip(*kernel_offsets(RADIUS_CELLS)) if k > 0]


def kernel(d):
    """k(d) = max(1 - d/R, 0), R = 3 cells (300 m)."""
    return np.clip(1.0 - np.asarray(d, dtype=np.float64) / R_PX, 0.0, None)


def components(p, g, mask=None):
    """Return dict(TP, FP, FN, S, K, DTI) for prediction p in [0,1], boolean truth g.

    ``mask`` (bool) marks pixels excluded from evaluation (catalogue and the area
    outside the study footprint); both p and g are zeroed on it before every sum.
    """
    p = np.nan_to_num(np.asarray(p, dtype=np.float64), nan=0.0)
    g = np.asarray(g, dtype=bool)
    if mask is not None:
        mask = np.asarray(mask, dtype=bool)
        p = np.where(mask, 0.0, p)
        g = g & ~mask
    r = dti_result(p, g, radius=R_PX)
    return dict(TP=r.tp, FP=r.fp, FN=r.fn, S=r.mass, K=float(g.sum()),
                DTI=(r.tp / (r.tp + ALPHA * r.fp + BETA * r.fn) if (r.tp + ALPHA * r.fp + BETA * r.fn) > 0 else 0.0))


def dti(p, g, mask=None):
    """Scalar distance-weighted Tversky index (convenience wrapper)."""
    return components(p, g, mask)["DTI"]


def dti_bruteforce(p, g):
    """O(N*M) literal transcription of the published formulas; tiny grids only.

    Independent of the shift-based fast path above, so agreement between the two
    is evidence that the vectorised implementation is the published metric.
    """
    p = np.asarray(p, dtype=np.float64)
    g = np.asarray(g, dtype=bool)
    G = np.argwhere(g)
    X = np.argwhere(p > 0)
    TP = 0.0
    FN = 0.0
    for gy, gx in G:
        m = 0.0
        for xy, xx in X:
            d = float(np.hypot(gy - xy, gx - xx))
            if d <= R_PX:
                m = max(m, p[xy, xx] * float(kernel(d)))
        TP += m
        FN += 1.0 - m
    FP = 0.0
    for xy, xx in X:
        kk = max([float(kernel(float(np.hypot(gy - xy, gx - xx)))) for gy, gx in G] or [0.0])
        FP += p[xy, xx] * (1.0 - kk)
    den = TP + ALPHA * FP + BETA * FN
    return TP / den if den > 0 else 0.0
