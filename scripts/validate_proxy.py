#!/usr/bin/env python3
"""Audit fixed predictions on a spatially partitioned SGMC off-catalogue proxy.

This is not the private organizer truth and is not model-training cross-validation.
The metric implementation follows the organizer's published DTI equations.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.validation import score_dti_regions

RADIUS_M = 300.0
ALPHA = 0.2
BETA = 0.8
INPUTS = {
    "dotted": (ROOT / "data/raw/dotted_h33_2_b2_zeros.tif", "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "tip": (ROOT / "data/raw/tip_h33d_stepover.tif", "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"),
    "template": (ROOT / "data/raw/sample_submission_template.tif", "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
    "labels": (ROOT / "data/raw/labels_catalogue.tif", "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    "sgmc_proxy": (ROOT / "data/raw/external/derived_sgmc_faults_100m_u8.tif", "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"),
}
FUSION_PATH = ROOT / "docs/downloads/gemsdoe48-h48-ds-yager-conflict-20261006.tif"
REPORT_PATH = ROOT / "docs/data/proxy-validation.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_checked(name: str) -> tuple[np.ndarray, dict, tuple[float, float]]:
    path, expected = INPUTS[name]
    if not path.exists():
        raise SystemExit(f"missing {path}; run bash scripts/fetch_inputs.sh")
    actual = sha256(path)
    if actual != expected:
        raise SystemExit(f"SHA-256 mismatch for {path}: {actual} != {expected}")
    with rasterio.open(path) as source:
        if source.count != 1:
            raise SystemExit(f"{path} has {source.count} bands; expected one")
        arr = source.read(1)
        profile = source.profile.copy()
        transform = source.transform
        crs = source.crs
    return arr, {"profile": profile, "transform": transform, "crs": crs}, (abs(transform.e), abs(transform.a))


def same_grid(ref: dict, other: dict) -> bool:
    return (
        ref["transform"] == other["transform"]
        and ref["crs"] == other["crs"]
        and ref["profile"]["width"] == other["profile"]["width"]
        and ref["profile"]["height"] == other["profile"]["height"]
    )


def read_prediction(path: Path, ref: dict) -> np.ndarray:
    with rasterio.open(path) as source:
        if source.count != 1 or not same_grid(ref, {
            "profile": source.profile,
            "transform": source.transform,
            "crs": source.crs,
        }):
            raise SystemExit(f"prediction grid mismatch: {path}")
        arr = source.read(1)
    return arr.astype(np.float32, copy=False)


def quadrant_regions(shape: tuple[int, int], evaluation_mask: np.ndarray) -> dict[str, np.ndarray]:
    height, width = shape
    row_mid, col_mid = height // 2, width // 2
    bounds = {
        "northwest": (slice(0, row_mid), slice(0, col_mid)),
        "northeast": (slice(0, row_mid), slice(col_mid, width)),
        "southwest": (slice(row_mid, height), slice(0, col_mid)),
        "southeast": (slice(row_mid, height), slice(col_mid, width)),
    }
    regions: dict[str, np.ndarray] = {"overall": evaluation_mask.copy()}
    for name, (ys, xs) in bounds.items():
        region = np.zeros(shape, dtype=bool)
        region[ys, xs] = True
        regions[name] = region
    return regions


def main() -> None:
    dotted, ref, pixel_size = read_checked("dotted")
    tip, ref2, _ = read_checked("tip")
    template, ref_template, _ = read_checked("template")
    labels, ref_labels, _ = read_checked("labels")
    sgmc, ref_sgmc, _ = read_checked("sgmc_proxy")
    for name, grid in [("tip", ref2), ("template", ref_template), ("labels", ref_labels), ("sgmc_proxy", ref_sgmc)]:
        if not same_grid(ref, grid):
            raise SystemExit(f"{name} grid differs from the pinned dotted raster")

    footprint = np.isfinite(template)
    if not np.array_equal(labels != -1, footprint):
        raise SystemExit("labels valid-data mask differs from sample-submission footprint")
    if not np.isin(labels, (-1, 0, 1)).all():
        raise SystemExit("labels contain unexpected values; expected -1, 0, 1")
    if not np.isin(sgmc, (0, 1)).all():
        raise SystemExit("SGMC proxy raster is not binary")

    # Official staff clarification: exact pixels of known catalogue faults are
    # masked/excluded from evaluation. The additional 300 m buffer below is
    # only a conservative rule for defining this off-catalogue proxy target.
    known_faults = labels == 1
    evaluation_mask = footprint & ~known_faults
    dist_from_known_m = distance_transform_edt(~known_faults, sampling=pixel_size)
    truth = (sgmc > 0) & footprint & (dist_from_known_m >= RADIUS_M) & ~known_faults

    fusion = read_prediction(FUSION_PATH, ref)
    naive_mean = ((dotted.astype(np.float32) + tip.astype(np.float32)) * np.float32(0.5))
    predictions = {
        "dotted": dotted.astype(np.float32, copy=False),
        "tip": tip.astype(np.float32, copy=False),
        "fusion": fusion,
        "naive_mean": naive_mean,
    }
    regions = quadrant_regions(truth.shape, evaluation_mask)

    scores: dict[str, dict[str, dict[str, float | int]]] = {}
    for name, prediction in predictions.items():
        scores[name] = score_dti_regions(
            prediction,
            truth,
            evaluation_mask,
            regions,
            radius_m=RADIUS_M,
            pixel_size_yx_m=pixel_size,
            alpha=ALPHA,
            beta=BETA,
        )

    best_anchor = max(("dotted", "tip", "naive_mean"), key=lambda key: scores[key]["overall"]["dti"])
    fold_names = ("northwest", "northeast", "southwest", "southeast")
    fold_deltas = {
        fold: float(scores["fusion"][fold]["dti"] - scores[best_anchor][fold]["dti"])
        for fold in fold_names
    }
    pooled_deltas = {
        name: float(scores["fusion"]["overall"]["dti"] - scores[name]["overall"]["dti"])
        for name in ("dotted", "tip", "naive_mean")
    }
    wins = sum(delta > 0.0 for delta in fold_deltas.values())
    gate_pass = bool(
        scores["fusion"]["overall"]["dti"] > scores[best_anchor]["overall"]["dti"]
        and wins >= 3
    )

    report = {
        "schema": "GEMSDOE48-proxy-v2",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "validation_type": "fixed-prediction spatial proxy assessment; no fitting or threshold selection on proxy labels",
        "protocol": {
            "blocks": "four fixed full-scene quadrants; full-scene distance neighborhoods are used, then TP/FP/FN terms are accumulated by block",
            "truth": "owner-mirrored USGS State Geologic Map Compilation-derived binary raster; SGMC-positive pixels at least 300 m from known-catalogue positive pixels",
            "evaluation_mask": "finite sample-submission footprint excluding exact known-fault pixels (labels == 1), in accordance with the organizer staff clarification",
            "metric": "official distance-weighted Tversky index: TP=sum_g max_x[p(x)k(d)], FP=sum_x[p(x)(1-max_g k(d))], FN=sum_g[1-max_x(p(x)k(d))], alpha=0.2, beta=0.8, triangular radius=300 m",
            "kernel": "k(d)=max(1-d/300 m, 0); prediction confidence is included in the TP maximum",
        },
        "warning": "Proxy only, not private expert truth or an organizer score. SGMC compilation/source bias remains; no claim that this is a model-training holdout or a leaderboard forecast.",
        "inputs": {
            name: {"file": str(path.relative_to(ROOT)), "sha256": expected}
            for name, (path, expected) in INPUTS.items()
        },
        "counts": {
            "grid_pixels": int(footprint.size),
            "valid_footprint_pixels": int(footprint.sum()),
            "known_fault_pixels_excluded_exactly": int(known_faults.sum()),
            "raw_sgmc_proxy_pixels": int((sgmc > 0).sum()),
            "off_catalogue_proxy_truth_pixels": int(truth.sum()),
            "pixel_size_yx_m": list(pixel_size),
            "radius_m": RADIUS_M,
        },
        "scores": scores,
        "blocked_comparison": {
            "anchor_selected_by_overall_proxy_dti": best_anchor,
            "pooled_dti_deltas_fusion_minus_each_baseline": pooled_deltas,
            "fold_deltas_fusion_minus_selected_anchor": fold_deltas,
            "positive_folds_vs_selected_anchor": wins,
            "gate_rule": "fusion overall DTI must exceed the best of dotted, tip, and naive mean and beat that selected anchor in at least 3 of 4 quadrants",
            "gate_pass": gate_pass,
            "submission_slot_recommendation": "DO NOT SPEND: this public proxy cannot clear a private-label slot gate; no DrivenData submission was made",
        },
        "fusion_artifact": {
            "file": str(FUSION_PATH.relative_to(ROOT)),
            "sha256": sha256(FUSION_PATH),
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
