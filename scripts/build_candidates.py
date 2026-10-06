#!/usr/bin/env python3
"""Build Dempster-Shafer fused candidates and screen them on the blocked proxy.

Outputs ``docs/data/h49-candidate-screen.json``.  Every number is tagged
[MEASURED] (computed here), [ANCHOR] (owner-reported leaderboard score used as
an input) or [MODEL] (stated assumption, always swept for sensitivity).
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.evidence import (  # noqa: E402
    combine_dempster,
    combine_yager,
    discounted_binary_mass,
    kernel_support,
    pignistic,
)
from gems48.metric import ALPHA, BETA, credit_per_dot, dti_result as dti  # noqa: E402

DOTTED = ROOT / "data/raw/dotted.tif"
TIP = ROOT / "data/raw/tip.tif"
TEMPLATE = ROOT / "data/raw/sample_submission.tif"
LABELS = ROOT / "data/raw/labels.tif"
SGMC = ROOT / "data/raw/external/derived_sgmc_faults_100m_u8.tif"

# Preregistered reliability discounts.  r_dotted = 0.90 (the stronger parent).
# r_tip is set from the *measured* live credit-efficiency ratio of the two
# parents (weighted TP per emitted dot: 0.13446 vs 0.11988) -> 0.90 * 0.8915.
R_DOTTED = 0.90
EFFICIENCY_RATIO = 0.11987588720357811 / 0.13446190223260976
R_TIP = 0.90 * EFFICIENCY_RATIO

NBLOCK = 4  # 4x4 = 16 spatial blocks


def rd(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        return s.read(1)


def top_n(score: np.ndarray, n: int, allowed: np.ndarray) -> np.ndarray:
    """Binary mask of the n highest-scoring allowed cells (deterministic)."""
    idx = np.flatnonzero(allowed)
    vals = score.ravel()[idx]
    if n >= idx.size:
        sel = idx
    else:
        # partition is O(n); ties resolved by the lowest flat index for reproducibility
        order = np.argpartition(-vals, n - 1)[:n]
        sel = idx[np.sort(order)]
    out = np.zeros(score.size, bool)
    out[sel] = True
    return out.reshape(score.shape)


def soft_emission(score: np.ndarray, budget: float, allowed: np.ndarray) -> np.ndarray:
    """p = min(1, score/tau) with tau solved so that sum(p) == budget."""
    idx = np.flatnonzero(allowed)
    v = score.ravel()[idx].astype(np.float64)
    if v.size == 0:
        return np.zeros(score.shape, dtype=np.float32)
    target = float(budget)
    lo, hi = 1e-9, float(v.max())
    for _ in range(80):
        mid = 0.5 * (lo + hi)
        mass = float(np.minimum(1.0, v / mid).sum())
        if mass > target:
            lo = mid
        else:
            hi = mid
    tau = max(0.5 * (lo + hi), 1e-9)
    out = np.zeros(score.size, dtype=np.float32)
    out[idx] = np.minimum(1.0, v / tau).astype(np.float32)
    return out.reshape(score.shape)


def blocks(shape, n=NBLOCK):
    h, w = shape
    out = []
    for i in range(n):
        for j in range(n):
            out.append((slice(i * h // n, (i + 1) * h // n), slice(j * w // n, (j + 1) * w // n)))
    return out


def main() -> None:
    dotted = rd(DOTTED) > 0
    tip = rd(TIP) > 0
    labels = rd(LABELS) > 0
    sgmc = rd(SGMC) > 0
    template = rd(TEMPLATE)
    footprint = np.isfinite(template)

    inter = dotted & tip
    union = dotted | tip

    # ---------------------------------------------------------------- evidence
    sup_d = kernel_support(dotted.astype(np.float64))
    sup_t = kernel_support(tip.astype(np.float64))
    a = discounted_binary_mass(sup_d, R_DOTTED)
    b = discounted_binary_mass(sup_t, R_TIP)
    bel_y, dis_y, unassigned, conflict = combine_yager(a, b)
    bel_dem, dis_dem, _ = combine_dempster(a, b)
    betp = pignistic(bel_y, dis_y)

    # ------------------------------------------------------------ proxy truths
    from scipy.ndimage import distance_transform_edt
    d_cat = distance_transform_edt(~labels)
    truths = {
        "sgmc_off300m": sgmc & footprint & (d_cat >= 3.0),
        "sgmc_off100m": sgmc & footprint & (d_cat >= 1.0),
    }

    allowed = footprint & (betp > 0)
    cand_sets = {
        "dotted_parent": dotted.astype(np.float32),
        "tip_parent": tip.astype(np.float32),
        "union_binary": union.astype(np.float32),
        "intersection": inter.astype(np.float32),
        "naive_mean": (0.5 * (dotted + tip)).astype(np.float32),
        "weighted_mean_64_36": (0.64 * dotted + 0.36 * tip).astype(np.float32),
    }
    budgets = [30123, 33989, 37654, 41500, 45360, 47905, 52000, 57500]
    for n in budgets:
        cand_sets[f"betp_top_{n}"] = top_n(betp, n, allowed).astype(np.float32)
    for n in [37654, 47905]:
        cand_sets[f"bel_yager_top_{n}"] = top_n(bel_y, n, allowed).astype(np.float32)
        cand_sets[f"bel_dempster_top_{n}"] = top_n(np.nan_to_num(bel_dem, nan=-1.0), n, allowed).astype(np.float32)
    cand_sets["betp_soft_mass37654"] = soft_emission(betp, 37654.0, allowed)
    cand_sets["betp_soft_mass47905"] = soft_emission(betp, 47905.0, allowed)
    # corroboration-by-sum, the naive alternative to the DS ranking
    cand_sets["support_sum_top_37654"] = top_n(sup_d + sup_t, 37654, allowed).astype(np.float32)
    cand_sets["support_sum_top_47905"] = top_n(sup_d + sup_t, 47905, allowed).astype(np.float32)

    report = {
        "schema": "GEMSDOE48-candidate-screen-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "reliability": {"r_dotted": R_DOTTED, "r_tip": R_TIP,
                        "rule": "[PREREGISTERED] r_dotted = 0.90; r_tip = 0.90 x (measured live credit-per-dot ratio)"},
        "evidence_fields": {
            "dotted_support_cells": int((sup_d > 0).sum()),
            "tip_support_cells": int((sup_t > 0).sum()),
            "candidate_cells": int(allowed.sum()),
        },
        "ds_fields": {
            "belief_yager": {"min": float(bel_y.min()), "max": float(bel_y.max()), "mean": float(bel_y.mean())},
            "unassigned": {"min": float(unassigned.min()), "max": float(unassigned.max()), "mean": float(unassigned.mean())},
            "conflict": {"min": float(conflict.min()), "max": float(conflict.max()), "mean": float(conflict.mean()),
                         "cells_gt0": int((conflict > 1e-9).sum())},
            "pignistic": {"min": float(betp.min()), "max": float(betp.max()), "mean": float(betp.mean())},
        },
    }

    # ------------------------------------------------------- proxy screening
    blks = blocks(truths["sgmc_off300m"].shape)
    screen = {}
    for tname, truth in truths.items():
        rows = {}
        for name, arr in cand_sets.items():
            r = dti(arr.astype(np.float64), truth)
            per_block = []
            for ys, xs in blks:
                sub_t = truth[ys, xs]
                if sub_t.sum() < 50:
                    continue
                per_block.append(dti(arr.astype(np.float64)[ys, xs], sub_t).dti)
            rows[name] = {
                **r.as_dict(),
                "dots_or_mass": float((arr > 0).sum()),
                "block_dti_mean": float(np.mean(per_block)) if per_block else None,
                "block_dti_min": float(np.min(per_block)) if per_block else None,
                "blocks_scored": len(per_block),
            }
        base = rows["dotted_parent"]["dti"]
        for name in rows:
            rows[name]["delta_vs_dotted_parent"] = rows[name]["dti"] - base
        screen[tname] = {"truth_pixels": int(truth.sum()), "candidates": rows}
    report["proxy_screen"] = screen

    # ------------------------------- proxy credit rate by DS score decile / class
    dense = (betp > 0).astype(np.float64)
    cred, _, _ = credit_per_dot(dense, truths["sgmc_off300m"])
    q = np.quantile(betp[dense > 0], np.linspace(0, 1, 11))
    dec = {}
    for k in range(10):
        m = dense > 0
        m &= (betp >= q[k]) & (betp <= q[k + 1]) if k == 9 else (betp >= q[k]) & (betp < q[k + 1])
        n = int(m.sum())
        dec[f"decile_{k+1}"] = {
            "cells": n,
            "betp_low": float(q[k]), "betp_high": float(q[k + 1]),
            "proxy_credit_per_cell": float(cred[m].sum() / n) if n else 0.0,
        }
    cls = {}
    for nm, m in [("intersection", inter), ("dotted_only", dotted & ~tip), ("tip_only", tip & ~dotted)]:
        n = int(m.sum())
        cls[nm] = {"dots": n, "proxy_credit_per_cell": float(cred[m].sum() / n) if n else 0.0,
                   "mean_betp": float(betp[m].mean()) if n else 0.0}
    report["proxy_credit_density"] = {
        "note": "[MEASURED] credit realised by every candidate cell when all of them are emitted; competition for the same truth pixel is resolved by the metric's max, so this is a *realised* rather than a marginal rate.",
        "by_betp_decile": dec, "by_class": cls}

    (ROOT / "docs" / "data").mkdir(parents=True, exist_ok=True)
    (ROOT / "docs" / "data" / "h49-candidate-screen.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report["ds_fields"], indent=2))
    print(json.dumps({k: {kk: round(vv, 6) if isinstance(vv, float) else vv for kk, vv in v.items()
                          if kk in ("dti", "emitted_mass", "tp_w", "fp_w", "delta_vs_dotted_parent", "block_dti_mean")}
                      for k, v in screen["sgmc_off300m"]["candidates"].items()}, indent=2))


if __name__ == "__main__":
    main()
