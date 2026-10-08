#!/usr/bin/env python3
"""Support-level prior-art audit for the H58-A artifact: top-5 positive-cell Jaccard overlaps.

Searches the same directories as scripts/check_candidate_uniqueness.py (docs/downloads, diagnostics,
data/families, data/raw/scored). Excludes the artifact's own companions (twin and diagnostics).
Writes evidence/h58_prior_art_jaccard_20261008.json. Support-level only; not organizer-side evidence.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / "docs/downloads/GEMSDOE48-H58-ds-belief-dotted-x-tipeuler-20261008-b92ba079-zeros-outside.tif"
TOKEN = "b92ba079"
SEARCH = ("docs/downloads", "docs/downloads/diagnostics", "data/families", "data/raw/scored")


def support(path: Path) -> np.ndarray | None:
    try:
        with rasterio.open(path) as ds:
            arr = ds.read(1).astype(np.float64)
    except Exception:
        return None
    arr = np.where(np.isfinite(arr), arr, 0.0)
    return arr > 0


def main() -> int:
    cand = support(CANDIDATE)
    rows = []
    for d in SEARCH:
        for p in sorted((ROOT / d).glob("*.tif")):
            if p.resolve() == CANDIDATE.resolve() or TOKEN in p.name:
                continue
            s = support(p)
            if s is None or s.shape != cand.shape:
                continue
            inter = int((cand & s).sum())
            union = int((cand | s).sum())
            rows.append({
                "file": str(p.relative_to(ROOT)),
                "positive_cells": int(s.sum()),
                "overlap_cells": inter,
                "jaccard": inter / union if union else 0.0,
                "identical_support": bool(np.array_equal(cand, s)),
            })
    rows.sort(key=lambda r: -r["jaccard"])
    payload = {
        "schema": "GEMSDOE48-H58-prior-art-jaccard-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "candidate": str(CANDIDATE.relative_to(ROOT)),
        "candidate_positive_cells": int(cand.sum()),
        "files_compared": len(rows),
        "scope": "local positive-cell support only; not organizer-side or global uniqueness",
        "top5": rows[:5],
        "any_identical_support": any(r["identical_support"] for r in rows),
    }
    out = ROOT / "evidence/h58_prior_art_jaccard_20261008.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    for r in rows[:5]:
        print(f"{r['jaccard']:.4f}  {r['overlap_cells']:6d}/{r['positive_cells']:6d}  {r['file']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
