"""Compare every GEMSDOE48 DS file (this PR, PR #1 on main, PR #2) on the same instruments.
Graded values handled exactly: A_b uses max-offset p*k (metric definition), S = sum p."""
import sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np, rasterio
from scipy import ndimage as ndi
from gems48.data import grid, binary, sgmc_offcat, quadrant_folds, RAW
from gems48.metric import OFFSETS, _shift, components, ALPHA, BETA
from gems48 import lsi
G = grid(); ev = ~G["mask"]; geom = sgmc_offcat(G); folds = quadrant_folds(G)
bb = binary(RAW / "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") > 0
bins, nb = lsi.make_bins(G, bb); N = np.bincount(bins[bins >= 0], minlength=nb).astype(float)
q = np.array(list(json.load(open(ROOT / "evidence/lsi_validation.json"))["q_full"].values()))
b2 = binary(RAW / "scored/b2_02778.tif") > 0
def feats(p):
    p = np.where(ev, p, 0.0)
    best = np.zeros_like(p)
    for dy, dx, k in OFFSETS: np.maximum(best, k * _shift(p, dy, dx), out=best)
    A = np.bincount(bins[ev], weights=best[ev], minlength=nb)[:nb]
    c = components(p, geom, G["mask"]); rho = c["TP"] / max(c["S"] - c["FP"], 1e-9)
    return dict(S=float(p.sum()), A=A, rho=rho)
files = {k: v for k, v in [a.split("=", 1) for a in sys.argv[1:]]}
out = {}
for name, f in files.items():
    p = np.nan_to_num(rasterio.open(f).read(1).astype(np.float64), nan=0.0)
    fe = feats(p)
    sg = [components(p, geom & fm, G["mask"] | ~fm)["DTI"] for fm in folds]
    pos = (p > 0) & ev
    out[name] = dict(px=int(pos.sum()), mass=fe["S"], values=sorted(map(float, np.unique(p[pos])))[:5],
                     lsi_pred=round(lsi.predict(q, fe, N), 5), sgmc_mean=round(float(np.mean(sg)), 5),
                     contains_all_b2=bool((b2 & ~pos).sum() == 0), extra_vs_b2=int((pos & ~b2).sum()),
                     within_200m_catalogue=int((pos & (G["dcat"] <= 2)).sum()))
    print(name, out[name])
json.dump(out, open(ROOT / "evidence/ds_file_comparison.json", "w"), indent=1)
