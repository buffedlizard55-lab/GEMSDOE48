#!/usr/bin/env python3
"""Build the preregistered, mass-matched H56-A strain-ridge holdout probe.

This is a label-free research probe, not a recommended submission. It follows the
explicit machine-readable H56-A frozen test; the prose slate's unspecified structure-
coherence clause is documented in ``docs/research/h56-slate-erratum-20261007.md``.
It writes a GeoTIFF under ignored ``scratch/`` and a JSON receipt. No label is used.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48.geotiff import (assert_competition_grid, display_path,
                               write_float32_zeros_outside)
from gemsdoe48.h56 import deterministic_top_k, hessian_line_response, robust_unit_scale

FEATURES = ROOT / "data/raw/training_features.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
OUTPUT = ROOT / "scratch/H56-A-strain-ridge-massmatched-20261007.tif"
RECEIPT = ROOT / "evidence/h56_strain_ridge_build_20261007.json"
EXPECTED_FEATURES_SHA256 = "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5"
EXPECTED_FOOTPRINT_SHA256 = "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f"
BANDS = {
    4: "geod_2ndinv - Geodetic second invariant - measure of strain rate tensor magnitude",
    7: "geod_shearrate - Geodetic shear rate - rate of angular deformation from GPS/InSAR",
    8: "geod_dilaterate - Geodetic dilatation rate - rate of volumetric strain (expansion/contraction)",
    16: "ieq_n100a15 - Earthquake intensity or density (n=100km radius, a=15° parameters)",
}
SCALES_PX = (3.0, 6.0, 9.0)
TOP_K = 37_654
RIDGE_WEIGHT = 0.9
EARTHQUAKE_WEIGHT = 0.1
SCALE_PERCENTILE = 99.5


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def log_abs_robust(values: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, float]:
    magnitude = np.abs(np.asarray(values, dtype=np.float32)[valid])
    nonzero = magnitude[magnitude > 0]
    if not nonzero.size:
        raise ValueError("strain band has no nonzero valid values")
    scale = float(np.median(nonzero))
    if not np.isfinite(scale) or scale <= 0:
        raise ValueError("strain-band robust scale is invalid")
    transformed = np.log1p(np.abs(np.asarray(values, dtype=np.float32)) / np.float32(scale))
    return transformed.astype(np.float32, copy=False), scale


def main() -> int:
    for path, expected in ((FEATURES, EXPECTED_FEATURES_SHA256),
                           (FOOTPRINT, EXPECTED_FOOTPRINT_SHA256)):
        if not path.exists():
            raise SystemExit(f"missing {path}; restore pinned inputs before running")
        actual = sha256_file(path)
        if actual != expected:
            raise SystemExit(f"SHA-256 mismatch for {path}: expected {expected}, got {actual}")

    with rasterio.open(FOOTPRINT) as fp_ds:
        assert_competition_grid(fp_ds.profile, path=FOOTPRINT)
        footprint = fp_ds.read(1) == 1
        if fp_ds.dtypes != ("uint8",) or int(footprint.sum()) != 5_167_373:
            raise SystemExit("footprint mask failed its registered count/dtype check")

    print("[1/5] verify feature grid, band descriptions, and common valid mask")
    with rasterio.open(FEATURES) as ds:
        profile = ds.profile.copy()
        profile["count"] = 1
        assert_competition_grid(profile, path=FEATURES)
        if ds.count != 19 or ds.nodata is None:
            raise SystemExit("feature stack must have 19 bands and a nodata value")
        for index, expected in BANDS.items():
            if ds.descriptions[index - 1] != expected:
                raise SystemExit(
                    f"band {index} description drift: {ds.descriptions[index - 1]!r} != {expected!r}"
                )
        masks = [ds.read_masks(index) > 0 for index in BANDS]
        if not all(np.array_equal(masks[0], value) for value in masks[1:]):
            raise SystemExit("H56-A source bands have different nodata masks; no silent fill allowed")
        common_valid = footprint & masks[0]
        if int(common_valid.sum()) != 5_164_312:
            raise SystemExit(f"unexpected valid overlap: {int(common_valid.sum())} cells")
        nodata_cells_inside_footprint = int((footprint & ~common_valid).sum())
        feature_valid_outside_footprint = int((~footprint & masks[0]).sum())
        nodata = float(ds.nodata)
        shape = (ds.height, ds.width)
        transform = tuple(ds.transform)[:6]
        crs = ds.crs.to_string()

        # A nearest-valid extension avoids treating the large outside-footprint
        # nodata region as a sharp geophysical edge. Output candidates are still
        # restricted to the valid survey footprint.
        nearest_indices = ndi.distance_transform_edt(
            ~common_valid, return_distances=False, return_indices=True
        )
        ridge_sum = np.zeros(shape, dtype=np.float32)
        per_band_scales: dict[str, float] = {}
        per_channel_scale_norms: list[dict] = []

        print("[2/5] compute three-channel, three-scale Hessian line responses")
        for index in (4, 7, 8):
            raw = ds.read(index).astype(np.float32, copy=False)
            raw_valid = common_valid & np.isfinite(raw) & (raw != nodata)
            if not np.array_equal(raw_valid, common_valid):
                raise SystemExit(f"band {index} contains unexpected nonfinite/nodata valid cells")
            # Use nearest valid values solely as derivative context outside the
            # valid domain; those cells can never be selected for emission.
            extended = raw[nearest_indices[0], nearest_indices[1]]
            del raw
            transformed, robust_scale = log_abs_robust(extended, common_valid)
            per_band_scales[str(index)] = robust_scale
            for sigma in SCALES_PX:
                response = hessian_line_response(transformed, sigma)
                scaled, high = robust_unit_scale(response, common_valid, SCALE_PERCENTILE)
                ridge_sum += scaled
                per_channel_scale_norms.append({
                    "band": index,
                    "sigma_px": sigma,
                    "response_p99_5": high,
                })
                del response, scaled
            del extended, transformed

        print("[3/5] add the frozen weak earthquake-density term")
        quake = ds.read(16).astype(np.float32, copy=False)
        if not np.isfinite(quake[common_valid]).all() or np.any(quake[common_valid] < 0):
            raise SystemExit("earthquake density is nonfinite or negative on the valid domain")
        quake_extended = quake[nearest_indices[0], nearest_indices[1]]
        del quake
        quake_log = np.log1p(quake_extended).astype(np.float32, copy=False)
        earthquake_scaled, earthquake_p99_5 = robust_unit_scale(
            quake_log, common_valid, SCALE_PERCENTILE
        )
        ridge_mean = ridge_sum / np.float32(9.0)
        score = RIDGE_WEIGHT * ridge_mean + EARTHQUAKE_WEIGHT * earthquake_scaled
        score[~common_valid] = 0.0
        del nearest_indices, ridge_sum, ridge_mean, quake_extended, quake_log, earthquake_scaled

    print("[4/5] freeze a mass-matched top-k emission and write ignored probe GeoTIFF")
    prediction = deterministic_top_k(score, common_valid, TOP_K).astype(np.float32)
    if int(np.count_nonzero(prediction)) != TOP_K:
        raise ArithmeticError("mass-matched top-k selection returned the wrong number of cells")
    file_receipt = write_float32_zeros_outside(
        OUTPUT,
        prediction,
        profile,
        valid_mask=footprint,
        description="H56-A mass-matched strain-ridge probe; NOT slot-cleared",
        tags={
            "candidate_id": "H56-A",
            "source_sha256": EXPECTED_FEATURES_SHA256,
            "method": "log-absolute strain Hessian ridges at 3/6/9 pixels plus 0.1 earthquake term",
            "status": "research_only_not_slot_cleared",
        },
    )
    output_sha = sha256_file(OUTPUT)
    file_receipt["sha256"] = output_sha
    if file_receipt["positive_cells"] != TOP_K:
        raise ArithmeticError("written output positive-cell count changed")

    report = {
        "schema_version": 1,
        "status": "BUILT_FOR_BLOCKED_RESEARCH_VALIDATION_NOT_A_SUBMISSION_RECOMMENDATION",
        "built_utc": datetime.now(timezone.utc).isoformat(),
        "hypothesis_slate": "evidence/hypothesis_slate_h56_20261007.json",
        "preregistration_interpretation": {
            "implemented_specification": "the explicit machine-readable hypotheses[H56-A].frozen_test transform",
            "companion_markdown_mismatch": "the original slate prose also mentions structure-tensor coherence; the machine frozen_test does not specify it, and this builder does not compute it",
            "confirmation_scope": "the holdout applies to this Hessian-only screen, not to the coherence-augmented prose idea",
            "erratum": "docs/research/h56-slate-erratum-20261007.md",
        },
        "inputs": {
            "training_features": {
                "path": "data/raw/training_features.tif",
                "sha256": EXPECTED_FEATURES_SHA256,
                "bytes": FEATURES.stat().st_size,
                "origin_class": "third-party mirror of competition-provided GeoDAWN numerical feature stack; hash-pinned, not organizer-authenticated",
                "bands": {str(i): ds for i, ds in BANDS.items()},
                "crs": crs,
                "transform": list(transform),
                "nodata": nodata,
            },
            "footprint": {
                "path": "data/source_mirrors/footprint-mask.tif",
                "sha256": EXPECTED_FOOTPRINT_SHA256,
                "inside_cells": int(footprint.sum()),
                "feature_nodata_cells_inside_footprint": nodata_cells_inside_footprint,
                "feature_valid_cells_outside_footprint_ignored": feature_valid_outside_footprint,
            },
        },
        "frozen_method": {
            "strain_bands": [4, 7, 8],
            "transformation": "log1p(abs(x)/median(abs(nonzero valid x)))",
            "ridge_operator": "scale-normalized absolute Hessian line response; response = |lambda_large| * exp(-0.5*(|lambda_small|/|lambda_large|)^2)",
            "scales_px": list(SCALES_PX),
            "per_band_scale_factors": per_band_scales,
            "response_normalization": {"percentile": SCALE_PERCENTILE, "records": per_channel_scale_norms},
            "earthquake_band": 16,
            "earthquake_transform": "log1p(nonnegative band 16); P99.5 clip/scale",
            "weights": {"mean_strain_ridge": RIDGE_WEIGHT, "earthquake_density": EARTHQUAKE_WEIGHT},
            "emission": "deterministic top 37,654 valid cells; descending score then ascending row-major index",
            "label_use_in_construction": False,
        },
        "output": {
            "path": display_path(OUTPUT),
            "sha256": output_sha,
            **file_receipt,
            "slot_cleared": False,
        },
        "score_diagnostics": {
            "ridge_score_quantiles_valid": {
                str(p): float(np.percentile(score[common_valid], p)) for p in (0, 50, 90, 99, 99.5, 100)
            },
            "earthquake_log_p99_5": earthquake_p99_5,
            "valid_cells": int(common_valid.sum()),
        },
        "limitations": [
            "Feature stack bytes came from a non-organizer GitHub mirror; hash identity is not original-source authentication or license clearance.",
            "A public-map proxy pass cannot establish private-label leaderboard performance.",
            "The score is an exploratory rank field, not a calibrated fault probability.",
            "Nearest-valid extension is derivative context only; output candidates are restricted to valid in-footprint cells.",
        ],
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print("[5/5] receipt written")
    print(json.dumps({"output": display_path(OUTPUT), "sha256": output_sha, "positive_cells": TOP_K,
                      "valid_cells": int(common_valid.sum()), "receipt": display_path(RECEIPT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
