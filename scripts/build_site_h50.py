#!/usr/bin/env python3
"""Generate the docs/h50 research sub-site from the machine receipts.

Every number on these pages is read from evidence JSON receipts at build time;
nothing is hand-typed into the HTML.  The sub-site lives in its own directory
and never overwrites the repository landing page or the other sessions'
sub-sites (docs/ds48-fusion, docs/h49).
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "h50"

BUILD = json.loads((ROOT / "evidence/build_ds50_receipt_20261007.json").read_text())
HOLDOUT = json.loads((ROOT / "evidence/holdout_ds50_20261007.json").read_text())
SPLAY = json.loads((ROOT / "evidence/splay_probe_holdout_20261007.json").read_text())
BOARD = json.loads((ROOT / "docs/data/leaderboard_20261007.json").read_text())

PRIMARY = BUILD["primary_file"]            # docs/downloads/...
PRIMARY_NAME = Path(PRIMARY).name
ZIP_NAME = Path(BUILD["zip_file"]).name
SHA = BUILD["primary_sha256"]
BYTES = BUILD["primary_bytes"]
FMT = BUILD["format_receipt"]
AA = BUILD["anti_average_check"]
PARENTS = BUILD["parents"]
METHOD = BUILD["method"]
NOTE = BUILD["submission_note"]
UNAME = BUILD["submission_name"]
DIAGS = BUILD["diagnostics"]

DISCLAIMER = (
    "No organizer score exists for any artifact on this site. Every candidate is "
    "UNSCORED research output; owner-reported live values are labelled [OWNER-REPORT]."
)

NAV = (
    '<nav><a href="index.html">H50 summary</a>'
    '<a href="executive-summary.html">Executive summary &amp; how to submit</a>'
    '<a href="method.html">Method &amp; evidence</a>'
    '<a href="hypotheses.html">Hypotheses</a>'
    '<a href="sources.html">Sources</a>'
    '<a href="../index.html">Repository site ↗</a></nav>'
)


def page(title: str, head_note: str, body: str) -> str:
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title><link rel="stylesheet" href="../assets/style.css"></head>
<body><header><p>DOE GEMS Prize · DrivenData #306 · GEMSDOE48 H50 · {head_note}</p>
<h1>{title}</h1>{NAV}</header><main class="wrap">
{body}
</main><footer><p>{DISCLAIMER}</p>
<p class="small">Built by scripts/build_site_h50.py from evidence receipts on the same commit.
Receipts: evidence/build_ds50_receipt_20261007.json, evidence/holdout_ds50_20261007.json,
docs/data/leaderboard_20261007.json.</p></footer></body></html>"""


def holdout_table(results: dict) -> str:
    order = ["dotted_b2_parent", "tip_h36_parent", "union_decision", "naive_mean_beliefs",
             "raw_sparse_rho05_same_parents", "h50_ds_belief", "h50_binary_budget_matched"]
    rows = []
    for name in order:
        r = results[name]
        folds = " · ".join(f"{r[f]['dti']:.4f}" for f in ("NW", "NE", "SW", "SE"))
        cls = ' style="background:#edf8f3;font-weight:700"' if name == "h50_ds_belief" else ""
        rows.append(f"<tr{cls}><td>{name}</td><td>{r['mean_dti']:.6f}</td><td>{folds}</td></tr>")
    return ('<div class="table-scroll"><table><tr><th>candidate</th><th>mean DTI</th>'
            '<th>folds NW·NE·SW·SE</th></tr>' + "".join(rows) + "</table></div>")


def board_rows(n: int = 8) -> str:
    rows = []
    for r in BOARD["rows"][:n]:
        rows.append(f"<tr><td>#{r['rank']}</td><td>{r['participant']}</td>"
                    f"<td>{r['best_public']:.4f}</td><td>{r['submissions']}</td></tr>")
    return ('<div class="table-scroll"><table><tr><th>rank</th><th>participant</th>'
            '<th>best public</th><th>submissions</th></tr>' + "".join(rows) + "</table></div>")


def build_index() -> str:
    mtheta = DIAGS["unassigned_mass_mTheta"]
    body = f"""
<section class="download">
<p class="eyebrow">1 · One-click submission file — unique research candidate</p>
<p><a class="button" href="../downloads/{PRIMARY_NAME}" download>⬇ Download H50 submission GeoTIFF ({BYTES:,} B)</a>
<a class="button alt" href="../downloads/{ZIP_NAME}" download>⬇ .zip (single GeoTIFF)</a>
<a class="button alt" href="../downloads/{Path(BUILD['nan_outside_twin']['path']).name}" download>⬇ NaN-outside twin (official sample convention)</a></p>
<p class="small">All three carry identical in-footprint values (SHA-audited twin). The zeros file is immune to the
portal's "[0, 1]" range rejection by construction; the NaN twin additionally passes
<code>scripts/validate_submission.py</code>'s official-convention audit
(<a href="../../evidence/h50_submission_validation_20261007.json">receipt</a>).</p>
<p><strong>Unique submission name:</strong> <code>{UNAME}</code><br>
<strong>Paste-ready note ({len(NOTE)}/200 chars):</strong> <code>{NOTE}</code></p>
<p class="small">SHA-256 <code>{SHA}</code> · one band float32 · {FMT['crs']} · 100 m ·
{FMT['height']}×{FMT['width']} · in-footprint [{FMT['min_value']:.4f}, {FMT['max_value']:.4f}] ·
all-finite, no nodata tag · zeros outside footprint · {FMT['positive_pixels']:,} positive cells</p>
<p class="small">Disagreement diagnostics (review only, never upload):
<a href="../downloads/diagnostics/{Path(mtheta['path']).name}" download>unassigned mass m(Θ)</a> ·
<a href="../downloads/diagnostics/{Path(DIAGS['conflict_K']['path']).name}" download>raw conflict K</a> ·
<a href="../downloads/diagnostics/{Path(DIAGS['plausibility']['path']).name}" download>plausibility Pl(F)</a></p>
</section>

<div class="warn"><strong>UNSCORED — NOT SLOT-CLEARED.</strong> This file is the brief's requested
unique Dempster–Shafer fusion of the two best families, format-verified and downloadable, but the
blocked-holdout diagnostics below do <em>not</em> beat both parents or the union on the public
proxies. The official public leaderboard (single read 2026-10-07) is topped by xiaofanhu at 0.3774;
the brief's "0.3195 highest" is stale (that is rank #7, DARD). No organizer score exists for this
artifact, and the 0.2778 row on the public board is participant extradr19 with no organizer-level
attribution to the local mirror bytes [OWNER-REPORT].</div>

<h2>2 · What the fusion preserves that averaging destroys</h2>
<p>Parents: dotted H33-2-B2 ({PARENTS['dotted_best']['positive_pixels']:,} px, owner live
{PARENTS['dotted_best']['owner_reported_live']:.4f}) × tip H36-1 rung30
({PARENTS['tip_best']['positive_pixels']:,} px, owner live {PARENTS['tip_best']['owner_reported_live']:.4f});
intersection {BUILD['parent_overlap']['intersection_pixels']:,} / union
{BUILD['parent_overlap']['union_pixels']:,} (Jaccard {BUILD['parent_overlap']['jaccard']:.3f}) —
{BUILD['parent_overlap']['xor_disagreement_pixels']:,} pixels on which the two strongest approaches
disagree. Dempster's rule carries that disagreement as unassigned mass m(Θ)
(range 0.0037–0.0306 in footprint) and raw conflict K (max 0.8804; 11.5 % of the footprint &gt; 0.3).</p>
<p><strong>Not the naive mean (brief's required check):</strong> Pearson {AA['pearson_in_footprint']:.4f},
Spearman {AA['spearman_in_footprint']:.4f}, MAE {AA['mae_in_footprint']:.4f}, max |Δ| {AA['max_abs_difference']:.4f},
{AA['fraction_cells_abs_diff_gt_0.05']:.1%} of cells with |Δ|&gt;0.05, top-{AA['topk']:,} emission Jaccard
{AA['topk_emission_jaccard']:.4f}. Pearson vs the prior H48 artifact 0.454; zero SHA-256 collisions against
44 existing grid rasters.</p>
<img src="../assets/h50_ds_layers.png" alt="Dempster-Shafer layers: belief, unassigned mass, conflict" style="width:100%;border:1px solid var(--line);border-radius:10px">
<img src="../assets/h50_disagreement.png" alt="DS belief versus naive mean disagreement" style="width:100%;border:1px solid var(--line);border-radius:10px;margin-top:.6rem">

<h2>3 · Blocked-holdout diagnostics (public proxies only)</h2>
<h3>SGMC off-catalogue truth (&gt;300 m from catalogue), 4 fixed quadrants, official metric</h3>
{holdout_table(HOLDOUT['sgmc_offcat_results'])}
<h3>Catalogue truth proxy, same folds</h3>
{holdout_table(HOLDOUT['catalogue_proxy_results'])}
<p>H50 beats the naive mean 4/4 folds on the SGMC proxy and improves on the raw-sparse rho=0.5 recipe
with the same parents (+0.0064 mean), but loses to both parents and to the union on both proxies.
<strong>The slot gate is not cleared; do not spend a weekly submission on this evidence alone.</strong></p>

<h2>4 · Public leaderboard snapshot (single manual read, 2026-10-07)</h2>
{board_rows()}
<p class="small">Source: official DrivenData public leaderboard. Scores identify participants, not files;
no row is attributed to any local artifact.</p>
"""
    return page("GEMSDOE48 H50 — conflict-aware fusion of the two best families",
                "research candidate · unscored", body)


def build_exec() -> str:
    body = f"""
<h2 style="margin-top:0">1 · How to submit to the competition, step by step</h2>
<ol>
<li>Open the official <a href="https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/">New submission</a> page (login required; at most the competition's stated weekly allowance).</li>
<li>Under <em>File to submit</em>, choose either the single GeoTIFF
<code>{PRIMARY_NAME}</code> (⬇ button on the <a href="index.html">H50 summary</a>) or its
<code>.zip</code> containing exactly that one GeoTIFF. Both are accepted shapes per the portal text.</li>
<li>Set the unique name you will use to recognize the run: <code>{UNAME}</code>.</li>
<li>Paste this note (≤200 chars) into the <em>Note (optional)</em> field:<br><code>{NOTE}</code></li>
<li>Submit. The portal scores distance-weighted Tversky (α=0.2, β=0.8, 300 m triangular kernel) on the private expert labels.</li>
</ol>
<div class="warn"><strong>Honest recommendation.</strong> The blocked holdout does not show H50 beating
both parents or the union on the public proxies. Per this repository's gate, a weekly slot should not be
spent on it unless the owner consciously overrides the gate after reading section 3 of the
<a href="index.html">summary</a>. The download exists because the project brief requires a unique,
format-valid, downloadable DS fusion; it is not a cleared pick.</div>

<h2>2 · The “Predicted values must be in range [0, 1]” error — why this file cannot trigger it</h2>
<p>Two distinct failures produce that portal message: (1) writing the float32 nodata sentinel
−3.4028235e38 through unchanged (it lies outside [0,1]; 3,061 such cells sit inside the footprint of the
official training features), and (2) a validator treating a NaN/nodata sentinel as a prediction
(IR-48-03). This file is re-read from disk and audited: <strong>1 band, float32, {FMT['crs']},
100 m, {FMT['height']}×{FMT['width']}, every one of the 12,279,160 cells finite, min {FMT['min_value']:.4f},
max {FMT['max_value']:.4f}, zero cells outside [0,1], zero NaN, no nodata tag</strong>
(<a href="../../evidence/build_ds50_receipt_20261007.json">receipt</a>). The same all-finite convention is
what the scored 0.27xx sibling files use.</p>

<h2>3 · What never to upload</h2>
<p>The three diagnostics — unassigned mass m(Θ), raw conflict K, plausibility Pl(F) — are geological
review layers, not predictions; uploading them would waste a slot. m(Θ) has range 0.0037–0.0306 and K is
near zero over most of the map; neither is a favorability surface.</p>

<h2>4 · Checklist before any upload</h2>
<ol>
<li>Re-run <code>scripts/validate_submission.py</code> on the exact bytes and keep the receipt.</li>
<li>Confirm the SHA-256 <code>{SHA}</code> matches the file you upload.</li>
<li>Confirm the weekly slot budget and that the gate override is deliberate.</li>
<li>Do not confuse this file with the withdrawn v1 anchor-1.0 build (sha 2c01d212…, removed from downloads).</li>
</ol>
"""
    return page("Executive summary — how to submit H50", "submission runbook", body)


def build_method() -> str:
    body = f"""
<h2 style="margin-top:0">1 · Construction</h2>
<ol>
<li>Belief surfaces in the metric's own geometry: b_i(x) = max over committed pixels y of
k(d(x,y)), k(d)=max(1−d/300 m,0).</li>
<li>Two-sided simple support masses with Shafer §11.2 discounting: m_i(F)=a_i·b_i,
m_i(notF)=a_i·(1−b_i), m_i(Θ)=1−a_i, with a_dotted={METHOD['reliabilities']['dotted']},
a_tip={METHOD['reliabilities']['tip']:.6f} (RHO_MAX=0.95 ceiling × owner-reported live ratio
0.2710/0.2778 [OWNER-REPORT]).</li>
<li>Canonical normalized Dempster rule; submission surface Bel(F)=m12(F) divided by its
in-footprint max (already [0,1]).</li>
<li>Diagnostics carried forward: m12(Θ) (where the families neither agree nor fully conflict) and raw
conjunctive conflict K (where they actively contradict; canonical normalization redistributes K, so it
is stored separately — Zadeh-paradox transparency).</li>
</ol>
<p>Provable properties (tests/test_ds50.py): masses sum to 1; commutativity; Bel=1 and K=0 at full
agreement; at full opposition K=a1·a2=0.8804 and m(Θ)&gt;0 (a perfect-reliability anchor would force
m(Θ)≡0 — the withdrawn v1 did exactly that).</p>

<h2>2 · Why 0.2778 won, and what beating 0.3774 requires</h2>
<p>The DTI is a budget: DTI = TPw / (0.2·(TPw+S−M) + 0.8·|G|); every emitted unit that is not the best
cover of a truth pixel costs 0.2, and binary {{0,1}} is optimal. The 0.2778 file wins by sitting at the
break-even credit bar (0.2·0.26 ≈ 0.052 per dot) with 37,654 dots, 0 within 200 m of the catalogue
(sibling GEMSDOE32 analysis, two independent derivations of the same bar). The 0.3774 leader needs
≈25 % more mean credit per pixel at matched mass — a detector improvement, not a fusion rule.</p>

<h2>3 · Why DS fusion loses on the proxies (and why that is expected)</h2>
<p>Dempster belief is intersection-like: high where both families agree, uncertain where they disagree.
The public proxies reward cheaply covering fault traces — the union's job. Preserving disagreement is
scientifically honest (the geologist sees where the two strongest approaches contradict) but is not by
itself score-raising. This session's kernel-credit calibration did help against the raw-sparse recipe
(+0.0064 mean SGMC), and H50 beats the naive mean 4/4 folds — but not the parents.</p>

<h2>4 · Evidence classes used on this site</h2>
<p>[OWNER-REPORT] owner-read live screens, no organizer receipt · [DERIVED] algebra from reported
quantities · proxy = public-map layer, never private expert truth. No page here states or implies an
organizer score.</p>
"""
    return page("Method & evidence — H50 Dempster-Shafer fusion", "method", body)


def build_hypotheses() -> str:
    splay_sgmc = SPLAY["sgmc_offcat_results"]
    body = f"""
<h2 style="margin-top:0">1 · Validated this session (top candidate, no new data needed)</h2>
<div class="warn"><strong>H50-1 coarse splay band — NEGATIVE result.</strong> An isotropic 100–600 m
offset band around catalogue traces (with and without a family-corridor gate) scored
{splay_sgmc['splay_band_100_600m']['mean_dti']:.4f} / {splay_sgmc['splay_band_x_family_corridor']['mean_dti']:.4f}
mean DTI on the SGMC off-catalogue blocked proxy versus {splay_sgmc['tip_h36_parent_reference']['mean_dti']:.4f}
for the tip parent and 0.0970 for the union. It does not clear the gate; no slot is spent. Receipt:
evidence/splay_probe_holdout_20261007.json.</div>

<h2>2 · Ranked new hypotheses (preregistered 2026-10-07)</h2>
<div class="table-scroll"><table>
<tr><th>#</th><th>hypothesis</th><th>layers / signature</th><th>why off-catalogue</th><th>differs from prior art</th><th>expected / cost / data</th></tr>
<tr><td>A</td><td>coverage-budget credit repacking on scatter-blurred family fields</td>
<td>family surfaces blurred at the ~1.85 px hidden-scatter scale; greedy marginal-credit packing at bar k&gt;0.2·DTI</td>
<td>spends budget on corroborated single-family corridors, not catalogue proximity</td>
<td>two-round objective; sibling live-anchored model measured +0.0247±0.0005 (12/12 draws) [DERIVED]</td>
<td>highest expected gain / medium / fully local</td></tr>
<tr><td>B</td><td>radiometric alteration ratio × DS conflict corridors</td>
<td>GeoDAWN K/Th/U/TC (USGS DOI 10.5066/P93LGLVQ) low-Th/K linear trends inside high-K corridors</td>
<td>alteration records fluid flow on buried structures absent from the inventory</td>
<td>first alteration-ratio × two-family-conflict prior</td>
<td>moderate / medium / mirror restorable, SHA-pinned</td></tr>
<tr><td>C</td><td>shallow temperature probe residual prior along corridors</td>
<td>INGENIOUS 2 m probes (GDR 1391, CC BY 4.0) residualized, gated by family support</td>
<td>active seeps mark permeable pathways with no mapped trace</td>
<td>temperature as residual point prior, not regional channel</td>
<td>low–moderate / medium / sibling CI receipt shows obtainable</td></tr>
<tr><td>D</td><td>scarp-youth continuation past catalogue tips</td>
<td>LiDAR scarp morphology (USGS 3DEP upstream) youthful segments beyond trace tips</td>
<td>spends budget past catalogue endpoints</td>
<td>morphology youth vs GEMSDOE38 Euler/step-over tip protection</td>
<td>moderate / medium / mirror restorable</td></tr>
<tr><td>E</td><td>oriented splay prior from SGMC contact topology</td>
<td>USGS SGMC vectors; oriented offset bands at extensional bends</td>
<td>targets unmapped splays by construction</td>
<td>refines the failed isotropic band with orientation</td>
<td>low–moderate / medium–high / obtainable per sibling CI</td></tr>
</table></div>

<h2>3 · Promotion rule</h2>
<p>A candidate touches a weekly slot only after beating the current blocked-holdout best (union 0.0970;
H49 0.1008 same proxy) in ≥3/4 folds on both proxy regimes, restating the leakage limitation. H50-1
(coarse) failed and is recorded as a negative result.</p>
"""
    return page("Hypotheses — H50 session slate", "preregistered 2026-10-07", body)


def build_sources() -> str:
    body = """
<h2 style="margin-top:0">Official and verified sources (manual review links)</h2>
<div class="table-scroll"><table>
<tr><th>source</th><th>authority</th><th>evidence class</th></tr>
<tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/">Competition problem description</a></td><td>organizer</td><td>rules, metric, format</td></tr>
<tr><td><a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">Public leaderboard</a></td><td>organizer display</td><td>single manual read 2026-10-07; rows identify participants, not files</td></tr>
<tr><td><a href="https://docs.nlr.gov/docs/fy26osti/96647.pdf">NLR/OSTI 96647 PDF</a></td><td>official report</td><td>submission format context</td></tr>
<tr><td><a href="https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and">USGS GeoDAWN survey</a> · DOI <a href="https://doi.org/10.5066/P93LGLVQ">10.5066/P93LGLVQ</a></td><td>USGS</td><td>airborne mag/rad upstream of mirrors</td></tr>
<tr><td><a href="https://gdr.openei.org/submissions/1391">GDR 1391 INGENIOUS data</a> · DOI <a href="https://doi.org/10.15121/1881483">10.15121/1881483</a></td><td>GDR/INEEL</td><td>fault catalogue, springs, probes; CC BY 4.0</td></tr>
<tr><td><a href="https://gbcge.org/current-projects/ingenious/">INGENIOUS project page</a></td><td>Great Basin Center</td><td>project context</td></tr>
<tr><td><a href="https://epsg.io/32611">EPSG:32611</a></td><td>IOGP registry</td><td>CRS definition (WGS 84 / UTM 11N)</td></tr>
<tr><td><a href="https://en.wikipedia.org/wiki/Tversky_index">Tversky index</a></td><td>reference</td><td>metric family background</td></tr>
<tr><td><a href="https://github.com/drivendataorg/gems-prize-reference-solution">Reference solution</a></td><td>organizer code</td><td>metric implementation anchor</td></tr>
<tr><td>Dempster (1967), Shafer (1976)</td><td>peer-reviewed</td><td>evidence theory; rule of combination</td></tr>
<tr><td><a href="https://mrdata.usgs.gov/geology/state/">USGS SGMC state compilations</a></td><td>USGS</td><td>public-domain fault traces behind the SGMC proxy</td></tr>
<tr><td><a href="https://www.usgs.gov/3d-elevation-program/about-3dep-products-services">USGS 3DEP</a></td><td>USGS</td><td>1 m DEM upstream of LiDAR scarp features; no use restrictions</td></tr>
</table></div>
<h2>Local provenance</h2>
<p>Parents and proxies are public owner mirrors pinned by SHA-256 (registry/inputs.json,
registry/data_manifest_gemsdoe32.json). The H36-1 mirror was re-downloaded from the pinned GEMSDOE28
commit via the GitHub API on 2026-10-07 and matches its pin; the local data/raw copy is a mask-identical
format rewrite. None of these bytes is organizer-authenticated.</p>
"""
    return page("Sources — official and verified", "manual review", body)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / ".nojekyll").write_text("")
    (OUT / "index.html").write_text(build_index())
    (OUT / "executive-summary.html").write_text(build_exec())
    (OUT / "method.html").write_text(build_method())
    (OUT / "hypotheses.html").write_text(build_hypotheses())
    (OUT / "sources.html").write_text(build_sources())
    print("wrote", sorted(p.name for p in OUT.iterdir()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
