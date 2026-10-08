"""Historical H55 helper functions — FORENSIC ONLY; not a validated score model.

The former H55 construction combined dotted-family and tip/step-over evidence,
then priced additions using a live-anchor surrogate. That surrogate inferred
hidden truth and a per-dot bar through ``FPw = S - TPw``; the identity is not
general under the official metric. Its ``T = 5,209``, union score, break-even
bar, scenario bands, ceiling, and ``live-equivalent`` values are invalidated by
``docs/research/metric-identity-erratum-20261007.md``. They are historical
outputs, not private-label facts, score estimates, or promotion evidence.

The geometry-only ``greedy_priced_additions`` helper still accepts an arbitrary
caller-supplied coverage cutoff, but that cutoff has no organizer-score meaning.
``price_addition_path`` is guarded for explicit legacy-model opt-in and returns
forensic-only surrogate values. Neither helper establishes that a blend beats
a parent, that the surfaces are independent, or that Dempster-Shafer ignorance
is conflict. No H55 artifact is cleared to submit.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from scipy.ndimage import distance_transform_edt

from .live_model import OFFSETS, max_credit_field

PIXEL_M = 100.0
MIN_SEPARATION_M = 300.0
CATALOGUE_BUFFER_M = 200.0
DS_CONFLICT_VETO = 0.36  # a1*a2*(1+1-2*0) = 0.36 for alpha1=alpha2=0.6, binary inputs
CONDUIT_OVERRIDE_TIER = 3


@dataclass
class SelectionResult:
    """Everything the builder needs to write and audit one candidate."""

    emission: np.ndarray
    a2_rows: np.ndarray
    a2_gains: np.ndarray
    a1_rows: np.ndarray
    a1_scores: np.ndarray
    coverage: float
    trace: list[dict] = field(default_factory=list)
    diagnostics: dict = field(default_factory=dict)


def _gain_field(coverage_now: np.ndarray, weight: np.ndarray) -> np.ndarray:
    """Marginal eligible-backbone coverage gained by adding one dot at each cell."""
    height, width = weight.shape
    out = np.zeros((height, width), dtype=np.float32)
    for dy, dx, w in OFFSETS:
        r0, r1 = max(-dy, 0), min(height, height - dy)
        c0, c1 = max(-dx, 0), min(width, width - dx)
        if r0 >= r1 or c0 >= c1:
            continue
        sr0, sr1 = r0 + dy, r1 + dy
        sc0, sc1 = c0 + dx, c1 + dx
        out[r0:r1, c0:c1] += weight[sr0:sr1, sc0:sc1] * np.maximum(
            0.0, w - coverage_now[sr0:sr1, sc0:sc1])
    return out


def _apply_local(coverage_now: np.ndarray, weight: np.ndarray, gain: np.ndarray,
                 pool: np.ndarray, index: np.ndarray, row: int, col: int) -> None:
    """Update ``coverage_now`` and the compact ``gain`` vector after adding a dot."""
    height, width = weight.shape
    for dy, dx, w in OFFSETS:
        r, c = row - dy, col - dx
        if 0 <= r < height and 0 <= c < width and weight[r, c] > 0 and w > coverage_now[r, c]:
            coverage_now[r, c] = w
    r0, r1 = max(0, row - 6), min(height, row + 7)
    c0, c1 = max(0, col - 6), min(width, col + 7)
    sub = np.zeros((r1 - r0, c1 - c0), dtype=np.float32)
    for dy, dx, w in OFFSETS:
        sr0, sr1 = r0 + dy, r1 + dy
        sc0, sc1 = c0 + dx, c1 + dx
        kr0, kr1 = max(0, sr0), min(height, sr1)
        kc0, kc1 = max(0, sc0), min(width, sc1)
        if kr0 >= kr1 or kc0 >= kc1:
            continue
        sub[(kr0 - sr0):(kr1 - sr0), (kc0 - sc0):(kc1 - sc0)] += (
            weight[kr0:kr1, kc0:kc1] * np.maximum(0.0, w - coverage_now[kr0:kr1, kc0:kc1]))
    pr, pc = np.nonzero(pool[r0:r1, c0:c1])
    if pr.size:
        gain[index[r0 + pr, c0 + pc]] = sub[pr, pc]


def greedy_priced_additions(
    core: np.ndarray,
    pool: np.ndarray,
    target: np.ndarray,
    *,
    bar: float,
    max_add: int,
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    """Greedily add pool pixels whose marginal target coverage exceeds ``bar``.

    ``bar`` is a caller-supplied geometric cutoff in coverage units; this helper
    does not calibrate it to DTI or an organizer score. Historical H55 runs used
    an invalid live-model threshold, which must not be treated as a current gate.
    Returns ``(rows_cols, gains, trace)`` in selection order.
    """
    core = np.asarray(core, dtype=bool)
    pool = np.asarray(pool, dtype=bool) & ~core
    weight = np.asarray(target, dtype=bool).astype(np.float32)
    coverage_now = max_credit_field(core).astype(np.float32)
    rows, cols = np.nonzero(pool)
    if rows.size == 0:
        return np.zeros((0, 2), dtype=np.int32), np.zeros(0), []
    index = -np.ones(pool.shape, dtype=np.int32)
    index[rows, cols] = np.arange(rows.size, dtype=np.int32)
    gain = _gain_field(coverage_now, weight)[rows, cols].astype(np.float32)

    selected: list[tuple[int, int]] = []
    gains: list[float] = []
    trace: list[dict] = []
    # float64 accumulation of float32 gains: the per-gain rounding is ~1e-6 relative,
    # which propagates to <1e-7 relative on the total coverage and <1e-8 on DTI.
    running = float((coverage_now.astype(np.float64) * weight).sum())
    for _ in range(int(max_add)):
        j = int(np.argmax(gain))
        value = float(gain[j])
        if value < bar:
            break
        row, col = int(rows[j]), int(cols[j])
        selected.append((row, col))
        gains.append(value)
        gain[j] = -np.inf
        _apply_local(coverage_now, weight, gain, pool, index, row, col)
        running += float(value)  # exact up to float32 gain rounding: `value` IS the
        # marginal coverage of this dot, because coverage is a maximum over dots
        trace.append({"n": len(selected), "coverage": running, "gain": value})
    out = np.asarray(selected, dtype=np.int32) if selected else np.zeros((0, 2), dtype=np.int32)
    return out, np.asarray(gains, dtype=np.float64), trace


def price_addition_path(
    core: np.ndarray,
    pool: np.ndarray,
    target: np.ndarray,
    *,
    break_even_bar: float,
    max_add: int,
    model,
    extra_mass: int = 0,
    safety_factor: float = 1.0,
) -> dict:
    """Reproduce the retired H55 surrogate path for forensic comparison only.

    The caller must pass an explicitly opted-in historical ``ForwardModel``.
    ``break_even_bar`` and all modelled DTI values inherit the invalid
    ``FPw=S-TPw`` assumption; the returned argmax/robust prefixes are not
    organizer-score optima or candidate recommendations. Coverage accounting
    remains a geometric helper and is checked separately without any live bar.
    """
    if not getattr(model, "legacy_audit_only", False):
        raise RuntimeError("invalidated H55 pricing path; explicit forensic-only ForwardModel required")
    rows, gains, trace = greedy_priced_additions(
        core, pool, target, bar=break_even_bar, max_add=max_add)
    core = np.asarray(core, dtype=bool)
    base_emitted = int(core.sum()) + int(extra_mass)
    base_cov = trace[0]["coverage"] - trace[0]["gain"] if trace else float(
        (max_credit_field(core) * np.asarray(target, dtype=bool)).sum())
    path = [{"n": 0, "emitted": base_emitted, "coverage": base_cov,
             "dti_pred": model.dti(base_cov, base_emitted), "last_gain": None}]
    for point in trace:
        path.append({"n": point["n"], "emitted": base_emitted + point["n"],
                     "coverage": point["coverage"], "last_gain": point["gain"],
                     "dti_pred": model.dti(point["coverage"], base_emitted + point["n"])})
    best = max(path, key=lambda p: p["dti_pred"])
    # Historical robustness-first prefix; `safety_factor * break_even_bar` has no
    # current promotion meaning. Gains are not guaranteed monotone along a greedy
    # max-coverage path, so this reproduces the old first-violation rule only.
    robust_n = 0
    for value in gains:
        if value < safety_factor * break_even_bar:
            break
        robust_n += 1
    robust = path[robust_n] if robust_n else path[0]
    return {"validity_status": "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION",
            "invalidation_reason": "H55 live-model path depends on invalid FPw=S-TPw substitution.",
            "promotion_use": "NONE — historical surrogate outputs only.",
            "break_even_bar_coverage_units_invalidated": float(break_even_bar),
            "break_even_bar_coverage_units": float(break_even_bar),
            "safety_factor": float(safety_factor), "path": path,
            "argmax_prefix": best, "robust_prefix": robust, "robust_n": robust_n,
            "n_admitted_at_break_even": int(len(rows)),
            "rows": rows, "gains": gains}


def dart_throw(score: np.ndarray, allowed: np.ndarray, min_separation_px: float,
               max_points: int, tie_break: np.ndarray | None = None) -> np.ndarray:
    """Rank ``allowed`` cells by ``score`` and keep one per ``min_separation_px`` disk.

    Deterministic: ties are broken by ``tie_break`` then by row-major index, so the
    output does not depend on any random seed.
    """
    score = np.asarray(score, dtype=np.float64)
    allowed = np.asarray(allowed, dtype=bool)
    rows, cols = np.nonzero(allowed)
    if rows.size == 0:
        return np.zeros((0, 2), dtype=np.int32)
    key = score[rows, cols]
    if tie_break is not None:
        secondary = np.asarray(tie_break, dtype=np.float64)[rows, cols]
    else:
        secondary = -(rows.astype(np.float64) * score.shape[1] + cols.astype(np.float64))
    order = np.lexsort((secondary, -key))
    radius = float(min_separation_px)
    half = int(np.ceil(radius)) + 1
    taken = np.zeros(score.shape, dtype=bool)
    out: list[tuple[int, int]] = []
    height, width = score.shape
    for j in order:
        r, c = int(rows[j]), int(cols[j])
        if taken[r, c]:
            continue
        out.append((r, c))
        if len(out) >= max_points:
            break
        r0, r1 = max(0, r - half), min(height, r + half + 1)
        c0, c1 = max(0, c - half), min(width, c + half + 1)
        rr, cc = np.mgrid[r0:r1, c0:c1]
        disk = ((rr - r) ** 2 + (cc - c) ** 2) <= radius * radius
        taken[r0:r1, c0:c1] |= disk
    return np.asarray(out, dtype=np.int32)


def distance_to_points_m(points_rows_cols: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    """Euclidean distance in metres from every cell to the nearest listed point."""
    mask = np.zeros(shape, dtype=bool)
    pts = np.asarray(points_rows_cols, dtype=np.int64).reshape(-1, 2)
    if pts.size:
        mask[pts[:, 0], pts[:, 1]] = True
    return distance_transform_edt(~mask, sampling=(PIXEL_M, PIXEL_M))


def conduit_anchors(
    tier: np.ndarray,
    score: np.ndarray,
    *,
    emitted: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    catalogue_distance_m: np.ndarray,
    conflict: np.ndarray,
    min_tier: int = 2,
    min_separation_m: float = MIN_SEPARATION_M,
    buffer_m: float = CATALOGUE_BUFFER_M,
    max_points: int = 5000,
) -> tuple[np.ndarray, np.ndarray, dict]:
    """Tiered hydrothermal-conduit anchors, DS-conflict vetoed and dart-thrown.

    Returns ``(rows_cols, scores, audit)``.
    """
    emitted = np.asarray(emitted, dtype=bool)
    distance_m = distance_to_points_m(np.argwhere(emitted), emitted.shape)
    in_tier = tier >= min_tier
    eligible = (in_tier & np.asarray(footprint, dtype=bool) & ~np.asarray(catalogue, dtype=bool)
                & ~emitted & (catalogue_distance_m > buffer_m) & (distance_m > min_separation_m))
    vetoed = eligible & (conflict >= DS_CONFLICT_VETO - 1e-9) & (tier < CONDUIT_OVERRIDE_TIER)
    allowed = eligible & ~vetoed
    pts = dart_throw(score, allowed, min_separation_m / PIXEL_M, max_points, tie_break=tier)
    audit = {
        "min_tier": min_tier,
        "tier_cells_total": int(in_tier.sum()),
        "eligible_after_masks": int(eligible.sum()),
        "vetoed_by_max_ds_conflict": int(vetoed.sum()),
        "allowed": int(allowed.sum()),
        "selected_after_dart_throw": int(len(pts)),
        "min_separation_m": min_separation_m,
        "catalogue_buffer_m": buffer_m,
        "ds_conflict_veto_threshold": DS_CONFLICT_VETO,
        "conduit_override_tier": CONDUIT_OVERRIDE_TIER,
        "max_points": max_points,
    }
    if len(pts):
        audit["selected_tier_counts"] = {str(int(t)): int((tier[pts[:, 0], pts[:, 1]] == t).sum())
                                         for t in sorted(set(int(x) for x in tier[pts[:, 0], pts[:, 1]]))}
        audit["selected_score_min"] = float(score[pts[:, 0], pts[:, 1]].min())
        audit["selected_score_max"] = float(score[pts[:, 0], pts[:, 1]].max())
    return pts, (score[pts[:, 0], pts[:, 1]] if len(pts) else np.zeros(0)), audit
