#!/usr/bin/env python3
"""Rebuild the historical PR #5 Yager-rule research candidate.

This is a separate, non-default experiment; its primary TIFF has finite zeros
outside the footprint and fails the published null/NaN-outside requirement.
It did not clear the spatial-proxy gate, has no organizer acceptance, and must not
be treated as the current rho=0.5 candidate or a submission recommendation.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.evidence import combine_yager, discounted_binary_mass, minmax_unit

NAME = "gemsdoe48-h48-ds-yager-conflict-20261006"
DOWNLOADS = ROOT / "docs" / "downloads"
OUT = DOWNLOADS / f"{NAME}.tif"
UNC = DOWNLOADS / f"{NAME}-unassigned-diagnostic.tif"
AUDIT = DOWNLOADS / f"{NAME}-audit.json"
UNIQUENESS_AUDIT = ROOT / "docs" / "data" / "uniqueness-audit.json"
INPUTS = {
    "dotted": (ROOT / "data/raw/dotted_h33_2_b2_zeros.tif", "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "tip": (ROOT / "data/raw/tip_h33d_stepover.tif", "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"),
    "template": (ROOT / "data/raw/sample_submission_template.tif", "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
}
# Heuristic discounts fixed before proxy scoring. These are not calibrated
# probabilities; the post-discount Yager rule is explicitly tested separately.
R_DOTTED, R_TIP = 0.90, 0.85


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_checked(path: Path, expected_sha256: str):
    if not path.exists():
        raise SystemExit(f"missing input {path}; restore candidate surfaces and template with the documented scripts in README.md")
    actual = sha256(path)
    if actual != expected_sha256:
        raise SystemExit(f"SHA-256 mismatch for {path}: {actual} != {expected_sha256}")
    with rasterio.open(path) as source:
        if source.count != 1:
            raise SystemExit(f"{path} has {source.count} bands; expected one")
        return source.read(1), source.profile.copy(), source.transform, source.crs


def write_tif(path: Path, data: np.ndarray, profile: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output_profile = profile.copy()
    output_profile.update(
        count=1,
        dtype="float32",
        nodata=None,
        compress="deflate",
        predictor=3,
        tiled=True,
        blockxsize=256,
        blockysize=256,
    )
    with rasterio.open(path, "w", **output_profile) as destination:
        destination.write(np.asarray(data, dtype=np.float32), 1)


def main() -> None:
    dotted, dotted_profile, dotted_transform, dotted_crs = read_checked(*INPUTS["dotted"])
    tip, tip_profile, tip_transform, tip_crs = read_checked(*INPUTS["tip"])
    template, template_profile, template_transform, template_crs = read_checked(*INPUTS["template"])

    if not (
        dotted.shape == tip.shape == template.shape
        and dotted_transform == tip_transform == template_transform
        and dotted_crs == tip_crs == template_crs
    ):
        raise SystemExit("input grids do not match exactly")
    if not (dotted_profile["count"] == tip_profile["count"] == template_profile["count"] == 1):
        raise SystemExit("all inputs must be single-band")

    footprint = np.isfinite(template)
    if not footprint.any():
        raise SystemExit("sample-submission footprint is empty")
    if np.any((dotted > 0) & ~footprint) or np.any((tip > 0) & ~footprint):
        raise SystemExit("a parent predicts positive fault mass outside the sample footprint")

    a = discounted_binary_mass(dotted, R_DOTTED)
    b = discounted_binary_mass(tip, R_TIP)
    belief, disbelief, unassigned, conflict = combine_yager(a, b)
    combined = minmax_unit(belief, footprint)
    # Range-hardened primary variant: the owner reported that NaN nodata cells
    # trigger the portal's [0,1] value check. The official page separately asks
    # for null/NaN outside bounds; that unresolved conflict is recorded below.
    combined[~footprint] = 0.0
    diagnostic = np.zeros(combined.shape, dtype=np.float32)
    diagnostic[footprint] = unassigned[footprint].astype(np.float32)

    write_tif(OUT, combined, dotted_profile)
    write_tif(UNC, diagnostic, dotted_profile)

    with rasterio.open(OUT) as output:
        reread = output.read(1)
        output_grid = {
            "bands": output.count,
            "dtype": output.dtypes[0],
            "crs": str(output.crs),
            "epsg": output.crs.to_epsg() if output.crs else None,
            "shape": list(output.shape),
            "transform": list(output.transform)[:6],
            "resolution": list(output.res),
            "nodata": output.nodata,
            "grid_matches_template": bool(
                output.shape == template.shape
                and output.transform == template_transform
                and output.crs == template_crs
            ),
        }
    with rasterio.open(UNC) as output:
        diagnostic_reread = output.read(1)
        diagnostic_grid_matches = bool(
            output.count == 1
            and output.shape == template.shape
            and output.transform == template_transform
            and output.crs == template_crs
        )

    active = footprint
    naive = (dotted.astype(np.float64) + tip.astype(np.float64)) / 2.0
    cand = reread[active].astype(np.float64)
    mean = naive[active]
    correlation = float(np.corrcoef(cand, mean)[0, 1])
    difference = cand - mean
    naive_check = {
        "pearson_correlation": correlation,
        "mean_absolute_difference": float(np.mean(np.abs(difference))),
        "root_mean_square_difference": float(np.sqrt(np.mean(difference**2))),
        "max_absolute_difference": float(np.max(np.abs(difference))),
        "pixel_identical": bool(np.array_equal(cand, mean.astype(np.float32).astype(np.float64))),
        "different_pixels": int(np.count_nonzero(cand != mean)),
        "pass_not_naive_mean": bool(np.any(difference != 0.0)),
    }

    if not UNIQUENESS_AUDIT.exists():
        raise SystemExit(f"missing historical uniqueness audit: {UNIQUENESS_AUDIT}")
    uniqueness = json.loads(UNIQUENESS_AUDIT.read_text())
    candidate_sha = sha256(OUT)
    uniqueness_matches = uniqueness.get("candidate_sha256") == candidate_sha
    zero_exact_matches = (
        uniqueness.get("exact_prediction_matches") == 0
        and uniqueness.get("exact_positive_support_matches") == 0
    )
    if not uniqueness_matches or not zero_exact_matches:
        raise SystemExit("historical uniqueness audit does not match this TIFF or reports an exact duplicate")

    format_checks = {
        "single_band_float32": bool(output_grid["bands"] == 1 and output_grid["dtype"] == "float32"),
        "epsg_32611": bool(output_grid["epsg"] == 32611),
        "sample_shape_transform_and_crs_match": output_grid["grid_matches_template"],
        "all_finite": bool(np.isfinite(reread).all()),
        "range_0_to_1_including_outside_footprint": bool(reread.min() >= 0.0 and reread.max() <= 1.0),
        "outside_footprint_zero_filled": bool(np.all(reread[~footprint] == 0.0)),
        "official_null_or_nan_outside_requirement_met": False,
        "diagnostic_grid_matches_template": diagnostic_grid_matches,
        "diagnostic_all_finite_in_range": bool(
            np.isfinite(diagnostic_reread).all()
            and diagnostic_reread.min() >= 0.0
            and diagnostic_reread.max() <= 1.0
        ),
    }
    portal_range_checks_pass = bool(
        format_checks["single_band_float32"]
        and format_checks["epsg_32611"]
        and format_checks["sample_shape_transform_and_crs_match"]
        and format_checks["all_finite"]
        and format_checks["range_0_to_1_including_outside_footprint"]
    )

    audit = {
        "schema": "GEMSDOE48-audit-v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_status": "RESEARCH CANDIDATE — NOT CLEARED FOR A COMPETITION SLOT; corrected public-proxy DTI gate failed",
        "method": "reliability-discounted binary masses; conjunctive combination; Yager transfer of conflict K to Theta; min-max normalized Bel(F)",
        "scientific_correction": "Classical normalized Dempster's rule divides non-empty masses by 1-K and removes conflict from the normalized result. Yager's modified rule transfers K to Theta. Zero-valued parents are treated here as evidence for not-fault; because these sparse detector rasters may encode silence rather than affirmative negative evidence, that semantic assumption is a major limitation.",
        "reliability_discounts_fixed_before_proxy_scoring": {"dotted": R_DOTTED, "tip": R_TIP},
        "inputs": {
            key: {"file": str(path.relative_to(ROOT)), "sha256": expected}
            for key, (path, expected) in INPUTS.items()
        },
        "input_counts_within_footprint": {
            "dotted_positive": int(((dotted > 0) & footprint).sum()),
            "tip_positive": int(((tip > 0) & footprint).sum()),
            "overlap": int(((dotted > 0) & (tip > 0) & footprint).sum()),
            "union": int((((dotted > 0) | (tip > 0)) & footprint).sum()),
            "exclusive_disagreement": int((((dotted > 0) ^ (tip > 0)) & footprint).sum()),
        },
        "output": {
            "file": str(OUT.relative_to(ROOT)),
            "sha256": candidate_sha,
            "bytes": OUT.stat().st_size,
            **output_grid,
            "min": float(reread.min()),
            "max": float(reread.max()),
            "positive_pixels": int((reread > 0).sum()),
            "format_checks": format_checks,
            "portal_range_checks_pass": portal_range_checks_pass,
            "format_note": "All cells are finite and in [0,1], with zero outside the footprint. The published competition format says null/NaN outside; this all-finite choice is a range-validator workaround, not confirmed portal acceptance.",
        },
        "unassigned_diagnostic": {
            "file": str(UNC.relative_to(ROOT)),
            "sha256": sha256(UNC),
            "min": float(diagnostic_reread.min()),
            "max": float(diagnostic_reread.max()),
            "conflict_positive_pixels": int((conflict[footprint] > 0).sum()),
            "positive_diagnostic_pixels": int((diagnostic_reread[footprint] > 0).sum()),
        },
        "naive_mean_check": naive_check,
        "mass_checks": {
            "belief_min": float(belief.min()),
            "belief_max": float(belief.max()),
            "unassigned_min": float(unassigned.min()),
            "unassigned_max": float(unassigned.max()),
            "sum_max_abs_error": float(np.max(np.abs(belief + disbelief + unassigned - 1.0))),
        },
        "historical_uniqueness": {
            "audit_file": str(UNIQUENESS_AUDIT.relative_to(ROOT)),
            "candidate_sha256_matches_audit": uniqueness_matches,
            "artifacts_compared": uniqueness.get("comparison_results"),
            "exact_prediction_matches": uniqueness.get("exact_prediction_matches"),
            "exact_positive_support_matches": uniqueness.get("exact_positive_support_matches"),
            "maximum_positive_support_jaccard": uniqueness.get("max_positive_support_jaccard"),
            "closest_artifact": uniqueness.get("closest_artifact"),
        },
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))


if __name__ == "__main__":
    main()
