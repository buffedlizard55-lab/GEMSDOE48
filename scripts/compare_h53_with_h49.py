#!/usr/bin/env python3
"""Compare the frozen H53-A spatial reports with same-protocol H49 receipts.

This report consumes only the candidate and comparator JSONs produced by the
repository's run_spatial_holdout.py. It refuses mismatched candidate hashes,
label sources, or fold/metric semantics. It does not query or infer organizer
scores.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "evidence/h53_vs_h49_20261007.json"
H53_NAME = "h53a_strike_coherent_12000"
H49_NAME = "h49_yager_balanced"
H53_SHA = "de35531d386792da1950eac815f98db8f36304f78debb6b568138d070640d9bd"
H49_SHA = "9f028289c364c071065245799d7ed131600e80e9f0d10602806b12ce34d7cae8"
EXPECTED_LABEL_SHA = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
EXPECTED_NEWER_SGMC_SHA = "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"
EXPECTED_OLDER_SGMC_SHA = "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c"
EXPECTED_GEOMETRY = "Four fixed 2x2 geographic quadrants on the full EPSG:32611 grid."
EXPECTED_METRIC = "Official distance-weighted Tversky equations; alpha=0.2, beta=0.8, triangular radius=300 m."
EXPECTED_DOMAIN = "Held-out quadrant plus a 300 m Euclidean halo, clipped to the finite survey footprint; only truth in the core quadrant is scored."
FOLDS = ("NW", "NE", "SW", "SE")


def load(path: Path) -> dict:
    with path.open(encoding="utf-8") as stream:
        return json.load(stream)


def display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(ROOT).as_posix()
    except ValueError:
        return str(resolved)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def target_scores(report: dict, target: str, candidate: str) -> tuple[dict[str, float], float]:
    field = "results" if target == "catalogue" else "sgmc_off_catalogue_results"
    try:
        row = report[field][candidate]
        per_fold = {fold: float(row[fold]["dti"]) for fold in FOLDS}
        mean = float(row["mean_dti"])
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(f"missing/invalid {target} scores for {candidate}: {exc}") from exc
    fold_mean = sum(per_fold.values()) / len(FOLDS)
    if not math.isclose(mean, fold_mean, rel_tol=1e-12, abs_tol=1e-12):
        raise SystemExit(
            f"{target} mean DTI for {candidate} ({mean}) does not match the four fold mean ({fold_mean})"
        )
    return per_fold, mean


def compare(target: str, candidate_report: dict, baseline_report: dict) -> dict:
    candidate_folds, candidate_mean = target_scores(candidate_report, target, H53_NAME)
    baseline_folds, baseline_mean = target_scores(baseline_report, target, H49_NAME)
    delta_by_fold = {
        fold: candidate_folds[fold] - baseline_folds[fold]
        for fold in FOLDS
    }
    mean_delta = sum(delta_by_fold.values()) / len(FOLDS)
    positive_folds = sum(value > 0.0 for value in delta_by_fold.values())
    return {
        "candidate_mean_dti": candidate_mean,
        "h49_mean_dti": baseline_mean,
        "paired_mean_delta_dti": mean_delta,
        "paired_fold_delta_dti": delta_by_fold,
        "positive_folds": positive_folds,
        "required_positive_folds": 3,
        "passes_preregistered_numeric_gate": bool(mean_delta > 0.0 and positive_folds >= 3),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h53-newer", type=Path, default=ROOT / "evidence/holdout_h53_spatial_20261007.json")
    parser.add_argument("--h53-older", type=Path, default=ROOT / "evidence/holdout_h53_raw_sgmc_20261007.json")
    parser.add_argument("--h49-newer", type=Path, default=ROOT / "evidence/holdout_h49_spatial_comparison_20261006.json")
    parser.add_argument("--h49-older", type=Path, default=ROOT / "evidence/holdout_h49_raw_sgmc_sensitivity_20261006.json")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    h53_newer, h53_older = load(args.h53_newer), load(args.h53_older)
    h49_newer, h49_older = load(args.h49_newer), load(args.h49_older)
    for name, report, expected_sha, expected_candidate in (
        ("H53 newer", h53_newer, H53_SHA, H53_NAME),
        ("H53 older", h53_older, H53_SHA, H53_NAME),
        ("H49 newer", h49_newer, H49_SHA, H49_NAME),
        ("H49 older", h49_older, H49_SHA, H49_NAME),
    ):
        require(report.get("candidate", {}).get("sha256") == expected_sha,
                f"{name}: candidate hash mismatch")
        require(report.get("candidate", {}).get("name") == expected_candidate,
                f"{name}: candidate name mismatch")
    for name, report in (("H53 newer", h53_newer), ("H53 older", h53_older),
                         ("H49 newer", h49_newer), ("H49 older", h49_older)):
        require(report.get("truth_sources", {}).get("catalogue", {}).get("sha256") == EXPECTED_LABEL_SHA,
                f"{name}: catalogue label hash mismatch")
        protocol = report.get("fold_protocol", {})
        require(protocol.get("metric") == EXPECTED_METRIC,
                f"{name}: metric does not match the preregistered DTI parameters")
        require(protocol.get("geometry") == EXPECTED_GEOMETRY,
                f"{name}: fold geometry does not match the preregistered quadrants")
        require(protocol.get("evaluation_domain") == EXPECTED_DOMAIN,
                f"{name}: evaluation domain does not match the preregistered core-plus-halo")
        require(protocol.get("candidate_retraining") is False,
                f"{name}: report unexpectedly retrains candidates inside folds")

    require(
        h53_newer["truth_sources"]["sgmc_off_catalogue_gt_300m"]["sha256"] == EXPECTED_NEWER_SGMC_SHA,
        "H53 newer report does not use the pinned newer SGMC raster",
    )
    require(
        h49_newer["truth_sources"]["sgmc_off_catalogue_gt_300m"]["sha256"] == EXPECTED_NEWER_SGMC_SHA,
        "H49 newer report does not use the pinned newer SGMC raster",
    )
    require(
        h53_older["truth_sources"]["sgmc_off_catalogue_gt_300m"]["sha256"] == EXPECTED_OLDER_SGMC_SHA,
        "H53 older report does not use the pinned raw SGMC raster",
    )
    require(
        h49_older["truth_sources"]["sgmc_off_catalogue_gt_300m"]["sha256"] == EXPECTED_OLDER_SGMC_SHA,
        "H49 older report does not use the pinned raw SGMC raster",
    )

    comparisons = {
        "newer_sgmc_offcatalogue": compare("sgmc", h53_newer, h49_newer),
        "older_raw_sgmc_offcatalogue": compare("sgmc", h53_older, h49_older),
        "public_catalogue_context_only": compare("catalogue", h53_newer, h49_newer),
    }
    newer_pass = comparisons["newer_sgmc_offcatalogue"]["passes_preregistered_numeric_gate"]
    older_pass = comparisons["older_raw_sgmc_offcatalogue"]["passes_preregistered_numeric_gate"]
    numeric_gate_passed = newer_pass and older_pass
    result = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "H53_A_NUMERIC_PROXY_GATE_PASSED_NO_SLOT_AUTHORIZED" if numeric_gate_passed else "H53_A_GATE_FAILED_NO_SLOT_USED",
        "candidate": {
            "name": H53_NAME,
            "sha256": H53_SHA,
            "source_report_newer": display_path(args.h53_newer),
            "source_report_newer_sha256": sha256_file(args.h53_newer),
            "source_report_older": display_path(args.h53_older),
            "source_report_older_sha256": sha256_file(args.h53_older),
        },
        "baseline": {
            "name": H49_NAME,
            "sha256": H49_SHA,
            "source_report_newer": display_path(args.h49_newer),
            "source_report_newer_sha256": sha256_file(args.h49_newer),
            "source_report_older": display_path(args.h49_older),
            "source_report_older_sha256": sha256_file(args.h49_older),
        },
        "comparisons": comparisons,
        "promotion_gate": {
            "requirements": "H53-A must beat H49 on the mean and in >=3/4 paired folds on both newer and older SGMC off-catalogue proxy reports.",
            "newer_pass": newer_pass,
            "older_pass": older_pass,
            "numeric_proxy_gate_passed": numeric_gate_passed,
            "competition_slot_authorized": False,
            "decision": (
                "NUMERIC PROXY GATE PASSED, BUT no weekly submission slot is authorized. A public-proxy pass alone does not establish private-label performance, leakage-free validation, or organizer acceptance."
                if numeric_gate_passed else
                "FAILED: no weekly submission slot is authorized or used. H53-A fails the mean and/or >=3/4-fold requirement against H49 on at least one SGMC proxy. Even a public-proxy pass would not alone establish private-label performance, leakage-free validation, or organizer acceptance."
            ),
        },
        "limitations": [
            "Both SGMC targets are public-map proxies, not private expert test truth or organizer scores.",
            "Candidate sources were not rebuilt independently inside the spatial folds; the full public catalogue was used as an exclusion mask during construction.",
            "The older SGMC raster is a separate sensitivity and was not pooled with the newer raster.",
            "A numerical comparison with H49 is valid only for these pinned local files and the recorded 4-quadrant/core-plus-halo protocol.",
        ],
        "weekly_slot_used": False,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
