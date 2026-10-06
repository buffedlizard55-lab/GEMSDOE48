# GEMSDOE48 — DOE GEMS Prize (DrivenData #306): conflict-preserving fault evidence fusion

> **Start every session here.**
> **Core values:** **Maximize P(Win)** — pick measured, auditable experiments over hopeful slot spending.
> **Own the Outcome** — diagnose failures, fix them, publish uncertainty, and never promote a proxy result to truth.

---

## 1 · Standing project prompt (verbatim intent, normalised — read before every change)

```
Review the repo.

HIGHEST URGENCY: generate a UNIQUE TIF submission for the competition. Do not copy a previous
submission unless it is for learning and education. The deliverable must be unique.

Combine the two best-performing families with a rule that preserves disagreement instead of
averaging it away: the spacing-tuned "dotted" family (up to 0.2778) and the tip/step-over family
(0.26-0.27). A naive weighted average washes out exactly the information in where they disagree.
Use Dempster-Shafer evidence theory (Dempster 1967; Shafer 1976), already established in GIS
favorability mapping as an alternative to weights-of-evidence, and combine the best dotted-family
surface with the best tip-family surface. Carry forward a mass of "uncertain/unassigned" belief
wherever the sources disagree. Treat the unassigned-belief mass as its own diagnostic layer so a
geologist can see not just where the model believes there is a fault, but where its two strongest
independent approaches actively disagree. Normalize the combined belief to [0,1], write to the
required format, and verify the result is not simply the average of the two inputs (a correlation
check against a naive mean will show this) before presenting it for download.

Before implementing, generate 3-5 candidate geological hypotheses not yet tried, each naming the
specific layer(s) involved, the physical signature targeted (e.g. an edge-detection or curvature
transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one
already in it, and how it differs from anything already implemented in this repo. Rank them by
expected DTI improvement and implementation cost. Validate the top candidate on the spatially
blocked holdout set before touching a weekly submission slot - do not spend a slot on an idea that
has not beaten the current holdout best. If a candidate cannot be validated without new external
data, name the specific free official source needed and check it is obtainable before proposing it
as viable.

Site requirements: the downloadable submission TIF must be obvious at the very top of the site,
with an executive-summary subpage explaining exactly how to submit into the contest. Every file
needs a unique name and a paste-ready short note. The portal once rejected an upload with
"Predicted values must be in range [0, 1]", so re-open the written bytes and verify every cell is
finite and inside [0,1]. Work line by line, verify from official verified trusted sources, provide
links for manual review, flag irregularities, no hallucinations. Run the task in three passes:
implement and verify; review for bugs, missing requirements, incorrect assumptions and edge cases
and fix them; re-check against the original request and improve accuracy, reliability,
completeness and code quality. Finally open a pull request and merge it, and list the remaining
work and limitations for the next session.

Competition target: place as high as possible on the leaderboard of
https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ .
Study the highest-scoring campaign submission (GEMSDOE32, 0.2778), explain why and how it scored
what it did, and whether a higher score is achievable. Do deep, autonomous, critical,
scientifically grounded research; find data sources others overlook; be contrarian but rigorous;
store everything for reuse by other projects.
```

---

## 2 · Immediate deliverable — download

**[⬇ Submission GeoTIFF](docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-e6f08013888b.tif)** · [single-member ZIP](docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006.zip)

| field | value |
|---|---|
| Submission name | `GEMSDOE48-H49-DS-CONFLICT-BALANCED-e6f08013888b` |
| Note to paste | `H49 Dempster-Shafer fusion of dotted + tip/step-over families; Yager keeps conflict as unassigned mass; pignistic-ranked, spatially balanced 47,905-cell emission; all-finite [0,1]; id e6f08013888b` |
| SHA-256 (TIF) | `e6f08013888b625db7d187d79bb75ba36c45d068081b77a3dd405ab7eec3d472` |
| SHA-256 (ZIP) | `b8f4dabf32fd18dfe9cab5de93adcf2d770f0aecf014fdffa555512a7c191b0b` (deterministic archive) |
| Grid | 1 band float32, EPSG:32611, 100 m, 3730 × 3292, origin 243350 / 4508550 |
| Values | all 12,279,160 cells finite; min 0.0, max 1.0; 0 out-of-range; no NaN; no nodata tag; 47,905 positive cells |
| Diagnostics (do **not** submit) | [unassigned belief](docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-unassigned-diagnostic.tif) · [normalised belief field](docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-belief-field.tif) |
| Audit | [audit.json](docs/downloads/gemsdoe48-h49-ds-conflict-balanced-20261006-audit.json) |

Executive summary and submission walkthrough: **[`docs/index.html`](docs/index.html)**

---

## 3 · What this session established (PhD-level answer, each item measured)

**Why 0.2778 won.** The official metric collapses to `1/DTI = α + α(F/T) + β(K/T)` with α = 0.2,
β = 0.8. One unit of emitted mass raises the denominator by exactly α *wherever it lands*, so a
cell earns its place only if its credit exceeds α·DTI ≈ **0.056** — i.e. it must sit within about
284 m of a *hidden* fault pixel. Every score-gaining move in this campaign's history was a
deletion of mass below that bar (121k → 60k → 44k → 40k → 37.6k cells produced
0.1922 → 0.2477 → 0.2600 → 0.2708 → 0.2778). H33-2-B2 leads the family because it is the
best-pruned emission, not because it is the best-calibrated probability field.

**Can we beat 0.2778?** Not with these two families alone. Every reachable direction was measured
and the dotted parent sits at a local optimum:

| direction | measurement | verdict |
|---|---|---|
| add the tip family's extra cells as a raw union | 0.0357 proxy credit/cell, 0.58 × the acceptance bar | reject |
| add them through the fused, spatially balanced allocation | **0.0599** proxy credit/cell, 0.81–1.08 × the bar, +0.0068 proxy DTI and 10/11 blocks | **adopt (break-even to slightly positive)** |
| add "compromise" cells at positions neither parent emitted | only viable under the spacing constraint; accounts for 6,409 cells | adopted inside the budget |
| prune by lineament coherence / density / component size (**hypothesis H-A**) | every quintile carries 0.13–0.17 proxy credit/cell vs a 0.037 removal threshold | **falsified** |
| raise the budget beyond the union | proxy approves it, but the proxy is 5.7 × denser than the hidden set and the live record is monotone against | not adopted |
| graded "belief-as-value" emission | halves the credit of exactly the cells that carry it; naïve mean scores 0.0903 vs 0.1029 | reject |

**Instrument calibration is the decisive check.** The lineage `d28 (44,090) ⊃ h27-4 (40,199) ⊃
h33-2-b2 (37,654)` lets us score the two removal sets whose live outcomes are known. The proxy
ranks both below the bar, and group B's live/proxy credit ratio (0.76) reproduces GEMSDOE32's
independently measured safety factor of 2.08 to within 3 %. That is what licenses the decision
above. See [`docs/data/h49-instrument-calibration.json`](docs/data/h49-instrument-calibration.json).

**Corrections carried forward and re-verified.** (i) Classical normalised Dempster's rule divides
by 1 − K and deletes conflict; Yager's modified rule, which transfers K to m(Θ), is the rule that
actually satisfies the brief's "preserve disagreement" requirement. (ii) The previous session's
proxy used a nearest-cell TP and ignored the magnitude of p in TP, so it could not see that
halving a value halves the credit; the metric is now implemented literally and brute-force
verified. (iii) The brief's "0.3195 is the highest score" is stale: the official leaderboard
retrieved 2026-10-06 is led by **0.3774**, with 0.3195 at rank 7 and our 0.2778 at rank 13.

---

## 4 · Method in one page

1. **Parents** (SHA-256 pinned): dotted = GEMSDOE32 `h33-h33-2-b2` (37,654 cells, owner-reported
   0.2778); tip = GEMSDOE33 `h33d-analog-tip-stepover-r30` (41,865 cells, owner-reported 0.2632).
   Intersection 31,614 / dotted-only 6,040 / tip-only 10,251 / union 47,905, Jaccard 0.660.
2. **Evidence**: each sparse family becomes `s(x) = max over its cells of k(d(x,y))` using the
   competition's own triangular kernel — "the credit this cell would realise if a truth pixel sat
   on it".
3. **Masses**: `m(F) = r·s`, `m(N) = r·(1−s)`, `m(Θ) = 1−r`, with preregistered `r_dotted = 0.90`
   and `r_tip = 0.90 × 0.8915 = 0.802` (0.8915 = the ratio of measured live credit per dot).
4. **Combination**: conjunctive rule; conflict `K = a_F b_N + a_N b_F`; **Yager** transfer of K to
   m(Θ). Classical Dempster belief is computed too, so the difference is shown, not asserted.
   Mass-conservation error 2.2 × 10⁻¹⁶.
5. **Decision score**: pignistic probability `BetP = Bel + m(Θ)/2`.
6. **Emission**: admit cells in descending BetP subject to a 2.5-cell minimum separation until the
   budget |dotted ∪ tip| = 47,905 is reached; emit p = 1 on admitted cells (optimal, because credit
   and cost are both linear in p while credit per truth pixel is capped).
7. **Diagnostics**: unassigned mass `m(Θ) + K` and the min-max normalised belief field as separate
   GeoTIFFs.

Full write-up: [`docs/method.html`](docs/method.html).

---

## 5 · Blocked holdout (16 blocks, 11 with ≥50 truth pixels), official metric, SGMC off-catalogue truth

| emission | cells | proxy DTI | Δ vs dotted parent | block mean | blocks won |
|---|---:|---:|---:|---:|---:|
| **H49 submission** | 47,905 | **0.102942** | **+0.006809** | 0.098403 | 10/11 |
| naïve union | 47,905 | 0.098979 | +0.002846 | 0.094742 | 9/11 |
| tip parent | 41,865 | 0.097094 | +0.000961 | 0.093188 | 8/11 |
| dotted parent | 37,654 | 0.096132 | 0 | 0.093036 | — |
| weighted mean 0.64/0.36 | 39,170 | 0.091067 | −0.005065 | 0.087600 | 0/11 |
| naïve mean 0.5/0.5 | 39,760 | 0.090303 | −0.005829 | 0.086703 | 0/11 |
| intersection only | 31,614 | 0.082233 | −0.013899 | 0.079188 | 0/11 |

Second proxy (≥100 m from the catalogue) gives the same ordering: H49 0.123756 > union 0.119095 >
tip 0.116779 > dotted 0.092893. **These are proxy DTIs, not leaderboard scores.**

Not-the-average check: Pearson r vs naïve mean 0.8831 (max abs difference 1.0); not pixel-identical
to the dotted parent, the tip parent, the union or the mean; Jaccard with the dotted parent 0.786.

---

## 6 · Hypotheses for the next session

Five are written up with layers, physical signature, catalogue-gap argument, ranking, cost and
source on [`docs/hypotheses.html`](docs/hypotheses.html). Headline:

1. **Blind-geothermal targeting** — 2 m temperature probes + spring/well chemistry + paleo-sinter
   (GDR 1391, CC BY 4.0) as a prior over any lineament detector. Highest expected value: it attacks
   `F/T` directly.
2. **Seismicity lineaments** from the INGENIOUS earthquake-density models / ANSS ComCat.
3. **Strain-rate residualisation** against the catalogue (geodetic shear/dilation models).
4. **1 m / 3DEP scarp matched filter** — high cost, high ceiling.
5. **Cultural/agricultural false-lineament masking** — bounded precision gain.

**Obtainability check executed:** `dropbox.com`, `usgs.gov`, `earthquake.usgs.gov`,
`gdr.openei.org` and `sciencebase.gov` all fail TLS at the socket from this sandbox (curl exit 35,
HTTP 000), while `api.github.com` and `pypi.org` return 200. Page text is retrievable, binary
downloads are not — so none of the external-data hypotheses can be validated here. They are
therefore ranked, not proposed as ready.

---

## 7 · Reproduce

```bash
python -m venv .venv
.venv/bin/pip install -e . pytest
bash scripts/fetch_inputs.sh                  # gh-authenticated, SHA-256 pinned
.venv/bin/python scripts/analyze_parents.py    # decomposition + live-anchored inversion
.venv/bin/python scripts/calibrate_instrument.py
.venv/bin/python scripts/test_coherence_pruning.py
.venv/bin/python scripts/test_budget_neutral.py
.venv/bin/python scripts/budget_sweep.py
.venv/bin/python scripts/build_submission.py   # emit, re-read, audit
.venv/bin/python scripts/marginal_value.py     # marginal acceptance analysis
.venv/bin/pytest -q
```

Raw inputs are Git-ignored; the small deliverables, audits and receipts are versioned.

## 8 · Repository map

```
src/gems48/metric.py              official distance-weighted Tversky index (brute-force verified)
src/gems48/evidence.py            kernel-support evidence, Shafer discounting, Yager/Dempster, pignistic
scripts/fetch_inputs.sh           hash-pinned input restore (GitHub API)
scripts/analyze_parents.py        parent decomposition + live-anchored inversion
scripts/calibrate_instrument.py   calibration against the two known-outcome removals
scripts/marginal_value.py         marginal acceptance of every candidate group
scripts/test_coherence_pruning.py hypothesis H-A (falsified)
scripts/test_budget_neutral.py    budget-neutral fusion at the live-tuned budget
scripts/budget_sweep.py           marginal credit vs budget
scripts/build_submission.py       emit + independent re-read + audit + ZIP
docs/                             GitHub Pages site (summary, method, hypotheses, sources)
docs/data/*.json                  every measurement receipt
docs/downloads/                   deliverable, diagnostics, ZIP, audit
```

## 9 · Limitations and what the next session must do

1. **No DrivenData session** — the agent cannot spend a submission slot and cannot read a private
   score; portal acceptance is unverified by us.
2. **The proxy is not the truth**, and its resolution is limited: SGMC is a public compilation,
   5.7 × denser than the hidden set, so it systematically over-rewards mass, *and* both proxy
   protocols rank the tip family ~0.001 proxy DTI above the dotted family even though the live
   board has the dotted family ahead by 0.0146. Proxy gaps below ~0.005 carry no information.
   All addition decisions therefore use the *live* bar converted into proxy units, never the
   proxy's own bar. A third, independent protocol (four fixed quadrants, same metric and truth
   mask) also puts the submission first: H49 0.102791 vs union 0.099052 vs tip 0.097561 vs dotted
   0.096700, 4/4 quadrants positive —
   [`docs/data/proxy-validation.json`](docs/data/proxy-validation.json).
3. **The two parents are 84 % co-located**, so the "independent evidence sources" assumption behind
   Dempster–Shafer is only partly satisfied.
4. **Owner-reported anchors** (0.2778, 0.2632) are not organiser receipts; no hash ties them to
   bytes.
5. **The bridged template is not the organiser's sample submission** — `sample_submission.tif`
   (SHA-256 `2176d08e…`) is pixel-identical to `labels.tif` with NaN outside the footprint. Its grid
   matches the published format and prior submissions built on it have scored, so it is used as the
   grid/footprint reference, but this is flagged rather than assumed.
6. **No external data is obtainable here** (section 6). The next session should run
   `scripts/fetch_inputs.sh` plus the GDR/USGS downloads from an unrestricted machine, then
   validate hypothesis 1 (blind-geothermal targeting) on the frozen 16-block holdout before any
   slot is spent.
7. **The 419 MB official feature stack** is required for any new detector built from geophysics; it
   needs a DrivenData login or the owner's mirror.
