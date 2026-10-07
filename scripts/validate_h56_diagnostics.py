#!/usr/bin/env python3
"""Independently validate H56-DS diagnostic GeoTIFFs and their semantics."""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
from gemsdoe48.geotiff import display_path

BUILD = ROOT / "evidence/build_h56_receipt_20261007.json"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
OUT = ROOT / "evidence/h56_diagnostics_validation_20261007.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    build = json.loads(BUILD.read_text(encoding="utf-8"))
    with rasterio.open(FOOTPRINT) as ds:
        footprint = ds.read(1) == 1
        shape = (ds.height, ds.width)
        crs = ds.crs.to_string()
        transform = tuple(ds.transform)[:6]

    arrays = {}
    records = {}
    for key, record in build["layers"]["diagnostics"].items():
        path = ROOT / record["path"]
        if not path.exists():
            raise SystemExit(f"missing diagnostic {path}")
        actual_hash = sha256_file(path)
        if actual_hash != record["sha256"]:
            raise SystemExit(f"hash mismatch for {path}: {actual_hash} != {record['sha256']}")
        with rasterio.open(path) as ds:
            if (ds.count != 1 or ds.dtypes != ("float32",) or (ds.height, ds.width) != shape
                    or ds.crs is None or ds.crs.to_string() != crs
                    or tuple(ds.transform)[:6] != transform or ds.nodata is not None):
                raise SystemExit(f"grid/type/nodata mismatch for {path}")
            values = ds.read(1)
        if not np.isfinite(values).all() or np.any((values < 0.0) | (values > 1.0)):
            raise SystemExit(f"nonfinite or out-of-range diagnostic: {path}")
        if np.any(values[~footprint] != 0.0):
            raise SystemExit(f"diagnostic is not zero outside footprint: {path}")
        arrays[key] = values
        records[key] = {
            "path": display_path(path),
            "sha256": actual_hash,
            "bytes": path.stat().st_size,
            "one_band_float32": True,
            "grid_matches_competition": True,
            "all_cells_finite": True,
            "all_cells_in_0_1": True,
            "outside_footprint_all_zero": True,
            "min_inside_footprint": float(values[footprint].min()),
            "max_inside_footprint": float(values[footprint].max()),
            "zero_outside_cells": int(np.count_nonzero(values[~footprint] == 0.0)),
        }

    bel_raw = arrays["belief_raw"][footprint]
    theta = arrays["unassigned_mtheta"][footprint]
    conflict = arrays["conflict_k"][footprint]
    plausibility = arrays["plausibility"][footprint]
    primary_path = ROOT / build["candidate"]["primary"]["path"]
    with rasterio.open(primary_path) as ds:
        primary = ds.read(1)[footprint]
    max_raw_belief = float(bel_raw.max())
    semantic_checks = {
        "raw_bel_max": max_raw_belief,
        "primary_equals_raw_bel_divided_by_max_within_2e_7": bool(
            np.allclose(primary, bel_raw / max_raw_belief, rtol=0.0, atol=2e-7)
        ),
        "plausibility_equals_bel_plus_mtheta_within_2e_7": bool(
            np.allclose(plausibility, bel_raw + theta, rtol=0.0, atol=2e-7)
        ),
        "mtheta_is_separate_from_conflict": bool(not np.array_equal(theta, conflict)),
        "mean_mtheta_in_footprint": float(theta.mean()),
        "mean_raw_conflict_k_in_footprint": float(conflict.mean()),
        "p95_raw_conflict_k": float(np.percentile(conflict, 95)),
        "footprint_cells": int(footprint.sum()),
    }
    if not all(semantic_checks[key] for key in (
        "primary_equals_raw_bel_divided_by_max_within_2e_7",
        "plausibility_equals_bel_plus_mtheta_within_2e_7",
        "mtheta_is_separate_from_conflict",
    )):
        raise SystemExit("H56 diagnostic semantic relation failed")

    report = {
        "schema_version": 1,
        "validated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_LOCAL_DIAGNOSTIC_FORMAT_AND_SEMANTIC_AUDIT_NOT_ORGANIZER_ACCEPTANCE",
        "primary": {
            "path": build["candidate"]["primary"]["path"],
            "sha256": build["candidate"]["primary"]["sha256"],
            "source_receipt": "evidence/h56_submission_validation_20261007.json",
        },
        "diagnostics": records,
        "semantic_checks": semantic_checks,
        "definition_note": "m(Theta) is the canonical normalized Dempster residual and does not include raw conflict K; plausibility is Bel(F)+m(Theta).",
    }
    OUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": report["status"], "semantic_checks": semantic_checks,
                      "layers": list(records), "receipt": display_path(OUT)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
