#!/usr/bin/env python3
"""Run the frozen H58-A four-quadrant public-proxy holdout against H49.

This uses the same scorer and core-plus-300m-halo implementation as
scripts/run_spatial_holdout.py. The targets are public-map proxies, not the
private expert-labelled competition test set. The family parents are frozen
upstream rasters and are not rebuilt independently inside each fold, so this
is conditional evidence with known leakage risk—not blind validation.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

# Import the repository's shared fold geometry/scoring code, avoiding a second
# implementation of the official metric in this validator.
SPEC = importlib.util.spec_from_file_location(
    "gemsdoe48_run_spatial_holdout", ROOT / "scripts/run_spatial_holdout.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("could not import scripts/run_spatial_holdout.py")
HOLDOUT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(HOLDOUT)

EXPECTED = {
    "labels": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sgmc_newer": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
    "sgmc_raw": "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c",
    "footprint": "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
    "h49": "9f028289c364c071065245799d7ed131600e80e9f0d10602806b12ce34d7cae8",
    "dotted": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "tip": "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
}
PATHS = {
    "labels": ROOT / "data/raw/labels_catalogue.tif",
    "sgmc_newer": ROOT / "data/official/derived_sgmc_faults_100m.tif",
    "sgmc_raw": ROOT / "data/raw/sgmc_faults_100m.tif",
    "footprint": ROOT / "data/source_mirrors/footprint-mask.tif",
    "h49": ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif",
    "dotted": ROOT / "data/families/dotted_b2_prune_02778.tif",
    "tip": ROOT / "data/families/tip_stepover_r30_02632.tif",
}
H58_RECEIPT = ROOT / "evidence/build_h58_receipt_20261008.json"
OUTPUT = ROOT / "evidence/holdout_h58_20261008.json"
EXPECTED_CATALOGUE_CELLS = 60_988
EXPECTED_NEW_SGMC_OFFCAT_CELLS = 62_122


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_grid(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as source:
        HOLDOUT.assert_competition_grid(source.profile, path=path)
        return source.read(1), source.profile.copy()


def load_candidate(
    path: Path,
    footprint: np.ndarray,
    template_profile: dict,
    *,
    require_all_finite: bool,
) -> np.ndarray:
    values, profile = read_grid(path)
    HOLDOUT.assert_same_grid(template_profile, profile, name_a="template", name_b=str(path))
    if values.dtype != np.float32:
        raise SystemExit(f"{path}: expected float32, got {values.dtype}")
    if require_all_finite and not np.isfinite(values).all():
        raise SystemExit(f"{path}: all-finite encoding required for the local range gate")
    if not np.isfinite(values[footprint]).all():
        raise SystemExit(f"{path}: prediction must be finite inside the scoring footprint")
    if np.any((values[footprint] < 0.0) | (values[footprint] > 1.0)):
        raise SystemExit(f"{path}: in-footprint values must be in [0,1]")
    if require_all_finite and np.any(values[~footprint] != 0.0):
        raise SystemExit(f"{path}: values outside footprint must be exactly zero")
    # The local metric ignores outside-footprint cells. This converts H49's
    # historical NaN-outside storage to zero without changing in-footprint data.
    return np.where(footprint, values, 0.0).astype(np.float32)


def summarize_candidate(
    name: str,
    prediction: np.ndarray,
    truth: np.ndarray,
    footprint: np.ndarray,
    blocks: dict[str, np.ndarray],
) -> dict:
    folds = {
        fold_name: HOLDOUT.score_fold(prediction, truth, footprint, core)
        for fold_name, core in blocks.items()
    }
    return {
        "per_fold": folds,
        "mean_dti": float(np.mean([folds[fold]["dti"] for fold in blocks])),
        "positive_prediction_cells": int(np.count_nonzero(prediction[footprint] > 0.0)),
        "prediction_mass_inside_footprint": float(prediction[footprint].sum(dtype=np.float64)),
    }


def paired_delta(candidate: dict, reference: dict, fold_names: list[str]) -> dict:
    deltas = {
        fold: float(candidate["per_fold"][fold]["dti"] - reference["per_fold"][fold]["dti"])
        for fold in fold_names
    }
    mean_delta = float(np.mean(list(deltas.values())))
    wins = int(sum(delta > 0.0 for delta in deltas.values()))
    return {
        "fold_delta_dti": deltas,
        "mean_delta_dti": mean_delta,
        "positive_folds": wins,
        "passes_necessary_numeric_gate": bool(mean_delta > 0.0 and wins >= 3),
    }


def main() -> int:
    build = json.loads(H58_RECEIPT.read_text(encoding="utf-8"))
    candidate_path = ROOT / build["candidate"]["primary"]["path"]
    expected_candidate_sha = build["candidate"]["primary"]["sha256"]
    if sha256_file(candidate_path) != expected_candidate_sha:
        raise SystemExit("H58 primary SHA-256 differs from its build receipt")

    for key, path in PATHS.items():
        actual = sha256_file(path)
        if actual != EXPECTED[key]:
            raise SystemExit(f"{key} SHA-256 mismatch: expected {EXPECTED[key]}, got {actual}")

    labels, label_profile = read_grid(PATHS["labels"])
    footprint_values, footprint_profile = read_grid(PATHS["footprint"])
    if footprint_values.dtype != np.uint8 or not np.isin(footprint_values, (0, 1)).all():
        raise SystemExit("footprint must be uint8 containing only 0/1")
    footprint = footprint_values == 1
    HOLDOUT.assert_same_grid(label_profile, footprint_profile, name_a="labels", name_b="footprint")
    if int(footprint.sum()) != 5_167_373:
        raise SystemExit(f"unexpected footprint cell count: {int(footprint.sum())}")
    if int(np.count_nonzero((labels > 0) & footprint)) != EXPECTED_CATALOGUE_CELLS:
        raise SystemExit("registered catalogue positive-cell count mismatch")

    newer_sgmc, newer_profile = read_grid(PATHS["sgmc_newer"])
    raw_sgmc, raw_profile = read_grid(PATHS["sgmc_raw"])
    HOLDOUT.assert_same_grid(label_profile, newer_profile, name_a="labels", name_b="newer SGMC")
    HOLDOUT.assert_same_grid(label_profile, raw_profile, name_a="labels", name_b="raw SGMC")
    catalogue_truth = (labels > 0) & footprint
    distance_to_catalogue = distance_transform_edt(
        ~catalogue_truth, sampling=(100.0, 100.0)
    )
    sgmc_newer_truth = (newer_sgmc > 0) & footprint & (distance_to_catalogue > 300.0)
    sgmc_raw_truth = (raw_sgmc > 0) & footprint & (distance_to_catalogue > 300.0)
    if int(sgmc_newer_truth.sum()) != EXPECTED_NEW_SGMC_OFFCAT_CELLS:
        raise SystemExit(f"newer SGMC off-catalogue count mismatch: {int(sgmc_newer_truth.sum())}")

    template, template_profile = read_grid(ROOT / "data/raw/sample_submission_template.tif")
    if not np.array_equal(np.isfinite(template), footprint):
        raise SystemExit("template finite mask differs from registered footprint")
    candidate = load_candidate(
        candidate_path, footprint, template_profile, require_all_finite=True
    )
    h49 = load_candidate(
        PATHS["h49"], footprint, template_profile, require_all_finite=False
    )
    dotted_band, dotted_profile = read_grid(PATHS["dotted"])
    tip_band, tip_profile = read_grid(PATHS["tip"])
    HOLDOUT.assert_same_grid(template_profile, dotted_profile, name_a="template", name_b="dotted")
    HOLDOUT.assert_same_grid(template_profile, tip_profile, name_a="template", name_b="tip")
    dotted = np.where(footprint, dotted_band, 0.0).astype(np.float32)
    tip = np.where(footprint, tip_band, 0.0).astype(np.float32)
    binary_mean = 0.5 * (dotted + tip)
    binary_union = ((dotted > 0.0) | (tip > 0.0)).astype(np.float32)

    blocks_raw = HOLDOUT.quadrants(*labels.shape)
    block_order = ["NW", "NE", "SW", "SE"]
    blocks = {name: blocks_raw[name] for name in block_order}
    targets = {
        "catalogue": catalogue_truth,
        "sgmc_newer_gt_300m_off_catalogue": sgmc_newer_truth,
        "sgmc_raw_gt_300m_off_catalogue_sensitivity": sgmc_raw_truth,
    }
    candidates = {
        "H58_positive_only_DS": candidate,
        "H49_current_same_protocol_reference": h49,
        "dotted_parent": dotted,
        "tip_stepover_parent": tip,
        "arithmetic_mean_of_binary_parents": binary_mean.astype(np.float32),
        "binary_union_of_parents": binary_union,
    }

    result_sets = {}
    deltas = {}
    for target_name, truth in targets.items():
        results = {
            name: summarize_candidate(name, values, truth, footprint, blocks)
            for name, values in candidates.items()
        }
        result_sets[target_name] = results
        deltas[target_name] = paired_delta(
            results["H58_positive_only_DS"],
            results["H49_current_same_protocol_reference"],
            block_order,
        )

    primary_gates = [
        deltas["catalogue"]["passes_necessary_numeric_gate"],
        deltas["sgmc_newer_gt_300m_off_catalogue"]["passes_necessary_numeric_gate"],
    ]
    passed = bool(all(primary_gates))
    prior_h49_path = ROOT / "evidence/holdout_h49_currentprotocol_20261007.json"
    prior_h49 = json.loads(prior_h49_path.read_text(encoding="utf-8"))
    prior_h49_scores = {
        "catalogue": prior_h49["results"]["h49_balanced_reference"],
        "sgmc_newer_gt_300m_off_catalogue": prior_h49["sgmc_off_catalogue_results"]["h49_balanced_reference"],
    }
    h49_crosscheck = {}
    for target_name, prior_scores in prior_h49_scores.items():
        current_scores = result_sets[target_name]["H49_current_same_protocol_reference"]
        fold_deltas = {
            fold: float(current_scores["per_fold"][fold]["dti"] - prior_scores[fold]["dti"])
            for fold in block_order
        }
        h49_crosscheck[target_name] = {
            "prior_receipt": str(prior_h49_path.relative_to(ROOT)),
            "prior_receipt_candidate_sha256": prior_h49["candidate"]["sha256"],
            "fold_delta_current_minus_prior": fold_deltas,
            "current_mean_minus_prior_mean": float(current_scores["mean_dti"] - prior_scores["mean_dti"]),
            "exact_within_1e_12": bool(
                max([abs(value) for value in fold_deltas.values()] +
                    [abs(current_scores["mean_dti"] - prior_scores["mean_dti"])]) <= 1e-12
            ),
        }
    if not all(item["exact_within_1e_12"] for item in h49_crosscheck.values()):
        raise SystemExit("current H49 scores do not reproduce the registered same-protocol reference")
    report = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BLOCKED_PUBLIC_PROXY_HOLDOUT_COMPLETED_NOT_PRIVATE_TRUTH",
        "candidate": {
            "name": build["candidate"]["unique_name"],
            "path": build["candidate"]["primary"]["path"],
            "sha256": expected_candidate_sha,
            "build_receipt": "evidence/build_h58_receipt_20261008.json",
        },
        "source_pins": {
            key: {"path": str(path.relative_to(ROOT)), "sha256": EXPECTED[key]}
            for key, path in PATHS.items()
        },
        "fold_protocol": {
            "source": "scripts/run_spatial_holdout.py shared quadrants() and score_fold() functions",
            "geometry": "four fixed 2x2 geographic quadrants on the 100m EPSG:32611 raster",
            "evaluation_domain": "held-out quadrant core plus 300m Euclidean halo, clipped to finite footprint; only core truth is scored",
            "metric": "distance-weighted Tversky, alpha=0.2, beta=0.8, 300m triangular kernel",
            "candidate_retraining": False,
            "proxy_target_warning": "Catalogue and SGMC are public-map proxies, not the private expert-labelled competition target. Parent surfaces are frozen upstream products and were not rebuilt fold-by-fold; the catalogue-derived B2 construction is potentially leaky.",
        },
        "targets": {
            "catalogue": {
                "path": "data/raw/labels_catalogue.tif",
                "sha256": EXPECTED["labels"],
                "positive_cells": int(catalogue_truth.sum()),
                "private_expert_truth": False,
            },
            "sgmc_newer_gt_300m_off_catalogue": {
                "path": "data/official/derived_sgmc_faults_100m.tif",
                "sha256": EXPECTED["sgmc_newer"],
                "positive_cells": int(sgmc_newer_truth.sum()),
                "definition": "SGMC positive inside footprint and strictly more than 300m from any positive public catalogue pixel",
                "private_expert_truth": False,
            },
            "sgmc_raw_gt_300m_off_catalogue_sensitivity": {
                "path": "data/raw/sgmc_faults_100m.tif",
                "sha256": EXPECTED["sgmc_raw"],
                "positive_cells": int(sgmc_raw_truth.sum()),
                "definition": "Older, distinct raw SGMC mirror under the same >300m catalogue exclusion; kept separate, never pooled",
                "private_expert_truth": False,
            },
        },
        "results": result_sets,
        "reference_reproduction_check": {
            "prior_reference": "evidence/holdout_h49_currentprotocol_20261007.json",
            "checks": h49_crosscheck,
            "all_pass": bool(all(item["exact_within_1e_12"] for item in h49_crosscheck.values())),
        },
        "paired_H58_minus_H49": deltas,
        "necessary_gate": {
            "rule": "H58 must have positive mean paired delta and >=3/4 positive folds against H49 on both primary proxy targets",
            "catalogue_pass": primary_gates[0],
            "newer_sgmc_off_catalogue_pass": primary_gates[1],
            "passes_both": passed,
            "weekly_slot_authorized": False,
            "reason": "Public proxy performance cannot by itself authorize a weekly competition slot; the H58 candidate must at minimum beat current H49 on both matched targets. No private-label or organizer score evidence exists.",
        },
        "limitation": "These are conditional public-proxy scores, not a leaderboard projection, hidden-test result, or proof of geological discovery. The SGMC derivation has a separately documented raster discrepancy; raw-SGMC sensitivity is reported separately.",
    }
    OUTPUT.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "candidate": report["candidate"],
        "paired_H58_minus_H49": deltas,
        "necessary_gate": report["necessary_gate"],
        "output": str(OUTPUT.relative_to(ROOT)),
    }, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
