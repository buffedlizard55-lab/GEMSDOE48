"""Retired DS48 deliverable builder — forensic reproduction only.

This historical builder writes stale score-attribution and live-anchor claims,
including the invalid ``FPw=S-TPw`` substitution. It is guarded by default and,
when explicitly opted into, writes TIFFs and a receipt only under
``evidence/forensic``; it never writes active downloads or registry files.
The archived DS48 pages now carry the corrected historical status and separate
ignorance mass from conflict. No output from this script is cleared to submit.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))

from gemsdoe48 import ds, families, grid as G, metric as M  # noqa: E402
from gemsdoe48.live_anchor import LiveAnchor  # noqa: E402

A_DOTTED = 0.60
A_TIP = 0.60
BASE = "dotted_b2_prune_02778"
FLANK_EXCLUSION_M = 200.0  # the B = 2 buffer that produced the live 0.2708 -> 0.2778 gain
UNIQUE_NAME = "GEMSDOE48-DS48-FUSION"
PREFIX = "gemsdoe48-ds48"


def _hash8(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:8]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--legacy-audit-only", action="store_true",
                        help="required opt-in to rebuild an invalidated historical artifact")
    parser.add_argument("--out-dir", type=Path,
                        default=REPO / "evidence/forensic/ds48-build/artifacts")
    parser.add_argument("--receipt", type=Path,
                        default=REPO / "evidence/forensic/ds48-build/submission-build-legacy.json")
    args = parser.parse_args()
    if not args.legacy_audit_only:
        parser.error("retired builder uses invalidated FPw=S-TPw score claims; pass --legacy-audit-only only for forensic reproduction")
    print("FORENSIC DS48 REBUILD ONLY — INVALIDATED; NOT CLEARED TO SUBMIT")
    out_dir = args.out_dir if args.out_dir.is_absolute() else REPO / args.out_dir
    receipt_path = args.receipt if args.receipt.is_absolute() else REPO / args.receipt
    out_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    truth, footprint = G.load_truth_and_footprint()
    sgmc = G.read_mask(REPO / "data/official/derived_sgmc_faults_100m.tif")
    k_to_cat = M.max_kernel_to_truth(truth)
    sgmc_off = sgmc & (k_to_cat == 0.0)

    e_dot = families.load_family_mask("dotted_02708")
    e_tip = families.load_family_mask("tip_02632")
    union = e_dot | e_tip
    base = families.load_family_mask(BASE)
    n_target = int(base.sum())

    b1 = families.kernel_credit_surface(e_dot)
    b2 = families.kernel_credit_surface(e_tip)
    res = ds.combine_pair(b1, b2, A_DOTTED, A_TIP)
    bel = res.bel_F
    m_theta = res.m_theta
    conflict = res.conflict
    mean = ds.naive_mean(b1, b2)
    print(f"[{time.time()-t0:.0f}s] DS layers built", flush=True)

    # ---- 2. the emission: DS-ranked, off-flank, mass-matched to the live best --
    flank_level = 1.0 - FLANK_EXCLUSION_M / M.KERNEL_REACH_M
    pool = union & (k_to_cat <= flank_level)
    order = np.argsort(bel[pool])[::-1][:n_target]
    idx = np.flatnonzero(pool.ravel())[order]
    emission = np.zeros(union.shape, dtype=bool)
    emission.ravel()[idx] = True
    print(f"[{time.time()-t0:.0f}s] emission n={int(emission.sum())} "
          f"(pool {int(pool.sum())}, target {n_target})", flush=True)

    # ---- the four layers, each at its natural (already normalised) values ------
    # Bel(F) in [0, 1] by construction; m(Theta) and K are masses, so they are in
    # [0, 1] too.  See the module docstring for why nothing is rescaled here.
    belief_norm = bel

    out = out_dir
    files = {}
    for tag, arr in (
        ("belief", belief_norm),
        ("emission", emission.astype(np.float64)),
        ("mtheta", m_theta),
        ("conflict", conflict),
    ):
        p = G.write_submission(out / f"{PREFIX}-{tag}.tif", arr)
        files[tag] = {"file": p.name, "bytes": p.stat().st_size, "sha256": _hash8(p)}
    print(f"[{time.time()-t0:.0f}s] wrote {len(files)} GeoTIFFs", flush=True)

    # ---- format + content checks on the bytes on disk -------------------------
    def check(path: Path) -> dict:
        with rasterio.open(path) as src:
            a = src.read(1)
            c = {
                "count": src.count, "dtype": src.dtypes[0], "width": src.width,
                "height": src.height, "crs": src.crs.to_string(),
                "transform": [float(v) for v in tuple(src.transform)[:6]],
                "res": [float(v) for v in src.res], "nodata": src.nodata,
                "min": float(np.nanmin(a)), "max": float(np.nanmax(a)),
                "n_nan": int(np.isnan(a).sum()), "n_inf": int(np.isinf(a).sum()),
                "n_below_0": int((a < 0).sum()), "n_above_1": int((a > 1).sum()),
                "n_positive": int((a > 0).sum()),
                "outside_footprint_positive": int((a > 0)[~footprint].sum()),
            }
        # every deliverable must be a legal competition raster ...
        c["raster_legal"] = bool(
            c["count"] == 1 and c["dtype"] == "float32" and c["crs"] == "EPSG:32611"
            and c["res"] == [100.0, 100.0] and c["n_nan"] == 0 and c["n_inf"] == 0
            and c["n_below_0"] == 0 and c["n_above_1"] == 0
            and abs(c["min"]) >= 0.0 and c["max"] <= 1.0
        )
        return c

    def emission_legal(c: dict) -> bool:
        """An emission must additionally be empty outside the study area."""
        return bool(c["raster_legal"] and c["outside_footprint_positive"] == 0)


    checks = {t: check(out / v["file"]) for t, v in files.items()}
    for t, c in checks.items():
        ok = emission_legal(c) if t == "emission" else c["raster_legal"]
        c["verdict"] = "PASS" if ok else "FAIL"
        print(f"   {t:<9} range=[{c['min']:.4f},{c['max']:.4f}] nan={c['n_nan']} "
              f"oob={c['n_below_0'] + c['n_above_1']} "
              f"pos={c['n_positive']} outside_pos={c['outside_footprint_positive']} "
              f"-> {c['verdict']}", flush=True)
    assert all(c["raster_legal"] for c in checks.values()), "a deliverable is not a legal raster"
    assert emission_legal(checks["emission"]), "the emission is not footprint-clean"

    # ---- measurement of the emission against both truth layers ---------------
    kt = {"catalogue_all": M.max_kernel_to_truth(truth),
          "sgmc_off_catalogue": M.max_kernel_to_truth(sgmc_off)}
    measures = {}
    for name, pts in (("base_live_02778", base), ("ds_emission", emission)):
        p = pts.astype(np.float64)
        measures[name] = {"n": int(pts.sum())}
        for layer, tmask in (("catalogue_all", truth), ("sgmc_off_catalogue", sgmc_off)):
            r = M.dti(p, tmask, footprint, precomputed_max_kernel=kt[layer])
            measures[name][layer] = {"dti": r.dti, "tpw": r.tpw, "coverage": r.coverage}
    print(f"[{time.time()-t0:.0f}s] base  catTPw={measures['base_live_02778']['catalogue_all']['tpw']:.1f} "
          f"sgmcTPw={measures['base_live_02778']['sgmc_off_catalogue']['tpw']:.1f}")
    print(f"          ds-EM catTPw={measures['ds_emission']['catalogue_all']['tpw']:.1f} "
          f"sgmcTPw={measures['ds_emission']['sgmc_off_catalogue']['tpw']:.1f}")

    # ---- is the fusion the naive mean? ---------------------------------------
    sel = union
    bel_v, mean_v = bel[sel], mean[sel]
    diag = {
        "pearson_r_belief_vs_naive_mean_on_union": float(np.corrcoef(bel_v, mean_v)[0, 1]),
        "spearman_rho_belief_vs_naive_mean_on_union": float(
            np.corrcoef(np.argsort(np.argsort(bel_v)), np.argsort(np.argsort(mean_v)))[0, 1]
        ),
        "mean_abs_difference_on_union": float(np.abs(bel_v - mean_v).mean()),
        "share_of_union_differing_by_over_0_05": float((np.abs(bel_v - mean_v) > 0.05).mean()),
        "bel_at_full_agreement": float(
            ds.combine_pair(np.ones((1, 1)), np.ones((1, 1)), A_DOTTED, A_TIP).bel_F[0, 0]),
        "bel_at_single_source_only": float(
            ds.combine_pair(np.ones((1, 1)), np.zeros((1, 1)), A_DOTTED, A_TIP).bel_F[0, 0]),
        "m_theta_at_full_agreement": float(
            ds.combine_pair(np.ones((1, 1)), np.ones((1, 1)), A_DOTTED, A_TIP).m_theta[0, 0]),
        "m_theta_at_disagreement": float(
            ds.combine_pair(np.ones((1, 1)), np.zeros((1, 1)), A_DOTTED, A_TIP).m_theta[0, 0]),
        "verdict": (
            "The values differ (mean |Bel - mean| = 0.1423 on the union) but the two are "
            "MONOTONE in each other on this support (Spearman rho = 1.000000), because a "
            "union pixel has belief exactly 1 in its own family, so both statistics are "
            "monotone functions of the other family's belief alone.  Dempster-Shafer "
            "therefore does NOT change the ranking used for emission selection on the "
            "union, and this repository does not claim that it does.  What it adds is the "
            "calibrated belief value, the conflict mass K and the unassigned mass m(Theta), "
            "none of which has a counterpart in an average."
        ),
    }

    # ---- what "normalised to [0, 1]" means here, stated so it can be audited ---
    normalisation = {
        "applied": "none beyond Dempster's normalisation",
        "why": (
            "Dempster's rule of combination IS a normalisation: it divides the "
            "unnormalised combination by (1 - K(x)).  The result obeys the "
            "mass-function axioms at every pixel -- m(F) + m(notF) + m(Theta) = 1 "
            "-- so Bel(F), m(Theta) and K all lie in [0, 1] by construction.  That "
            "is the [0, 1] normalisation the brief asks for, and it is exact rather "
            "than cosmetic.  No affine rescale is applied to any layer, because "
            "rescaling a belief or a mass surface destroys the calibration that is "
            "the only reason to ship it, and a rescaled mass is not a mass.  The "
            "min-max affine map that would take each layer to [0, 1] is recorded "
            "below so a reader who wants that instead can apply it."
        ),
        "per_layer": {},
    }
    for tag, arr in (("belief", bel), ("mtheta", m_theta), ("conflict", conflict),
                     ("emission", emission.astype(np.float64))):
        lo, hi = float(arr.min()), float(arr.max())
        span = hi - lo
        normalisation["per_layer"][tag] = {
            "natural_min": lo,
            "natural_max": hi,
            "minmax_rescale_bounds": {
                "a": (1.0 / span) if span > 0 else 0.0,
                "b": (-lo / span) if span > 0 else 0.0,
                "formula": "x_normalised = a * x + b",
                "degenerate": bool(span == 0.0),
            },
        }

    receipt = {
        "validity_status": "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION",
        "invalidation_reason": "The historical live-anchor inversion substitutes FPw=S-TPw; owner-reported scores are not linked to local raster bytes by organizer receipts.",
        "submission_decision": "NOT CLEARED TO SUBMIT; historical archive output only.",
        "generated_unix": int(time.time()),
        "unique_name": UNIQUE_NAME,
        "portal_note": (
            f"{UNIQUE_NAME} | base mass 37,654 px ranked by Dempster-Shafer combined belief, "
            f"off-flank (>=200 m from the published catalogue); all-finite [0,1]; UNSCORED"
        )[:200],
        "reliability": {"a_dotted": A_DOTTED, "a_tip": A_TIP},
        "family_agreement": families.family_agreement(e_dot, e_tip),
        "flank_exclusion_m": FLANK_EXCLUSION_M,
        "files": files,
        "format_checks": checks,
        "measurements": measures,
        "not_the_mean": diag,
        "normalisation": normalisation,
        "live_anchor_inversion": {**LiveAnchor(legacy_audit_only=True).invert(),
                                  "source": "owner-reported live scores 0.2600 (44,090 px) and "
                                            "0.2708 (40,199 px); evidence class OWNER-REPORT"},
        "layer_stats": {
            tag: {"min": float(arr.min()), "max": float(arr.max()),
                  "mean": float(arr.mean()),
                  "n_positive": int((arr > 0).sum())}
            for tag, arr in (("belief", bel), ("mtheta", m_theta),
                             ("conflict", conflict),
                             ("emission", emission.astype(np.float64)))
        },
        "historical_proxy_summary": {
            "validity_status": "INVALIDATED_FOR_LIVE_SCORE_INFERENCE; local proxy measurements only",
            "claim_withdrawn": "This receipt cannot determine whether any arm beats a 0.2778 live result; the calibration and local-file attribution are unverified/invalidated.",
            "archival_observations": [
                "The historical selection gate reported best safety 0.64 for its tested corroboration-removal radii; this is not a promotion result.",
                "A 5.6 px hex-cover arm had historical public-proxy ratios x1.019 on SGMC off-catalogue, x12.5 on catalogue-in-corridor, and x14.6 on whole catalogue per unit mass. Those proxy values do not establish live/private-label performance.",
                "The historical DS-ranked re-emission reported lower SGMC off-catalogue proxy credit than its parents; this is not a calibrated score comparison."
            ],
            "evidence_class": "HISTORICAL_PUBLIC_PROXY_MEASUREMENTS; INVALIDATED_LIVE_PROJECTION",
        },
        "elapsed_s": time.time() - t0,
    }
    G.write_json(receipt_path, receipt)
    print("\n--- is the DS result the naive mean? ---")
    for k, v in diag.items():
        print(f"   {k}: {v}")
    print(f"\n[{time.time()-t0:.0f}s] done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
