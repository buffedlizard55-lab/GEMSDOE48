> **Historical PR archive.** This earlier page is preserved for provenance; claims may be superseded. See the [current overview](../index.html) and [current validation](../validation.html).

---

# GEMSDOE48 — conflict-preserving DOE GEMS fault discovery

> **Start every session here. Core values:** **Maximize P(Win)** by choosing measured, auditable experiments over hopeful slot spending. **Own the Outcome** end-to-end: diagnose failures, fix them, publish uncertainty, and never promote a proxy as truth.

## Immediate deliverable

**[Download the unique submission GeoTIFF](docs/downloads/gemsdoe48-h48-ds-yager-conflict-20261006.tif)**

Single-member ZIP: [download](docs/downloads/gemsdoe48-h48-ds-yager-conflict-20261006.zip)

Executive summary / GitHub Pages entry: [`docs/index.html`](docs/index.html)

- Name: `GEMSDOE48-H48-DS-CONFLICT`
- Note: `H48 conflict-preserving dotted+tip evidence fusion; Yager transfer of DS conflict to uncertainty; 4/4 SGMC proxy folds positive; all-finite [0,1]`
- SHA-256: `fe68ae6f57be013e26d20006551b43cd84bb5fe4a0b07d1d10ce4725c90fd16c`
- Single-band float32; EPSG:32611; 100 m; 3730×3292; all finite; min 0; max 1; no nodata tag
- Diagnostic (do **not** submit): [unassigned belief](docs/downloads/gemsdoe48-h48-ds-yager-conflict-20261006-unassigned-diagnostic.tif)

## Answer to the research question

The dotted H33-2-B2 family’s reported 0.2778 is plausibly explained by **credit-density optimization under the official distance-weighted Tversky index**, not by better probability calibration. At α=0.2, β=0.8 and 300 m support, thinning redundant adjacent predictions can keep most distance-weighted true-positive coverage while reducing false-positive prediction mass. Its flank pruning and spacing reduce mass near the public catalogue and preserve a sparse 37,654-cell geometry. That explanation follows from the official metric and the observed family progression; hidden expert labels prevent causal proof, and the public leaderboard does not identify a TIFF hash.

A score above 0.2778 is possible but cannot be promised. This conflict-preserving fusion beat the dotted parent on the frozen four-block SGMC off-catalogue proxy (mean 0.10562 vs 0.09670; Δ +0.00893; 4/4 blocks) and beat a naïve mean (0.10258). Those are **proxy DTIs, not competition scores**. The official leaderboard observed 2026-10-06 was led by **0.3774**, making the brief’s 0.3195 target stale.

## Standing project prompt (normalized, persistent)

The project exists to place as high as possible in DrivenData competition 306, the DOE Geologic Enhanced Mapping System Prize. It must autonomously research geothermal-indicative, previously unmapped faults; organize official, auditable sources; build and spatially validate distinct strategies; generate a legal, unique, easy-to-download single-band GeoTIFF; and explain submission steps at the beginning of the site. Never copy a prior submission as the new deliverable. Prior artifacts may be inputs for learning and evidence fusion only.

Highest-urgency requested experiment: combine the strongest spacing-tuned dotted family (reported up to 0.2778) and tip/step-over family (reported around 0.26–0.27) without averaging disagreement away. Use Dempster–Shafer-style evidence assignments, normalize combined fault belief to [0,1], publish uncertain/unassigned belief as a diagnostic, and numerically prove the primary is not the naïve mean. **Scientific correction retained in this repository:** classical normalized Dempster combination removes conflict through division by `1-K`; Yager’s modified Dempster rule transfers conflict to Θ and is therefore the rule that actually satisfies the requested disagreement-preservation behavior.

Before a weekly slot, specify 3–5 untried geological hypotheses. Each must name exact layers, physical transform/signature, why it may reveal a fault absent from USGS/INGENIOUS, how it differs from this repository, expected DTI improvement, cost, official free source, and availability. Rank them, then spatially validate the top candidate. Do not spend a slot on a candidate that fails the frozen gate. Proxy validation must be labeled as such; private truth and organizer score must never be implied.

Every delivered TIFF must match the competition CRS, shape, geotransform and float32 range. The owner encountered `Predicted values must be in range [0, 1]`; therefore re-open written bytes and verify every cell is finite and within range, while flagging the tension with official language requesting null/NaN outside bounds. Give each file a unique name and a paste-ready short note. Create an executive-summary page with one-click TIF and ZIP links.

Research must use official, verified, preferably primary sources with direct manual-review links. External data must be free, legally usable under competition rules, and shareable with the sponsor. Flag inaccessible, mirrored, owner-reported, stale, contradictory, or unauthenticated evidence. Never invent a score, source, causal explanation, data provenance, portal acceptance, or validation result. Review implementation in three passes: complete and test; inspect bugs/assumptions/edges and fix; re-check every original requirement and improve.

Competition references that must remain in scope:

- [Official overview, task, data, metric, and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official about/resources](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [Official data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) (login may be required)
- [Official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official rules entry](https://www.drivendata.org/competitions/306/competition-doe-gems/rules/)
- [DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [DOE/NLR PDF supplied in the brief](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [DOE GDR submission 1391](https://gdr.openei.org/submissions/1391)
- Owner-supplied Dropbox links for `example_submission.tif`, `existing_faults.tif`, `gems-geodawn-numerical-features.tif`, DEM link PDF, and competition PDF (treat as owner-supplied until authenticated)
- The historical owner sites GEMSDOE, GEMSDOE2–47 and numbered 5–20 variants supplied in the brief, especially [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) and [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/). Their reported scores are experimental history, not independent evidence.

The prior-session blocker (“place competition data, run download and prepare scripts; GPU required for full model training”) is no longer a blocker for this evidence-fusion build: its exact sparse parents and template are publicly restorable and CPU inference is sufficient. Full raw-feature model development still requires the ~419 MB feature stack; neural training benefits from GPU access.

## Method and validation

See:

- [`docs/hypotheses.html`](docs/hypotheses.html) — five ranked geological hypotheses and availability checks
- [`docs/method.html`](docs/method.html) — equations, three-pass review, limits, next actions
- [`docs/sources.html`](docs/sources.html) — source/evidence-class register
- [`docs/data/proxy-validation.json`](docs/data/proxy-validation.json) — all four blocked folds
- [`docs/downloads/*-audit.json`](docs/downloads/gemsdoe48-h48-ds-yager-conflict-20261006-audit.json) — independent byte re-read

## Reproduce exactly

```bash
python -m venv .venv
.venv/bin/pip install -e . pytest
bash scripts/fetch_inputs.sh
.venv/bin/python scripts/build_submission.py
.venv/bin/python scripts/validate_proxy.py
.venv/bin/pytest -q
```

Input and output SHA-256 hashes are fail-closed. Raw inputs are ignored by Git; the final small deliverables and receipts are versioned.

## Limitations / access needed for the next phase

1. No user DrivenData session is available here; the agent cannot spend a slot or retrieve a private score. Portal acceptance remains unverified.
2. Source score-to-byte attribution is owner-reported, not organizer-authenticated.
3. SGMC proxy truth is not the experts’ hidden test set and may share compilation bias.
4. The two parent families overlap and may share upstream features, weakening the strict independence assumption of evidence combination.
5. H48-A (cross-scale gravity/magnetic maxspot persistence) is the best next detector. It needs the official numerical feature stack and fold-specific construction; do not submit it before it beats this frozen fusion and anchor under preregistered spatial blocks.
