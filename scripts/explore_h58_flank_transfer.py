#!/usr/bin/env python3
"""EXPLORATORY (post-gate, not promotable): apply the B2 flank rule to the tip/Euler H32-1 parent.

B2 = the 0.2708 dotted base minus every dot within 200 m of the public catalogue. Here the same rule is
applied to H32-1 (drop dots within 200 m of the catalogue), giving a budget-matched comparison with B2
(37,657 vs 37,654 dots). Scored with the official metric on the SGMC off-catalogue proxy, full footprint,
four quadrants (300 m halo), and truth-density subsamples. Writes evidence/h58_flank_transfer_explore_20261008.json.
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
sys.path.insert(0, str(ROOT / "src"))
from build_h58_ds_b2_h32 import INPUTS, SGMC_EXPECTED_OFFCAT, read_plane, require, quadrant_scores  # noqa: E402
from gemsdoe48 import ds58  # noqa: E402
from gemsdoe48 import metric as M  # noqa: E402
from gemsdoe48.holdout import quadrants  # noqa: E402


def main() -> int:
    for label in ("dotted_b2", "tip_h32_1", "footprint", "catalogue", "sgmc"):
        require(*INPUTS[label], label)
    fp = read_plane(INPUTS["footprint"][0]) > 0
    cat = read_plane(INPUTS["catalogue"][0]) > 0
    sgmc = read_plane(INPUTS["sgmc"][0]) > 0
    dist = distance_transform_edt(~cat, sampling=100.0)
    offcat = sgmc & fp & (dist > 300.0)
    if int(offcat.sum()) != SGMC_EXPECTED_OFFCAT:
        raise SystemExit("SGMC off-catalogue count mismatch")
    b2 = (read_plane(INPUTS["dotted_b2"][0]) > 0) & fp
    tip = (read_plane(INPUTS["tip_h32_1"][0]) > 0) & fp
    tip_flank = tip & (dist > 200.0)
    quads = quadrants(fp)

    ra, rb = ds58.reliabilities()
    h48_path = ROOT / "docs/downloads/gemsdoe48-h48-1-ds-fusion-b2xh32tip-20261006-407bb7f4-zeros.tif"
    require(h48_path, "6cb2aab8dbd71335152dea7e2fa442126abffc609b426286f5a171f14353b454", "H48-1 prior artifact")
    h48 = (read_plane(h48_path) > 0) & fp
    cands = {
        "H48-1_prior_artifact_binary (repo, 2026-10-06)": h48.astype(float),
        "B2_owner_0.2778": b2.astype(float),
        "H32-1_tip_0.2649 (unpruned)": tip.astype(float),
        "H32-1_tip_flank_pruned_200m (EXPLORATORY)": tip_flank.astype(float),
        "H58_DS_unpruned_inputs (primary artifact)": ds58.fuse_dots(b2, tip, fp, ra, rb).belief,
        "H58_DS_flank_pruned_inputs (EXPLORATORY; not published, duplicates H48-1 pairing)": ds58.fuse_dots(b2, tip_flank, fp, ra, rb).belief,
        "union_flank_pruned_binary (EXPLORATORY)": (b2 | tip_flank).astype(float),
    }
    out = {"dots": {k: int((v > 0).sum()) for k, v in cands.items()}, "full_footprint_dti": {}, "quadrant_dti": {},
           "density_mean_dti": {}}
    for k, v in cands.items():
        p = np.where(cat, 0.0, v)
        out["full_footprint_dti"][k] = float(M.dti(p, offcat, fp).dti)
        out["quadrant_dti"][k] = quadrant_scores(p, offcat, fp, quads)
    b2q = np.array(out["quadrant_dti"]["B2_owner_0.2778"])
    out["quadrant_wins_vs_B2"] = {k: int(np.sum(np.array(v) > b2q)) for k, v in out["quadrant_dti"].items()}
    out["full_minus_B2"] = {k: v - out["full_footprint_dti"]["B2_owner_0.2778"] for k, v in out["full_footprint_dti"].items()}
    idx = np.flatnonzero(offcat.ravel())
    for dens in (25000, 12632):
        vals = {k: [] for k in cands}
        for seed in (1, 2, 3):
            rng = np.random.default_rng(seed)
            keep = rng.choice(idx, size=dens, replace=False)
            truth = np.zeros(offcat.size, dtype=bool)
            truth[keep] = True
            truth = truth.reshape(offcat.shape)
            for k, v in cands.items():
                vals[k].append(float(M.dti(np.where(cat, 0.0, v), truth, fp).dti))
        out["density_mean_dti"][str(dens)] = {k: float(np.mean(v)) for k, v in vals.items()}
    payload = {
        "schema": "GEMSDOE48-H58-flank-transfer-explore-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "status": "EXPLORATORY, post-gate; not used for any promotion decision",
        "rule": "drop H32-1 dots within 200 m of the public catalogue (same rule that makes B2 the 0.2708 base minus its flank dots)",
        "truth": "SGMC off-catalogue public-map proxy (62,122 px); predictions on catalogue cells zeroed",
        "decision_note": "Post-gate exploration. The primary H58-A artifact was fixed before these variants were scored. The flank-pruned DS variant is not published: its support duplicates the earlier H48-1 file (Jaccard 0.982). Any variant here must be preregistered before any scoring that could promote it.",
        "results": out,
    }
    path = ROOT / "evidence/h58_flank_transfer_explore_20261008.json"
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
