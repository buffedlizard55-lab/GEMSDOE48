#!/usr/bin/env python3
"""Score the preregistered H58-G1 isostatic-gravity edge candidate (docs/research/h58-gravity-edge-preregistration-20261008.md).

Procedure and decision rule are frozen in that document; this script implements them without tuning.
Outputs evidence/h58_gravity_edge_holdout_20261008.json. Public SGMC proxy only; not organizer evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, maximum_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gemsdoe48 import ds58  # noqa: E402
from gemsdoe48 import metric as M  # noqa: E402
from gemsdoe48.holdout import quadrants  # noqa: E402

from build_h58_ds_b2_h32 import (  # noqa: E402
    COMPARISON, INPUTS, SGMC_EXPECTED_OFFCAT, read_plane, require,
)

FEATURES = ROOT / "data/raw/training_features.tif"
FEATURES_SHA = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
BAND_ISO_GRAV = 13  # iso_grav_anom
BUDGET = 37654
NO_GRAVITY_IN_FOOTPRINT = -1
PIXEL_M = 100.0
RADIUS_M = 300.0
DENSITY_SEEDS = (1, 2, 3)
RANDOM_SEEDS = (1, 2, 3, 4, 5)


def gravity_edge_candidates(fp: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (candidate mask, magnitude) for the frozen Blakely-Simpson 3x3 maxima rule."""
    with rasterio.open(FEATURES) as ds:
        if ds.count != 19 or ds.width != 3292 or ds.height != 3730:
            raise SystemExit("training_features.tif grid/band count does not match the competition grid")
        g = ds.read(BAND_ISO_GRAV).astype(np.float64)
        nodata = ds.nodatavals[BAND_ISO_GRAV - 1]
    valid = fp & np.isfinite(g)
    if nodata is not None and np.isfinite(nodata):
        valid &= g != nodata
    # Footprint cells without a finite gravity value are excluded from candidates (preregistered step 1).
    global NO_GRAVITY_IN_FOOTPRINT
    NO_GRAVITY_IN_FOOTPRINT = int((fp & ~valid).sum())
    g = np.where(valid, g, 0.0)
    gy, gx = np.gradient(g, PIXEL_M, PIXEL_M)
    mag = np.sqrt(gx * gx + gy * gy)
    # exclude cells whose 8-neighbourhood leaves the footprint
    interior = valid & ~(maximum_filter((~valid).astype(np.uint8), size=3) > 0)
    score = np.where(interior, mag, -np.inf)
    local_max = (score >= maximum_filter(score, size=3)) & interior
    return local_max, np.where(interior, mag, 0.0)


def topk_mask(values: np.ndarray, allowed: np.ndarray, k: int) -> np.ndarray:
    idx = np.flatnonzero(allowed.ravel())
    k = min(k, idx.size)
    order = idx[np.argsort(-values.ravel()[idx], kind="stable")[:k]]
    out = np.zeros(values.size, dtype=bool)
    out[order] = True
    return out.reshape(values.shape)


def quadrant_scores(pred: np.ndarray, offcat: np.ndarray, fp: np.ndarray, quads) -> list[float]:
    out = []
    for quad in quads:
        domain = (distance_transform_edt(~quad, sampling=PIXEL_M) <= RADIUS_M) & fp
        out.append(float(M.distance_weighted_tversky(pred, offcat & quad, valid=domain)["dti"]))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "evidence/h58_gravity_edge_holdout_20261008.json")
    args = ap.parse_args()
    require(FEATURES, FEATURES_SHA, "training_features")
    for label in ("dotted_b2", "tip_h32_1", "footprint", "catalogue", "sgmc"):
        require(*INPUTS[label], label)

    with rasterio.open(INPUTS["footprint"][0]) as ds:
        fp = ds.read(1) == 1
    cat = read_plane(INPUTS["catalogue"][0]) > 0
    sgmc = read_plane(INPUTS["sgmc"][0]) > 0
    dotted = (read_plane(INPUTS["dotted_b2"][0]) > 0) & fp
    tip = (read_plane(INPUTS["tip_h32_1"][0]) > 0) & fp
    dist_cat = distance_transform_edt(~cat, sampling=PIXEL_M)
    offcat = sgmc & fp & (dist_cat > RADIUS_M)
    if int(offcat.sum()) != SGMC_EXPECTED_OFFCAT:
        raise SystemExit("SGMC off-catalogue count mismatch")
    quads = quadrants(fp)

    maxima, mag = gravity_edge_candidates(fp)
    n_max = int((maxima & fp).sum())
    eligible = maxima & fp & (dist_cat > RADIUS_M)
    n_eligible = int(eligible.sum())
    g_emit = topk_mask(mag, eligible, BUDGET)
    if int(g_emit.sum()) != min(BUDGET, n_eligible):
        raise SystemExit("budget selection error")

    ra, rb = ds58.reliabilities()
    h58 = ds58.fuse_dots(dotted, tip, fp, ra, rb).belief
    rand_sets = {}
    for seed in RANDOM_SEEDS:
        rng = np.random.default_rng(seed)
        idx = np.flatnonzero(fp.ravel())
        keep = rng.choice(idx, size=BUDGET, replace=False)
        m = np.zeros(fp.size, dtype=bool)
        m[keep] = True
        rand_sets[seed] = m.reshape(fp.shape)

    def ev_full(pred_bool_or_float):
        p = np.where(cat, 0.0, np.where(fp, np.asarray(pred_bool_or_float, dtype=np.float64), 0.0))
        return float(M.dti(p, offcat, fp).dti)

    def ev_quads(pred_bool_or_float):
        p = np.where(cat, 0.0, np.where(fp, np.asarray(pred_bool_or_float, dtype=np.float64), 0.0))
        return quadrant_scores(p, offcat, fp, quads)

    full = {
        "G1_gravity_edge_top37654": ev_full(g_emit),
        "B2_owner_0.2778 (reference)": ev_full(dotted),
        "H58_dot_supported_DS": ev_full(h58),
        "random_budget_37654 (mean of seeds)": float(np.mean([ev_full(rand_sets[s]) for s in RANDOM_SEEDS])),
    }
    quad = {
        "G1_gravity_edge_top37654": ev_quads(g_emit),
        "B2_owner_0.2778 (reference)": ev_quads(dotted),
        "H58_dot_supported_DS": ev_quads(h58),
        "random_budget_37654 (mean of seeds)": list(np.mean([ev_quads(rand_sets[s]) for s in RANDOM_SEEDS], axis=0)),
    }
    b2_q = np.array(quad["B2_owner_0.2778 (reference)"])
    g_q = np.array(quad["G1_gravity_edge_top37654"])
    wins_quadrants = int(np.sum(g_q > b2_q))

    density = {}
    idx_off = np.flatnonzero(offcat.ravel())
    for dens in (25000, 12632):
        vals = {"G1": [], "B2": [], "random": []}
        for seed in DENSITY_SEEDS:
            rng = np.random.default_rng(seed)
            keep = rng.choice(idx_off, size=dens, replace=False)
            truth = np.zeros(offcat.size, dtype=bool)
            truth[keep] = True
            truth = truth.reshape(offcat.shape)
            for name, pred in {"G1": g_emit, "B2": dotted, "random": rand_sets[RANDOM_SEEDS[0]]}.items():
                p = np.where(cat, 0.0, pred.astype(np.float64))
                vals[name].append(float(M.dti(p, truth, fp).dti))
        density[str(dens)] = {k: float(np.mean(v)) for k, v in vals.items()}
        density[str(dens)]["G1_minus_B2"] = float(np.mean(np.array(vals["G1"]) - np.array(vals["B2"])))

    gate = {
        "a_full_footprint_G1_gt_B2": full["G1_gravity_edge_top37654"] > full["B2_owner_0.2778 (reference)"],
        "b_quadrant_wins_vs_B2": wins_quadrants,
        "b_pass_at_least_3_of_4": wins_quadrants >= 3,
        "c_density_25000_G1_gt_B2": density["25000"]["G1_minus_B2"] > 0,
        "c_density_12632_G1_gt_B2": density["12632"]["G1_minus_B2"] > 0,
    }
    gate["passes_preregistered_proxy_gate"] = bool(
        gate["a_full_footprint_G1_gt_B2"] and gate["b_pass_at_least_3_of_4"]
        and gate["c_density_25000_G1_gt_B2"] and gate["c_density_12632_G1_gt_B2"]
    )
    gate["slot_cleared"] = False

    # EXPLORATORY (not part of the frozen gate): the budget was infeasible (12,600 < 37,654), so report
    # the emitted-mass-matched comparison at the realised size, to say what the signal is worth.
    n_emit = int(g_emit.sum())
    near_truth = distance_transform_edt(~offcat, sampling=PIXEL_M) <= RADIUS_M
    rng = np.random.default_rng(1)
    idx_fp = np.flatnonzero(fp.ravel())
    rnd = np.zeros(fp.size, dtype=bool)
    rnd[rng.choice(idx_fp, size=n_emit, replace=False)] = True
    rnd = rnd.reshape(fp.shape)
    exploratory = {
        "label": "EXPLORATORY, post-gate: mass-matched at the realised emission size; not used for the decision",
        "emitted": n_emit,
        "precision_within_300m_of_truth": {
            "G1": float(near_truth[g_emit].mean()),
            "random_same_mass_seed1": float(near_truth[rnd].mean()),
            "footprint_base_rate": float(near_truth[fp].mean()),
        },
        "full_footprint_dti": {
            "G1": ev_full(g_emit),
            "random_same_mass_seed1": ev_full(rnd),
        },
    }

    payload = {
        "schema": "GEMSDOE48-H58-G1-gravity-edge-holdout-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "preregistration": "docs/research/h58-gravity-edge-preregistration-20261008.md",
        "inputs": {
            "training_features": {"path": "data/raw/training_features.tif", "sha256": FEATURES_SHA,
                                  "band": BAND_ISO_GRAV, "name": "iso_grav_anom"},
            "dotted_b2": {"sha256": INPUTS["dotted_b2"][1]},
            "tip_h32_1": {"sha256": INPUTS["tip_h32_1"][1]},
        },
        "candidate_counts": {
            "footprint_cells": int(fp.sum()),
            "footprint_cells_without_finite_gravity": NO_GRAVITY_IN_FOOTPRINT,
            "local_maxima_in_footprint": n_max,
            "eligible_offcatalogue_gt_300m": n_eligible,
            "emitted": int(g_emit.sum()),
            "budget": BUDGET,
        },
        "full_footprint_dti": full,
        "quadrant_dti": quad,
        "density_sensitivity_mean_dti": density,
        "gate": gate,
        "exploratory_matched_mass": exploratory,
        "limitations": [
            "The public SGMC proxy is a published map; gravity edges may also reflect lithologic contacts.",
            "Single preregistered configuration; no tuning was performed on this proxy.",
            "The training feature stack is an owner mirror of the official GeoDAWN features; provenance is unverified.",
        ],
        "verdict": "NOT CLEARED" if not gate["passes_preregistered_proxy_gate"] else "ELIGIBLE FOR PREREGISTERED SLOT REVIEW ONLY",
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"candidate_counts": payload["candidate_counts"], "full": full, "gate": gate,
                      "density": density}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
