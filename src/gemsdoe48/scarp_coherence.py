"""Strike-coherent persistence for the regional H52-1 100 m scarp product.

This is a second-stage raster diagnostic, not a replacement for the native-DEM
scarp detector. It uses the single best strike retained for each 100 m cell and
therefore cannot recover sub-cell strike mixtures or remeasure the source profile.
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

STRIKE_BIN_DEGREES = 15.0
N_STRIKE_BINS = 12


def circular_strike_difference(a: np.ndarray | float, b: float) -> np.ndarray:
    """Smallest absolute difference between unoriented strikes (degrees modulo 180)."""
    values = np.asarray(a, dtype=np.float64)
    return np.abs((values - float(b) + 90.0) % 180.0 - 90.0)


@lru_cache(maxsize=24)
def strike_sample_offsets(
    strike_deg: int,
    pixel_size_m: int = 100,
    cross_track_max_m: int = 75,
    max_grid_offset: int = 3,
) -> tuple[tuple[int, int], ...]:
    """Return four distinct nearest grid samples at ±100 m and ±200 m along strike.

    Strike is clockwise from north and unoriented (0..180 degrees). ``dr`` is
    positive southward and ``dc`` eastward. For each side/target, select the
    unused integer offset with cross-track distance <=75 m that lexicographically
    minimizes along-distance error, absolute cross-track distance, Euclidean
    distance, then ``dr`` and ``dc``. The small-grid search is deterministic.
    """
    if pixel_size_m <= 0 or cross_track_max_m < 0 or max_grid_offset < 1:
        raise ValueError("invalid pixel size or search bounds")
    bearing = float(strike_deg) % 180.0
    radians = np.deg2rad(bearing)
    sin_b, cos_b = float(np.sin(radians)), float(np.cos(radians))
    candidates: list[tuple[int, int, float, float]] = []
    for dr in range(-max_grid_offset, max_grid_offset + 1):
        for dc in range(-max_grid_offset, max_grid_offset + 1):
            if dr == 0 and dc == 0:
                continue
            east_m = dc * pixel_size_m
            north_m = -dr * pixel_size_m
            along_m = east_m * sin_b + north_m * cos_b
            cross_m = east_m * cos_b - north_m * sin_b
            if abs(cross_m) <= cross_track_max_m + 1e-9:
                candidates.append((dr, dc, along_m, cross_m))

    chosen: list[tuple[int, int]] = []
    for side in (-1, 1):
        used: set[tuple[int, int]] = set()
        for target_m in (100, 200):
            options = [
                item for item in candidates
                if side * item[2] > 0 and (item[0], item[1]) not in used
            ]
            if not options:
                raise ValueError(
                    f"no grid offset for strike={bearing:g}, side={side}, target={target_m} m"
                )
            best = min(
                options,
                key=lambda item: (
                    abs(abs(item[2]) - target_m),
                    abs(item[3]),
                    float(np.hypot(item[0], item[1])),
                    item[0],
                    item[1],
                ),
            )
            offset = (best[0], best[1])
            used.add(offset)
            chosen.append(offset)
    if len(set(chosen)) != 4:
        raise AssertionError(f"strike offsets are not four distinct samples: {chosen}")
    return tuple(chosen)


def _sample_neighbor(values: np.ndarray, dr: int, dc: int) -> np.ndarray:
    """At output cell (r,c), read input cell (r+dr,c+dc), filling outside with 0."""
    height, width = values.shape
    out = np.zeros(values.shape, dtype=values.dtype)
    r0, r1 = max(0, -dr), min(height, height - dr)
    c0, c1 = max(0, -dc), min(width, width - dc)
    if r0 < r1 and c0 < c1:
        out[r0:r1, c0:c1] = values[r0 + dr:r1 + dr, c0 + dc:c1 + dc]
    return out


def strike_coherent_scarp_score(
    height_m: np.ndarray,
    strike_deg: np.ndarray,
    cover: np.ndarray,
    *,
    min_height_m: float = 0.30,
    min_cover: float = 0.90,
    strike_tolerance_deg: float = 15.0,
    min_supported_samples: int = 4,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Compute H53-A's coherent-cell mask, support count, and ranking score.

    The five samples are the center and four deterministic nearest integer-grid
    offsets from :func:`strike_sample_offsets`. Neighbors must independently meet
    the height/cover criteria and agree with the center bin within the specified
    unoriented strike tolerance. A center is accepted only when it and at least
    ``min_supported_samples - 1`` neighbors meet the rule. Returned score is
    ``height_m * support_count / 5`` on accepted centers and zero elsewhere.
    """
    h = np.asarray(height_m, dtype=np.float32)
    strike = np.asarray(strike_deg, dtype=np.float32)
    cover_values = np.asarray(cover, dtype=np.float32)
    if h.ndim != 2 or strike.shape != h.shape or cover_values.shape != h.shape:
        raise ValueError("height, strike, and cover must be same-shaped 2-D arrays")
    if not np.isfinite(min_height_m) or min_height_m < 0:
        raise ValueError("min_height_m must be finite and nonnegative")
    if not np.isfinite(min_cover) or not 0.0 <= min_cover <= 1.0:
        raise ValueError("min_cover must be in [0,1]")
    if not np.isfinite(strike_tolerance_deg) or not 0.0 <= strike_tolerance_deg <= 90.0:
        raise ValueError("strike_tolerance_deg must be in [0,90]")
    if not 1 <= min_supported_samples <= 5:
        raise ValueError("min_supported_samples must be in [1,5]")

    eligible = (
        np.isfinite(h)
        & np.isfinite(strike)
        & np.isfinite(cover_values)
        & (h >= min_height_m)
        & (cover_values >= min_cover)
    )
    # Stored `strike_at` values are 15-degree bins; quantize defensively to the
    # nearest bin and wrap 180 degrees to 0 for an unoriented line.
    bins = np.zeros(h.shape, dtype=np.uint8)
    bins[eligible] = (
        np.rint(np.mod(strike[eligible], 180.0) / STRIKE_BIN_DEGREES)
        .astype(np.int16)
        % N_STRIKE_BINS
    ).astype(np.uint8)

    coherent = np.zeros(h.shape, dtype=bool)
    support_count = np.zeros(h.shape, dtype=np.uint8)
    score = np.zeros(h.shape, dtype=np.float32)
    for bin_index in range(N_STRIKE_BINS):
        center_strike = bin_index * STRIKE_BIN_DEGREES
        center = eligible & (bins == bin_index)
        if not center.any():
            continue
        compatible = eligible & (
            circular_strike_difference(strike, center_strike)
            <= strike_tolerance_deg + 1e-6
        )
        count = center.astype(np.uint8)
        for dr, dc in strike_sample_offsets(int(center_strike)):
            count += _sample_neighbor(compatible, dr, dc).astype(np.uint8)
        accepted = center & (count >= min_supported_samples)
        coherent[accepted] = True
        support_count[accepted] = count[accepted]
        score[accepted] = h[accepted] * (count[accepted].astype(np.float32) / 5.0)

    return coherent, support_count, score
