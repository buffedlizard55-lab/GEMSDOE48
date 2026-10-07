#!/usr/bin/env python3
"""Join frozen H56 build receipts to the identical-protocol H49 reference runs."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "ds_build": ROOT / "evidence/build_h56_receipt_20261007.json",
    "strain_build": ROOT / "evidence/h56_strain_ridge_build_20261007.json",
    "ds_holdout": ROOT / "evidence/holdout_h56_ds_20261007.json",
    "strain_holdout": ROOT / "evidence/holdout_h56a_strain_ridge_20261007.json",
    "h49_reference": ROOT / "evidence/holdout_h56_h49_reference_20261007.json",
    "uniqueness": ROOT / "evidence/h56_uniqueness_audit_20261007.json",
    "format": ROOT / "evidence/h56_submission_validation_20261007.json",
}
OUT = ROOT / "evidence/h56_decision_20261007.json"
FOLDS = ("NW", "NE", "SW", "SE")


def load(key: str) -> dict:
    return json.loads(FILES[key].read_text(encoding="utf-8"))


def compare(candidate: dict, reference: dict, candidate_key: str, reference_key: str) -> dict:
    targets = {
        "catalogue_proxy": ("results", "results"),
        "sgmc_off_catalogue_gt_300m_proxy": ("sgmc_off_catalogue_results", "sgmc_off_catalogue_results"),
    }
    out = {}
    for label, (candidate_section, reference_section) in targets.items():
        cand = candidate[candidate_section][candidate_key]
        ref = reference[reference_section][reference_key]
        fold_delta = {fold: float(cand[fold]["dti"] - ref[fold]["dti"]) for fold in FOLDS}
        out[label] = {
            "candidate_mean_dti": float(cand["mean_dti"]),
            "h49_same_protocol_mean_dti": float(ref["mean_dti"]),
            "mean_delta_vs_h49": float(sum(fold_delta.values()) / len(FOLDS)),
            "fold_delta_vs_h49": fold_delta,
            "positive_folds": int(sum(value > 0.0 for value in fold_delta.values())),
            "pass_numeric_improvement": bool(sum(fold_delta.values()) > 0.0 and all(value > 0.0 for value in fold_delta.values())),
        }
    return out


def main() -> int:
    ds_build, strain_build = load("ds_build"), load("strain_build")
    ds_holdout, strain_holdout = load("ds_holdout"), load("strain_holdout")
    h49 = load("h49_reference")
    uniqueness, format_audit = load("uniqueness"), load("format")

    if ds_build["candidate"]["primary"]["sha256"] != ds_holdout["candidate"]["sha256"]:
        raise SystemExit("H56-DS holdout hash does not match built primary")
    if strain_build["output"]["sha256"] != strain_holdout["candidate"]["sha256"]:
        raise SystemExit("H56-A holdout hash does not match built probe")
    if ds_build["candidate"]["primary"]["sha256"] != format_audit["sha256"]:
        raise SystemExit("H56-DS format receipt hash does not match built primary")
    if uniqueness["primary"]["sha256"] != format_audit["sha256"]:
        raise SystemExit("H56-DS uniqueness receipt hash does not match format receipt")

    ds_vs_h49 = compare(ds_holdout, h49, "h56_ds_open_world_b2xh33d", "h49_balanced_same_protocol_reference")
    strain_vs_h49 = compare(strain_holdout, h49, "h56a_strain_ridge", "h49_balanced_same_protocol_reference")
    for build, comparison, candidate_name in (
        (ds_build, ds_vs_h49, "H56-DS"),
        (strain_build, strain_vs_h49, "H56-A"),
    ):
        build["holdout"] = {
            "status": "COMPLETED_CONDITIONAL_PUBLIC_PROXY_SPATIAL_BLOCK_TEST",
            "h49_reference_receipt": "evidence/holdout_h56_h49_reference_20261007.json",
            "candidate_receipt": (
                "evidence/holdout_h56_ds_20261007.json" if candidate_name == "H56-DS"
                else "evidence/holdout_h56a_strain_ridge_20261007.json"
            ),
            "results_vs_h49": comparison,
            "slot_decision": "NOT_CLEARED",
            "decision_reason": "The candidate fails to beat same-protocol H49 on both public proxy targets; no private-label or organizer score exists.",
        }
        build["status"] = "BUILT_AND_PUBLIC_PROXY_TESTED_NOT_SLOT_CLEARED"
        path = FILES["ds_build"] if candidate_name == "H56-DS" else FILES["strain_build"]
        path.write_text(json.dumps(build, indent=2) + "\n", encoding="utf-8")

    decision = {
        "schema_version": 1,
        "finalized_utc": datetime.now(timezone.utc).isoformat(),
        "status": "NO_SLOT_CLEARED",
        "current_proxy_best": {
            "candidate": h49["candidate"],
            "source_receipt": "evidence/holdout_h56_h49_reference_20261007.json",
            "catalogue_mean_dti": h49["results"]["h49_balanced_same_protocol_reference"]["mean_dti"],
            "sgmc_off_catalogue_mean_dti": h49["sgmc_off_catalogue_results"]["h49_balanced_same_protocol_reference"]["mean_dti"],
            "not_private_truth_or_organizer_score": True,
        },
        "H56_DS": {
            "build_receipt": "evidence/build_h56_receipt_20261007.json",
            "holdout_receipt": "evidence/holdout_h56_ds_20261007.json",
            "format_receipt": "evidence/h56_submission_validation_20261007.json",
            "uniqueness_receipt": "evidence/h56_uniqueness_audit_20261007.json",
            "comparison_vs_h49": ds_vs_h49,
            "download": ds_build["candidate"]["primary"]["path"],
            "download_ok": True,
            "submission_recommendation": "DO_NOT_SUBMIT; public proxy is substantially below H49, and no private-label or organizer acceptance exists.",
            "novelty": uniqueness["novelty_scope"],
            "nonmean_diagnostics": ds_build["not_the_naive_mean"],
            "outside_encoding_note": "all-finite zeros outside passed local range checks; official description also documents null/NaN outside, and organizer acceptance is untested.",
        },
        "H56_A": {
            "build_receipt": "evidence/h56_strain_ridge_build_20261007.json",
            "holdout_receipt": "evidence/holdout_h56a_strain_ridge_20261007.json",
            "comparison_vs_h49": strain_vs_h49,
            "download": "scratch/H56-A-strain-ridge-massmatched-20261007.tif",
            "download_ok_for_research_only": True,
            "submission_recommendation": "DO_NOT_SUBMIT; machine-spec mass-matched Hessian-only strain-ridge probe fails H49 on both public proxy targets.",
            "preregistration_interpretation": "The original Markdown slate also mentioned an unspecified structure-tensor term; the explicit machine-readable frozen_test omits it and the builder did not compute it. This result applies to the Hessian-only screen, not the coherence-augmented prose idea.",
            "preregistration_erratum": "docs/research/h56-slate-erratum-20261007.md",
            "feature_stack_caveat": "SHA-pinned third-party mirror, not organizer-authenticated; 3,061 in-footprint cells are nodata and 1,540 valid stack cells outside the competition footprint were excluded.",
        },
        "0_2778_attribution": {
            "status": "OWNER_REPORTED_FAMILY_SCORE_NOT_VERIFIED_FOR_LOCAL_BYTES",
            "explanation": "The owner-reported A→B→C dotted ladder (0.2600→0.2708→0.2778) is algebraically consistent with removing predictions close to the public USGS/INGENIOUS catalogue that the organizer says is masked during scoring. This is a plausible explanation, not proof that the exact local B2 TIFF earned 0.2778; the local audit says UNSCORED and no organizer file-to-score receipt exists.",
            "primary_record": "docs/research/why-02778-and-ceiling-20261007.md",
            "official_metric": "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
            "official_mask_clarification": "https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4",
            "leaderboard_observation": "The 2026-10-06 snapshot placed a 0.2778 row at rank 13; a leaderboard row does not identify these local file bytes.",
        },
        "limitations": [
            "Four-quadrant spatial-block outputs are conditional public-map proxy diagnostics, not private expert-label scores.",
            "The frozen family inputs were not reconstructed independently inside each fold; the H33-2-B2 owner audit describes full-scene catalogue-distance pruning, creating potential leakage.",
            "No organizer portal upload/acceptance, official score, or leaderboard link to the H56 file exists.",
            "H56-DS is a distinct open-world D-S parameterization, not a new geological evidence family or concept-level novelty claim.",
            "No weekly competition slot is cleared or recommended.",
        ],
    }
    OUT.write_text(json.dumps(decision, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": decision["status"],
        "H56_DS_vs_H49": ds_vs_h49,
        "H56_A_vs_H49": strain_vs_h49,
        "receipt": OUT.relative_to(ROOT).as_posix(),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
