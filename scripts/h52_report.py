#!/usr/bin/env python3
"""Render the H52 candidate sweep (evidence/h52_candidate_sweep_*.json) as a Markdown report
and apply the pre-registered slot gate from docs/research/hypotheses-h52-20261007.md §4."""
from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]


def fmt(x):
    return "—" if x is None else f"{x:.6f}"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sweep", type=pathlib.Path, default=ROOT / "evidence/h52_candidate_sweep_20261007.json")
    ap.add_argument("--out", type=pathlib.Path, default=ROOT / "docs/research/holdout-h52-results-20261007.md")
    ap.add_argument("--title", default="H52-1 candidate sweep — blocked SGMC proxy")
    args = ap.parse_args()
    d = json.load(args.sweep.open())
    refs, vars_ = d["references"], d["variants"]
    folds = list(next(iter(refs.values()))["sgmc_newer_offcat"]["folds"].keys())
    L = [f"# {args.title} — {d['generated_utc']}", "",
         "Protocol: identical to `scripts/run_spatial_holdout.py` — four fixed quadrants, core + 300 m halo domain, "
         "truth = SGMC fault cells > 300 m from any public-catalogue cell (newer pinned derivative; raw-raster sensitivity "
         "in the second table), DTI with α = 0.2, β = 0.8, R = 300 m. The SGMC proxy is a *bedrock geologic-map* fault set; "
         "it is the agreed like-for-like instrument of this repository but a weak proxy for lidar-visible alluvial scarps, "
         "which is what H52-1 targets. Proxy scores are not organizer scores.", "",
         f"Inputs: base `{d['inputs']['base']}` (SHA-256 `{d['inputs']['base_sha256'][:12]}…`), scarp product "
         f"`{d['inputs']['scarp']}` (SHA-256 `{d['inputs']['scarp_sha256'][:12]}…`), layer `{d['inputs']['layer']}`, "
         f"cover ≥ {d['inputs']['cover_min']}. Covered cells {d['counts']['covered_cells']:,}; eligible addition cells "
         f"{d['counts']['eligible_cells']:,}; Poisson-thinned pool {d['counts']['thinned_available']:,}.", "",
         "## Label-free detector check (top cells of the gated height vs catalogue adjacency, per quadrant)", "",
         "| Quadrant / tail | covered cells | selected | base near-rate | lift |", "|---|---:|---:|---:|---:|"]
    gate_lift_ok = True
    for k, v in d["detector_check"].items():
        if not isinstance(v, dict):
            continue
        L.append(f"| {k} | {v['covered_cells']:,} | {v['selected']:,} | {v['base_near_rate']:.4f} | {fmt(v['lift'])} |")
        if k.endswith("top2pct") and (v["lift"] is None or v["lift"] < 2.0):
            gate_lift_ok = False
    L += ["", f"Global thresholds: top-2 % = {d['detector_check']['global_threshold_m_top2pct']:.2f} m, "
              f"top-1 % = {d['detector_check']['global_threshold_m_top1pct']:.2f} m.", "",
          "## Newer-SGMC off-catalogue proxy", "",
          "| Candidate | dots | " + " | ".join(folds) + " | mean | Δ vs C | Δ vs H49 |",
          "|---|---:|" + "---:|" * len(folds) + "---:|---:|---:|"]
    c_mean = refs["C_dotted_02778"]["sgmc_newer_offcat"]["mean_dti"]
    h49_mean = refs["h49_yager_balanced"]["sgmc_newer_offcat"]["mean_dti"]
    h49_folds = refs["h49_yager_balanced"]["sgmc_newer_offcat"]["folds"]
    for name, r in refs.items():
        s = r["sgmc_newer_offcat"]
        L.append(f"| {name} | {r['dots']:,} | " + " | ".join(fmt(s['folds'][f]) for f in folds) +
                 f" | {fmt(s['mean_dti'])} | {s['mean_dti'] - c_mean:+.6f} | {s['mean_dti'] - h49_mean:+.6f} |")
    best = None
    for n, v in vars_.items():
        s = v["sgmc_newer_offcat"]
        pos = sum(s["folds"][f] > h49_folds[f] for f in folds)
        L.append(f"| C + {v['added']:,} lidar additions | {v['dots']:,} | " + " | ".join(fmt(s['folds'][f]) for f in folds) +
                 f" | {fmt(s['mean_dti'])} | {v['delta_vs_C_newer']:+.6f} | {v['delta_vs_h49_newer']:+.6f} ({pos}/4 folds) |")
        if best is None or s["mean_dti"] > best[1]:
            best = (n, s["mean_dti"], pos, v)
    L += ["", "## Raw-SGMC sensitivity (separate raster, not pooled)", "",
          "| Candidate | mean | " + " | ".join(folds) + " |", "|---|---:|" + "---:|" * len(folds)]
    for name, r in refs.items():
        s = r["sgmc_raw_offcat"]
        L.append(f"| {name} | {fmt(s['mean_dti'])} | " + " | ".join(fmt(s['folds'][f]) for f in folds) + " |")
    for n, v in vars_.items():
        s = v["sgmc_raw_offcat"]
        L.append(f"| C + {v['added']:,} | {fmt(s['mean_dti'])} | " + " | ".join(fmt(s['folds'][f]) for f in folds) + " |")
    n, m, pos, v = best
    beats_h49 = m > h49_mean and pos >= 3
    L += ["", "## Pre-registered gate", "",
          f"* Best variant: C + {v['added']:,} additions, mean {m:.6f} (Δ vs C {v['delta_vs_C_newer']:+.6f}; Δ vs H49 "
          f"{v['delta_vs_h49_newer']:+.6f}, {pos}/4 folds above H49).",
          f"* Beats H49 on the mean **and** ≥ 3/4 folds: **{'yes' if beats_h49 else 'no'}**.",
          f"* Detector top-2 % lift ≥ 2× in all four quadrants: **{'yes' if gate_lift_ok else 'no'}**.",
          f"* **Slot decision: {'gate passed on the proxy — still requires the live-anchor bracket and a human go' if (beats_h49 and gate_lift_ok) else 'NOT slot-cleared'}.**",
          "", "Machine-readable: `" + str(args.sweep.resolve().relative_to(ROOT)) + "`."]
    args.out.write_text("\n".join(L) + "\n")
    print(args.out, "best", n, m, "beats_h49", beats_h49, "lift_ok", gate_lift_ok)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
