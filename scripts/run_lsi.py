"""Fit + leave-one-out validate the LSI instrument. Caches features to data/cache/lsi_feats.npz"""
import sys, json, pathlib, pickle
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from scipy.stats import spearmanr
from gems48.data import grid, binary, sgmc_offcat, RAW
from gems48 import lsi
LIVE = json.load(open(ROOT / "registry/live_scores.json"))["rasters"]
G = grid(); geom = sgmc_offcat(G)
bb = binary(RAW / "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") > 0
bins, nb = lsi.make_bins(G, bb)
N = np.bincount(bins[bins >= 0], minlength=nb).astype(float)
cache = ROOT / "data/cache/lsi_feats.pkl"; cache.parent.mkdir(parents=True, exist_ok=True)
if cache.exists(): fs = pickle.load(open(cache, "rb"))
else:
    fs = [lsi.features(binary(RAW / "scored" / r["file"]), G, bins, nb, geom) for r in LIVE]
    pickle.dump(fs, open(cache, "wb"))
live = np.array([r["live"] for r in LIVE])
out = {}
for ridge in [1e-4, 1e-3, 1e-2]:
    pr = lsi.loo(fs, live, N, ridge)
    out[str(ridge)] = dict(loo_mae=float(np.abs(pr - live).mean()), loo_spearman=float(spearmanr(pr, live).statistic),
                           loo_pred=[round(float(x), 4) for x in pr])
    fam = [i for i, r in enumerate(LIVE) if r["live"] > 0.24]
    out[str(ridge)]["loo_spearman_top8"] = float(spearmanr(pr[fam], live[fam]).statistic)
    out[str(ridge)]["loo_mae_top8"] = float(np.abs(pr[fam] - live[fam]).mean())
    print(ridge, {k: v for k, v in out[str(ridge)].items() if k != "loo_pred"})
q = lsi.fit(fs, live, N, 1e-3)
for n_, qq, nn in zip(lsi.bin_names(), q, N): print(f"{n_:28s} q={qq:.5f} N={nn:.0f}")
for r, f in zip(LIVE, fs): print(f'{r["id"]:22s} live={r["live"]:.4f} fit={lsi.predict(q, f, N):.4f} rho={f["rho"]:.3f}')
out["q_full"] = dict(zip(lsi.bin_names(), map(float, q))); out["N"] = dict(zip(lsi.bin_names(), map(float, N)))
out["rows"] = [dict(id=r["id"], live=r["live"], fit=lsi.predict(q, f, N), rho=f["rho"], S=f["S"]) for r, f in zip(LIVE, fs)]
json.dump(out, open(ROOT / "evidence/lsi_validation.json", "w"), indent=1)
