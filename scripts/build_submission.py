#!/usr/bin/env python3
"""Build, independently re-read, and audit the GEMSDOE48 evidence-fusion GeoTIFF."""
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
from gems48.evidence import combine_yager, discounted_binary_mass, minmax_unit

NAME = "gemsdoe48-h48-ds-yager-conflict-20261006"
OUT = ROOT / "docs" / "downloads" / f"{NAME}.tif"
UNC = ROOT / "docs" / "downloads" / f"{NAME}-unassigned-diagnostic.tif"
AUDIT = ROOT / "docs" / "downloads" / f"{NAME}-audit.json"
INPUTS = {
    "dotted": (ROOT / "data/raw/dotted.tif", "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
    "tip": (ROOT / "data/raw/tip.tif", "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"),
    "template": (ROOT / "data/raw/sample_submission.tif", "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"),
}
# Heuristic source discounts fixed before proxy evaluation. Public DTI is not a
# calibrated probability; these values only encode the observed family ordering.
R_DOTTED, R_TIP = 0.90, 0.85


def sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_checked(path: Path, expected: str):
    got = sha(path)
    if got != expected:
        raise SystemExit(f"hash mismatch: {path}: {got} != {expected}")
    with rasterio.open(path) as src:
        return src.read(1), src.profile.copy(), src.transform, src.crs


def write_tif(path: Path, data: np.ndarray, profile: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    p = profile.copy()
    p.update(count=1, dtype="float32", nodata=None, compress="deflate", predictor=3,
             tiled=True, blockxsize=256, blockysize=256)
    with rasterio.open(path, "w", **p) as dst:
        dst.write(data.astype("float32"), 1)


def main():
    dotted, profile, transform, crs = read_checked(*INPUTS["dotted"])
    tip, p2, t2, c2 = read_checked(*INPUTS["tip"])
    template, pt, tt, ct = read_checked(*INPUTS["template"])
    if not (dotted.shape == tip.shape == template.shape and transform == t2 == tt and crs == c2 == ct):
        raise SystemExit("input grids do not match")
    footprint = np.isfinite(template)
    a = discounted_binary_mass(dotted, R_DOTTED)
    b = discounted_binary_mass(tip, R_TIP)
    belief, disbelief, unassigned, conflict = combine_yager(a, b)
    combined = minmax_unit(belief, footprint)
    # Range-harden for the portal behavior reported by the owner: all outside
    # cells are finite zero and no nodata tag is written.
    combined[~footprint] = 0.0
    diagnostic = np.zeros_like(combined)
    diagnostic[footprint] = unassigned[footprint].astype("float32")
    write_tif(OUT, combined, profile)
    write_tif(UNC, diagnostic, profile)

    naive = ((dotted.astype("float64") + tip.astype("float64")) / 2.0)
    active = footprint
    corr = float(np.corrcoef(combined[active], naive[active])[0, 1])
    max_diff = float(np.max(np.abs(combined[active] - naive[active])))
    identical = bool(np.array_equal(combined[active], naive[active].astype("float32")))

    with rasterio.open(OUT) as chk:
        reread = chk.read(1)
        tags = {
            "bands": chk.count, "dtype": chk.dtypes[0], "crs": str(chk.crs),
            "epsg": chk.crs.to_epsg(), "shape": list(chk.shape),
            "transform": list(chk.transform)[:6], "resolution": list(chk.res),
            "nodata": chk.nodata,
        }
    audit = {
        "schema": "GEMSDOE48-audit-v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
        "method": "reliability-discounted binary masses; conjunctive rule; Yager transfer of conflict K to Theta; min-max normalized Bel(F)",
        "scientific_correction": "Classical normalized Dempster's rule renormalizes conflict away. Yager's modified Dempster rule is used because the requested output must preserve disagreement as unassigned mass.",
        "reliability_discounts_preregistered": {"dotted": R_DOTTED, "tip": R_TIP},
        "inputs": {k: {"file": str(v[0].relative_to(ROOT)), "sha256": v[1]} for k, v in INPUTS.items()},
        "input_counts": {"dotted_positive": int((dotted > 0).sum()), "tip_positive": int((tip > 0).sum()), "overlap": int(((dotted > 0) & (tip > 0)).sum()), "union": int(((dotted > 0) | (tip > 0)).sum())},
        "output": {"file": str(OUT.relative_to(ROOT)), "sha256": sha(OUT), "bytes": OUT.stat().st_size, **tags,
                   "all_finite": bool(np.isfinite(reread).all()), "min": float(reread.min()), "max": float(reread.max()),
                   "outside_footprint_all_zero": bool(np.all(reread[~footprint] == 0)), "out_of_range_count": int(((reread < 0) | (reread > 1)).sum()),
                   "positive_pixels": int((reread > 0).sum())},
        "unassigned_diagnostic": {"file": str(UNC.relative_to(ROOT)), "sha256": sha(UNC), "min": float(diagnostic.min()), "max": float(diagnostic.max()), "conflict_positive_pixels": int((conflict[footprint] > 0).sum())},
        "naive_mean_check": {"pearson_correlation": corr, "max_absolute_difference": max_diff, "pixel_identical": identical, "pass_not_naive_mean": bool(not identical and max_diff > 0)},
        "mass_checks": {"belief_min": float(belief.min()), "belief_max": float(belief.max()), "unassigned_min": float(unassigned.min()), "unassigned_max": float(unassigned.max()), "sum_max_abs_error": float(np.max(np.abs(belief + disbelief + unassigned - 1.0)))},
        "format_pass": bool(tags["bands"] == 1 and tags["dtype"] == "float32" and tags["epsg"] == 32611 and tags["shape"] == [3730, 3292] and np.isfinite(reread).all() and reread.min() >= 0 and reread.max() <= 1 and tags["nodata"] is None),
    }
    AUDIT.write_text(json.dumps(audit, indent=2) + "\n")
    print(json.dumps(audit, indent=2))

if __name__ == "__main__":
    main()
