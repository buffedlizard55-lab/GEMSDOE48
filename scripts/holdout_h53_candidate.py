#!/usr/bin/env python3
"""Score the frozen H53 candidate on the repository's spatially blocked proxies.

The same fixed four-quadrant/core-plus-300 m-halo protocol is used for the newer
SGMC primary proxy, older raw-SGMC sensitivity, and catalogue proxy. Public owner-
mirror surfaces are frozen upstream and may leak public catalogue geometry; this is
conditional validation, not a private-label estimate or slot clearance.
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
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48.geotiff import assert_competition_grid, assert_same_grid, display_path, read_band  # noqa: E402

_spec = importlib.util.spec_from_file_location("run_spatial_holdout", ROOT / "scripts/run_spatial_holdout.py")
rsh = importlib.util.module_from_spec(_spec)
sys.modules["run_spatial_holdout"] = rsh
_spec.loader.exec_module(rsh)  # type: ignore[union-attr]

B2 = ROOT / "data/families/dotted_b2_prune_02778.tif"
H33D = ROOT / "data/families/tip_stepover_r30_02632.tif"
LABELS = ROOT / "data/raw/labels_catalogue.tif"
SGMC_NEW = ROOT / "data/official/derived_sgmc_faults_100m.tif"
SGMC_OLD = ROOT / "data/raw/sgmc_faults_100m.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
H49 = ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif"
BUILD_RECEIPT = ROOT / "evidence/build_h53_receipt_20261007.json"

PINS = {
    B2: "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    H33D: "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
    LABELS: "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    SGMC_NEW: "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
    SGMC_OLD: "26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c",
    FOOTPRINT: "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
    H49: "9f028289c364c071065245799d7ed131600e80e9f0d10602806b12ce34d7cae8",
}
EXPECTED_TARGET_CELLS = {SGMC_NEW: 62_122, SGMC_OLD: 61_664}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def finite(values: np.ndarray) -> np.ndarray:
    return np.where(np.isfinite(values), values, 0.0).astype(np.float64)


def read_grid(path: Path) -> tuple[np.ndarray, dict]:
    array, profile = read_band(path)
    assert_competition_grid(profile, path=path)
    return array, profile


def compare_to(results: dict, candidate: str, base: str, blocks: dict) -> dict:
    return rsh.paired_delta(results, candidate, base, blocks)


def mean_result(results: dict, name: str) -> float:
    return float(results[name]["mean_dti"])


def main() -> int:
    receipt = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    candidate_path = ROOT / receipt["candidate"]["path"]
    short_id = receipt["candidate"]["unique_submission_name"].rsplit("-", 1)[-1]
    base = f"GEMSDOE48-H53-DS-RadEdge-B2xH33D-20261007-{short_id}"
    diagnostic_dir = ROOT / "docs/downloads/diagnostics"
    diagnostic_paths = {
        "two_family_dempster_no_radiometry": (
            "two_family_dempster_only", diagnostic_dir / f"{base}-two-family-dempster-only.tif"
        ),
        "two_family_naive_mean": (
            "two_family_naive_mean", diagnostic_dir / f"{base}-two-family-naive-mean.tif"
        ),
    }

    for path, expected in PINS.items():
        got = sha256_file(path)
        if got != expected:
            raise SystemExit(f"pin violation: {path}: {got} != {expected}")
    if sha256_file(candidate_path) != receipt["candidate"]["sha256"]:
        raise SystemExit("H53 candidate bytes no longer match the build receipt")
    for candidate_name, (receipt_key, path) in diagnostic_paths.items():
        info = receipt["diagnostics"][receipt_key]
        if sha256_file(path) != info["sha256"]:
            raise SystemExit(f"H53 diagnostic SHA mismatch: {candidate_name}")

    labels, label_profile = read_grid(LABELS)
    sgmc_new, new_profile = read_grid(SGMC_NEW)
    sgmc_old, old_profile = read_grid(SGMC_OLD)
    dotted, b2_profile = read_grid(B2)
    h33d, h33d_profile = read_grid(H33D)
    h49, h49_profile = read_grid(H49)
    candidate, candidate_profile = read_grid(candidate_path)
    for profile, path in (
        (new_profile, SGMC_NEW), (old_profile, SGMC_OLD), (b2_profile, B2),
        (h33d_profile, H33D), (h49_profile, H49), (candidate_profile, candidate_path),
    ):
        assert_same_grid(label_profile, profile, name_a=str(LABELS), name_b=str(path))
    with rasterio.open(FOOTPRINT) as dataset:
        assert_competition_grid(dataset.profile, path=FOOTPRINT)
        footprint = dataset.read(1) == 1
    if int(footprint.sum()) != 5_167_373:
        raise SystemExit("footprint count changed from the pinned source receipt")

    catalogue_truth = (finite(labels) > 0) & footprint
    distance_to_catalogue = distance_transform_edt(~catalogue_truth, sampling=(100.0, 100.0))
    dotted_b2 = np.where(footprint, finite(dotted), 0.0)
    h33d_parent = np.where(footprint, finite(h33d), 0.0)
    h49_best = np.where(footprint, finite(h49), 0.0)
    h53_prediction = np.where(footprint, finite(candidate), 0.0)

    baselines = {
        "h49_current_blocked_best": h49_best,
        "dotted_b2_parent": dotted_b2,
        "h33d_tip_stepover_parent": h33d_parent,
        "binary_union": np.where(footprint, ((dotted_b2 > 0) | (h33d_parent > 0)).astype(np.float64), 0.0),
    }
    for name, (_receipt_key, path) in diagnostic_paths.items():
        values, profile = read_grid(path)
        assert_same_grid(label_profile, profile, name_a=str(LABELS), name_b=str(path))
        baselines[name] = np.where(footprint, finite(values), 0.0)
    candidates = {"h53_dempster_radiometric_edge": h53_prediction, **baselines}

    blocks = rsh.quadrants(*labels.shape)
    catalogue_results = rsh.score_surface_set(candidates, catalogue_truth, footprint, blocks)
    targets: dict[str, tuple[np.ndarray, Path]] = {}
    for path, values in ((SGMC_NEW, sgmc_new), (SGMC_OLD, sgmc_old)):
        target = (finite(values) > 0) & footprint & (distance_to_catalogue > 300.0)
        count = int(target.sum())
        if count != EXPECTED_TARGET_CELLS[path]:
            raise SystemExit(f"off-catalogue target changed for {path}: {count} != {EXPECTED_TARGET_CELLS[path]}")
        targets[path.name] = (target, path)

    target_results = {}
    for label, (target, _path) in targets.items():
        target_results[label] = rsh.score_surface_set(candidates, target, footprint, blocks)

    comparison_names = [
        "h49_current_blocked_best",
        "dotted_b2_parent",
        "h33d_tip_stepover_parent",
        "binary_union",
        "two_family_dempster_no_radiometry",
        "two_family_naive_mean",
    ]
    primary_label = SGMC_NEW.name
    older_label = SGMC_OLD.name
    primary = target_results[primary_label]
    older = target_results[older_label]
    primary_deltas = {name: compare_to(primary, "h53_dempster_radiometric_edge", name, blocks) for name in comparison_names}
    older_deltas = {name: compare_to(older, "h53_dempster_radiometric_edge", name, blocks) for name in comparison_names}
    catalogue_deltas = {name: compare_to(catalogue_results, "h53_dempster_radiometric_edge", name, blocks) for name in comparison_names}

    gate = {
        "newer_sgmc_mean_delta_vs_h49": primary_deltas["h49_current_blocked_best"]["mean_delta_dti"],
        "newer_sgmc_positive_folds_vs_h49": primary_deltas["h49_current_blocked_best"]["positive_folds"],
        "older_sgmc_mean_delta_vs_h49": older_deltas["h49_current_blocked_best"]["mean_delta_dti"],
        "older_sgmc_positive_folds_vs_h49": older_deltas["h49_current_blocked_best"]["positive_folds"],
        "newer_sgmc_gain_vs_two_family_dempster": primary_deltas["two_family_dempster_no_radiometry"]["mean_delta_dti"],
        "newer_sgmc_gain_vs_two_family_mean": primary_deltas["two_family_naive_mean"]["mean_delta_dti"],
    }
    gate["passes_preregistered_proxy_gate"] = bool(
        gate["newer_sgmc_mean_delta_vs_h49"] >= 0.005
        and gate["newer_sgmc_positive_folds_vs_h49"] >= 3
        and gate["older_sgmc_mean_delta_vs_h49"] > 0.0
        and gate["older_sgmc_positive_folds_vs_h49"] >= 3
        and gate["newer_sgmc_gain_vs_two_family_dempster"] > 0.0
        and gate["newer_sgmc_gain_vs_two_family_mean"] > 0.0
    )

    report = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "CONDITIONAL_BLOCKED_PUBLIC_PROXY_RESULT_NOT_ORGANIZER_EVIDENCE",
        "preregistration": "evidence/h53_preregistration_20261007.json",
        "candidate": {
            "name": receipt["candidate"]["unique_submission_name"],
            "path": display_path(candidate_path),
            "sha256": sha256_file(candidate_path),
            "build_receipt": "evidence/build_h53_receipt_20261007.json",
        },
        "source_hashes": {path.name: sha256_file(path) for path in PINS},
        "fold_protocol": {
            "implementation": "scripts/run_spatial_holdout.py quadrant, fold-domain, and distance-weighted Tversky functions",
            "geometry": "four fixed geographic 2x2 quadrants on the full 3292x3730 EPSG:32611 grid",
            "evaluation_domain": "held-out quadrant plus 300 m Euclidean halo, clipped to footprint; truth in core only",
            "metric": "official triangular distance kernel, 300 m, alpha=0.2, beta=0.8",
            "candidate_retraining": False,
            "holdout_parameter_tuning": False,
            "leakage": "Frozen owner-mirror surfaces; B2 was catalogue-flank-pruned with full public-catalogue geometry, and no family surface was rebuilt inside each fold. Results are conditional and potentially leaky.",
        },
        "truth_sources": {
            "catalogue_proxy": {"sha256": sha256_file(LABELS), "positive_cells_in_footprint": int(catalogue_truth.sum()), "private_test_truth": False},
            "newer_sgmc_off_catalogue": {"sha256": sha256_file(SGMC_NEW), "positive_cells_gt_300m": int(((finite(sgmc_new) > 0) & footprint & (distance_to_catalogue > 300.0)).sum()), "private_test_truth": False},
            "older_raw_sgmc_off_catalogue": {"sha256": sha256_file(SGMC_OLD), "positive_cells_gt_300m": int(((finite(sgmc_old) > 0) & footprint & (distance_to_catalogue > 300.0)).sum()), "private_test_truth": False},
        },
        "candidate_set": {
            "h53_dempster_radiometric_edge": "H53 primary normalized Bel(F), B2/H33-D family BPAs plus weak GeoDAWN multiband-edge BPA",
            "h49_current_blocked_best": "same-grid H49 format-audited raster; current public SGMC proxy best (0.100751188 newer-SGMC mean)",
            "dotted_b2_parent": "binary B2 committed pixels",
            "h33d_tip_stepover_parent": "binary H33-D committed pixels",
            "binary_union": "binary union of B2 and H33-D",
            "two_family_dempster_no_radiometry": "H53 support-geometry B2 x H33-D Dempster baseline, same reliability parameters, no radiometric BPA",
            "two_family_naive_mean": "mean of the two 300 m kernel-support surfaces",
        },
        "catalogue_proxy_results": catalogue_results,
        "newer_sgmc_off_catalogue_results": primary,
        "older_raw_sgmc_sensitivity_results": older,
        "paired_deltas_newer_sgmc": primary_deltas,
        "paired_deltas_older_sgmc": older_deltas,
        "paired_deltas_catalogue_proxy": catalogue_deltas,
        "preregistered_gate": gate,
        "slot_decision": {
            "cleared": False,
            "reason": "Public catalogue/SGMC proxies are not private organizer labels; H53 has no organizer file-score receipt. Do not spend a weekly slot based on this report.",
        },
        "limitations": [
            "No organizer score or leaderboard improvement is estimated or claimed.",
            "Both evaluation targets are public-map proxies and share mapping/coverage bias with the catalogue used to prune B2.",
            "The H49 comparator is a post-selection proxy best; this same-protocol comparison is not an independent blind confirmation.",
            "The source families overlap heavily and were not rebuilt independently inside the spatial folds.",
            "A failed proxy gate does not prove zero private-label utility; a passed proxy gate would not establish organizer value.",
        ],
    }
    output = ROOT / "evidence/holdout_h53_20261007.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    receipt["candidate"]["holdout_status"] = (
        "PROXY_GATE_PASSED_NOT_SLOT_CLEARED" if gate["passes_preregistered_proxy_gate"] else "FAILED_PREREGISTERED_PROXY_GATE"
    )
    receipt["candidate"]["holdout_report"] = display_path(output)
    receipt["candidate"]["slot_cleared"] = False
    receipt["candidate"]["proxy_gate_summary"] = gate
    BUILD_RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "candidate": report["candidate"], "gate": gate, "newer_sgmc": {key: value["mean_dti"] for key, value in primary.items()}, "older_sgmc": {key: value["mean_dti"] for key, value in older.items()}, "catalogue": {key: value["mean_dti"] for key, value in catalogue_results.items()}, "report": display_path(output)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
