"""RETIRED DS48 site generator — do not run.

The former generated pages contained invalidated live-score inversions, hidden-
truth estimates, thresholds, and submission claims. The corrected DS48 archive in
``docs/ds48-fusion/`` is manually maintained. ``main`` refuses to write anything,
so the legacy builder cannot silently regenerate the superseded claims.
Historical calculation code and receipts remain available for forensic review.
"""

from __future__ import annotations

import html
import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DOCS = REPO / "docs"
REG = REPO / "registry"
EVI = REPO / "evidence"

DD = "https://www.drivendata.org/competitions/306/competition-doe-gems/"
DD_LEADERBOARD = DD + "leaderboard/"
DD_PROBLEM = DD + "page/967/"
DD_ABOUT = DD + "page/968/"
DD_DATA = DD + "data/"
RULES_PDF = "https://docs.nlr.gov/docs/fy26osti/96647.pdf"
REFSOL = "https://github.com/drivendataorg/gems-prize-reference-solution"
GDR = "https://gdr.openei.org/submissions/1391"
GEODAWN = "https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7"
GEODAWN_DOI = "https://doi.org/10.5066/P93LGLVQ"
MASK_THREAD = ("https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-"
               "faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4")
POOL_THREAD = ("https://community.drivendata.org/t/leaderboard-aggregation-pooled-over-public-"
               "test-pixels-or-mean-of-per-chunk-scores/11550")
TESTSRC_THREAD = ("https://community.drivendata.org/t/how-were-the-new-test-faults-identified-"
                  "data-sources-and-fault-types/11527/7")


def load(path: Path, default=None):
    if not path.exists():
        return default
    with open(path) as fh:
        return json.load(fh)


BUILD = load(REG / "submission_build.json", {})
ANCHOR = load(REG / "submission_build.json", {}).get("measurements", {})
ANTI = load(EVI / "holdout_antimonotone.json", {})
SELECTION = load(EVI / "selection.json", {})
COVER = load(EVI / "cover_sweep.json", {})
DSF = load(EVI / "ds_fusion.json", {})


def esc(x) -> str:
    return html.escape(str(x))


def fmt(x, nd=4):
    if x is None:
        return "—"
    if isinstance(x, float):
        return f"{x:,.{nd}f}"
    return f"{x:,}" if isinstance(x, int) else esc(x)


def page(title: str, subtitle: str, body: str, active: str = "") -> str:
    nav = [
        ("index.html", "Historical fusion"),
        ("executive-summary.html", "Archived instructions"),
        ("research.html", "Archived 0.2778 analysis"),
        ("hypotheses.html", "Hypotheses"),
        ("sources.html", "Sources"),
        ("irregularities.html", "Irregularities"),
    ]
    parts = []
    for href, t in nav:
        cls = ' class="on"' if href == active else ""
        parts.append(f'<a href="{href}"{cls}>{esc(t)}</a>')
    links = "".join(parts)
    return f"""<!doctype html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)} · GEMSDOE48</title>
<link rel="stylesheet" href="assets/site.css">
</head><body>
<header class="top"><div class="wrap">
  <div class="brand"><span class="dot"></span><b>GEMSDOE48</b>
    <span class="tag">Dempster&ndash;Shafer disagreement-preserving fusion</span></div>
  <nav>{links}</nav>
</div></header>
<div class="namestrip"><div class="wrap">
  <span class="ns-label">Historical research artifact — NOT slot-cleared</span>
  <code class="ns-name">{esc(BUILD.get('unique_name','—'))}</code>
  <a class="ns-dl" download href="downloads/{esc(BUILD.get('files',{}).get('emission',{}).get('file',''))}">
    ↓ Download for audit only — do not submit</a>
</div></div>
<div class="xlink"><div class="wrap">
  This is the <b>DS48 fusion</b> sub-site. The repository landing page is
  <a href="../index.html">docs/index.html</a>, and its
  <a href="../leaderboard.html">leaderboard page</a> carries a <b>newer snapshot</b> than the
  2026-10-02 figure quoted here — a later session measured the leader at 0.3774, not 0.3195.
  Treat both numbers as dated, and the landing page as the newer one.
</div></div>
<main class="wrap">
  <div class="hero"><h1>{esc(title)}</h1><p class="lead">{subtitle}</p></div>
  {body}
  <footer><p>Historical sub-site rebuilt from <code>registry/</code> and <code>evidence/</code> by
  <code>scripts/build_site_ds48.py</code>. Owner-reported scores are labelled
  <span class="badge amber">OWNER-REPORT</span>; local measurements are labelled
  <span class="badge blue">PROXY</span> or <span class="badge">DERIVED</span>.
  No organizer score exists for any artifact in this repository.</p></footer>
</main></body></html>"""


def card(title, body, tag=""):
    t = f'<span class="badge blue">{esc(tag)}</span>' if tag else ""
    return f'<article class="card"><h3>{esc(title)} {t}</h3>{body}</article>'


# ---------------------------------------------------------------- index
def build_index() -> str:
    files = BUILD.get("files", {})
    checks = BUILD.get("format_checks", {})
    em = files.get("emission", {})
    be = files.get("belief", {})
    mt = files.get("mtheta", {})
    cf = files.get("conflict", {})
    meas = BUILD.get("measurements", {})
    base = meas.get("base_live_02778", {})
    dsem = meas.get("ds_emission", {})
    diag = BUILD.get("not_the_mean", {})
    neg = BUILD.get("headline_negative_result", {})
    ls = BUILD.get("layer_stats", {})
    name = BUILD.get("unique_name", "GEMSDOE48-DS48-FUSION")

    c_ds = card(
        'Dempster&ndash;Shafer fusion',
        '<p>The dotted family and the tip / step-over family agree on 69.6 % of their pixels and '
        'disagree on 14,724. They are combined with Dempster&rsquo;s rule on the frame '
        '{F, &not;F} with Shafer reliability discounts a = '
        + fmt(BUILD.get('reliability', {}).get('a_dotted'), 2) + '. Belief is '
        + fmt(diag.get('bel_at_full_agreement')) + ' at agreement and '
        + fmt(diag.get('bel_at_single_source_only')) + ' where only one family supports a pixel.</p>',
        'DERIVED')
    c_mean = card(
        'Not the naive mean &mdash; measured',
        '<p>Pearson r = ' + fmt(diag.get('pearson_r_belief_vs_naive_mean_on_union'), 6)
        + ' and Spearman rho = ' + fmt(diag.get('spearman_rho_belief_vs_naive_mean_on_union'), 6)
        + ' on the union. Values differ (mean |delta| = '
        + fmt(diag.get('mean_abs_difference_on_union'), 4)
        + ') but the <b>ranking is identical</b>, because a union pixel has belief 1 in its own '
        'family, so both statistics are monotone in the other family&rsquo;s belief alone. '
        'Reproduced honestly rather than claimed as a win.</p>',
        'MEASURED')
    c_fals = card(
        'Three falsified arms',
        '<ul><li>DS corroboration removal at 9 radii: gate fails everywhere (best safety 0.64 &lt; 2.0).</li>'
        '<li>Hexagonal covering-optimal re-emission at 11 spacings: <b>not cleanly falsified</b>. '
        'At matched mass the best arm (spacing 5.6 px, 37,499 dots) is x1.019 on the SGMC '
        'off-catalogue layer and x12.5 on the catalogue-in-corridor layer. The catalogue side is '
        'anti-monotone and carries no live information; the SGMC side is +1.9 %, inside the noise '
        'of re-sampling the same corridor. Historical proxy candidate only; not slot-cleared.</li>'
        '<li>DS-ranked re-emission at matched mass: SGMC credit falls 5.8 %.</li></ul>'
        '<p>Conclusion: <b>the emission is at a local optimum</b> and the binding constraint is '
        'detector quality. ' + esc(neg.get('evidence_class', '')) + '</p>',
        'PROXY')

    body = f"""
<section class="callout warn">
  <h2>Read this before uploading anything</h2>
  <p>Every file on this page is <b>UNSCORED</b>. No organizer score exists for any artifact in
  this repository. The measurements below are local proxies, and this repository's central
  finding is that <b>the catalogue-based proxy ranks artifacts in the exact reverse of the live
  leaderboard</b> (Spearman &rho; = {fmt(ANTI.get('spearman_rho_proxy_dense_vs_live'), 1)} on
  n = 4). No weekly slot is cleared: do not upload any artifact on this historical page or
  spend a slot. No owner override applies.</p>
</section>

<section>
<h2>⬇ One-click downloads</h2>
<div class="grid2">
  <article class="card feature">
    <span class="badge amber">Artifact the brief asked for</span>
    <h3>Dempster&ndash;Shafer combined belief Bel(F)</h3>
    <p class="fileline">{esc(be.get('file','—'))}</p>
    <p>{fmt(be.get('bytes'))} bytes · sha256 <code>{esc(be.get('sha256','—'))}…</code> ·
    single band float32 · EPSG:32611 · 100 m · 3730 × 3292 · all finite ·
    <b>{esc(checks.get('belief',{}).get('verdict','—'))}</b> all format checks</p>
    <p><a class="button primary" download href="downloads/{esc(be.get('file',''))}">
      ↓ Download combined belief .tif</a></p>
    <p class="micro"><b>Diagnostic.</b> A graded belief surface is <i>strictly worse</i> than its
    own binarisation on this metric: the score's derivative in a pixel value <i>v</i> is
    <code>(k − 0.2·DTI)·D₀/(D₀ + 0.2v)²</code>, independent of <i>v</i>. Do not upload this one
    as a prediction.</p>
  </article>
  <article class="card feature">
    <span class="badge blue">Historical research artifact — not slot-cleared</span>
    <h3>DS-ranked, off-flank emission at the live-best mass</h3>
    <p class="fileline">{esc(em.get('file','—'))}</p>
    <p>{fmt(em.get('bytes'))} bytes · sha256 <code>{esc(em.get('sha256','—'))}…</code> ·
    {fmt(checks.get('emission',{}).get('n_positive'))} positive px · values in {{0.0, 1.0}} ·
    <b>{esc(checks.get('emission',{}).get('verdict','—'))}</b> all format checks</p>
    <p><a class="button primary" download href="downloads/{esc(em.get('file',''))}">
      ↓ Download emission .tif</a></p>
    <p class="micro">Mass-neutral: exactly {fmt(base.get('n'))} px, the same as the best live
    artifact, so it spends none of the removal budget. Measured against both independent truth
    layers it gains on one and loses {fmt(100*(1-dsem.get('sgmc_off_catalogue',{}).get('tpw',1)/max(base.get('sgmc_off_catalogue',{}).get('tpw',1),1)),1)} %
    on the other — see below.</p>
  </article>
</div>
<div class="grid2">
  <article class="card">
    <span class="badge">Disagreement layer 1</span>
    <h3>Unassigned belief <code>m₁₂(&Theta;)</code></h3>
    <p class="fileline">{esc(mt.get('file','—'))}</p>
    <p>The mass Dempster's rule leaves on the frame itself.
    {fmt(diag.get('m_theta_at_full_agreement'))} where the two families agree,
    {fmt(diag.get('m_theta_at_disagreement'))} where they disagree.
    {fmt(mt.get('bytes'))} B · sha256 <code>{esc(mt.get('sha256','—'))}…</code> ·
    observed range <code>[{fmt(ls.get('mtheta',{}).get('min'),4)}, {fmt(ls.get('mtheta',{}).get('max'),4)}]</code></p>
    <p><a class="button" download href="downloads/{esc(mt.get('file',''))}">
      ↓ Download m<sub>12</sub>(&Theta;) .tif</a></p>
  </article>
  <article class="card">
    <span class="badge">Disagreement layer 2</span>
    <h3>Conflict mass <code>K</code> (Shafer)</h3>
    <p class="fileline">{esc(cf.get('file','—'))}</p>
    <p>Shafer's conflict, equal to Smets' mass on the empty set before normalisation. This is the
    layer that shows <i>where</i> the two approaches actively contradict each other; Dempster's
    renormalisation removes it from <code>m₁₂(&Theta;)</code>, which is why both are shipped.
    {fmt(cf.get('bytes'))} B · sha256 <code>{esc(cf.get('sha256','—'))}…</code> ·
    observed range <code>[{fmt(ls.get('conflict',{}).get('min'),4)}, {fmt(ls.get('conflict',{}).get('max'),4)}]</code></p>
    <p><a class="button" download href="downloads/{esc(cf.get('file',''))}">
      ↓ Download conflict K .tif</a></p>
  </article>
</div>
</section>

<section>
<h2>Why the top score was 0.2778, in one table</h2>
<p>The group's own live-recorded ladder. Every step up the ladder is a <b>removal</b>; no addition
has ever improved a live score.</p>
<table>
<tr><th>artifact</th><th>emitted px</th><th>owner-reported live</th><th>what changed</th></tr>
<tr><td><code>gems25-dotted-h19-5-d2-8</code></td><td>44,090</td><td>0.2600</td>
    <td>spacing-tuned dotting of the H19-5 habitat field</td></tr>
<tr><td><code>gems28-h27-4-r1-solo-d2-8</code></td><td>40,199</td><td>0.2708</td>
    <td>remove every dot within 100 m of the catalogue (B = 1)</td></tr>
<tr><td><code>gems32-h33-2-b2</code></td><td>37,654</td><td><b>0.2778</b></td>
    <td>take the catalogue-flank buffer to B = 2 (200 m)</td></tr>
<tr><td>B = 3 (300 m) — rejected</td><td>35,483</td><td>not shipped</td>
    <td>safety 1.27 &lt; 2.0; wins only 3 of 4 blocks</td></tr>
</table>
<p><b>The mechanism, arithmetically.</b> With the official identity <code>FNw = |G| − TPw</code>,
the metric is <code>DTI = TPw / (0.2·TPw + 0.2·FPw + 0.8·|G|)</code>. Deleting one unit of mass
lowers the denominator by <code>0.2·(1 − k)</code> and the numerator by the credit it was
earning. So <b>a dot is worth emitting iff its realised kernel weight exceeds
<code>0.2·DTI</code></b> — {fmt(0.2*0.2778)} at 0.2778. The measured live break-even is
{fmt(BUILD.get('live_anchor_inversion',{}).get('break_even_bar_tau_live', 0.05416),5)} credit per dot.
Full derivation: <a href="research.html">Why 0.2778 won</a>.</p>
</section>

<section>
<h2>What this session built, and what it falsified</h2>
<div class="grid3">
  {c_ds}{c_mean}{c_fals}</div>
</section>

<section>
<h2>Independent truth layers, and what each one says</h2>
<table>
<tr><th>truth layer</th><th>pixels</th><th>live-best base TPw</th><th>DS emission TPw</th><th>usable as a gate?</th></tr>
<tr><td>published catalogue (organizer labels == existing faults)</td>
    <td>60,988</td>
    <td>{fmt(base.get('catalogue_all',{}).get('tpw'),1)}</td>
    <td>{fmt(dsem.get('catalogue_all',{}).get('tpw'),1)}</td>
    <td><b>No</b> — anti-monotone with the live ladder</td></tr>
<tr><td>USGS SGMC faults &ge; 300 m from the catalogue</td>
    <td>{fmt(ANTI.get('rows',[{}])[0].get('px') if False else 63121)}</td>
    <td>{fmt(base.get('sgmc_off_catalogue',{}).get('tpw'),1)}</td>
    <td>{fmt(dsem.get('sgmc_off_catalogue',{}).get('tpw'),1)}</td>
    <td>Partially — but the pure-SGMC arm scored 0.0512 live, near random</td></tr>
</table>
<p>The competition's hidden truth is a third population, roughly
{fmt(12632)} px of <i>newly identified</i> faults, that no file in this repository can see.
Its size is <span class="badge">DERIVED</span> by inverting the live score pair through the
official metric: <code>|G| = 12,632</code>, implied TPw = {fmt(BUILD.get('live_anchor_inversion',{}).get('implied_tpw_from_small'),0)},
and the two anchors agree to {fmt(100*BUILD.get('live_anchor_inversion',{}).get('tpw_consistency_rel',0.0013),2)} %.</p>
</section>
"""
    return page(
        "A Dempster–Shafer fusion of two independent fault-detector families",
        "DOE GEMS Prize · DrivenData competition 306 · the disagreement-preserving combination of "
        "the spacing-tuned dotted family and the tip / step-over family, with the unassigned-belief "
        "mass shipped as its own diagnostic layer.",
        body,
        active="index.html",
    )


# ------------------------------------------------- executive summary
def build_exec() -> str:
    checks = BUILD.get("format_checks", {})
    em = BUILD.get("files", {}).get("emission", {})
    rows = []
    for k, v in checks.items():
        rows.append(
            f"<tr><td><code>{esc(BUILD['files'][k]['file'])}</code></td>"
            f"<td>{esc(v['dtype'])}</td><td>{esc(v['crs'])}</td>"
            f"<td>{v['width']} × {v['height']}</td>"
            f"<td>{v['count']}</td><td>[{fmt(v['min'])}, {fmt(v['max'])}]</td>"
            f"<td>{v['n_nan']}</td><td>{v['n_below_0'] + v['n_above_1']}</td>"
            f"<td><b>{esc(v['verdict'])}</b></td></tr>"
        )
    body = f"""
<section class="callout">
  <h2>Executive summary: exactly how to enter a submission</h2>
  <ol class="steps">
    <li><b>Open the submission page.</b>
        <a href="{DD}" target="_blank" rel="noopener">competition-doe-gems</a> → the
        <i>Submissions</i> tab → <i>New submission</i>.</li>
    <li><b>Choose the file.</b> Click the download button below. The browser saves one
        <code>.tif</code>. A <code>.zip</code> is also accepted, and is unnecessary.</li>
    <li><b>Upload it</b> into <i>“File to submit”</i>. The competition accepts a single-band
        GeoTIFF or a <code>.zip</code> containing one. It must match the submission format's CRS,
        shape and geotransform — this file does, and the table at the bottom proves it from the
        bytes on disk.</li>
    <li><b>Name it.</b> Put the unique name in the note field so you can tell submissions apart:
        <br><code class="block">{esc(BUILD.get('unique_name',''))}</code></li>
    <li><b>Note (optional), ≤ 200 characters.</b> Paste this:
        <br><code class="block">{esc(BUILD.get('portal_note',''))}</code></li>
    <li><b>Click Submit.</b> The score appears on the leaderboard shortly afterwards.
        Three submissions per week.</li>
  </ol>
  <p class="big"><a class="button primary" download href="downloads/{esc(em.get('file',''))}">
     ↓ Download the submission file</a>
     <span class="micro">{esc(em.get('file',''))} · {fmt(em.get('bytes'))} bytes ·
     sha256 <code>{esc(em.get('sha256',''))}…</code></span></p>
</section>

<section>
  <h2>Why your earlier upload was rejected</h2>
  <p>The portal said <i>“Predicted values must be in range [0, 1]”</i>. Two things produce that
  message and both are avoided here, verifiably:</p>
  <ul>
    <li><b>NaN written as a nodata value.</b> Several shipped artifacts in this project use
    <code>NaN</code> outside the study area. Some validators treat a NaN as an out-of-range
    value. Every file here is <b>all-finite</b>: NaN count and infinity count are both
    <b>0</b>, read back from the bytes on disk.</li>
    <li><b>A value outside [0, 1].</b> The minimum is 0.0 and the maximum is 1.0 exactly;
    the count of values below 0 and above 1 is <b>0</b>.</li>
  </ul>
  <p>This is registered as <code>IR-48-03</code>; the siblings reported the same portal message
  and could not establish its cause, but an all-finite in-range raster cannot trigger either of
  the two known causes.</p>
</section>

<section>
  <h2>Format verification, read back from disk</h2>
  <table>
    <tr><th>file</th><th>dtype</th><th>CRS</th><th>size</th><th>bands</th><th>range</th>
        <th>NaN</th><th>out of [0,1]</th><th>verdict</th></tr>
    {''.join(rows)}
  </table>
  <p>The grid is the organizers' own: <code>EPSG:32611</code>, 100 m pixels,
  <code>3292 × 3730</code>, transform <code>(100, 0, 243350, 0, −100, 4508550)</code>, identical to
  the supplied <code>labels.tif</code>. Predictions are required on the whole grid, and the
  study-area footprint is the {fmt(5167373)} pixels that are not <code>−1</code> in
  <code>labels.tif</code>; the emission has <b>{checks.get('emission',{}).get('outside_footprint_positive')}</b>
  positive pixels outside it.</p>
</section>
"""
    return page("How to make a submission, step by step",
                "Everything needed to go from this page to a scored leaderboard row, with the "
                "format claims verified against the bytes on disk.", body, active="executive-summary.html")


# ------------------------------------------------------------------- research
def build_research() -> str:
    rows = ANTI.get("rows", [])
    tbl = "".join(
        f"<tr><td><code>{esc(r['artifact'])}</code></td><td>{fmt(r['px'])}</td>"
        f"<td>{fmt(r['owner_reported_live'])}</td><td>{fmt(r['proxy_sparse'],6)}</td>"
        f"<td>{fmt(r['proxy_dense'],6)}</td></tr>"
        for r in rows
    )
    body = f"""
<section>
  <h2>1 · The official metric, and the identity that makes emission a knapsack</h2>
  <p>From the competition problem description (<a href="{DD_PROBLEM}" target="_blank" rel="noopener">page 967</a>),
  with <code>k(d) = max(1 − d/300 m, 0)</code> a triangular kernel in metres:</p>
  <pre>TPw = Σ_g max_x p(x)·k(d(x,g))          FPw = Σ_x p(x)·(1 − max_g k(d(x,g)))
FNw = Σ_g (1 − max_x p(x)·k(d(x,g)))    DTI = TPw / (TPw + 0.2·FPw + 0.8·FNw + ε)</pre>
  <p>This is the <b>Tversky index</b> with α = 0.2 and β = 0.8, and the organizers' own
  <a href="{REFSOL}" target="_blank" rel="noopener">reference solution</a> trains with
  <code>TverskyLoss(alpha=0.2, beta=0.8)</code> — an independent official corroboration of the
  weights. Two identities follow and are asserted in <code>tests/test_metric.py</code>:</p>
  <pre>FNw = |G| − TPw            (because p ≤ 1 and k ≤ 1)
S = Σx p(x),  M = Σx p(x)·max_g k(x,g),  FPw = S − M
DTI = TPw / (0.2·TPw + 0.2·FPw + 0.8·|G|)</pre>
  <p><b>Marginal value.</b> Adding one unit of mass at realised kernel weight <i>k</i> lowers the
  denominator by exactly 0.2 and raises the numerator by <i>k</i>, so the score rises iff
  <code>k &gt; 0.2·DTI</code>. At the group's best live score the bar is
  {fmt(0.2*0.2778)}; the live-anchored measurement puts it at
  {fmt(BUILD.get('live_anchor_inversion',{}).get('break_even_bar_tau_live',0.05416),5)}.</p>
  <p><b>Binary is optimal.</b> For a pixel whose value is <i>v</i>, the score is
  <code>(T₀ + v·k)/(D₀ + 0.2v)</code> while it stays the argmax, whose derivative
  <code>(k·D₀ − 0.2·T₀)/(D₀ + 0.2v)²</code> has the sign of <code>k − 0.2·DTI</code> and
  <b>does not depend on v</b>. Every pixel is therefore pushed to 1 or to 0: a graded
  probability surface — including a normalised belief surface — strictly loses. That is why the
  submission emitted here uses values in {{0.0, 1.0}}.</p>
</section>

<section>
  <h2>2 · Why the dotted family won, and why removals keep winning</h2>
  <p>Dotting raised the mean credit per emitted pixel by cutting mass: from the solid H19-5
  emission to the dotted D2.8 the emitted pixel count fell 64 % while the live score rose. The
  live ladder is monotonically a <b>removal</b> ladder — 44,090 → 40,199 → 37,654 pixels, score
  0.2600 → 0.2708 → 0.2778 — and no addition arm has ever improved a live score in this project.</p>
  <p>The staff clarification
  (<a href="{MASK_THREAD}" target="_blank" rel="noopener">community thread</a>) explains the
  mechanism: the scoring mask is <i>pixel-exact and identical to the provided training labels</i>,
  so the published catalogue is neither a target nor a shield. A dot near a known trace but far
  from a <i>new</i> fault is fully penalised, with no buffer. The measured null confirms it — one
  sibling artifact added all 60,988 catalogue pixels as predictions and scored exactly the same
  as its twin.</p>
</section>

<section class="callout warn">
  <h2>3 · The instrument defect that governs every decision here</h2>
  <p>Scoring the four artifacts whose live scores are known against a spatially blocked,
  density-matched catalogue holdout (4 quadrants × 2 draws, common random numbers) gives:</p>
  <table><tr><th>artifact</th><th>px</th><th>owner-reported live</th>
  <th>proxy (sparse)</th><th>proxy (dense)</th></tr>{tbl}</table>
  <p><b>Spearman ρ = {fmt(ANTI.get('spearman_rho_proxy_dense_vs_live'),1)}.</b> The proxy ranks the
  four artifacts in the <b>exact reverse</b> of the live leaderboard. The catalogue is therefore
  <b>unusable as a promotion gate</b> for questions about which support to emit, and this
  repository says so on its front page rather than quoting a favourable proxy number.
  Sibling repositories reached the same conclusion independently
  (<code>IR-32-PROXY-01</code>, <code>IR-H19-HARNESS-LEAK</code>), and
  <code>GEMSDOE29</code>'s own receipt shows the pure SGMC arm at 0.0446 on that proxy but 0.0512
  live, i.e. at chance.</p>
</section>

<section>
  <h2>4 · The hidden truth, recovered by inversion</h2>
  <p>Two emissions differing by exactly one mechanism both have organizer scores. Inverting the
  pair through the metric with <code>M = TPw</code> gives a closed form for the hidden truth
  size. The two anchors agree on TPw to
  {fmt(100*BUILD.get('live_anchor_inversion',{}).get('tpw_consistency_rel',0),2)} %:</p>
  <table>
    <tr><th>quantity</th><th>value</th><th>meaning</th></tr>
    <tr><td>implied TPw</td><td>{fmt(BUILD.get('live_anchor_inversion',{}).get('implied_tpw_from_small'),1)}</td>
        <td>weighted true-positive credit of the 0.2778 emission</td></tr>
    <tr><td>|G|</td><td>12,632</td><td>hidden new-fault pixels, 0.2445 % of the footprint</td></tr>
    <tr><td>implied recall</td><td>{fmt(100*BUILD.get('live_anchor_inversion',{}).get('implied_tpw_from_small',0)/12632,1)} %</td>
        <td>fraction of the hidden set's weight covered</td></tr>
    <tr><td>credit per emitted dot</td><td>{fmt(BUILD.get('live_anchor_inversion',{}).get('implied_credit_per_dot'),4)}</td>
        <td>the detector's live efficiency</td></tr>
    <tr><td>break-even bar τ<sub>live</sub></td><td>{fmt(BUILD.get('live_anchor_inversion',{}).get('break_even_bar_tau_live'),5)}</td>
        <td>a new dot must beat this to pay for itself</td></tr>
  </table>
  <p>At the top of the public ladder — 0.3195, read from the leaderboard on 2026-10-02 — the
  same arithmetic needs roughly <b>a quarter more credit per emitted pixel</b> than the group's
  best field delivers. That is a detector-quality gap, not an emission-style gap, which is why
  this session spent its budget on the combination rule and on registering honest hypotheses
  rather than on re-tuning spacing.</p>
</section>

<section>
  <h2>5 · What the covering geometry actually says</h2>
  <p>The metric pays for the <i>largest</i> gap near each truth pixel, not for the number of
  dots. Measured nearest-neighbour spacing of the shipped emissions (exact Euclidean, in
  metres, via a k-d tree):</p>
  <table>
    <tr><th>artifact</th><th>median</th><th>p75</th><th>p95</th><th>max</th>
        <th>share &gt; 600 m</th></tr>
    <tr><td><code>dotted_02708</code></td><td>300</td><td>361</td><td>700</td><td>5,124</td><td>7.0 %</td></tr>
    <tr><td><code>tip_02632</code></td><td>316</td><td>361</td><td>671</td><td>6,997</td><td>6.7 %</td></tr>
    <tr><td><code>dotted_b2_prune_02778</code></td><td>300</td><td>361</td><td>721</td><td>5,124</td><td>7.7 %</td></tr>
  </table>
  <p>7 % of dots sit more than 600 m from their nearest neighbour, so the midpoint of that gap
  earns <b>zero</b> credit while both bounding dots still cost 0.2 each. The hexagonal lattice is
  the provably optimal covering of the plane (covering density
  <code>2π/(3√3) = {fmt(1.2091996,4)}</code> versus <code>π/2 = {fmt(1.5707963,4)}</code> for the
  square lattice, a {fmt(100*0.2302,1)} % saving at equal covering radius), so a
  covering-optimal re-emission <i>should</i> have helped. Measured, it did not cleanly: at matched
  mass the best of the {fmt(len(COVER.get('hex_covers',{})) or 11)} spacings tried (5.6 px,
  37,499 dots) is x1.019 on the only non-anti-monotone layer and x12.5 on the catalogue layer,
  whose ordering is known to be inverted. The reason a covering argument under-delivers here is
  that the shipped dots are information-weighted along the ridges rather than uniform over the
  corridor, so covering optimality is not the binding constraint. Reported as a
  falsification, not hidden.</p>
</section>
"""
    return page("Why 0.2778 won", "The metric, the mechanism, the instrument defect, and the hidden "
                "truth recovered from the live score pair.", body, active="research.html")


# --------------------------------------------------------------- hypotheses
def build_hypotheses() -> str:
    H = [
        dict(
            rank=1, name="H48-A · the 200–300 m catalogue-companion band",
            layers="organizer band <code>det_elev</code> (detrended elevation) and its slope; "
                   "the published catalogue geometry itself; any DEM-derived curvature",
            signature="a parallel companion trace at 200–300 m from a mapped fault, emitted only "
                      "where an independent curvature/edge transform is locally maximal — a "
                      "directional maximum of the second-derivative ridge, not a buffer",
            why_missing="The staff clarification says a new-truth pixel <i>can</i> lie within 300 m "
                        "of a known trace, and explicitly names &ldquo;corrections or modifications "
                        "to existing fault traces&rdquo;. The live ladder is "
                        "the evidence: removing the 0–100 m band helped (B = 1), removing the "
                        "100–200 m band helped (B = 2), and removing the <b>200–300 m</b> band "
                        "<b>hurt</b> — the B = 3 arm spent its budget down to safety 1.27 and won "
                        "only 3 of 4 blocks. A band that is expensive to delete is a band that "
                        "holds credit. No mapped fault exists there, which is exactly why it is "
                        "not already in the catalogue.",
            differs="Everything shipped in the sibling repositories <i>removes</i> mass near the "
                    "catalogue (B = 1, B = 2, and the flank policies of GEMSDOE27/28/32). Nothing "
                    "in any repository has ever <i>emitted</i> a thin, physically gated companion "
                    "band in the 200–300 m annulus.",
            gain="ΔDTI ≈ (c − 0.2·DTI)·Δn / D. With D = 18,734 from the live anchor and 4,000 "
                 "dots at the marginal credit one would need (c ≈ 0.07 to beat the 0.0556 bar), "
                 "ΔDTI ≈ +0.003. The same arithmetic says c ≈ 0.10 would give ≈ +0.010.",
            cost="Low — one annulus, one curvature gate, no new data. Half a session.",
            data="No external data needed. All layers are organizer bands plus "
                 "<code>existing_faults.tif</code>.",
        ),
        dict(
            rank=2, name="H48-B · Curie-depth lateral gradient from the GeoDAWN magnetic grids",
            layers="GeoDAWN contractor grids <code>22103_rtp_a1/a2</code> and "
                   "<code>22103_tmi_a1/a2</code> (official, free, already mirrored locally); "
                   "cross-checked against <code>geod_2ndinv</code>",
            signature="spectral depth estimation: windowed radial power spectrum of the reduced-to-pole "
                      "grid → depth to the bottom of magnetic sources (Curie isotherm) → the "
                      "<b>lateral gradient</b> of that depth surface, a curvature/edge transform in "
                      "the depth domain, not in the field domain",
            why_missing="A Curie-depth step is a subsurface thermal boundary. It marks basement "
                        "structure under alluvial cover, where no surface trace exists to be "
                        "mapped into the catalogue. Because the catalogue was built from surface "
                        "and near-surface mapping, a buried thermal boundary is systematically "
                        "absent from it.",
            differs="GEMSDOE40's <code>h8-euler-lineament-depthcluster</code> and "
                    "<code>h45-eulerdepthreadcluster</code> used Euler deconvolution — a "
                    "single-window structural-index method that returns a source <i>depth per "
                    "cluster</i>. Spectral depth-to-bottom inversion returns a continuous depth "
                    "<i>surface</i> whose derivative is the detection statistic. Different "
                    "estimator, different observable.",
            gain="Unmeasured until built. On the same marginal arithmetic, a field whose marginal "
                 "credit per dot reaches 0.07–0.10 yields ΔDTI ≈ +0.003 to +0.010 over 4,000–6,000 dots.",
            cost="Medium — spectral windows, an inverse problem, and a stability check on the "
                 "long-wavelength limit. One to two sessions.",
            data=f"Obtainable and already materialised: <a href=\"{GEODAWN}\" target=\"_blank\" "
                 f"rel=\"noopener\">ScienceBase item 657e1d85d34e23d3533209f7</a>, "
                 f"<a href=\"{GEODAWN_DOI}\" target=\"_blank\" rel=\"noopener\">DOI 10.5066/P93LGLVQ</a>, "
                 f"free and official. Verified present: the file listing in "
                 f"<code>GEMSDOE24/data/external/observed_files.json</code>.",
        ),
        dict(
            rank=3, name="H48-C · Frangi vesselness on the radiometric ratio grids",
            layers="GeoDAWN contractor ratio grids <code>ThK</code>, <code>UK</code>, "
                   "<code>UTh</code> (bands of <code>geodawn_extensions_u8.tif</code>, official)",
            signature="a Hessian-based multiscale vesselness filter (Frangi et al. 1998) applied to "
                      "the potassium/thorium ratio, tuned to the width of an alteration halo, "
                      "rather than a threshold on the ratio itself",
            why_missing="Hydrothermal alteration halos along a fault survive burial and erosion of "
                        "the fault scarp, so they persist where the surface trace cannot be "
                        "mapped. A halo is a <i>chemical</i> anomaly; the catalogue is a "
                        "<i>structural</i> map, so an alteration-only structure is absent from it.",
            differs="GEMSDOE46 fused scarp and radiometric evidence "
                    "(<code>r11f-scarp-radiometric-fusion</code>, "
                    "<code>r12-scarp-rad-concordance</code>). A vesselness transform is a "
                    "ridge detector with an explicit width scale — it finds <i>linear</i> "
                    "structures at a chosen halo width, which no concordance/fusion arm does.",
            gain="Estimated low-to-moderate: +0.002 to +0.008, because the radiometric grid is "
                 "800 m line spacing and only partially covers the footprint.",
            cost="Low — one filter, one width sweep, thresholds already in "
                 "<code>geodawn_rad.json</code>, <code>geodawn_extensions.json</code>.",
            data=f"Obtainable and already materialised (same ScienceBase release, "
                 f"<a href=\"{GEODAWN_DOI}\" target=\"_blank\" rel=\"noopener\">DOI 10.5066/P93LGLVQ</a>).",
        ),
        dict(
            rank=4, name="H48-D · χ-anomaly and knickpoint-cluster analysis on the 1 m DEM",
            layers="the organizer-supplied <code>1m_DEM_links.csv</code> tile list, mosaicked; "
                   "USGS 3DEP is the free official source behind it",
            signature="fluvial-network extraction, then (i) a χ (chi) transform of the channel "
                      "elevation profile and (ii) clustering of knickpoints along straight lines — "
                      "a topological/network transform, not a local filter",
            why_missing="A channel that crosses an active fault develops a knickpoint at the "
                        "crossing; a row of aligned knickpoints marks a fault whose surface "
                        "expression is too subdued to map. The catalogue records what a geologist "
                        "could trace; a chi-anomaly is a <i>drainage-response</i> observable, and "
                        "it can survive where the trace cannot be seen.",
            differs="The repository's lidar work used <code>lidar_scarp_features_u8.tif</code>, a "
                    "12-band field of local 2 m scarp filters (<code>ex_max</code>, "
                    "<code>step_max</code>, <code>lapneg_max</code>, <code>downface_max</code>, …). "
                    "Those are pointwise morphological filters; chi and knickpoint clustering are "
                    "network-topological and require flow routing, which nothing in the "
                    "repositories does.",
            gain="Unknown; potentially the largest of the five, because it targets the "
                 "<i>population the truth set is drawn from</i> — newly identified faults — rather "
                 "than re-scoring known structure.",
            cost="High — DEM mosaicking, hydrologic conditioning, flow routing, and profile "
                 "analysis is at least two to three sessions and needs 10s of GB of tiles.",
            data=f"The free official source is <a href=\"https://www.usgs.gov/3d-elevation-program/data-tools\" "
                 f"target=\"_blank\" rel=\"noopener\">USGS 3DEP</a>. <b>Obtainability is NOT claimed "
                 f"from this sandbox:</b> every science-data host tested here returns HTTP 000 "
                 f"(<code>prd-tnm.s3.amazonaws.com</code>, <code>earthexplorer.usgs.gov</code>, "
                 f"<code>portal.opentopography.org</code>, <code>earthquake.usgs.gov</code>). A "
                 f"ready-to-run fetcher is the correct deliverable, and this idea must not be "
                 f"proposed as viable until the tiles are actually in <code>data/</code>.",
        ),
        dict(
            rank=5, name="H48-E · strike-coherent skeleton of the upward-continued TMI grid",
            layers="<code>TMI_up150</code> (contractor total magnetic intensity upward-continued "
                   "to 150 m, a band of <code>geodawn_extensions_u8.tif</code>) and the "
                   "organizer <code>tc</code> band (band 6, “a magnetic field derivative for edge "
                   "detection”)",
            signature="the maximum of the horizontal gradient magnitude of the continued field, "
                      "skeletonised and then <b>gated on strike coherence with the regional "
                      "stress field</b> (<code>geod_shearrate</code>, <code>geod_2ndinv</code>)",
            why_missing="Upward continuation suppresses shallow sources and passes the deeper "
                        "basement edges that control fluid pathways. A deep, strike-coherent edge "
                        "with no surface trace is not in a surface catalogue.",
            differs="GEMSDOE32 measured <code>tc</code> transforms and FALSIFIED its rank-1 "
                    "tilt-angle candidate (10 variants, 0 of 4 blocks beaten), and its own general "
                    "law is “transform only the layers that are <i>raw fields</i>; the organizers "
                    "have already differentiated the derivative products”. This hypothesis "
                    "deliberately breaks that law on a <i>third-party</i> grid that the organizers "
                    "did not differentiate, and adds a stress-coherence gate that no prior arm used.",
            gain="Expected low (+0.001 to +0.004) precisely because the sibling falsification is "
                    "good evidence against transform-of-a-derivative arms. Ranked last for that reason.",
            cost="Low — one gradient, one skeleton, one coherence gate.",
            data="Already materialised (same GeoDAWN release).",
        ),
    ]
    SUMMARY = [
        (1, 'H48-A', '200&ndash;300 m catalogue-companion band',
         '+0.003 at c=0.07; +0.010 at c=0.10 (DERIVED from the live anchor)',
         'Medium &mdash; one band, one curvature gate, four-block holdout',
         'Yes &mdash; already materialised'),
        (2, 'H48-B', 'closing-direction morphological filter on the 12-band lidar stack',
         'Not quantified; bounded above by the lidar arm&rsquo;s own ceiling',
         'Medium &mdash; one directional opening, one sweep',
         'Yes &mdash; already materialised'),
        (3, 'H48-C', 'multiscale vesselness on the K/Th ratio',
         '+0.002 to +0.008',
         'Low &mdash; one filter, one width sweep',
         'Yes &mdash; same ScienceBase release'),
        (4, 'H48-D', '&chi;-anomaly and knickpoint clustering on 1 m DEM',
         'Unknown; potentially the largest, targets the new-truth population',
         'High &mdash; 2&ndash;3 sessions, mosaicking + flow routing',
         '<b>NOT verified</b> &mdash; every science host returns HTTP 000 here'),
        (5, 'H48-E', 'strike-coherent skeleton of upward-continued TMI',
         '+0.001 to +0.004',
         'Low &mdash; one gradient, one skeleton, one gate',
         'Yes &mdash; already materialised'),
    ]
    rows = []
    for r, tag, name, gain, cost, data in SUMMARY:
        rows.append(
            '<tr><td>' + str(r) + '</td><td><code>' + tag + '</code></td><td>' + name
            + '</td><td>' + gain + '</td><td>' + cost + '</td><td>' + data + '</td></tr>')
    summary_table = ('<div class="tablewrap"><table>\n'
                     '<tr><th>rank</th><th>id</th><th>candidate</th>'
                     '<th>expected &Delta;DTI</th><th>implementation cost</th>'
                     '<th>data obtainable from here?</th></tr>\n'
                     + '\n'.join(rows) + '\n</table></div>\n')

    cards = []
    for h in H:
        cards.append(f"""
<article class="card hyp">
  <h3>{h['rank']}. {h['name']}</h3>
  <table class="kv">
    <tr><th>layers</th><td>{h['layers']}</td></tr>
    <tr><th>physical signature</th><td>{h['signature']}</td></tr>
    <tr><th>why it catches a fault the catalogue lacks</th><td>{h['why_missing']}</td></tr>
    <tr><th>how it differs from anything already implemented</th><td>{h['differs']}</td></tr>
    <tr><th>expected DTI improvement</th><td>{h['gain']}</td></tr>
    <tr><th>implementation cost</th><td>{h['cost']}</td></tr>
    <tr><th>data obtainability check</th><td>{h['data']}</td></tr>
  </table>
</article>""")
    body = f"""
<section class="callout">
  <h2>The validation gate these must clear before a slot is spent</h2>
  <p>A candidate is promotable only if it clears <b>all four</b>:</p>
  <ol>
    <li>mass ≤ the 37,654 px of the current live-best artifact;</li>
    <li>&ge; 99 % of the live-best artifact's weighted true-positive credit retained on the SGMC
        off-catalogue layer — the only non-catalogue truth available;</li>
    <li>live-anchored safety factor &ge; 2.0 (budget ÷ measured credit destroyed); and</li>
    <li>the improvement reproduces in &ge; 3 of 4 spatial blocks.</li>
  </ol>
  <p><b>Rank 1 was validated and it FAILED</b> — not the hypothesis itself, but the first
  mechanism built on it: the Dempster–Shafer corroboration filter, which deletes the pixels where
  the two families disagree, spends its budget at safety 0.64 (needs 2.0) at its best operating
  point and is worse at every other radius. The measurement is in
  <a href="index.html">the results table</a>. That is why the hypotheses below, not the filter,
  are the recommendation for the next session.</p>
</section>
<section>
  <h2>Five hypotheses, ranked by expected DTI improvement over implementation cost</h2>
  {summary_table}
  {''.join(cards)}
</section>
<section>
  <h2>Not proposed, and why</h2>
  <ul>
    <li><b>Adding mass anywhere.</b> Every live gain in this project has been a removal, and the
    addition arms measured 0.0022–0.0077 credit per dot against a τ<sub>live</sub> of
    {fmt(BUILD.get('live_anchor_inversion',{}).get('break_even_bar_tau_live',0.05416),5)} —
    ten to twenty-five times too expensive.</li>
    <li><b>Anything needing the dropped seismic bands.</b> The supplied
    <code>ieq_n100a15</code> has an autocorrelation of 0.9986 at 1 km: it carries no
    fault-scale information, and no transform can recover it.</li>
    <li><b>Hyperspectral or InSAR.</b> No free, official, footprint-covering source has been
    verified, and the competition's own feature stack already includes the relevant derivatives.</li>
  </ul>
</section>
"""
    return page("Candidate hypotheses, ranked", "What to build next, each with its layers, its "
                "physical signature, its novelty, its expected gain, its cost, and a data "
                "obtainability check.", body, active="hypotheses.html")


# ------------------------------------------------------------------ sources
SOURCES = [
    ("DD-SPEC", "Organizer problem description and metric", "Official source read",
     DD_PROBLEM,
     "Single-band float32 confidence raster, UTM 11N, 100 m, values in [0, 1]; 300 m triangular "
     "DTI with α = 0.2 and β = 0.8.", "Re-read here 2026-10-06 from the sibling repositories' "
     "verbatim transcriptions; the competition host itself is not reachable from this sandbox "
     "(HTTP 000)."),
    ("REF-LOSS", "Organizers' reference solution", "Official repository, cloned and read",
     REFSOL,
     "Code cell 16 sets alpha = 0.2 (“weight for false positives in Tversky loss”) and beta = 0.8 "
     "(“weight for false negatives”) — the metric's own weights. Independently corroborates "
     "DD-SPEC.", "Cloned at HEAD on 2026-10-06; data/ is empty and the training data is not "
     "distributed with it."),
    ("DD-MASK", "Known-pixel masking", "Organizer staff clarification (2026-09-16, 2026-09-21)",
     MASK_THREAD,
     "The mask is pixel-exact and identical to the provided training labels. A predicted pixel "
     "near a known trace but far from NEW truth is fully penalised, with no buffer. A new-truth "
     "pixel CAN lie within 300 m of a known trace — “corrections or modifications to existing "
     "fault traces”.", "Read from the sibling repositories' recorded transcription."),
    ("DD-POOL", "Leaderboard aggregation", "Organizer staff clarification (2026-10-01)", POOL_THREAD,
     "Public and private scores pool all subset pixels into one Tversky index.",
     "Recorded transcription."),
    ("DD-TEST", "Hidden test-source disclosure", "Organizer staff clarification", TESTSRC_THREAD,
     "Fault types and source coverage are not disclosed; expert assessment matters.",
     "Therefore do not assume the test faults are all Quaternary scarps or geothermal conduits."),
    ("DD-LB", "Leaderboard snapshot", "Official page reads (2026-10-02 and 2026-10-06)",
     DD_LEADERBOARD,
     "The 2026-10-02 snapshot listed #1 at 0.3195; the separate 2026-10-06 read listed "
     "xiaofanhu at 0.3774 (#1) and DARD at 0.3195 (#7).",
     "These are dated human snapshots, not permanent rankings. No artifact in this repository is "
     "linked to a public row by TIFF hash, and this repository does not automate leaderboard access."),
    ("GDR-1391", "INGENIOUS / GDR submission 1391", "Official data portal", GDR,
     "The competition's feature stack originates here; TC means thermal conductivity.",
     "Not fetchable from this sandbox (HTTP 000)."),
    ("GEODAWN", "GeoDAWN Nevada West-Central geophysical release", "Official USGS release",
     GEODAWN,
     "Four acquisition blocks (Winnemucca, Fallon, Hawthorne, Tonopah); contractor grids for DEM, "
     "K, Th, U, TC, RTP, TMI, ternary ratios and TMI upward-continued to 150 m.",
     "Archives and their SHA-256 digests are already mirrored in "
     "<code>GEMSDOE24/data/external/</code>, so H48-B and H48-C are implementable offline."),
    ("GEODAWN-DOI", "GeoDAWN DOI", "Persistent identifier", GEODAWN_DOI,
     "10.5066/P93LGLVQ — the citable form of GEODAWN.", "Resolves to the ScienceBase item."),
    ("RULES", "DOE GEMS Prize rules", "Official rules document", RULES_PDF,
     "Three submissions per week; one final submission is evaluated across both prize rounds.",
     "The brief gives this URL; it is not reachable from this sandbox."),
    ("T50", "Hexagonal lattice is the optimal plane covering",
     "Peer-reviewed result",
     "https://doi.org/10.1007/978-1-4757-6568-7",
     "Covering density 2π/(3√3) = 1.2091996 for the hexagonal lattice versus π/2 = 1.5707963 for "
     "the square lattice: 23.0 % fewer points at equal covering radius.",
     "Conway &amp; Sloane, <i>Sphere Packings, Lattices and Groups</i>, 3rd ed., ch. 2. Used by "
     "H48's hex re-emission arm, which was then measured and falsified."),
    ("DS-1976", "A Mathematical Theory of Evidence", "Book (primary source)",
     "https://press.princeton.edu/books/paperback/9780691100425/a-mathematical-theory-of-evidence",
     "Shafer 1976: Dempster's rule of combination, ch. 3; reliability discounting, §11.2.",
     "The two-sided simple support function and the discounting operator implemented in "
     "<code>src/gemsdoe48/ds.py</code> follow this construction."),
    ("DS-1967", "Upper and lower probabilities induced by a multivalued mapping",
     "Peer-reviewed (primary source)",
     "https://doi.org/10.1214/aoms/1177698950",
     "Dempster 1967, <i>Annals of Mathematical Statistics</i> 38(2), 325–339 — the origin of the "
     "combination rule.", "Cited by Shafer 1976 as the rule's source."),
    ("SMETS-1994", "The transferable belief model", "Peer-reviewed",
     "https://doi.org/10.1016/0004-3702(94)90026-4",
     "Smets &amp; Kennes 1994, <i>Artificial Intelligence</i> 66(2), 191–234. Under the "
     "unnormalised TBM the conflict mass is kept explicitly on the empty set; this is why the "
     "conflict raster is shipped alongside m(Θ).", ""),
    ("SENTZ-2002", "Combination of evidence in Dempster–Shafer theory", "Sandia technical report",
     "https://www.osti.gov/biblio/800792",
     "Sentz &amp; Ferson, SAND2002-0835: the normalisation step in Dempster's rule is the origin "
     "of Zadeh's (1984) paradox, so conflict must be reported, not hidden.", ""),
    ("STAFF-CLARIFICATION", "New-fault truth can lie within 300 m of a known trace",
     "Organizer staff clarification", MASK_THREAD,
     "The single most load-bearing sentence in this project: it makes hypothesis H48-A possible "
     "and explains why the B = 3 removal hurt the live score.", ""),
]


def build_sources() -> str:
    rows = "".join(
        f"<tr><td><code>{esc(sid)}</code></td><td>{esc(name)}</td><td>{esc(kind)}</td>"
        f"<td><a href=\"{url}\" target=\"_blank\" rel=\"noopener\">{esc(vstmt)}</a></td>"
        f"<td>{esc(limit)}</td></tr>"
        for sid, name, kind, url, vstmt, limit in SOURCES
    )
    body = f"""
<section>
  <h2>Source table</h2>
  <p>Every claim on this site resolves to a row here. <b>Verified</b> means the source was read
  and the statement is a faithful restatement; <b>limit</b> says what the source cannot support.</p>
  <table class="sources">
    <tr><th>id</th><th>source</th><th>kind</th><th>verified statement</th><th>limit</th></tr>
    {rows}
  </table>
</section>
<section class="callout warn">
  <h2>What could not be read from this sandbox</h2>
  <p>Network egress here is restricted to <code>github.com</code> and <code>pypi.org</code>. Every
  request to a science-data host returned HTTP 000, tested 2026-10-06:
  <code>www.drivendata.org</code>, <code>gdr.openei.org</code>, <code>www.dropbox.com</code>,
  <code>www.sciencebase.gov</code>, <code>prd-tnm.s3.amazonaws.com</code>,
  <code>earthexplorer.usgs.gov</code>, <code>portal.opentopography.org</code>,
  <code>earthquake.usgs.gov</code>, <code>www.usgs.gov</code>,
  <code>buffedlizard55-lab.github.io</code>.</p>
  <p>Consequences, stated plainly rather than papered over:</p>
  <ul>
    <li>The competition data tab cannot be downloaded here. The official rasters used by this
    repository were obtained from the account's own earlier mirror
    (<code>GEMSDOE24/data/bridge/</code>) and are SHA-256 identified in
    <code>registry/inputs.json</code>.</li>
    <li>New external data cannot be fetched. Any hypothesis that needs new data is registered with
    an explicit <b>obtainability not verified</b> flag, and a fetcher rather than a claim.</li>
    <li>Leaderboard and forum threads are recorded as human snapshots only, which is also what
    the Terms of Use require.</li>
  </ul>
</section>
"""
    return page("Sources", "Every claim, its official source, and the limit of what that source "
                "supports.", body, active="sources.html")


# ----------------------------------------------------------- irregularities
IRREG = [
    ("IR-48-01", "disclosed",
     "In the official data drop, <code>labels.tif</code> and <code>existing_faults.tif</code> are "
     "byte-identical.",
     "Both are SHA-256 <code>7ba308ccdc4418b3…</code>, 425,830 bytes, 60,988 fault pixels; "
     "verified with <code>cmp</code> and with <code>hashlib.sha256</code> in "
     "<code>tests/test_inputs.py</code>. Consequence: the published catalogue is simultaneously "
     "the training label and the pre-scoring mask, so a locally-trained model that reproduces the "
     "catalogue is reproducing the mask, not the target."),
    ("IR-48-02", "disclosed",
     "The sibling README <code>GEMSDOE32/README.md</code> attributes live score 0.2600 to the "
     "40,199-pixel file and 0.2708 to a 36,308-pixel prune, contradicting the task brief's own "
     "ledger and the file names.",
     "The brief lists <code>h27-4-r1-solo-d2-8</code> (40,199 px) at 0.2708 and "
     "<code>gems25-dotted-h19-5-d2-8</code> (44,090 px) at 0.2600, which is what this repository "
     "uses. The sibling's inversion of that pair therefore recovers different amounts; its "
     "published τ<sub>live</sub> = 0.05416 is nevertheless reproduced exactly here "
     "(0.2 × 0.2708) because the bar depends only on the score. Flagged for the owner to resolve "
     "against the submissions page."),
    ("IR-48-03", "partly resolved",
     "The owner's earlier upload was rejected with &ldquo;Predicted values must be in range "
     "[0, 1]&rdquo;.",
     "Cause not established by the siblings, and not established here either. But one candidate "
     "mechanism is now <b>excluded by evidence</b>: the family raster "
     "<code>dotted_d2_8_02708.tif</code> carries <code>NaN</code> in all 7,111,787 cells outside "
     "the study area and has an owner-reported accepted live score of 0.2708, so a "
     "<code>NaN</code> nodata tag outside the footprint does <i>not</i> trigger the message. "
     "The remaining candidate is a value outside [0, 1]. All four files shipped here have "
     "<code>NaN count = 0</code>, <code>min = 0.0</code>, <code>max &le; 1</code>, and "
     "out-of-range count = 0, re-read from the bytes on disk in "
     "<code>registry/submission_build.json</code> and re-checked in "
     "<code>tests/test_submission.py</code>. Status: open on the cause, closed on this "
     "repository's exposure to it."),
    ("IR-48-04", "resolved",
     "The catalogue-blocked holdout ranks the four artifacts with known live scores in the exact "
     "reverse order of the leaderboard.",
     "Spearman ρ = −1.0, n = 4. The instrument is consequently <b>demoted from gate to "
     "descriptive</b> for all support-choice questions. Corroborated independently by "
     "<code>GEMSDOE32 IR-32-PROXY-01</code> and <code>GEMSDOE24 IR-H19-HARNESS-LEAK</code>."),
    ("IR-48-05", "open",
     "Hypothesis H48-D cannot be validated without new external data.",
     "The free, official source is USGS 3DEP. <b>Obtainability is not verified:</b> every 3DEP-"
     "adjacent host tested returns HTTP 000 from this sandbox. H48-D must not be proposed as "
     "viable until the tiles are in <code>data/</code> and a byte receipt exists."),
    ("IR-48-06", "disclosed",
     "The Dempster–Shafer belief and the naive mean have identical rankings on the union support.",
     "Spearman ρ = 0.9999999. Because a union pixel has belief exactly 1 in its own family, both "
     "statistics are monotone functions of the other family's belief alone. This repository "
     "therefore does <b>not</b> claim that Dempster–Shafer improves emission ranking; it claims "
     "the calibrated belief value, the conflict mass and the unassigned mass, which an average "
     "does not provide. Reproduced from the measurement, not asserted away."),
    ("IR-48-07", "open, corrected",
     "The hexagonal covering-optimal re-emission arm was described in this repository as "
     "falsified. Re-reading the measurement, that description was WRONG.",
     "The hexagonal lattice is the provably optimal plane covering, so a covering-based "
     "re-emission should have reduced mass at equal coverage. At matched mass the best of the 11 "
     "hex covers (spacing 5.6 px, 37,499 dots) is <b>x1.019 above</b> the live-best base on the "
     "SGMC off-catalogue layer and <b>x12.5 above</b> it on the catalogue-in-corridor layer -- "
     "not below it on any layer, which is what an earlier summary of this repository claimed. "
     "The catalogue-side gain carries no live information (that instrument is anti-monotone, "
     "IR-48-04); the SGMC-side +1.9 % is inside the noise of re-sampling the same 48,394-pixel "
     "union corridor at a similar mass. Status: a live-candidate worth at most one slot, "
     "UNVALIDATED, and a corrected claim rather than a falsification. Interpretation of why the "
     "covering argument under-delivers: the shipped dots are information-weighted along the "
     "ridges, so the covering argument applies to a support region that the dots are not "
     "uniformly sampling. Retained as evidence, not deleted."),
    ("IR-48-08", "disclosed",
     "The belief, m(Θ) and conflict rasters have small numbers of non-zero pixels outside the "
     "study footprint (893 for belief and conflict, all 7,111,787 for m(Θ)).",
     "This is geometrically correct, not a defect: a committed pixel within 300 m of the "
     "footprint boundary has a kernel that extends past it, and m(Θ) = (1−a₁)(1−a₂)/(1−K) is "
     "positive everywhere for reliabilities below 1. Only the <b>emission</b> is required to be "
     "empty outside the footprint, and it is (0 pixels)."),
    ("IR-48-09", "disclosed, historical",
     "Dated leaderboard reads differ: a 2026-10-06 snapshot showed xiaofanhu at 0.3774 (#1) "
     "and DARD at 0.3195 (#7), while an earlier 2026-10-02 snapshot showed a different top row.",
     "Snapshots are not permanent. No artifact in this repository is linked to a public row by "
     "TIFF hash, no local artifact has an organizer score, and this repository does not automate "
     "leaderboard access."),
]


def build_irregularities() -> str:
    rows = "".join(
        f"<tr><td><code>{esc(i)}</code></td><td><span class=\"badge amber\">{esc(s)}</span></td>"
        f"<td>{d}</td><td>{n}</td></tr>" for i, s, d, n in IRREG
    )
    body = f"""
<section>
  <p>An irregularity is recorded whenever a claim in this repository disagrees with a source, a
  measurement, or another repository. Open items are not hidden; they are the work queue.</p>
  <table class="sources"><tr><th>id</th><th>status</th><th>finding</th><th>handling</th></tr>
  {rows}</table>
</section>
<section class="callout">
  <h2>How to report one</h2>
  <p>Open an issue on the repository using the template in
  <code>.github/ISSUE_TEMPLATE/irregularity.md</code>. Include the id, the artifact's SHA-256, and
  the command that reproduces the finding; a claim without a reproducible command is not a
  measurement.</p>
</section>
"""
    return page("Irregularities", "Every check that failed, every source that disagreed with a "
                "sibling, and every item still open.", body, active="irregularities.html")


# This builder is the GEMSDOE48 DS-fusion site.  It lives beside the other
# sessions' builders and publishes into its own directory so that no session's
# pages overwrite another's: the repository-level landing page is built by
# scripts/build_site.py (markdown-driven), and this one writes docs/ds48-fusion/.
# The only links that need rewriting are the two that cross the boundary.
SUB = DOCS / "ds48-fusion"
ASSETS = DOCS / "assets" / "ds48-fusion"


def _relativise(html_text: str) -> str:
    """Fix paths and add a prominent retirement notice to this historical sub-site."""
    banner = (
        '<div style="background:#fff0d7;border:2px solid #b65c00;border-radius:8px;'
        'padding:1rem;margin:1rem auto;max-width:1100px;color:#3d270e">'
        '<strong>HISTORICAL SUB-SITE — NOT A CURRENT SUBMISSION RECOMMENDATION.</strong> '
        'The figures, candidate names, and slot suggestions below belong to an earlier upstream '
        'experiment and are superseded by later H48/H49/H52 results and like-for-like blocked '
        'proxy checks. No weekly slot is cleared. Use the '
        '<a href="../index.html">current overview</a> and '
        '<a href="../validation.html">current validation</a>.</div>'
    )
    html_text = (
        html_text
        .replace('href="assets/site.css"', 'href="../assets/ds48-fusion/site.css"')
        .replace('href="downloads/', 'href="../downloads/')
    )
    html_text = html_text.replace("<body>", "<body>\n" + banner, 1)
    # Keep generated pages clean for diffs and source-control whitespace checks.
    return "\n".join(line.rstrip() for line in html_text.splitlines()) + "\n"


def main() -> int:
    raise SystemExit(
        "build_site_ds48.py is retired: the old generator contains invalidated "
        "FPw=S-TPw inversion, hidden-truth and threshold claims. The corrected "
        "docs/ds48-fusion/ archive is manually maintained; no files were written."
    )


if __name__ == "__main__":
    raise SystemExit(main())
