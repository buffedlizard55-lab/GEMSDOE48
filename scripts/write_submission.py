"""Write the H48-1 submission GeoTIFF + diagnostic layers, re-read every byte, audit, receipt.

Primary variant is V1 (best dotted b2 x best tip h32-1), fixed by the task statement before
any instrument reading.  Encoding = all-finite float32, 0 outside footprint, no nodata tag
(the encoding of the live-scored 0.2778 file; immune to the portal's
"Predicted values must be in range [0, 1]" error).
"""
import sys, json, pathlib, hashlib, zipfile, glob
ROOT = pathlib.Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / "src"))
import numpy as np, rasterio
from scipy.stats import pearsonr, spearmanr
from gems48.data import grid, binary, RAW
from gems48 import ds

VARIANT = "V1_b2+h32tip"
DATE = "20261006"
G = grid(); ev = ~G["mask"]; fp = G["footprint"]
z = np.load(ROOT / f"data/cache/ds_{VARIANT}.npz")
sel, bel, K, u, yu = z["sel"], z["bel"], z["K"], z["u"], z["yu"]

sub = np.where(fp, sel.astype(np.float32), np.float32(0.0)).astype(np.float32)
digest = hashlib.sha256(sub.tobytes()).hexdigest()[:8]
NAME = f"gemsdoe48-h48-1-ds-fusion-b2xh32tip-{DATE}-{digest}-zeros"
OUT = ROOT / "docs/downloads"; DIAG = OUT / "diagnostics"; OUT.mkdir(parents=True, exist_ok=True); DIAG.mkdir(exist_ok=True)

with rasterio.open(RAW / "sample_submission.tif") as s:
    prof = s.profile.copy()
# identical TIFF layout to the live-scored 0.2778 file: tiled 256x256, DEFLATE, float predictor 3
prof.update(dtype="float32", count=1, nodata=None, compress="deflate", predictor=3, tiled=True,
            blockxsize=256, blockysize=256, interleave="band")

def write(path, arr, desc):
    with rasterio.open(path, "w", **prof) as d:
        d.write(arr.astype(np.float32), 1); d.set_band_description(1, desc)

tif = OUT / f"{NAME}.tif"
write(tif, sub, "H48-1 Dempster-Shafer fused fault dots (1=emit)")
with zipfile.ZipFile(OUT / f"{NAME}.zip", "w", zipfile.ZIP_DEFLATED) as zf:
    zf.write(tif, tif.name)

diag = {"belief_dempster_mF_norm01": np.where(fp, bel, 0),
        "conflict_K": np.where(fp, K, 0),
        "unassigned_dempster_mTheta": np.where(fp, u, 0),
        "unassigned_yager_mTheta_incl_conflict": np.where(fp, yu, 0)}
for k, a in diag.items():
    a = np.clip(np.nan_to_num(a, nan=0.0), 0, 1)
    write(DIAG / f"gemsdoe48-h48-1-{k}.tif", a, k)

# ------------------------------------------------------------------ re-read audit
with rasterio.open(tif) as s:
    a = s.read(1); p = s.profile
with rasterio.open(RAW / "sample_submission.tif") as s:
    ref = s.profile
checks = {
    "single_band": p["count"] == 1, "dtype_float32": p["dtype"] == "float32",
    "shape_3730x3292": (p["height"], p["width"]) == (3730, 3292),
    "crs_epsg_32611": p["crs"].to_epsg() == 32611,
    "transform_equals_sample": tuple(p["transform"])[:6] == tuple(ref["transform"])[:6],
    "all_finite": bool(np.isfinite(a).all()), "min_ge_0": float(a.min()) >= 0.0, "max_le_1": float(a.max()) <= 1.0,
    "zero_outside_footprint": bool((a[~fp] == 0).all()),
    "zero_on_catalogue": int((a[G["catalogue"]] > 0).sum()) == 0,
    "zero_within_200m_of_catalogue": int((a[G["dcat"] <= 2] > 0).sum()) == 0,
    "bytes_equal_in_memory": bool(np.array_equal(a, sub)),
    "layout_matches_scored_02778_file": (p.get("tiled"), p.get("blockxsize"), p.get("compress")) == (True, 256, "deflate"),
}
pos = a > 0
# ------------------------------------------------------------------ uniqueness audit
known = sorted(set(glob.glob(str(ROOT.parent / "ref/*/docs/downloads/**/*.tif"), recursive=True)
                   + glob.glob(str(ROOT.parent / "ref/*/archive/**/*.tif"), recursive=True)
                   + glob.glob(str(RAW / "scored/*.tif"))))
uniq = []
for f in known:
    q = np.nan_to_num(rasterio.open(f).read(1), nan=0.0)
    if q.shape != a.shape: continue
    qp = q > 0
    uniq.append(dict(file=pathlib.Path(f).name, identical_support=bool(np.array_equal(qp & fp, pos)),
                     jaccard=round(float((qp & pos).sum() / max((qp | pos).sum(), 1)), 5)))
uniq.sort(key=lambda r: -r["jaccard"])
# ------------------------------------------------------------------ not-an-average audit
b2 = binary(RAW / "scored/b2_02778.tif") > 0
h32 = binary(RAW / "scored/h32tip_02649.tif") > 0
s1 = ds.bpa(b2 & ev, 1.0, 0.0)[3]; s2 = ds.bpa(h32 & ev, 1.0, 0.0)[3]
mean = 0.5 * (s1 + s2)
supp = ((s1 > 0) | (s2 > 0)) & ev
dis = supp & (np.abs(s1 - s2) >= 1 / 3)
avg = {"region_support_px": int(supp.sum()), "region_disagree_px": int(dis.sum()),
       "pearson_all_support": float(pearsonr(bel[supp], mean[supp]).statistic),
       "pearson_disagreement_region": float(pearsonr(bel[dis], mean[dis]).statistic),
       "spearman_disagreement_region": float(spearmanr(bel[dis], mean[dis]).statistic),
       "mean_conflict_K_disagreement": float(K[dis].mean()), "mean_conflict_K_agreement": float(K[supp & ~dis].mean()),
       "flank_disagreement_px": int((dis & (G["dcat"] <= 2)).sum())}
# within the disagreement region: which source does the fused belief side with?
only1 = dis & (s1 > s2); only2 = dis & (s2 > s1)
avg["mean_bel_where_dotted_stronger"] = float(bel[only1].mean())
avg["mean_bel_where_tip_stronger"] = float(bel[only2].mean())
avg["mean_naive_where_dotted_stronger"] = float(mean[only1].mean())
avg["mean_naive_where_tip_stronger"] = float(mean[only2].mean())

sha = hashlib.sha256(tif.read_bytes()).hexdigest()
receipt = dict(name=NAME, file=tif.name, zip=f"{NAME}.zip", sha256=sha, bytes=tif.stat().st_size,
               emitted_px=int(pos.sum()), in_footprint_px=int(fp.sum()), checks=checks,
               all_checks_passed=all(checks.values()), uniqueness_top5=uniq[:5], n_files_compared=len(uniq),
               any_identical=any(r["identical_support"] for r in uniq), not_an_average=avg,
               portal_note=f"GEMSDOE48 H48-1 Dempster-Shafer fusion b2(0.2778) x h32-1 tip(0.2649); pignistic>0.5, NMS 2.8px; {int(pos.sum())} dots, 0 within 200m of catalogue",
               portal_unique_name="GEMSDOE48-H48-1-DS-fusion")
json.dump(receipt, open(OUT / f"receipt-{NAME}.json", "w"), indent=1)
print(json.dumps(receipt, indent=1))
