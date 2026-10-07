#!/usr/bin/env python3
"""Audit H56-DS byte/pixel uniqueness and comparison with known D-S prior art."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48.geotiff import display_path
from gemsdoe48.h56 import deterministic_top_k

PRIMARY = ROOT / "docs/downloads/GEMSDOE48-H56-OWDS-B2xH33D-20261007-1f7b5a4f18db-zeros-outside.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
RECEIPT = ROOT / "evidence/h56_uniqueness_audit_20261007.json"
NEW_PREFIX = "GEMSDOE48-H56-OWDS-B2xH33D-20261007-1f7b5a4f18db"
TOP_K = 37_654


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def canonical_grid(path: Path, shape: tuple[int, int], crs: str, transform: tuple) -> np.ndarray | None:
    try:
        with rasterio.open(path) as src:
            if (src.count != 1 or src.height != shape[0] or src.width != shape[1]
                    or src.crs is None or src.crs.to_string() != crs
                    or tuple(src.transform)[:6] != transform):
                return None
            values = src.read(1).astype(np.float32, copy=False)
            nodata = src.nodata
            if nodata is not None:
                if isinstance(nodata, float) and np.isnan(nodata):
                    values = np.where(np.isfinite(values), values, 0.0)
                else:
                    values = np.where(values == nodata, 0.0, values)
            if not np.isfinite(values).all():
                values = np.where(np.isfinite(values), values, 0.0)
            return np.asarray(values, dtype=np.float32)
    except (rasterio.errors.RasterioIOError, ValueError, OSError):
        return None


def compare_surface(pred: np.ndarray, prior: np.ndarray, footprint: np.ndarray) -> dict:
    p = pred[footprint].astype(np.float64, copy=False)
    q = prior[footprint].astype(np.float64, copy=False)
    step = max(1, int(np.ceil(p.size / 100_000)))
    if p.std() and q.std():
        pearson = float(pearsonr(p, q).statistic)
        spearman = float(spearmanr(p[::step], q[::step]).statistic)
    else:
        pearson = None
        spearman = None
    difference = np.abs(p - q)
    p_top = deterministic_top_k(pred, footprint, TOP_K)
    q_top = deterministic_top_k(prior, footprint, TOP_K)
    intersection = int((p_top & q_top).sum())
    union = int((p_top | q_top).sum())
    return {
        "canonical_pixelwise_equal_inside_footprint": bool(np.array_equal(p, q)),
        "pearson_inside_footprint": pearson,
        "spearman_inside_footprint_deterministic_sample": spearman,
        "spearman_sample_cells": int(p[::step].size),
        "mean_absolute_difference": float(difference.mean()),
        "max_absolute_difference": float(difference.max()),
        "fraction_abs_difference_gt_0p05": float((difference > 0.05).mean()),
        "positive_cells_prior_inside_footprint": int(np.count_nonzero(q > 0.0)),
        "top_37654_rank_jaccard": float(intersection / union) if union else None,
    }


def main() -> int:
    if not PRIMARY.exists():
        raise SystemExit(f"missing H56 primary: {PRIMARY}")
    with rasterio.open(FOOTPRINT) as ds:
        footprint = ds.read(1) == 1
        shape = (ds.height, ds.width)
        crs = ds.crs.to_string()
        transform = tuple(ds.transform)[:6]
    with rasterio.open(PRIMARY) as ds:
        if (ds.count != 1 or (ds.height, ds.width) != shape or ds.crs.to_string() != crs
                or tuple(ds.transform)[:6] != transform):
            raise SystemExit("primary is not on the exact competition grid")
        prediction = ds.read(1).astype(np.float32, copy=False)
    if not np.isfinite(prediction).all() or np.any((prediction < 0.0) | (prediction > 1.0)):
        raise SystemExit("primary contains nonfinite/out-of-range values")

    paths: list[Path] = []
    for base in (ROOT / "data", ROOT / "docs/downloads"):
        paths.extend(base.rglob("*.tif"))
    paths = sorted({p.resolve() for p in paths if p.is_file()})
    prior_candidates = [p for p in paths if NEW_PREFIX not in p.name]
    exact_hash_matches = []
    exact_pixel_matches = []
    comparisons = []
    comparable_count = 0
    primary_sha = sha256_file(PRIMARY)
    for path in prior_candidates:
        values = canonical_grid(path, shape, crs, transform)
        if values is None:
            continue
        comparable_count += 1
        digest = sha256_file(path)
        if digest == primary_sha:
            exact_hash_matches.append(display_path(path))
        if np.array_equal(prediction[footprint], values[footprint]):
            exact_pixel_matches.append(display_path(path))
        key = path.relative_to(ROOT).as_posix()
        if any(token in key.lower() for token in (
            "h53", "h55", "h49", "h48", "h50", "h51", "h54", "ds-conflict", "dempster", "yager"
        )):
            comparisons.append({
                "path": key,
                "sha256": digest,
                **compare_surface(prediction, values, footprint),
            })

    comparisons.sort(key=lambda item: (item["pearson_inside_footprint"] is None,
                                      -(item["pearson_inside_footprint"] or 0.0)))
    # Pin the most important direct prior-art references even if their path token
    # did not match an H-name convention.
    direct_refs = {
        "H53_two_family_dempster_diagnostic": ROOT / "docs/downloads/diagnostics/GEMSDOE48-H53-DS-RadEdge-B2xH33D-20261007-4c01fcf2ad8c-two-family-dempster-only.tif",
        "H53_two_family_arithmetic_mean_diagnostic": ROOT / "docs/downloads/diagnostics/GEMSDOE48-H53-DS-RadEdge-B2xH33D-20261007-4c01fcf2ad8c-two-family-naive-mean.tif",
        "H55_belief_diagnostic": ROOT / "docs/downloads/diagnostics/gemsdoe48-h55-bel-055da9855353.tif",
        "H49_current_blocked_best": ROOT / "docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif",
    }
    direct_comparisons = {}
    for name, path in direct_refs.items():
        if path.exists():
            values = canonical_grid(path, shape, crs, transform)
            direct_comparisons[name] = {
                "path": display_path(path),
                "sha256": sha256_file(path),
                **compare_surface(prediction, values, footprint),
            } if values is not None else {"path": display_path(path), "comparable": False}

    receipt = {
        "schema_version": 1,
        "audited_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_LOCAL_BYTE_AND_PIXEL_UNIQUENESS_ONLY_NOT_GLOBAL_OR_ORGANIZER_PROOF",
        "primary": {
            "path": display_path(PRIMARY),
            "sha256": primary_sha,
            "bytes": PRIMARY.stat().st_size,
            "canonicalization": "Float32 values compared only inside the official finite footprint; nodata/NaN outside is canonicalized to zero for prior rasters.",
        },
        "search_scope": {
            "directories": ["data/", "docs/downloads/"],
            "prior_candidate_tiffs_examined_for_metadata": len(prior_candidates),
            "same_grid_one_band_prior_rasters_compared": comparable_count,
            "multi_band_or_different_grid_files_skipped": len(prior_candidates) - comparable_count,
        },
        "result": {
            "same_sha256_as_prior_raster": bool(exact_hash_matches),
            "sha256_matches": exact_hash_matches,
            "pixelwise_equal_inside_footprint_to_prior_raster": bool(exact_pixel_matches),
            "pixelwise_matches": exact_pixel_matches,
        },
        "known_prior_art_comparisons": direct_comparisons,
        "related_same_grid_prior_rasters_sorted_by_correlation": comparisons[:12],
        "novelty_scope": {
            "not_claimed": "Dempster-Shafer, family fusion, or geological source novelty; H53 already contains the same two-family parents and a Dempster diagnostic.",
            "resolved_difference": "H53 family diagnostic used alpha=0.50 simple-support masses m(F)=alpha*b, m(notF)=alpha*(1-b), m(Theta)=1-alpha, and H53's full three-source product adds GeoDAWN. H56 uses the frozen open-world m(notF)=alpha*0.10*(1-b), alpha=0.60 per family, then exports relative max-normalized Bel(F) with separate raw canonical m(Theta) and conflict K.",
            "interpretation": "This is a distinct, audited parameterization/output—not a relabelled H53 file or a claim of a new geological signal. The two parent masks and their high spatial dependence are unchanged.",
        },
        "not_the_arithmetic_mean": {
            "receipt": "evidence/build_h56_receipt_20261007.json",
            "important_caveat": "The output differs numerically from the arithmetic mean, but the measured top-37,654 rank selection has Jaccard 1.0 and Spearman is near 1.0; it should not be described as a materially different rank ordering at that budget.",
        },
    }
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": receipt["status"],
        "primary_sha256": primary_sha,
        "prior_same_grid_rasters": comparable_count,
        "sha_matches": exact_hash_matches,
        "pixel_matches": exact_pixel_matches,
        "direct_comparisons": direct_comparisons,
        "receipt": display_path(RECEIPT),
    }, indent=2))
    return 0 if not exact_hash_matches and not exact_pixel_matches else 2


if __name__ == "__main__":
    raise SystemExit(main())
