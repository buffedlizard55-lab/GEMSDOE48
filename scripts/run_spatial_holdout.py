#!/usr/bin/env python3
"""Run four fixed spatial-block DTI diagnostics against owner-mirror catalogue labels.

The output is explicitly a conditional proxy test, not a private-label validation. The
source candidate TIFs are frozen owner mirrors and are not rebuilt independently per fold.
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
    """Include a Euclidean radius halo around the held-out rectangle, then mask footprint."""
    d_to_core = distance_transform_edt(~core, sampling=(100.0, 100.0))
    return (d_to_core <= radius_m) & footprint


def score_fold(
    prediction: np.ndarray,
    labels: np.ndarray,
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
    local_truth = (labels[sl] > 0) & local_core
    local_prediction = np.where(local_domain, prediction[sl], 0.0).astype(np.float32)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--labels", type=Path, default=ROOT / "data/proxy/labels.tif")
    parser.add_argument("--footprint", type=Path, default=ROOT / "data/source_mirrors/footprint-mask.tif")
    parser.add_argument("--dotted", type=Path, default=ROOT / "data/source_mirrors/gemsdoe32-h33-h33-2-b2.tif")
    parser.add_argument("--tip", type=Path, default=ROOT / "data/source_mirrors/GEMSDOE33-h33d-tip-stepover.tif")
    parser.add_argument("--combined", type=Path, default=ROOT / "docs/downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/holdout_20261006.json")
    parser.add_argument("--allow-unpinned-labels", action="store_true")
    parser.add_argument("--allow-unpinned-sources", action="store_true")
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
    labels, label_profile = read(args.labels)
    dotted, dotted_profile = read(args.dotted)
    tip, tip_profile = read(args.tip)
    combined, combined_profile = read(args.combined)
    for profile, path in ((dotted_profile, args.dotted), (tip_profile, args.tip), (combined_profile, args.combined)):
        assert_same_grid(label_profile, profile, name_a=str(args.labels), name_b=str(path))
    with rasterio.open(args.footprint) as ds:
        assert_competition_grid(ds.profile, path=args.footprint)
        footprint_raw = ds.read(1)
    footprint = footprint_raw == 1
    if labels.shape != footprint.shape:
        raise SystemExit("label and footprint dimensions do not match")
    if label_hash == EXPECTED_LABEL_SHA256 and int(np.count_nonzero((labels > 0) & footprint)) != EXPECTED_LABEL_POSITIVES:
        raise SystemExit("registered label mirror positive count did not match its receipt")

    dotted = np.where(footprint, dotted, 0.0).astype(np.float32)
    tip = np.where(footprint, tip, 0.0).astype(np.float32)
    combined = np.where(footprint, combined, 0.0).astype(np.float32)
    mean = arithmetic_mean(dotted, tip)
    candidates = {"dotted": dotted, "tip_stepover": tip, "arithmetic_mean": mean, "dempster_combined": combined}
    blocks = quadrants(*labels.shape)
    results: dict[str, dict] = {}
    for candidate_name, prediction in candidates.items():
        results[candidate_name] = {
            fold_name: score_fold(prediction, labels, footprint, core)
            for fold_name, core in blocks.items()
        }
        fold_scores = [float(results[candidate_name][name]["dti"]) for name in blocks]
        results[candidate_name]["mean_dti"] = float(np.mean(fold_scores))

    gate: dict[str, dict] = {}
    for comparator in ("dotted", "tip_stepover"):
        deltas = {
            fold: float(results["dempster_combined"][fold]["dti"] - results[comparator][fold]["dti"])
            for fold in blocks
        }
        gate[comparator] = {
            "fold_delta_dti": deltas,
            "mean_delta_dti": float(np.mean(list(deltas.values()))),
            "positive_folds": int(sum(value > 0 for value in deltas.values())),
            "passes_numeric_gate": bool(np.mean(list(deltas.values())) > 0 and sum(value > 0 for value in deltas.values()) >= 3),
        }

    delta_to_mean = {
        fold: float(results["dempster_combined"][fold]["dti"] - results["arithmetic_mean"][fold]["dti"])
        for fold in blocks
    }
    comparison_to_mean = {
        "fold_delta_dti": delta_to_mean,
        "mean_delta_dti": float(np.mean(list(delta_to_mean.values()))),
        "positive_folds": int(sum(value > 0 for value in delta_to_mean.values())),
    }

    source_leakage = (
        "These surfaces are frozen upstream owner mirrors and are not reconstructed inside each fold. "
        "The H33-2-B2 owner audit describes deleting predictions within 200 m of the full catalogue; "
        "therefore withheld catalogue geometry was available to source construction. The measurements "
        "are conditional diagnostics, not a leakage-free model validation."
    )
    report = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "CONDITIONAL_SPATIAL_BLOCK_DIAGNOSTIC_NOT_SLOT_CLEARED",
        "source_inputs": {
            "dotted": {"path": display_path(args.dotted), "sha256": dotted_hash},
            "tip_stepover": {"path": display_path(args.tip), "sha256": tip_hash},
            "combined": {"path": display_path(args.combined), "sha256": sha256_file(args.combined)},
        },
        "truth_source": {
            "path": display_path(args.labels),
            "sha256": label_hash,
            "class": "owner-mirror of existing public USGS/INGENIOUS catalogue labels",
            "organizer_authenticated": False,
            "positive_pixels": int(np.count_nonzero((labels > 0) & footprint)),
            "is_private_expert_test_truth": False,
        },
        "fold_protocol": {
            "geometry": "Four fixed 2x2 geographic quadrants on the full EPSG:32611 grid.",
            "metric": "Official distance-weighted Tversky equations; alpha=0.2, beta=0.8, triangular radius=300 m.",
            "evaluation_domain": "Held-out quadrant plus a 300 m Euclidean halo, clipped to the finite survey footprint.",
            "candidate_retraining": False,
            "leakage_limitation": source_leakage,
        },
        "results": results,
        "paired_gate_vs_each_input": gate,
        "paired_comparison_vs_arithmetic_mean": comparison_to_mean,
        "slot_decision": {
            "cleared": False,
            "reason": "The frozen source surfaces were not rebuilt fold-by-fold and are not independent of the full catalogue; a numeric proxy result cannot clear a competition slot.",
        },
        "caveats": [
            "The mirrored labels are visible catalogue faults, not the private expert-labelled competition target.",
            "Owner mirrors are not organizer-authenticated.",
            "Sample submission values were not used as truth; only the derived finite footprint mask is used.",
            "No leaderboard or competition score is estimated by this holdout.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
