#!/usr/bin/env python3
"""Blocked-holdout diagnostics for the H51 plausibility-budget emission.

Identical fold geometry, evaluation domain (held-out quadrant + 300 m halo),
truth sources and official metric call as ``scripts/holdout_ds50.py``
(2026-10-07), so the numbers are directly comparable.  Added comparators: the
H49 Yager/pignistic budget artifact (current proxy best) and the graded
plausibility field (to isolate the binary-vs-graded effect).

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

from gemsdoe48 import ds50, h51
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

_h51 = sorted((ROOT / "docs/downloads").glob("gemsdoe48-h51-plausibility-budget-*-zeros.tif"))
if not _h51:
    raise SystemExit("no H51 primary found; run scripts/build_h51_submission.py first")
H51_PRIMARY = _h51[-1]
_h50 = sorted((ROOT / "docs/downloads").glob("gemsdoe48-h50-ds-b2xh36rung30-*-zeros.tif"))
if not _h50:
    raise SystemExit("no H50 primary found")
H50_PRIMARY = _h50[-1]

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
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/holdout_h51_20261007.json")
    args = parser.parse_args()

    for path, expected in PINNED.items():
        got = rsh.sha256_file(path)
        if got != expected:
            raise SystemExit(f"pin violation: {path} sha {got} != {expected}")

    labels, label_profile = read_band(LABELS)
    sgmc_values, sgmc_profile = read_band(SGMC)
    dotted_raw, dotted_profile = read_band(DOTTED)
    tip_h36_raw, tip_h36_profile = read_band(TIP_H36)
    h51_raw, h51_profile = read_band(H51_PRIMARY)
    h50_raw, h50_profile = read_band(H50_PRIMARY)
    h49_raw, h49_profile = read_band(H49)
    with rasterio.open(FOOTPRINT) as fp_ds:
        assert_competition_grid(fp_ds.profile, path=FOOTPRINT)
        footprint = fp_ds.read(1) == 1

    for prof, path in (
        (sgmc_profile, SGMC), (dotted_profile, DOTTED), (tip_h36_profile, TIP_H36),
        (h51_profile, H51_PRIMARY), (h50_profile, H50_PRIMARY), (h49_profile, H49),
    ):
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
    h51_emission = np.where(footprint, finite(h51_raw), 0.0)
    h50_belief = np.where(footprint, finite(h50_raw), 0.0)
    h49_emission = np.where(footprint, finite(h49_raw), 0.0)
    if not np.isin(h51_emission, (0.0, 1.0)).all():
        raise SystemExit("H51 primary must be binary")

    # Recreate the H50 fusion to obtain the graded plausibility comparator.
    belief_a = ds50.kernel_belief_surface((dotted > 0) & footprint)
    belief_b = ds50.kernel_belief_surface((tip_h36 > 0) & footprint)
    fusion = ds50.dempster_fuse(
        belief_a, belief_b, ds50.RHO_MAX,
        ds50.RHO_MAX * (ds50.LIVE_TIP_H36 / ds50.LIVE_DOTTED_B2),
        footprint=footprint,
    )
    pl_graded = np.where(footprint, fusion.plausibility, 0.0)
    pl_graded = np.where(footprint, pl_graded / pl_graded[footprint].max(), 0.0)
    naive = ds50.naive_mean_belief(belief_a, belief_b)
    naive = np.where(footprint, naive / naive[footprint].max(), 0.0)
    union_decision = np.where(footprint, ((dotted > 0) | (tip_h36 > 0)).astype(np.float64), 0.0)
    budget = int(np.count_nonzero(dotted > 0))
    h50_binary = np.where(
        ds50.top_k_mask(h50_belief, budget, where=footprint), 1.0, 0.0
    ).astype(np.float64)

    candidates = {
        "dotted_b2_parent": dotted,
        "tip_h36_parent": tip_h36,
        "naive_mean_beliefs": naive,
        "union_decision": union_decision,
        "h50_ds_belief": h50_belief,
        "h50_binary_bel_budget": h50_binary,
        "h51_plausibility_graded": pl_graded,
        "h51_plausibility_budget": h51_emission,
        "h49_yager_pignistic_budget": h49_emission,
    }

    blocks = rsh.quadrants(*labels.shape)
    results_cat = rsh.score_surface_set(candidates, catalogue_truth, footprint, blocks)
    results_sgmc = rsh.score_surface_set(candidates, sgmc_offcat_truth, footprint, blocks)

    def gate_block(results: dict, name: str) -> dict:
        out = {}
        for base in (
            "dotted_b2_parent", "tip_h36_parent", "naive_mean_beliefs",
            "union_decision", "h50_ds_belief", "h50_binary_bel_budget",
            "h49_yager_pignistic_budget",
        ):
            if base == name:
                continue
            out[base] = rsh.paired_delta(results, name, base, blocks)
        return out

    # Preregistered numeric gate (docs/research/hypotheses-20261007.md): beat
    # the blocked-holdout best in >=3/4 folds on BOTH proxy regimes.
    gate_h51_sgmc = gate_block(results_sgmc, "h51_plausibility_budget")
    gate_h51_cat = gate_block(results_cat, "h51_plausibility_budget")
    numeric_pass = (
        gate_h51_sgmc["h49_yager_pignistic_budget"]["positive_folds"] >= 3
        and gate_h51_cat["union_decision"]["positive_folds"] >= 3
    )

    report = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": (
            "NUMERIC_GATE_PASSED_PROXY_ONLY_NOT_SLOT_CLEARED"
            if numeric_pass
            else "CONDITIONAL_SPATIAL_BLOCK_DIAGNOSTIC_NOT_SLOT_CLEARED"
        ),
        "candidate": {
            "name": "h51_plausibility_budget",
            "path": str(H51_PRIMARY.relative_to(ROOT)),
            "sha256": rsh.sha256_file(H51_PRIMARY),
            "build_receipt": "evidence/build_h51_receipt_20261007.json",
            "preregistered_budget": budget,
        },
        "fold_protocol": {
            "geometry": "Four fixed 2x2 geographic quadrants (identical to run_spatial_holdout.py).",
            "metric": "Official distance-weighted Tversky; alpha=0.2, beta=0.8, 300 m triangular kernel.",
            "evaluation_domain": "Held-out quadrant plus 300 m halo, clipped to footprint; core-only truth.",
            "candidate_retraining": False,
            "leakage_limitation": (
                "Frozen upstream owner-mirror surfaces; the b2 parent was catalogue-flank-pruned with "
                "full-catalogue knowledge. Results are conditional and potentially leaky."
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
        "candidates_note": {
            "dotted_b2_parent": "binary committed pixels, H33-2-B2 (owner live 0.2778)",
            "tip_h36_parent": "binary committed pixels, H36-1 rung30 (owner live 0.2710)",
            "naive_mean_beliefs": "max-normalized 0.5*(b_a+b_b) kernel-credit belief surfaces",
            "union_decision": "binary union of the two parents (49,066 px)",
            "h50_ds_belief": "normalized Dempster belief of kernel-credit surfaces (graded)",
            "h50_binary_bel_budget": "binary top-37,654 by H50 belief",
            "h51_plausibility_graded": "max-normalized plausibility Pl(F) (graded sensitivity)",
            "h51_plausibility_budget": "binary top-37,654 by plausibility (the submission)",
            "h49_yager_pignistic_budget": "H49 Yager/pignistic budget artifact, 47,905 px (proxy best)",
        },
        "catalogue_proxy_results": results_cat,
        "sgmc_offcat_results": results_sgmc,
        "catalogue_paired_gates": {"h51_plausibility_budget": gate_h51_cat},
        "sgmc_paired_gates": {"h51_plausibility_budget": gate_h51_sgmc},
        "numeric_gate": {
            "rule": (
                "beat the blocked-holdout best (H49 on SGMC offcat; union on catalogue) "
                "in >=3/4 folds on BOTH proxy regimes -- hypotheses-20261007.md"
            ),
            "sgmc_vs_h49_positive_folds": gate_h51_sgmc["h49_yager_pignistic_budget"]["positive_folds"],
            "sgmc_vs_h49_mean_delta": gate_h51_sgmc["h49_yager_pignistic_budget"]["mean_delta_dti"],
            "catalogue_vs_union_positive_folds": gate_h51_cat["union_decision"]["positive_folds"],
            "catalogue_vs_union_mean_delta": gate_h51_cat["union_decision"]["mean_delta_dti"],
            "passed": bool(numeric_pass),
        },
        "slot_decision": {
            "cleared": False,
            "reason": (
                "Public-map proxy targets only; frozen upstream surfaces; no organizer receipt. "
                "Even a numeric proxy win would not be private-label evidence."
            ),
        },
        "caveats": [
            "Catalogue and SGMC proxies are not the private expert-labelled target.",
            "Owner mirrors are not organizer-authenticated; reuse licenses unverified.",
            "No leaderboard score is estimated here.",
            "H51's budget and ranking rule were preregistered before this run; no post-hoc tuning.",
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
