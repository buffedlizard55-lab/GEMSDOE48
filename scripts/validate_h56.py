#!/usr/bin/env python3
"""Audit the H56B graded-belief GeoTIFF without a live-score surrogate.

This validator performs local format/uniqueness checks and evaluates the frozen H56B
surface against the same-protocol H49 *public-proxy* reference. It deliberately does
not compute or use an owner-score forward projection: the earlier projection relied
on FPw=S-TPw, which is not an identity under the official metric.

A public-proxy pass is necessary but cannot clear a competition slot. The primary
H56B file uses finite zeros outside the data footprint while the official problem
page says outside cells should be null/NaN; the portal has not been tested. Therefore
the script can say "OK TO DOWNLOAD FOR INSPECTION" but never "OK TO SUBMIT".

Usage: python scripts/validate_h56.py --primary docs/downloads/<h56b-zeros-outside.tif>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
for entry in (ROOT / "src", ROOT / "scripts"):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from gemsdoe48.geotiff import assert_competition_grid, assert_same_grid, display_path  # noqa: E402
from run_spatial_holdout import quadrants  # noqa: E402
from validate_h57a import compare_to_h49, make_contexts, score_surface  # noqa: E402

EXPECTED = {
    "dotted": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "tip": "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
    "labels": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "sgmc": "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0",
    "footprint": "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
    "h49": "9f028289c364c071065245799d7ed131600e80e9f0d10602806b12ce34d7cae8",
}
H49 = ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif"
H49_REF = ROOT / "evidence/holdout_h56_h49_reference_20261007.json"
LABELS = ROOT / "data/raw/labels_catalogue.tif"
SGMC = ROOT / "data/official/derived_sgmc_faults_100m.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
DOTTED = ROOT / "data/families/dotted_b2_prune_02778.tif"
TIP = ROOT / "data/families/tip_stepover_r30_02632.tif"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_one(path: Path) -> tuple[np.ndarray, dict]:
    with rasterio.open(path) as dataset:
        assert_competition_grid(dataset.profile, path=path)
        if dataset.count != 1:
            raise SystemExit(f"expected one band in {path}, got {dataset.count}")
        return dataset.read(1), dataset.profile.copy()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary", required=True, type=Path)
    parser.add_argument("--h49", type=Path, default=H49)
    args = parser.parse_args()
    args.primary = args.primary.resolve()
    args.h49 = args.h49.resolve()
    if not args.primary.exists():
        raise SystemExit(f"missing H56B primary: {args.primary}")
    if not args.h49.exists():
        raise SystemExit(f"missing H49 reference: {args.h49}")
    now = datetime.now(timezone.utc).isoformat()

    input_paths = {
        "dotted": DOTTED, "tip": TIP, "labels": LABELS, "sgmc": SGMC,
        "footprint": FOOTPRINT, "h49": args.h49,
    }
    input_hashes = {name: sha256_file(path) for name, path in input_paths.items()}
    for name, expected in EXPECTED.items():
        if input_hashes[name] != expected:
            raise SystemExit(f"pinned {name} SHA-256 changed: {input_hashes[name]} != {expected}")

    labels, label_profile = read_one(LABELS)
    sgmc_raw, sgmc_profile = read_one(SGMC)
    footprint_raw, footprint_profile = read_one(FOOTPRINT)
    dotted_raw, dotted_profile = read_one(DOTTED)
    tip_raw, tip_profile = read_one(TIP)
    h49_raw, h49_profile = read_one(args.h49)
    with rasterio.open(ROOT / "data/raw/sample_submission_template.tif") as template_ds:
        assert_competition_grid(template_ds.profile, path="data/raw/sample_submission_template.tif")
        template_profile = template_ds.profile.copy()
    with rasterio.open(args.primary) as primary_ds:
        assert_competition_grid(primary_ds.profile, path=args.primary)
        primary = primary_ds.read(1)
        primary_profile = primary_ds.profile.copy()

    for profile, path in (
        (label_profile, LABELS), (sgmc_profile, SGMC), (footprint_profile, FOOTPRINT),
        (dotted_profile, DOTTED), (tip_profile, TIP), (h49_profile, args.h49),
    ):
        assert_same_grid(template_profile, profile, name_a="sample template", name_b=str(path))
    assert_same_grid(template_profile, primary_profile, name_a="sample template", name_b=str(args.primary))

    footprint = footprint_raw == 1
    if not np.array_equal(footprint, labels != -1):
        raise SystemExit("footprint mask differs from catalogue-label nodata support")
    catalogue = (labels == 1) & footprint
    dotted = (dotted_raw > 0) & footprint
    tip = (tip_raw > 0) & footprint
    h49 = np.nan_to_num(h49_raw.astype(np.float32), nan=0.0)
    if int(catalogue.sum()) != 60_988:
        raise SystemExit("pinned catalogue positive count changed")

    # ------------------------------------------- 1. local format, separate portal caveat
    value = primary.astype(np.float64)
    outside = ~footprint
    format_checks = {
        "crs_matches_template": primary_profile["crs"] == template_profile["crs"],
        "transform_matches_template": primary_profile["transform"] == template_profile["transform"],
        "shape_matches_template": (primary_profile["height"], primary_profile["width"]) == (template_profile["height"], template_profile["width"]),
        "single_band_float32": primary_profile["count"] == 1 and primary_profile["dtype"] == "float32",
        "all_cells_finite": bool(np.isfinite(value).all()),
        "whole_raster_values_in_0_1": bool(value.min() >= 0.0 and value.max() <= 1.0),
        "max_equals_one": bool(abs(float(value.max()) - 1.0) < 1e-6),
        "nodata_unset": primary_profile.get("nodata") is None,
        "outside_footprint_finite_zero": bool(np.all(value[outside] == 0.0)),
        "official_null_nan_outside_rule_satisfied": bool(np.isnan(value[outside]).all()) if outside.any() else True,
    }
    format_receipt = {
        "generated_utc": now,
        "path": display_path(args.primary),
        "sha256": sha256_file(args.primary),
        "checks": format_checks,
        "local_core_format_passed": bool(all(format_checks[key] for key in (
            "crs_matches_template", "transform_matches_template", "shape_matches_template",
            "single_band_float32", "all_cells_finite", "whole_raster_values_in_0_1",
        ))),
        "official_outside_policy_passed": bool(format_checks["official_null_nan_outside_rule_satisfied"]),
        "portal_acceptance_tested": False,
        "format_interpretation": "local grid/dtype/range checks are distinct from portal acceptance; the zero-outside primary does not satisfy the published null/NaN outside-footprint wording",
    }

    # -------------------------------------------------------- 2. byte and value uniqueness
    download_dir = ROOT / "docs/downloads"
    byte_collisions = []
    canonical_duplicates = []
    encoding_twins = []
    byte_compared = 0
    canonical_compared = 0
    primary_stem = args.primary.stem.replace("-zeros-outside", "").replace("-nan-outside", "")
    for path in sorted(download_dir.rglob("*.tif")):
        if path.resolve() == args.primary:
            continue
        byte_compared += 1
        if sha256_file(path) == format_receipt["sha256"]:
            byte_collisions.append(str(path.relative_to(ROOT)))
        try:
            other, other_profile = read_one(path)
            assert_same_grid(primary_profile, other_profile, name_a=str(args.primary), name_b=str(path))
            other_values = np.nan_to_num(other.astype(np.float32), nan=0.0)
            canonical_compared += 1
            if np.array_equal(other_values[footprint], primary[footprint]):
                rel = str(path.relative_to(ROOT))
                other_stem = path.stem.replace("-zeros-outside", "").replace("-nan-outside", "")
                if other_stem == primary_stem:
                    # Same H56B prediction emitted twice solely to retain both outside encodings.
                    encoding_twins.append(rel)
                else:
                    canonical_duplicates.append(rel)
        except Exception:
            # Non-submission diagnostics can have another grid/profile; byte check remains valid.
            continue
    uniqueness = {
        "generated_utc": now,
        "path": display_path(args.primary),
        "sha256": format_receipt["sha256"],
        "byte_distinct_from_local_downloads": not byte_collisions,
        "byte_collisions": byte_collisions,
        "byte_comparisons": byte_compared,
        "canonical_footprint_equal_duplicates": canonical_duplicates,
        "same_surface_encoding_twins": encoding_twins,
        "canonical_footprint_comparisons": canonical_compared,
        "matches_registry_mirror_pin": False,
        "registry_note": "This is a new H56B output, not a byte-pinned public leaderboard file; a NaN-outside twin has the same in-footprint values.",
        "pass": not byte_collisions and not canonical_duplicates,
    }

    # ------------------------------------------- 3. comparable four-quadrant holdout
    dcat = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    sgmc_truth = (sgmc_raw > 0) & footprint & (dcat > 300.0)
    truths = {"catalogue_proxy": catalogue, "sgmc_off_catalogue_gt300m": sgmc_truth}
    contexts = make_contexts(truths, footprint, quadrants(*footprint.shape))
    surfaces = {
        "h56_belief": np.where(footprint, value, 0.0),
        "dotted_c": dotted.astype(np.float64),
        "tip_stepover": tip.astype(np.float64),
        "union_binary": (dotted | tip).astype(np.float64),
        "naive_mean_binary": 0.5 * (dotted.astype(np.float64) + tip.astype(np.float64)),
        "h49_reference": h49.astype(np.float64),
    }
    holdout_results = {name: score_surface(surface, contexts) for name, surface in surfaces.items()}
    frozen_h49 = json.loads(H49_REF.read_text(encoding="utf-8"))
    for truth_name, ref_key in (("catalogue_proxy", "results"), ("sgmc_off_catalogue_gt300m", "sgmc_off_catalogue_results")):
        stored = frozen_h49[ref_key]["h49_balanced_same_protocol_reference"]
        for fold in ("NW", "NE", "SW", "SE"):
            actual = holdout_results["h49_reference"][truth_name][fold]["dti"]
            if not np.isclose(actual, stored[fold]["dti"], rtol=0.0, atol=1e-10):
                raise SystemExit(f"H49 fold protocol drift for {truth_name}/{fold}: {actual} != {stored[fold]['dti']}")
    h49_comparison = compare_to_h49(holdout_results["h56_belief"], holdout_results["h49_reference"])
    parent_comparisons = {}
    for parent_name in ("dotted_c", "tip_stepover"):
        parent_comparisons[parent_name] = {}
        for truth_name in truths:
            h56 = holdout_results["h56_belief"][truth_name]
            parent = holdout_results[parent_name][truth_name]
            deltas = {fold: float(h56[fold]["dti"] - parent[fold]["dti"]) for fold in ("NW", "NE", "SW", "SE")}
            parent_comparisons[parent_name][truth_name] = {
                "fold_delta_dti": deltas,
                "mean_delta_dti": float(np.mean(list(deltas.values()))),
                "positive_folds": int(sum(delta > 0.0 for delta in deltas.values())),
            }

    h49_gate = all(row["passes_numeric_gate"] for row in h49_comparison.values())
    format_pass = bool(format_receipt["local_core_format_passed"])
    uniqueness_pass = bool(uniqueness["pass"])
    download_ok = args.primary.exists()
    report = {
        "schema_version": 1,
        "generated_utc": now,
        "candidate": {"name": "H56B graded Dempster belief", "path": display_path(args.primary), "sha256": format_receipt["sha256"]},
        "public_proxy_best": {
            "path": str(args.h49.relative_to(ROOT)),
            "sha256": input_hashes["h49"],
            "source_receipt": "evidence/holdout_h56_h49_reference_20261007.json",
            "mean_dti": {truth: holdout_results["h49_reference"][truth]["mean_dti"] for truth in truths},
            "not_private_truth_or_leaderboard_score": True,
        },
        "truth_sources": {
            "catalogue_proxy": {"sha256": input_hashes["labels"], "positive_pixels": int(catalogue.sum()), "is_private_expert_truth": False},
            "sgmc_off_catalogue_gt300m": {"sha256": input_hashes["sgmc"], "positive_pixels": int(sgmc_truth.sum()), "is_private_expert_truth": False},
        },
        "holdout_protocol": {
            "implementation": "scripts/run_spatial_holdout.py fold geometry and official metric; local folds cached using scripts/validate_h57a.py helpers",
            "geometry": "four fixed NW/NE/SW/SE quadrants split at full-grid midpoint",
            "evaluation_domain": "held-out core plus 300 m Euclidean halo clipped to footprint; only core-quadrant truth scored",
            "alpha": 0.2, "beta": 0.8, "radius_m": 300.0, "pixel_size_m": 100.0,
            "candidate_retrained_within_folds": False,
        },
        "results": holdout_results,
        "paired_vs_h49_current_proxy_best": h49_comparison,
        "paired_vs_parent_families": parent_comparisons,
        "gates": {
            "local_grid_dtype_range": format_pass,
            "official_null_nan_outside_rule": format_receipt["official_outside_policy_passed"],
            "byte_and_canonical_uniqueness": uniqueness_pass,
            "beats_h49_on_both_proxies": bool(h49_gate),
            "beats_h49_rule": "positive mean paired delta and at least 3/4 positive fold deltas on both proxy truths",
        },
        "download_verdict": "OK TO DOWNLOAD FOR INSPECTION" if download_ok else "NOT AVAILABLE",
        "submit_verdict": "NOT OK / NOT CLEARED TO SUBMIT",
        "slot_decision": {
            "cleared": False,
            "reason": "H56B fails the same-protocol H49 proxy gate and its zero-outside primary conflicts with the published null/NaN outside-footprint wording. Public proxies and local format checks cannot establish private-label performance or portal acceptance.",
        },
        "metric_projection": {
            "status": "INVALIDATED_NOT_USED",
            "reason": "The historical forward-model score estimate assumes FPw=S-TPw, which is false in general under the official metric; no projection is used as a candidate gate.",
            "historical_receipt": "evidence/h56_live_model_projection_20261007.json",
        },
        "caveats": [
            "The H56B surface uses fixed upstream parents and a catalogue-flank absence rule; it was not refit within folds.",
            "The two validation targets are public map proxies, not the competition's private expert-labelled test set.",
            "The H49 proxy-best reference is not the official live leaderboard leader or private-label best.",
            "The primary zero-outside encoding is not the official null/NaN outside encoding; a NaN-outside twin exists, but portal acceptance is untested.",
            "No organizer receipt ties any local TIFF to a public leaderboard score.",
        ],
    }

    # Keep the older artifact names, but their new contents contain no live-model projection.
    format_receipt["verdict"] = report["submit_verdict"]
    format_receipt["holdout_gate"] = {"passed_vs_h49": bool(h49_gate), "paired": h49_comparison}
    format_receipt["download_verdict"] = report["download_verdict"]
    (ROOT / "evidence/h56_format_audit_20261007.json").write_text(json.dumps(format_receipt, indent=2) + "\n", encoding="utf-8")
    (ROOT / "evidence/h56_uniqueness_20261007.json").write_text(json.dumps(uniqueness, indent=2) + "\n", encoding="utf-8")
    (ROOT / "evidence/holdout_h56_belief_h49_20261007.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print("local core format:", format_pass)
    print("official null/NaN outside policy:", format_receipt["official_outside_policy_passed"])
    print("byte/canonical uniqueness:", uniqueness_pass, "files:", byte_compared)
    for truth_name in truths:
        print(
            truth_name,
            "H56B=", f"{holdout_results['h56_belief'][truth_name]['mean_dti']:.6f}",
            "H49=", f"{holdout_results['h49_reference'][truth_name]['mean_dti']:.6f}",
            "delta=", f"{h49_comparison[truth_name]['mean_delta_dti_vs_h49']:+.6f}",
            "wins=", f"{h49_comparison[truth_name]['positive_folds']}/4",
        )
    print("download:", report["download_verdict"])
    print("submit:", report["submit_verdict"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
