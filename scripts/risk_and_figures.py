"""Downside/upside bound of the 100 added dots (scale-free algebra, LSI-anchored) + site figures."""
import sys, json, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np, matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
from gems48.data import grid, binary, RAW
from gems48.metric import ALPHA, BETA
G = grid(); fp = G["footprint"]
rec = json.load(open(next((ROOT / "docs/downloads").glob("receipt-*.json"))))
z = np.load(ROOT / "data/cache/ds_V1_b2+h32tip.npz")
b2 = binary(RAW / "scored/b2_02778.tif") > 0
added = z["sel"] & ~b2; n_add = int(added.sum())
D0 = 0.2778
# Exact algebra: 1/DTI = 1 + alpha*F/T + beta*(K-T)/T  -> den = T/D0.  T is unknown; take the LSI
# estimate of T for b2 and a +/-50% band.  Worst case: every added dot is pure false positive.
lsi = json.load(open(ROOT / "evidence/lsi_validation.json"))
q = np.array(list(lsi["q_full"].values()))
from gems48 import lsi as L
from gems48.data import sgmc_offcat
from scipy import ndimage as ndi
bb = binary(RAW / "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") > 0
bins, nb = L.make_bins(G, bb); N = np.bincount(bins[bins >= 0], minlength=nb).astype(float)
f = L.features(b2.astype(float), G, bins, nb, sgmc_offcat(G))
T_lsi = float(q @ f["A"]); K_lsi = float(q @ N)
out = {"n_added": n_add, "n_removed": int((b2 & ~z["sel"]).sum()), "T_b2_lsi": T_lsi, "K_lsi": K_lsi}
for tag, T in [("T_lsi", T_lsi), ("T_lsi_x0.5", 0.5 * T_lsi), ("T_lsi_x1.5", 1.5 * T_lsi)]:
    den = T / D0
    worst = T / (den + ALPHA * n_add)
    # best case: each added dot sits on a straight 1-px truth line it alone credits:
    # 1 + 2*(2/3) + 2*(1/3) = 3.0 kernel credit, no false-positive mass
    tb = 3.0 * n_add
    best = (T + tb) / (den + tb - BETA * tb)
    out[tag] = {"worst_case_dti": round(worst, 5), "best_case_dti": round(best, 5)}
# break-even per added dot: k > alpha*DTI
out["break_even_mean_credit_per_added_dot"] = ALPHA * D0
json.dump(out, open(ROOT / "evidence/risk_bound.json", "w"), indent=1); print(json.dumps(out, indent=1))

# ---------------- figures (decimated for the site)
A = ROOT / "docs/assets"; A.mkdir(parents=True, exist_ok=True)
s = 4
def show(ax, arr, title, cmap):
    a = arr[::s, ::s].astype(float); a[~fp[::s, ::s]] = np.nan
    im = ax.imshow(a, cmap=cmap, vmin=0, vmax=1, interpolation="nearest"); ax.set_title(title, fontsize=10)
    ax.set_xticks([]); ax.set_yticks([]); plt.colorbar(im, ax=ax, fraction=0.04)
def maxpool(a):
    return ndi.maximum_filter(a.astype(np.float32), size=s)
fig, axs = plt.subplots(1, 3, figsize=(16, 6.5))
show(axs[0], maxpool(z["bel"]), "Dempster belief m(F), normalised [0,1]", "viridis")
show(axs[1], maxpool(z["K"]), "Conflict K = where the two families disagree", "magma")
show(axs[2], maxpool(z["yu"]), "Yager unassigned m(Θ) incl. conflict", "cividis")
fig.suptitle("GEMSDOE48 H48-1 — Dempster–Shafer fusion of dotted b2 (0.2778) × tip h32-1 (0.2649)  (max-pooled 400 m for display)")
plt.tight_layout(); plt.savefig(A / "fig1_ds_layers.png", dpi=110); plt.close()
# zoom on a disagreement-rich window
dens = ndi.uniform_filter(added.astype(np.float32), 61); cy, cx = np.unravel_index(int(np.argmax(dens)), dens.shape)
w = 60; sl = (slice(max(cy - w, 0), cy + w), slice(max(cx - w, 0), cx + w))
fig, axs = plt.subplots(1, 2, figsize=(13, 6.5))
axs[0].imshow(z["K"][sl], cmap="magma", vmin=0, vmax=1); axs[0].set_title("conflict K (zoom, 100 m px)")
rgb = np.zeros(z["K"][sl].shape + (3,))
cg = G["catalogue"][sl] * 0.45
rgb[..., 0] = cg; rgb[..., 1] = np.maximum(cg, b2[sl]); rgb[..., 2] = np.maximum(cg, ndi.binary_dilation(added[sl]))
h32 = binary(RAW / "scored/h32tip_02649.tif")[sl] > 0
rgb[..., 0] = np.maximum(rgb[..., 0], (h32 & ~b2[sl]) * 1.0)
axs[1].imshow(rgb); axs[1].set_title("green=b2 kept · blue=DS-added tip dots (3x3)\nred=tip dots rejected · grey=catalogue")
for a in axs: a.set_xticks([]); a.set_yticks([])
plt.tight_layout(); plt.savefig(A / "fig2_ds_zoom.png", dpi=110); plt.close()
# LSI calibration figure
rows = lsi["rows"]; pr = lsi["0.001"]["loo_pred"]
fig, ax = plt.subplots(figsize=(6.5, 6))
ax.scatter([r["live"] for r in rows], pr); ax.plot([0, .3], [0, .3], "k--", lw=.8)
for r, p in zip(rows, pr): ax.annotate(r["id"], (r["live"], p), fontsize=6)
ax.set_xlabel("owner-reported live DTI"); ax.set_ylabel("LSI leave-one-out prediction")
ax.set_title(f"LSI instrument: LOO Spearman {lsi['0.001']['loo_spearman']:.2f} (all 17), {lsi['0.001']['loo_spearman_top8']:.2f} (top 8)")
plt.tight_layout(); plt.savefig(A / "fig3_lsi_calibration.png", dpi=110); plt.close()
