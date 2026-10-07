#!/usr/bin/env python3
"""Blocked-holdout diagnostics for the H50-B alteration-conflict probe.

Identical fold geometry, evaluation domain (held-out quadrant + 300 m halo),
truth sources and official metric call as ``scripts/holdout_ds50.py`` /
``scripts/holdout_h51.py`` (2026-10-07).  The candidate surface is the
preregistered H50-B emission; comparators are the same frozen set.

Nothing here is private-label evidence or a slot clearance. The frozen
comparator key ``tip_h36_parent`` is a legacy alias for H36-1 rung30
(H19-5/rung-30 repacking), not the actual tip/step-over family.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from gemsdoe48.geotiff import assert_competition_grid, read_band

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "run_spatial_holdout", ROOT / "scripts/run_spatial_holdout.py"
)
rsh = importlib.util.module_from_spec(_spec)
sys.modules["run_spatial_holdout"] = rsh
_spec.loader.exec_module(rsh)  # type: ignore[union-attr]

DOTTED = ROOT / "data/raw/dotted_h33_2_b2_zeros.tif"
TIP_H36 = ROOT / "data/source_mirrors/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"
LABELS = ROOT / "data/raw/labels_catalogue.tif"
SGMC = ROOT / "data/official/derived_sgmc_faults_100m.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
H49 = ROOT / "docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-e6f08013888b.tif"

_h50b = sorted((ROOT / "docs/downloads").glob("gemsdoe48-h50b-alteration-conflict-*-zeros.tif"))
if not _h50b:
    raise SystemExit("no H50-B primary found; run scripts/build_h50b_probe.py first")
H50B_PRIMARY = _h50b[-1]
_h51 = sorted((ROOT / "docs/downloads").glob("gemsdoe48-h51-plausibility-budget-*-zeros.tif"))
H51_PRIMARY = _h51[-1] if _h51 else None

PINNED = {
    DOTTED: rsh.EXPECTED_DOTTED_SHA256,
    TIP_H36: "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641",
    LABELS: rsh.EXPECTED_LABEL_SHA256,
    SGMC: rsh.EXPECTED_SGMC_SHA256,
    FOOTPRINT: "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
    H49: "e6f08013888b625db7d187d79bb75ba36c45d068081b77a3dd405ab7eec3d472",
}


def finite(values: np.ndarray) -> np.ndarray:
    return np.where(np.isfinite(values), values, 0.0).astype(np.float64)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/holdout_h50b_20261007.json")
    args = parser.parse_args()

    for path, expected in PINNED.items():
        got = rsh.sha256_file(path)
        if got != expected:
            raise SystemExit(f"pin violation: {path} sha {got} != {expected}")

    labels, label_profile = read_band(LABELS)
    sgmc_values, sgmc_profile = read_band(SGMC)
    dotted_raw, dotted_profile = read_band(DOTTED)
    tip_h36_raw, tip_h36_profile = read_band(TIP_H36)
    h50b_raw, h50b_profile = read_band(H50B_PRIMARY)
    h49_raw, h49_profile = read_band(H49)
    with rasterio.open(FOOTPRINT) as fp_ds:
        assert_competition_grid(fp_ds.profile, path=FOOTPRINT)
        footprint = fp_ds.read(1) == 1

    grid_pairs = [
        (sgmc_profile, SGMC), (dotted_profile, DOTTED), (tip_h36_profile, TIP_H36),
        (h50b_profile, H50B_PRIMARY), (h49_profile, H49),
    ]
    h51_raw = None
    if H51_PRIMARY is not None:
        h51_raw, h51_profile = read_band(H51_PRIMARY)
        grid_pairs.append((h51_profile, H51_PRIMARY))
    for prof, path in grid_pairs:
        rsh.assert_same_grid(label_profile, prof, name_a=str(LABELS), name_b=str(path))

    catalogue_truth = (finite(labels) > 0) & footprint
    distance_to_catalogue_m = distance_transform_edt(~catalogue_truth, sampling=(100.0, 100.0))
    sgmc_offcat_truth = (finite(sgmc_values) > 0) & footprint & (distance_to_catalogue_m > 300.0)
    if int(sgmc_offcat_truth.sum()) != rsh.EXPECTED_SGMC_OFFCAT_POSITIVES:
        raise SystemExit(
            f"SGMC off-catalogue positives {int(sgmc_offcat_truth.sum())} != pinned "
            f"{rsh.EXPECTED_SGMC_OFFCAT_POSITIVES}"
        )

    dotted = np.where(footprint, finite(dotted_raw), 0.0)
    tip_h36 = np.where(footprint, finite(tip_h36_raw), 0.0)
    h50b = np.where(footprint, finite(h50b_raw), 0.0)
    h49 = np.where(footprint, finite(h49_raw), 0.0)
    if not np.isin(h50b, (0.0, 1.0)).all():
        raise SystemExit("H50-B primary must be binary")

    candidates = {
        "dotted_b2_parent": dotted,
        "tip_h36_parent": tip_h36,
        "union_decision": np.where(footprint, ((dotted > 0) | (tip_h36 > 0)).astype(np.float64), 0.0),
        "h50b_alteration_conflict": h50b,
        "h49_yager_pignistic_budget": h49,
    }
    if h51_raw is not None:
        candidates["h51_plausibility_budget"] = np.where(footprint, finite(h51_raw), 0.0)

    blocks = rsh.quadrants(*labels.shape)
    results_cat = rsh.score_surface_set(candidates, catalogue_truth, footprint, blocks)
    results_sgmc = rsh.score_surface_set(candidates, sgmc_offcat_truth, footprint, blocks)

    def gate_block(results: dict) -> dict:
        return {
            base: rsh.paired_delta(results, "h50b_alteration_conflict", base, blocks)
            for base in candidates
            if base != "h50b_alteration_conflict"
        }

    gate_sgmc = gate_block(results_sgmc)
    gate_cat = gate_block(results_cat)
    numeric_pass = (
        gate_sgmc["h49_yager_pignistic_budget"]["positive_folds"] >= 3
        and gate_cat["union_decision"]["positive_folds"] >= 3
    )

    report = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "NUMERIC_GATE_PASSED_PROXY_ONLY_NOT_SLOT_CLEARED"
            if numeric_pass
            else "NEGATIVE_RESULT_SPATIAL_BLOCK_DIAGNOSTIC_NOT_SLOT_CLEARED"
        ),
        "hypothesis_id": "H50-B",
        "candidate": {
            "name": "h50b_alteration_conflict",
            "path": str(H50B_PRIMARY.relative_to(ROOT)),
            "sha256": rsh.sha256_file(H50B_PRIMARY),
            "preregistration": "evidence/h50b_preregistration_20261007.json",
        },
        "fold_protocol": {
            "geometry": "Four fixed 2x2 geographic quadrants (identical to run_spatial_holdout.py).",
            "metric": "Official distance-weighted Tversky; alpha=0.2, beta=0.8, 300 m triangular kernel.",
            "evaluation_domain": "Held-out quadrant plus 300 m halo, clipped to footprint; core-only truth.",
            "candidate_retraining": False,
            "leakage_limitation": (
                "Construction uses no fold truth; global footprint statistics only. The dotted "
                "parent's conflict layer inherits its catalogue-flank pruning (documented upstream)."
            ),
        },
        "truth_sources": {
            "catalogue": {
                "sha256": rsh.sha256_file(LABELS),
                "positive_pixels": int(catalogue_truth.sum()),
                "class": "owner-mirror of public USGS/INGENIOUS catalogue labels; not the private test truth",
            },
            "sgmc_off_catalogue_gt_300m": {
                "sha256": rsh.sha256_file(SGMC),
                "positive_pixels": int(sgmc_offcat_truth.sum()),
                "class": "owner-mirror rasterization of USGS SGMC fault traces, >300 m from catalogue",
            },
        },
        "catalogue_proxy_results": results_cat,
        "sgmc_offcat_results": results_sgmc,
        "catalogue_paired_gates": {"h50b_alteration_conflict": gate_cat},
        "sgmc_paired_gates": {"h50b_alteration_conflict": gate_sgmc},
        "numeric_gate": {
            "rule": "beat H49 on SGMC offcat and union on catalogue in >=3/4 folds each",
            "sgmc_vs_h49_positive_folds": gate_sgmc["h49_yager_pignistic_budget"]["positive_folds"],
            "sgmc_vs_h49_mean_delta": gate_sgmc["h49_yager_pignistic_budget"]["mean_delta_dti"],
            "catalogue_vs_union_positive_folds": gate_cat["union_decision"]["positive_folds"],
            "catalogue_vs_union_mean_delta": gate_cat["union_decision"]["mean_delta_dti"],
            "passed": bool(numeric_pass),
        },
        "slot_decision": {
            "cleared": False,
            "reason": (
                "Public-map proxy targets only; no organizer receipt. A numeric proxy win "
                "would still not be private-label evidence."
            ),
        },
        "caveats": [
            "Radiometric mirror is uint8 per-channel percentile-quantised; the Th/K ratio is ordinal, not physical units.",
            "Alteration is a lithology proxy; the corridor gate supplies the structural hypothesis.",
            "Catalogue and SGMC proxies are not the private expert-labelled target.",
            "No leaderboard score is estimated here.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    def summarize(results: dict, label: str) -> None:
        print(f"--- {label} mean DTI ---")
        for name in results:
            print(f"  {name:36s} {results[name]['mean_dti']:.6f}")

    summarize(results_cat, "catalogue proxy")
    summarize(results_sgmc, "SGMC off-catalogue proxy")
    print("numeric gate passed:", numeric_pass)
    print(json.dumps({"written": [str(args.output)]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
