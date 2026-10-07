#!/usr/bin/env python3
"""Independent local format, mass-diagnostic, and bounded-uniqueness audit for H53."""
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
from gemsdoe48.geotiff import assert_competition_grid, display_path  # noqa: E402

BUILD_RECEIPT = ROOT / "evidence/build_h53_receipt_20261007.json"
HOLDOUT = ROOT / "evidence/holdout_h53_20261007.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_tif(path: Path) -> tuple[np.ndarray, dict, tuple[str, ...]]:
    with rasterio.open(path) as dataset:
        if dataset.count != 1:
            raise ValueError(f"{path}: expected one band, got {dataset.count}")
        profile = dataset.profile.copy()
        tags = tuple(sorted(dataset.tags().items()))
        return dataset.read(1), profile, tags


def pearson(x: np.ndarray, y: np.ndarray) -> float:
    a = np.asarray(x, dtype=np.float64)
    b = np.asarray(y, dtype=np.float64)
    if a.size < 2 or a.std() == 0.0 or b.std() == 0.0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def main() -> int:
    build = json.loads(BUILD_RECEIPT.read_text(encoding="utf-8"))
    candidate_path = ROOT / build["candidate"]["path"]
    if sha256_file(candidate_path) != build["candidate"]["sha256"]:
        raise SystemExit("candidate SHA no longer matches build receipt")
    with rasterio.open(ROOT / "data/source_mirrors/footprint-mask.tif") as dataset:
        assert_competition_grid(dataset.profile, path="footprint")
        footprint = dataset.read(1) == 1

    candidate, profile, tags = read_tif(candidate_path)
    assert_competition_grid(profile, path=candidate_path)
    if profile["dtype"] != "float32" or profile["nodata"] is None or not np.isnan(profile["nodata"]):
        raise SystemExit("candidate dtype or NaN nodata metadata is not compliant")
    if not np.isfinite(candidate[footprint]).all():
        raise SystemExit("candidate has nonfinite in-footprint values")
    if np.any((candidate[footprint] < 0.0) | (candidate[footprint] > 1.0)):
        raise SystemExit("candidate values fall outside [0,1]")
    if not np.isnan(candidate[~footprint]).all():
        raise SystemExit("candidate outside-footprint cells are not all NaN")

    diagnostics = {}
    for key, info in build["diagnostics"].items():
        path = ROOT / info["path"]
        if sha256_file(path) != info["sha256"]:
            raise SystemExit(f"diagnostic {key} SHA no longer matches build receipt")
        array, diagnostic_profile, _ = read_tif(path)
        assert_competition_grid(diagnostic_profile, path=path)
        if not np.isfinite(array[footprint]).all() or not np.isnan(array[~footprint]).all():
            raise SystemExit(f"diagnostic {key} has an invalid footprint/nodata pattern")
        if np.any((array[footprint] < 0.0) | (array[footprint] > 1.0)):
            raise SystemExit(f"diagnostic {key} contains values outside [0,1]")
        diagnostics[key] = {
            "path": display_path(path),
            "sha256": sha256_file(path),
            "min": float(array[footprint].min()),
            "max": float(array[footprint].max()),
        }

    # Bounded local check: every top-level previous submission TIFF plus the
    # family-source TIFFs. This does not claim global or sibling-repository
    # uniqueness. Diagnostics are checked for hashes/format above, but are not
    # treated as prior submissions in this list.
    compare_paths = set((ROOT / "docs/downloads").glob("*.tif"))
    compare_paths.update((ROOT / "data/families").glob("*.tif"))
    compare_paths.discard(candidate_path)
    candidates = []
    exact_hash_matches = []
    exact_pixel_matches = []
    skipped = []
    for path in sorted(compare_paths):
        try:
            previous_hash = sha256_file(path)
            previous, previous_profile, _ = read_tif(path)
            if (
                previous_profile.get("width") != profile["width"]
                or previous_profile.get("height") != profile["height"]
                or previous_profile.get("crs") != profile["crs"]
                or previous_profile.get("transform") != profile["transform"]
            ):
                skipped.append({"path": display_path(path), "reason": "different grid"})
                continue
            if previous_hash == build["candidate"]["sha256"]:
                exact_hash_matches.append(display_path(path))
            prev_valid = np.where(np.isfinite(previous), previous, 0.0)[footprint].astype(np.float32)
            cand_valid = candidate[footprint]
            exact_pixels = bool(np.array_equal(cand_valid, prev_valid))
            if exact_pixels:
                exact_pixel_matches.append(display_path(path))
            correlation = pearson(cand_valid, prev_valid)
            topk = min(37_654, int(footprint.sum()))
            idx_c = np.argpartition(cand_valid, cand_valid.size - topk)[cand_valid.size - topk:]
            idx_p = np.argpartition(prev_valid, prev_valid.size - topk)[prev_valid.size - topk:]
            mask_c = np.zeros(cand_valid.size, dtype=bool); mask_c[idx_c] = True
            mask_p = np.zeros(prev_valid.size, dtype=bool); mask_p[idx_p] = True
            intersection = int((mask_c & mask_p).sum())
            union = int((mask_c | mask_p).sum())
            candidates.append({
                "path": display_path(path),
                "sha256": previous_hash,
                "pearson_in_footprint": correlation,
                "exact_pixel_match": exact_pixels,
                "top_37654_jaccard": float(intersection / union) if union else None,
            })
        except Exception as exc:  # audit should finish and document non-raster files
            skipped.append({"path": display_path(path), "reason": f"unreadable: {type(exc).__name__}: {exc}"})

    closest = sorted(candidates, key=lambda row: row["pearson_in_footprint"], reverse=True)[:5]
    holdout = json.loads(HOLDOUT.read_text(encoding="utf-8"))
    report = {
        "schema_version": 1,
        "audited_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_LOCAL_FORMAT_AND_BOUNDED_UNIQUENESS_ONLY_NOT_ORGANIZER_ACCEPTANCE",
        "candidate": {
            "name": build["candidate"]["unique_submission_name"],
            "path": display_path(candidate_path),
            "bytes": candidate_path.stat().st_size,
            "sha256": sha256_file(candidate_path),
            "single_band_float32": True,
            "grid": "EPSG:32611, 100 m, 3292 x 3730",
            "in_footprint_cells": int(footprint.sum()),
            "finite_in_footprint": bool(np.isfinite(candidate[footprint]).all()),
            "min": float(candidate[footprint].min()),
            "max": float(candidate[footprint].max()),
            "positive_in_footprint": int(np.count_nonzero(candidate[footprint] > 0.0)),
            "outside_is_nan": bool(np.isnan(candidate[~footprint]).all()),
            "tags": dict(tags),
        },
        "diagnostics": diagnostics,
        "bounded_uniqueness": {
            "comparison_universe": "top-level docs/downloads TIFFs (historical candidate/submission files) plus data/families source TIFFs; different-grid and unreadable items recorded as skipped",
            "same_grid_files_compared": len(candidates),
            "exact_sha256_matches": exact_hash_matches,
            "exact_in_footprint_pixel_matches": exact_pixel_matches,
            "exact_matches_found": bool(exact_hash_matches or exact_pixel_matches),
            "closest_local_maps_by_pearson": closest,
            "skipped": skipped,
            "scope_limit": "This bounded local-repository audit does not establish uniqueness across sibling repositories, organizer uploads, or the competition portal.",
        },
        "not_a_mean_review": {
            "vs_two_family_mean": build["not_merely_a_mean"]["vs_two_family_naive_mean"],
            "interpretation": "The TIFF is not pixelwise the family mean, but its Pearson correlation and budget-matched top-k overlap are reported candidly; mathematical difference is not evidence of useful new ranking signal.",
        },
        "holdout_decision": {
            "passes_preregistered_proxy_gate": holdout["preregistered_gate"]["passes_preregistered_proxy_gate"],
            "slot_cleared": False,
            "reason": "The public spatial holdout is a proxy only; no organizer score or file-to-score receipt exists.",
        },
    }
    output = ROOT / "evidence/h53_submission_validation_20261007.json"
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "candidate": report["candidate"]["path"],
        "format": {key: report["candidate"][key] for key in ("single_band_float32", "in_footprint_cells", "min", "max", "positive_in_footprint", "outside_is_nan")},
        "same_grid_files_compared": len(candidates),
        "exact_matches_found": report["bounded_uniqueness"]["exact_matches_found"],
        "closest_local_maps": closest,
        "proxy_gate_passed": report["holdout_decision"]["passes_preregistered_proxy_gate"],
        "report": display_path(output),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
