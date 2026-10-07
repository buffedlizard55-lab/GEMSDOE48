#!/usr/bin/env python3
"""GEMSDOE48 H56 research battery — band screen + candidate-field validation.

Purpose
-------
1. Per-band screen over ALL 19 official GeoDAWN bands (restored byte-identical
   this session, SHA-256 4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5):
   lift of the incumbent C dots over the >200 m catalogue moat, plus a
   rank-based AUC robust to signed bands.
2. H55-B strain-rate localisation ridge field (previous session's Priority-3
   next step), gated exactly as its frozen slate says: structure-tensor
   coherence above the 95th percentile; the conjunctive p90-ridgeness variant
   is reported alongside.
3. New H56-A DEMGLOW candidate (hydrothermal demagnetisation lows x magnetic
   gradient ridges) with a pre-registered two-tier sensitivity ladder
   (z in {-1.5, -2.0} x HG in {p75, p90}); the battery evaluates the primary
   rung z<=-1.5 & HG>=p75 plus same-mass controls.
4. Light statistics for H56-D (conduit stepping-stone anchors) and H56-E
   (cover / basement depth).

Everything here is a PROXY measurement. The repository's measured position:
the SGMC off-catalogue proxy is NOT a model of the hidden truth, the
catalogue proxy can be anti-monotone, and the live-calibrated forward model
is the only instrument fitted to live scores (in-family RMS 1.76 %,
out-of-family transfer error -38 %). Results are labelled [PROXY] or
[PROJECTION], never scores.

Staged to survive the 3 GB sandbox: each stage frees its arrays and writes a
checkpoint JSON before the next stage allocates.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems48.metric import dti_result, weighted_tp_credit  # noqa: E402
from gems48.emission import poisson_sample  # noqa: E402

FEATURES = ROOT / "data/raw/training_features.tif"
ALPHA, BETA, R = 0.2, 0.8, 3.0
RHO = 0.06801513031394778
G_PX = 14027.470000000054
SPACING = float(np.sqrt(8.0))
SEED = 20261007
EV = ROOT / "evidence"


def read_raw(path: Path) -> np.ndarray:
    with rasterio.open(path) as s:
        return s.read(1).astype(np.float64)


def read_feature_band(i: int) -> np.ndarray:  # 1-based band index
    with rasterio.open(FEATURES) as s:
        b = s.read(i).astype(np.float64)
        nodata = s.nodata
    if nodata is not None:
        b[b <= nodata + 1] = np.nan  # reference-solution convention: X[X < -1e38] = NaN
    return b


def load_grid():
    lab = read_raw(ROOT / "data/raw/labels_catalogue.tif").astype(np.int8)
    footprint = lab != -1
    catalogue = lab == 1
    dcat = ndi.distance_transform_edt(~catalogue)
    return footprint, catalogue, dcat


def auc_lift(dot_vals: np.ndarray, bg_vals: np.ndarray) -> float:
    d = dot_vals[np.isfinite(dot_vals)]
    b = bg_vals[np.isfinite(bg_vals)]
    if d.size == 0 or b.size == 0:
        return float("nan")
    rng = np.random.default_rng(SEED)
    if b.size > 200000:
        b = b[rng.choice(b.size, 200000, replace=False)]
    comb = np.concatenate([d, b])
    order = np.argsort(comb, kind="stable")
    sorted_comb = comb[order]
    _, inv, cnt = np.unique(sorted_comb, return_inverse=True, return_counts=True)
    starts = np.concatenate([[0], np.cumsum(cnt)[:-1]])
    avg_rank = starts + (cnt - 1) / 2.0
    ranks = np.empty_like(avg_rank[inv])
    ranks[order] = avg_rank[inv]
    rsum = ranks[: d.size].sum()
    return float((rsum - d.size * (d.size - 1) / 2.0) / (d.size * b.size))


def stage_screen(footprint, catalogue, dcat, dots_c) -> dict:
    out_path = EV / "h56_band_screen_20261007.json"
    if out_path.exists():
        print("[screen] cached")
        return json.loads(out_path.read_text())
    moat = footprint & (dcat > 2.0)
    with rasterio.open(FEATURES) as s:
        NB = s.count
        nodata = s.nodata
        desc = [s.tags(i + 1).get("description", "") for i in range(NB)]
    rows = []
    for i in range(1, NB + 1):
        with rasterio.open(FEATURES) as s:
            b = s.read(i).astype(np.float64)
        if nodata is not None:
            b[b <= nodata + 1] = np.nan
        valid = np.isfinite(b)
        dv = b[dots_c & valid]
        bv = b[moat & valid & ~dots_c]
        mb = float(np.nanmean(bv)) if bv.size else float("nan")
        md = float(np.nanmean(dv)) if dv.size else float("nan")
        lift = md / mb if abs(mb) > 1e-12 else float("nan")
        p99 = np.nanpercentile(bv, 99) if bv.size else np.nan
        rows.append({"band": i, "description": desc[i - 1],
                     "mean_at_C_dots": md, "mean_moat_background": mb,
                     "lift_mean_ratio": lift,
                     "frac_C_dots_above_bg_p99": float((dv > p99).mean()) if dv.size else None,
                     "auc_dot_vs_background": auc_lift(dv, bv)})
        print(f"[screen] band {i:2d} {desc[i-1][:52]:52s} lift={lift:.3f} "
              f"auc={rows[-1]['auc_dot_vs_background']:.3f}", flush=True)
        del b, dv, bv
    res = {"generated_utc": datetime.now(timezone.utc).isoformat(),
           "moat_definition": "footprint & d(catalogue) > 200 m",
           "features_sha256": "4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5 (restored, manifest-pinned)",
           "bands": rows}
    out_path.write_text(json.dumps(res, indent=1))
    return res


def main() -> int:
    now = datetime.now(timezone.utc).isoformat()
    footprint, catalogue, dcat = load_grid()
    moat = footprint & (dcat > 2.0)
    offcat = dcat > 2.0
    dots_c = (np.nan_to_num(read_raw(ROOT / "data/families/dotted_b2_prune_02778.tif"), nan=0.0) > 0) & footprint
    bb = (np.nan_to_num(read_raw(ROOT / "data/raw/scored/h19_5_01922.tif"), nan=0.0) > 0) & footprint
    sgmc = read_raw(ROOT / "data/official/derived_sgmc_faults_100m.tif")
    sgmc_truth = (sgmc > 0) & footprint & (dcat > 3.0)
    del sgmc

    out = {"generated_utc": now}
    out["screen"] = stage_screen(footprint, catalogue, dcat, dots_c)

    # ------------------------------------------------ Part 1: H55-B strain ridge
    b4 = read_feature_band(4)   # geodetic second invariant
    b7 = read_feature_band(7)   # geodetic shear rate
    ridge_max = np.zeros(footprint.shape)
    for f in (np.log1p(np.abs(b4)) * np.sign(b4), np.abs(b7)):
        fs = np.where(np.isfinite(f), f, 0.0)
        for sigma in (3.0, 6.0, 9.0):
            Lxx = sigma**2 * ndi.gaussian_filter(fs, sigma, order=[0, 2])
            Lyy = sigma**2 * ndi.gaussian_filter(fs, sigma, order=[2, 0])
            Lxy = sigma**2 * ndi.gaussian_filter(fs, sigma, order=[1, 1])
            tmp = np.sqrt(((Lxx - Lyy) / 2.0) ** 2 + Lxy**2)
            lam1 = (Lxx + Lyy) / 2.0 - tmp
            lam2 = (Lxx + Lyy) / 2.0 + tmp
            rid = np.maximum(-lam1, 0.0) * np.where(
                np.abs(lam2) > 1e-12,
                1.0 - np.abs(lam1) / np.maximum(np.abs(lam2), 1e-12), 0.0)
            ridge_max = np.maximum(ridge_max, rid)
            del Lxx, Lyy, Lxy, tmp, lam1, lam2, rid
    g = np.where(np.isfinite(b4), np.abs(b4), 0.0) + np.where(np.isfinite(b7), np.abs(b7), 0.0)
    gx = ndi.gaussian_filter(g, 3.0, order=[0, 1])
    gy = ndi.gaussian_filter(g, 3.0, order=[1, 0])
    Jxx = ndi.gaussian_filter(gx * gx, 3.0)
    Jyy = ndi.gaussian_filter(gy * gy, 3.0)
    Jxy = ndi.gaussian_filter(gx * gy, 3.0)
    tmp = np.sqrt(((Jxx - Jyy) / 2.0) ** 2 + Jxy**2)
    mu1 = (Jxx + Jyy) / 2.0 + tmp
    mu2 = (Jxx + Jyy) / 2.0 - tmp
    with np.errstate(invalid="ignore", divide="ignore"):
        coh = np.where((mu1 + mu2) > 1e-12, ((mu1 - mu2) / (mu1 + mu2)) ** 2, 0.0)
    coh = np.nan_to_num(coh)
    p95 = float(np.nanpercentile(coh[footprint], 95))
    ridge_slate = footprint & (coh > p95)                       # frozen slate gate
    ridge_strict = ridge_slate & (ridge_max >= float(np.nanpercentile(ridge_max[footprint], 90)))
    out["h55b_strain_ridge"] = {
        "spec": "slate gate: structure-tensor coherence > p95 on |b4|+|b7|; ridgeness = "
                "max-over-sigma(3,6,9) Hessian line response on log|b4| and |b7|",
        "coherence_p95": p95,
        "slate_field_px": int(ridge_slate.sum()),
        "strict_field_px": int(ridge_strict.sum()),
        "overlap_with_C_dots_slate": int((ridge_slate & dots_c).sum()),
        "C_dots_in_slate_field_frac": float((ridge_slate & dots_c).sum() / max(1, int(dots_c.sum()))),
    }
    print("[h55b]", out["h55b_strain_ridge"], flush=True)
    del b4, b7, g, gx, gy, Jxx, Jyy, Jxy, mu1, mu2, tmp

    # ------------------------------------------------ Part 2: H56-A DEMGLOW
    tmi = read_feature_band(14)  # total magnetic intensity
    hg = read_feature_band(3)    # TMI horizontal gradient
    tmi_v = np.isfinite(tmi) & footprint
    denom = np.maximum(ndi.uniform_filter(tmi_v.astype(float), 9), 1e-9)
    mu9 = ndi.uniform_filter(np.where(tmi_v, tmi, 0.0), 9) / denom
    sq = ndi.uniform_filter(np.where(tmi_v, tmi**2, 0.0), 9) / denom
    sd9 = np.sqrt(np.maximum(sq - mu9**2, 0.0))
    z14 = np.where(sd9 > 1e-9, (tmi - mu9) / sd9, 0.0)
    del mu9, sq, sd9, denom
    hg_fin = footprint & np.isfinite(hg)
    hg_p75 = float(np.nanpercentile(hg[hg_fin], 75))
    hg_p90 = float(np.nanpercentile(hg[hg_fin], 90))
    ladder = {}
    for zt in (-1.5, -2.0):
        for ht, hname in ((hg_p75, "HG>=p75"), (hg_p90, "HG>=p90")):
            cell = footprint & (z14 <= zt) & (hg >= ht) & np.isfinite(z14)
            ladder[f"z<={zt} & {hname}"] = {"px": int(cell.sum()),
                                             "offcat_px": int((cell & offcat).sum()),
                                             "C_dots_inside": int((cell & dots_c).sum())}
    primary = footprint & (z14 <= -1.5) & (hg >= hg_p75) & np.isfinite(z14)
    out["h56a_demglow"] = {
        "spec": "band-14 TMI local z-score (9x9 window) below tier AND band-3 HG above tier; "
                "primary rung z<=-1.5 & HG>=p75; emission Poisson-spaced 2.83 px, offcat>200 m",
        "hg_p75": hg_p75, "hg_p90": hg_p90,
        "ladder": ladder,
        "primary_px": int(primary.sum()),
        "primary_offcat_px": int((primary & offcat).sum()),
        "C_dots_in_primary": int((primary & dots_c).sum()),
    }
    print("[h56a]", json.dumps(out["h56a_demglow"]["ladder"], indent=1), flush=True)

    allowed = primary & offcat
    score = np.where(allowed, hg, -np.inf)
    dem_dots = poisson_sample(score, SPACING, int(allowed.sum()), allowed)
    out["h56a_demglow"]["emitted_dots"] = int(dem_dots.sum())
    n_dem = int(dem_dots.sum())

    rng = np.random.default_rng(SEED)
    rnd = np.zeros_like(footprint)
    idx = np.flatnonzero((offcat & footprint).ravel())
    pick = rng.choice(idx, size=min(max(n_dem, 1), idx.size), replace=False)
    rnd.ravel()[pick] = True
    rid_dots = poisson_sample(np.where(hg_fin & (hg >= hg_p75) & offcat, hg, -np.inf),
                              SPACING, n_dem, hg_fin & (hg >= hg_p75) & offcat)
    low_dots = poisson_sample(np.where(footprint & (z14 <= -1.5), -z14, -np.inf),
                              SPACING, n_dem, footprint & (z14 <= -1.5))
    del tmi, hg, z14, primary

    # ------------------------------------------------ battery
    ys, xs = np.nonzero(footprint)
    ym, xm = int(np.median(ys)), int(np.median(xs))
    H, W = footprint.shape
    yy, xx = np.mgrid[0:H, 0:W]
    qmask = (yy >= ym).astype(np.int8) * 2 + (xx >= xm).astype(np.int8)
    folds = [(qmask == i) & footprint for i in range(4)]
    del yy, xx
    belig = bb & offcat & footprint

    def battery(mask):
        p = (mask & footprint).astype(np.float64)
        res = {"positive_cells": int(p.sum())}
        credit, _ = weighted_tp_credit(p, belig, R)
        S = float(p.sum())
        res["cov_elig"] = float(credit.sum())
        res["live_projection_standalone"] = RHO * res["cov_elig"] / (0.2 * S + 0.8 * G_PX) if S else 0.0
        del credit
        p2 = np.maximum(dots_c.astype(np.float64), p)
        credit2, _ = weighted_tp_credit(p2, belig, R)
        S2 = float(p2.sum())
        res["live_projection_C_plus_field"] = RHO * float(credit2.sum()) / (0.2 * S2 + 0.8 * G_PX)
        del credit2, p2
        res["added_vs_C"] = int(((p > 0) & ~dots_c).sum())
        for tname, truth in [("catalogue", catalogue), ("sgmc_offcat", sgmc_truth)]:
            dts = []
            for core in folds:
                dom = core | (ndi.distance_transform_edt(~core) <= R)
                dom &= footprint
                r0, r1 = np.nonzero(dom)[0].min(), np.nonzero(dom)[0].max() + 1
                c0, c1 = np.nonzero(dom)[1].min(), np.nonzero(dom)[1].max() + 1
                sl = (slice(r0, r1), slice(c0, c1))
                dts.append(dti_result(p[sl] * dom[sl], truth[sl] & core[sl], ALPHA, BETA, R).dti)
            res[f"holdout_mean_{tname}"] = float(np.mean(dts))
        return res

    bat = {}
    bat["dotted_C_reference"] = battery(dots_c)
    bat["h55b_strain_ridge_dots"] = battery(poisson_sample(
        np.where(ridge_slate & offcat, coh, -np.inf), SPACING,
        int((ridge_slate & offcat).sum()), ridge_slate & offcat))
    bat["h56a_demglow"] = battery(dem_dots)
    bat["control_random_same_mass"] = battery(rnd)
    bat["control_ridgeHG_only"] = battery(rid_dots)
    bat["control_low_only"] = battery(low_dots)
    out["battery"] = bat
    for k, v in bat.items():
        print(f"[battery] {k:28s} n={v['positive_cells']:6d} "
              f"proj={v['live_projection_standalone']:.4f} projC+={v['live_projection_C_plus_field']:.4f} "
              f"cat={v['holdout_mean_catalogue']:.4f} sgmc={v['holdout_mean_sgmc_offcat']:.4f}", flush=True)
    del ridge_slate, ridge_strict, ridge_max, coh

    # ------------------------------------------------ Part 3/4 light stats
    try:
        from gemsdoe48 import conduit as conduit_mod
        sites = conduit_mod.read_sites(ROOT / "data/raw/external/gdr_wellspring_in_footprint.csv")
        tier, _ = conduit_mod.site_arrays(sites, footprint.shape, min_tier=2)
        anchors = (tier >= 2) & footprint & offcat
        n_anchor = int(anchors.sum())
        hg3 = read_feature_band(3)
        out["h56d_step_trace"] = {
            "anchors_tier_ge2_offcat": n_anchor,
            "mean_band3_HG_at_anchors": float(np.nanmean(hg3[anchors & np.isfinite(hg3)])) if n_anchor else None,
            "mean_band3_HG_moat_background": float(np.nanmean(hg3[moat & np.isfinite(hg3)])),
            "note": "anchor statistics only; least-cost trace propagation deferred to a build phase",
        }
        del hg3
    except Exception as exc:
        out["h56d_step_trace"] = {"error": str(exc)}
    b15 = read_feature_band(15)
    out["h56e_cover"] = {
        "mean_basement_depth_at_C_dots": float(np.nanmean(b15[dots_c & np.isfinite(b15)])),
        "mean_basement_depth_moat": float(np.nanmean(b15[moat & np.isfinite(b15)])),
        "frac_C_dots_below_median_depth": float(
            (b15[dots_c & np.isfinite(b15)] > np.nanmedian(b15[moat & np.isfinite(b15)])).mean()),
    }
    del b15
    print("[h56d/e]", out.get("h56d_step_trace"), out["h56e_cover"], flush=True)

    (EV / "h56_research_battery_20261007.json").write_text(json.dumps(out, indent=1))
    print("[evidence] evidence/h56_research_battery_20261007.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
