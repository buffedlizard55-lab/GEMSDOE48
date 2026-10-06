"""H48-1: Dempster-Shafer fusion of the dotted family (b2, live 0.2778) and the tip family.

Writes data/cache/ds_<variant>.npz and evidence/ds_variants.json.  Deterministic.
"""
import sys, json, pathlib, pickle
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np
from scipy import ndimage as ndi
from scipy.stats import pearsonr, spearmanr
from gems48.data import grid, binary, sgmc_offcat, quadrant_folds, RAW
from gems48 import ds, lsi
from gems48.metric import components

LIVE = {r["id"]: r for r in json.load(open(ROOT / "registry/live_scores.json"))["rasters"]}
G = grid(); ev = ~G["mask"]; flank = G["dcat"] <= 2.0
bb = binary(RAW / "scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") > 0
onbb = ndi.distance_transform_edt(~bb) <= 1.0
SRC = {"b2": "h33-2-b2", "h32tip": "h32-1-prethin-tip", "h33d": "h33d-tip-stepover"}
D = {k: (binary(RAW / "scored" / LIVE[v]["file"]) > 0) & ev for k, v in SRC.items()}

# --- frozen hyper-parameters (chosen a priori, documented in docs/method.md) ---
A_OFF, A_ON = 0.2, 0.5          # absence informativeness off / on the shared H19-5 backbone
R_TOP = 0.9                     # reliability of the best live source
NMS_R = 2.8                     # families' own minimum spacing is sqrt(8)=2.83 px
def reliability(k): return R_TOP * LIVE[SRC[k]]["live"] / LIVE["h33-2-b2"]["live"]

def absence(k):
    a = np.where(onbb, A_ON, A_OFF).astype(np.float32)
    if k == "b2":
        a[flank] = 1.0           # explicit, live-validated rejection (0.2708 -> 0.2778)
    return a

def fuse(keys, rule="dempster"):
    ms = []
    for k in keys:
        f, n, u, s = ds.bpa(D[k], reliability(k), absence(k)); ms.append((f, n, u))
    comb = ds.dempster if rule == "dempster" else ds.yager
    f, n, u, K = comb(ms[0], ms[1])
    Kall = K.copy()
    for m in ms[2:]:
        f, n, u, K2 = comb((f, n, u), m); Kall = np.maximum(Kall, K2)
    return f, n, u, Kall, ms

def emit(f, u, keys):
    betp = ds.pignistic(f, u)
    cand = np.zeros_like(ev)
    for k in keys: cand |= D[k]
    cand &= ev & ~flank & (betp > 0.5)
    return ds.nms_select(betp, cand, NMS_R), betp

# ---------------------------------------------------------------- instruments
geom = sgmc_offcat(G); folds = quadrant_folds(G)
binsA, nb = lsi.make_bins(G, bb)
N = np.bincount(binsA[binsA >= 0], minlength=nb).astype(float)
q = np.array(list(json.load(open(ROOT / "evidence/lsi_validation.json"))["q_full"].values()))
def instruments(p):
    out = {"S": int(p.sum()), "lsi_pred": lsi.predict(q, lsi.features(p.astype(float), G, binsA, nb, geom), N)}
    out["sgmc_folds"] = [components(p.astype(float), geom & fm, G["mask"] | ~fm)["DTI"] for fm in folds]
    out["sgmc_mean"] = float(np.mean(out["sgmc_folds"]))
    return out

if __name__ == "__main__":
    res = {"frozen": dict(A_OFF=A_OFF, A_ON=A_ON, R_TOP=R_TOP, NMS_R=NMS_R,
                          reliabilities={k: reliability(k) for k in SRC})}
    base = instruments(D["b2"]); res["b2_reference"] = base
    print("b2", base)
    variants = {"V1_b2+h32tip": ["b2", "h32tip"], "V2_b2+h33d": ["b2", "h33d"],
                "V3_b2+h32tip+h33d": ["b2", "h32tip", "h33d"]}
    (ROOT / "data/cache").mkdir(parents=True, exist_ok=True)
    for name, keys in variants.items():
        f, n, u, K, ms = fuse(keys)
        sel, betp = emit(f, u, keys)
        # naive-mean comparison on the support of either source
        s_mean = np.mean([ds.bpa(D[k], 1.0, 0.0)[3] for k in keys], axis=0)
        sup = (s_mean > 0) & ev
        bel = f / f[ev].max()
        r_p = pearsonr(bel[sup], s_mean[sup]).statistic
        r_s = spearmanr(bel[sup][::7], s_mean[sup][::7]).statistic
        # naive-mean emission at equal count, same candidates & NMS
        cand = np.zeros_like(ev)
        for k in keys: cand |= D[k]
        cand &= ev & ~flank
        order = np.sort(s_mean[cand])[::-1]
        naive = ds.nms_select(s_mean + 1e-6 * betp, cand & (s_mean >= order[min(sel.sum(), order.size) - 1]), NMS_R)
        jac = float((sel & naive).sum() / max((sel | naive).sum(), 1))
        yf, yn, yu, _ = ds.yager(ms[0], ms[1])
        out = instruments(sel)
        out.update(keys=keys, added_vs_b2=int((sel & ~D["b2"]).sum()), removed_vs_b2=int((D["b2"] & ~sel).sum()),
                   pearson_bel_vs_naive_mean=float(r_p), spearman_bel_vs_naive_mean=float(r_s),
                   jaccard_emission_vs_naive_mean=jac, naive_S=int(naive.sum()),
                   conflict_px_gt_0_3=int(((K > 0.3) & ev).sum()),
                   flank_dots=int((sel & flank).sum()), masked_dots=int((sel & G["mask"]).sum()))
        res[name] = out
        print(name, {k: v for k, v in out.items() if k != "keys"})
        np.savez_compressed(ROOT / f"data/cache/ds_{name}.npz", sel=sel, bel=bel.astype(np.float32),
                            K=K, u=u, yu=yu.astype(np.float32), betp=betp.astype(np.float32))
    json.dump(res, open(ROOT / "evidence/ds_variants.json", "w"), indent=1)
