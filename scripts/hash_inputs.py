#!/usr/bin/env python3
"""Hash every input raster so that any result in this repository can be re-derived
byte-for-byte, and so that the provenance of each family artifact is auditable.

Writes ``registry/inputs.json``.  Safe to re-run; the output is deterministic apart
from the ``generated_utc`` stamp.

Every entry records:
  path        repository-relative path
  sha256      full hex digest of the file bytes
  bytes       file size
  role        official | family | truth-layer
  provenance  where the bytes came from (see docs/sources.html for the URLs)
  grid        width, height, crs, transform, dtype, nodata -- read with rasterio
  values      min, max, n_positive, n_nan, n_outside_footprint
"""
from __future__ import annotations

import datetime as _dt
import hashlib
import json
import pathlib
import sys

import numpy as np
import rasterio

REPO = pathlib.Path(__file__).resolve().parents[1]

# (path, role, provenance).  Provenance strings name the exact artifact they were
# extracted from in the sibling repositories; see registry/submission_build.json and
# docs/sources.html for the upstream URLs.
INPUTS = [
    ("data/official/labels.tif", "truth-layer",
     "Third-party public owner-mirror of the competition training labels (known public faults), "
     "pinned by SHA-256; not organizer-authenticated in this repository and not private expert "
     "test truth. Its relation to the score-time mask follows the official staff clarification."),
    ("data/official/existing_faults.tif", "truth-layer",
     "Third-party public owner-mirror of the public known-fault catalogue, pinned by SHA-256; "
     "not organizer-authenticated in this repository and not private expert test truth."),
    ("data/official/derived_sgmc_faults_100m.tif", "truth-layer",
     "USGS State Geologic Map Compilation (SGMC) faults rasterized to the competition-aligned "
     "100 m grid via a sibling-repository owner mirror. This repository did not independently "
     "rebuild the vector derivation. Public-map proxy only; not organizer-authenticated or "
     "private expert test truth."),
    ("data/families/dotted_d2_8_02600.tif", "family",
     "Spacing-tuned dotted family, owner-reported live 0.2600 (GEMSDOE25, artifact "
     "e56ea318af89). Upstream of the 0.2708 and 0.2778 rungs."),
    ("data/families/dotted_d2_8_02708.tif", "family",
     "Spacing-tuned dotted family, owner-reported live 0.2708 (GEMSDOE28, artifact "
     "8acb75e1f2cc, catalogue-flank buffer B = 1)."),
    ("data/families/dotted_b2_prune_02778.tif", "family",
     "LIVE-BEST artifact, owner-reported live 0.2778 (GEMSDOE32 H33-2-B2, artifact "
     "e5eb6e7e). 37,654 positive pixels. This is the mass target the submission reproduces."),
    ("data/families/tip_stepover_r30_02632.tif", "family",
     "Tip / step-over family, owner-reported live 0.2632 (GEMSDOE33, artifact "
     "cb490425926e). The second family combined by Dempster's rule."),
]

FOOTPRINT_CRS = "EPSG:32611"
EXPECTED_SHAPE = (3730, 3292)  # (height, width) of the official grid


def sha256_of(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe(path: pathlib.Path) -> dict:
    with rasterio.open(path) as src:
        a = src.read(1)
        grid = {
            "width": src.width,
            "height": src.height,
            "count": src.count,
            "dtype": src.dtypes[0],
            "crs": src.crs.to_string() if src.crs else None,
            "transform": [float(v) for v in src.transform[:6]],
            "nodata": None if src.nodata is None or np.isnan(src.nodata) else float(src.nodata),
            "res_m": abs(float(src.transform.a)),
        }
    finite = np.isfinite(a)
    if src.nodata is not None and not np.isnan(src.nodata):
        # Official truth layers carry -1 in the nodata/outside-footprint cells.
        # Range legality applies to real data cells only.
        finite = finite & (a != src.nodata)
    vals = {
        "min": float(a[finite].min()) if finite.any() else None,
        "max": float(a[finite].max()) if finite.any() else None,
        "n_positive": int((a[finite] > 0).sum()),
        "n_nan": int((~finite).sum()),
        "n_outside_0_1": int(((a[finite] < 0) | (a[finite] > 1)).sum()),
        "n_cells": int(a.size),
        "unique_values": int(np.unique(a[finite]).size),
    }
    return grid, vals


def main() -> int:
    out = {
        "generated_utc": _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generated_by": "scripts/hash_inputs.py",
        "hash_algorithm": "sha256",
        "expected_grid": {"shape_hw": list(EXPECTED_SHAPE), "crs": FOOTPRINT_CRS, "res_m": 100.0},
        "note": "Hashes are of the exact bytes in this repository. Any artifact built by "
                "scripts/build_submission.py must reproduce from these inputs alone.",
        "inputs": [],
    }
    problems: list[str] = []
    for rel, role, prov in INPUTS:
        p = REPO / rel
        if not p.exists():
            problems.append(f"MISSING {rel}")
            continue
        grid, vals = describe(p)
        rec = {
            "path": rel,
            "role": role,
            "sha256": sha256_of(p),
            "bytes": p.stat().st_size,
            "provenance": prov,
            "grid": grid,
            "values": vals,
        }
        out["inputs"].append(rec)
        flag = ""
        if (grid["height"], grid["width"]) != EXPECTED_SHAPE:
            problems.append(f"GRID MISMATCH {rel}: {(grid['height'], grid['width'])}")
            flag = "  <-- GRID MISMATCH"
        if grid["crs"] != FOOTPRINT_CRS:
            problems.append(f"CRS MISMATCH {rel}: {grid['crs']}")
            flag += "  <-- CRS MISMATCH"
        if vals["n_outside_0_1"]:
            problems.append(f"RANGE VIOLATION {rel}: {vals['n_outside_0_1']} cells")
            flag += "  <-- RANGE VIOLATION"
        print(f"{rec['sha256'][:12]}  {vals['n_positive']:>7,} pos  {rel}{flag}")

    out["grid_consistent"] = not problems
    out["problems"] = problems
    dest = REPO / "registry" / "inputs.json"
    dest.write_text(json.dumps(out, indent=2) + "\n")
    print(f"\nwrote registry/inputs.json  ({len(out['inputs'])} inputs, "
          f"{len(problems)} problem(s))")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
