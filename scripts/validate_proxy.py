#!/usr/bin/env python3
"""Four-block SGMC off-catalogue proxy validation; never represented as private truth."""
from __future__ import annotations
import json, sys
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
ROOT=Path(__file__).resolve().parents[1]
R=3.0

def kernel(d): return np.maximum(1.0-d/R,0.0)
def score(pred, truth):
    if not truth.any(): return {"dti":0.0,"tp":0.0,"fp":float(pred.sum()),"truth":0}
    dp=distance_transform_edt(pred<=0)
    tp=float(kernel(dp[truth]).sum())
    dg=distance_transform_edt(~truth)
    fp=float((pred*(1-kernel(dg))).sum())
    fn=float(truth.sum())-tp
    return {"dti":tp/(tp+.2*fp+.8*fn+1e-12),"tp":tp,"fp":fp,"truth":int(truth.sum())}
def read(p):
    with rasterio.open(p) as s:return s.read(1)
def main():
    dotted=read(ROOT/'data/raw/dotted.tif').astype(float)
    tip=read(ROOT/'data/raw/tip.tif').astype(float)
    fusion=read(ROOT/'docs/downloads/gemsdoe48-h48-ds-yager-conflict-20261006.tif').astype(float)
    labels=read(ROOT/'data/raw/labels.tif')>0
    sgmc=read(ROOT/'data/raw/external/derived_sgmc_faults_100m_u8.tif')>0
    with rasterio.open(ROOT/'data/raw/sample_submission.tif') as s: footprint=np.isfinite(s.read(1))
    truth=sgmc & footprint & (distance_transform_edt(~labels)>=3.0)
    h,w=truth.shape; folds=[]
    for i,(ys,xs) in enumerate([(slice(0,h//2),slice(0,w//2)),(slice(0,h//2),slice(w//2,w)),(slice(h//2,h),slice(0,w//2)),(slice(h//2,h),slice(w//2,w))]):
        t=truth[ys,xs]
        row={"fold":i,"truth_pixels":int(t.sum())}
        for name,a in [("dotted",dotted),("tip",tip),("fusion",fusion),("naive_mean",(dotted+tip)/2)]: row[name]=score(a[ys,xs],t)
        row["fusion_minus_dotted"]=row["fusion"]["dti"]-row["dotted"]["dti"]
        folds.append(row)
    means={name:float(np.mean([f[name]["dti"] for f in folds])) for name in ["dotted","tip","fusion","naive_mean"]}
    report={"schema":"GEMSDOE48-proxy-v1","protocol":"four fixed spatial quadrants; USGS SGMC-derived faults >=300 m from public catalogue", "warning":"Proxy only. Not private expert truth; SGMC provenance and source dependence prevent a slot-clearance claim.","folds":folds,"mean_dti":means,"fusion_minus_dotted_mean":means['fusion']-means['dotted'],"positive_folds_vs_dotted":sum(f['fusion_minus_dotted']>0 for f in folds),"gate_rule":"fusion mean > dotted mean and >=3/4 folds positive","gate_pass":bool(means['fusion']>means['dotted'] and sum(f['fusion_minus_dotted']>0 for f in folds)>=3),"submission_slot_recommendation":"DO NOT SPEND"}
    (ROOT/'docs/data/proxy-validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
