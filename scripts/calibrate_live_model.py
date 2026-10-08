#!/usr/bin/env python3
"""INVALIDATED H55 surrogate; forensic reproduction requires explicit opt-in.

The historical calibration infers hidden-truth mass with the generally false
``FPw = S - TPw`` substitution. It is not an official-metric inverse, score
estimate, ceiling, or promotion gate. Its command refuses by default; only pass
``--legacy-audit-only`` to reproduce old outputs for forensic comparison.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48 import h55 as h55_mod                                            # noqa: E402
from gemsdoe48.live_model import (LIVE_ARTIFACTS, OUT_OF_FAMILY, ForwardModel,  # noqa: E402
                                  calibrate, coverage, invert_truth, load_binary,
                                  max_credit_field)

CATALOGUE = ROOT / "data/official/labels.tif"
FOOTPRINT = ROOT / "data/source_mirrors/footprint-mask.tif"

#: leaderboard snapshot read once on 2026-10-06 UTC (docs/data/leaderboard_20261007.json)
LEADERBOARD = [("xiaofanhu", 0.3774), ("alexoktaba", 0.3345), ("nchuzhoy", 0.3262),
               ("DARD", 0.3195), ("(rank 8)", 0.2888), ("extradr19 (this family)", 0.2778)]


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    forensic_root = ROOT / "evidence/forensic"
    parser.add_argument("--output", type=Path,
                        default=forensic_root / "live_model_calibration_legacy_20261007.json")
    parser.add_argument("--csv", type=Path,
                        default=forensic_root / "live_model_inverted_truth_legacy_20261007.csv")
    parser.add_argument("--no-frontier", action="store_true",
                        help="skip the ~5 min from-scratch greedy coverage frontier")
    parser.add_argument("--frontier-max", type=int, default=45_000)
    parser.add_argument("--legacy-audit-only", action="store_true",
                        help="required opt-in; outputs reproduce an invalidated surrogate, not a score gate")
    args = parser.parse_args()
    if not args.legacy_audit_only:
        parser.error("invalidated historical calibration; rerun only with --legacy-audit-only for forensic reproduction")
    print("LEGACY AUDIT ONLY — INVALIDATED; NOT A SCORE ESTIMATE OR PROMOTION GATE")

    missing = [a.path for a in (*LIVE_ARTIFACTS, OUT_OF_FAMILY) if not (ROOT / a.path).exists()]
    if missing:
        raise SystemExit("missing mirrors, run: python scripts/restore_h55_inputs.py\n  "
                         + "\n  ".join(missing))
    for art in (*LIVE_ARTIFACTS, OUT_OF_FAMILY):
        got = sha256_file(ROOT / art.path)
        if got != art.sha256:
            raise SystemExit(f"SHA-256 mismatch for {art.path}: pinned {art.sha256}, got {got}")
    print("all nine live-scored mirrors restored byte-identical to their pins")

    backbone = load_binary(ROOT / LIVE_ARTIFACTS[0].path)
    catalogue = load_binary(CATALOGUE)
    footprint = load_binary(FOOTPRINT)
    catalogue_distance_m = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))

    receipt = calibrate(backbone, catalogue_distance_m, legacy_audit_only=True)
    receipt["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    receipt["provenance"] = {
        "class": "OWNER-REPORT",
        "statement": ("every live score used here was pasted into the session brief by the "
                      "repository owner; no organizer receipt links any file to any score"),
        "mirrors": [{"key": a.key, "path": a.path, "sha256": a.sha256, "live": a.live,
                     "note": a.note} for a in (*LIVE_ARTIFACTS, OUT_OF_FAMILY)],
        "catalogue_sha256": sha256_file(CATALOGUE),
        "footprint_sha256": sha256_file(FOOTPRINT),
        "containment_verified_pixelwise": True,
    }

    model = ForwardModel(receipt["hidden_truth_fit"]["hidden_truth_px"],
                         receipt["rho_fit"]["rho"], receipt["eligible_backbone_px"],
                         legacy_audit_only=True)
    eligible = backbone & (catalogue_distance_m > 200.0)

    # ---- inverted truth table + the greedy coverage frontier (the family ceiling)
    rows = []
    for art in LIVE_ARTIFACTS:
        mask = load_binary(ROOT / art.path)
        s = int(mask.sum())
        t = invert_truth(art.live, s, model.hidden_truth_px, legacy_audit_only=True)
        rows.append({"artifact": art.key, "emitted_px": s, "live": art.live,
                     "inverted_tpw": t, "recall": t / model.hidden_truth_px,
                     "credit_per_px": t / s,
                     "cov_eligible_backbone": coverage(mask, eligible)})
    receipt["inverted_truth_table"] = rows

    # ---- from-scratch greedy coverage frontier: the family ceiling
    core_live_best = load_binary(ROOT / "data/families/dotted_b2_prune_02778.tif")
    cov_c = coverage(core_live_best, eligible)
    dti_c_model = model.dti(cov_c, 37_654)
    if args.no_frontier:
        frontier = {"status": "skipped (--no-frontier)"}
        achievable_cov = achievable_t = None
    else:
        print(f"tracing the from-scratch greedy coverage frontier over B_elig "
              f"({int(eligible.sum())} px) up to {args.frontier_max} dots ...")
        empty = np.zeros_like(eligible)
        priced = h55_mod.price_addition_path(empty, eligible, eligible, break_even_bar=0.0,
                                             max_add=args.frontier_max, model=model)
        path = priced["path"]
        best = priced["argmax_prefix"]
        achievable_cov = float(best["coverage"])
        achievable_t = model.tpw(achievable_cov)
        frontier = {
            "target_and_pool": "B_elig (backbone AND >200 m off-catalogue)",
            "objective": "greedy maximum coverage of B_elig under the 300 m triangular kernel",
            "dots_traced": len(path) - 1,
            "argmax_prefix": best,
            "argmax_model_dti": float(best["dti_pred"]),
            "argmax_live_equivalent": 0.2778 + (float(best["dti_pred"]) - dti_c_model),
            "sampled_path": [p for p in path if p["n"] % 2500 == 0 or p is best],
        }
        print(f"frontier maximum: n={best['n']} Cov={best['coverage']:,.1f} "
              f"model DTI={best['dti_pred']:.4f} live-equivalent={frontier['argmax_live_equivalent']:.4f}")
    receipt["family_coverage_frontier"] = frontier

    # ---- ceiling table.  Two separate reachability tests, because they answer
    # different questions: (i) does the field CONTAIN that much truth at all (dense
    # backbone yield), and (ii) can any 37,654-px SUBSET of it deliver that much
    # (measured coverage geometry).
    t_dense = invert_truth(0.1922, 121_131, model.hidden_truth_px, legacy_audit_only=True)
    ceiling_live_equiv = frontier.get("argmax_live_equivalent")
    ceiling = []
    for who, dti in LEADERBOARD:
        needed = model.tpw_needed(dti, 37_654)
        ceiling.append({
            "who": who, "dti": dti, "tpw_needed_at_37654_px": needed,
            "recall_needed": needed / model.hidden_truth_px,
            "pct_above_C_tpw": 100.0 * (needed / invert_truth(0.2778, 37_654,
                                                              model.hidden_truth_px, legacy_audit_only=True) - 1.0),
            "test_1_within_dense_backbone_truth_yield": bool(needed <= t_dense),
            "dense_backbone_truth_yield": t_dense,
            "test_2_achievable_by_any_37654_px_subset": (
                bool(needed <= achievable_t) if achievable_t is not None else None),
            "achievable_tpw_at_frontier": achievable_t,
            # The decisive test: the frontier argmax maximises model DTI over ALL
            # subset sizes, so its live-equivalent is the ceiling for every emission
            # drawn from this corridor field at any mass.
            "test_3_reachable_at_any_mass_from_this_field": (
                bool(dti <= ceiling_live_equiv) if ceiling_live_equiv else None),
            "field_ceiling_live_equivalent_at_any_mass": ceiling_live_equiv,
        })
    receipt["ceiling_table"] = ceiling
    headroom = (float(frontier["argmax_model_dti"]) - dti_c_model) if achievable_cov else None
    receipt["family_ceiling"] = {
        "cov_of_live_best_C": cov_c,
        "model_dti_of_live_best_C": dti_c_model,
        "model_bias_on_C_live_minus_pred": 0.2778 - dti_c_model,
        "achievable_cov_at_frontier": achievable_cov,
        "coverage_shortfall_of_C_pct": (100.0 * (1 - cov_c / achievable_cov)
                                        if achievable_cov else None),
        "model_dti_at_frontier": float(frontier.get("argmax_model_dti")) if achievable_cov else None,
        "live_equivalent_at_frontier": frontier.get("argmax_live_equivalent"),
        "in_family_headroom_model_units": headroom,
        "instrument_rms_relative_error_pct": receipt["rho_fit"]["rms_relative_error_pct"],
        "instrument_resolution_in_dti_units": 0.2778 * receipt["rho_fit"]["rms_relative_error_pct"] / 100.0,
        "headroom_below_instrument_resolution": (
            bool(headroom < 0.2778 * receipt["rho_fit"]["rms_relative_error_pct"] / 100.0)
            if headroom is not None else None),
    }
    receipt["union_priced"] = {
        "px": int((load_binary(ROOT / "data/families/dotted_b2_prune_02778.tif")
                   | load_binary(ROOT / "data/raw/tip_h33d_stepover.tif")).sum()),
        "cov": coverage(load_binary(ROOT / "data/families/dotted_b2_prune_02778.tif")
                        | load_binary(ROOT / "data/raw/tip_h33d_stepover.tif"), eligible),
    }
    receipt["union_priced"]["model_dti"] = model.dti(receipt["union_priced"]["cov"],
                                                     receipt["union_priced"]["px"])
    receipt["footprint_px"] = int(footprint.sum())
    receipt["catalogue_px"] = int(catalogue.sum())
    receipt["backbone_px"] = int(backbone.sum())

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    with args.csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n|G| = {model.hidden_truth_px:,.1f} px    rho = {model.rho:.6f}    "
          f"RMS rel err = {receipt['rho_fit']['rms_relative_error_pct']:.3f} %")
    print(f"{'artifact':18s} {'px':>7s} {'live':>7s} {'T':>8s} {'recall':>7s} {'T/px':>7s} {'Cov':>9s}")
    for r in rows:
        print(f"{r['artifact']:18s} {r['emitted_px']:7d} {r['live']:7.4f} {r['inverted_tpw']:8.1f} "
              f"{r['recall']:7.4f} {r['credit_per_px']:7.4f} {r['cov_eligible_backbone']:9.1f}")
    print(f"\n{'target':26s} {'DTI':>7s} {'T needed@37654':>14s} {'recall':>7s} {'%>C':>7s} "
          f"{'in field?':>9s} {'37,654 subset?':>14s} {'ANY mass?':>10s}")
    for c in ceiling:
        t2 = c['test_2_achievable_by_any_37654_px_subset']
        t3 = c['test_3_reachable_at_any_mass_from_this_field']
        print(f"{c['who']:26s} {c['dti']:7.4f} {c['tpw_needed_at_37654_px']:14.1f} "
              f"{c['recall_needed']:7.4f} {c['pct_above_C_tpw']:+7.1f} "
              f"{'yes' if c['test_1_within_dense_backbone_truth_yield'] else 'NO':>9s} "
              f"{('yes' if t2 else 'NO') if t2 is not None else 'n/a':>14s} "
              f"{('yes' if t3 else 'NO') if t3 is not None else 'n/a':>10s}")
    fc = receipt["family_ceiling"]
    print(f"\nfamily ceiling: C Cov {fc['cov_of_live_best_C']:,.1f} of achievable "
          f"{fc['achievable_cov_at_frontier'] or float('nan'):,.1f} "
          f"({fc['coverage_shortfall_of_C_pct'] or float('nan'):.2f} % short); model DTI "
          f"{fc['model_dti_of_live_best_C']:.4f} -> {fc['model_dti_at_frontier'] or float('nan'):.4f}; "
          f"headroom {fc['in_family_headroom_model_units'] or float('nan'):+.4f} vs instrument "
          f"resolution +/-{fc['instrument_resolution_in_dti_units']:.4f}")
    oof = receipt["out_of_family_transfer_check"]
    if "implied_rho" in oof:
        print(f"\nout-of-family transfer: {oof['key']} live {oof['live']} -> implied rho "
              f"{oof['implied_rho']:.5f} vs family {model.rho:.5f}; model transfer error "
              f"{oof['relative_transfer_error_pct']:+.1f} %")
    print(f"\nreceipt {args.output.relative_to(ROOT)}\ncsv     {args.csv.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
