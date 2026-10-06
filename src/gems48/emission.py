"""Mass-budgeted, spatially balanced emission from a continuous score field.

Why spatial balance and not simply "the top N cells"
----------------------------------------------------
The published metric takes, for each truth pixel, the MAXIMUM over the kernel
support: ``TP_w = sum_g max_{x: d(x,g) <= R} p(x) k(d(x,g))``.  Two admitted
cells that lie one cell apart on the same structure therefore compete for the
same truth pixels instead of covering twice as many.  Ranking alone clusters,
and clustering wastes mass; the live record of this campaign agrees (a
Poisson-disk spacing of d = 2.8 px beat d = 1.5 px on the leaderboard).

``poisson_sample`` walks the candidates in descending score and admits a cell
only if no already-admitted cell lies inside the minimum separation, which is a
greedy maximal Poisson-disk (farthest-point style) sample of the score field.
"""
from __future__ import annotations

import numpy as np


def poisson_sample(score: np.ndarray, spacing: float, budget: int, allowed: np.ndarray) -> np.ndarray:
    """Greedy descending-score sample under a minimum-separation constraint.

    Parameters
    ----------
    score   : ranking field (higher = better).
    spacing : minimum Euclidean separation, in cells, between admitted cells.
    budget  : maximum number of cells to admit.
    allowed : boolean mask of candidates (also used to restrict to the footprint).

    Returns a boolean array of the same shape as ``score``.
    """
    score = np.asarray(score, dtype=np.float64)
    allowed = np.asarray(allowed, dtype=bool)
    if score.shape != allowed.shape:
        raise ValueError("score and allowed must share a shape")
    if spacing <= 0:
        raise ValueError("spacing must be positive")
    if budget < 0:
        raise ValueError("budget must be non-negative")

    h, w = score.shape
    blocked = np.zeros(score.size, bool)
    out = np.zeros(score.size, bool)
    idx = np.flatnonzero(allowed.ravel())
    if idx.size == 0 or budget == 0:
        return out.reshape(score.shape)
    order = idx[np.argsort(-score.ravel()[idx], kind="stable")]
    r = int(np.ceil(spacing))
    offs = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1)
            if dy * dy + dx * dx <= spacing * spacing]
    taken = 0
    for flat in order:
        if taken >= budget:
            break
        if blocked[flat]:
            continue
        y, x = divmod(int(flat), w)
        out[flat] = True
        taken += 1
        for dy, dx in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                blocked[yy * w + xx] = True
    return out.reshape(score.shape)


def soft_emission(score: np.ndarray, budget: float, allowed: np.ndarray,
                  iterations: int = 80) -> np.ndarray:
    """``p = min(1, score/tau)`` on cells whose score clears tau, total mass = budget.

    Kept for completeness and documented as *not* used for the deliverable: on
    the admissible support the optimal value is 1, because credit ``p*k`` and
    cost ``alpha*p`` are both linear in p while credit per truth pixel is capped.
    """
    score = np.asarray(score, dtype=np.float64)
    allowed = np.asarray(allowed, dtype=bool)
    out = np.zeros(score.size, dtype=np.float32)
    idx = np.flatnonzero(allowed.ravel())
    if idx.size == 0:
        return out.reshape(score.shape)
    v = score.ravel()[idx]
    lo, hi = 1e-9, float(v.max()) or 1.0
    for _ in range(iterations):
        mid = 0.5 * (lo + hi)
        mass = float(np.minimum(1.0, np.where(v > mid, v / mid, 0.0)).sum())
        if mass > budget:
            lo = mid
        else:
            hi = mid
    tau = max(0.5 * (lo + hi), 1e-9)
    out[idx] = np.minimum(1.0, np.where(v > tau, v / tau, 0.0)).astype(np.float32)
    return out.reshape(score.shape)
