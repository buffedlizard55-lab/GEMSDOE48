#!/usr/bin/env python3
"""Blocked-holdout diagnostics for the H50 candidate and its comparators.

Reuses the exact fold geometry, evaluation domain (held-out quadrant + 300 m
halo), and official metric call of ``scripts/run_spatial_holdout.py`` so the
numbers are comparable with the 2026-10-06 reports.  Truth sources remain the
two public owner-mirror proxies (catalogue labels; SGMC faults >300 m from the
catalogue).  Nothing here is private-label evidence or a slot clearance.
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

from gemsdoe48 import ds50
from gemsdoe48.evidence import combine_dempster
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
TIP_H33D = ROOT / "data/raw/tip_h33d_stepover.tif"
LABELS = ROOT / "data/raw/labels_catalogue.tif"
SGMC = ROOT / "data/official/derived_sgmc_faults_100m.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
_h50_candidates = sorted((ROOT / "docs/downloads").glob("gemsdoe48-h50-ds-b2xh36rung30-*-zeros.tif"))
if not _h50_candidates:
    raise SystemExit("no H50 primary submission found; run scripts/build_ds50_submission.py first")
H50_PRIMARY = _h50_candidates[-1]

PINNED = {
    DOTTED: rsh.EXPECTED_DOTTED_SHA256,
    TIP_H36: "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641",
    TIP_H33D: rsh.EXPECTED_TIP_SHA256,
    LABELS: rsh.EXPECTED_LABEL_SHA256,
    SGMC: rsh.EXPECTED_SGMC_SHA256,
    FOOTPRINT: "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
}


def finite(values: np.ndarray) -> np.ndarray:
    return np.where(np.isfinite(values), values, 0.0).astype(np.float64)


def dilate_cross(mask: np.ndarray, radius: int) -> np.ndarray:
    out = np.asarray(mask, dtype=bool).copy()
    for _ in range(int(radius)):
        cur = out
        up = np.zeros_like(cur); up[1:, :] = cur[:-1, :]
        down = np.zeros_like(cur); down[:-1, :] = cur[1:, :]
        left = np.zeros_like(cur); left[:, 1:] = cur[:, :-1]
        right = np.zeros_like(cur); right[:, :-1] = cur[:, 1:]
        out = cur | up | down | left | right
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/holdout_ds50_20261007.json")
    parser.add_argument("--splay-output", type=Path, default=ROOT / "evidence/splay_probe_holdout_20261007.json")
    args = parser.parse_args()

    for path, expected in PINNED.items():
        got = rsh.sha256_file(path)
        if got != expected:
            raise SystemExit(f"pin violation: {path} sha {got} != {expected}")

    labels, label_profile = read_band(LABELS)
    sgmc_values, sgmc_profile = read_band(SGMC)
    dotted_raw, dotted_profile = read_band(DOTTED)
    tip_h36_raw, tip_h36_profile = read_band(TIP_H36)
    tip_h33d_raw, tip_h33d_profile = read_band(TIP_H33D)
    h50_raw, h50_profile = read_band(H50_PRIMARY)
    with rasterio.open(FOOTPRINT) as fp_ds:
        assert_competition_grid(fp_ds.profile, path=FOOTPRINT)
        footprint = fp_ds.read(1) == 1

    for prof, path in (
        (sgmc_profile, SGMC), (dotted_profile, DOTTED), (tip_h36_profile, TIP_H36),
        (tip_h33d_profile, TIP_H33D), (h50_profile, H50_PRIMARY),
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
    tip_h33d = np.where(footprint, finite(tip_h33d_raw), 0.0)
    h50_belief = np.where(footprint, finite(h50_raw), 0.0)

    # Kernel-credit belief surfaces (identical construction to the build script).
    belief_a = ds50.kernel_belief_surface((dotted > 0) & footprint)
    belief_b = ds50.kernel_belief_surface((tip_h36 > 0) & footprint)
    naive = ds50.naive_mean_belief(belief_a, belief_b)
    naive = np.where(footprint, naive / naive[footprint].max(), 0.0)
    union_decision = np.where(footprint, ((dotted > 0) | (tip_h36 > 0)).astype(np.float64), 0.0)
    budget = int(np.count_nonzero(dotted > 0))  # 37,654 cells, mass-matched to parent A
    h50_binary = np.where(
        ds50.top_k_mask(h50_belief, budget, where=footprint), 1.0, 0.0
    ).astype(np.float64)
    # Same-parent raw-sparse rho=0.5 reference (the H48 recipe on the new pair).
    raw_ds = combine_dempster(
        np.where(footprint, dotted, 0.0).astype(np.float32),
        np.where(footprint, tip_h36, 0.0).astype(np.float32),
        reliability=0.5,
    )
    raw_sparse_rho05 = np.where(footprint, raw_ds.fault.astype(np.float64), 0.0)

    candidates = {
        "dotted_b2_parent": dotted,
        "tip_h36_parent": tip_h36,
        "tip_h33d_prior_tip": tip_h33d,
        "naive_mean_beliefs": naive,
        "union_decision": union_decision,
        "raw_sparse_rho05_same_parents": raw_sparse_rho05,
        "h50_ds_belief": h50_belief,
        "h50_binary_budget_matched": h50_binary,
    }

    blocks = rsh.quadrants(*labels.shape)
    results_cat = rsh.score_surface_set(candidates, catalogue_truth, footprint, blocks)
    results_sgmc = rsh.score_surface_set(candidates, sgmc_offcat_truth, footprint, blocks)

    def gate_block(results: dict, name: str) -> dict:
        out = {}
        for base in ("dotted_b2_parent", "tip_h36_parent", "naive_mean_beliefs", "union_decision"):
            if base == name:
                continue
            out[base] = rsh.paired_delta(results, name, base, blocks)
        return out

    report = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "CONDITIONAL_SPATIAL_BLOCK_DIAGNOSTIC_NOT_SLOT_CLEARED",
        "candidate": {
            "name": "h50_ds_belief",
            "path": str(H50_PRIMARY.relative_to(ROOT)),
            "sha256": rsh.sha256_file(H50_PRIMARY),
            "build_receipt": "evidence/build_ds50_receipt_20261007.json",
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
            "tip_h33d_prior_tip": "binary committed pixels, H33-D (owner live 0.2632) -- prior tip parent",
            "naive_mean_beliefs": "max-normalized 0.5*(b_a+b_b) kernel-credit belief surfaces",
            "union_decision": "binary union of the two parents",
            "raw_sparse_rho05_same_parents": "H48 recipe (raw sparse surfaces, rho=0.5) applied to the H50 parents",
            "h50_ds_belief": "normalized Dempster belief of kernel-credit surfaces, live-anchored discounts",
            "h50_binary_budget_matched": "value-1 emission on the top 37,654 cells of h50_ds_belief",
        },
        "catalogue_proxy_results": results_cat,
        "sgmc_offcat_results": results_sgmc,
        "catalogue_paired_gates": {
            name: gate_block(results_cat, name)
            for name in ("h50_ds_belief", "h50_binary_budget_matched")
        },
        "sgmc_paired_gates": {
            name: gate_block(results_sgmc, name)
            for name in ("h50_ds_belief", "h50_binary_budget_matched")
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
        ],
    }

    # ---- H50-5 splay-prior hypothesis probe (same folds, separate report) ----
    band = footprint & (distance_to_catalogue_m > 100.0) & (distance_to_catalogue_m <= 600.0)
    corridor = dilate_cross(((dotted > 0) | (tip_h36 > 0)) & footprint, 1)
    splay_candidates = {
        "splay_band_100_600m": np.where(band, 1.0, 0.0),
        "splay_band_x_family_corridor": np.where(band & corridor, 1.0, 0.0),
        "h50_ds_belief_reference": h50_belief,
        "tip_h36_parent_reference": tip_h36,
    }
    splay_cat = rsh.score_surface_set(splay_candidates, catalogue_truth, footprint, blocks)
    splay_sgmc = rsh.score_surface_set(splay_candidates, sgmc_offcat_truth, footprint, blocks)
    splay_report = {
        "schema_version": 1,
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis_id": "H50-5",
        "hypothesis": (
            "Hidden faults cluster on unmapped parallel splays of catalogue traces at 100-600 m "
            "perpendicular offset; a distance-band prior around the catalogue, optionally gated by "
            "family support, should catch off-catalogue structure."
        ),
        "status": "CONDITIONAL_SPATIAL_BLOCK_DIAGNOSTIC_NOT_SLOT_CLEARED",
        "construction": {
            "splay_band_100_600m": "binary 1 where 100 m < d(catalogue) <= 600 m, inside footprint",
            "splay_band_x_family_corridor": "band intersected with the 1-px-dilated union corridor of both parents",
        },
        "catalogue_proxy_results": splay_cat,
        "sgmc_offcat_results": splay_sgmc,
        "sgmc_paired_gates": {
            name: rsh.paired_delta(splay_sgmc, name, "h50_ds_belief_reference", blocks)
            for name in ("splay_band_100_600m", "splay_band_x_family_corridor")
        },
        "slot_decision": {"cleared": False, "reason": "proxy-only diagnostic"},
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    args.splay_output.write_text(json.dumps(splay_report, indent=2) + "\n", encoding="utf-8")

    def summarize(results: dict, label: str) -> None:
        print(f"--- {label} mean DTI ---")
        for name in results:
            print(f"  {name:36s} {results[name]['mean_dti']:.6f}")

    summarize(results_cat, "catalogue proxy")
    summarize(results_sgmc, "SGMC off-catalogue proxy")
    summarize(splay_sgmc, "splay probe (SGMC offcat)")
    print(json.dumps({"written": [str(args.output), str(args.splay_output)]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
