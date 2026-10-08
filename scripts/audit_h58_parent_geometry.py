#!/usr/bin/env python3
"""Geometry audit of the owner-mirrored dotted and tip parents against the public catalogue.

Counts emitted dots by distance to the public catalogue (100 m cells) and checks the claim that the
dotted B2 file is the 0.2708 base minus the dots within 200 m of the catalogue. Writes
evidence/h58_parent_geometry_20261008.json. Public-map geometry only; not organizer evidence.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_h58_ds_b2_h32 import COMPARISON, INPUTS, read_plane, require  # noqa: E402


def main() -> int:
    for label in ("dotted_b2", "catalogue", "footprint"):
        require(*INPUTS[label], label)
    require(*COMPARISON["dotted_base_0.2708"], "dotted_base_0.2708")
    require(*COMPARISON["tip_H33-D_0.2632"], "tip_H33-D_0.2632")
    cat = read_plane(INPUTS["catalogue"][0]) > 0
    fp = read_plane(INPUTS["footprint"][0]) > 0
    dist = distance_transform_edt(~cat, sampling=100.0)
    sets = {
        "B2_owner_0.2778": (read_plane(INPUTS["dotted_b2"][0]) > 0) & fp,
        "dotted_base_0.2708": (read_plane(COMPARISON["dotted_base_0.2708"][0]) > 0) & fp,
        "H33-D_tip_0.2632": (read_plane(COMPARISON["tip_H33-D_0.2632"][0]) > 0) & fp,
        "H32-1_tip_0.2649": (read_plane(INPUTS["tip_h32_1"][0]) > 0) & fp,
    }
    out = {}
    for name, m in sets.items():
        d = dist[m]
        out[name] = {
            "dots": int(m.sum()), "on_catalogue": int((m & cat).sum()),
            "min_distance_m": float(d.min()),
            "within_100m": int((d <= 100).sum()), "within_200m": int((d <= 200).sum()),
            "within_300m": int((d <= 300).sum()),
        }
    base = sets["dotted_base_0.2708"]
    b2 = sets["B2_owner_0.2778"]
    removed = base & ~b2
    added = b2 & ~base
    out["difference_base_to_B2"] = {
        "removed": int(removed.sum()), "added": int(added.sum()),
        "removed_min_distance_m": float(dist[removed].min()) if removed.any() else None,
        "removed_max_distance_m": float(dist[removed].max()) if removed.any() else None,
        "B2_is_base_minus_within_200m": bool(np.array_equal(b2, base & (dist > 200.0))),
        "B2_equals_base_minus_removed_set": bool(int(removed.sum()) == int(base.sum() - b2.sum())),
    }
    payload = {
        "schema": "GEMSDOE48-H58-parent-geometry-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "note": "Owner-mirrored raster geometry against the owner-mirrored public catalogue. Not organizer evidence.",
        "sets": out,
    }
    path = ROOT / "evidence/h58_parent_geometry_20261008.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
