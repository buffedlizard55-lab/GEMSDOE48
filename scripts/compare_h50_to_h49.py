#!/usr/bin/env python3
"""Paired, hash-checked comparison of H50-1 against the stored H49 best."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRIMARY_CANDIDATE = ROOT / "evidence/holdout_h50_probe_v2_exact_location_20261007.json"
PRIMARY_REFERENCE = ROOT / "evidence/holdout_h49_spatial_comparison_20261006.json"
SENSITIVITY_CANDIDATE = ROOT / "evidence/holdout_h50_probe_v2_exact_location_raw_sgmc_20261007.json"
SENSITIVITY_REFERENCE = ROOT / "evidence/holdout_h49_raw_sgmc_sensitivity_20261006.json"
OUTPUT = ROOT / "evidence/h50_probe_v2_exact_location_vs_h49_20261007.json"
CANDIDATE_NAME = "h50_probe_persistence_v2_exact_location"
REFERENCE_NAME = "h49_yager_balanced"
TARGET_KEY = "sgmc_off_catalogue_gt_300m"
RESULTS_KEY = "sgmc_off_catalogue_results"
FOLDS = ("NW", "NE", "SW", "SE")
MINIMUM_PRIMARY_DELTA = 0.005


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def compare_pair(
    candidate_report_path: Path,
    reference_report_path: Path,
    candidate_name: str,
    reference_name: str,
    *,
    enforce_target_hash: bool = True,
) -> dict:
    candidate = load(candidate_report_path)
    reference = load(reference_report_path)
    if candidate.get("fold_protocol") != reference.get("fold_protocol"):
        raise ValueError(f"fold protocols differ: {candidate_report_path} vs {reference_report_path}")
    candidate_truth = candidate["truth_sources"][TARGET_KEY]
    reference_truth = reference["truth_sources"][TARGET_KEY]
    if enforce_target_hash and candidate_truth.get("sha256") != reference_truth.get("sha256"):
        raise ValueError("candidate and reference reports do not use the same SGMC truth raster")
    if candidate_truth.get("positive_pixels") != reference_truth.get("positive_pixels"):
        raise ValueError("candidate and reference reports do not use the same positive truth count")
    candidate_scores = candidate[RESULTS_KEY][candidate_name]
    reference_scores = reference[RESULTS_KEY][reference_name]
    deltas = {
        fold: float(candidate_scores[fold]["dti"] - reference_scores[fold]["dti"])
        for fold in FOLDS
    }
    mean_delta = float(sum(deltas.values()) / len(FOLDS))
    positive_folds = int(sum(value > 0.0 for value in deltas.values()))
    return {
        "candidate_report": candidate_report_path.relative_to(ROOT).as_posix(),
        "reference_report": reference_report_path.relative_to(ROOT).as_posix(),
        "candidate_name": candidate_name,
        "reference_name": reference_name,
        "sgmc_truth_sha256": candidate_truth["sha256"],
        "sgmc_truth_positive_cells": int(candidate_truth["positive_pixels"]),
        "candidate_mean_dti": float(candidate_scores["mean_dti"]),
        "reference_mean_dti": float(reference_scores["mean_dti"]),
        "fold_delta_dti": deltas,
        "mean_delta_dti": mean_delta,
        "positive_folds": positive_folds,
        "folds_compared": list(FOLDS),
        "candidate_prediction_mass_by_fold": {
            fold: float(candidate_scores[fold]["prediction_mass"]) for fold in FOLDS
        },
        "reference_prediction_mass_by_fold": {
            fold: float(reference_scores[fold]["prediction_mass"]) for fold in FOLDS
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, default=PRIMARY_CANDIDATE)
    parser.add_argument("--reference", type=Path, default=PRIMARY_REFERENCE)
    parser.add_argument("--candidate-sensitivity", type=Path, default=SENSITIVITY_CANDIDATE)
    parser.add_argument("--reference-sensitivity", type=Path, default=SENSITIVITY_REFERENCE)
    parser.add_argument("--candidate-name", default=CANDIDATE_NAME)
    parser.add_argument("--reference-name", default=REFERENCE_NAME)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()

    primary = compare_pair(args.candidate, args.reference, args.candidate_name, args.reference_name)
    sensitivity = compare_pair(
        args.candidate_sensitivity,
        args.reference_sensitivity,
        args.candidate_name,
        args.reference_name,
    )
    primary_pass = primary["mean_delta_dti"] >= MINIMUM_PRIMARY_DELTA and primary["positive_folds"] >= 3
    sensitivity_pass = sensitivity["mean_delta_dti"] > 0.0 and sensitivity["positive_folds"] >= 3
    report = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_NUMERIC_PROXY_GATE_ONLY" if primary_pass and sensitivity_pass else "FAIL_NUMERIC_PROXY_GATE_NOT_SLOT_CLEARED",
        "preregistered_numeric_gate": {
            "primary_minimum_mean_delta_over_h49": MINIMUM_PRIMARY_DELTA,
            "primary_positive_folds_minimum": 3,
            "raw_sgmc_sensitivity_requires_positive_mean_and_at_least_3_folds": True,
        },
        "primary_newer_sgmc": primary,
        "older_raw_sgmc_sensitivity": sensitivity,
        "gate_checks": {
            "primary_gate_pass": primary_pass,
            "older_raw_sensitivity_pass": sensitivity_pass,
            "both_proxy_checks_pass": primary_pass and sensitivity_pass,
        },
        "slot_decision": {
            "cleared": False,
            "reason": "The candidate is compared only on public-map proxy labels. The proxy numerical gate failed; independently, a proxy pass would still not establish organizer/private-label performance or slot eligibility.",
        },
        "interpretation_limit": "These are same-fold paired differences under the repository's conditional public-proxy protocol. They are not independent confidence intervals, leaderboard scores, or evidence of a private test score.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
