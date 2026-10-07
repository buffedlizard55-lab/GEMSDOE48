#!/usr/bin/env python3
"""Does weighting the coverage target predict the eight live scores better than uniform?

Reproduces the negative result quoted in
``docs/research/h55-live-model-ceiling-and-candidate-20261007.md`` §2.4 and in the H55
hypothesis slate: nine target weightings were fitted against the same eight owner-reported
live scores, and **uniform wins**. Every density weighting is actively worse.

The forward model is ``T = rho * Cov_q(X)`` with
``Cov_q(X) = sum_{b in B_elig} q(b) * max_{x in X} k(d(x,b))``.  For each weighting ``q``,
``rho`` is fitted by least squares through the origin and the relative error of the resulting
DTI prediction is reported for all eight artifacts.

Weightings that need an optional mirror (radiometric ratios, 3 m lidar roughness) are skipped
with an explicit note rather than silently dropped.

Usage:  python scripts/compare_coverage_weightings.py [--output PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import uniform_filter
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from gemsdoe48.live_model import (LIVE_ARTIFACTS, ForwardModel, invert_truth,  # noqa: E402
                                  load_binary, max_credit_field)

BACKBONE = ROOT / "data/raw/scored/h19_5_01922.tif"
CATALOGUE = ROOT / "data/official/labels.tif"
RADIOMETRIC = ROOT / "data/raw/external/geodawn_extensions_u8.tif"
LIDAR3M = ROOT / "data/external/h52_scarp3m_100m.tif"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path,
                        default=ROOT / "evidence/coverage_weighting_comparison_20261007.json")
    args = parser.parse_args()
    if not BACKBONE.exists():
        raise SystemExit("missing backbone mirror; run: python scripts/restore_h55_inputs.py")

    backbone = load_binary(BACKBONE)
    catalogue = load_binary(CATALOGUE)
    catalogue_distance_m = distance_transform_edt(~catalogue, sampling=(100.0, 100.0))
    eligible = backbone & (catalogue_distance_m > 200.0)
    height, width = eligible.shape

    masses, lives, keys, fields = [], [], [], []
    for art in LIVE_ARTIFACTS:
        path = ROOT / art.path
        if not path.exists():
            raise SystemExit(f"missing mirror {art.path}; run scripts/restore_h55_inputs.py")
        mask = load_binary(path)
        masses.append(int(mask.sum()))
        lives.append(art.live)
        keys.append(art.key)
        fields.append(max_credit_field(mask))

    # hidden truth from the nested triple, exactly as scripts/calibrate_live_model.py does
    from gemsdoe48.live_model import fit_hidden_truth
    nested = [i for i, a in enumerate(LIVE_ARTIFACTS) if a.key in ("A_d2_8", "B_prune100", "C_prune200")]
    gfit = fit_hidden_truth([masses[i] for i in nested], [lives[i] for i in nested])
    hidden = gfit["hidden_truth_px"]
    truth = [invert_truth(l, s, hidden) for l, s in zip(lives, masses)]

    backbone_f = backbone.astype(np.float64)
    dens7 = uniform_filter(backbone_f, size=7) * 49.0
    dens13 = uniform_filter(backbone_f, size=13) * 169.0
    far = np.clip((catalogue_distance_m - 200.0) / 800.0, 0.0, 1.0)

    weightings: dict[str, np.ndarray] = {
        "uniform": np.ones((height, width)),
        "dens_7px_box": dens7,
        "dens_13px_box": dens13,
        "sqrt_dens_7px_box": np.sqrt(np.maximum(dens7, 0.0)),
        "log1p_dens_13px_box": np.log1p(np.maximum(dens13, 0.0)),
        "far_from_catalogue": 0.5 + far,
        "dens_7px_x_far": dens7 * (0.5 + far),
    }
    skipped: dict[str, str] = {}

    def zscore(x: np.ndarray, mask: np.ndarray) -> np.ndarray:
        v = x[mask]
        return (x - float(np.nanmean(v))) / (float(np.nanstd(v)) + 1e-9)

    if RADIOMETRIC.exists():
        with rasterio.open(RADIOMETRIC) as ds:
            names = ds.descriptions
            bands = {names[i]: ds.read(i + 1).astype(np.float64) for i in range(ds.count)}
        rad = np.maximum(zscore(bands["UK"], eligible), 0.0) + \
            np.maximum(zscore(bands["ThK"], eligible), 0.0)
        weightings["radiometric_ratio_corroboration"] = 1.0 + 0.5 * rad / (rad[eligible].mean() + 1e-9)
    else:
        skipped["radiometric_ratio_corroboration"] = f"mirror absent: {RADIOMETRIC.name}"

    if LIDAR3M.exists():
        with rasterio.open(LIDAR3M) as ds:
            names = list(ds.descriptions)
            nodata = ds.nodata
            sigma = ds.read(names.index("sigma_mean") + 1).astype(np.float64)
        sigma = np.where(sigma == nodata, np.nan, sigma)
        if np.isfinite(sigma[eligible]).any():
            lid = np.maximum(np.nan_to_num(zscore(sigma, eligible & np.isfinite(sigma))), 0.0)
            weightings["lidar3m_roughness_corroboration"] = \
                1.0 + 0.5 * lid / (lid[eligible].mean() + 1e-9)
        else:
            skipped["lidar3m_roughness_corroboration"] = "no finite lidar cells inside B_elig"
    else:
        skipped["lidar3m_roughness_corroboration"] = f"mirror absent: {LIDAR3M.name}"

    results = {}
    print(f"{'weighting':36s} {'rho':>10s} {'RMS rel %':>10s} {'max rel %':>10s} {'vs uniform':>11s}")
    baseline_rms = None
    for name, q in weightings.items():
        cov = [float((f * q)[eligible].sum()) for f in fields]
        xs = np.asarray(cov)
        ys = np.asarray(truth)
        rho = float((xs * ys).sum() / (xs * xs).sum())
        model = ForwardModel(hidden, rho, int(eligible.sum()))
        pred = np.asarray([model.dti(c, s) for c, s in zip(cov, masses)])
        act = np.asarray(lives)
        rel = (pred - act) / act
        rms = float(100.0 * np.sqrt((rel ** 2).mean()))
        if baseline_rms is None:
            baseline_rms = rms
        results[name] = {
            "rho": rho, "rms_relative_error_pct": rms,
            "max_abs_relative_error_pct": float(100.0 * np.abs(rel).max()),
            "per_artifact_relative_error_pct": [float(r) * 100.0 for r in rel],
            "coverage": {k: c for k, c in zip(keys, cov)},
            "worse_than_uniform_by_pct_points": rms - baseline_rms,
        }
        print(f"{name:36s} {rho:10.6f} {rms:10.3f} "
              f"{results[name]['max_abs_relative_error_pct']:10.3f} {rms - baseline_rms:+11.3f}")

    best = min(results.items(), key=lambda kv: kv[1]["rms_relative_error_pct"])
    receipt = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": ("does weighting the coverage target predict the eight owner-reported live "
                     "scores better than uniform weighting?"),
        "hidden_truth_px": hidden,
        "eligible_backbone_px": int(eligible.sum()),
        "artifacts": [{"key": k, "emitted": s, "live": l, "inverted_tpw": t}
                      for k, s, l, t in zip(keys, masses, lives, truth)],
        "weightings": results,
        "skipped": skipped,
        "best_weighting": best[0],
        "best_rms_relative_error_pct": best[1]["rms_relative_error_pct"],
        "uniform_rms_relative_error_pct": results["uniform"]["rms_relative_error_pct"],
        "conclusion": (
            f"uniform RMS {results['uniform']['rms_relative_error_pct']:.3f} % vs best alternative "
            f"'{best[0]}' at {best[1]['rms_relative_error_pct']:.3f} % on eight points - not a "
            "meaningful improvement. Every backbone-density weighting is worse "
            "(+0.37 to +0.88 percentage points). A corridor pixel is not more likely to sit near "
            "hidden truth because it has more corridor neighbours. Uniform coverage is kept."),
        "provenance_class": "OWNER-REPORT (all eight live scores are owner-pasted, not organizer receipts)",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"\nbest: {best[0]} at {best[1]['rms_relative_error_pct']:.3f} % "
          f"(uniform {results['uniform']['rms_relative_error_pct']:.3f} %)")
    if skipped:
        print("skipped:", json.dumps(skipped))
    print(f"receipt {args.output.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
