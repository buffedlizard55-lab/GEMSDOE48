#!/usr/bin/env python3
"""Offline, blocked-proxy test of the preregistered H56-F D-S pruning ladder.

This is a no-slot diagnostic. It thresholds the frozen H56B normalized Bel(F)
values only at H33-2-B2 cells (never adds cells), evaluates fixed 2x2 spatial
folds with the shared official-metric implementation, and compares the rungs
against both parents and the current H49 proxy reference. Public-map truth and
frozen full-scene source surfaces make these results conditional and potentially
leaky; they are not private-label or organizer scores.
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
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))

from run_spatial_holdout import quadrants, score_fold  # noqa: E402
from gemsdoe48.h56f import prune_dotted  # noqa: E402

PINNED = {
    "dotted": ("data/families/dotted_b2_prune_02778.tif", "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "tip_stepover": ("data/families/tip_stepover_r30_02632.tif", "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"),
    "belief": ("docs/downloads/GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif", "4d6548d4ec07a47a25b83d28ebc05d58b57448c1507b460aed52cec395bdb6b5"),
    "h49_reference": ("docs/downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif", "9f028289c364c071065245799d7ed131600e80e9f0d10602806b12ce34d7cae8"),
    "labels": ("data/raw/labels_catalogue.tif", "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"),
    "sgmc": ("data/official/derived_sgmc_faults_100m.tif", "643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0"),
    "footprint": ("data/source_mirrors/footprint-mask.tif", ""),
}
THRESHOLDS = (0.90, 0.95, 0.99)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load(name: str) -> tuple[np.ndarray, dict]:
    relative, expected = PINNED[name]
    path = ROOT / relative
    if not path.is_file():
        raise FileNotFoundError(path)
    got = sha256(path)
    if expected and got != expected:
        raise ValueError(f"SHA-256 mismatch for {name}: {got} != {expected}")
    with rasterio.open(path) as dataset:
        array = dataset.read(1)
        profile = dataset.profile.copy()
    return array, profile


def main() -> int:
    dotted_raw, profile = load("dotted")
    tip_raw, tip_profile = load("tip_stepover")
    belief_raw, belief_profile = load("belief")
    h49_raw, h49_profile = load("h49_reference")
    labels, labels_profile = load("labels")
    sgmc, sgmc_profile = load("sgmc")
    footprint_raw, footprint_profile = load("footprint")
    for name, other in (("tip", tip_profile), ("belief", belief_profile), ("H49", h49_profile),
                        ("labels", labels_profile), ("SGMC", sgmc_profile),
                        ("footprint", footprint_profile)):
        if other["crs"] != profile["crs"] or other["transform"] != profile["transform"] \
                or other["height"] != profile["height"] or other["width"] != profile["width"]:
            raise ValueError(f"Grid mismatch: dotted versus {name}")

    footprint = footprint_raw == 1
    dotted = (dotted_raw > 0) & footprint
    tip = (tip_raw > 0) & footprint
    if np.any(~np.isfinite(belief_raw[footprint])) or np.any((belief_raw[footprint] < 0) | (belief_raw[footprint] > 1)):
        raise ValueError("H56B belief is not finite and bounded on the footprint")
    belief = np.nan_to_num(belief_raw, nan=0.0, posinf=0.0, neginf=0.0)
    h49 = np.nan_to_num(h49_raw, nan=0.0, posinf=0.0, neginf=0.0)
    blocks = quadrants(*dotted.shape)
    catalogue_truth = (labels > 0) & footprint
    distance_to_catalogue = __import__("scipy").ndimage.distance_transform_edt(
        ~catalogue_truth, sampling=(100.0, 100.0)
    )
    sgmc_offcat_truth = (sgmc > 0) & footprint & (distance_to_catalogue > 300.0)
    truths = {"catalogue_public_proxy": catalogue_truth,
              "SGMC_off_catalogue_gt300m_public_proxy": sgmc_offcat_truth}

    surfaces: dict[str, np.ndarray] = {
        "dotted_parent": dotted.astype(np.float32),
        "tip_stepover_parent": tip.astype(np.float32),
        "parent_union": (dotted | tip).astype(np.float32),
        "naive_binary_mean": (0.5 * (dotted.astype(np.float32) + tip.astype(np.float32))),
        "H56B_graded_belief": belief.astype(np.float32),
        "H49_same_protocol_proxy_reference": h49.astype(np.float32),
    }
    rung_metadata = {}
    scratch = ROOT / "scratch/h56f-pruning"
    scratch.mkdir(parents=True, exist_ok=True)
    for threshold in THRESHOLDS:
        kept = prune_dotted(dotted, belief, threshold)
        name = f"H56F_Bel_ge_{threshold:.2f}"
        surface = kept.astype(np.float32)
        surfaces[name] = surface
        rung_metadata[name] = {
            "threshold_on": "frozen H56B normalized Bel(F), sampled only at dotted-parent positive cells",
            "threshold": threshold,
            "input_dotted_cells": int(dotted.sum()),
            "kept_cells": int(kept.sum()),
            "removed_cells": int((dotted & ~kept).sum()),
            "tip_parent_intersection_cells": int((dotted & tip).sum()),
            "subset_of_dotted_parent": bool(np.all(~kept | dotted)),
        }
        output = scratch / f"{name}.tif"
        out_profile = dict(profile)
        out_profile.update(driver="GTiff", count=1, dtype="float32", nodata=None, compress="deflate")
        with rasterio.open(output, "w", **out_profile) as dataset:
            dataset.write(surface, 1)
        rung_metadata[name]["scratch_raster"] = str(output.relative_to(ROOT))
        rung_metadata[name]["scratch_sha256"] = sha256(output)

    results: dict[str, dict] = {}
    for truth_name, truth in truths.items():
        fold_result = {}
        for name, prediction in surfaces.items():
            scores = {fold_name: score_fold(prediction, truth, footprint, core)
                      for fold_name, core in blocks.items()}
            scores["mean_dti"] = float(np.mean([scores[fold]["dti"] for fold in blocks]))
            fold_result[name] = scores
        comparisons = {}
        for name in rung_metadata:
            comparisons[name] = {}
            for comparator in ("dotted_parent", "tip_stepover_parent", "parent_union",
                              "naive_binary_mean", "H56B_graded_belief",
                              "H49_same_protocol_proxy_reference"):
                delta = {fold: float(fold_result[name][fold]["dti"] - fold_result[comparator][fold]["dti"])
                         for fold in blocks}
                comparisons[name][comparator] = {
                    "fold_delta_dti": delta,
                    "mean_delta_dti": float(np.mean(list(delta.values()))),
                    "positive_folds": int(sum(value > 0 for value in delta.values())),
                }
        results[truth_name] = {"scores": fold_result, "paired_deltas": comparisons}

    receipt = {
        "schema_version": 1,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "status": "OFFLINE_SPATIAL_PROXY_TEST_ONLY_NOT_SLOT_CLEARED",
        "candidate": "H56-F absence-driven D-S pruning ladder; no new cells are added",
        "sources": {name: {"path": path, "sha256": sha256(ROOT / path)}
                    for name, (path, _) in PINNED.items()},
        "protocol": {
            "folds": "Four fixed 2x2 full-grid quadrants; held-out core plus 300 m Euclidean halo clipped to footprint; truth scored in core only.",
            "metric": "official distance-weighted Tversky implementation, alpha=0.2, beta=0.8, triangular R=300 m",
            "SGMC_truth": "on-grid public USGS SGMC mirror cells more than 300 m from public catalogue-label cells",
            "candidate_surface": "binary subset of dotted C; only H56B normalized Bel(F) thresholds are varied; no threshold tuning after this frozen 0.90/0.95/0.99 ladder",
            "limitations": [
                "Both truth sources are public-map proxies, not private expert labels or organizer scores.",
                "The source surfaces are frozen upstream full-scene rasters and were not independently reconstructed in each fold.",
                "The parent dotted surface's construction uses catalogue-distance pruning; this creates potential spatial information leakage.",
                "This is an offline screen only; no competition slot was used or is recommended by this result.",
            ],
        },
        "rungs": rung_metadata,
        "results": results,
        "slot_decision": {
            "cleared": False,
            "reason": "A candidate must beat the current same-protocol blocked proxy best before any weekly slot. This screen is diagnostic, and proxy performance cannot establish private-label improvement.",
        },
    }
    target = ROOT / "evidence/h56f_pruning_holdout_20261007.json"
    target.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({
        "status": receipt["status"],
        "rungs": {name: {"kept": item["kept_cells"], "removed": item["removed_cells"]}
                  for name, item in rung_metadata.items()},
        "means": {truth: {name: scores["mean_dti"] for name, scores in entry["scores"].items()
                           if name.startswith("H56F") or name == "H49_same_protocol_proxy_reference"}
                  for truth, entry in results.items()},
        "receipt": str(target.relative_to(ROOT)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
