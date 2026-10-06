#!/usr/bin/env python3
"""Derive a standalone valid-footprint mask from the sample GeoTIFF's finite mask.

The sample raster values are never read as labels; only its finite-data mask is used.
When the pinned owner-mirror labels are present, their nodata mask is compared cell by
cell to the sample mask. Both sources are still owner mirrors, not organizer-authenticated.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

from gemsdoe48.geotiff import assert_competition_grid, assert_same_grid, display_path, write_mask

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_SAMPLE_SHA256 = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
EXPECTED_LABEL_SHA256 = "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093"
EXPECTED_FOOTPRINT_CELLS = 5_167_373
EXPECTED_LABEL_POSITIVES = 60_988


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sample", type=Path, default=ROOT / "data/raw/sample_submission_template.tif")
    parser.add_argument("--labels", type=Path, default=ROOT / "data/raw/labels_catalogue.tif")
    parser.add_argument("--output", type=Path, default=ROOT / "data/source_mirrors/footprint-mask.tif")
    parser.add_argument("--allow-unpinned-sample", action="store_true")
    parser.add_argument("--allow-unpinned-labels", action="store_true")
    parser.add_argument("--skip-label-mask-check", action="store_true")
    args = parser.parse_args()
    actual_hash = sha256_file(args.sample)
    if actual_hash != EXPECTED_SAMPLE_SHA256 and not args.allow_unpinned_sample:
        raise SystemExit(
            f"Sample hash {actual_hash} is not the registered public mirror. "
            "Use --allow-unpinned-sample only after checking provenance."
        )
    with rasterio.open(args.sample) as src:
        assert_competition_grid(src.profile, path=args.sample)
        sample_values = src.read(1)
        footprint = np.isfinite(sample_values)
        profile = src.profile.copy()
    cells = int(footprint.sum())
    if actual_hash == EXPECTED_SAMPLE_SHA256 and cells != EXPECTED_FOOTPRINT_CELLS:
        raise SystemExit(f"Registered sample mask has {cells} cells; expected {EXPECTED_FOOTPRINT_CELLS}")

    label_audit = {"checked": False, "equal_cell_count": None, "difference_cells": None}
    if not args.skip_label_mask_check:
        if not args.labels.is_file():
            raise SystemExit("Pinned labels are needed for the mask comparison; restore them or pass --skip-label-mask-check")
        label_hash = sha256_file(args.labels)
        if label_hash != EXPECTED_LABEL_SHA256 and not args.allow_unpinned_labels:
            raise SystemExit(
                f"Label hash {label_hash} is not the registered public mirror. "
                "Use --allow-unpinned-labels only after checking provenance."
            )
        with rasterio.open(args.labels) as labels_ds:
            assert_competition_grid(labels_ds.profile, path=args.labels)
            assert_same_grid(profile, labels_ds.profile, name_a=str(args.sample), name_b=str(args.labels))
            labels = labels_ds.read(1)
            label_mask = labels_ds.dataset_mask() != 0
            label_nodata = labels_ds.nodata
        label_domain = labels != label_nodata
        differences = int(np.count_nonzero(footprint ^ label_mask))
        value_mask_differences = int(np.count_nonzero(footprint ^ label_domain))
        if differences or value_mask_differences:
            raise SystemExit(
                f"Sample/label footprint mismatch: GDAL mask differs at {differences} cells; "
                f"label-nodata comparison differs at {value_mask_differences} cells"
            )
        positive_labels = int(np.count_nonzero((labels == 1) & footprint))
        if label_hash == EXPECTED_LABEL_SHA256 and positive_labels != EXPECTED_LABEL_POSITIVES:
            raise SystemExit(
                f"Registered labels have {positive_labels} positive cells; "
                f"expected {EXPECTED_LABEL_POSITIVES}"
            )
        label_audit = {
            "checked": True,
            "label_sha256": label_hash,
            "label_provenance": "public owner-mirror; not organizer-authenticated",
            "equal_cell_count": cells,
            "difference_cells": differences,
            "label_value_nodata_difference_cells": value_mask_differences,
            "positive_labels_inside_footprint": positive_labels,
        }

    write_mask(args.output, footprint.astype(np.uint8), profile)
    audit = {
        "source": display_path(args.sample),
        "source_sha256": actual_hash,
        "source_provenance": "Public owner-mirror of the sample template; not organizer-authenticated.",
        "usage": "Only finite mask used; sample pixel values are not used as labels.",
        "footprint_cells": cells,
        "outside_cells": int(footprint.size - cells),
        "sample_label_mask_comparison": label_audit,
        "output": display_path(args.output),
        "output_sha256": sha256_file(args.output),
        "mask_is_binary": True,
    }
    receipt = ROOT / "evidence" / "footprint_mask_receipt.json"
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
