#!/usr/bin/env python3
"""Inventory competition-style training files and end-to-end ML scripts in this checkout.

This does not download data or infer its provenance. It records exact local presence,
size and SHA-256 for the paths named in the README and detects the optional third-party
feature-stack restore recipe. Run from any directory with the project's Python env:

    ./.venv/bin/python scripts/audit_training_inventory.py
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA_PATHS = (
    "data/raw/training_features.tif",
    "data/raw/labels.tif",
    "data/raw/sample_submission.tif",
    "data/raw/sample_submission_template.tif",
    "data/raw/1m_DEM_links.csv",
    "data/official/training_features.tif",
    "data/official/labels.tif",
    "data/official/existing_faults.tif",
    "data/official/1m_DEM_links.csv",
    "data/raw/labels_catalogue.tif",
)
PIPELINE_PATHS = (
    "scripts/download_competition_data.sh",
    "scripts/prepare_data.py",
    "scripts/train.py",
    "scripts/infer.py",
    "scripts/inference.py",
    "scripts/run_spatial_holdout.py",
    "scripts/restore_h55_inputs.py",
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def describe(relative: str) -> dict:
    path = ROOT / relative
    if not path.is_file():
        return {"path": relative, "present": False}
    return {
        "path": relative,
        "present": True,
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
        "git_ignored": path.relative_to(ROOT).as_posix().startswith("data/raw/"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/training_inventory_20261007.json")
    args = parser.parse_args()
    data = [describe(path) for path in DATA_PATHS]
    scripts = [describe(path) for path in PIPELINE_PATHS]
    training_features = next(row for row in data if row["path"] == "data/raw/training_features.tif")
    restore_script = ROOT / "scripts/restore_h55_inputs.py"
    restore_recipe = {
        "script_present": restore_script.is_file(),
        "command": "python scripts/restore_h55_inputs.py --with-official-features",
        "expected_path": "data/raw/training_features.tif",
        "expected_bytes": 418_912_844,
        "expected_sha256": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
        "source_class": "third-party owner GitHub mirror; hash pin proves mirrored-byte identity, not organizer authentication or data-use clearance",
    }
    inventory = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "data_paths": data,
        "pipeline_paths": scripts,
        "optional_feature_stack_restore": restore_recipe,
        "assessment": {
            "training_feature_stack_present_now": bool(training_features["present"]),
            "competition_labels_authenticated_here": False,
            "official_sample_submission_tif_present_under_named_paths": False,
            "1m_dem_links_csv_present": False,
            "download_competition_data_script_present": (ROOT / "scripts/download_competition_data.sh").is_file(),
            "prepare_data_script_present": (ROOT / "scripts/prepare_data.py").is_file(),
            "supervised_train_and_inference_pipeline_present": False,
            "available_capability": "local raster analysis, deterministic candidate-building, exact metric, format validation, and public-proxy holdouts; these do not constitute a full supervised training pipeline",
            "limitation": "README statements that a single data-placement step unlocks a ready full train→inference→validate pipeline are not supported by the files/scripts present in this checkout.",
        },
    }
    output = args.output if args.output.is_absolute() else ROOT / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(inventory["assessment"], indent=2))
    print(f"wrote {output.relative_to(ROOT) if output.is_relative_to(ROOT) else output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
