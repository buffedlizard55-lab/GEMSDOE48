#!/usr/bin/env python3
"""Run four fixed spatial-block diagnostics on two public fault-label proxies.

Both truth sources are owner-mirror products, not private expert labels. The input
candidate surfaces are frozen upstream outputs and are not rebuilt independently per
fold, so all results are conditional and potentially leaky.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from gemsdoe48.evidence import arithmetic_mean, combine_dempster
from gemsdoe48.geotiff import assert_competition_grid, assert_same_grid, display_path
from gemsdoe48.metric import distance_weighted_tversky

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LABEL_SHA256 = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
EXPECTED_LABEL_POSITIVES = 60_988
EXPECTED_DOTTED_SHA256 = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
EXPECTED_TIP_SHA256 = "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"
EXPECTED_SGMC_SHA256 = "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"
EXPECTED_SGMC_OFFCAT_POSITIVES = 62_122
EXPECTED_YAGER_SHA256 = "fe68ae6f57be013e26d20006551b43cd84bb5fe4a0b07d1d10ce4725c90fd16c"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as ds:
        assert_competition_grid(ds.profile, path=path)
        return ds.read(1), ds.profile.copy()


def quadrants(height: int, width: int) -> dict[str, np.ndarray]:
    mid_y, mid_x = height // 2, width // 2
    rows, cols = np.indices((height, width))
    north = rows < mid_y
    west = cols < mid_x
    return {
        "NW": north & west,
        "NE": north & ~west,
        "SW": ~north & west,
        "SE": ~north & ~west,
    }


def fold_domain(core: np.ndarray, footprint: np.ndarray, radius_m: float = 300.0) -> np.ndarray:
    """Return the held-out rectangle plus a Euclidean score-kernel halo."""
    distance_to_core = distance_transform_edt(~core, sampling=(100.0, 100.0))
    return (distance_to_core <= radius_m) & footprint


def score_fold(
    prediction: np.ndarray,
    truth_mask: np.ndarray,
    footprint: np.ndarray,
    core: np.ndarray,
    *,
    radius_m: float = 300.0,
) -> dict[str, float | int]:
    domain = fold_domain(core, footprint, radius_m)
    rows, cols = np.nonzero(domain)
    if rows.size == 0:
        raise ValueError("spatial fold has no valid cells")
    r0, r1 = max(0, int(rows.min())), min(domain.shape[0], int(rows.max()) + 1)
    c0, c1 = max(0, int(cols.min())), min(domain.shape[1], int(cols.max()) + 1)
    sl = (slice(r0, r1), slice(c0, c1))
    local_domain = domain[sl]
    local_core = core[sl]
    local_truth = truth_mask[sl] & local_core
    local_prediction = np.where(local_domain, prediction[sl], 0.0).astype(np.float64)
    result = distance_weighted_tversky(
        local_prediction,
        local_truth,
        valid=local_domain,
        radius_m=radius_m,
        pixel_size_m=100.0,
        alpha=0.2,
        beta=0.8,
    )
    result["prediction_mass"] = float(local_prediction[local_domain].sum(dtype=np.float64))
    result["positive_cells"] = int(np.count_nonzero(local_prediction[local_domain] > 0.0))
    result["valid_domain_cells"] = int(local_domain.sum())
    return result


def score_surface_set(
    candidates: dict[str, np.ndarray],
    truth_mask: np.ndarray,
    footprint: np.ndarray,
    blocks: dict[str, np.ndarray],
) -> dict[str, dict]:
    results: dict[str, dict] = {}
    for candidate_name, prediction in candidates.items():
        results[candidate_name] = {
            fold_name: score_fold(prediction, truth_mask, footprint, core)
            for fold_name, core in blocks.items()
        }
        fold_scores = [float(results[candidate_name][name]["dti"]) for name in blocks]
        results[candidate_name]["mean_dti"] = float(np.mean(fold_scores))
    return results


def paired_delta(
    results: dict[str, dict],
    candidate: str,
    comparator: str,
    blocks: dict[str, np.ndarray],
) -> dict[str, dict | float | int | bool]:
    deltas = {
        fold: float(results[candidate][fold]["dti"] - results[comparator][fold]["dti"])
        for fold in blocks
    }
    mean_delta = float(np.mean(list(deltas.values())))
    positive_folds = int(sum(value > 0 for value in deltas.values()))
    return {
        "fold_delta_dti": deltas,
        "mean_delta_dti": mean_delta,
        "positive_folds": positive_folds,
        "passes_numeric_gate": bool(mean_delta > 0 and positive_folds >= 3),
    }


def paired_comparisons(
    results: dict[str, dict],
    blocks: dict[str, np.ndarray],
    candidate: str = "dempster_combined",
) -> tuple[dict, dict]:
    gate = {
        comparator: paired_delta(results, candidate, comparator, blocks)
        for comparator in ("dotted", "tip_stepover")
    }
    return gate, paired_delta(results, candidate, "arithmetic_mean", blocks)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=ROOT / "data/raw/labels_catalogue.tif")
    parser.add_argument("--sgmc", type=Path, default=ROOT / "data/official/derived_sgmc_faults_100m.tif")
    parser.add_argument("--footprint", type=Path, default=ROOT / "data/source_mirrors/footprint-mask.tif")
    parser.add_argument("--dotted", type=Path, default=ROOT / "data/raw/dotted_h33_2_b2_zeros.tif")
    parser.add_argument("--tip", type=Path, default=ROOT / "data/raw/tip_h33d_stepover.tif")
    parser.add_argument("--combined", type=Path, default=ROOT / "docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif")
    parser.add_argument(
        "--yager", type=Path, default=None,
        help="optional historical Yager-rule raster; if supplied, it is scored on the identical folds",
    )
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/holdout_20261006.json")
    parser.add_argument("--allow-unpinned-labels", action="store_true")
    parser.add_argument("--allow-unpinned-sgmc", action="store_true")
    parser.add_argument("--allow-unpinned-sources", action="store_true")
    parser.add_argument("--allow-unpinned-yager", action="store_true")
    args = parser.parse_args()

    dotted_hash = sha256_file(args.dotted)
    tip_hash = sha256_file(args.tip)
    if not args.allow_unpinned_sources:
        if dotted_hash != EXPECTED_DOTTED_SHA256:
            raise SystemExit(f"Dotted input SHA-256 {dotted_hash} is not the registered source")
        if tip_hash != EXPECTED_TIP_SHA256:
            raise SystemExit(f"Tip/stepover input SHA-256 {tip_hash} is not the registered source")
    label_hash = sha256_file(args.labels)
    if label_hash != EXPECTED_LABEL_SHA256 and not args.allow_unpinned_labels:
        raise SystemExit(f"Label SHA-256 {label_hash} is not the registered public mirror")
    sgmc_hash = sha256_file(args.sgmc)
    if sgmc_hash != EXPECTED_SGMC_SHA256 and not args.allow_unpinned_sgmc:
        raise SystemExit(f"SGMC raster SHA-256 {sgmc_hash} is not the registered mirror")

    labels, label_profile = read(args.labels)
    sgmc_values, sgmc_profile = read(args.sgmc)
    dotted, dotted_profile = read(args.dotted)
    tip, tip_profile = read(args.tip)
    combined, combined_profile = read(args.combined)
    yager = None
    yager_profile = None
    yager_hash = None
    if args.yager is not None:
        yager_hash = sha256_file(args.yager)
        if yager_hash != EXPECTED_YAGER_SHA256 and not args.allow_unpinned_yager:
            raise SystemExit(f"Yager raster SHA-256 {yager_hash} is not the registered historical candidate")
        yager, yager_profile = read(args.yager)
    profiles_and_paths = [
        (sgmc_profile, args.sgmc), (dotted_profile, args.dotted),
        (tip_profile, args.tip), (combined_profile, args.combined),
    ]
    if yager_profile is not None:
        profiles_and_paths.append((yager_profile, args.yager))
    for profile, path in profiles_and_paths:
        assert_same_grid(label_profile, profile, name_a=str(args.labels), name_b=str(path))
    with rasterio.open(args.footprint) as ds:
        assert_competition_grid(ds.profile, path=args.footprint)
        footprint_raw = ds.read(1)
    footprint = footprint_raw == 1
    if labels.shape != footprint.shape or sgmc_values.shape != footprint.shape:
        raise SystemExit("label, SGMC, and footprint dimensions do not match")
    if label_hash == EXPECTED_LABEL_SHA256 and int(np.count_nonzero((labels > 0) & footprint)) != EXPECTED_LABEL_POSITIVES:
        raise SystemExit("registered label mirror positive count did not match its receipt")

    catalogue_truth = (labels > 0) & footprint
    distance_to_catalogue_m = distance_transform_edt(~catalogue_truth, sampling=(100.0, 100.0))
    sgmc_offcat_truth = (sgmc_values > 0) & footprint & (distance_to_catalogue_m > 300.0)
    sgmc_offcat_count = int(sgmc_offcat_truth.sum())
    if sgmc_hash == EXPECTED_SGMC_SHA256 and sgmc_offcat_count != EXPECTED_SGMC_OFFCAT_POSITIVES:
        raise SystemExit(
            f"Registered SGMC off-catalogue mask has {sgmc_offcat_count} pixels; "
            f"expected {EXPECTED_SGMC_OFFCAT_POSITIVES}"
        )

    dotted = np.where(footprint, dotted, 0.0).astype(np.float64)
    tip = np.where(footprint, tip, 0.0).astype(np.float64)
    combined = np.where(footprint, combined, 0.0).astype(np.float64)
    prior_ds_099 = combine_dempster(dotted, tip, reliability=0.99).fault
    prior_max = float(prior_ds_099[footprint].max())
    prior_belief_099 = np.where(footprint, prior_ds_099 / prior_max if prior_max > 0 else 0.0, 0.0)
    prior_union = np.where(footprint, (dotted > 0) | (tip > 0), 0.0).astype(np.float64)
    candidates = {
        "dotted": dotted,
        "tip_stepover": tip,
        "arithmetic_mean": 0.5 * (dotted + tip),
        "prior_alpha_099_belief": prior_belief_099.astype(np.float64),
        "prior_union_decision": prior_union,
        "dempster_combined": combined,
    }
    if yager is not None:
        candidates["yager_conflict_transfer"] = np.where(footprint, yager, 0.0).astype(np.float64)

    blocks = quadrants(*labels.shape)
    results = score_surface_set(candidates, catalogue_truth, footprint, blocks)
    gate, comparison_to_mean = paired_comparisons(results, blocks)
    comparison_to_prior_union = paired_delta(results, "dempster_combined", "prior_union_decision", blocks)
    comparison_to_prior_belief = paired_delta(results, "dempster_combined", "prior_alpha_099_belief", blocks)
    sgmc_results = score_surface_set(candidates, sgmc_offcat_truth, footprint, blocks)
    sgmc_gate, sgmc_comparison_to_mean = paired_comparisons(sgmc_results, blocks)
    sgmc_comparison_to_prior_union = paired_delta(sgmc_results, "dempster_combined", "prior_union_decision", blocks)
    sgmc_comparison_to_prior_belief = paired_delta(sgmc_results, "dempster_combined", "prior_alpha_099_belief", blocks)

    alternative_comparisons = {}
    if yager is not None:
        yager_gate, yager_comparison_to_mean = paired_comparisons(
            results, blocks, candidate="yager_conflict_transfer"
        )
        yager_sgmc_gate, yager_sgmc_comparison_to_mean = paired_comparisons(
            sgmc_results, blocks, candidate="yager_conflict_transfer"
        )
        alternative_comparisons["yager_conflict_transfer"] = {
            "paired_gate_vs_each_input": yager_gate,
            "paired_comparison_vs_arithmetic_mean": yager_comparison_to_mean,
            "paired_comparison_vs_prior_alpha_099_belief": paired_delta(
                results, "yager_conflict_transfer", "prior_alpha_099_belief", blocks
            ),
            "paired_comparison_vs_prior_union_decision": paired_delta(
                results, "yager_conflict_transfer", "prior_union_decision", blocks
            ),
            "paired_comparison_vs_rho_0_5_dempster": paired_delta(
                results, "yager_conflict_transfer", "dempster_combined", blocks
            ),
            "sgmc_paired_gate_vs_each_input": yager_sgmc_gate,
            "sgmc_paired_comparison_vs_arithmetic_mean": yager_sgmc_comparison_to_mean,
            "sgmc_paired_comparison_vs_prior_alpha_099_belief": paired_delta(
                sgmc_results, "yager_conflict_transfer", "prior_alpha_099_belief", blocks
            ),
            "sgmc_paired_comparison_vs_prior_union_decision": paired_delta(
                sgmc_results, "yager_conflict_transfer", "prior_union_decision", blocks
            ),
            "sgmc_paired_comparison_vs_rho_0_5_dempster": paired_delta(
                sgmc_results, "yager_conflict_transfer", "dempster_combined", blocks
            ),
            "slot_decision": {
                "cleared": False,
                "reason": "A public-map proxy result cannot clear a private-label slot gate; the Yager alternative is included only as a same-protocol research comparator.",
            },
        }

    source_leakage = (
        "These surfaces are frozen upstream owner mirrors and are not reconstructed inside each fold. "
        "The H33-2-B2 owner audit describes deleting predictions within 200 m of the full catalogue; "
        "therefore catalogue geometry was available during source construction. SGMC faults are filtered "
        "to >300 m from that catalogue, but this does not independently reconstruct or validate the source "
        "models. Both targets remain public-map proxies, not the private expert-labelled set."
    )
    report = {
        "schema_version": 2,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "CONDITIONAL_SPATIAL_BLOCK_DIAGNOSTIC_NOT_SLOT_CLEARED",
        "source_inputs": {
            "dotted": {"path": display_path(args.dotted), "sha256": dotted_hash},
            "tip_stepover": {"path": display_path(args.tip), "sha256": tip_hash},
            "combined": {"path": display_path(args.combined), "sha256": sha256_file(args.combined)},
            **({"yager": {"path": display_path(args.yager), "sha256": yager_hash}} if args.yager is not None else {}),
        },
        "truth_sources": {
            "catalogue": {
                "path": display_path(args.labels),
                "sha256": label_hash,
                "class": "owner-mirror of existing public USGS/INGENIOUS catalogue labels",
                "organizer_authenticated": False,
                "positive_pixels": int(catalogue_truth.sum()),
                "is_private_expert_test_truth": False,
            },
            "sgmc_off_catalogue_gt_300m": {
                "path": display_path(args.sgmc),
                "sha256": sgmc_hash,
                "class": "owner-mirror of an on-grid rasterization of USGS SGMC fault traces",
                "organizer_authenticated": False,
                "positive_pixels": sgmc_offcat_count,
                "definition": "SGMC raster positive and within footprint, with Euclidean distance >300 m from a positive catalogue-label cell.",
                "source_comparison_receipt": "evidence/sgmc_raster_comparison_20261006.json",
                "prior_raw_raster_sensitivity_receipt": "evidence/holdout_raw_sgmc_20261006.json",
                "is_private_expert_test_truth": False,
            },
        },
        "fold_protocol": {
            "geometry": "Four fixed 2x2 geographic quadrants on the full EPSG:32611 grid.",
            "metric": "Official distance-weighted Tversky equations; alpha=0.2, beta=0.8, triangular radius=300 m.",
            "evaluation_domain": "Held-out quadrant plus a 300 m Euclidean halo, clipped to the finite survey footprint; only truth in the core quadrant is scored.",
            "candidate_retraining": False,
            "leakage_limitation": source_leakage,
        },
        "results": results,
        "paired_gate_vs_each_input": gate,
        "paired_comparison_vs_arithmetic_mean": comparison_to_mean,
        "paired_comparison_vs_prior_alpha_099_belief": comparison_to_prior_belief,
        "paired_comparison_vs_prior_union_decision": comparison_to_prior_union,
        "sgmc_off_catalogue_results": sgmc_results,
        "sgmc_paired_gate_vs_each_input": sgmc_gate,
        "sgmc_paired_comparison_vs_arithmetic_mean": sgmc_comparison_to_mean,
        "sgmc_paired_comparison_vs_prior_alpha_099_belief": sgmc_comparison_to_prior_belief,
        "sgmc_paired_comparison_vs_prior_union_decision": sgmc_comparison_to_prior_union,
        "alternative_candidate_comparisons": alternative_comparisons,
        "slot_decision": {
            "cleared": False,
            "reason": "The current rho=0.5 candidate does not improve over both parents on either proxy under the preregistered >=3/4-fold rule; source surfaces are frozen and a proxy pass would still not establish private-label performance.",
        },
        "caveats": [
            "The catalogue and SGMC labels are public map proxies, not the private expert-labelled competition target.",
            "Owner mirrors are not organizer-authenticated; their applicable reuse licenses were not verified.",
            "Source surfaces were not rebuilt independently within folds; results are conditional and potentially leaky.",
            "Two pinned SGMC rasters share the spatial grid but differ in hash, nodata metadata, and 1,450 positive-mask cells; the newer derived raster is primary and the older raw raster has a separate sensitivity report.",
            "Sample submission values were not used as truth; only its derived finite footprint mask is used.",
            "No leaderboard or competition score is estimated by this holdout.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
