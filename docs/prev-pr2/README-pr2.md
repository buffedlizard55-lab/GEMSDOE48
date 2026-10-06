> **Historical PR archive.** This earlier page is preserved for provenance; claims may be superseded. See the [current overview](../index.html) and [current validation](../validation.html).

---

# GEMSDOE48 — Dempster-Shafer Family Fusion for the DOE GEMS Prize

> **Read this file first, every session.** It is the project charter and the
> standing brief. Everything below the charter line is the operative prompt.

**Competition:** [The Geologic Enhanced Mapping System (GEMS) Prize Challenge](https://www.drivendata.org/competitions/306/competition-doe-gems/)
(DrivenData #306). Find geothermal-indicative geological faults in the
GeoDAWN region (NW Nevada) that are **not** in the USGS/INGENIOUS catalogue,
and ship them as a single-band float32 GeoTIFF on the competition grid
(EPSG:32611, 100 m, 3730×3292).

**What this repo ships:** a unique competition submission built by combining
the two best-performing surface families — the spacing-tuned *dotted* family
(best owner-reported live score **0.2778**, GEMSDOE32 `h33-h33-2-b2`) and the
*tip/step-over* family (**0.2632**, GEMSDOE33 `h33d-analog-tip-stepover-r30`) —
with **Dempster-Shafer evidence theory** (Dempster 1967; Shafer 1976), which
preserves disagreement instead of averaging it away. The unassigned-belief
mass is shipped as its own diagnostic layer.

---

## ⬇ One-click submission file

The submission TIF lives in [`docs/downloads/`](docs/downloads/) and is linked
from the very top of the GitHub Pages site (`docs/index.html`):

* **PRIMARY (submit this):**
  `gemsdoe48-ds-dotted-x-tipstepover-20261006T201749Z-95897e3f8125-decision-zeros.tif`
  — the DS decision emission: combined-belief support (47,905 dots) at full
  confidence, selected by the blocked off-catalogue holdout tier sweep.
  All-finite float32 in `[0,1]`, no nodata tag, portal-safe.
  SHA-256 `a913f633925e9e683be150ec7826d8dad6cca44589bf832ec5d8e689ccda5c52`.
* **SECONDARY:** `…-belief-zeros.tif` — the literal normalized combined belief
  Bel(F) ∈ [0,1] (tiers 1.0 both-family / 0.4975 single-family), SHA-256
  `1aef3f909aea5b6c792380f4498d834231fa8cc8f03cc677098bf9076e0edc73`.
* Unique submission name: **`GEMSDOE48-DS-DOTTED-x-TIPSTEPOVER-95897e3f8125`**
* Note to paste into the DrivenData *Note (optional)* field (173/200 chars):
  `GEMSDOE48 Dempster-Shafer fusion dotted 0.2778 x tip-stepover 0.2632; union support 47905 dots full confidence per holdout tier sweep; unassigned-mass layer; id 95897e3f8125`

Diagnostic layers (not for submission; for geologists):
`gemsdoe48-ds-unassigned-mass-…` (preserved ignorance after combination),
`gemsdoe48-ds-conflict-…` (where the families actively contradict),
`gemsdoe48-ds-plausibility-…`, `gemsdoe48-ds-belief-raw-…`.
All hashes pinned in `evidence/build_submission.json`.

---

## Standing brief (the prompt, verbatim intent)

**HIGHEST URGENCY:** generate a **unique** TIF submission for the
competition. Do not copy a previous submission (learning/education reuse of
inputs is fine, the derived artifact must be new and its construction
documented). There must be an easy-to-download submission TIF.

**Method directive:** Combine the two best-performing families with a rule
that preserves disagreement instead of averaging it away. The spacing-tuned
"dotted" family (up to **0.2778**) and the tip/step-over family
(**0.26–0.27**) are the two strongest independently-built results; a naive
weighted average of the two surfaces would wash out exactly the information
in *where they disagree*. Dempster-Shafer evidence theory combines two
evidence sources via Dempster's rule of combination, which explicitly carries
forward a mass of "uncertain/unassigned" belief wherever the sources
disagree rather than forcing it into a single blended probability. Treat the
resulting unassigned-belief mass as its own diagnostic layer — a geologist
reading this submission can see not just where the model believes there is a
fault, but where its two strongest independent approaches actively disagree.
Normalize the combined belief to `[0,1]`, write to the required format, and
verify the result isn't simply the average of the two inputs (correlation
check against the naive mean) before presenting it for download.

**Study target:** the highest-scoring submission on our sites,
[`GEMSDOE32 h33-h33-2-b2` (0.2778)](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html).
Why it scored: the DTI metric is a *budget* — every emitted pixel costs
`0.2·(1−kernel-weight)` in false-positive mass and earns at most its kernel
credit; the dotted family thins a thick detector field to ~37.7k well-spaced
dots (min spacing ≈283 m) so each dot clears the credit bar `k > 0.2·DTI`
(≈0.052–0.055). Can we beat it? Only by raising credit density or adding
corroborated off-catalogue detections — see `docs/hypotheses.html`.

**Public target to beat:** 0.3195 was quoted as the current top; the
GEMSDOE32 site read #1 = 0.3262 on 2026-10-04. Leaderboard facts are
recorded with dates and sources in `docs/sources.html`; we do not scrape the
leaderboard (DrivenData ToS) — treat all numbers as point-in-time reads.

**Validation rule:** do not spend a submission slot on an idea that hasn't
beaten the current holdout best. This repo implements a spatially-blocked
holdout on two truth proxies: (1) catalogue-gap blocks of the official label
raster (60,988 px), and (2) USGS SGMC state-map faults more than 300 m from
the catalogue (61,664 px — the only populated off-catalogue fault population
in reach). Exact official metric: distance-weighted Tversky, α=0.2, β=0.8,
triangular kernel R=300 m, graded predictions (verbatim from the problem
page; implementation in `src/gemsdoe48/metric.py`, unit-tested against a
literal transcription and hand-computed cases).

**New-hypothesis pipeline:** every session should generate 3–5 candidate
geological hypotheses not yet tried, each naming the specific layer(s),
the physical signature/transform, why it should catch a fault missing from
the USGS/INGENIOUS catalogue, and how it differs from anything already
implemented; rank by expected DTI improvement vs implementation cost;
validate the top candidate on the blocked holdout before touching a weekly
slot. See `docs/hypotheses.html` for the current ranked set.

**Core values (Arena):**
*Maximize P(Win)* — every decision weighs tradeoffs and risk; submission
slots are experiments, not lottery tickets. *Own the Outcome* — we own
results end to end; failures are signals, published not dropped; every claim
carries an evidence class and a link.

**Working rules:** work line by line from official, verified, trusted
sources; provide links for manual review; no manual input required; no
hallucinations; flag irregularities for review; run three passes
(implement → review for bugs/edge cases → re-check against the original
request).

---

## Known limitations & blockers (flagged for review)

1. **No DrivenData auth in this sandbox** → cannot download
   `training_features.tif`, `labels.tif`, `sample_submission.tif`,
   `1m_DEM_links.csv` from the competition data page (login-walled).
   Workaround in use: sha256-pinned owner mirrors of `labels.tif` and
   `sample_submission.tif` from GEMSDOE24 (hashes match the GEMSDOE32
   manifest of the official files). The 419 MB feature stack is **not**
   mirrored here; detector re-training is out of scope for this repo —
   we fuse finished surfaces instead.
2. **Dropbox, raw.githubusercontent.com and S3 are TLS-blocked** from this
   sandbox (curl exit 35). All artifacts are fetched via the GitHub API raw
   media type. The organizer's `example_submission.tif` / `existing_faults.tif`
   Dropbox links could not be fetched directly; grid identity is instead
   pinned by the sha256-verified mirrors above.
3. **Holdout truth is proxy truth.** Catalogue truth cannot reward genuinely
   new faults; SGMC off-catalogue truth resembles but is not the hidden
   expert-mapped set. No organizer score exists for anything in this repo
   until it is submitted.
4. **Leaderboard reads are point-in-time** (ToS forbids scraping); the
   "current best" numbers (0.2778 own, 0.3195/0.3262 public) date from
   2026-10-03/04 reads on the sibling sites.

## Next session — suggested work (in priority order)

1. **File the submission** on an account with DrivenData access; record the
   organizer score receipt in `evidence/` (this converts CLAIM → RECEIPT).
2. **Build hypothesis H49-2** (paleo-discharge × dilational stepover jogs):
   the GDR paleo + 2-m-probe rasters are already mirrored in GEMSDOE30 and
   fetchable here via the GitHub API; validate on the blocked SGMC holdout
   against the shipped DS support before spending any slot.
3. **LOSFO far-field falsification** of the shipped file and of H49-2: remove
   whole fault systems with a 600 m buffer and re-score; a gain that vanishes
   in the far field is catalogue-adjacency leakage.
4. **Re-verify grid inputs against Dropbox** from an unrestricted machine
   (IR-48-01): fetch `example_submission.tif` / `existing_faults.tif`
   directly and compare against the sha256-pinned mirrors.
5. **Place the training data** (`training_features.tif`, `labels.tif`,
   `sample_submission.tif`, `1m_DEM_links.csv`) into `data/` on an
   unrestricted machine, then `python3 scripts/prepare_data.py`-style
   preparation unlocks detector re-training (GPU needed).

## Reproduce

```bash
pip install rasterio scipy numpy
python3 tests/test_metric.py          # 8/8 metric unit tests
python3 scripts/build_submission.py   # rebuilds the submission + evidence
python3 scripts/validate_holdout.py   # blocked holdout gate (~5 min)
```

## Layout

```
docs/            GitHub Pages site (index.html = executive summary + download)
docs/downloads/  submission TIF + diagnostic layers (the deliverables)
src/gemsdoe48/   metric, Dempster-Shafer fusion, I/O, format audits
scripts/         build + validation entry points
tests/           metric verification suite
data/raw/        sha256-pinned input rasters + receipts
evidence/        JSON evidence receipts (build, holdout gate)
external_ref/    cloned official reference solution (gitignored)
```
