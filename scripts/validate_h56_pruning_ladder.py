#!/usr/bin/env python3
"""Validate the preregistered H56-F belief-threshold pruning ladder on blocked proxies.

The old H56 slate's live-model gate is invalidated because its forward-model
identity FPw=S-TPw is false in general. This script uses no live-score projection:
it scores the frozen tau={0.99,0.95,0.90} C-dot masks on the same four-quadrant,
300 m-halo holdouts as H49, and compares them with the current H49 reference. A
fixed-seed same-budget random-deletion control is reported for the primary tau=.99
rung. No candidate TIFF is written and no submission slot is considered cleared.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT / "src", ROOT / "scripts"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from gemsdoe48.geotiff import assert_same_grid  # noqa: E402
from run_spatial_holdout import quadrants  # noqa: E402
from validate_h57a import compare_to_h49, make_contexts, read_one, read_raster, score_surface, sha256_array, sha256_file  # noqa: E402

PRIMARY = ROOT / "docs/downloads/GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif"
DOTTED = ROOT / "data/families/dotted_b2_prune_02778.tif"
TIP = ROOT / "data/families/tip_stepover_r30_02632.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
LABELS = ROOT / "data/raw/labels_catalogue.tif"
SGMC = ROOT / "data/official/derived_sgmc_faults_100m.tif"
H49 = ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif"
H49_REFERENCE = ROOT / "evidence/holdout_h56_h49_reference_20261007.json"
PINS = {
    "primary": "4d6548d4ec07a47a25b83d28ebc05d58b57448c1507b460aed52cec395bdb6b5",
    "dotted": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "tip": "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
    "footprint": "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
    "labels": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sgmc": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
    "h49": "9f028289c364c071065245799d7ed131600e80e9f0d10602806b12ce34d7cae8",
}
THRESHOLDS = (0.99, 0.95, 0.90)
RANDOM_SEED = 20261007


def paired_delta(candidate: dict[str, dict], baseline: dict[str, dict], truth_name: str) -> dict:
    folds = ("NW", "NE", "SW", "SE")
    deltas = {fold: float(candidate[truth_name][fold]["dti"] - baseline[truth_name][fold]["dti"]) for fold in folds}
    mean_delta = float(np.mean(list(deltas.values())))
    wins = int(sum(value > 0.0 for value in deltas.values()))
    return {
        "fold_delta_dti_vs_h49": deltas,
        "mean_delta_dti_vs_h49": mean_delta,
        "positive_folds": wins,
        "passes_numeric_gate": bool(mean_delta > 0.0 and wins >= 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/holdout_h56_pruning_ladder_20261007.json")
    parser.add_argument("--random-controls", type=int, default=24)
    args = parser.parse_args()
    if args.random_controls < 0:
        raise SystemExit("--random-controls must be nonnegative")

    files = {
        "primary": PRIMARY, "dotted": DOTTED, "tip": TIP,
        "footprint": FOOTPRINT, "labels": LABELS, "sgmc": SGMC, "h49": H49,
    }
    for path in files.values():
        if not path.exists():
            raise SystemExit(f"missing H56-F input: {path}")
    hashes = {name: sha256_file(path) for name, path in files.items()}
    for name, actual in hashes.items():
        if actual != PINS[name]:
            raise SystemExit(f"{name} SHA-256 changed: {actual} != {PINS[name]}")

    belief, p_primary = read_one(PRIMARY)
    dotted_raw, p_dotted = read_one(DOTTED)
    tip_raw, p_tip = read_one(TIP)
    footprint_raw, p_footprint = read_one(FOOTPRINT)
    labels, p_labels = read_one(LABELS)
    sgmc, p_sgmc = read_one(SGMC)
    h49_raw, p_h49 = read_one(H49)
    for profile, path in ((p_dotted,DOTTED),(p_tip,TIP),(p_footprint,FOOTPRINT),(p_labels,LABELS),(p_sgmc,SGMC),(p_h49,H49)):
        assert_same_grid(p_primary, profile, name_a=str(PRIMARY), name_b=str(path))

    footprint = footprint_raw == 1
    if not np.array_equal(footprint, labels != -1):
        raise SystemExit("footprint mask differs from catalogue-label nodata support")
    catalogue = (labels == 1) & footprint
    h49 = np.nan_to_num(h49_raw.astype(np.float32), nan=0.0)
    if not np.isfinite(belief).all() or np.any((belief < 0.0) | (belief > 1.0)):
        raise SystemExit("H56B primary must be finite and in [0,1]")
    dotted = (dotted_raw > 0) & footprint
    tip = (tip_raw > 0) & footprint
    distance_to_catalogue_m = __import__("scipy.ndimage", fromlist=["distance_transform_edt"]).distance_transform_edt(
        ~catalogue, sampling=(100.0, 100.0)
    )
    sgmc_offcat = (sgmc > 0) & footprint & (distance_to_catalogue_m > 300.0)
    truths = {"catalogue_proxy": catalogue, "sgmc_off_catalogue_gt300m": sgmc_offcat}
    contexts = make_contexts(truths, footprint, quadrants(*footprint.shape))

    baseline_surface = h49.astype(np.float64)
    baseline = score_surface(baseline_surface, contexts)
    frozen_ref = json.loads(H49_REFERENCE.read_text(encoding="utf-8"))
    for truth_name, receipt_name in (("catalogue_proxy", "results"), ("sgmc_off_catalogue_gt300m", "sgmc_off_catalogue_results")):
        expected = frozen_ref[receipt_name]["h49_balanced_same_protocol_reference"]
        for fold in ("NW", "NE", "SW", "SE"):
            actual = baseline[truth_name][fold]["dti"]
            if not np.isclose(actual, expected[fold]["dti"], rtol=0.0, atol=1e-10):
                raise SystemExit(f"H49 same-protocol baseline drift at {truth_name}/{fold}")

    candidates: dict[str, np.ndarray] = {}
    thresholds = {}
    for tau in THRESHOLDS:
        selected = dotted & (belief >= tau)
        name = f"H56-F_tau_{tau:.2f}"
        candidates[name] = selected.astype(np.float64)
        thresholds[name] = {
            "threshold": tau,
            "positive_cells": int(selected.sum()),
            "removed_from_dotted": int(dotted.sum() - selected.sum()),
            "selected_mask_sha256": sha256_array(selected.astype(np.uint8)),
        }

    comparators = {
        "H49_reference": baseline,
        "dotted_C": score_surface(dotted.astype(np.float64), contexts),
        "tip_stepover": score_surface(tip.astype(np.float64), contexts),
    }
    scored_candidates = {name: score_surface(surface, contexts) for name, surface in candidates.items()}
    paired_vs_h49 = {
        candidate_name: {
            truth_name: paired_delta(scored, baseline, truth_name)
            for truth_name in truths
        }
        for candidate_name, scored in scored_candidates.items()
    }

    primary_name = "H56-F_tau_0.99"
    primary_budget = int(candidates[primary_name].sum())
    dot_indices = np.flatnonzero(dotted.ravel())
    rng = np.random.default_rng(RANDOM_SEED)
    controls = []
    for i in range(args.random_controls):
        random_mask = np.zeros(dotted.size, dtype=bool)
        if primary_budget:
            chosen = rng.choice(dot_indices, size=primary_budget, replace=False)
            random_mask[chosen] = True
        random_mask = random_mask.reshape(dotted.shape)
        scored = score_surface(random_mask.astype(np.float64), contexts)
        controls.append({
            "draw": i,
            "mask_sha256": sha256_array(random_mask.astype(np.uint8)),
            "results": scored,
            "paired_vs_h49": {
                truth_name: paired_delta(scored, baseline, truth_name)
                for truth_name in truths
            },
        })
    control_summary = {}
    primary_scored = scored_candidates[primary_name]
    for truth_name in truths:
        values = [row["results"][truth_name]["mean_dti"] for row in controls]
        feature_value = primary_scored[truth_name]["mean_dti"]
        control_summary[truth_name] = {
            "feature_rank_mean_dti": feature_value,
            "random_same_budget_mean_dti": float(np.mean(values)) if values else None,
            "feature_minus_random_mean": float(feature_value - np.mean(values)) if values else None,
            "random_draws_below_feature": int(sum(value < feature_value for value in values)),
            "random_draws": len(values),
            "warning": "small descriptive control sample, not a significance test",
        }

    all_h49_gates_pass = all(
        paired_vs_h49[name][truth]["passes_numeric_gate"]
        for name in candidates
        for truth in truths
    )
    report = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "H56_F_BLOCKED_PROXY_RESEARCH_ONLY_NOT_SLOT_CLEARED",
        "preregistration": "evidence/hypothesis_slate_h56b_20261007.json, H56-F; its live-projection kill criterion is invalidated by docs/research/metric-identity-erratum-20261007.md",
        "candidate_thresholds": thresholds,
        "inputs": {name: {"path": str(path.relative_to(ROOT)), "sha256": hashes[name]} for name, path in files.items()},
        "fold_protocol": {
            "implementation": "same quadrant/300 m halo/metric as scripts/run_spatial_holdout.py, with fold-context computation shared through scripts/validate_h57a.py",
            "truth_in_core_only": True,
            "surface_retrained_within_folds": False,
            "alpha": 0.2,
            "beta": 0.8,
            "radius_m": 300,
        },
        "results": {
            "H49_reference": baseline,
            "dotted_C": comparators["dotted_C"],
            "tip_stepover": comparators["tip_stepover"],
            **scored_candidates,
        },
        "paired_vs_h49": paired_vs_h49,
        "primary_rung_same_budget_random_pruning_control": controls,
        "random_control_summary": control_summary,
        "slot_gate": {
            "rule": "each candidate must beat current H49 reference on both proxies: positive mean paired delta and >=3/4 positive folds",
            "all_thresholds_passed": bool(all_h49_gates_pass),
            "cleared": False,
            "reason": "Public proxy testing cannot establish private-label performance or organizer acceptance; all H56-F thresholds also fail at least one H49 proxy gate.",
        },
        "submit_verdict": "NOT CLEARED / DO NOT SUBMIT",
        "caveats": [
            "The original H56-F live-model threshold of 0.2727 was not used: its underlying FPw=S-TPw identity is false in general.",
            "The H56B belief input uses label-informed absence evidence and is a frozen upstream raster, not refit inside folds.",
            "Catalogue labels and SGMC are public map proxies, not private expert test truth.",
            "Random controls are descriptive, not inferential.",
            "No candidate TIFF was emitted; this is not a download artifact or slot authorization.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("H56-F thresholds:")
    for name in candidates:
        print(name, {truth: round(scored_candidates[name][truth]["mean_dti"], 6) for truth in truths})
        print("  vs H49", {truth: paired_vs_h49[name][truth]["mean_delta_dti_vs_h49"] for truth in truths})
    print("tau .99 random mean:", control_summary)
    print("submit verdict:", report["submit_verdict"])
    print("receipt:", args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
