"""Dempster-Shafer fusion of binary fault-dot emissions on the frame {F (fault), N (no fault)}.

References (verified links in docs/sources.md):
  Dempster (1967) Ann. Math. Statist. 38(2):325-339, doi:10.1214/aoms/1177698950
  Shafer (1976) A Mathematical Theory of Evidence, Princeton Univ. Press
  Yager (1987) Information Sciences 41:93-137 (conflict -> Theta)
  Denoeux (2008) Artificial Intelligence 172:234-264 (non-distinct evidence)
  Smets' pignistic transform BetP(F) = m(F) + m(Theta)/2 (decision rule)

Basic probability assignment for one source i with dot set D_i:
  s_i(x)     = k(d(x, D_i))            kernel support, 1 on a dot, 0 beyond 300 m
  m_i(F)     = r_i * s_i(x)
  m_i(N)     = r_i * (1 - s_i(x)) * a_i(x)    a_i = confidence that ABSENCE is informative
  m_i(Theta) = 1 - m_i(F) - m_i(N)
r_i is a Shafer reliability discount.  a_i(x) is larger where the source examined the
pixel and declined to place a dot (on its ridge backbone) and is 1 where the source
explicitly rejected the pixel (the dotted family's live-validated catalogue-flank prune).
"""
from __future__ import annotations

import numpy as np
from scipy import ndimage as ndi

from .metric import kernel


def bpa(dots, r, absence):
    s = kernel(ndi.distance_transform_edt(~dots)).astype(np.float32)
    f = (r * s).astype(np.float32)
    n = (r * (1.0 - s) * absence).astype(np.float32)
    u = (1.0 - f - n).astype(np.float32)
    return f, n, u, s


def dempster(m1, m2):
    """Dempster's rule (normalised).  Returns f, n, u, K (conflict before normalisation)."""
    f1, n1, u1 = m1; f2, n2, u2 = m2
    K = f1 * n2 + n1 * f2
    z = np.maximum(1.0 - K, 1e-9)
    f = (f1 * f2 + f1 * u2 + u1 * f2) / z
    n = (n1 * n2 + n1 * u2 + u1 * n2) / z
    u = (u1 * u2) / z
    return f.astype(np.float32), n.astype(np.float32), u.astype(np.float32), K.astype(np.float32)


def yager(m1, m2):
    """Yager's rule: conflict is moved to Theta instead of being normalised away."""
    f1, n1, u1 = m1; f2, n2, u2 = m2
    K = f1 * n2 + n1 * f2
    f = f1 * f2 + f1 * u2 + u1 * f2
    n = n1 * n2 + n1 * u2 + u1 * n2
    u = u1 * u2 + K
    return f, n, u, K


def pignistic(f, u):
    return f + 0.5 * u


def nms_select(score, cand, radius):
    """Greedy non-maximum suppression: visit candidates by descending score, keep a pixel
    only if no kept pixel lies within Euclidean distance < radius.  Deterministic
    (ties broken by raster order)."""
    ys, xs = np.nonzero(cand)
    order = np.lexsort((xs, ys, -score[ys, xs]))
    H, W = score.shape
    taken = np.zeros((H, W), bool)
    out = np.zeros((H, W), bool)
    R = int(np.ceil(radius))
    offs = [(dy, dx) for dy in range(-R, R + 1) for dx in range(-R, R + 1)
            if dy * dy + dx * dx < radius * radius]
    for i in order:
        y, x = ys[i], xs[i]
        if taken[y, x]:
            continue
        out[y, x] = True
        for dy, dx in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < H and 0 <= xx < W:
                taken[yy, xx] = True
    return out
