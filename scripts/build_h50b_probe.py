#!/usr/bin/env python3
"""Build the H50-B probe: radiometric alteration anomaly x DS conflict corridors.

Hypothesis (preregistered in docs/research/hypotheses-20261007.md as H50-B):
hydrothermal alteration (argillic/potassic) depresses Th/K; a low Th/K anomaly
inside a high-K H50 disagreement corridor marks a possible fluid pathway where
the B2 dotted surface and H36-1 rung30 surface disagree. H36-1 is an H19-5/rung-30
repacking, not an actual tip/step-over family; this probe says nothing about
the H33-D tip/step-over surface or faults missing from the catalogue.

Evidence layers
---------------
*  Radiometrics: GeoDAWN airborne K/Th/U/TC (official USGS DOI 10.5066/P93LGLVQ),
   owner-mirror ``data/source_mirrors/geodawn_rad_u8.tif`` (uint8 per-channel
   1st-99th percentile quantisation, 0=nodata), SHA-256 pinned below.  The
   mirror's own metadata calls this "lithology/alteration proxy, not a fault
   detector" -- the corridor gate supplies the structural part.
*  Conflict: the H50 raw conjunctive conflict K of the B2 x H36-1 rung30
   fusion (recomputed from pinned parents; identical to the H50 diagnostic layer).

Construction (every constant fixed before any holdout scoring)
---------------------------------------------------------------
*  corridor    = H50 conflict K > 0.3 (the documented 11.5 % high-conflict tail)
*  highK       = radiometric K band >= its in-footprint median
*  ratio       = Th/K on the quantised bands; robust z = (ratio-med)/(1.4826*MAD)
                 over admissible cells; anomaly score = -z (lower Th/K = better)
*  admissible  = footprint & rad-valid & corridor & highK
*  emission    = binary 1 on the top 37,654 admissible cells by score
                 (mass-matched to the dotted parent); fewer if fewer admissible

Outputs: primary zeros TIF, NaN twin, zip, preregistration receipt.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

from gemsdoe48 import ds50, h51
from gemsdoe48.geotiff import (
    assert_competition_grid,
    assert_same_grid,
    read_band,
    write_float32,
)
from gemsdoe48.grid import write_submission

ROOT = Path(__file__).resolve().parents[1]

PINNED_DOTTED = ROOT / "data/raw/dotted_h33_2_b2_zeros.tif"
PINNED_TIP = ROOT / "data/source_mirrors/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"
RADIOMETRICS = ROOT / "data/source_mirrors/geodawn_rad_u8.tif"
RADIOMETRICS_META = "geodawn_rad.json fetched from GEMSDOE24 on 2026-10-07"

SHA_DOTTED = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
SHA_TIP_H36 = "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641"
SHA_FOOTPRINT = "ddadb8c96cda673b91ddaa0bbed2aa955c358a8f6196c4c4e8fa70d454dd429f"
SHA_RAD = "c22420f75999030d7cc65c9e31e50d232ea6158423bca051613a18a8b20ba682"

CONFLICT_THRESHOLD = 0.3
DATESTAMP = "20261007"
SUBMISSION_NAME = "GEMSDOE48-H50B-ALTERATION-CONFLICT"
SUBMISSION_NOTE = (
    "GEMSDOE48 H50-B | GeoDAWN low-Th/K anomalies in conflict corridors from "
    "B2 x H36-1 rung30 (H19-5 repack, not tip/step-over); 37,654 budget; "
    "negative, unscored probe."
)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def require_sha(path: Path, expected: str, label: str) -> None:
    got = sha256_file(path)
    if got != expected:
        raise SystemExit(f"{label}: SHA-256 {got} != pinned {expected} ({path})")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--outdir", type=Path, default=ROOT / "docs/downloads")
    parser.add_argument("--receipt", type=Path, default=ROOT / "evidence/h50b_preregistration_20261007.json")
    args = parser.parse_args()

    if len(SUBMISSION_NOTE) > 200:
        raise SystemExit("submission note exceeds the portal's 200-character limit")
    require_sha(PINNED_DOTTED, SHA_DOTTED, "dotted parent")
    require_sha(PINNED_TIP, SHA_TIP_H36, "H36-1 rung30 parent")
    require_sha(FOOTPRINT, SHA_FOOTPRINT, "footprint mask")
    require_sha(RADIOMETRICS, SHA_RAD, "radiometric mirror")

    dotted_raw, dotted_profile = read_band(PINNED_DOTTED)
    tip_raw, tip_profile = read_band(PINNED_TIP)
    with rasterio.open(FOOTPRINT) as fp_ds:
        assert_competition_grid(fp_ds.profile, path=FOOTPRINT)
        footprint = fp_ds.read(1) == 1
    with rasterio.open(RADIOMETRICS) as rad_ds:
        rp = rad_ds.profile
        if (rp["width"], rp["height"]) != (3292, 3730) or str(rp["crs"]) != "EPSG:32611":
            raise SystemExit("radiometric mirror grid mismatch")
        if tuple(rp["transform"])[:6] != (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0):
            raise SystemExit("radiometric mirror transform mismatch")
        assert rad_ds.count == 4, "radiometric mirror must carry K, Th, U, TC"
        rad_descriptions = list(rad_ds.descriptions)
        K_band = rad_ds.read(1).astype(np.float64)
        Th_band = rad_ds.read(2).astype(np.float64)

    dotted = np.where(np.isfinite(dotted_raw), dotted_raw, 0.0)
    tip = np.where(np.isfinite(tip_raw), tip_raw, 0.0)
    dotted_mask = (dotted > 0) & footprint
    tip_mask = (tip > 0) & footprint
    budget = int(dotted_mask.sum())  # 37,654, mass-matched to the dotted parent

    # ---------------- conflict corridors (identical to the H50 fusion) ---------
    belief_a = ds50.kernel_belief_surface(dotted_mask)
    belief_b = ds50.kernel_belief_surface(tip_mask)
    fusion = ds50.dempster_fuse(
        belief_a, belief_b, ds50.RHO_MAX,
        ds50.RHO_MAX * (ds50.LIVE_TIP_H36 / ds50.LIVE_DOTTED_B2),
        footprint=footprint,
    )
    corridor = footprint & (fusion.conflict > CONFLICT_THRESHOLD)

    # ---------------- alteration anomaly ---------------------------------------
    rad_valid = footprint & (K_band > 0) & (Th_band > 0)
    k_median = float(np.median(K_band[footprint & (K_band > 0)]))
    high_k = footprint & (K_band >= k_median)
    admissible = rad_valid & corridor & high_k
    ratio = np.zeros_like(K_band)
    ratio[rad_valid] = Th_band[rad_valid] / K_band[rad_valid]
    r_adm = ratio[admissible]
    if r_adm.size < 1000:
        raise SystemExit(f"admissible set too small: {r_adm.size}")
    med = float(np.median(r_adm))
    mad = float(np.median(np.abs(r_adm - med)))
    scale = 1.4826 * mad if mad > 0 else 1.0
    score = np.zeros_like(K_band)
    score[admissible] = -(ratio[admissible] - med) / scale  # low Th/K ranks first

    emission_mask = h51.plausibility_emission(score, budget=budget, where=admissible) > 0
    emitted = int(emission_mask.sum())
    if emitted > budget:
        raise SystemExit("budget exceeded")

    # ---------------- preregistration (stamped before any holdout) -------------
    preregistered_utc = datetime.now(timezone.utc).isoformat()
    preregistration = {
        "schema_version": 1,
        "preregistered_utc": preregistered_utc,
        "hypothesis_id": "H50-B",
        "hypothesis": (
            "Low Th/K radiometric anomalies (argillic alteration signature) inside "
            "high-conflict two-family corridors mark fluid pathways on faults the "
            "catalogue and both families miss."
        ),
        "construction": {
            "conflict_threshold": CONFLICT_THRESHOLD,
            "conflict_layer": "H50 raw conjunctive conflict K (B2 x H36-1 rung30; H19-5 repack, not tip/step-over)",
            "high_k_gate": f"radiometric K band >= in-footprint median ({k_median})",
            "anomaly": "robust z of Th/K over admissible cells, score = -z",
            "budget": budget,
            "budget_rationale": "mass-matched to the dotted parent (owner live 0.2778)",
            "rule": "binary 1 on top-budget admissible cells by anomaly score",
        },
        # ``tip_sha256`` is retained only as a frozen H50-B schema alias for
        # H36-1 rung30, not as a claim that H36 is the tip/step-over family.
        "inputs": {
            "radiometrics": {
                "path": str(RADIOMETRICS.relative_to(ROOT)),
                "sha256": SHA_RAD,
                "bands": rad_descriptions,
                "doi": "10.5066/P93LGLVQ",
                "quantisation": "uint8 1..255 per-channel 1st..99th pct; 0=nodata",
                "provenance": "owner-mirror restored from GEMSDOE24 (sha-verified byte-identical)",
                "mirror_caveat": "lithology/alteration proxy, not a fault detector (mirror metadata)",
            },
            "dotted_sha256": SHA_DOTTED,
            "tip_sha256": SHA_TIP_H36,
        },
        "admissible_cells": int(admissible.sum()),
        "emitted_cells": emitted,
        "no_parameter_tuned_on_holdout_results": True,
    }

    # ---------------- write artifacts -------------------------------------------
    submission = np.where(footprint & emission_mask, 1.0, 0.0).astype(np.float32)
    args.outdir.mkdir(parents=True, exist_ok=True)
    tmp_primary = args.outdir / f".tmp-h50b-{DATESTAMP}.tif"
    write_submission(tmp_primary, submission)
    primary_sha = sha256_file(tmp_primary)
    short_id = primary_sha[:8]
    primary_path = args.outdir / f"gemsdoe48-h50b-alteration-conflict-{DATESTAMP}-{short_id}-zeros.tif"
    primary_path.unlink(missing_ok=True)
    tmp_primary.rename(primary_path)
    zip_path = primary_path.with_suffix(".zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(primary_path, arcname=primary_path.name)
    twin_path = primary_path.with_name(primary_path.name.replace("-zeros.tif", "-nan.tif"))
    write_float32(
        twin_path,
        np.where(footprint, np.where(emission_mask, 1.0, 0.0), np.nan).astype(np.float32),
        dotted_profile,
        valid_mask=footprint,
        description="H50-B alteration-conflict emission; NaN/nodata outside survey footprint",
        tags={
            "model": "H50-B low-Th/K anomaly inside H50 conflict corridors",
            "radiometrics_doi": "10.5066/P93LGLVQ",
            "radiometrics_sha256": SHA_RAD,
            "conflict_threshold": str(CONFLICT_THRESHOLD),
            "submission_name": SUBMISSION_NAME,
        },
    )

    # uniqueness
    existing = sorted(
        p for p in list((ROOT / "docs/downloads").rglob("*.tif")) + list((ROOT / "data").rglob("*.tif"))
        if p.is_file() and p not in (primary_path, twin_path)
    )
    collisions = [str(p.relative_to(ROOT)) for p in existing if sha256_file(p) == primary_sha]
    if collisions:
        raise SystemExit(f"hash collision with existing artifacts: {collisions}")

    preregistration.update({
        "submission_name": SUBMISSION_NAME,
        "submission_note": SUBMISSION_NOTE,
        "primary_file": str(primary_path.relative_to(ROOT)),
        "primary_sha256": primary_sha,
        "primary_bytes": primary_path.stat().st_size,
        "zip_sha256": sha256_file(zip_path),
        "nan_twin_sha256": sha256_file(twin_path),
        "ratio_stats_admissible": {
            "median": med,
            "mad": mad,
            "p5": float(np.percentile(r_adm, 5)),
            "p95": float(np.percentile(r_adm, 95)),
        },
        "corridor_cells": int(corridor.sum()),
        "uniqueness": {"compared_existing_tifs": len(existing), "hash_collisions": collisions},
        "organizer_score": None,
        "score_claim": "No organizer score exists for this artifact; no leaderboard projection is claimed.",
    })
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(preregistration, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "primary": str(primary_path.relative_to(ROOT)),
        "sha256": primary_sha,
        "emitted_cells": emitted,
        "admissible_cells": int(admissible.sum()),
        "corridor_cells": int(corridor.sum()),
        "receipt": str(args.receipt.relative_to(ROOT)),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
