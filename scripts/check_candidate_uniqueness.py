#!/usr/bin/env python3
"""Compare a candidate with GeoTIFFs in a bounded set of local artifact directories.

The competition brief requires a *unique* submission: prior submissions may be used
only for learning. This script compares local in-footprint support (positive cells),
byte hashes, Jaccard overlap and symmetric difference for files under ``SEARCH_DIRS``.
A no-duplicate result is scoped to those scanned local files only; it is not a proof of
global uniqueness, organizer-side uniqueness, prior submission status, or score linkage.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import time

import numpy as np
import rasterio

ROOT = pathlib.Path(__file__).resolve().parents[1]
SEARCH_DIRS = ("docs/downloads", "docs/downloads/diagnostics", "data/families", "data/raw/scored")


def sha256_file(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def support_of(path: pathlib.Path) -> np.ndarray | None:
    try:
        with rasterio.open(path) as src:
            values = src.read(1).astype(np.float64)
            nodata = src.nodata
    except Exception:
        return None
    values = np.where(np.isfinite(values), values, 0.0)
    if nodata is not None and np.isfinite(nodata):
        values = np.where(values == nodata, 0.0, values)
    return values > 0.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("candidate", type=pathlib.Path)
    parser.add_argument("--receipt", type=pathlib.Path, required=True)
    parser.add_argument(
        "--companion-token", action="append", default=[],
        help="file names containing this token belong to the same build (twins, diagnostics); "
             "they are excluded from the duplicate verdict but still reported",
    )
    args = parser.parse_args()
    t0 = time.time()

    candidate = args.candidate.resolve()
    candidate_sha = sha256_file(candidate)
    support = support_of(candidate)
    assert support is not None, f"cannot read {candidate}"
    n_candidate = int(support.sum())

    comparisons, worst = [], {"overlap_cells": -1}
    for directory in SEARCH_DIRS:
        for path in sorted((ROOT / directory).glob("*.tif")):
            if path.resolve() == candidate:
                continue
            other = support_of(path)
            if other is None or other.shape != support.shape:
                continue
            overlap = int((support & other).sum())
            union = int((support | other).sum())
            companion = path.name.startswith(candidate.stem) or any(
                tok and tok in path.name for tok in args.companion_token)  # same build: twin / diagnostics
            row = {
                "file": str(path.relative_to(ROOT)),
                "companion_of_same_artifact": bool(companion),
                "sha256": sha256_file(path),
                "byte_identical": sha256_file(path) == candidate_sha,
                "cells": int(other.sum()),
                "overlap_cells": overlap,
                "jaccard": overlap / union if union else 0.0,
                "symmetric_difference_cells": union - overlap,
                "identical_support": bool(np.array_equal(support, other)),
            }
            comparisons.append(row)
            if overlap > worst["overlap_cells"]:
                worst = row

    duplicate_flags = [row["file"] for row in comparisons
                       if not row["companion_of_same_artifact"]
                       and (row["byte_identical"] or row["identical_support"])]
    companions = [row["file"] for row in comparisons if row["companion_of_same_artifact"]]
    receipt = {
        "schema": "GEMSDOE48-candidate-uniqueness-v1",
        "generated_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "candidate": {"file": str(candidate.relative_to(ROOT)), "sha256": candidate_sha,
                      "bytes": candidate.stat().st_size, "positive_cells": n_candidate},
        "compared_files": len(comparisons),
        "uniqueness_scope": "bounded comparison of local TIFFs in SEARCH_DIRS only; not organizer-side or global",
        "organizer_uniqueness_tested": False,
        "global_uniqueness_established": False,
        "max_overlap_excluding_companions": max(
            (row for row in comparisons if not row["companion_of_same_artifact"]),
            key=lambda row: row["overlap_cells"], default=None),
        "companion_tokens": list(args.companion_token),
        "companions_of_same_artifact": companions,
        "max_jaccard_excluding_companions": max(
            (row for row in comparisons if not row["companion_of_same_artifact"]),
            key=lambda row: row["jaccard"], default=None),
        "duplicates_byte_or_support_identical": duplicate_flags,
        "verdict": "UNIQUE" if not duplicate_flags else "DUPLICATE_OF_PRIOR_ART",
        "note": "Support-level comparison (positive cells). A candidate that shares a support "
                "with an earlier artifact is not a new submission even if the bytes differ.",
    }
    args.receipt.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("candidate", "compared_files", "max_overlap_excluding_companions", "verdict")}, indent=2))
    print(f"({time.time() - t0:.0f}s) receipt -> {args.receipt}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
