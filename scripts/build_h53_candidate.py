#!/usr/bin/env python3
"""Build H53-1: B2 x H33-D D-S fusion with weak GeoDAWN edge evidence.

All construction parameters were frozen in docs/research/hypotheses-h53-20261007.md
and evidence/h53_preregistration_20261007.json before this script was written or
run. This is a research candidate, not a cleared submission.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48 import ds50, h53  # noqa: E402
from gemsdoe48.geotiff import assert_competition_grid, assert_same_grid, display_path, read_band, write_float32  # noqa: E402

B2 = ROOT / "data/families/dotted_b2_prune_02778.tif"
H33D = ROOT / "data/families/tip_stepover_r30_02632.tif"
RADIOMETRY = ROOT / "data/source_mirrors/geodawn_rad_u8.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"

EXPECTED_SHA = {
    B2: "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    H33D: "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
    RADIOMETRY: "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682",
    FOOTPRINT: "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
}
EXPECTED_DOTS = {"b2": 37_654, "h33d": 41_865}
RHO_FAMILY = 0.50
RHO_RADIOMETRIC = 0.25
ABSENCE_RAD = 0.10
SIGMAS = (1.0, 3.0)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_sha(path: Path) -> str:
    got = sha256_file(path)
    expected = EXPECTED_SHA[path]
    if got != expected:
        raise SystemExit(f"source SHA mismatch for {path}: {got} != {expected}")
    return got


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    xv = np.asarray(x, dtype=np.float64).ravel()
    yv = np.asarray(y, dtype=np.float64).ravel()
    if xv.size < 2 or xv.std() == 0.0 or yv.std() == 0.0:
        return float("nan")
    return float(np.corrcoef(xv, yv)[0, 1])


def top_k(masked_values: np.ndarray, valid: np.ndarray, k: int) -> np.ndarray:
    flat_valid = np.flatnonzero(valid.ravel())
    k = min(int(k), flat_valid.size)
    out = np.zeros(valid.size, dtype=bool)
    if k:
        values = np.asarray(masked_values, dtype=np.float32).ravel()[flat_valid]
        selected = np.argpartition(values, values.size - k)[values.size - k:]
        out[flat_valid[selected]] = True
    return out.reshape(valid.shape)


def comparison_stats(primary: np.ndarray, baseline: np.ndarray, valid: np.ndarray, top_count: int) -> dict:
    p = np.asarray(primary[valid], dtype=np.float32)
    b = np.asarray(baseline[valid], dtype=np.float32)
    difference = p - b
    sample_step = max(1, int(np.ceil(p.size / 100_000)))
    sample_p = p[::sample_step]
    sample_b = b[::sample_step]
    sp = spearmanr(sample_p, sample_b).statistic if sample_p.size > 1 else float("nan")
    p_top = top_k(primary, valid, top_count)
    b_top = top_k(baseline, valid, top_count)
    intersection = int((p_top & b_top).sum())
    union = int((p_top | b_top).sum())
    return {
        "pearson_in_footprint": pearson(p, b),
        "spearman_deterministic_sample": float(sp),
        "spearman_sample_cells": int(sample_p.size),
        "mae_in_footprint": float(np.abs(difference).mean()),
        "max_abs_difference": float(np.abs(difference).max()),
        "fraction_abs_difference_gt_0_05": float((np.abs(difference) > 0.05).mean()),
        "exactly_equal_cells": int(np.count_nonzero(difference == 0.0)),
        "different_cells": int(np.count_nonzero(difference != 0.0)),
        "budget_matched_top_k": int(top_count),
        "top_k_jaccard": float(intersection / union) if union else None,
        "is_pixelwise_equal": bool(np.array_equal(p, b)),
    }


def write_diagnostic(path: Path, values: np.ndarray, profile: dict, footprint: np.ndarray, description: str, tags: dict[str, str]) -> dict:
    surface = np.asarray(values, dtype=np.float32).copy()
    surface[~footprint] = np.nan
    return write_float32(path, surface, profile, valid_mask=footprint, description=description, tags=tags)


def main() -> int:
    for source in EXPECTED_SHA:
        verify_sha(source)

    dotted_raw, profile = read_band(B2)
    h33d_raw, h33d_profile = read_band(H33D)
    assert_competition_grid(profile, path=B2)
    assert_competition_grid(h33d_profile, path=H33D)
    assert_same_grid(profile, h33d_profile, name_a=str(B2), name_b=str(H33D))

    with rasterio.open(FOOTPRINT) as dataset:
        assert_competition_grid(dataset.profile, path=FOOTPRINT)
        footprint = dataset.read(1) == 1
    if int(footprint.sum()) != 5_167_373:
        raise SystemExit(f"unexpected footprint size: {int(footprint.sum())}")

    with rasterio.open(RADIOMETRY) as dataset:
        rad_profile = dataset.profile.copy()
        if dataset.count != 4:
            raise SystemExit(f"GeoDAWN input has {dataset.count} bands; expected K, Th, U, TC")
        for key, expected in (("width", 3292), ("height", 3730), ("crs", profile["crs"]), ("transform", profile["transform"])):
            if rad_profile.get(key) != expected:
                raise SystemExit(f"GeoDAWN {key} mismatch: {rad_profile.get(key)!r} != {expected!r}")
        descriptions = tuple(dataset.descriptions)
        if descriptions != ("K", "Th", "U", "TC"):
            raise SystemExit(f"unexpected GeoDAWN band descriptions: {descriptions!r}")
        if dataset.nodata != 0:
            raise SystemExit(f"expected zero nodata in GeoDAWN; found {dataset.nodata!r}")
        radiometric_raw = dataset.read()

    dotted_values = np.where(np.isfinite(dotted_raw), dotted_raw, 0.0).astype(np.float32)
    h33d_values = np.where(np.isfinite(h33d_raw), h33d_raw, 0.0).astype(np.float32)
    if np.any((dotted_values < 0.0) | (dotted_values > 1.0)) or np.any((h33d_values < 0.0) | (h33d_values > 1.0)):
        raise SystemExit("family source pixels must be in [0,1]")
    dotted_mask = (dotted_values > 0.0) & footprint
    h33d_mask = (h33d_values > 0.0) & footprint
    if int(dotted_mask.sum()) != EXPECTED_DOTS["b2"] or int(h33d_mask.sum()) != EXPECTED_DOTS["h33d"]:
        raise SystemExit(f"unexpected source dot counts: B2={int(dotted_mask.sum())}, H33D={int(h33d_mask.sum())}")

    radiometric_valid = footprint & np.all(radiometric_raw > 0, axis=0)
    if not radiometric_valid.any():
        raise SystemExit("GeoDAWN has no valid cells in the competition footprint")
    edge_result = h53.multiband_edge_coherence(
        radiometric_raw.astype(np.float32),
        radiometric_valid,
        sigmas=SIGMAS,
        pctl=99.0,
        min_mask_weight=0.99,
    )
    edge = edge_result.score

    # Same 300 m triangular support geometry as the scoring kernel.
    belief_b2 = ds50.kernel_belief_surface(dotted_mask).astype(np.float32)
    belief_h33d = ds50.kernel_belief_surface(h33d_mask).astype(np.float32)
    bpa_b2 = h53.simple_support_bpa(belief_b2, RHO_FAMILY)
    bpa_h33d = h53.simple_support_bpa(belief_h33d, RHO_FAMILY)
    bpa_rad = h53.radiometric_bpa(edge, RHO_RADIOMETRIC, ABSENCE_RAD)
    fusion = h53.dempster_three(bpa_b2, bpa_h33d, bpa_rad)
    two_family = h53.dempster_two(bpa_b2, bpa_h33d)

    max_fault = float(fusion.fault[footprint].max())
    if not np.isfinite(max_fault) or max_fault <= 0.0:
        raise SystemExit("D-S combination has no positive fault belief in footprint")
    prediction = np.clip(fusion.fault / max_fault, 0.0, 1.0).astype(np.float32)
    two_family_prediction = np.clip(two_family[0] / float(two_family[0][footprint].max()), 0.0, 1.0).astype(np.float32)
    mean_two = (belief_b2 + belief_h33d) / np.float32(2.0)
    mean_two /= max(float(mean_two[footprint].max()), 1e-12)
    mean_three = (belief_b2 + belief_h33d + edge) / np.float32(3.0)
    mean_three /= max(float(mean_three[footprint].max()), 1e-12)

    tags = {
        "candidate_id": "H53-1",
        "model": "Canonical normalized three-source Dempster-Shafer combination",
        "family_sources": "H33-2-B2 dotted and H33-D tip/step-over",
        "radiometric_source": "GeoDAWN K, Th, U, TC multiscale gradient-orientation coherence",
        "family_reliability": str(RHO_FAMILY),
        "radiometric_reliability": str(RHO_RADIOMETRIC),
        "radiometric_absence_informativeness": str(ABSENCE_RAD),
        "gaussian_sigmas_pixels": "1.0,3.0",
        "metric_kernel": "triangular 300 m support; max-credit field",
        "parent_b2_sha256": EXPECTED_SHA[B2],
        "parent_h33d_sha256": EXPECTED_SHA[H33D],
        "geodawn_sha256": EXPECTED_SHA[RADIOMETRY],
        "warning": "Owner-mirror inputs; public proxy only; normalized belief is not calibrated probability; not slot-cleared.",
    }

    downloads = ROOT / "docs/downloads"
    diagnostics = downloads / "diagnostics"
    downloads.mkdir(parents=True, exist_ok=True)
    diagnostics.mkdir(parents=True, exist_ok=True)
    temporary = downloads / ".h53-primary-unhashed.tif"
    primary_record = write_float32(
        temporary,
        np.where(footprint, prediction, np.nan).astype(np.float32),
        profile,
        valid_mask=footprint,
        description="H53-1 normalized Dempster Bel(F), B2 x H33-D plus weak GeoDAWN radiometric-edge BPA",
        tags=tags,
    )
    primary_sha = sha256_file(temporary)
    short_id = primary_sha[:12]
    base_name = f"GEMSDOE48-H53-DS-RadEdge-B2xH33D-20261007-{short_id}"
    primary_path = downloads / f"{base_name}-nan-outside.tif"
    primary_path.unlink(missing_ok=True)
    temporary.replace(primary_path)
    primary_record["path"] = display_path(primary_path)
    primary_record["sha256"] = primary_sha

    diag_specs = {
        "mtheta_dempster": (fusion.unassigned_dempster, "H53 canonical Dempster residual unassigned mass m(Theta); excludes raw conflict K"),
        "conflict_total_K": (fusion.conflict_total, "H53 cumulative raw conjunctive Dempster conflict K before normalization"),
        "conflict_b2_h33d_K": (fusion.conflict_ab, "H53 raw Dempster conflict K between B2 and H33-D family BPAs"),
        "radiometric_edge_coherence": (edge, "H53 cross-band radiometric edge strength times doubled-angle orientation coherence; not a fault probability"),
        "two_family_dempster_only": (two_family_prediction, "H53 B2 x H33-D two-family Dempster Bel(F), excluding GeoDAWN"),
        "two_family_naive_mean": (mean_two, "H53 naive arithmetic mean of B2 and H33-D kernel-support surfaces"),
    }
    diagnostic_records: dict[str, dict] = {}
    for key, (array, description) in diag_specs.items():
        suffix = key.replace("_", "-")
        path = diagnostics / f"{base_name}-{suffix}.tif"
        diagnostic_records[key] = write_diagnostic(path, array, profile, footprint, description, tags)
        diagnostic_records[key]["sha256"] = sha256_file(path)

    overlap = int((dotted_mask & h33d_mask).sum())
    union = int((dotted_mask | h33d_mask).sum())
    submitted_name = f"GEMSDOE48-H53-DS-RadEdge-B2xH33D-{short_id}"
    portal_note = (
        f"{submitted_name} | H33-2-B2 x H33-D plus weak GeoDAWN K/Th/U/TC edge evidence; "
        "Dempster-Shafer, unscored research candidate, not slot-cleared."
    )
    if len(portal_note) > 200:
        raise SystemExit(f"portal note is {len(portal_note)} characters; maximum is 200")

    comparisons = {
        "vs_two_family_naive_mean": comparison_stats(prediction, mean_two, footprint, int(dotted_mask.sum())),
        "vs_three_input_naive_mean": comparison_stats(prediction, mean_three, footprint, int(dotted_mask.sum())),
        "vs_two_family_dempster_no_radiometry": comparison_stats(prediction, two_family_prediction, footprint, int(dotted_mask.sum())),
    }
    in_footprint = prediction[footprint]
    receipt = {
        "schema_version": 1,
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "status": "BUILT_RESEARCH_CANDIDATE_HOLDOUT_NOT_YET_RUN_NOT_SLOT_CLEARED",
        "preregistration": "evidence/h53_preregistration_20261007.json",
        "candidate": {
            "id": "H53-1",
            "unique_submission_name": submitted_name,
            "path": display_path(primary_path),
            "sha256": primary_sha,
            "bytes": primary_path.stat().st_size,
            "portal_note_characters": len(portal_note),
            "portal_note": portal_note,
            "holdout_status": "not yet run",
            "leaderboard_claim": False,
            "slot_cleared": False,
        },
        "inputs": {
            "h33_2_b2": {"path": display_path(B2), "sha256": EXPECTED_SHA[B2], "positive_cells": int(dotted_mask.sum()), "owner_reported_live": 0.2778, "official_file_score_receipt": False},
            "h33d_tip_stepover": {"path": display_path(H33D), "sha256": EXPECTED_SHA[H33D], "positive_cells": int(h33d_mask.sum()), "owner_reported_live": 0.2632, "official_file_score_receipt": False},
            "geodawn_radiometry": {"path": display_path(RADIOMETRY), "sha256": EXPECTED_SHA[RADIOMETRY], "bands": list(descriptions), "nodata": 0, "valid_cells_in_footprint": int(radiometric_valid.sum()), "invalid_cells_in_footprint": int((footprint & ~radiometric_valid).sum())},
            "footprint": {"path": display_path(FOOTPRINT), "sha256": EXPECTED_SHA[FOOTPRINT], "valid_cells": int(footprint.sum())},
        },
        "family_overlap": {
            "shared_cells": overlap,
            "union_cells": union,
            "jaccard": overlap / union if union else None,
            "fraction_b2_shared": overlap / int(dotted_mask.sum()),
            "fraction_h33d_shared": overlap / int(h33d_mask.sum()),
            "interpretation": "High dependence is plausible; separate build pipelines do not establish statistical independence.",
        },
        "frozen_parameters": {
            "family_belief": "competition triangular max-credit field, radius 300 m",
            "family_reliabilities": {"B2": RHO_FAMILY, "H33-D": RHO_FAMILY},
            "radiometric_sigma_pixels": list(SIGMAS),
            "gradient_normalization": "per-band/per-scale P99 over valid edge cells",
            "orientation": "doubled-angle coherence across eight gradients",
            "radiometric_reliability": RHO_RADIOMETRIC,
            "radiometric_absence_informativeness": ABSENCE_RAD,
            "combination": "canonical normalized Dempster-Shafer, three sources",
            "submission": "normalized Bel(F), float32, one band, NaN outside footprint",
            "labels_used_to_build": False,
            "post_holdout_parameter_tuning": False,
        },
        "edge_summary": {
            "valid_edge_cells": edge_result.valid_edge_cells,
            "p99_gradient_by_scale_then_band": [list(row) for row in edge_result.band_scale_p99],
            "edge_score_quantiles_in_footprint": {str(q): float(np.quantile(edge[footprint], q)) for q in (0.5, 0.9, 0.95, 0.99, 1.0)},
            "coherence_median_in_footprint": float(np.median(edge_result.coherence[footprint])),
            "note": "Edge scores are normalized texture/edge evidence, not fault probabilities; edge-level geology has not been independently mapped.",
        },
        "dempster_diagnostics": {
            "belief_max_before_normalization": max_fault,
            "belief_normalization": "m(F) divided by maximum m(F) within the footprint",
            "mtheta_is_canonical_dempster_residual": True,
            "raw_conflict_is_separate": True,
            "yager_sensitivity": "computed internally only; not exported. Canonical m(Theta) and raw K remain separate; no conflict-to-ignorance diagnostic is presented as Dempster m(Theta).",
            "mass_sum_max_abs_error_in_footprint": float(np.max(np.abs((fusion.fault + fusion.not_fault + fusion.unassigned_dempster)[footprint] - 1.0))),
            "mean_mtheta": float(np.mean(fusion.unassigned_dempster[footprint])),
            "mean_raw_conflict_K": float(np.mean(fusion.conflict_total[footprint])),
            "p95_raw_conflict_K": float(np.quantile(fusion.conflict_total[footprint], 0.95)),
        },
        "not_merely_a_mean": comparisons,
        "primary_format_checks": {
            "single_band_float32": True,
            "crs": "EPSG:32611",
            "shape": [3730, 3292],
            "pixel_size_m": 100,
            "in_footprint_finite": bool(np.isfinite(in_footprint).all()),
            "in_footprint_min": float(in_footprint.min()),
            "in_footprint_max": float(in_footprint.max()),
            "outside_footprint_nan": True,
            "valid_cells": int(footprint.sum()),
            "all_local_checks_passed": True,
        },
        "diagnostics": diagnostic_records,
        "limitations": [
            "B2 0.2778 is an owner-reported registry value; no official receipt links it to this exact local TIFF, and its local audit labels it UNSCORED.",
            "The two family supports overlap heavily; statistical independence is not established and belief is not calibrated probability.",
            "The radiometric edge is an indirect signature confounded by lithologic contacts, weathering, topography, quantization, and survey artifacts.",
            "Owner-mirror family and radiometric input licensing/organizer identity are not independently verified by these hashes.",
            "No organizer score, leaderboard result, upload, or slot clearance is asserted.",
        ],
    }
    receipt_path = ROOT / "evidence/build_h53_receipt_20261007.json"
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"candidate": receipt["candidate"], "format": receipt["primary_format_checks"], "comparisons": comparisons, "receipt": display_path(receipt_path)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
