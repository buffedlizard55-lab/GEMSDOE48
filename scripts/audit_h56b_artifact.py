#!/usr/bin/env python3
"""Independent audit of the generated H56B GeoTIFF and diagnostic rasters.

Recomputes the raster from pinned parents and the recorded recipe without
importing the build script or its BPA/Dempster helper functions. Writes a
machine-readable audit receipt. This verifies file identity/format and
implementation reproducibility, not geological validity or organizer acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
BUILD_RECEIPT = ROOT / "evidence/build_h56b_belief_receipt_20261007.json"
OLD_ZERO_FILE = ROOT / "docs/downloads/GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif"
OUT = ROOT / "evidence/audit_h56b_artifact_20261007.json"
PINS = {
    "dotted": ("data/families/dotted_b2_prune_02778.tif", "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "tip": ("data/families/tip_stepover_r30_02632.tif", "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"),
    "backbone": ("data/raw/scored/h19_5_01922.tif", "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d"),
    "template": ("data/raw/sample_submission_template.tif", "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
    "labels": ("data/raw/labels_catalogue.tif", "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    "footprint_mask": ("data/source_mirrors/footprint-mask.tif", "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f"),
}
R_DOT = 0.95
R_TIP = 0.95 * 0.2632 / 0.2778
A_ON, A_OFF, FLANK_PX = 0.5, 0.2, 2.0


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as src:
        for chunk in iter(lambda: src.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path: Path):
    with rasterio.open(path) as ds:
        return ds.read(1), ds.profile.copy(), ds.transform, ds.crs


def close(a, b, tol=2e-7) -> bool:
    return np.allclose(a, b, rtol=0.0, atol=tol, equal_nan=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--build-receipt", type=Path, default=BUILD_RECEIPT)
    parser.add_argument("--output", type=Path, default=OUT)
    args = parser.parse_args()
    build_receipt = args.build_receipt.resolve()
    output_path = args.output.resolve()
    receipt = json.loads(build_receipt.read_text())
    pin_results = {}
    for key, (relative, expected) in PINS.items():
        path = ROOT / relative
        actual = sha256(path)
        if actual != expected:
            raise SystemExit(f"input pin mismatch for {key}: {actual} != {expected}")
        pin_results[key] = {"path": relative, "sha256": actual, "verified": True}

    tmpl, template_profile, transform, crs = read(ROOT / PINS["template"][0])
    labels, label_profile, labels_transform, labels_crs = read(ROOT / PINS["labels"][0])
    footprint_band, footprint_profile, footprint_transform, footprint_crs = read(ROOT / PINS["footprint_mask"][0])
    footprint = labels != -1
    if not (template_profile["dtype"] == "float32" and label_profile["dtype"] == "float32"):
        # The labels mirror is permitted to be integer in future revisions; grid equality is the key invariant.
        pass
    if not (transform == labels_transform == footprint_transform and crs == labels_crs == footprint_crs):
        raise SystemExit("template, labels, and footprint grids differ")
    mask_agreement = {
        "template_finite_vs_labels": int(np.count_nonzero(np.isfinite(tmpl) != footprint)),
        "labels_vs_pinned_footprint": int(np.count_nonzero(footprint != (footprint_band == 1))),
        "footprint_cells": int(footprint.sum()),
    }
    if mask_agreement["template_finite_vs_labels"] or mask_agreement["labels_vs_pinned_footprint"]:
        raise SystemExit(f"footprint masks differ: {mask_agreement}")

    dotted, _, d_transform, d_crs = read(ROOT / PINS["dotted"][0])
    tip, _, t_transform, t_crs = read(ROOT / PINS["tip"][0])
    backbone, _, b_transform, b_crs = read(ROOT / PINS["backbone"][0])
    if not (d_transform == t_transform == b_transform == transform and d_crs == t_crs == b_crs == crs):
        raise SystemExit("one or more pinned source grids differ from the output grid")
    dot_mask = (dotted > 0) & footprint
    tip_mask = (tip > 0) & footprint
    s_dot = np.maximum(1.0 - ndi.distance_transform_edt(~dot_mask) / 3.0, 0.0).astype(np.float32)
    s_tip = np.maximum(1.0 - ndi.distance_transform_edt(~tip_mask) / 3.0, 0.0).astype(np.float32)
    catalogue = labels == 1
    d_catalogue = ndi.distance_transform_edt(~catalogue)
    backbone_mask = np.nan_to_num(backbone.astype(np.float32), nan=0.0) > 0
    on_backbone = ndi.distance_transform_edt(~backbone_mask) <= 1.0
    absence_tip = np.where(on_backbone, A_ON, A_OFF).astype(np.float32)
    absence_dot = absence_tip.copy()
    flank_px = receipt["recipe"].get("flank_absence_dotted_only_px")
    if flank_px is not None:
        absence_dot[(d_catalogue <= float(flank_px)) & footprint] = 1.0

    def construct(support: np.ndarray, reliability: float, absence: np.ndarray):
        support64 = support.astype(np.float64)
        absence64 = absence.astype(np.float64)
        f = (reliability * support64).astype(np.float32).astype(np.float64)
        n = (reliability * (1.0 - support64) * absence64).astype(np.float32).astype(np.float64)
        u = (1.0 - f - n).astype(np.float32).astype(np.float64)
        return f, n, u

    fd, nd, ud = construct(s_dot, R_DOT, absence_dot)
    ft, nt, ut = construct(s_tip, R_TIP, absence_tip)
    conflict = fd * nt + nd * ft
    denominator = 1.0 - conflict
    if np.any(denominator[footprint] <= 1e-12):
        raise SystemExit("total/numerical conflict encountered in the footprint")
    raw_belief = (fd * ft + fd * ut + ud * ft) / denominator
    not_belief = (nd * nt + nd * ut + ud * nt) / denominator
    theta = (ud * ut) / denominator
    if np.max(np.abs((raw_belief + not_belief + theta)[footprint] - 1.0)) > 3e-7:
        raise SystemExit("independent combined masses do not sum to one")
    maximum = float(raw_belief[footprint].max())
    expected = np.where(footprint, raw_belief / maximum, np.nan).astype(np.float32)
    expected_theta = np.where(footprint, theta, np.nan).astype(np.float32)
    expected_conflict = np.where(footprint, conflict, np.nan).astype(np.float32)
    expected_support_difference = np.where(footprint, np.abs(s_dot - s_tip), np.nan).astype(np.float32)

    primary_info = receipt["artifacts"]["primary"]
    primary_path = ROOT / primary_info["path"]
    primary, profile, output_transform, output_crs = read(primary_path)
    if sha256(primary_path) != primary_info["sha256"]:
        raise SystemExit("primary GeoTIFF SHA-256 does not match the build receipt")
    if output_transform != transform or output_crs != crs:
        raise SystemExit("primary GeoTIFF grid differs from official template")
    if profile["dtype"] != "float32" or profile["count"] != 1 or not np.isnan(profile.get("nodata", 0.0)):
        raise SystemExit(f"unexpected primary GeoTIFF profile: {profile}")
    if not np.isfinite(primary[footprint]).all() or not np.isnan(primary[~footprint]).all():
        raise SystemExit("primary values must be finite in footprint and NaN outside")
    if primary[footprint].min() < 0.0 or primary[footprint].max() > 1.0:
        raise SystemExit("primary footprint values are not normalized to [0,1]")
    if not close(primary, expected):
        raise SystemExit("primary does not reproduce from independent recomputation")

    diagnostics = {}
    expected_diagnostics = {
        "mtheta": expected_theta,
        "conflict": expected_conflict,
        "support_difference": expected_support_difference,
    }
    for key, wanted in expected_diagnostics.items():
        meta = receipt["artifacts"]["diagnostics"][key]
        path = ROOT / meta["path"]
        arr, diag_profile, diag_transform, diag_crs = read(path)
        if sha256(path) != meta["sha256"]:
            raise SystemExit(f"diagnostic SHA-256 mismatch for {key}")
        if diag_transform != transform or diag_crs != crs or diag_profile["dtype"] != "float32":
            raise SystemExit(f"diagnostic grid/type mismatch for {key}")
        if not close(arr, wanted):
            raise SystemExit(f"diagnostic {key} does not reproduce independently")
        diagnostics[key] = {
            "path": meta["path"],
            "sha256": meta["sha256"],
            "matches_independent_recomputation": True,
            "outside_is_nan": bool(np.isnan(arr[~footprint]).all()),
        }

    mean_kernel_raw = 0.5 * (s_dot.astype(np.float64) + s_tip.astype(np.float64))
    mean_kernel = mean_kernel_raw / mean_kernel_raw[footprint].max()
    mean_binary = 0.5 * (dot_mask.astype(np.float64) + tip_mask.astype(np.float64))
    delta = np.abs(primary[footprint].astype(np.float64) - mean_kernel[footprint])
    support = (dot_mask | tip_mask) & footprint
    comparison = {
        "is_identical_to_normalized_kernel_mean": bool(np.array_equal(primary[footprint], mean_kernel[footprint])),
        "normalized_kernel_mean_pearson_r": float(np.corrcoef(primary[footprint], mean_kernel[footprint])[0, 1]),
        "normalized_kernel_mean_mae": float(delta.mean()),
        "normalized_kernel_mean_max_abs_difference": float(delta.max()),
        "fraction_footprint_diff_gt_0_05": float((delta > 0.05).mean()),
        "fraction_footprint_diff_gt_0_05_count": int((delta > 0.05).sum()),
        "normalized_binary_mean_pearson_r": float(np.corrcoef(primary[footprint], mean_binary[footprint])[0, 1]),
        "is_identical_to_either_mean": bool(
            np.array_equal(primary[footprint], mean_binary[footprint])
            or np.array_equal(primary[footprint], mean_kernel[footprint])
        ),
        "interpretation": "not the arithmetic mean; highly correlated with the normalized kernel mean, but materially different at a minority of cells",
    }
    if comparison["is_identical_to_either_mean"]:
        raise SystemExit("primary unexpectedly equals one of the arithmetic means")

    old_compatibility = {"checked": False}
    if OLD_ZERO_FILE.exists():
        old, _, old_transform, old_crs = read(OLD_ZERO_FILE)
        old_compatibility = {
            "checked": True,
            "old_path": str(OLD_ZERO_FILE.relative_to(ROOT)),
            "old_sha256": sha256(OLD_ZERO_FILE),
            "same_grid": bool(old_transform == transform and old_crs == crs),
            "inside_footprint_exactly_equal": bool(np.array_equal(primary[footprint], old[footprint])),
            "inside_footprint_max_abs_difference": float(np.max(np.abs(primary[footprint] - old[footprint]))),
            "comparison_scope": "only the old file's outside-zero encoding is excluded; byte identity is not expected",
        }

    report = {
        "schema_version": 1,
        "audited_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_FORMAT_AND_RECOMPUTATION_NOT_VALIDITY_OR_ACCEPTANCE",
        "input_pins": pin_results,
        "footprint_agreement": mask_agreement,
        "independent_recomputation": {
            "method": "separate implementation in this audit script; no builder module imported",
            "bpa_mass_sum_max_abs_error": float(np.max(np.abs((raw_belief + not_belief + theta)[footprint] - 1.0))),
            "conflict_K_max_footprint": float(conflict[footprint].max()),
            "mtheta_min_footprint": float(theta[footprint].min()),
            "mtheta_max_footprint": float(theta[footprint].max()),
            "primary_matches_with_atol_2e_7": True,
            "diagnostics": diagnostics,
        },
        "primary": {
            "path": primary_info["path"],
            "sha256": primary_info["sha256"],
            "dtype": profile["dtype"],
            "crs": str(output_crs),
            "width": profile["width"],
            "height": profile["height"],
            "nodata_is_nan": bool(np.isnan(profile["nodata"])),
            "outside_cells_all_nan": bool(np.isnan(primary[~footprint]).all()),
            "finite_footprint_range": [float(primary[footprint].min()), float(primary[footprint].max())],
        },
        "not_the_arithmetic_mean": comparison,
        "prior_h56_zero_outside_artifact_comparison": old_compatibility,
        "limitations": [
            "This audit verifies reproducibility and geospatial file invariants, not geological truth or Dempster-Shafer assumption validity.",
            "The parent sources overlap and source independence is not established.",
            "Discount and absence parameters are heuristic, partly informed by owner-reported scores, and not calibrated reliabilities.",
            "An in-range float32 EPSG:32611 GeoTIFF is not proof of portal acceptance.",
        ],
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "output": str(output_path.relative_to(ROOT)),
        "status": report["status"],
        "primary": report["primary"],
        "not_the_arithmetic_mean": comparison,
        "old_compatibility": old_compatibility,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
