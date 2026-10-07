#!/usr/bin/env python3
"""Build preregistered H53-A: C plus strike-coherent regional 3DEP scarp cells.

This builder does not read the SGMC holdout truth. It reads only the already
pinned scarp product, public catalogue exclusion raster, dotted parent C, and
finite competition footprint. See docs/research/hypotheses-h53-20261007.md and
its frozen JSON receipt for the complete construction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

from gemsdoe48.geotiff import assert_competition_grid, display_path
from gemsdoe48.scarp_coherence import strike_coherent_scarp_score

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PRODUCT = ROOT / "data/external/h52_scarp3m_100m.tif"
DEFAULT_BASE = ROOT / "data/families/dotted_b2_prune_02778.tif"
DEFAULT_LABELS = ROOT / "data/official/labels.tif"
DEFAULT_FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
DEFAULT_OUTPUT_DIR = ROOT / "docs/downloads"
DEFAULT_RECEIPT = ROOT / "evidence/build_h53_receipt_20261007.json"
SLATE = ROOT / "evidence/hypothesis_slate_h53_20261007.json"

PINNED_SHA256 = {
    "product": "b5e53d67c3a7d3d1ca44ae04ae1e84d8574857da3fcd5e34ba47276d6c04b923",
    "base": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "labels": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    "footprint": "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f",
}
EXPECTED_SHAPE = (3730, 3292)
EXPECTED_C_DOTS = 37_654
EXPECTED_FOOTPRINT = 5_167_373
EXPECTED_CATALOGUE = 60_988
EXPECTED_ADDITIONS = 12_000
MIN_DIST_PX = 2.8284271247461903


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_hash(path: Path, expected: str, name: str) -> str:
    got = sha256_file(path)
    if got != expected:
        raise SystemExit(f"{name} SHA-256 {got} does not match the frozen value {expected}")
    return got


def assert_spatial_grid_equal(profile_a: dict, profile_b: dict, *, name_a: str, name_b: str) -> None:
    """Compare spatial grid metadata while allowing multi-band source products."""
    keys = ("width", "height", "crs", "transform")
    differences = [key for key in keys if profile_a.get(key) != profile_b.get(key)]
    if differences:
        raise ValueError(f"spatial grid mismatch between {name_a} and {name_b}: {', '.join(differences)}")


def read_scaled_product(path: Path) -> tuple[dict[str, np.ndarray], dict]:
    layers: dict[str, np.ndarray] = {}
    with rasterio.open(path) as ds:
        profile = ds.profile.copy()
        if ds.count != 7:
            raise ValueError(f"H52 product must contain seven bands, got {ds.count}")
        tags = ds.tags()
        names = list(ds.descriptions)
        required = {"h_gate12", "strike_at", "cover"}
        if not required.issubset(names):
            raise ValueError(f"missing H53-A bands: {sorted(required - set(names))}")
        for name in required:
            index = names.index(name) + 1
            values = ds.read(index).astype(np.float32)
            valid = np.isfinite(values)
            if ds.nodata is not None:
                valid &= values != ds.nodata
            scale_tag = f"SCALE_{name}"
            if scale_tag not in tags:
                raise ValueError(f"missing declared scale tag {scale_tag}")
            values /= float(tags[scale_tag])
            values[~valid] = np.nan
            layers[name] = values
    return layers, profile


def poisson_thin(
    order_rows: np.ndarray,
    order_cols: np.ndarray,
    occupied: np.ndarray,
    n_max: int,
    min_dist: float,
) -> tuple[np.ndarray, np.ndarray]:
    """Greedy deterministic Poisson thinning with a disk in cell units."""
    rows = np.asarray(order_rows)
    cols = np.asarray(order_cols)
    occupied_mask = np.asarray(occupied, dtype=bool)
    if not isinstance(n_max, (int, np.integer)) or n_max < 0:
        raise ValueError("n_max must be a nonnegative integer")
    if not np.isfinite(min_dist) or min_dist <= 0:
        raise ValueError("min_dist must be positive and finite")
    if occupied_mask.ndim != 2:
        raise ValueError("occupied must be a two-dimensional mask")
    if rows.ndim != 1 or cols.ndim != 1 or rows.shape != cols.shape:
        raise ValueError("order_rows and order_cols must be same-shaped one-dimensional arrays")
    if rows.dtype.kind not in "iu" or cols.dtype.kind not in "iu":
        raise ValueError("candidate coordinates must be integers")
    if rows.size and (
        np.any(rows < 0) or np.any(cols < 0)
        or np.any(rows >= occupied_mask.shape[0])
        or np.any(cols >= occupied_mask.shape[1])
    ):
        raise ValueError("candidate coordinates must be within the occupied mask")
    if n_max == 0 or rows.size == 0:
        return np.asarray([], dtype=np.int64), np.asarray([], dtype=np.int64)
    radius = int(np.ceil(min_dist))
    yy, xx = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    disk = (yy * yy + xx * xx) <= min_dist * min_dist + 1e-12
    padded = np.pad(occupied_mask, radius)
    kept_rows: list[int] = []
    kept_cols: list[int] = []
    for row, col in zip(rows, cols):
        window = padded[row:row + 2 * radius + 1, col:col + 2 * radius + 1]
        if np.any(window & disk):
            continue
        padded[row + radius, col + radius] = True
        kept_rows.append(int(row))
        kept_cols.append(int(col))
        if len(kept_rows) >= n_max:
            break
    return np.asarray(kept_rows, dtype=np.int64), np.asarray(kept_cols, dtype=np.int64)


def write_nan_submission(path: Path, binary: np.ndarray, footprint: np.ndarray, profile: dict) -> None:
    output = np.where(footprint, np.asarray(binary, dtype=np.float32), np.nan).astype(np.float32)
    out_profile = dict(profile)
    out_profile.update(
        driver="GTiff",
        dtype="float32",
        count=1,
        nodata=np.nan,
        compress="deflate",
        predictor=2,
        tiled=False,
    )
    out_profile.pop("blockxsize", None)
    out_profile.pop("blockysize", None)
    path.parent.mkdir(parents=True, exist_ok=True)
    with rasterio.open(path, "w", **out_profile) as dst:
        dst.write(output, 1)
        dst.update_tags(
            candidate_id="H53-A",
            method="C plus 12,000 Poisson-spaced strike-coherent 3DEP scarp additions",
            source_product_sha256=PINNED_SHA256["product"],
            source_base_sha256=PINNED_SHA256["base"],
            submission_status="UNSCORED_RESEARCH_CANDIDATE_NOT_SLOT_CLEARED",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--product", type=Path, default=DEFAULT_PRODUCT)
    parser.add_argument("--base", type=Path, default=DEFAULT_BASE)
    parser.add_argument("--labels", type=Path, default=DEFAULT_LABELS)
    parser.add_argument("--footprint", type=Path, default=DEFAULT_FOOTPRINT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--receipt", type=Path, default=DEFAULT_RECEIPT)
    parser.add_argument("--n-add", type=int, default=EXPECTED_ADDITIONS)
    args = parser.parse_args()

    if args.n_add != EXPECTED_ADDITIONS:
        raise SystemExit(
            f"H53-A preregistered budget is exactly {EXPECTED_ADDITIONS}; got {args.n_add}"
        )
    if not SLATE.is_file():
        raise SystemExit(f"frozen H53 slate not found: {SLATE}")
    slate_hash = sha256_file(SLATE)
    product_hash = require_hash(args.product, PINNED_SHA256["product"], "3DEP-derived product")
    base_hash = require_hash(args.base, PINNED_SHA256["base"], "dotted parent C")
    labels_hash = require_hash(args.labels, PINNED_SHA256["labels"], "catalogue label mirror")
    footprint_hash = require_hash(args.footprint, PINNED_SHA256["footprint"], "footprint mask")

    layers, product_profile = read_scaled_product(args.product)
    with rasterio.open(args.base) as ds:
        assert_competition_grid(ds.profile, path=args.base)
        base_profile = ds.profile.copy()
        base_values = ds.read(1)
    with rasterio.open(args.labels) as ds:
        assert_competition_grid(ds.profile, path=args.labels)
        labels_profile = ds.profile.copy()
        labels = ds.read(1)
    with rasterio.open(args.footprint) as ds:
        assert_competition_grid(ds.profile, path=args.footprint)
        footprint_profile = ds.profile.copy()
        footprint_raw = ds.read(1)
    for profile, path in (
        (product_profile, args.product),
        (base_profile, args.base),
        (labels_profile, args.labels),
    ):
        assert_spatial_grid_equal(footprint_profile, profile, name_a=str(args.footprint), name_b=str(path))

    footprint = footprint_raw == 1
    if footprint.shape != EXPECTED_SHAPE:
        raise SystemExit(f"unexpected grid shape: {footprint.shape}")
    if int(footprint.sum()) != EXPECTED_FOOTPRINT:
        raise SystemExit(f"footprint count {footprint.sum()} != frozen {EXPECTED_FOOTPRINT}")
    catalogue = (labels > 0) & footprint
    if int(catalogue.sum()) != EXPECTED_CATALOGUE:
        raise SystemExit(f"catalogue count {catalogue.sum()} != frozen {EXPECTED_CATALOGUE}")
    if not np.isin(base_values[footprint], (0.0, 1.0)).all():
        raise SystemExit("dotted parent C is not binary in the finite footprint")
    base = (base_values > 0.0) & footprint
    if int(base.sum()) != EXPECTED_C_DOTS:
        raise SystemExit(f"C positive count {base.sum()} != frozen {EXPECTED_C_DOTS}")

    coherent, support_count, score = strike_coherent_scarp_score(
        layers["h_gate12"], layers["strike_at"], layers["cover"],
        min_height_m=0.30,
        min_cover=0.90,
        strike_tolerance_deg=15.0,
        min_supported_samples=4,
    )
    distance_to_catalogue = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    distance_to_base = distance_transform_edt(~base, sampling=(100.0, 100.0))
    eligible = coherent & footprint & (distance_to_catalogue > 200.0) & (distance_to_base > 200.0)
    rows, cols = np.nonzero(eligible)
    if rows.size == 0:
        raise SystemExit("H53-A produced no eligible coherent cells")
    # Stable, explicit row-major tie-break after descending physical score.
    order = np.lexsort((cols, rows, -score[rows, cols]))
    rows, cols = rows[order], cols[order]
    accepted_rows, accepted_cols = poisson_thin(rows, cols, base, args.n_add, MIN_DIST_PX)
    if accepted_rows.size != args.n_add:
        raise SystemExit(
            f"only {accepted_rows.size} cells passed the frozen rule; required {args.n_add}; "
            "do not relax the frozen criteria after seeing holdout scores"
        )

    candidate = base.copy()
    candidate[accepted_rows, accepted_cols] = True
    if int(candidate.sum()) != EXPECTED_C_DOTS + args.n_add:
        raise SystemExit("candidate count does not equal base plus the frozen addition budget")
    if not np.array_equal(candidate & ~footprint, np.zeros_like(footprint)):
        raise SystemExit("candidate has positive cells outside the footprint")

    timestamp = datetime.now(timezone.utc).isoformat()
    note = (
        "GEMSDOE48-H53 | C + 12k Poisson dots ranked by 500m strike-coherent 3DEP scarp support; "
        "proxy-tested research only; NOT slot-cleared."
    )
    if len(note) > 200:
        raise SystemExit("paste-ready note exceeds 200 characters")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=".h53-", suffix=".tif", dir=args.output_dir, delete=False) as tmp:
        temp_path = Path(tmp.name)
    try:
        write_nan_submission(temp_path, candidate, footprint, base_profile)
        output_hash = sha256_file(temp_path)
        output_path = args.output_dir / (
            f"GEMSDOE48-H53-STRIKE-COHERENCE-20261007-{output_hash[:12]}-nan-outside.tif"
        )
        if output_path.exists():
            if sha256_file(output_path) != output_hash:
                raise SystemExit(f"refusing to overwrite nonidentical output: {output_path}")
            temp_path.unlink()
        else:
            os.replace(temp_path, output_path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    selected_heights = layers["h_gate12"][accepted_rows, accepted_cols]
    selected_support = support_count[accepted_rows, accepted_cols]
    receipt = {
        "schema_version": 1,
        "status": "BUILT_FOR_RESEARCH_NOT_SLOT_CLEARED",
        "candidate_id": "H53-A",
        "generated_utc": timestamp,
        "preregistration": {
            "document": display_path(ROOT / "docs/research/hypotheses-h53-20261007.md"),
            "json": display_path(SLATE),
            "json_sha256": slate_hash,
        },
        "candidate_name": output_path.stem,
        "portal_note": note,
        "portal_note_length": len(note),
        "output": {
            "path": display_path(output_path),
            "sha256": output_hash,
            "bytes": output_path.stat().st_size,
            "dtype": "float32",
            "bands": 1,
            "positive_cells": int(candidate.sum()),
            "nan_outside": True,
        },
        "inputs": {
            "scarp_product": {"path": display_path(args.product), "sha256": product_hash},
            "dotted_parent_C": {"path": display_path(args.base), "sha256": base_hash},
            "catalogue_exclusion_mirror": {"path": display_path(args.labels), "sha256": labels_hash},
            "footprint": {"path": display_path(args.footprint), "sha256": footprint_hash},
        },
        "construction": {
            "height_band": "h_gate12",
            "strike_band": "strike_at",
            "cover_band": "cover",
            "minimum_effective_height_m": 0.30,
            "minimum_cover_fraction": 0.90,
            "strike_tolerance_degrees_mod_180": 15.0,
            "window_points_including_center": 5,
            "minimum_support_points": 4,
            "selected_support_count_min": int(selected_support.min()),
            "selected_support_count_max": int(selected_support.max()),
            "selected_height_min_m": float(selected_heights.min()),
            "selected_height_median_m": float(np.median(selected_heights)),
            "selected_height_max_m": float(selected_heights.max()),
            "eligible_coherent_cells_before_distance_masks": int(coherent.sum()),
            "eligible_after_catalogue_and_parent_exclusion": int(eligible.sum()),
            "catalogue_exclusion_distance_m": 200.0,
            "parent_exclusion_distance_m": 200.0,
            "poisson_min_spacing_px": MIN_DIST_PX,
            "addition_count": int(accepted_rows.size),
            "base_C_count": int(base.sum()),
            "candidate_count": int(candidate.sum()),
            "emission": "binary 0/1 inside footprint; NaN outside",
        },
        "provenance_limits": [
            "This is a derived product from an owner group's regional mosaic of USGS 3DEP staged tiles; this checkout re-verifies local hashes but did not directly re-fetch USGS payloads.",
            "The source product stores a single best strike per 100 m cell; the continuity test is quantized and is not a native-resolution 500 m line trace.",
            "The full-area public catalogue is used as a distance exclusion mask; source C is frozen and was also built using catalogue geometry, so blocked results remain conditional and potentially leaky.",
            "The TIFF is a unique local research candidate; it is not an organizer-submitted file, score, or acceptance test.",
        ],
    }
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
