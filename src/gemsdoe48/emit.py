"""Covering-optimal re-emission.

The lever, and why it is truth-free
-----------------------------------
For a truth pixel `g` the metric takes `max over emitted pixels d of k(d(g, d))`.
So the credit a pixel earns is set by the **largest gap** in the emission near it,
not by the number of dots.  Spacing-tuned thinning as practised in the sibling
repositories (`dot_thin`, a geodesic Poisson-disk / dart-throwing operator)
constrains the *minimum* distance between dots; it does **not** constrain the
largest distance from a point to the nearest dot, which is the quantity the
metric actually pays for.

Controlling the covering radius instead gives a theorem, not a proxy:

    Fejes Toth (1940s; see Conway & Sloane, *Sphere Packings, Lattices and
    Groups*, 3rd ed., ch. 2): the hexagonal lattice is the optimal covering of
    the plane.  Its covering density is 2*pi/(3*sqrt(3)) = 1.2092, versus
    pi/2 = 1.5708 for the square lattice.  Ratio 0.7698.

Concretely, for a covering radius `rho` (the largest distance from any pixel of
the support to its nearest dot):

    square lattice   spacing s_q = rho*sqrt(2)      density 1/s_q^2  = 0.500 /rho^2
    hexagonal lattice spacing s_h = rho*sqrt(3)     density 2/(sqrt(3) s_h^2)
                                                            = 0.3849 /rho^2

so the hexagonal arrangement needs **23.0 % fewer dots for the same guaranteed
coverage**.  That saving is paid at 0.2 per unit of emitted mass in the
denominator and costs the *guaranteed* part of `TPw` nothing: every support pixel
still has k >= 1 - rho/300m.

`tests/test_emit.py` verifies the density constants numerically, and
`evidence/cover_sweep.json` reports the measured (N, covering radius, TPw)
frontier against the shipped artifacts on three independent truth layers.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

HEX_COVERING_DENSITY = 2.0 * np.pi / (3.0 * np.sqrt(3.0))  # 1.2091996
SQ_COVERING_DENSITY = np.pi / 2.0  # 1.5707963
HEX_SAVING = 1.0 - HEX_COVERING_DENSITY / SQ_COVERING_DENSITY  # 0.2302


def distance_to_mask(mask: np.ndarray) -> np.ndarray:
    """Exact Euclidean distance (in pixels) from every pixel to the nearest True."""
    return ndimage.distance_transform_edt(~np.asarray(mask, dtype=bool))


def covering_radius(points_mask: np.ndarray, support_mask: np.ndarray) -> float:
    """max over support pixels of the distance to the nearest point."""
    d = distance_to_mask(points_mask)
    sel = np.asarray(support_mask, dtype=bool)
    if not sel.any():
        return float("nan")
    return float(d[sel].max())


def coverage_profile(points_mask: np.ndarray, support_mask: np.ndarray) -> dict:
    d = distance_to_mask(points_mask)
    sel = np.asarray(support_mask, dtype=bool)
    v = d[sel]
    if v.size == 0:
        return {"n": 0}
    return {
        "n": int(v.size),
        "max": float(v.max()),
        "mean": float(v.mean()),
        "p50": float(np.percentile(v, 50)),
        "p90": float(np.percentile(v, 90)),
        "p99": float(np.percentile(v, 99)),
        "share_above_1px": float((v > 1.0).mean()),
        "share_above_1p5px": float((v > 1.5).mean()),
    }


def hex_lattice(shape: tuple[int, int], spacing: float, phase: tuple[float, float] = (0.0, 0.0)):
    """Boolean mask of a triangular (hexagonal) lattice with nearest-neighbour spacing."""
    h, w = shape
    dy = spacing * np.sqrt(3.0) / 2.0
    rows = np.arange(0.0, h, dy)
    out = np.zeros(shape, dtype=bool)
    for i, y in enumerate(rows):
        x0 = phase[0] + (spacing / 2.0 if (i % 2) else 0.0)
        xs = np.arange(x0 + phase[1], w, spacing)
        if xs.size == 0:
            continue
        r = int(round(y))
        if 0 <= r < h:
            cols = np.round(xs).astype(int)
            cols = cols[(cols >= 0) & (cols < w)]
            out[r, cols] = True
    return out


def square_lattice(shape: tuple[int, int], spacing: float):
    h, w = shape
    out = np.zeros(shape, dtype=bool)
    rows = np.arange(0, h, spacing)
    cols = np.arange(0, w, spacing)
    rr, cc = np.meshgrid(rows, cols, indexing="ij")
    out[rr.astype(int), cc.astype(int)] = True
    return out


def best_phase_hex(shape, spacing: float, support: np.ndarray, n_phase: int = 6) -> np.ndarray:
    """Pick the hexagonal phase whose dots best cover `support` (cheapest surrogate:
    largest share of support within `spacing/sqrt(3)`)."""
    best, best_score, best_mask = None, -1.0, None
    for i in range(n_phase):
        for j in range(n_phase):
            m = hex_lattice(shape, spacing, (spacing * i / n_phase, spacing * j / n_phase))
            m = m & dilate_mask(support, int(np.ceil(spacing)))
            if m.sum() == 0:
                continue
            d = distance_to_mask(m)[support]
            score = float((d <= spacing / np.sqrt(3.0) + 1e-9).mean())
            if score > best_score:
                best, best_score, best_mask = (i, j), score, m
    return best_mask if best_mask is not None else np.zeros(shape, dtype=bool)


def dilate_mask(mask: np.ndarray, radius: int) -> np.ndarray:
    """City-block (Manhattan) dilation by `radius` px: {|dr| + |dc| <= radius}.

    Four shifted ORs per step, so the footprint is the L1 ball, NOT a square and
    NOT an exact disk.  It coincides with `dilate_disk` for radius <= 2 and is
    strictly *contained* in the Euclidean disk from radius 3 (the disk gains 4
    extra cells at r = 3, 8 at r = 4, 20 at r = 5); see
    tests/test_emit.py::TestCoverageHelpers.  Use this for corridor construction,
    where the difference is immaterial and the tighter ball is the safe direction,
    and `dilate_disk` whenever the result is meant to represent the metric's
    Euclidean 300 m reach.
    """
    out = np.asarray(mask, dtype=bool).copy()
    for _ in range(int(radius)):
        cur = out
        out = cur | _shift_bool(cur, 1, 0) | _shift_bool(cur, -1, 0) | _shift_bool(cur, 0, 1) | _shift_bool(cur, 0, -1)
    return out


def erode_mask(mask: np.ndarray, radius: int) -> np.ndarray:
    if radius <= 0:
        return mask.copy()
    return ndimage.binary_erosion(mask, iterations=radius)


_DISK_OFFSETS: dict[float, list[tuple[int, int]]] = {}


def disk_offsets(radius: float) -> list[tuple[int, int]]:
    """Integer offsets (dr, dc) with sqrt(dr^2 + dc^2) <= radius.  Cached."""
    key = round(float(radius), 6)
    if key in _DISK_OFFSETS:
        return _DISK_OFFSETS[key]
    n = int(np.ceil(key))
    offs = [
        (dr, dc)
        for dr in range(-n, n + 1)
        for dc in range(-n, n + 1)
        if np.hypot(dr, dc) <= key + 1e-12
    ]
    _DISK_OFFSETS[key] = offs
    return offs


def _shift_bool(a: np.ndarray, dr: int, dc: int) -> np.ndarray:
    out = np.zeros_like(a)
    h, w = a.shape
    r0, r1 = max(dr, 0), min(h, h + dr)
    c0, c1 = max(dc, 0), min(w, w + dc)
    if r0 < r1 and c0 < c1:
        out[r0:r1, c0:c1] = a[r0 - dr : r1 - dr, c0 - dc : c1 - dc]
    return out


def dilate_disk(mask: np.ndarray, radius: float) -> np.ndarray:
    """Exact Euclidean-disk dilation by `radius` px, via shifted ORs.

    Exact, not approximate: a pixel is within `radius` of a True pixel iff one of
    the integer offsets with hypot(dr, dc) <= radius lands on a True pixel.  Cost
    is len(offsets) boolean ORs on the full grid (~25 for radius 3), which is about
    two orders of magnitude cheaper than `scipy.ndimage.binary_dilation` here.
    """
    if radius <= 0:
        return mask.copy()
    out = mask.copy()
    for dr, dc in disk_offsets(radius):
        if dr == 0 and dc == 0:
            continue
        out |= _shift_bool(mask, dr, dc)
    return out


def covered_within(points: np.ndarray, radius: float) -> np.ndarray:
    """Pixels within `radius` px of some point (exact Euclidean disk)."""
    return dilate_disk(points, radius)


def greedy_fill(
    points: np.ndarray, support: np.ndarray, radius: float, *, max_passes: int = 40
) -> np.ndarray:
    """Add points until every support pixel is within `radius` of some point.

    Batch form: each pass adds one point per connected component of the residual
    uncovered set (located at the component's centroid), which closes a whole
    frontier per pass instead of a single gap, so a handful of passes suffices
    on ribbon-shaped supports.
    """
    pts = points.copy()
    support = np.asarray(support, dtype=bool)
    st = np.ones((3, 3), dtype=int)
    for _ in range(int(max_passes)):
        unc = support & ~covered_within(pts, radius)
        if not unc.any():
            break
        lab, n = ndimage.label(unc, structure=st)
        if n == 0:
            break
        for y, x in component_centroids(lab, n):
            pts[int(round(y)), int(round(x))] = True
    return pts


def component_centroids(lab: np.ndarray, n: int) -> list[tuple[float, float]]:
    """Centroids of labels 1..n, computed with bincount (no full-array moments)."""
    if n <= 0:
        return []
    idx = lab.ravel()
    sel = idx > 0
    rows, cols = np.divmod(np.flatnonzero(sel), lab.shape[1])
    labels_flat = idx[sel]
    counts = np.bincount(labels_flat, minlength=n + 1)
    sy = np.bincount(labels_flat, weights=rows, minlength=n + 1)
    sx = np.bincount(labels_flat, weights=cols, minlength=n + 1)
    out = []
    for k in range(1, n + 1):
        if counts[k]:
            out.append((sy[k] / counts[k], sx[k] / counts[k]))
    return out


def prune_redundant_batched(
    points: np.ndarray, support: np.ndarray, radius: float, *, rounds: int = 3
) -> np.ndarray:
    """Batched reverse-delete: try removing every other point at once, then restore
    every removed point that was holding down an uncovered pixel.

    O(rounds) full-grid coverage tests instead of O(number of points) -- the
    earlier per-point reverse delete recomputed a distance transform per point and
    did not finish in 28 minutes on this grid.
    """
    pts = points.copy()
    support = np.asarray(support, dtype=bool)
    for r_i in range(rounds):
        ys, xs = np.nonzero(pts)
        if ys.size == 0:
            break
        sel = np.arange(ys.size)[(r_i % 2) :: 2]
        if sel.size == 0:
            break
        removed = np.zeros_like(pts)
        removed[ys[sel], xs[sel]] = True
        trial = pts & ~removed
        unc = support & ~covered_within(trial, radius)
        if not unc.any():
            pts = trial
            continue
        # restore exactly the removed points that still serve an uncovered pixel
        near = dilate_disk(unc, radius)
        pts = trial | (removed & near)
    return pts


def cover_region(
    support: np.ndarray,
    spacing: float,
    *,
    keep_radius: int | None = None,
    prune: bool = True,
    phase: tuple[float, float] = (0.0, 0.0),
    max_fill_passes: int = 6,
) -> dict:
    """Hexagonal-lattice covering of `support` at covering radius `spacing/sqrt(3)`.

    The lattice supplies a near-optimal covering; `greedy_fill` closes the few
    residual gaps at the ends and corners of the ribbons; the batched pruner then
    removes the lattice sites that turned out to be redundant.  The guarantee
    `k >= 1 - rho / 300 m` for every support pixel therefore holds for the final
    point set, and the *measured* radius is recomputed exactly on the real grid
    with `scipy.ndimage.distance_transform_edt`.
    """
    target_radius = spacing / np.sqrt(3.0)
    if keep_radius is None:
        keep_radius = int(np.ceil(target_radius))
    lat = hex_lattice(support.shape, spacing, phase)
    band = dilate_mask(support, keep_radius)
    pts = lat & band
    pts = greedy_fill(pts, support, target_radius, max_passes=max_fill_passes)
    if prune:
        pts = prune_redundant_batched(pts, support, target_radius)
    return {
        "points": pts,
        "n": int(pts.sum()),
        "target_radius": float(target_radius),
        "measured_radius": covering_radius(pts, support),
        "spacing": float(spacing),
        "keep_radius": int(keep_radius),
    }
