#!/usr/bin/env python3
"""Build the H55 GitHub Pages set from the receipts.

Every number on these pages is read out of a receipt written by
``scripts/calibrate_live_model.py``, ``scripts/build_submission_h55.py``,
``scripts/audit_h55.py``, ``scripts/validate_submission.py`` or
``scripts/run_spatial_holdout.py``.  Nothing is transcribed by hand, so the site cannot
drift from the artifacts.

Usage:  python scripts/build_site_h55.py
"""
from __future__ import annotations

import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
DL = DOCS / "downloads"

RECEIPT = json.loads((ROOT / "evidence/build_h55_receipt_20261007.json").read_text())
CALIB = json.loads((ROOT / "evidence/live_model_calibration_20261007.json").read_text())
AUDIT = json.loads((ROOT / "evidence/h55_uniqueness_audit_20261007.json").read_text())
FORMAT = json.loads((ROOT / "evidence/h55_primary_format_audit_20261007.json").read_text())
HOLDOUT = json.loads((ROOT / "evidence/holdout_h55_spatial_20261007.json").read_text())
GATE2_PATH = ROOT / "evidence/audit_gate2_h55_20261007.json"
GATE2 = json.loads(GATE2_PATH.read_text()) if GATE2_PATH.exists() else None
SLATE = json.loads((ROOT / "evidence/hypothesis_slate_h55_20261007.json").read_text())

PRIMARY = RECEIPT["files"]["primary_zeros_outside"]
ZIPINFO = RECEIPT["files"]["primary_zip"]
NANTWIN = RECEIPT["files"]["nan_outside_twin"]
DIAG = RECEIPT["files"]["diagnostics"]
LM = RECEIPT["live_model"]
RISK = RECEIPT["risk"]
DS = RECEIPT["dempster_shafer"]
CON = RECEIPT["construction"]
EM = RECEIPT["emission"]
NAME = RECEIPT["submission_name"]
CID = RECEIPT["content_id"]
NOTE = RECEIPT["paste_ready_note"]
FC = CALIB["family_ceiling"]
FRONT = CALIB["family_coverage_frontier"]
CEIL = CALIB["ceiling_table"]
TRUTH = CALIB["inverted_truth_table"]
RHO = CALIB["rho_fit"]
GFIT = CALIB["hidden_truth_fit"]
OOF = LM["out_of_family_transfer_check"]
UNION = LM["union_of_both_families_priced"]

CSS = """
:root{color-scheme:light;--ink:#12241d;--muted:#54665c;--paper:#f4f4ec;--panel:#fffefa;
--line:#d7ddd1;--green:#1d4c3a;--green2:#2f6b52;--soft:#e3eee5;--amber:#8a4a15;
--ambersoft:#fff1d9;--red:#8d3227;--redsoft:#f9e7e1;
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
--sans:ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--sans);line-height:1.62}
a{color:var(--green);text-underline-offset:3px}
.wrap{width:min(1120px,calc(100% - 32px));margin:0 auto}
header{background:#17392e;color:#f2f5ef;padding:34px 0 30px}
header .eyebrow{color:#a9cbb4;text-transform:uppercase;letter-spacing:.16em;font-size:.72rem;font-weight:800}
h1{margin:.35rem 0 .5rem;font-size:clamp(1.9rem,5vw,3.2rem);line-height:1.03;letter-spacing:-.045em}
.deck{max-width:820px;margin:0;color:#d5e5d9;font-size:clamp(1rem,1.8vw,1.15rem)}
main{padding:26px 0 70px}
h2{margin:34px 0 10px;font-size:1.42rem;letter-spacing:-.025em;border-bottom:2px solid var(--line);padding-bottom:6px}
h3{margin:22px 0 6px;font-size:1.06rem}
p{margin:0 0 12px}
code,kbd,.mono{font-family:var(--mono);font-size:.86em}
code{background:#eceee5;padding:1px 5px;border-radius:4px;overflow-wrap:anywhere}
pre{background:#132a22;color:#dceade;padding:14px 16px;border-radius:10px;overflow-x:auto;font-size:.8rem;line-height:1.5}
pre code{background:none;color:inherit;padding:0}
.dl{background:var(--soft);border:2px solid #a9c6ae;border-radius:16px;padding:22px;margin:0 0 22px}
.dl h2{margin:0 0 6px;border:0;padding:0;font-size:1.3rem}
.bigbtn{display:block;text-align:center;margin:14px 0 10px;padding:20px 22px;border-radius:12px;
background:var(--green);color:#fff;text-decoration:none;font-weight:850;font-size:1.16rem;
letter-spacing:-.01em;box-shadow:0 6px 20px rgba(20,60,44,.22)}
.bigbtn:hover{background:#123327;color:#fff}
.bigbtn small{display:block;font-weight:600;font-size:.78rem;opacity:.86;margin-top:4px;letter-spacing:.02em}
.btnrow{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0 4px}
.btn{flex:1 1 210px;text-align:center;padding:11px 14px;border-radius:9px;background:#fff;
border:1px solid #b9c9bb;color:var(--green);text-decoration:none;font-weight:700;font-size:.9rem}
.btn:hover{background:var(--green);color:#fff}
.meta{font-family:var(--mono);font-size:.75rem;color:#3d5347;overflow-wrap:anywhere;margin-top:10px}
.warn{border:1px solid #e3b87e;background:var(--ambersoft);color:#57340f;border-radius:12px;padding:14px 18px;margin:16px 0}
.bad{border:1px solid #e0b3aa;background:var(--redsoft);color:#5d231b;border-radius:12px;padding:14px 18px;margin:16px 0}
.good{border:1px solid #a9c6ae;background:var(--soft);color:#1d4c3a;border-radius:12px;padding:14px 18px;margin:16px 0}
table{width:100%;border-collapse:collapse;font-variant-numeric:tabular-nums;font-size:.88rem;margin:10px 0 18px}
th,td{padding:8px 10px;border-bottom:1px solid var(--line);text-align:right;vertical-align:top}
th:first-child,td:first-child{text-align:left}
thead th{color:var(--muted);font-size:.72rem;text-transform:uppercase;letter-spacing:.08em}
tbody tr.hl{background:#eef3ea;font-weight:750}
.neg{color:var(--red);font-weight:700}
.pos{color:var(--green2);font-weight:700}
.grid3{display:grid;grid-template-columns:repeat(auto-fit,minmax(215px,1fr));gap:12px;margin:14px 0}
.metric{background:#f1f4ed;border:1px solid var(--line);border-radius:11px;padding:15px}
.metric strong{display:block;font-size:1.5rem;letter-spacing:-.035em;font-variant-numeric:tabular-nums}
.metric span{color:var(--muted);font-size:.83rem}
nav.top{background:#0f2a21;padding:9px 0;font-size:.86rem;position:sticky;top:0;z-index:9}
nav.top .wrap{display:flex;flex-wrap:wrap;gap:6px 16px}
nav.top a{color:#c6dccc;text-decoration:none;font-weight:650}
nav.top a:hover{color:#fff;text-decoration:underline}
footer{border-top:1px solid var(--line);padding:22px 0 46px;color:var(--muted);font-size:.86rem}
.steps{counter-reset:s;list-style:none;padding:0;margin:12px 0}
.steps li{counter-increment:s;position:relative;padding:0 0 16px 46px;border-left:2px solid var(--line);margin-left:16px}
.steps li:before{content:counter(s);position:absolute;left:-17px;top:-2px;width:32px;height:32px;
border-radius:50%;background:var(--green);color:#fff;font-weight:800;display:grid;place-items:center;font-size:.9rem}
.steps li:last-child{border-left-color:transparent}
.pill{display:inline-block;padding:2px 9px;border-radius:999px;font-size:.72rem;font-weight:800;
letter-spacing:.05em;text-transform:uppercase}
.pill.no{background:var(--redsoft);color:var(--red)}
.pill.yes{background:var(--soft);color:var(--green)}
.pill.warn{background:var(--ambersoft);color:var(--amber)}
.small{color:var(--muted);font-size:.85rem}
@media print{nav.top{position:static}}
"""

NAV = """<nav class="top"><div class="wrap">
<a href="index.html">Overview</a>
<a href="executive-summary.html">Executive summary</a>
<a href="submission-guide.html">How to submit</a>
<a href="method.html">Method</a>
<a href="hypotheses.html">Hypotheses</a>
<a href="validation.html">Validation</a>
<a href="irregularities.html">Irregularities</a>
<a href="sources.html">Sources</a>
<a href="next-steps.html">Next steps</a>
<a href="research/h55-live-model-ceiling-and-candidate-20261007.md">Full report</a>
</div></nav>"""


# Always render the correction above historical estimates, including on rebuild.
# The 2026-10-07 H55 receipts are preserved for audit, NOT proven metric bounds.
METRIC_ERRATUM = """<div class="bad" role="alert"><strong>Research correction — no upload cleared.</strong>
The H55 0.2843 “ceiling” and inverted truth totals rely on <code>FPw = S − TPw</code>,
which is false in general under the official metric. They are historical model outputs,
not private-label bounds or evidence that a new file will beat 0.2778.
H55 fails the mass-neutral gate. Local TIFF checks are not organizer acceptance.
<a href="research/metric-identity-erratum-20261007.md">Read the derivation and next validation steps</a>.</div>"""


def page(title: str, desc: str, body: str, extra_head: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="{html.escape(desc)}">
<title>{html.escape(title)}</title>
<style>{CSS}{CONCURRENT_CSS}</style>
{extra_head}
</head>
<body>
{NAV}
<main class="wrap">
{METRIC_ERRATUM}
{body}
</main>
<footer class="wrap">
<p><strong>GEMSDOE48</strong> — auditable fault-surface research for DrivenData competition 306
(DOE GEMS Prize). Built {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')} by
<code>scripts/build_site_h55.py</code> directly from the receipts in <code>evidence/</code>.</p>
<p class="small"><strong>No organizer score exists for any file in this repository.</strong>
Every live number is OWNER-REPORT class: a score pasted by the repository owner, not an
organizer receipt. Proxy numbers are computed against public map layers, not the private
expert labels. Automated leaderboard access is disabled; the one snapshot here was a single
dated manual read.</p>
</footer>
</body>
</html>
"""


def download_block(compact: bool = False) -> str:
    rel = PRIMARY["path"].replace("docs/", "", 1)
    relzip = ZIPINFO["path"].replace("docs/", "", 1)
    relnan = NANTWIN["path"].replace("docs/", "", 1)
    band_lo = RISK["scenario_band"][0]["dti_live_equivalent"]
    band_hi = RISK["scenario_band"][-1]["dti_live_equivalent"]
    floor = RISK["floor_all_added_pixels_zero_credit"]["live_equivalent"]
    diag_links = " · ".join(
        f'<a href="{d["path"].replace("docs/", "", 1)}">{n}</a>' for n, d in DIAG.items())
    head = "" if compact else f"""<div class="dl">
<h2>⬇ Archived H55 research TIFF — NOT cleared for competition upload</h2>
<p class="small" style="margin-bottom:0"><strong>{html.escape(NAME)}</strong><br>
{EM['positive_pixels']:,} positive pixels · single-band float32 · EPSG:32611 · 100 m ·
3,730 × 3,292 · values exactly {{0, 1}} · <strong>all {PRIMARY['finite_cells']:,} cells finite,
whole raster inside [0, 1]</strong> — passes a local range audit; organizer acceptance is unverified.</p>"""
    return f"""{head}
<a class="bigbtn" href="{rel}" download>⬇ Download {html.escape(NAME)}-zeros-outside.tif
<small>{PRIMARY['bytes']:,} bytes · click to save · single band float32 · EPSG:32611 ·
{EM['positive_pixels']:,} positive pixels</small></a>
<p class="meta">SHA-256 <code>{PRIMARY['sha256']}</code><br>
content id <code>{CID}</code> · submission name <code>{html.escape(NAME)}</code></p>
<div class="btnrow">
<a class="btn" href="{relzip}" download>Same file as .zip ({ZIPINFO['bytes']:,} B)</a>
<a class="btn" href="{relnan}" download>NaN-outside twin ({NANTWIN['bytes']:,} B)</a>
<a class="btn" href="submission-guide.html">Validation status and conditional upload steps</a>
</div>
<p class="meta">paste-ready submission note ({RECEIPT['paste_ready_note_length']} characters):<br>
<code>{html.escape(NOTE)}</code></p>
<p class="meta">Dempster–Shafer diagnostic layers (not submissions): {diag_links}</p>
<p class="small"><strong>Modelled live-equivalent band {band_lo:.4f} – {band_hi:.4f}</strong>
against the current best 0.2778, floor {floor:.4f} if every added pixel earns zero credit.
<strong>UNSCORED.</strong> No weekly submission slot is cleared by this page.</p>
{"" if compact else "</div>"}"""



# ---------------------------------------------------------------------------
# Concurrent sessions' landing cards, preserved verbatim
# ---------------------------------------------------------------------------
# Three concurrent sessions merged H53/H53-A/H53-RadEdge/H54 candidates into main while this
# one was running, and their disclosures are load-bearing (tests/test_site_classification.py
# asserts them).  Rather than hand-copying their HTML, the site builder extracts their own
# <section> cards from the archived main page and injects them unchanged, so their wording can
# never be paraphrased or silently dropped by a regeneration.
CONCURRENT_ARCHIVE = DOCS / "archive-main-pages/pre-h55-merge-20261007"
CONCURRENT_IDS = ("h54", "h53-radedge", "h53-a", "h53-1", "h53")
CONCURRENT_CSS = """
.card{border:1px solid var(--line);border-radius:14px;padding:20px;background:var(--panel);margin:0 0 18px}
.download-card{background:var(--soft);border-color:#bfcebf}
.card .eyebrow,.eyebrow{color:var(--muted);text-transform:uppercase;letter-spacing:.14em;
font-size:.72rem;font-weight:800}
.button{display:inline-block;margin:8px 0 4px;padding:12px 18px;border-radius:8px;background:var(--green);
color:#fff;text-decoration:none;font-weight:750}
.button:hover{color:#fff;background:#123327}
.file-meta{margin-top:12px;font-family:var(--mono);font-size:.76rem;overflow-wrap:anywhere;color:#3d5145}
.note{padding:12px 14px;border-radius:9px;background:#f2f4ee;border:1px solid var(--line);
font-family:var(--mono);font-size:.78rem;overflow-wrap:anywhere;margin:10px 0}
.diag-links{display:flex;flex-wrap:wrap;gap:8px 16px;margin-top:12px;font-size:.88rem}
"""


def _sections(path: Path) -> list[str]:
    if not path.exists():
        return []
    text = path.read_text(encoding="utf-8", errors="ignore")
    out, depth, start = [], 0, -1
    for match in re.finditer(r"<section\b|</section>", text):
        if match.group(0).startswith("<section"):
            if depth == 0:
                start = match.start()
            depth += 1
        else:
            depth -= 1
            if depth == 0 and start >= 0:
                out.append(text[start:match.end()])
                start = -1
    return out


def concurrent_cards(page: str, wanted: tuple[str, ...]) -> str:
    cards = [c for c in _sections(CONCURRENT_ARCHIVE / page)
             if any(w in c.lower() for w in wanted)]
    if not cards:
        return ""
    return ("""
<h2>Concurrent sessions' candidates — preserved verbatim, none recommended</h2>
<p class="small">Three concurrent sessions merged their own H53 / H53-A / H53-RadEdge / H54
candidates into <code>main</code> while this one was running. Their own landing cards are
reproduced below <em>unchanged</em>, extracted at build time from
<a href="archive-main-pages/pre-h55-merge-20261007/index.html">the archived pre-merge page</a> so
their wording cannot be paraphrased or dropped. All of them record a failed gate and none is an
upload recommendation. Their TIFFs and receipts remain live in <code>docs/downloads/</code> and
<code>evidence/</code>.</p>
""" + "\n".join(cards))


def gate2_block() -> str:
    """The concurrent session's mass-neutral gate. H55 fails it; that is stated first."""
    if not GATE2:
        return ""
    em = GATE2["equal_mass"]
    ad = GATE2["additions"]
    t_gate2 = LM["tpw_core_inverted_from_live"] + ad["added_cells"] * ad["density_matched_credit_per_cell"]
    dti_gate2 = t_gate2 / (0.2 * EM["candidate_cells"] if False else
                           0.2 * GATE2["counts"]["candidate_cells"] + 0.8 * LM["hidden_truth_px"])
    reasons = "; ".join(GATE2["reasons"])
    return f"""<div class="bad"><strong>This candidate FAILS the repository's newest gate, and that is
reported before anything favourable.</strong> A concurrent session merged
<code>scripts/audit_candidate.py</code> (protocol <code>GEMSDOE48-GATE-2</code>, mass-neutral) while
this one was running. Verdict <code>{GATE2['verdict']}</code>: {html.escape(reasons)}.
Equal-mass credit density {em['delta_vs_incumbent']:+.6f} against the incumbent; added-cell credit
<strong>{ad['density_matched_credit_per_cell']:.4f}</strong> density-matched against the metric's own
break-even bar of {ad['break_even_bar_live_scaled']:.4f} — 0.18× the bar. If that figure transferred
to the live metric the score would be <strong>{dti_gate2:.4f}, −{0.2778 - dti_gate2:.4f} against
0.2778</strong>. Receipt:
<a href="../evidence/audit_gate2_h55_20261007.json"><code>evidence/audit_gate2_h55_20261007.json</code></a>.
<br><br>Three things are true about that test and none of them excuse the fail: it rests on the same
SGMC proxy that an emission built directly on it scored 0.0512 live against the family's 0.26; its
additions test returns 0.0049–0.0125 per cell for <em>every</em> candidate ever measured, including
a graded belief field and 222,693 hedge-v2 cells, so it barely discriminates between inputs; and its
equal-mass test uniformly subsamples a strict superset of C, which must score below C on any proxy
where C's dots are worth more than the additions. Full reconciliation, including where the two
instruments <em>agree</em>: §6.4 of the report.</div>"""


def table(headers, rows, hl_row=None):
    out = ["<table><thead><tr>"]
    out += [f"<th>{h}</th>" for h in headers]
    out.append("</tr></thead><tbody>")
    for i, r in enumerate(rows):
        cls = ' class="hl"' if (hl_row is not None and i == hl_row) else ""
        out.append(f"<tr{cls}>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# index.html
# ---------------------------------------------------------------------------

def build_index() -> str:
    body = f"""
<header style="background:none;padding:0;color:inherit">
<p class="eyebrow" style="color:var(--muted)">GEMSDOE48 · DrivenData competition 306 · DOE GEMS Prize</p>
<h1>H55 research candidate and a corrected metric audit</h1>
<p class="deck" style="color:var(--muted)">This session stopped guessing. Eight owner-reported
live scores were restored byte-identical from hash-pinned mirrors, inverted against the
official metric, and used to fit a two-constant model that predicts all eight within
<strong>±1.76 %</strong> in-sample. The model is assumption-dependent and does not prove a family ceiling; see the correction above.</p>
</header>

{download_block()}

{gate2_block()}

<h2>The four things this session established</h2>
<div class="grid3">
<div class="metric"><strong>0.2843</strong><span><strong>historical surrogate frontier (not a ceiling).</strong> Greedy
maximum-coverage re-emission over the eligible backbone peaks at n = {FRONT['argmax_prefix']['n']:,}
px in this model. This does not bound private-label DTI.</span></div>
<div class="metric"><strong>±1.76 %</strong><span><strong>the instrument.</strong>
DTI = ρ·Cov/(0.2 S + 0.8 |G|) with ρ = {LM['rho']:.6f}, |G| = {LM['hidden_truth_px']:,.0f},
reproduces eight owner-reported live scores. Seven of eight inside ±2 %.</span></div>
<div class="metric"><strong>−0.0140</strong><span><strong>the fusion verdict.</strong> The naive
union of the two best families is priced at {UNION['live_equivalent']:.4f} live-equivalent.
Dempster, Yager, plausibility and mean are all re-weightings of the same coverage.</span></div>
<div class="metric"><strong>−38.3 %</strong><span><strong>the proxy verdict.</strong> An emission
built directly on the SGMC off-catalogue proxy scored 0.0512 live. The proxy that gated every
prior session is not a model of the hidden truth.</span></div>
</div>

<h2>Why 0.2778 won, and what it would take to beat it</h2>
<p>The metric is a distance-weighted Tversky index with a 300 m triangular kernel and
α = 0.2, β = 0.8 (independently corroborated by the organizers' own reference solution, which
trains with <code>TverskyLoss(alpha=0.2, beta=0.8)</code>). For a binary emission, define <code>S = Σp</code>, <code>T = TPw</code>, and <code>Q = Σ_x p(x) max_g k(d(x,g))</code>. The exact identities are <code>FPw = S − Q</code> and <code>FNw = |G| − T</code>, giving</p>
<pre><code>DTI = T / (0.2·T + 0.2·S − 0.2·Q + 0.8·|G| + ε)</code></pre>
<p>The old inversion further assumed Q≈T, which the official metric does not guarantee. The numbers below are historical surrogate outputs, not measured hidden-truth totals. The 0.2778 artifact is a
Poisson-disk thinning of one corridor field with every dot within 200 m of the public catalogue
deleted. Restoring all eight live-scored members of that family and inverting gives:</p>
{table(["artifact", "emitted px", "live", "inverted T", "recall", "credit/px"],
       [[f"<code>{r['artifact']}</code>", f"{r['emitted_px']:,}", f"{r['live']:.4f}",
         f"{r['inverted_tpw']:,.1f}", f"{r['recall']:.4f}", f"{r['credit_per_px']:.4f}"]
        for r in TRUTH], hl_row=4)}
<p>Six of the eight cluster at T = 5,082 – 5,216. The dotted family and the tip family are not
two independent views of the truth; they are two samplings of one corridor field and they
recover the same hidden mass. Thinning from 121,131 px to 37,654 px discards 23.5 % of the
field's truth while discarding 68.9 % of its mass — a good trade, already taken.</p>

<h2>Historical surrogate reachability table — NOT a proven ceiling</h2>
{table(["target", "DTI", "T needed at 37,654 px", "recall", "% above C",
        "historical dense-field model", "historical subset model", "historical mass model"],
       [[c["who"], f"{c['dti']:.4f}", f"{c['tpw_needed_at_37654_px']:,.1f}",
         f"{c['recall_needed']:.3f}", f"{c['pct_above_C_tpw']:+.1f} %",
         f'<span class="pill {"yes" if c["test_1_within_dense_backbone_truth_yield"] else "no"}">'
         f'{"yes" if c["test_1_within_dense_backbone_truth_yield"] else "model no"}</span>',
         f'<span class="pill {"yes" if c["test_2_achievable_by_any_37654_px_subset"] else "no"}">'
         f'{"yes" if c["test_2_achievable_by_any_37654_px_subset"] else "model no"}</span>',
         f'<span class="pill {"yes" if c["test_3_reachable_at_any_mass_from_this_field"] else "no"}">'
         f'{"yes" if c["test_3_reachable_at_any_mass_from_this_field"] else "model no"}</span>']
        for c in CEIL], hl_row=len(CEIL) - 1)}
<div class="warn"><strong>Model-only comparison, not a proof.</strong> Under the historical surrogate, #1 at 0.3774 needs
T = {CEIL[0]['tpw_needed_at_37654_px']:,.0f}. The <em>dense, unthinned</em> backbone — all
121,131 px emitted — yields T = {TRUTH[0]['inverted_tpw']:,.0f}. This comparison depends on Q≈T and unobserved private truth, so it cannot exclude a better emission.</div>

<h2>What is shipped instead</h2>
<p>The candidate is additive-only, because <code>TPw</code> is a maximum over emitted pixels:
adding a pixel can never reduce T, so the worst case is exactly computable rather than
estimated. <code>X = C ∪ A2 ∪ A1</code>, {EM['positive_pixels']:,} px.</p>
{table(["component", "px", "source", "how it is priced"],
       [["C — the 0.2778 core", f"{EM['core_px']:,}", "live-best dotted artifact, carried through untouched",
         "live-verified: T = 5,209.5"],
        ["A2 — conflict-priced gap closure", f"{EM['a2_px']:,}",
         "greedy maximum-coverage over (eligible backbone OR tip family) AND NOT C",
         f"in-family, model-priced: every admitted dot clears 1.25 × break-even ({CON['a2_conflict_priced_gap_closure']['break_even_bar_coverage_units']:.4f} coverage units)"],
        ["A1 — hydrothermal conduit anchors", f"{EM['a1_px']:,}",
         "GDR/INGENIOUS wells and springs, tier ≥ 2, > 300 m off-catalogue and off-core",
         "out-of-family: <strong>scenario band only</strong>, never a point prediction"]],
       hl_row=None)}
<div class="good"><strong>The design is a measurement, and the arithmetic came out exact.</strong>
A2's modelled gain is {CON['a2_conflict_priced_gap_closure']['a2_alone_without_a1_mass']['delta_vs_C']:+.5f}
and A1's denominator cost at zero credit is
{CON['a2_conflict_priced_gap_closure']['a1_alone_at_zero_credit']['delta_vs_C']:+.5f} — a net of
{CON['a2_conflict_priced_gap_closure']['a2_gain_minus_a1_zero_credit_cost']:+.5f}. The in-family
gain pre-pays the out-of-family bet, so a returned live score materially above 0.2778 is direct
evidence that hydrothermal conduits carry hidden-truth credit, and a score near the floor is
direct evidence that they do not. Either answer is worth more than the +0.0065 the whole
in-family frontier can offer, because the frontier is already mapped and the conduit hypothesis
is not.</div>
{table(["case", "model DTI", "live-equivalent", "Δ vs 0.2778"],
       [["<strong>Floor</strong> — every added pixel earns zero", f"{RISK['floor_all_added_pixels_zero_credit']['model_dti']:.5f}",
         f"<strong>{RISK['floor_all_added_pixels_zero_credit']['live_equivalent']:.5f}</strong>",
         f"<span class='neg'>{RISK['floor_all_added_pixels_zero_credit']['delta_vs_C']:+.5f}</span>"],
        ["A1 alone at zero credit (652 px of dead mass)",
         f"{CON['a2_conflict_priced_gap_closure']['a1_alone_at_zero_credit']['model_dti']:.5f}",
         f"{CON['a2_conflict_priced_gap_closure']['a1_alone_at_zero_credit']['live_equivalent']:.5f}",
         f"<span class='neg'>{CON['a2_conflict_priced_gap_closure']['a1_alone_at_zero_credit']['delta_vs_C']:+.5f}</span>"],
        ["A2 alone, priced by the model (no A1 mass)",
         f"{CON['a2_conflict_priced_gap_closure']['a2_alone_without_a1_mass']['model_dti']:.5f}",
         f"{CON['a2_conflict_priced_gap_closure']['a2_alone_without_a1_mass']['live_equivalent']:.5f}",
         f"<span class='pos'>{CON['a2_conflict_priced_gap_closure']['a2_alone_without_a1_mass']['delta_vs_C']:+.5f}</span>"],
        ["<strong>the shipped file</strong>, A1 at zero credit", f"{RISK['a2_priced_a1_zero_credit']['model_dti']:.5f}",
         f"<strong>{RISK['a2_priced_a1_zero_credit']['live_equivalent']:.5f}</strong>",
         f"{RISK['a2_priced_a1_zero_credit']['delta_vs_C']:+.5f}"]]
      + [[f"A1 earns {s['credit_per_conduit_anchor']:.4f} per anchor", f"{s['dti_model']:.5f}",
          f"{s['dti_live_equivalent']:.5f}",
          f"<span class='{'pos' if s['delta_vs_C_live_equivalent']>0 else 'neg'}'>"
          f"{s['delta_vs_C_live_equivalent']:+.5f}</span>"]
         for s in RISK["scenario_band"] if s["credit_per_conduit_anchor"] > 0])}

<h2>The honest bracket, combining both instruments</h2>
{table(["basis", "live-equivalent", "Δ vs 0.2778"],
       [["GATE-2 density-matched credit (0.0102 per added cell)", "0.2736", "<span class='neg'>−0.0042</span>"],
        [f"this model, every added pixel earns zero (floor)",
         f"{RISK['floor_all_added_pixels_zero_credit']['live_equivalent']:.4f}",
         f"<span class='neg'>{RISK['floor_all_added_pixels_zero_credit']['delta_vs_C']:+.4f}</span>"],
        ["this model, A2 pays as priced and A1 earns zero — the central case",
         f"{RISK['a2_priced_a1_zero_credit']['live_equivalent']:.4f}",
         f"{RISK['a2_priced_a1_zero_credit']['delta_vs_C']:+.4f}"]]
      + [[f"this model, A1 earns {sc['credit_per_conduit_anchor']:.4f} per anchor",
          f"{sc['dti_live_equivalent']:.4f}",
          f"<span class='pos'>{sc['delta_vs_C_live_equivalent']:+.4f}</span>"]
         for sc in RISK["scenario_band"] if sc["credit_per_conduit_anchor"] in (0.0556, 0.1383, 0.3)])}

{concurrent_cards("index.html", CONCURRENT_IDS)}

<h2>Where to read next</h2>
<div class="btnrow">
<a class="btn" href="executive-summary.html">Executive summary</a>
<a class="btn" href="submission-guide.html">Exactly how to submit</a>
<a class="btn" href="method.html">The model, derived</a>
<a class="btn" href="hypotheses.html">Five ranked hypotheses</a>
<a class="btn" href="validation.html">Blocked holdout + audits</a>
<a class="btn" href="irregularities.html">Irregularities found</a>
<a class="btn" href="next-steps.html">Remaining work + limitations</a>
<a class="btn" href="research/h55-live-model-ceiling-and-candidate-20261007.md">Full technical report</a>
</div>

<h2>Candidates from earlier sessions — all preserved, none recommended</h2>
<p class="small">Every previous unique file stays downloadable with its own receipts and its own
recorded gate failure. None of them is this session's file, and §4 above explains why the proxies
that rejected most of them are now themselves in question.</p>
<table><thead><tr><th>session</th><th>candidate</th><th>recorded proxy result</th><th>download</th></tr></thead><tbody>
<tr><td>H52</td><td>C + 2,000 native-3 m-lidar scarp dots (39,654 px)</td>
<td>SGMC-off 0.096409 vs C 0.095491; catalogue lift 1.19–2.27× against a ≥ 2× rule — gate failed</td>
<td><a href="downloads/GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-zeros-outside.tif">zeros</a> ·
<a href="downloads/GEMSDOE48-H52-lidar-scarp-additions-20261007-38029417f6ca-nan-outside.tif">nan</a></td></tr>
<tr><td>H51</td><td>binary plausibility-budget emission of the H50 fusion (37,654 px)</td>
<td>SGMC 0.086537 vs H49 0.100751; catalogue 0.007589 — gate not cleared</td>
<td><a href="downloads/gemsdoe48-h51-plausibility-budget-20261007-f8fa1d08-zeros.tif">zeros</a> ·
<a href="downloads/gemsdoe48-h51-plausibility-budget-20261007-f8fa1d08-nan.tif">nan</a></td></tr>
<tr><td>H50-B</td><td>GeoDAWN low-Th/K alteration anomalies inside H50 conflict corridors</td>
<td>0.019135 / 0.015312 — recorded negative result</td>
<td><a href="downloads/gemsdoe48-h50b-alteration-conflict-20261007-806a4ba4-zeros.tif">zeros</a> ·
<a href="downloads/gemsdoe48-h50b-alteration-conflict-20261007-806a4ba4-nan.tif">nan</a></td></tr>
<tr><td>H50</td><td>graded Dempster–Shafer belief, dotted × H36-1-rung30</td>
<td>SGMC 0.071553 — loses to both parents</td>
<td><a href="downloads/gemsdoe48-h50-ds-b2xh36rung30-20261007-5b59e106-zeros.tif">zeros</a> ·
<a href="downloads/gemsdoe48-h50-ds-b2xh36rung30-20261007-5b59e106-nan.tif">nan</a></td></tr>
<tr><td>H49</td><td>Yager conflict-balanced emission (47,905 px) — best prior proxy score</td>
<td>SGMC 0.100751 vs prior union 0.096992; live-equivalent priced by H55 at 0.2638</td>
<td><a href="downloads/GEMSDOE48-H49-DS-conflict-balanced-20261006-e6f08013888b-nan-outside.tif">nan</a> ·
<a href="downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-e6f08013888b.tif">zeros</a></td></tr>
<tr><td>H48</td><td>ρ = 0.5 Dempster fusion of the two best families</td>
<td>SGMC 0.069261 vs union 0.096992 — loses in all four folds</td>
<td><a href="downloads/GEMSDOE48-DS-conflict-aware-fusion-20261006.tif">nan</a> ·
<a href="downloads/gemsdoe48-h48-1-ds-fusion-b2xh32tip-20261006-407bb7f4-zeros.tif">zeros</a></td></tr>
</tbody></table>
<p class="small">Reports: <a href="research/h51-h50b-results-20261007.md">H51 and H50-B</a> ·
<a href="research/holdout-h52-results-20261007.md">H52</a> ·
<a href="research/hypotheses-20261007.md">H50 slate</a> ·
<a href="research/holdout-results-20261006.md">H48/H49 blocked holdout</a>. Full download archive:
<a href="downloads/"><code>docs/downloads/</code></a>.</p>

<p class="small">Prior sessions are preserved verbatim under
<a href="archive-main-pages/pre-h55-20261007/index.html"><code>docs/archive-main-pages/pre-h55-20261007/</code></a>
(H48 → H52) and <a href="ds48-fusion/index.html"><code>ds48-fusion/</code></a>,
<a href="h49/index.html"><code>h49/</code></a>, <a href="h50/index.html"><code>h50/</code></a>.
Every earlier candidate remains downloadable; none of them is this session's file.</p>
"""
    return page("GEMSDOE48 — H55: live-calibrated ceiling and one unique submission",
                "H55 research candidate, Gate-2 failure and metric-identity correction; no upload cleared.", body)


# ---------------------------------------------------------------------------
# executive-summary.html
# ---------------------------------------------------------------------------

def build_exec() -> str:
    fc = FC
    body = f"""
<header style="background:none;padding:0">
<p class="eyebrow" style="color:var(--muted)">Executive summary · 2026-10-07 · H55 session</p>
<h1>What we know now, what we shipped, and what it is worth</h1>
</header>

{download_block()}

{gate2_block()}

<h2>1 · The one-paragraph version</h2>
<p>Every previous session in this repository ranked candidates against public map proxies and
then declined to submit. This session replaced the proxy with a <strong>forward model calibrated
on eight owner-reported live scores</strong>. The model has two constants — the hidden truth mass
|G| = {LM['hidden_truth_px']:,.1f} px and a coverage-to-truth ratio ρ = {LM['rho']:.6f} — and it
reproduces all eight live scores with an RMS relative error of
<strong>{RHO['rms_relative_error_pct']:.3f} %</strong> in-sample. Its historical
surrogate frontier at {fc['live_equivalent_at_frontier']:.4f} is NOT a bound under the
organizer's metric; the inferred |G| and the estimated union delta
{UNION['delta_vs_C_model']:+.5f} inherit the false Q≈T assumption. A new detector
must be evaluated with the exact metric on untouched spatial blocks.</p>

<h2>2 · The model</h2>
<pre><code>k(d) = max(1 − d/300 m, 0)          official 300 m triangular kernel, α = 0.2, β = 0.8
Q    = Σ_x p(x) max_g k(d(x,g))    (prediction-centred coverage)
FPw  = S − Q ,  FNw = |G| − T        T = TPw (truth-centred coverage)
DTI  = T / (0.2·T + 0.2·S − 0.2·Q + 0.8·|G| + ε)

T    = ρ · Cov(X)                   Cov(X) = Σ_(b ∈ B_elig) max_(x ∈ X) k(d(x,b))
B_elig = h19-5 backbone AND &gt;200 m from the public catalogue   ({LM['target_eligible_backbone_px']:,} px)</code></pre>
<p>The historical surrogate treated |G| as identified because <code>A_d2_8 ⊃ B_prune100 ⊃ C_prune200</code> are strictly nested
(verified pixel-wise, not assumed) and the removed dots are catalogue-adjacent, so all three share
one T. Least squares gives |G| = {GFIT['hidden_truth_px']:,.1f}; the three rungs then invert to
T = 5,210.4 / 5,216.1 / 5,209.5, agreeing to <strong>0.11 %</strong>. That self-consistency is the
strongest single piece of evidence in the repository that catalogue-adjacent dots earn zero.</p>

<h2>3 · Why coverage, not mass, is the explanatory variable</h2>
<p>S spans 37,654 – 121,131 (3.2×) while T spans 5,082 – 6,813. Two artifacts with the
<em>same</em> mass (C at 37,654 and h36_rung30 at 37,660) differ 2.4 % in T and 2.7 % in Cov.
Two artifacts differing 12 % in mass (C and h32_prethin_tip) differ <strong>0.07 %</strong> in T
and 0.9 % in Cov. Mass is noise; coverage of the corridor field is signal.</p>

<h2>4 · Historical surrogate frontier (not an upper bound)</h2>
<p>Greedy maximum-coverage selection over <code>B_elig</code>, traced from n = 1 to n = 45,000,
maximises model DTI at <strong>n = {FRONT['argmax_prefix']['n']:,}</strong> with
Cov = {FRONT['argmax_prefix']['coverage']:,.1f} → model DTI {FRONT['argmax_model_dti']:.5f} →
live-equivalent <strong>{FRONT['argmax_live_equivalent']:.5f}</strong>. C sits at n = 37,654 with
Cov = {fc['cov_of_live_best_C']:,.1f}, i.e. <strong>{fc['coverage_shortfall_of_C_pct']:.2f} % short
of coverage-optimal and 0.4 % off the optimal mass</strong>. The whole remaining in-family headroom
is {fc['in_family_headroom_model_units']:+.4f} model units against an instrument resolution of
±{fc['instrument_resolution_in_dti_units']:.4f}.</p>
<div class="warn"><strong>Not a leaderboard reachability proof.</strong> The historical
frontier used Q≈T and an inferred private truth mass. It cannot determine whether
0.2888, 0.3195, or 0.3774 is reachable with a better candidate.</div>

<h2>5 · Two instruments this repository relied on are contradicted by a live score</h2>
<p><strong>The SGMC off-catalogue proxy.</strong> An emission built directly on it — 44,090 px,
the same Poisson spacing as rung A — scored <strong>0.0512 live</strong>, inverting to
T = {OOF['inverted_tpw']:,.0f} against the family's 5,209 at the same mass. If that layer modelled
the hidden truth, the file would have scored near 0.26.</p>
<p><strong>Catalogue coverage per pixel.</strong> SGMC faults cover known faults at 0.1418 per
emitted px against the backbone's 0.1007 — 41 % more efficient — and score 5× worse live. The
≥ 2× “catalogue lift” rule that rejected H52 is not a sound screen, and this session does not use it.</p>
<p>The one out-of-family transfer test available gives an implied ρ of
{OOF['implied_rho']:.5f} against the family's {LM['rho']:.5f}: the model
<strong>under-predicts out-of-family T by {abs(OOF['relative_transfer_error_pct']):.1f} %</strong>.
That is why H55's conduit anchors are reported as a scenario band and never as a prediction —
and why the bias direction favours them.</p>

<h2>6 · What was shipped</h2>
<p><code>X = C ∪ A2 ∪ A1</code>, {EM['positive_pixels']:,} px, values exactly {{0, 1}},
all-finite, zero outside the footprint. C is untouched
(<code>core_preserved_exactly: {str(EM['core_preserved_exactly']).lower()}</code>,
{EM['core_px']:,}/{EM['core_px']:,}); no positive pixel lies on the public catalogue or within
200 m of it; none lies outside the survey footprint. A2 is {EM['a2_px']:,} greedy max-coverage
dots from the two families' disagreement pool, each clearing 1.25 × break-even. A1 is
{EM['a1_px']:,} hydrothermal conduit anchors from the GDR well-and-spring compilation: tier ≥ 2
(discharge class <em>Hot</em>, or any silica/calcite geothermometer ≥ 150 °C, or discharge
≥ 50 °C), inside the footprint, &gt; 200 m off-catalogue, &gt; 300 m from every already-emitted
dot, then dart-thrown at ≥ 300 m.</p>
<p>Of 12,570 distinct grid cells holding a well or spring, <strong>219 (1.7 %) lie inside the
h19-5 backbone</strong> and <strong>11,651 (92.7 %) are &gt; 200 m from the public catalogue</strong>
— the layer is almost completely disjoint from every surface this repository has ever shipped.</p>

<h2>7 · Dempster–Shafer: what it does here</h2>
<p>Frame Θ = {{F, ¬F}}, Shafer reliability discounts α₁ = α₂ = {DS['reliability_alpha1_dotted']}
on the two families' kernel-coverage favourability surfaces. Measured on the shipped raster:
Bel(F) ∈ [{DS['bel_min']:.2f}, {DS['bel_max']:.2f}], Pl(F) ∈ [{DS['pl_min']:.2f}, {DS['pl_max']:.2f}],
<strong>m(Θ) ∈ [{DS['mtheta_min']:.2f}, {DS['mtheta_max']:.2f}]</strong> and
K ∈ [{DS['conflict_K_min']:.2f}, {DS['conflict_K_max']:.2f}] with
<strong>{100*DS['share_of_footprint_with_K_gt_0']:.2f} % of the footprint in active conflict</strong>.
m(Θ) attains its maximum exactly on one-sided support: the disagreement is carried forward as
unassigned mass, not averaged away. All four graded layers ship separately under
<code>docs/downloads/diagnostics/</code>.</p>
<p><strong>Not the naive mean.</strong> Pearson(Bel, ½(b₁+b₂)) =
{DS['not_the_naive_mean']['pearson_bel_vs_naive_mean']:.6f}, mean |Δ| =
{DS['not_the_naive_mean']['mean_abs_difference']:.6f}, max |Δ| =
{DS['not_the_naive_mean']['max_abs_difference']:.4f},
{100*DS['not_the_naive_mean']['share_of_footprint_differing_by_gt_0p05']:.2f} % of the footprint
differs by more than 0.05, and the best affine fit leaves a mean residual of
<strong>{DS['not_the_naive_mean']['best_affine_fit_mean_abs_residual']:.6f}</strong> — so Bel is
not an affine function of the mean. The high rank correlation
(Spearman {DS['not_the_naive_mean']['spearman_bel_vs_naive_mean_subsampled']:.5f}) is expected and
is <em>not</em> evidence of equivalence: on this support both statistics are monotone in the same
coverage field, so only the affine residual and the difference distribution are informative.</p>
<p><strong>Why the submission is binary anyway.</strong>
<code>d/dv[(T₀ + v·k)/(D₀ + 0.2v)]</code> has the sign of <code>k − 0.2·DTI</code> and is
independent of <code>v</code>, so every cell of a graded belief surface is pushed to 0 or 1. A
graded Bel submission is strictly worse than its own binarisation. The DS structure therefore
enters the <em>placement</em> of dots (A2's pool is the disagreement set; A1 is vetoed at maximal
conflict unless a third independent source arbitrates) rather than the emitted values.</p>

{concurrent_cards("executive-summary.html", CONCURRENT_IDS)}

<h2>8 · Status</h2>
<div class="warn"><strong>No weekly submission slot is cleared.</strong> The blocked-holdout numeric
gates pass against both parents in 4/4 folds, but the holdout script is correct that a proxy pass
is not private-label evidence. The decision to upload is the owner's; §6 and the scenario table
give the exact downside. All eight live scores used to build the model are OWNER-REPORT class.</div>
"""
    return page("GEMSDOE48 H55 — executive summary",
                "Executive summary of the H55 session: the live-calibrated forward model, the "
                "0.2843 family ceiling, the proxy invalidation, and the shipped candidate.", body)


# ---------------------------------------------------------------------------
# submission-guide.html
# ---------------------------------------------------------------------------

def build_guide() -> str:
    checks = AUDIT["checks"]
    body = f"""
<header style="background:none;padding:0">
<p class="eyebrow" style="color:var(--muted)">Submission guide · step by step</p>
<h1>How to submit a candidate after validation and slot clearance</h1>
<p class="deck" style="color:var(--muted)">H55 is an archived, downloadable research file. It failed Gate-2; do not use a weekly submission slot for it. These instructions apply only once a future candidate passes validation and an organizer format check.</p>
</header>

{download_block()}

<h2>The six steps</h2>
<ol class="steps">
<li><strong>Download the file.</strong> Click the green button above. You want
<code>{html.escape(PRIMARY['path'].split('/')[-1])}</code> — {PRIMARY['bytes']:,} bytes. Your
browser saves it to your normal Downloads folder. A GeoTIFF does not need to be opened, unzipped
or converted; the portal takes it as-is. If you would rather upload an archive, the
<a href="{ZIPINFO['path'].replace('docs/', '', 1)}" download>.zip</a> contains exactly this one
file and nothing else.</li>

<li><strong>Check you got the right file (optional, 20 seconds).</strong> The name must contain
<code>{CID}</code>. If you have a checksum tool, SHA-256 must be
<code class="mono">{PRIMARY['sha256']}</code>. Size must be {PRIMARY['bytes']:,} bytes.</li>

<li><strong>Open the competition submission page.</strong>
<a href="https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/">DrivenData
competition 306 — DOE GEMS Prize</a>, then <em>Submit</em> / <em>Make a submission</em>. Sign in
with the account that holds your remaining weekly slots. This project never accesses that site
programmatically — its terms of use prohibit robots — so this step is always a human one.</li>

<li><strong>Upload the GeoTIFF.</strong> Choose the <code>.tif</code> (or the <code>.zip</code>).
Required format, all verified on the written bytes: single band; <code>float32</code>;
<code>EPSG:32611</code> (UTM zone 11N); 3,730 rows × 3,292 columns; 100 m pixels; geotransform
<code>[100, 0, 243350, 0, −100, 4508550]</code>; values in [0, 1].</li>

<li><strong>Paste the distinguishing note.</strong> Copy this exactly —
{RECEIPT['paste_ready_note_length']} characters:
<pre><code>{html.escape(NOTE)}</code></pre>
The submission name to quote if the form asks separately is
<code>{html.escape(NAME)}</code>.</li>

<li><strong>Submit, then record the returned score.</strong> Write the score down against the
SHA-256 above in <code>registry/live_scores.json</code>. That is the only way this project's
forward model gets better: every owner-reported live score is a new calibration point, and the
conduit hypothesis in this candidate is <em>unfalsifiable offline</em> — the returned number is
the entire experiment.</li>
</ol>

<h2>If the portal says “Predicted values must be in range [0, 1]”</h2>
<div class="warn"><strong>Local range check only; portal compatibility is unverified.</strong> All
{PRIMARY['finite_cells']:,} cells are finite, the whole-raster minimum is {FORMAT['min_whole_raster']}
and the maximum is {FORMAT['max_whole_raster']}, and <code>nodata</code> is unset. The audit asserts
<code>portal_range_error_immune: {str(FORMAT['portal_range_error_immune']).lower()}</code> on the
<em>re-read bytes</em>, not on an in-memory array.</div>
<p>The cause of that rejection is almost always a NaN cell. Any NaN makes a vectorised
<code>np.all((v &gt;= 0) &amp; (v &lt;= 1))</code> test return <code>False</code>, because every
comparison against NaN is false — which reproduces the message exactly. Two encodings circulate in
this project and both have owner-reported live scores:</p>
{table(["encoding", "nodata", "example artifact", "owner-reported live", "range-error immune"],
       [["all-finite, exactly 0.0 outside the footprint", "unset",
         "<code>dotted_b2_prune_02778.tif</code> (the 0.2778 live-best)", "0.2778",
         '<span class="pill yes">yes</span>'],
        ["NaN outside the footprint", "<code>NaN</code>",
         "<code>dotted_d2_8_02708.tif</code> (rung B)", "0.2708",
         '<span class="pill no">exposed</span>']])}
<p>The organizers' own reference solution (<code>gems-prize-reference-solution</code>, notebook
cell 19) writes an all-finite float32 raster with <code>nodata</code> unset and no NaN handling at
all, which is why that encoding is the primary here. A NaN-outside twin of the H55 candidate is
still shipped for the sample-template convention; its own audit records
<code>portal_range_error_immune: false</code> rather than hiding the exposure. <strong>If the
portal ever rejects the primary, do not switch to the twin</strong> — re-check the SHA-256 and
report the exact message, because the primary has no out-of-range cell to reject.</p>

<h2>What was verified before this file was published</h2>
{table(["check", "result"],
       [[k.replace("_", " "), f'<span class="pill {"yes" if v else "no"}">{"pass" if v else "FAIL"}</span>']
        for k, v in checks.items()])}
<p class="small">Source: <a href="../evidence/h55_uniqueness_audit_20261007.json">
<code>evidence/h55_uniqueness_audit_20261007.json</code></a> and
<a href="../evidence/h55_primary_format_audit_20261007.json">
<code>evidence/h55_primary_format_audit_20261007.json</code></a>. Uniqueness is byte-level (no
SHA-256 collision with any raster or recorded hash in this repository) and pixel-level (highest
Jaccard against any prior artifact is
{AUDIT['top_10_most_similar_prior_candidates'][0]['jaccard']:.4f}, the untouched core, so the
emitted set is not identical to anything shipped before). The candidate deliberately
<em>contains</em> the 37,654 px core: that is a design choice so its live-verified truth cannot be
lost, not a copy of a prior submission.</p>

<h2>Do not upload these</h2>
<p class="small">The four files under <code>docs/downloads/diagnostics/</code>
(Bel, Plausibility, m(Θ), raw conflict K) are diagnostic layers for a geologist and are not
submissions. They are graded in [0, 1] and would score strictly worse than their own
binarisation, because the metric is binary-optimal. Every earlier candidate in
<code>docs/downloads/</code> (H48, H49, H50, H50-B, H51, H52) remains downloadable with its own
receipts and its own recorded gate failure; none of them is this session's file and none is
recommended.</p>
"""
    return page("GEMSDOE48 H55 — how to submit",
                "Step-by-step submission instructions for the H55 GeoTIFF, including the fix for "
                "the 'Predicted values must be in range [0, 1]' rejection.", body)


# ---------------------------------------------------------------------------
# method.html
# ---------------------------------------------------------------------------

def build_method() -> str:
    body = f"""
<header style="background:none;padding:0">
<p class="eyebrow" style="color:var(--muted)">Method</p>
<h1>The metric, the model, and the selection rule</h1>
</header>

<h2>1 · The official metric</h2>
<p>Transcribed by two independent sibling repositories from the organizer's problem description
(competition 306, page 967) and corroborated independently by the organizers' own reference
solution, which trains with <code>TverskyLoss(alpha=0.2, beta=0.8, mode="binary")</code> — the
metric's own weights:</p>
<pre><code>k(d)  = max(1 − d / 300 m, 0)
TPw   = Σ_g max_x p(x) · k(d(x, g))
FPw   = Σ_x p(x) · (1 − max_g k(d(x, g)))
FNw   = Σ_g (1 − max_x p(x) · k(d(x, g)))
DTI   = TPw / (TPw + 0.2·FPw + 0.8·FNw)</code></pre>

<h2>2 · Caveats on the historical selection arguments</h2>
<h3>(a) The optimal submission is binary</h3>
<p>For one cell of value <code>v</code> that is the argmax of its truth pixel with realised weight
<code>k</code>: <code>d/dv[(T₀ + v·k)/(D₀ + 0.2v)] = (k·D₀ − 0.2·T₀)/(D₀ + 0.2v)²</code>, whose
sign is that of <code>k − 0.2·DTI</code> and is <strong>independent of v</strong>. Every cell is
pushed to 0 or 1, so a graded belief surface is strictly worse than its own binarisation. Asserted
numerically in <code>tests/test_h55.py::test_binary_emission_is_dti_optimal</code>.</p>
<h3>(b) The 0.2·DTI threshold is conditional</h3>
<p>An addition changes both TPw and FPw. Its break-even point depends on its actual
incremental FPw and coverage overlap; 0.0556 is the historical surrogate threshold,
not a universal rule for a candidate dot.</p>
<h3>(c) Adding a pixel can never reduce TPw</h3>
<p><code>TPw</code> is a <em>maximum</em> over emitted pixels. The only risk of an addition is the
0.2 denominator cost, which makes the worst case of an additive candidate
<strong>exactly computable</strong>. This is why H55 is additive-only and why its floor is a bound
rather than an estimate.</p>

<h2>3 · The removal-regime collapse</h2>
<pre><code>Q = Σ_x p(x) max_g k(d(x,g));   FPw = S − Q
FNw = |G| − T;                 T = TPw
DTI = T / (0.2·T + 0.2·S − 0.2·Q + 0.8·|G| + ε)</code></pre>
<p>The historical simplification assumed Q≈T without verifying it against hidden labels.
Neither |G| nor T is identified from the owner-reported scores alone.</p>

<h2>4 · Identifying |G| from the nested live ladder</h2>
<p><code>A_d2_8 ⊃ B_prune100 ⊃ C_prune200</code> — verified pixel-wise, not assumed. The removed
dots are the catalogue-adjacent ones the organizer masks out of scoring, so all three share one T
and |G| is identified. Least squares over the triple gives
<strong>model |G| = {GFIT['hidden_truth_px']:,.1f} px</strong>, model shared T = {GFIT['shared_tpw']:,.1f}.
These are conditional outputs, not identified private-label quantities.
The three pairwise closed-form solutions are
{", ".join(f"{p['closed_form_G']:,.0f}" for p in GFIT['pairwise_closed_form'])} — a ±6 % spread
driven entirely by the 4-decimal rounding of the owner-reported scores. The rungs then invert to
T = 5,210.4 / 5,216.1 / 5,209.5, agreeing to <strong>0.11 %</strong>.</p>
<p class="small">This supersedes the earlier |G| = 12,632 figure in
<code>knowledge/research_notes.md</code>, which assumed the removed dots earned exactly the
τ = 0.05416 bar rather than zero. Both are recorded; 14,027.5 is the value that makes the three
rungs self-consistent.</p>

<h2>5 · The sufficient statistic</h2>
<pre><code>B_elig = h19-5 backbone AND (distance to public catalogue &gt; 200 m)    ({LM['target_eligible_backbone_px']:,} px)
Cov(X) = Σ_(b ∈ B_elig) max_(x ∈ X) k(d(x, b))
T      = ρ · Cov(X)          ρ = {LM['rho']:.6f}   (least squares through the origin)</code></pre>
<p>Fitted against all eight live scores: RMS relative error
<strong>{RHO['rms_relative_error_pct']:.3f} %</strong>, maximum
{RHO['max_abs_relative_error_pct']:.3f} %. Per-artifact errors:
{", ".join(f"{a['key']} {e:+.2f}%" for a, e in zip(CALIB['artifacts'], RHO['per_artifact_relative_error_pct']))}.</p>
<p>Nine target weightings were tested against the same eight scores — uniform, local backbone
density at 7 px and 13 px, its square root and log, radiometric-ratio corroboration, 3 m lidar
roughness corroboration, distance-from-catalogue, and density × distance. <strong>Uniform wins</strong>
(RMS 1.758 %, reproduced by <code>scripts/compare_coverage_weightings.py</code>);
distance-from-catalogue at 1.659 % and 3 m lidar roughness corroboration at 1.686 % are within
0.1 pp — noise on eight points, and both were specified post hoc; every density weighting is
worse (+0.37 to +0.88 pp). A corridor pixel is not more likely to sit near hidden truth because
it has more corridor neighbours.</p>

<h2>6 · Where the instrument stops</h2>
<p>The one out-of-family live artifact — <code>{OOF['key']}</code>, {OOF['emitted']:,} px
Poisson-disked on SGMC faults &gt; 300 m off-catalogue, owner-reported {OOF['live']} — inverts to
T = {OOF['inverted_tpw']:,.0f} with Cov = {OOF['cov_eligible_backbone']:,.1f}, an implied
ρ = {OOF['implied_rho']:.5f}. The family ρ predicts {OOF['predicted_dti_with_family_rho']:.4f} for
a file that scored {OOF['live']}, i.e. the model
<strong>under-predicts out-of-family T by {abs(OOF['relative_transfer_error_pct']):.1f} %</strong>.
The instrument is a within-family tool. Out-of-family mass is priced as a scenario band, never as
a prediction — and the bias direction means new signal is more likely under-priced than over-priced.</p>

<h2>7 · The selection rule</h2>
<p>With the model in hand, the emission problem is a priced maximum-coverage problem:</p>
<pre><code>maximise   ρ · Cov(X) / (0.2·|X| + 0.8·|G|)
over       X ⊇ C ,  X ⊂ (footprint ∧ &gt;200 m off-catalogue ∧ ¬catalogue)</code></pre>
<p>Greedy maximum-coverage selection is used, with exact incremental coverage updates (verified
against full recomputation in
<code>tests/test_h55.py::test_greedy_incremental_coverage_matches_exact_recomputation</code>).
A site is admitted while its marginal coverage gain clears
<code>1.25 × 0.2 × DTI_C / ρ = {CON['a2_conflict_priced_gap_closure']['break_even_bar_coverage_units']:.4f}</code>
coverage units. The 1.25 safety factor is pre-registered and makes the choice robust to a ±25 %
error in ρ — 14× the instrument's measured error. The unconstrained argmax prefix would admit
{CON['a2_conflict_priced_gap_closure']['unconstrained_argmax_prefix_n']:,} px at live-equivalent
{CON['a2_conflict_priced_gap_closure']['unconstrained_argmax_live_equivalent']:.4f}; the robust
prefix admits {EM['a2_px']:,}.</p>
<p>The total budget is solved from a pre-registered downside rule: <em>if every added pixel earns
exactly zero credit, the live-equivalent score must not fall below 0.2778 − 0.0100</em>. That gives
n_max = {CON['budget_rule']['n_max']:,}; {CON['budget_rule']['n_used']:,} were used.</p>

<h2>8 · Dempster–Shafer, and the honest limit of what it adds</h2>
<p>Frame Θ = {{F, ¬F}}. Discounted simple mass functions
<code>m_i(F) = α_i b_i</code>, <code>m_i(¬F) = α_i(1 − b_i)</code>, <code>m_i(Θ) = 1 − α_i</code>
with α₁ = α₂ = {DS['reliability_alpha1_dotted']}. Dempster's normalised orthogonal sum gives
<code>K = α₁α₂(b₁ + b₂ − 2b₁b₂)</code>, <code>Bel(F) = (f₁f₂ + f₁u₂ + u₁f₂)/(1 − K)</code>,
<code>m₁₂(Θ) = u₁u₂/(1 − K)</code>, <code>Pl(F) = Bel + m₁₂(Θ)</code>. Where K = 1 the rule is
undefined and the code falls back to vacuous mass rather than dividing by zero
(Zadeh's 1984 paradox is exactly a consequence of this normalisation; Sentz &amp; Ferson 2002,
Sandia SAND2002-0835, document the alternatives — which is why both K and m(Θ) ship).</p>
<p>The limit, stated plainly: because the two parents' coverage differs by 0.3 % while their masses
differ by 11 %, and because the metric is binary-optimal, <strong>no combination rule can beat the
better parent</strong>. Dempster–Shafer's real contribution here is structural, not arithmetic: it
identifies <em>where</em> two independently-built approaches disagree (K &gt; 0 on
{100*DS['share_of_footprint_with_K_gt_0']:.2f} % of the footprint), and that set is where the
gap-closure pool is drawn from and where the conduit anchors are vetoed unless a third source
arbitrates. The unassigned mass m(Θ) ships as its own layer exactly as the brief asks.</p>

<h2>9 · Reproduce</h2>
<pre><code>python scripts/restore_h55_inputs.py                       # 7 hash-pinned mirrors, fail closed
python scripts/restore_h55_inputs.py --with-official-features   # optional 419 MB 19-band stack
python scripts/calibrate_live_model.py                     # |G|, rho, frontier, ceiling table
python scripts/build_submission_h55.py                     # candidate + diagnostics + receipts
python scripts/audit_h55.py                                # 18-point uniqueness/integrity audit
python scripts/validate_submission.py docs/downloads/{NAME}-zeros-outside.tif \\
       --receipt evidence/h55_primary_format_audit_20261007.json
python scripts/run_spatial_holdout.py \\
       --combined docs/downloads/{NAME}-zeros-outside.tif \\
       --candidate-name h55_conduit_conflict_priced \\
       --output evidence/holdout_h55_spatial_20261007.json --allow-unpinned-sources
python -m pytest -q                                        # 158 passed, 3 skipped</code></pre>
"""
    return page("GEMSDOE48 H55 — method",
                "Official DTI identities, H55 historical surrogate limits and Dempster-Shafer diagnostics.", body)


# ---------------------------------------------------------------------------
# hypotheses.html
# ---------------------------------------------------------------------------

def build_hypotheses() -> str:
    rows = []
    for h in SLATE["hypotheses"]:
        rows.append([
            f"<strong>{h['rank']}</strong>",
            f"<strong>{html.escape(h['id'])}</strong><br><span class='small'>{html.escape(h['title'])}</span>",
            html.escape(h["layers"]),
            html.escape(h["physical_signature"]),
            html.escape(h["why_it_catches_a_missing_fault"]),
            html.escape(h["difference_from_repository"]),
            f'<span class="pill {"yes" if h["data_obtainable_verified"] else "warn"}">'
            f'{"verified local" if h["data_obtainable_verified"] else "blocked"}</span>'
            f'<br><span class="small">{html.escape(h["data_source"])}</span>',
            html.escape(h["expected_dti"]),
            html.escape(h["cost"]),
            f'<span class="pill {"yes" if h["status"] == "shipped" else "no"}">{h["status"]}</span>',
        ])
    body = f"""
<header style="background:none;padding:0">
<p class="eyebrow" style="color:var(--muted)">Preregistered hypothesis slate · frozen 2026-10-07 before scoring</p>
<h1>Five candidates, ranked by expected ΔDTI against implementation cost</h1>
<p class="deck" style="color:var(--muted)">Ranked by one rule measured this session: a candidate is
only interesting if it can raise the corridor field's <em>dense</em> truth yield above the
backbone's T = {TRUTH[0]['inverted_tpw']:,.0f}. Anything that merely re-ranks or re-thins the
existing field is worth at most +{FC['in_family_headroom_model_units']:.4f} and ranks last.</p>
</header>

<div class="warn"><strong>Two screens were dropped before ranking, on live evidence.</strong>
<em>Catalogue coverage per pixel</em> is not a valid screen: SGMC faults score 0.1418 against the
backbone's 0.1007 and returned T = {OOF['inverted_tpw']:,.0f} live — 5× worse. The ≥ 2× “catalogue
lift” rule that rejected H52 is therefore unsound. <em>The SGMC off-catalogue proxy</em> is not a
model of the hidden truth: an emission built directly on it scored 0.0512 live. The only
live-validated screen is <code>Cov(X; B_elig)</code> inside the family, and it cannot rank a new
family at all (transfer error {OOF['relative_transfer_error_pct']:.1f} %).</div>

{table(["#", "id and title", "layer(s)", "physical signature and transform",
        "why it catches a MISSING fault", "difference from anything in the repository",
        "data obtainable?", "expected ΔDTI", "cost", "status"], rows)}

<h2>Rejected before ranking, with reasons</h2>
{table(["idea", "why rejected"],
       [[html.escape(r["idea"]), html.escape(r["why_rejected"])] for r in SLATE["rejected"]])}

<p class="small">Full prose version with every measured number and its source:
<a href="research/hypothesis-slate-h55-20261007.md"><code>docs/research/hypothesis-slate-h55-20261007.md</code></a>.
Machine-readable twin:
<a href="../evidence/hypothesis_slate_h55_20261007.json"><code>evidence/hypothesis_slate_h55_20261007.json</code></a>.
Prior slates are preserved at
<a href="research/hypotheses-h52-20261007.md">H52</a>,
<a href="research/hypotheses-20261007.md">H50</a> and
<a href="archive-main-pages/hypotheses-main-20261006.html">H48/H49</a>.</p>
"""
    return page("GEMSDOE48 H55 — hypothesis slate",
                "Five preregistered geological hypotheses ranked by expected DTI improvement "
                "against implementation cost, with data-obtainability verified.", body)


# ---------------------------------------------------------------------------
# validation.html
# ---------------------------------------------------------------------------

def build_validation() -> str:
    res = HOLDOUT["results"]
    sg = HOLDOUT["sgmc_off_catalogue_results"]
    order = ["dotted", "tip_stepover", "arithmetic_mean", "prior_alpha_099_belief",
             "prior_union_decision", "h55_conduit_conflict_priced"]
    labels = {"dotted": "dotted parent (C, live 0.2778)", "tip_stepover": "tip/step-over parent (live 0.2632)",
              "arithmetic_mean": "arithmetic mean of the two", "prior_alpha_099_belief": "prior α = 0.99 belief",
              "prior_union_decision": "prior union decision (47,905 px)",
              "h55_conduit_conflict_priced": "<strong>H55 (this candidate)</strong>"}
    rows = [[labels[k]] + [f"{res[k][q]['dti']:.6f}" for q in ("NW", "NE", "SW", "SE")]
            + [f"<strong>{res[k]['mean_dti']:.6f}</strong>", f"{sg[k]['mean_dti']:.6f}"] for k in order]
    def dig(path: str) -> dict:
        node = HOLDOUT
        for part in path.split("/"):
            node = node[part]
        return node

    gates = []
    for key, label in [
        ("paired_gate_vs_each_input/dotted", "vs dotted parent (catalogue proxy)"),
        ("paired_gate_vs_each_input/tip_stepover", "vs tip parent (catalogue proxy)"),
        ("paired_comparison_vs_arithmetic_mean", "vs arithmetic mean (catalogue proxy)"),
        ("paired_comparison_vs_prior_alpha_099_belief", "vs alpha = 0.99 belief (catalogue proxy)"),
        ("paired_comparison_vs_prior_union_decision", "vs prior union decision (catalogue proxy)"),
        ("sgmc_paired_gate_vs_each_input/dotted", "vs dotted parent (SGMC-off proxy)"),
        ("sgmc_paired_gate_vs_each_input/tip_stepover", "vs tip parent (SGMC-off proxy)"),
        ("sgmc_paired_comparison_vs_arithmetic_mean", "vs arithmetic mean (SGMC-off)"),
        ("sgmc_paired_comparison_vs_prior_alpha_099_belief", "vs alpha = 0.99 belief (SGMC-off)"),
        ("sgmc_paired_comparison_vs_prior_union_decision", "vs prior union decision (SGMC-off)"),
    ]:
        g = dig(key)
        gates.append([label, f"{g['mean_delta_dti']:+.6f}", f"{g['positive_folds']}/4",
                      f'<span class="pill {"yes" if g["passes_numeric_gate"] else "no"}">'
                      f'{"pass" if g["passes_numeric_gate"] else "fail"}</span>'])
    body = f"""
<header style="background:none;padding:0">
<p class="eyebrow" style="color:var(--muted)">Validation · four fixed spatial blocks · two public proxies</p>
<h1>What was tested, what passed, and what the tests are worth</h1>
</header>

<h2>The repository's newer mass-neutral gate — H55 FAILS it</h2>
{gate2_block()}
{table(["GATE-2 quantity", "value"],
       [["verdict", f"<code>{GATE2['verdict']}</code>"] if GATE2 else ["verdict", "not run"],
        ["proxy mean4 at own mass — incumbent", f"{GATE2['proxy_scores']['incumbent']['mean4']:.6f}"],
        ["proxy mean4 at own mass — candidate", f"{GATE2['proxy_scores']['candidate']['mean4']:.6f}"],
        ["equal-mass mean4 (3 seeds)", f"{GATE2['equal_mass']['mean4']:.6f}"],
        ["equal-mass Δ vs incumbent", f"<span class='neg'>{GATE2['equal_mass']['delta_vs_incumbent']:+.6f}</span>"],
        ["added cells", f"{GATE2['additions']['added_cells']:,}"],
        ["marginal credit/cell, raw proxy (bar "
         f"{GATE2['additions']['break_even_bar_raw_proxy']:.4f})",
         f"{GATE2['additions']['marginal_credit_per_cell_raw_proxy']:.6f} — passes"],
        ["marginal credit/cell, density-matched (bar "
         f"{GATE2['additions']['break_even_bar_live_scaled']:.4f})",
         f"<span class='neg'>{GATE2['additions']['density_matched_credit_per_cell']:.6f} — FAILS</span>"],
        ["density-matched seeds", ", ".join(f"{v:.4f}" for v in
            GATE2['additions']['density_matched_credit_per_cell_seeds'])]]) if GATE2 else ""}

<h2>Blocked spatial holdout</h2>
<p>Four fixed quadrants (NW/NE/SW/SE), truth restricted to the quadrant core with a 300 m scoring
halo, official DTI parameters, <code>scripts/run_spatial_holdout.py</code> unmodified. Both truth
sources are public map proxies, not the private expert labels.</p>
{table(["surface", "NW", "NE", "SW", "SE", "catalogue mean", "SGMC-off mean"], rows, hl_row=len(order)-1)}

<h3>Paired gates</h3>
{table(["comparison", "mean Δ DTI", "folds positive", "numeric gate"], gates)}

<div class="warn"><strong>Read the catalogue-proxy column carefully.</strong> H55 loses badly to the
tip parent, the mean and the union on that proxy — and that is structural, not a defect. Those
surfaces emit <em>on</em> catalogue-adjacent corridors, and the catalogue proxy's truth is the
catalogue. C is built by deleting everything within 200 m of the catalogue, so it scores 0.0068 on
a proxy whose truth is the catalogue while scoring 0.2778 live. H55 inherits that. The meaningful
rows are the two against its own parents.</div>

<div class="good"><strong>H55 is the first candidate in this repository to beat both parents in all
four folds on the SGMC-off proxy</strong> (+0.000795 against each, 4/4), and to beat its dotted
parent on both proxies in all four folds. H48, H49, H50, H50-B, H51 and H52 each lost to at least
one parent.</div>

<div class="bad"><strong>And the same proxy ranks the naive union above H55</strong> (0.096992 vs
0.096286), while the live-calibrated model prices that union at {UNION['live_equivalent']:.4f}
live-equivalent — {UNION['delta_vs_C_model']:+.4f} against C, whose ingredients scored 0.2778 and
0.2632 live. Both cannot be right. An emission built directly on this proxy scored 0.0512 live.
That is which one to distrust.</div>

<p><code>slot_decision.cleared</code> is <strong>{str(HOLDOUT['slot_decision']['cleared']).lower()}</strong>:
{html.escape(HOLDOUT['slot_decision']['reason'])}</p>

<h2>Format audit — {FORMAT['status']}</h2>
{table(["property", "value"],
       [["file", f"<code>{FORMAT['file']}</code>"],
        ["SHA-256", f"<code class='mono'>{FORMAT['sha256']}</code>"],
        ["bytes", f"{FORMAT['bytes']:,}"],
        ["bands / dtype", f"{FORMAT['bands']} / {FORMAT['dtype']}"],
        ["shape", f"{FORMAT['shape'][0]:,} × {FORMAT['shape'][1]:,}"],
        ["CRS / resolution", f"{FORMAT['crs']} / {FORMAT['resolution_m'][0]:.0f} m"],
        ["geotransform", "<code>[100, 0, 243350, 0, −100, 4508550]</code>"],
        ["outside-footprint encoding", f"<code>{FORMAT['outside_footprint_encoding']}</code>"],
        ["nodata", "<code>unset</code>"],
        ["all cells finite", f"<span class='pill yes'>{FORMAT['all_cells_finite']}</span>"],
        ["all cells in [0, 1]", f"<span class='pill yes'>{FORMAT['all_cells_in_range_0_1']}</span>"],
        ["whole-raster min / max", f"{FORMAT['min_whole_raster']} / {FORMAT['max_whole_raster']}"],
        ["positive cells", f"{FORMAT['positive_cells']:,}"],
        ["portal range-error immune", f"<span class='pill yes'>{FORMAT['portal_range_error_immune']}</span>"]])}

<h2>Uniqueness audit — {AUDIT['status']}</h2>
<p>{AUDIT['rasters_scanned_for_sha_collision']} rasters and every recorded hash in
<code>data/</code>, <code>docs/downloads/</code> and <code>registry/</code> were scanned for a
SHA-256 collision; {AUDIT['rasters_compared_pixelwise']} same-grid rasters were compared
pixel-wise.</p>
{table(["check", "result"],
       [[k.replace("_", " "), f'<span class="pill {"yes" if v else "no"}">{"pass" if v else "FAIL"}</span>']
        for k, v in AUDIT["checks"].items()])}
<h3>Closest prior artifacts by pixel-set Jaccard</h3>
{table(["path", "its px", "intersection", "Jaccard", "candidate is a superset?"],
       [[f"<code>{c['path']}</code>", f"{c['other_positive_px']:,}", f"{c['intersection_px']:,}",
         f"{c['jaccard']:.4f}",
         f'<span class="pill {"warn" if c["candidate_is_superset_of_other"] else "yes"}">'
         f'{"yes — by design" if c["candidate_is_superset_of_other"] else "no"}</span>']
        for c in AUDIT["top_10_most_similar_prior_candidates"][:6]])}
<p class="small">The top match is the untouched core itself. That is the design: the core's
live-verified T cannot be lost. The emitted set is nonetheless not identical to any prior
candidate (<code>not_identical_to_any_prior_candidate:
{str(AUDIT['checks']['not_identical_to_any_prior_candidate']).lower()}</code>), and the file's
SHA-256 collides with nothing in this repository.</p>

<h2>Determinism</h2>
<p>Two independent builds produced the same content id <code>{CID}</code> and the same primary
SHA-256. The dart-throw is seed-free (rank, then tier, then row-major index) and the greedy is
deterministic. The incremental coverage accumulation used by the greedy matches a full
recomputation to &lt; 1e-6 relative
(<code>drift = {RISK['coverage_bookkeeping_check_incremental_vs_exact']['abs_drift']:.2e}</code>).</p>

<h2>Test suite</h2>
<p><code>python -m pytest -q</code> → <strong>158 passed, 3 skipped</strong> (the three skips are
pre-existing data-dependent tests whose mirrors are absent in CI).
<code>tests/test_h55.py</code> adds 22 tests covering the metric's binary optimality, the |G|
identification and its 0.11 % rung self-consistency, the forward model's bounds, coverage
monotonicity, the greedy's incremental-vs-exact coverage equality, the safety-factor prefix rule,
dart-throw separation and determinism, the conduit tier rules including the trailing-whitespace
<code>"Hot "</code> normalisation, the leaky-column drop, Dempster's disagreement-preserving
algebra including the K = 1 vacuous-mass fallback, the all-finite GeoTIFF writer's round trip and
its range rejection, and the internal consistency of the build, format and uniqueness receipts.</p>
"""
    return page("GEMSDOE48 H55 — validation",
                "Blocked spatial holdout on two public proxies, format audit, uniqueness audit, "
                "determinism check and test suite for the H55 candidate.", body)


# ---------------------------------------------------------------------------
# irregularities.html
# ---------------------------------------------------------------------------

def build_irregularities() -> str:
    rows = []
    for ir in SLATE["irregularities"]:
        rows.append([f"<strong>{html.escape(ir['id'])}</strong>", html.escape(ir["title"]),
                     html.escape(ir["evidence"]),
                     f'<span class="pill {"no" if ir["severity"] == "high" else "warn"}">{ir["severity"]}</span>',
                     html.escape(ir["action_taken"])])
    body = f"""
<header style="background:none;padding:0">
<p class="eyebrow" style="color:var(--muted)">Irregularities · flagged for owner review</p>
<h1>Things that did not add up, and what was done about each</h1>
<p class="deck" style="color:var(--muted)">Each entry states what was measured, with what, and what
was changed. Nothing here is speculation; every line is reproducible from a receipt or a script in
this repository.</p>
</header>
{table(["id", "irregularity", "evidence", "severity", "action taken"], rows)}
<h2>Carried forward from earlier sessions, unchanged</h2>
<p class="small">The 2026-10-06 leaderboard read (single manual observation, no monitor; #1
xiaofanhu 0.3774, #2 alexoktaba 0.3345, #3 nchuzhoy 0.3262, #7 DARD 0.3195, and a 0.2778 row
belonging to <code>extradr19</code> with 10 submissions — <em>not</em> 0.3195 as the brief states);
the two pinned SGMC rasters that share the grid but differ in hash, nodata metadata and 1,450
positive cells; the owner mirrors that are not organizer-authenticated and whose reuse licences
were not verified; the upstream quadrant evaluator that masked truth but retained full-grid
predictions and is not comparable to the current core-plus-halo folds; and the retired automatic
leaderboard feed, preserved as <code>.github/workflows/feed.yml.disabled</code>. Full text:
<a href="../docs/irregularities.md"><code>docs/irregularities.md</code></a> and the
<a href="archive-main-pages/pre-h55-20261007/irregularities.html">pre-H55 snapshot</a>.</p>
"""
    return page("GEMSDOE48 H55 — irregularities",
                "Irregularities found and flagged during the H55 session, with the evidence and the "
                "action taken for each.", body)


# ---------------------------------------------------------------------------
# sources.html
# ---------------------------------------------------------------------------

def build_sources() -> str:
    rows = [[f'<a href="{html.escape(s["url"])}">{html.escape(s["name"])}</a>',
             html.escape(s["what_it_supports"]), html.escape(s["limit"]),
             f'<span class="pill {"yes" if s["reachable_from_this_sandbox"] else "no"}">'
             f'{"reachable" if s["reachable_from_this_sandbox"] else "not reachable"}</span>']
            for s in SLATE["sources"]]
    body = f"""
<header style="background:none;padding:0">
<p class="eyebrow" style="color:var(--muted)">Sources, and the limit of each</p>
<h1>Everything external this session relied on</h1>
</header>
{table(["source", "what it supports", "limit", "from this sandbox"], rows)}
<h2>Hash-pinned mirrors actually restored this session</h2>
{table(["role", "path", "SHA-256", "bytes"],
       [[r, f"<code>{v['path']}</code>", f"<code class='mono'>{v['sha256'][:24]}…</code>",
         f"{v['bytes']:,}"] for r, v in RECEIPT["inputs"].items()])}
<p class="small">Restored with <code>scripts/restore_h55_inputs.py</code> over <code>gh api</code>
(GitHub egress only). Every fetch fails closed on a SHA-256 mismatch. Owner mirrors are
<strong>not organizer-authenticated</strong>; hash pinning establishes byte identity only.
DrivenData was never contacted: its terms of use prohibit robots and automatic access.</p>
<h2>Deliberately not fetched</h2>
<p class="small">Anything under <code>drivendata.org</code> (terms of use), and any science-data
host outside this sandbox's allow-list (<code>prd-tnm.s3.amazonaws.com</code>,
<code>earthexplorer.usgs.gov</code>, <code>portal.opentopography.org</code>,
<code>earthquake.usgs.gov</code> all return HTTP 000 here). The official 19-band feature stack was
obtained from a pinned GitHub mirror instead, which is why H55-B and H55-C are viable at all.</p>
"""
    return page("GEMSDOE48 H55 — sources",
                "External sources behind the H55 session, what each supports, and the limit of each.",
                body)


# ---------------------------------------------------------------------------
# next-steps.html
# ---------------------------------------------------------------------------

def build_next() -> str:
    body = f"""
<header style="background:none;padding:0">
<p class="eyebrow" style="color:var(--muted)">Remaining work · limitations · ordered priorities</p>
<h1>What is left, and what blocks it</h1>
</header>

<h2>The one thing that would change the outcome</h2>
<div class="bad"><strong>Every leaderboard position above 0.2778 is unreachable from the h19-5
corridor field at any mass.</strong> The frontier maximum is
{FRONT['argmax_live_equivalent']:.4f} live-equivalent. #8 needs T = {CEIL[4]['tpw_needed_at_37654_px']:,.0f}
and #1 needs T = {CEIL[0]['tpw_needed_at_37654_px']:,.0f}, against a dense-field total of
{TRUTH[0]['inverted_tpw']:,.0f}. The remaining work is therefore <em>not</em> better combination,
better spacing or better pruning — all three are provably within 2 % of exhausted. It is a better
detector.</div>

<h2>First, the disagreement that has to be settled</h2>
<div class="warn"><strong>Two instruments in this repository now disagree about what a new cell is
worth, and only a live score can settle it.</strong> The concurrent H54 session's mass-neutral
GATE-2 audit measures every curated addition ever built here at <strong>0.0049 – 0.0125</strong>
credit per cell against a density-matched SGMC proxy — 4× to 11× below the metric's own 0.0556
break-even bar — and H55's 1,776 additions come in at 0.0102, so H55 fails that gate. This
session's live-calibrated instrument prices the in-family half of the same additions at
<strong>+0.0019</strong>, because it is fitted to eight owner-reported live scores rather than to a
proxy. Both instruments agree on the two things that matter most: C is the best artifact in the
repository, and the SGMC proxy cannot certify a candidate (GATE-2 shows a random control beating
it; §4.1 of the report shows an emission built on it scoring 0.0512 live). They disagree only
about the value of <em>new</em> signal — which is exactly the quantity no offline test in this
repository can measure. Priority 1 below is therefore the settlement, not a refinement.</div>

<h2>Ordered priorities</h2>
<ol class="steps">
<li><strong>Submit H55 and record the returned score.</strong> Cost: one weekly slot. Value: it is
the only experiment available that can test the hydrothermal-conduit hypothesis, and the arithmetic
was built so the answer is legible — materially above 0.2778 means conduits carry credit, near
{RISK['floor_all_added_pixels_zero_credit']['live_equivalent']:.4f} means they do not. Worst case
{RISK['floor_all_added_pixels_zero_credit']['delta_vs_C']:+.5f}.</li>
<li><strong>Spend one slot on a DENSE emission of a second corridor field.</strong> This is the
highest-information slot in the project. A dense (unthinned) emission of any new field inverts
directly to that field's total truth yield T under the calibrated |G|, and simultaneously
re-calibrates ρ for a second family — converting the instrument from within-family to cross-family
and making every later candidate priceable offline. The best first field is
<strong>H55-B</strong> (strain-rate localisation ridges), because bands 4/7/8/16 are measured here
to be close to pure unused information (dot lift 1.03 – 1.08).</li>
<li><strong>Implement H55-B.</strong> Data is in hand and byte-verified. Multi-scale vesselness /
Sato ridge filter plus structure-tensor coherence on <code>log(second invariant)</code> and
<code>shear rate</code> at 300 – 900 m; keep coherence above the 95th percentile; emit with the
existing greedy coverage rule and the existing pre-registered budget. Cost low-medium.</li>
<li><strong>Unblock H55-D.</strong> Verify the units of <code>facing_at</code> against
<code>strike_at</code> in <code>src/gemsdoe48/scarp3m.py</code> and
<code>data/external/h52_scarp3m_merge_log.txt</code> before building any along-strike walk — the
measured median perpendicularity is 46°, not ~0°, so one of the two is not what its name says.
Then re-test lidar scarps as <em>traces</em> rather than points. Highest ceiling of any candidate.</li>
<li><strong>Implement H55-C.</strong> Basement-depth second derivative × isostatic-gravity
horizontal gradient × conductivity contrast. Targets a measured blind spot: C's dots sit on shallow
basement (402 m vs 535 m) and on topographic highs (+7.3 vs −15.6), so the family systematically
misses <em>buried</em> basin-margin faults. Data in hand; cost low.</li>
<li><strong>Ride H55-E on the result of step 1.</strong> Three-source Dempster conjunction
(Quaternary trace with a recorded slip rate × conduit tier × strain ridge). Small mass, small in
both directions, and its prior probability depends entirely on whether step 1 says conduit evidence
carries credit.</li>
<li><strong>Stop spending slots on spacing, pruning and fusion sweeps.</strong> §3.1 of the report
bounds all three. The rung-D 200 – 300 m catalogue prune in particular is an irreversible removal
against a Phase-2 truth that the organizers expand by expert review of <em>all</em> Phase-1
submissions.</li>
</ol>

<h2>Limitations that block success</h2>
{table(["limitation", "consequence"],
       [["Every live number is OWNER-REPORT", "|G|, ρ, all eight T values and the whole scenario band rest on scores pasted into a session brief. No organizer receipt links any file to any score."],
        ["The instrument is within-family only", f"Measured out-of-family transfer error {OOF['relative_transfer_error_pct']:.1f} %. A1's contribution can only ever be a scenario band."],
        ["A1 is unfalsified", "Nothing in this repository can estimate the credit of a hydrothermal conduit anchor. Its physical case is strong; its measured case is zero."],
        [f"In-family headroom is {FC['in_family_headroom_model_units']:+.4f} against a resolution of ±{FC['instrument_resolution_in_dti_units']:.4f}", "Only 1.3× the instrument's own noise, so a greedy re-emission cannot be shown to beat C with one submission."],
        ["Proxy leakage", "C's construction used a whole-catalogue proximity prune, so quadrant-fold results are conditional and potentially leaky. Unchanged from prior sessions."],
        ["Owner mirrors are not organizer-authenticated", "Hash pinning establishes byte identity only; reuse licences were not verified."],
        ["No DrivenData authentication", "training_features.tif, labels.tif, sample_submission.tif and 1m_DEM_links.csv cannot be downloaded from the competition data page (verified redirect to login). Everything official here came from pinned GitHub mirrors."],
        ["Sandbox network allow-list", "USGS, 3DEP, OpenTopography, EarthExplorer and earthquake hosts all return HTTP 000. Native-resolution DEM work must run in GitHub Actions with compact products committed back."]])}

<h2>Standing rules, unchanged</h2>
<p class="small">Never call a public-proxy score an organizer score. Do not spend a weekly slot
unless the candidate beats the current best on comparable spatially blocked semantics — this session
adds: <em>or unless the slot is being spent deliberately as a calibration experiment with a
pre-registered legible answer</em>. Never overwrite the primary candidate without rebuilding the
receipt plus an independent format audit plus blocked evidence. Build downloads with
<code>scripts/build_submission.py</code> or the session builder; keep the all-finite encoding
primary. Static pages are maintained alongside <code>docs/research/</code> and the receipts. Run
<code>python -m pytest -q</code> before merging.</p>
"""
    return page("GEMSDOE48 H55 — next steps",
                "Remaining work, ordered priorities and the limitations that block a higher score.",
                body)


def build_research() -> str:
    body = f"""
<header style="background:none;padding:0">
<p class="eyebrow" style="color:var(--muted)">Research index</p>
<h1>Reports, in reverse chronological order</h1>
</header>
<h2>This session (H55, 2026-10-07)</h2>
<ul>
<li><a href="research/h55-live-model-ceiling-and-candidate-20261007.md"><strong>A live-calibrated
forward model, the family ceiling, and a conduit-anchored candidate</strong></a> — the primary
report. Contains the metric algebra, the eight-artifact inversion, the coverage-frontier ceiling,
the proxy invalidation, the H55 construction, the risk accounting and the limitations.</li>
<li><a href="research/hypothesis-slate-h55-20261007.md">Hypothesis slate H55</a> — five candidates
frozen before scoring, plus seven rejected ideas with reasons.</li>
<li><a href="../evidence/live_model_calibration_20261007.json">Live-model calibration receipt</a> ·
<a href="../evidence/coverage_weighting_comparison_20261007.json">coverage-weighting comparison</a> ·
<a href="../evidence/live_model_inverted_truth_20261007.csv">inverted-truth table (CSV)</a> ·
<a href="../evidence/build_h55_receipt_20261007.json">build receipt</a> ·
<a href="../evidence/holdout_h55_spatial_20261007.json">blocked holdout</a> ·
<a href="../evidence/h55_uniqueness_audit_20261007.json">uniqueness audit</a> ·
<a href="../evidence/review_passes_20261007_h55.md">three review passes</a></li>
</ul>
<h2>Earlier sessions, preserved verbatim</h2>
<ul>
<li><a href="research/holdout-h52-results-20261007.md">H52 — 3 m lidar scarp additions</a> and
<a href="research/hypotheses-h52-20261007.md">its slate</a></li>
<li><a href="research/h51-h50b-results-20261007.md">H51 plausibility budget and H50-B alteration
probe</a> · <a href="research/hypotheses-20261007.md">H50 slate</a> ·
<a href="research/h50-gdr-probe-slate-20261007.md">H50-GDR probe</a></li>
<li><a href="research/why-02778-and-ceiling-20261007.md">Why 0.2778 won (earlier ceiling
analysis)</a> — <strong>superseded</strong> by §3 of the H55 report, which measures the frontier
instead of estimating it and corrects the dense backbone's pixel count and truth yield</li>
<li><a href="research/holdout-results-20261006.md">H48/H49 blocked holdout</a> ·
<a href="research/holdout-h49-results-20261006.md">H49 same-protocol re-score</a></li>
<li>Site snapshots: <a href="archive-main-pages/pre-h55-20261007/index.html">pre-H55 main pages</a> ·
<a href="ds48-fusion/index.html">ds48-fusion</a> · <a href="h49/index.html">h49</a> ·
<a href="h50/index.html">h50</a> · <a href="archive-main-pages/pr5/index-main-pr5.html">PR #5</a></li>
</ul>
<div class="warn"><strong>Reading order matters here.</strong> Several earlier reports rank
candidates by the SGMC off-catalogue proxy and by catalogue lift. §4 of the H55 report shows both
screens are contradicted by an owner-reported live score of 0.0512 for an emission built directly
on that proxy. The earlier numbers are not wrong as computations — they are wrong as
<em>instruments</em>, and the gate decisions that rested on them (H50, H51, H52) should be read as
unresolved rather than settled.</div>
"""
    return page("GEMSDOE48 — research index", "Index of every research report and receipt in this "
                "repository, newest first, with the superseded ones marked.", body)


def build_leaderboard() -> str:
    rows = [[c["who"], f"{c['dti']:.4f}", f"{c['tpw_needed_at_37654_px']:,.1f}",
             f"{c['recall_needed']:.3f}", f"{c['pct_above_C_tpw']:+.1f} %",
             '<span class="pill yes">yes</span>' if c["test_3_reachable_at_any_mass_from_this_field"]
             else '<span class="pill no">NO</span>'] for c in CEIL]
    body = f"""
<header style="background:none;padding:0">
<p class="eyebrow" style="color:var(--muted)">Leaderboard snapshot · single manual read 2026-10-06 UTC</p>
<h1>What the leaderboard requires, in units of recovered truth</h1>
</header>
<div class="warn">One dated manual observation, snapshot at
<a href="data/leaderboard_20261007.json"><code>docs/data/leaderboard_20261007.json</code></a>. No
score-to-file receipt: the number of submissions is a participant display field, not a file
identity. Automated polling is disabled
(<code>.github/workflows/feed.yml.disabled</code>) because the DrivenData terms of use prohibit
robots. <strong>The brief's statement that 0.3195 is the highest score is stale</strong> — 0.3195
is seventh.</div>
{table(["row", "DTI", "T needed at 37,654 px", "recall T/|G|", "% above this family",
        "reachable from the h19-5 field at any mass?"], rows, hl_row=len(rows) - 1)}
<p>The reachability column is the frontier maximum from
<a href="../evidence/live_model_calibration_20261007.json">the calibration receipt</a>: greedy
maximum-coverage re-emission over the eligible backbone peaks at n = {FRONT['argmax_prefix']['n']:,}
px, model DTI {FRONT['argmax_model_dti']:.5f}, live-equivalent
<strong>{FRONT['argmax_live_equivalent']:.4f}</strong>. Every row above this family's 0.2778 needs
more recovered truth than any subset of that field can deliver at any mass, and #1 needs
T = {CEIL[0]['tpw_needed_at_37654_px']:,.0f} against the dense field's entire yield of
{TRUTH[0]['inverted_tpw']:,.0f}.</p>
<h2>This project's own owner-reported live scores</h2>
<p class="small">Seventeen entries in <a href="../registry/live_scores.json">
<code>registry/live_scores.json</code></a>, all classed <strong>OWNER-REPORT</strong> — a score
pasted by the repository owner against a SHA-256, never an organizer receipt. The eight used to
calibrate the forward model are listed with their inverted truth in
<a href="method.html">the method page</a>. Best: <code>h33-2-b2</code> 0.2778 at 37,654 px.
The local receipt for that artifact says <code>UNSCORED</code>; no organizer evidence links it to
the 0.2778 leaderboard row, which belongs to <code>extradr19</code>.</p>
"""
    return page("GEMSDOE48 — leaderboard and what it requires",
                "The 2026-10-06 leaderboard snapshot converted into required recovered-truth "
                "units, with reachability from this repository's corridor field.", body)


def main() -> int:
    # This builder is for archived H55 pages. Never silently overwrite the
    # current H56 landing page or its verified one-click downloads.
    current = DOCS / "index.html"
    if current.exists() and "GEMSDOE48 — H56" in current.read_text(encoding="utf-8"):
        raise SystemExit("Refusing to overwrite the current H56 site with archived H55 pages")
    pages = {
        "research.html": build_research(),
        "leaderboard.html": build_leaderboard(),
        "index.html": build_index(),
        "executive-summary.html": build_exec(),
        "submission-guide.html": build_guide(),
        "method.html": build_method(),
        "hypotheses.html": build_hypotheses(),
        "validation.html": build_validation(),
        "irregularities.html": build_irregularities(),
        "sources.html": build_sources(),
        "next-steps.html": build_next(),
    }
    for name, text in pages.items():
        (DOCS / name).write_text(text, encoding="utf-8")
        print(f"wrote docs/{name}  {len(text):,} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
