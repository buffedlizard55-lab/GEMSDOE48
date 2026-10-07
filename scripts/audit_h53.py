#!/usr/bin/env python3
"""Independent uniqueness + integrity audit of the H53 candidate.

Answers, from the written bytes alone (nothing is taken from the build receipt):

1. Does the primary SHA-256 collide with ANY other raster or hash recorded in this
   repository?  (byte-level uniqueness)
2. Is the emitted pixel set identical to, or a superset of, any previously shipped
   candidate?  (content-level uniqueness)
3. Is the 0.2778 live-best core preserved *exactly*, pixel for pixel?
4. Are the hard format invariants satisfied: single band float32, EPSG:32611,
   3730 x 3292, 100 m, values in {0,1} subset of [0,1], all-finite, zero outside
   the footprint, no positive on or within 200 m of the public catalogue?

Usage:  python scripts/audit_h53.py [--primary PATH] [--output PATH]
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
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48.geotiff import HEIGHT, TRANSFORM, WIDTH, assert_competition_grid  # noqa: E402

CORE = ROOT / "data/families/dotted_b2_prune_02778.tif"
CATALOGUE = ROOT / "data/official/labels.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
SCAN_ROOTS = ("data", "docs/downloads", "registry")
DEFAULT_PRIMARY = ROOT / ("docs/downloads/GEMSDOE48-H53-conduit-conflict-priced-"
                          "20261007-055da9855353-zeros-outside.tif")


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_mask(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        return np.nan_to_num(ds.read(1).astype(np.float64), nan=0.0) > 0.5


def jaccard(a: np.ndarray, b: np.ndarray) -> float:
    inter = int((a & b).sum())
    union = int((a | b).sum())
    return inter / union if union else 1.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary", type=Path, default=DEFAULT_PRIMARY)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "evidence/h53_uniqueness_audit_20261007.json")
    args = parser.parse_args()
    if not args.primary.exists():
        raise SystemExit(f"primary artifact not found: {args.primary}")

    with rasterio.open(args.primary) as ds:
        assert_competition_grid(ds.profile, path=args.primary)
        dtype = ds.dtypes[0]
        nodata = ds.nodata
        crs = ds.crs.to_string()
        transform = tuple(ds.transform)[:6]
        bands = ds.count
        values = ds.read(1)
        tags = ds.tags()
    finite = np.isfinite(values)
    emission = values > 0.5
    footprint = read_mask(FOOTPRINT)
    catalogue = read_mask(CATALOGUE)
    core = read_mask(CORE)
    catalogue_distance_m = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))

    primary_sha = sha256_file(args.primary)

    # ---- 1. byte-level uniqueness across every recorded hash and every local raster
    collisions: list[dict] = []
    scanned = 0
    for root_name in SCAN_ROOTS:
        for path in sorted((ROOT / root_name).rglob("*")):
            if not path.is_file() or path.resolve() == args.primary.resolve():
                continue
            if path.suffix.lower() in {".tif", ".tiff"}:
                scanned += 1
                other = sha256_file(path)
                if other == primary_sha:
                    collisions.append({"path": str(path.relative_to(ROOT)), "sha256": other})
            elif path.suffix.lower() == ".json":
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if primary_sha in text and "h53" not in path.name.lower():
                    collisions.append({"path": str(path.relative_to(ROOT)),
                                       "reason": "sha256 appears in a pre-existing receipt"})

    # ---- 2./3. content-level uniqueness and core preservation
    comparisons: list[dict] = []
    identical: list[str] = []
    same_candidate: list[str] = []
    content_id = str(tags.get("content_id", ""))
    for root_name in ("data", "docs/downloads"):
        for path in sorted((ROOT / root_name).rglob("*.tif")):
            if path.resolve() == args.primary.resolve():
                continue
            if content_id and content_id in path.name:
                # the NaN-outside twin and the diagnostic layers of THIS candidate
                # share its content id by construction; they are not prior work
                same_candidate.append(str(path.relative_to(ROOT)))
                continue
            try:
                with rasterio.open(path) as ds:
                    if ds.count != 1 or ds.width != WIDTH or ds.height != HEIGHT:
                        continue
                    other = np.nan_to_num(ds.read(1).astype(np.float64), nan=0.0) > 0.5
            except Exception:  # noqa: BLE001 - unreadable mirrors are skipped, not fatal
                continue
            if not other.any():
                continue
            inter = int((emission & other).sum())
            comparisons.append({
                "path": str(path.relative_to(ROOT)), "other_positive_px": int(other.sum()),
                "intersection_px": inter,
                "jaccard": jaccard(emission, other),
                "candidate_is_superset_of_other": bool(inter == int(other.sum())),
                "candidate_is_identical_to_other": bool(inter == int(other.sum())
                                                        == int(emission.sum())),
            })
            if inter == int(other.sum()) == int(emission.sum()):
                identical.append(str(path.relative_to(ROOT)))
    comparisons.sort(key=lambda c: -c["jaccard"])

    core_intersection = int((emission & core).sum())
    checks = {
        "single_band": bands == 1,
        "dtype_float32": dtype == "float32",
        "crs_epsg_32611": crs == "EPSG:32611",
        "dimensions_3730x3292": values.shape == (HEIGHT, WIDTH),
        "transform_100m": transform == tuple(TRANSFORM)[:6],
        "all_cells_finite": bool(finite.all()),
        "nodata_unset": nodata is None,
        "all_cells_in_range_0_1": bool(values.min() >= 0.0 and values.max() <= 1.0),
        "value_set_is_binary": sorted(set(np.unique(values).tolist())) == [0.0, 1.0],
        "zeros_outside_footprint": bool(np.array_equal(values[~footprint],
                                                       np.zeros(int((~footprint).sum()), dtype=np.float32))),
        "no_positive_outside_footprint": int((emission & ~footprint).sum()) == 0,
        "no_positive_on_catalogue": int((emission & catalogue).sum()) == 0,
        "no_positive_within_200m_of_catalogue": int(
            (emission & (catalogue_distance_m <= 200.0)).sum()) == 0,
        "core_preserved_exactly": core_intersection == int(core.sum()),
        "core_pixel_count": int(core.sum()),
        "no_sha256_collision": not collisions,
        "not_identical_to_any_prior_candidate": not identical,
        "portal_range_error_immune": bool(finite.all() and values.min() >= 0.0 and values.max() <= 1.0),
    }
    receipt = {
        "status": "PASS_LOCAL_AUDIT_NOT_ORGANIZER_ACCEPTANCE" if all(checks.values()) else "FAIL",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "auditor": str(Path(__file__).resolve().relative_to(ROOT)),
        "primary": {
            "path": str(args.primary.relative_to(ROOT)), "sha256": primary_sha,
            "bytes": args.primary.stat().st_size, "positive_px": int(emission.sum()),
            "emitted_fraction_of_footprint": float(emission.sum() / footprint.sum()),
            "added_over_core": int(emission.sum()) - int(core.sum()),
            "tags": tags,
        },
        "checks": checks,
        "all_checks_passed": bool(all(checks.values())),
        "byte_collisions": collisions,
        "identical_prior_candidates": identical,
        "rasters_scanned_for_sha_collision": scanned,
        "same_candidate_files_excluded_by_content_id": same_candidate,
        "rasters_compared_pixelwise": len(comparisons),
        "top_10_most_similar_prior_candidates": comparisons[:10],
        "caveats": [
            "Byte-level uniqueness is a SHA-256 statement about this repository's own files only.",
            "Pixel-level uniqueness is reported as Jaccard against every same-grid raster here; "
            "a Jaccard below 1.0 means the emitted set is not identical to any prior candidate.",
            "The candidate deliberately CONTAINS the 37,654 px live-best core; that is a design "
            "choice (the core's recovered truth cannot be lost), not a copy of a prior submission.",
            "No organizer score, acceptance, or leaderboard position is claimed by this audit.",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": receipt["status"], "checks": checks,
                      "added_over_core": receipt["primary"]["added_over_core"],
                      "top_similar": comparisons[:4],
                      "receipt": str(args.output.relative_to(ROOT))}, indent=2))
    return 0 if receipt["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
