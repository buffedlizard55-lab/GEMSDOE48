> **Historical main-branch README snapshot (after PR #5).** Preserved for provenance; its candidate recommendations and validation claims are superseded by the current README and [current validation](../validation.html). Any six-hour leaderboard-feed instructions in this archive are historical: the current branch disables that workflow under the Terms-of-Use review, and the retained parser has no network-fetch path.

---

# GEMSDOE48 — Dempster–Shafer fault-discovery research for the DOE GEMS Prize (DrivenData #306)

**Live site:** <https://buffedlizard55-lab.github.io/GEMSDOE48/docs/index.html> ·
**How to submit:** [docs/executive-summary.html](https://buffedlizard55-lab.github.io/GEMSDOE48/docs/executive-summary.html) ·
**Competition:** <https://www.drivendata.org/competitions/306/competition-doe-gems/> ·
**Metric & format:** [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)

> **START OF EVERY SESSION:** read this README top to bottom, including the
> [full project brief](#the-project-brief-verbatim) at the end. Then read
> [`docs/md/next-steps.md`](../md/next-steps.md) and
> [`docs/md/irregularities.md`](../md/irregularities.md).

> ### Our Core Values
> **Maximize P(Win).** In every decision we weigh tradeoffs, assess risk, and choose the path
> that maximizes the probability of winning. We set aside emotion and make tough decisions.
> **Own the Outcome.** We own results end to end. When problems arise and we have the means to
> act, we act. Failure and success are signals we use to improve.
> *Applied here:* our own validation instruments were measured against live scores before being
> trusted, and their failures are published (IR-48-05, IR-48-06).

## Current decision — 2026-10-06 (overrides older upload recommendations below)

**No candidate is cleared for a weekly competition slot.** The Yager conflict-transfer raster
requested in this work loses to the dotted parent, tip parent, and naïve mean on the corrected
SGMC proxy, including every quadrant. The earlier v1 apparent pass is retracted. H48-1's binary
Dempster candidate also did not beat its spatial holdout best; its owner-built LSI estimate is
not reliable enough to call it a tie or a score forecast. No upload, portal acceptance, or private
score has been observed.

- **Yager research raster:** [`gemsdoe48-h48-ds-yager-conflict-20261006.tif`](../downloads/gemsdoe48-h48-ds-yager-conflict-20261006.tif), one-band float32, EPSG:32611, 100 m, 3730×3292, range [0,1], SHA-256 `fe68ae6f57be013e26d20006551b43cd84bb5fe4a0b07d1d10ce4725c90fd16c`. It is not the naïve mean. The separate unassigned-belief diagnostic is [`here`](../downloads/gemsdoe48-h48-ds-yager-conflict-20261006-unassigned-diagnostic.tif) (**do not submit**).
- **Corrected SGMC proxy DTI:** Yager 0.08407; tip 0.09709; dotted 0.09613; naïve mean 0.09030. Proxy only—not private truth or organizer score. See [`v2 receipt`](../data/proxy-validation.json); [`v1 retraction`](../data/proxy-validation-v1-retracted.json).
- **Format caveat:** all cells are finite and in [0,1], with zero outside. This passes a local range audit but does not establish the cause of the reported portal error or demonstrate portal acceptance; it also does **not** satisfy the official page's null/NaN-outside language. The portal was not tested.
- **Suggested name:** `GEMSDOE48-H48-DS-CONFLICT` · **suggested short note:** `H48 dotted+tip Yager fusion; distinct in bounded scan; SGMC proxy gate failed; do not spend slot`.
- **PR #6 DS48 emission (comparison only):** [`gemsdoe48-ds48-emission.tif`](../downloads/gemsdoe48-ds48-emission.tif), 37,654 px; byte-format checks passed. It scored 0.09068 on the owner-derived SGMC off-catalogue proxy versus 0.09613 for the dotted baseline (about 5.7% lower). The separate catalogue-proximity proxy is anti-monotone with the known live ladder (Spearman −1, n=4), so that apparent gain cannot clear it. No organizer score or portal acceptance exists. [PR #6 research site](../ds48-fusion/index.html).

This result supersedes any prior page/README phrase that says to upload a fusion. H48-1, the PR #6 DS48 emission, and the Yager raster remain research artifacts only. **None is cleared for a weekly slot**; do not treat a download button or a format audit as a submission recommendation.

---

## H48-1 Dempster file (historical research candidate; not slot-cleared)

**[`docs/downloads/gemsdoe48-h48-1-ds-fusion-b2xh32tip-20261006-407bb7f4-zeros.tif`](../downloads/gemsdoe48-h48-1-ds-fusion-b2xh32tip-20261006-407bb7f4-zeros.tif)**
· [.zip](../downloads/gemsdoe48-h48-1-ds-fusion-b2xh32tip-20261006-407bb7f4-zeros.zip)
· [receipt](../downloads/receipt-gemsdoe48-h48-1-ds-fusion-b2xh32tip-20261006-407bb7f4-zeros.json)

| | |
|---|---|
| sha256 | `6cb2aab8dbd71335152dea7e2fa442126abffc609b426286f5a171f14353b454` |
| bytes | 226,886 |
| format | single-band float32 GeoTIFF · EPSG:32611 · 100 m · 3730 × 3292 · transform identical to `sample_submission.tif` · same TIFF layout as the scored 0.2778 file |
| range | **all finite, min 0.0, max 1.0, 0 NaN.** These are local byte checks, not proof of the reported error's cause or a portal fix. Like the Yager TIFF, it uses finite zeros outside despite the official null/NaN wording; portal acceptance is untested |
| content | 37,754 dots = all 37,654 dots of h33-2-b2 (live 0.2778) + 100 tip-family dots accepted by Dempster–Shafer fusion; 0 dots within 200 m of the catalogue |
| historical label | `GEMSDOE48-H48-1-DS-fusion` (research only; not slot-cleared) |
| historical note | `GEMSDOE48 H48-1 Dempster-Shafer fusion b2(0.2778) x h32-1 tip(0.2649); pignistic>0.5, NMS 2.8px; 37754 dots, 0 within 200m of catalogue` (do not use to imply clearance) |
| bounded uniqueness | support differed from the 80 sibling GeoTIFFs checked in that session; not a global uniqueness guarantee |
| holdout verdict | did not beat b2 on the reported SGMC quadrants (2/4); owner-built LSI estimates 0.26336 vs 0.26351 but has negative top-8 rank power. No organizer score or tie claim. |

Diagnostic layers (for geologists, not for submission) are in `docs/downloads/diagnostics/`:
normalised Dempster belief, **conflict K (where the two families disagree)**, Yager m(Θ), and
Dempster m(Θ).

## ⚠ Competition-slot decision (three DS files plus corrected Yager proxy)

| file | evidence status |
|---|---|
| `gemsdoe48-h48-1-ds-fusion-b2xh32tip-20261006-407bb7f4-zeros.tif` | **Do not upload yet.** It did not beat b2 on the reported SGMC quadrants; the LSI instrument cannot rank this close to the top family, and portal acceptance is untested. |
| `gemsdoe48-h48-ds-yager-conflict-20261006.tif` | **Do not upload.** Corrected DTI proxy 0.08407 vs tip 0.09709, dotted 0.09613, and naïve mean 0.09030; lost all four quadrants. |
| `gemsdoe48-ds-dotted-x-tipstepover-20261006T201749Z-95897e3f8125-decision-zeros.tif` | **Do not upload on prior LSI evidence alone.** Owner reports 0.25903 LSI estimate vs b2 0.26351; no private or organizer score verified. |

The unique TIF artifacts are retained for research/download because the brief requests a genuinely new raster, but **none is slot-cleared**. The historical pages in [`docs/prev-pr1/`](../prev-pr1/) and [`docs/prev-pr2/`](../prev-pr2/) are not current submission instructions.

## Key findings (measurements, owner reports, and model estimates are distinct)

1. **Owner-reported 0.2778 sequence:** the project history associates that value with b2, whose
   37,654 positive cells are verified locally. The reported sequence is consistent with a
   precision/removal hypothesis, not proof of causation or discovery performance; no local TIFF
   hash is tied to an organizer receipt. See the [uncertainty-aware explanation](../research.html).
2. **The two "families" overlap heavily.** h32-1 shares 36,874 of b2's 37,654 pixels. This is a
   measured support overlap and violates the independence assumption needed for a calibrated
   Dempster fusion; it does not itself bound any hidden-score change.
3. **The catalogue-based and SGMC instruments have limitations.** The earlier 17-anchor SGMC
   calibration (Spearman −0.17) and later four-anchor catalogue-proximity calibration (Spearman
   −1) are distinct proxy tests, not forecasts. Neither is used to claim private-score gain.
4. **The LSI inversion is a model, not a score.** Its historical leave-one-out rank statistics
   (0.81 over 17 reported anchors, −0.69 within the top 8) are owner-derived and model-dependent;
   they do not resolve close candidate ordering.
5. **Board:** a human-readable 2026-10-06 snapshot showed a leader at **0.3774** and a 0.2778 row
   at rank 13. The row's account and any local TIFF match are unverified. Native 1 m LiDAR is a
   research path; full coverage and holdout gain remain unverified.
6. **Theory correction:** Dempster's rule normalises conflict away. Yager's rule transfers conflict
   to unassigned mass. The repo keeps both as research diagnostics; neither fusion is slot-cleared.

## Reproduce

```bash
pip install -r requirements.txt
bash scripts/run_all.sh        # fetch (sha256-verified via gh) -> instruments -> fusion -> file -> site -> tests
```

| path | role |
|---|---|
| `src/gems48/metric.py` | exact DTI (tested vs brute force + organiser example) |
| `src/gems48/ds.py` | BPA, Dempster, Yager, pignistic, NMS |
| `src/gems48/lsi.py` | live-score inversion instrument |
| `scripts/build_ds.py` · `write_submission.py` | fusion variants · file, audit, receipt |
| `registry/live_scores.json` | owner-reported live scores (append new ones here) |
| `evidence/*.json` | every number quoted on the site |

## Limitations / access needed
No DrivenData login (scores are owner-reported, uploads are manual by the owner). No sandbox
egress to USGS/AWS (data jobs must run in GitHub Actions). 2 CPU / 3 GB RAM / no GPU. Full list:
[next steps](../md/next-steps.md).

---

## The project brief (verbatim)

<details open><summary>Owner's brief, pasted 2026-10-06. Read at the start of every session. Wording is verbatim; only the per-site results list was reflowed to one line per site.</summary>

Review the repo.

THE FOLLOWING IS THE HIGHEST URGENCY AND MUST BE FOLLOWED!

MUST GENERATE A UNIQUE TIF SUBMISSION FOR THE COMPETITION.  DO NOT COPY A PREVIOUS SUBMISSION UNLESS IT'S FOR LEARNING AND EDUCATION.  BUT WE MUST GENERATE A UNIQUE TIF SUBMISSION.

There should be an easy to download submission tif file as described by the prompt.  Read the entire prompt.

Combine your two best-performing families with a rule that preserves disagreement instead of averaging it away. The spacing-tuned "dotted" family (up to 0.2778) and the tip/step-over family (0.26–0.27) are your two strongest, independently-built results, and a naive weighted average of the two surfaces would wash out exactly the information in where they disagree. Dempster-Shafer evidence theory (Dempster, 1967; Shafer, A Mathematical Theory of Evidence, 1976) — already established in exactly this kind of GIS favorability mapping as an alternative to weights-of-evidence — combines two evidence sources via Dempster's rule of combination, which explicitly carries forward a mass of "uncertain/unassigned" belief wherever the sources disagree rather than forcing it into a single blended probability. Combine your best dotted-family surface and best tip-family surface this way, and treat the resulting unassigned-belief mass as its own diagnostic layer — a geologist reading this submission can see not just where the model believes there's a fault, but where its two strongest independent approaches actively disagree. Normalize the combined belief to [0,1], write to the required format, and verify the result isn't simply the average of the two inputs (a quick correlation check against a naive mean will show this) before presenting it for download.

The following sites should serve as a starting point for understanding how to generate TIF submissions.  These websites are researched, and tested and have generated TIF submissions.  But we need to generate high scoring submissions.

Here are the results from submissions into the competition, separated by ....:

https://buffedlizard55-lab.github.io/GEMSDOE/docs/index.html — gems-submission-20260925T001403Z-7f00890a: 0.1563
....
https://buffedlizard55-lab.github.io/6GEMSDOE/ — gems6_hgb88-topk03_33cec71ff0: 0.0286
....
https://buffedlizard55-lab.github.io/GEMSDOE3/docs/index.html — pindrop-v4-nodes-20260925T152420Z-f347b70daa: 0.1193; pindrop-v4-discovery-20260925T152423Z-37f9d5b855: 0.0830; pindrop-v4-ridge-20260925T152422Z-4e03fc9705: 0.1152
....
https://buffedlizard55-lab.github.io/GEMSDOE2/docs/index.html — gemsdoe2-dual-family-union-20260925T160406Z-f68e590f: 0.1560
....
https://buffedlizard55-lab.github.io/GEMSDOE4/ — gems-submission-20260926T163915Z-237f0063: 0.0343
....
https://buffedlizard55-lab.github.io/5GEMSDOE/docs/index.html — gems-submission-20260926T175114Z-7f00890a: 0.1563
....
https://buffedlizard55-lab.github.io/7GEMSDOE/ — lidarscarp-ridge-top2pct-36c3a3f341c8: 0.1461
....
https://buffedlizard55-lab.github.io/8GEMSDOE/ — Hedge-v2_submission: 0.1563
....
https://buffedlizard55-lab.github.io/GEMSDOE9/docs/index.html — 2314b599: 0.0107
....
https://buffedlizard55-lab.github.io/11GEMSDOE/docs/index.html — gems-structural-area06-v1: 0.0202
....
https://buffedlizard55-lab.github.io/12GEMSDOE/docs/index.html — r7-nms3-dem10-scarp_0c9199f14e62: 0.1294; r7-nms3-dem10-scarp_0c9199f14e62_allfinite: 0.1294
....
https://buffedlizard55-lab.github.io/15GEMSDOE/docs/index.html — gems-tso1-20260929T005627Z-conj_alteration_mag: 0.0782
....
https://buffedlizard55-lab.github.io/14GEMSDOE/docs/index.html — GEMS_r5-geom-horse-ensemble_20260929T154852Z_ccbe1de0_site_e96e942f: 0.0020
....
https://buffedlizard55-lab.github.io/17GEMSDOE/ — 17GEMSDOE_F-ensemble-2pct_20260930T050626Z: 0.0187
....
https://buffedlizard55-lab.github.io/18GEMSDOE/ — H19-C_20260930T212401Z_c11e495e: 0.0297
....
https://buffedlizard55-lab.github.io/19GEMSDOE/docs/index.html — h19-4-multiline-corroborated-openness-thermal-pop-20260930-691e4dfa-nan: 0.1894; h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan: 0.1922
....
https://buffedlizard55-lab.github.io/GEMSDOE10/ — h16-continuation-20260927T065521077735Z-3431b83c7c: 0.0461; h20-dem10-scarp-thin-20260927T155223039488Z-ffc91a1686: 0.0921; H25-ctx-ridge-20260927T232947704150Z-6452ae1d00: 0.1280; h28-dotted-ridge-20260928T020256236880Z-6452ae1d00: 0.1839
....
https://buffedlizard55-lab.github.io/13GEMSDOE/ — 20261001_r13-lattice-s5_v2_nan-outside: 0.0904
....
https://buffedlizard55-lab.github.io/16GEMSDOE/docs/index.html — h16-1-topo-geophys-baseline-ridges-20260930-df20f65e-nan: 0.1855; h18-3a-topo-geophys-x-complexity-prior-20260930-c502dfab-nan: 0.0976; h18-4-usgs-geologic-map-faults-gap-20260930-aef8f42c-nan: 0.0360
....
https://buffedlizard55-lab.github.io/GEMSDOE21/ — h19-4-reference-20260930-691e4dfa: 0.1894
....
https://buffedlizard55-lab.github.io/20GEMSDOE/docs/index.html — h20-1-sarnnpu-powerlaw-pi0363-tilt-wingcrack-20260930-be0e8f6b-nan: 0.1890; h20-5-continuous-pu-proxy-unverified-20260930-824ce73a-nan: 0.1859
....
https://buffedlizard55-lab.github.io/GEMSDOE22/docs/index.html — h23-a-dti-optimal-emission-6pct-20261002-e2ec4b49-nan: 0.1002; h23-b-dti-optimal-emission-10pct-20261002-86176698-nan: 0.0748
....
https://buffedlizard55-lab.github.io/GEMSDOE23/ — h30-arrangement-matched-habitat-20261002-0d4e02e8-nan: 0.1352
....
https://buffedlizard55-lab.github.io/GEMSDOE24/ — h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan: 0.2477
....
https://buffedlizard55-lab.github.io/GEMSDOE25/ — dotted-h19-5-d2-8-20261002-e56ea318af89-nan: 0.2600
....
https://buffedlizard55-lab.github.io/GEMSDOE26/ — dilcond-oof-v1-20261003-47629f496133-nan: 0.1223
....
https://buffedlizard55-lab.github.io/GEMSDOE27/ — topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan: 0.2449
....
https://buffedlizard55-lab.github.io/GEMSDOE28/ — h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan: 0.2708; h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan: 0.2649; h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan: 0.2710; h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE29/docs/index.html — efd28-repro-20261003-1cc7dc534d51-nan: 0.2600; repo-c0-habitat-emission-20261003-a4d439b07426-nan: 0.0041; sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan: 0.0512; wormrank-d28-20261003-59dcaf6dd11d-zeros: ; wormsurv-filter-20261003-921f10960d6e-zeros: ; xfit-c0-habitat-20261003-ca879db0089a-zeros: ; xfit-h41-union-qfaults-20261003-9edb34b99e3a-zeros:
....
https://buffedlizard55-lab.github.io/GEMSDOE30/ — d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca: 0.2600
....
https://buffedlizard55-lab.github.io/GEMSDOE31/docs/ — h27-4-solo-d28-20261004-8acb75e1-nan: 0.2708
....
https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html — h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778
....
https://buffedlizard55-lab.github.io/GEMSDOE33/ — h33d-analog-tip-stepover-r30-20261004-cb490425926e: 0.2632
....
https://buffedlizard55-lab.github.io/GEMSDOE34/docs/index.html — h34-scatter-q50-arr-matched-20261004T223317Z: 0.0778
....
https://buffedlizard55-lab.github.io/GEMSDOE35/docs/index.html — h35-06-aaa86efb25-20261004T225420098147Z-candidate: 0.0418
....
https://buffedlizard55-lab.github.io/GEMSDOE36/docs/ — anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros: 0.2750
....
https://buffedlizard55-lab.github.io/GEMSDOE37/ — h6-physics-dotted-80k-20261005T055000Z-0bef9211631c: 0.1193
....
https://buffedlizard55-lab.github.io/GEMSDOE38/docs/index.html — D-step-3p0-07pct-tipProt-20261005-ecfbf59e2b48-zero: 0.0763
....
https://buffedlizard55-lab.github.io/GEMSDOE39/ — h40-e-disc-h40e-30k-zeros: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE40/docs/index.html — h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1: ; h8-euler-lineament-depthcluster-20261006-785c4f5d5ce1-hard: ; h45-eulerdepthreadcluster-20261006-f28e5cff6826-zeros: (no scores)
....
https://buffedlizard55-lab.github.io/GEMSDOE41/docs/index.html — h42-submission-primary: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE42/docs/index.html — xscale-worm-persistence-20261006T000541Z-nan: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE43/docs/index.html — sup01-hgb21-sep40-n40000-20261006-bc2e4e9a8d6f-nan: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE44/docs/ — h46-twostageAB_20261006T160000Z_b0cfe956-zeros: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE45/ — h51-km-faultzone-20261006-zeros: (no score)
....
https://buffedlizard55-lab.github.io/GEMSDOE46/ — r11f-scarp-radiometric-fusion-00e049b51218-zeros: ; r12-scarp-rad-concordance-23e807e2de9f-zeros: (no scores)
....
https://buffedlizard55-lab.github.io/GEMSDOE47/ — (no score) · 48GEMSDOE … 54GEMSDOE — (no scores yet)
....

WE NEED TO STUDY, ANALYZE, AND UNDERSTAND THE HIGHEST SCORE FROM THE GEMDOE SITE WHERE THE SUBMISSION TIF IS DOWNLOADED FROM WHICH IS THE FOLLOWING:

https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html — h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778

Why and how did this get the highest score and are we able to generate a submission that scores higher than 0.2778?

Answer the question using Phd level experience, knowledge, and judgement. Then use the answer to generate a unique TIF submission into the competition.  Must be unique submission unlike any within the GEMSDOE sites above.  Verify working line by line no hallucinations.

The following is the leaderboard for the competition: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/

We need to quickly look at the results and results from the GEMSDOE websites above.

Before implementing, generate 3–5 candidate geological hypotheses we haven't tried yet, each naming: the specific layer(s) involved, the physical signature being targeted (e.g., an edge-detection or curvature transform), why it should catch a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented in this repo. Rank them by expected DTI improvement and implementation cost. Validate the top candidate on our spatially-blocked holdout set before touching a weekly submission slot — do not spend a submission slot on an idea that hasn't beaten the current holdout best. If a candidate can't be validated without new external data, name the specific free, official source needed and check it's obtainable before proposing the idea as viable.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We have a good understanding of how our hypothesis, methodology, calculations, analysis are done so we should be able to figure out a way to score higher on the leaderboard using previous results and scoring that we have across the sites listed above.  We need to come up with distinct and unique strategies to score higher in this competition leaderboard.  We need to start doing heavy and deep research into the part of the project that matters the most, which is the scientific discovery of geothermal vents.  We should store all of our information and knowledge that we can gather from official verified sources.  This will serve as a starting point for other projects as well.  We need to think outside the box but still be grounded in proper scientific research, we are ultimately aiming for a top prize that many others are competing for.  So it's important to be contrarian but be smart about it.  We need to find sources of data that others are over looking or areas of the project when it comes to geothermal vents.  We need to do deep research and critical thinking and come up with new hypothesis to test.

0.3195 is the highest score right now so we need to design a new strategy, research, testing, analyzing, and generating submission system than the current website.  It should be unique, take unique approaches to generating a submission that can score higher than 0.3195.

Put this prompt into the repo readme and read it everytime we work on the project as a starting point to make sure we are building what we are aiming for and have a strong base to continue building and improving on making something useful for everyday use.  It should solve the problem of having to manually check everything ourselves and having an up to date current feed.

Review the repo.

The following is taken from the Arena AI team and I think it makes a good point on building a successful project, so let's keep the Core Values and Own the Outcome as a focal point when building, developing, researching, suggesting upgrades, and implementing the work.

Our Core Values

Maximize P(Win) — "Maximize the Probability of Winning": our decision making framework. In every decision, we weigh tradeoffs, assess risk, and choose the path that maximizes the probability that Arena succeeds. We set aside our emotions and make tough decisions in order to maximize P(Win). "Maximize P(Win)" frees us from constraints and clarifies that we must put Arena first.

Own the Outcome — We own results end to end — not just our individual slice of the work. When problems arise and we have the means to act, we do so without waiting for permission or assignment. We treat failure and success as signals and use them to improve. At Arena, we stay accountable to the final outcome.

Work line by line verifying from official verified trusted sources, provide links for manual review.  There should be no manual input, work on your own to complete tasks.  Flag any irregularities for review.  No hallucinations.

Verify no hallucinations.

The goal of this project is to get a full list that follow our requirements.  No hallucinations.  Verify line by line.

We need to focus on being able to generate a submission into the competition.

The site should be able to generate a TIF file that is required for submission.  It should be as easy as download to click a File to submit into the competition.  This needs to be in the executive summary or the very beginning of the site.  it should be obvious when you visit the site.

I tried to submit the document that i downloaded from the site but it returned this error on the submission form: "Predicted values must be in range [0, 1]"

Also we need to give it a unique name and A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Here is the submission page when i click submit file: New submission — File to submit (No file chosen). You can submit a single-band GeoTIFF (.tif) file, or a .zip file containing a single GeoTIFF, with your predictions. It must match the submission format's CRS, shape, and geotransform. You may wish to review the competition rules first. Note (optional): A short comment to help you or your team tell submissions apart later e.g. clustering with k=25

Create a executive summary subpage that explains exactly how to make a submission into the contest.

Work on the next steps from the previous sessions first.

The goal of this project is to place top of the leaderboard in this competition.  The following is the competition: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

We need to create a project that can compete and place top of the leaderboard.  We need to understand the problem, collect all the data and organize it into a clean easily auditable table with official verified links for manual verification.

This is the guidelines we need to follow. https://www.drivendata.org/competitions/306/competition-doe-gems/

Get familiar with the problem through the overview and problem description, https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/. You might also want to reference additional resources available on the about page, https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/.

Download the data from the data, https://www.drivendata.org/competitions/306/competition-doe-gems/data/, tab.

Create and train your own model. This reference solution, https://github.com/drivendataorg/gems-prize-reference-solution implements a simple approach.

Use your model to generate predictions that match the submission format.

Tell me what are you limitations and what you need access to during this project.  We will need to find free publicly available sources and data from official and verified sources if we are to use 3rd party or external data.

this pdf outlines how submissions must be entered into the competition. https://docs.nlr.gov/docs/fy26osti/96647.pdf

You must be able to do your own research, deep research, scientific literature research and organize the knowledge so that we can critically think through the problem and generate a solution through scientific and free publicly available information.  this must be done autonomously and must be constantly reviewed and improved upon.  Provide suggestions and improvements and implement them.

❌ No DrivenData auth → cannot auto-download training_features.tif, labels.tif, sample_submission.tif, 1m_DEM_links.csv from https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (verified redirect to login)

See below for links from the above site. https://gdr.openei.org/submissions/1391

Download competition data from https://www.drivendata.org/competitions/306/competition-doe-gems/data/ (requires login) to data/

See links below for competition data:
https://www.dropbox.com/scl/fi/aemhtutjgcp6tr3tint94/GEMS_96647.pdf?rlkey=rek210cj2smnmzb8n0sla1vmd&st=wz4kofki&dl=0
https://www.dropbox.com/scl/fi/6rgvnuady818ol8yqgis4/example_submission.tif?rlkey=kbykilvau066xuogoosbf4cq8&st=8junzdyw&dl=0
https://www.dropbox.com/scl/fi/t7fyt03qdh9egyme0itwo/existing_faults.tif?rlkey=yiao96uluqdkipf0h5vju71jf&st=rnino7ya&dl=0
https://www.dropbox.com/scl/fi/3vz9o0wwavi26xaeoxlwr/gems-geodawn-numerical-features.tif?rlkey=je8d8fepqfbst9lnwsq9rkplu&st=zj1lag1r&dl=0
https://www.dropbox.com/scl/fi/ig0mban712ns1atphgphe/Digital-elevation-model-links-JSON.pdf?rlkey=zm77f1vbtt2if8hlruymptnu3&st=srhhir10&dl=0

Site creation: Create a github page for this repo that has clean ui, user friendly, simple and easy to use.  It should be organized and clean.  It should include all relevant information in an easy to read format with official verified links as sources for review.  Work line by line verify everything no hallucinations.

**The single remaining blocker to training is data placement**: run `bash scripts/download_competition_data.sh` on any unrestricted machine into `data/`, then `python scripts/prepare_data.py` — after that the full train→inference→validate pipeline is ready to run (GPU needed for training; metric/losses/validation all verified working here on CPU). — you need to complete the above task by yourself.

Run this task through multiple passes. Pass 1: Implement the task completely and verify the result. Pass 2: Review your work for bugs, missing requirements, incorrect assumptions, and edge cases. Fix everything you find. Pass 3: Re-check the entire implementation against the original request. Improve accuracy, reliability, completeness, and code quality. Fix any remaining issues. Do not stop after the first pass. Each pass must build on the previous one. Before finishing, verify that the final result fully satisfies the original request.

Go ahead and create a pull request and then merge the pull request onto the main. Make suggestions for what work still needs to be done and any limitations that is in the way of a successful project.  It should be worked on in this next session or the next session.  Work line by line verify everything no hallucinations.

</details>

---

## DS48 fusion sub-site (PR #6; research-only, not slot-cleared)

The self-contained DS48 sub-site is retained at `docs/ds48-fusion/`; it does **not** replace the
current project landing page.

- **DS-ranked emission (audit only):** `docs/downloads/gemsdoe48-ds48-emission.tif` — 37,654 px,
  all-finite float32 `[0,1]`, EPSG:32611, 3730 × 3292. Its recorded owner-derived SGMC
  off-catalogue DTI is 0.09068 vs 0.09613 for the dotted baseline (about 5.7% lower).
- **Diagnostics:** `-belief.tif` (`Bel(F)`, `[0.0000, 0.8400]`), `-mtheta.tif` (unassigned mass,
  `[0.1600, 0.2500]`), `-conflict.tif` (Shafer's `K`, `[0.0000, 0.3600]`).
- **Artifact label:** `GEMSDOE48-DS48-FUSION` is retained from that experiment; it is not a
  submission recommendation. The finite-zero outside convention does not meet official
  null/NaN-outside wording, and portal acceptance is untested.
- **Decision:** no organizer score exists; the catalogue-based proxy is anti-monotone with the
  four known live anchors. Do not upload or spend a weekly slot on this unvalidated/losing artifact.

The page's 0.2778 analysis, Dempster–Shafer diagnostics, and historical H48-A–E proposal list are
preserved as research. Its H48-A 200–300 m interpretation is not the current hypothesis ranking;
use [`docs/md/hypotheses.md`](../md/hypotheses.md). The dotted and tip masks overlap
substantially (31,614 of b2's 37,654 positive pixels), so the Dempster independence/distinctness
assumption is unsupported and its layers are diagnostics, not calibrated probabilities. It also
does not re-rank union support (Spearman ρ≈1).

**Current tests:** `./.venv/bin/python -m unittest discover -s tests -t tests` — 120 tests passed
on the merged worktree. The suite reads local raster inputs; it does not require network access.

**Correction.** `DS48-IR-07` in the subsite records the hexagonal covering arm as unvalidated and
not slot-cleared; its +1.9% SGMC-side signal was within re-sampling noise.
