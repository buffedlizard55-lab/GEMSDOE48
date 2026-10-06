"""Does a proxy truth rank the owner-reported live scores?  Writes evidence/proxy_calibration.json"""
import sys, json, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
import numpy as np
from scipy.stats import spearmanr, pearsonr
from gems48.data import grid, binary, sgmc_offcat, RAW
from gems48.metric import components
LIVE = json.load(open(pathlib.Path(__file__).resolve().parents[1] / "registry" / "live_scores.json"))
G = grid()
truth = sgmc_offcat(G)
rows = []
for r in LIVE["rasters"]:
    p = binary(RAW / "scored" / r["file"])
    c = components(p, truth, G["mask"])
    ev = p * (~G["mask"])
    rows.append(dict(id=r["id"], live=r["live"], S_eval=float(ev.sum()), proxy_dti=c["DTI"],
                     proxy_TP=c["TP"], proxy_FP=c["FP"], K=c["K"]))
    print(f'{r["id"]:28s} live={r["live"]:.4f} S={ev.sum():8.0f} proxy={c["DTI"]:.5f}')
live = [r["live"] for r in rows]; px = [r["proxy_dti"] for r in rows]
out = dict(truth="SGMC faults (derived_sgmc_faults_100m_u8) >3 px from catalogue, in footprint",
           n=len(rows), spearman=spearmanr(live, px).statistic, spearman_p=spearmanr(live, px).pvalue,
           pearson=pearsonr(live, px).statistic, rows=rows)
# within-family (same H19-5 backbone, binary, 37k-121k dots) subset
fam = [r for r in rows if r.get("id") in LIVE["family_ids"]]
out["family_spearman"] = spearmanr([r["live"] for r in fam], [r["proxy_dti"] for r in fam]).statistic
out["family_n"] = len(fam)
print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=1))
pathlib.Path("evidence").mkdir(exist_ok=True)
json.dump(out, open("evidence/proxy_calibration.json", "w"), indent=1)
