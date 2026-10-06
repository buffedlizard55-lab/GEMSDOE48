"""Fetch every input this repo needs from hash-pinned public GitHub mirrors; FAIL CLOSED on mismatch.

Uses `gh api` (GitHub egress only; DrivenData is never contacted).  Usage: python scripts/fetch_mirrors.py
"""
import json, subprocess, sys, hashlib, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]; DEST = ROOT / "data/raw"
NEED = ["existing_faults", "sample_submission", "ext_derived_sgmc_faults_100m_u8", "ext_gdr_qfaults_traces",
        "ext_lidar_scarp_features_u8", "scored_h19_5", "scored_h19_4", "scored_h16_1", "scored_d15_scored",
        "scored_d28_unscored", "scored_gems27_tgc_v2_d15", "calib_13gems_20261001_r13-lattice-s5_v2_nan-ou",
        "calib_8GEMSDOE_Hedge-v2_submission", "calib_gems10-h25-ctx-ridge-20260927T2329477041",
        "calib_gems10-h28-dotted-ridge-20260928T0202562", "calib_gemsdoe-ens12-adopted-7f00890a",
        "calib_gemsdoe9-PLACEHOLDER-2314b599"]
SIBLING = [  # (repo, path, dest, sha256) — live-scored family files used by H48-1
 ("buffedlizard55-lab/GEMSDOE32", "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", "scored/b2_02778.tif", "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"),
 ("buffedlizard55-lab/GEMSDOE28", "docs/downloads/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif", "scored/r1solo_02708.tif", "ab02300152248fdda04e988e2cd2a0c13f35eec42fcf670a15e8b76b19e24a73"),
 ("buffedlizard55-lab/GEMSDOE28", "docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", "scored/h36_02710.tif", "5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641"),
 ("buffedlizard55-lab/GEMSDOE28", "docs/downloads/gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif", "scored/h32tip_02649.tif", "04d31922f5c1ea4016984fc470ab2b0ff8e266c615792f0e86020da3b940d3ff"),
 ("buffedlizard55-lab/GEMSDOE33", "docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif", "scored/h33d_tip_02632.tif", "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"),
]
def gh(repo, path, ref, out):
    out.parent.mkdir(parents=True, exist_ok=True)
    q = f"repos/{repo}/contents/{path}" + (f"?ref={ref}" if ref else "")
    with out.open("wb") as fh:
        subprocess.run(["gh", "api", q, "-H", "Accept: application/vnd.github.raw"], stdout=fh, check=True)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
fail = []
spec = json.load(open(ROOT / "registry/data_manifest_gemsdoe32.json"))
for f in spec["files"]:
    if f["id"] not in NEED: continue
    t = DEST / f["dest"]
    if not (t.exists() and sha(t) == f["sha256"]): gh(f["repo"], f["path"], f["ref"], t)
    ok = sha(t) == f["sha256"]; print("PASS" if ok else "FAIL", f["id"]); fail += [] if ok else [f["id"]]
for repo, path, dest, h in SIBLING:
    t = DEST / dest
    if not (t.exists() and sha(t) == h): gh(repo, path, None, t)
    ok = sha(t) == h; print("PASS" if ok else "FAIL", dest); fail += [] if ok else [dest]
print(json.dumps({"failed": fail})); sys.exit(1 if fail else 0)
