# GEMSDOE48 — DOE GEMS fault-discovery research

> **Start every session by reading this file in full.**
> **Maximize P(Win):** choose measured, auditable experiments over hopeful leaderboard probes or wasted submission slots.
> **Own the Outcome:** correct bad results, retain retractions, expose uncertainty, and carry work end-to-end.

## Current decision — read first

**The candidate TIFF has no exact match in the bounded historical owner-artifact scan, but it is *not cleared for a DrivenData submission slot*.** The corrected, organizer-faithful DTI proxy evaluator shows that the requested dotted+tip Yager fusion scores below its baselines in all four spatial quadrants. Do not submit it on the basis of its format or uniqueness.

- **Inspection/download:** [primary candidate `.tif`](docs/downloads/gemsdoe48-h48-ds-yager-conflict-20261006.tif)
- Single-file ZIP: [candidate `.zip`](docs/downloads/gemsdoe48-h48-ds-yager-conflict-20261006.zip)
- Diagnostic only—**do not submit**: [unassigned-belief raster](docs/downloads/gemsdoe48-h48-ds-yager-conflict-20261006-unassigned-diagnostic.tif)
- Executive summary and one-click download: [`docs/index.html`](docs/index.html)
- **Status:** research candidate; proxy gate failed; no DrivenData upload and no private score observed.
- Suggested name: `GEMSDOE48-H48-DS-CONFLICT`
- Suggested research note: `H48 dotted+tip Yager fusion; distinct in bounded scan; SGMC proxy gate failed; do not spend slot`
- Primary TIFF SHA-256: `fe68ae6f57be013e26d20006551b43cd84bb5fe4a0b07d1d10ce4725c90fd16c`

### Corrected proxy decision

| Raster | Overall proxy DTI | Relative to fusion |
|---|---:|---:|
| Tip parent | **0.09709** | +0.01302 |
| Dotted parent | 0.09613 | +0.01206 |
| Naïve mean | 0.09030 | +0.00623 |
| Yager fusion | **0.08407** | — |

The fusion loses to the best baseline in **0/4** quadrants and fails the gate. These are fixed-prediction spatial contributions against an owner-derived SGMC proxy—not private expert truth, a model-training cross-validation estimate, or a DrivenData score. The v1 result that appeared to pass is explicitly retracted: v1 omitted prediction confidence from TP and cropped each quadrant before distance calculations. See [`proxy-validation-v1-retracted.json`](docs/data/proxy-validation-v1-retracted.json) and the corrected [`v2 receipt`](docs/data/proxy-validation.json).

## What the requested model does

The requested operation combines the two owner-reported strong families: the dotted-spacing parent (37,654 positive cells; owner reports up to 0.2778) and tip/step-over parent (41,865 positive cells; owner reports around 0.26–0.27). They share 31,614 positive cells and have 16,291 exclusive detections. Reliability-discounted binary mass assignments are combined conjunctively; Yager’s modified Dempster rule transfers conflict K to unassigned mass Θ. The diagnostic stores that mass separately. The primary raster is min–max normalized and is not the naïve mean.

**Important scientific caveats:** classical normalized Dempster combination removes conflict by dividing by `1−K`; Yager’s rule is used because it transfers conflict to Θ. More importantly, the current conversion `m(N)=r(1−x)` treats every zero in a sparse detector as affirmative evidence of no fault. A zero could instead mean that a detector was silent/uncertain. That modeling assumption is not justified by calibration and likely contributes to the corrected proxy loss. Do not promote the current evidence assignment.

The candidate differs numerically from the parent mean: within the valid footprint Pearson r=0.96359, 16,291 cells differ, maximum absolute difference=0.41371, and exact equality is false. The high correlation is expected because the parents overlap; **correlation alone is not a non-average proof**. Exact pixel checks and the historical artifact scan are in the build/uniqueness receipts.

## Unique-artifact check and format irregularity

- A visible-artifact inventory from the owner’s GEMSDOE47 repository listed 336 unique raster blobs. We fetched them and verified Git blob SHA-1; **334** matched this exact grid, while two had different grids. This raster has no exact pixel-value match and no exact positive-support-mask match among those 334. Maximum positive-support Jaccard is 0.87392 against the tip parent, which is expected for a fusion built from that parent. This is a bounded check of visible owner repositories, **not global uniqueness proof**.
- The TIFF is one-band float32, EPSG:32611, 100 m, 3730×3292, all cells finite in [0,1], with no nodata tag. It stores zero outside the study footprint to avoid a reported range-check failure.
- **Published-format conflict:** the official problem page says null/NaN outside bounds. The all-finite primary does not meet that literal outside-mask rule. NaN can also fail a naïve all-pixels `[0,1]` check. Portal acceptance was not tested. The mismatch is explicit in the byte audit—do not describe the TIFF as fully official-format compliant.

## Why the owner-reported 0.2778 may be high

The official metric is a distance-weighted Tversky index with `α=0.2`, `β=0.8` and a 300 m triangular kernel. False negatives carry four times the coefficient of false positives. Sparsifying predictions can reduce off-target mass while preserving near-trace credit, but removing real hidden faults increases FN. The reported 0.2778 is therefore consistent with an efficient coverage/false-mass tradeoff; it does **not** prove that the raster is geologically complete or that thinning caused the score. Public leaderboard rows do not publish TIFF hashes, so the owner’s precise artifact-to-score association remains unverified.

The official leaderboard snapshot observed 2026-10-06 had #1 at **0.3774**; **0.3195 was rank 7**, not the leader. Standings change. The snapshot and configured—but not yet enabled or live-verified—six-hour feed are in [`docs/data/leaderboard.json`](docs/data/leaderboard.json). A six-hour GitHub Actions refresh/deploy workflow is configured, but repository Pages settings have **not** been switched to Actions. The initial fetch against the live raw HTML has also not succeeded in this sandbox. Until Pages deployment is enabled and the parser passes a live fetch, the site shows the manually recorded snapshot—not an automatically refreshed leaderboard.

## Prospective research queue — none is slot-cleared

The starting checkout already contained H48 hypotheses, but they were not a verifiable pre-registration. Review found that cross-scale TMI persistence had already been tested as GEMSDOE47 H47-B and was reported to lose to a random control, so it is not described as new. The current fusion itself failed the corrected proxy gate.

1. **H48-A, highest qualitative upside:** co-located, strike-coherent horizontal-gradient maxima from isostatic gravity and RTP/TMI magnetics, with detrended-slope/survey-seam nuisance controls. This differs from TMI-only scale persistence. Sources are listed in official competition features, the official USGS GeoDAWN TIF archive, and USGS Nevada gravity Data Series 42. The competition stack is login-gated; official public source pages were checked, but this sandbox could not download .gov binaries. **Not validated.**
2. **H48-B:** 3-D ComCat hypocenter planes with focal-mechanism coherence. Official FDSN count queries returned 16,919 M≥2 events and 5,292 focal-mechanism products in the approximate study bbox since 2000; payload and detector not locally validated.
3. **H48-C:** channel offsets/bends and knickpoints extracted from 1 m 3DEP DEMs, not another scarp/ridge detector. USGS 3DEP is free; exact block-level 1 m coverage has not been inventoried.
4. **H48-D:** signed K/eTh or K/eU opposite-flank radiometric asymmetry with survey normalization. Distinct from prior scarp–radiometric concordance, but source bytes and test performance are not available here.

Expected gains are qualitative only; no defensible numeric ΔDTI is claimed. The exact layers, physical signatures, confounds, cost, official availability status, and novelty caveats are recorded in [`docs/hypotheses.html`](docs/hypotheses.html) and [`docs/data/source-checks.json`](docs/data/source-checks.json). **Do not spend a weekly slot on an idea until it beats the corrected spatial holdout best.**

## Project charter — persist and follow

The goal is to maximize performance in DrivenData competition 306, the DOE Geologic Enhanced Mapping System Prize, while producing useful, auditable geothermal fault-discovery research. Each session must:

1. Start with this README; preserve **Maximize P(Win)** and **Own the Outcome** as operational values.
2. Research the competition, fault geology, geothermal structural controls, and model limits using primary official sources. Keep direct manual-review links and dated evidence; distinguish official facts, owner claims, inferences, and hypotheses.
3. Organize data, provenance, licenses, checksums, geotransforms, processing, spatial holdouts, and negative results. Unlabeled pixels are not automatically confirmed negatives.
4. Before new geology code, list 3–5 distinct hypotheses, exact layers/transforms, target mechanism, non-fault mimics, reason it might reveal uncatalogued faults, difference from prior work, expected relative DTI improvement, implementation cost, and free official data source. Check the source is actually available. Do not invent numeric forecasts.
5. Validate candidates on spatial blocks with the organizer’s exact DTI and exact known-fault masking. Keep source-derived proxy results separate from private expert truth and leaderboard score. No candidate uses a slot before it beats the corrected holdout best.
6. Generate a genuinely distinct, correctly named, single-band float32 GeoTIFF only when appropriate; hash, reopen, verify values and grid, and show an obvious download and paste-ready name/note near the site entrance. Publish the unassigned-belief diagnostic separately and label it “do not submit.”
7. Maintain a current official leaderboard feed via scheduled fetch, but never infer score-to-file attribution.
8. Run three passes: (1) implement and test, (2) inspect bugs/assumptions/edge cases, (3) re-check the full request and improve. Preserve corrections and retractions.

Core sources: [official problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [about/resources](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/), [data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login may be required), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [rules entry](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/), [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [DOE/NLR competition report](https://docs.nlr.gov/docs/fy26osti/96647.pdf), and [GDR submission 1391](https://gdr.openei.org/submissions/1391). [Owner-reported H47-B TMI-persistence validation](https://github.com/buffedlizard55-lab/GEMSDOE47/blob/main/docs/validation-h47b-20261006.md) is experiment history, not independent scientific evidence. See the source register and uniqueness audit.

## Reproduce and test

```bash
python -m venv .venv
.venv/bin/pip install -e . pytest
bash scripts/fetch_inputs.sh
.venv/bin/python scripts/build_submission.py
.venv/bin/python scripts/validate_proxy.py
.venv/bin/pytest -q
```

Raw inputs are ignored by Git and restored from pinned public owner mirrors via authenticated `gh`; their hashes identify bytes, not scientific validity. Run the leaderboard parser fixtures offline with `pytest`. The scheduled workflow attempts the network fetch from GitHub-hosted runners, but local live-fetch verification failed on TLS and Pages deployment is not enabled.

## Limitations and access needed

1. No DrivenData session is available: cannot submit, retrieve private scores, confirm portal acceptance, or download the login-gated competition feature stack.
2. Official USGS pages and ComCat count endpoints were checked, but direct .gov binary transfer from this sandbox failed TLS. No GeoDAWN or gravity binary was ingested here.
3. SGMC proxy labels are owner-derived/public compilation data, not the hidden expert test labels.
4. The two parent surfaces are correlated and D-S source independence is not demonstrated; zero-to-not-fault conversion is not calibrated.
5. The all-finite zero-outside TIFF avoids a range error but diverges from the written null/NaN outside rule; the portal has not been tested.
6. The six-hour leaderboard workflow is best-effort. GitHub Pages must use Actions as its deployment source; if the feed stalls, check the workflow and the official page layout.

See [`docs/method.html`](docs/method.html), [`docs/sources.html`](docs/sources.html), [`docs/data/proxy-validation.json`](docs/data/proxy-validation.json), [`docs/data/uniqueness-audit.json`](docs/data/uniqueness-audit.json), and the build audit for the full receipts.
