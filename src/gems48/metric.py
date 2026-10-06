"""Exact distance-weighted Tversky index (DTI) of the DOE GEMS Prize.

Transcribed from the official problem description
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric

    k(d)  = max(1 - d/R, 0),  R = 300 m = 3 px at 100 m
    TP_w  = sum_{g in G} max_{x: d(x,g) <= R} p(x) k(d(x,g))
    FP_w  = sum_{x: p(x) > 0} p(x) [1 - max_{g in G} k(d(x,g))]
    FN_w  = sum_{g in G} [1 - max_{x: d(x,g) <= R} p(x) k(d(x,g))]
    DTI   = TP_w / (TP_w + alpha FP_w + beta FN_w + eps),  alpha = 0.2, beta = 0.8

Masking: DrivenData staff stated (community thread 11516) that known USGS/INGENIOUS
pixels are excluded from evaluation.  We implement that by zeroing both p and g on the
mask before every sum (``mask`` argument).  This is a modelling assumption that is
consistent with the 0.1563 == 0.1563 natural experiment recorded in GEMSDOE47.
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

ALPHA = 0.2
BETA = 0.8
R_PX = 3.0  # 300 m / 100 m

# the 25 integer offsets with k > 0 (dy^2 + dx^2 < 9)
OFFSETS = [(dy, dx, 1.0 - np.hypot(dy, dx) / R_PX)
           for dy in range(-2, 3) for dx in range(-2, 3)
           if np.hypot(dy, dx) < R_PX]


def kernel(d):
    return np.clip(1.0 - np.asarray(d, dtype=np.float64) / R_PX, 0.0, None)


def _shift(a, dy, dx):
    """out[y, x] = a[y + dy, x + dx] with zero fill."""
    out = np.zeros_like(a)
    H, W = a.shape
    ys = slice(max(0, -dy), min(H, H - dy)); yd = slice(max(0, dy), min(H, H + dy))
    xs = slice(max(0, -dx), min(W, W - dx)); xd = slice(max(0, dx), min(W, W + dx))
    out[ys, xs] = a[yd, xd]
    return out


def components(p, g, mask=None):
    """Return dict(TP, FP, FN, S, K, DTI) for prediction p in [0,1] and boolean truth g.

    ``mask`` (bool) marks pixels excluded from evaluation (catalogue + outside footprint).
    """
    p = np.nan_to_num(np.asarray(p, dtype=np.float64), nan=0.0)
    g = np.asarray(g, dtype=bool)
    if mask is not None:
        p = np.where(mask, 0.0, p)
        g = g & ~mask
    # best kernel-weighted prediction reaching each pixel: max over offsets p(x+o) k(o)
    best = np.zeros_like(p)
    for dy, dx, k in OFFSETS:
        np.maximum(best, k * _shift(p, dy, dx), out=best)
    TP = float(best[g].sum())
    K = float(g.sum())
    FN = K - TP
    if g.any():
        dG = ndi.distance_transform_edt(~g)
        kap = kernel(dG)
    else:
        kap = np.zeros_like(p)
    pos = p > 0
    FP = float((p[pos] * (1.0 - kap[pos])).sum())
    S = float(p.sum())
    den = TP + ALPHA * FP + BETA * FN
    return dict(TP=TP, FP=FP, FN=FN, S=S, K=K, DTI=(TP / den) if den > 0 else 0.0)


def dti(p, g, mask=None):
    return components(p, g, mask)["DTI"]


def dti_bruteforce(p, g):
    """O(N*M) literal transcription, for tests on tiny grids only."""
    p = np.asarray(p, float); g = np.asarray(g, bool)
    G = np.argwhere(g); X = np.argwhere(p > 0)
    TP = FN = 0.0
    for gy, gx in G:
        m = 0.0
        for xy, xx in X:
            d = np.hypot(gy - xy, gx - xx)
            if d <= R_PX:
                m = max(m, p[xy, xx] * float(kernel(d)))
        TP += m; FN += 1 - m
    FP = 0.0
    for xy, xx in X:
        kk = max([float(kernel(np.hypot(gy - xy, gx - xx))) for gy, gx in G] or [0.0])
        FP += p[xy, xx] * (1 - kk)
    return TP / (TP + ALPHA * FP + BETA * FN)
