#!/usr/bin/env python3
"""Truth-density sensitivity for the H58 parents and candidates (public SGMC proxy, official metric).

Why: the 0.2778 -> 0.2708 owner ladder is a pruning of dots 100-200 m from the public catalogue.
Whether such pruning helps depends on how sparse the *hidden* truth is, which is unknown.  This
script re-scores the same surfaces against random subsamples of the public SGMC off-catalogue proxy
at three truth densities: the full 62,122 px, 25,000 px, and 12,632 px.  The 12,632 value is taken
from the repository's older inversion, which the metric-identity erratum withdrew as an estimate; it
is used here only as one sensitivity grid point, never as a measured hidden density.

Outputs evidence/holdout_h58_density_20261008.json.  Nothing here is organizer or leaderboard evidence.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48 import ds58  # noqa: E402
from gemsdoe48 import metric as M  # noqa: E402

from build_h58_ds_b2_h32 import COMPARISON, INPUTS, SGMC_EXPECTED_OFFCAT, read_plane, require  # noqa: E402

DENSITIES = (62122, 25000, 12632)
SEEDS = (1, 2, 3)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", type=Path, default=ROOT / "evidence/holdout_h58_density_20261008.json")
    args = ap.parse_args()
    for label, (path, sha) in {**INPUTS, "H49_yager_pignistic": COMPARISON["H49_yager_pignistic"],
                               "dotted_base_0.2708": COMPARISON["dotted_base_0.2708"]}.items():
        require(path, sha, label)

    with rasterio.open(INPUTS["footprint"][0]) as ds:
        fp = ds.read(1) == 1
    cat = read_plane(INPUTS["catalogue"][0]) > 0
    sgmc = read_plane(INPUTS["sgmc"][0]) > 0
    dotted = (read_plane(INPUTS["dotted_b2"][0]) > 0) & fp
    tip = (read_plane(INPUTS["tip_h32_1"][0]) > 0) & fp
    base = (read_plane(COMPARISON["dotted_base_0.2708"][0]) > 0) & fp
    h49 = read_plane(COMPARISON["H49_yager_pignistic"][0])
    dist_cat = distance_transform_edt(~cat, sampling=100.0)
    offcat = sgmc & fp & (dist_cat > 300.0)
    if int(offcat.sum()) != SGMC_EXPECTED_OFFCAT:
        raise SystemExit("SGMC off-catalogue count mismatch")

    ra, rb = ds58.reliabilities()
    h58 = ds58.fuse_dots(dotted, tip, fp, ra, rb).belief
    candidates = {
        "B2_owner_0.2778": dotted.astype(np.float64),
        "dotted_base_0.2708": base.astype(np.float64),
        "H32-1_tip_owner_0.2649": tip.astype(np.float64),
        "H49_yager_pignistic": h49,
        "H58_dot_supported_DS": h58,
    }
    for name in candidates:
        candidates[name] = np.where(cat, 0.0, np.clip(candidates[name], 0.0, 1.0))

    idx = np.flatnonzero(offcat.ravel())
    grid = {}
    for dens in DENSITIES:
        per_name = {n: [] for n in candidates}
        for seed in SEEDS:
            if dens >= idx.size:
                truth = offcat
            else:
                rng = np.random.default_rng(seed)
                keep = rng.choice(idx, size=dens, replace=False)
                truth = np.zeros(offcat.size, dtype=bool)
                truth[keep] = True
                truth = truth.reshape(offcat.shape)
            for name, pred in candidates.items():
                per_name[name].append(float(M.dti(np.where(fp, pred, 0.0), truth, fp).dti))
        b2 = np.array(per_name["B2_owner_0.2778"])
        grid[str(dens)] = {
            "truth_px_per_draw": int(dens) if dens < idx.size else int(offcat.sum()),
            "seeds": list(SEEDS) if dens < idx.size else "full (no subsampling)",
            "mean_dti": {n: float(np.mean(v)) for n, v in per_name.items()},
            "per_seed_dti": per_name,
            "B2_minus_dotted_base_mean": float(np.mean(b2 - np.array(per_name["dotted_base_0.2708"]))),
            "B2_beats_dotted_base_seeds": int(np.sum(b2 > np.array(per_name["dotted_base_0.2708"]))),
            "H49_minus_B2_mean": float(np.mean(np.array(per_name["H49_yager_pignistic"]) - b2)),
            "H58_minus_B2_mean": float(np.mean(np.array(per_name["H58_dot_supported_DS"]) - b2)),
        }

    payload = {
        "schema": "GEMSDOE48-H58-density-sensitivity-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "truth": "public SGMC off-catalogue proxy (62,122 px full), random subsamples at 25,000 and 12,632 px",
        "metric": "official distance-weighted Tversky, alpha=0.2, beta=0.8, 300 m triangular kernel; full footprint",
        "masking": "predictions on pixel-exact catalogue cells set to 0",
        "density_12632_provenance": "value from the withdrawn repository inversion (docs/research/metric-identity-erratum-20261007.md); sensitivity grid point only",
        "grid": grid,
        "reading": "The B2-minus-0.2708 pruning gain and the H49-minus-B2 difference both change with truth density, so proxy rankings are density-dependent and cannot select a leaderboard candidate.",
        "limitations": [
            "The truth is a public map proxy; hidden expert labels may differ in density and location.",
            "Random subsamples are not spatial blocks; this is a density sensitivity, not a blocked holdout.",
        ],
        "pinned_inputs": {k: {"path": str(p.relative_to(ROOT)), "sha256": s} for k, (p, s) in {
            **INPUTS, "H49_yager_pignistic": COMPARISON["H49_yager_pignistic"],
            "dotted_base_0.2708": COMPARISON["dotted_base_0.2708"]}.items()},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    for dens, row in grid.items():
        print(dens, {k: round(v, 5) for k, v in row["mean_dti"].items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
