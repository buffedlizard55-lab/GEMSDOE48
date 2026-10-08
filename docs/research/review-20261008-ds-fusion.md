# Repository review and H56 Dempster–Shafer decision — 2026-10-08

## Executive decision

**Download for inspection: yes. Upload/submit: no; do not use a weekly slot.** The requested dotted × tip/step-over Dempster–Shafer fusion already exists in this checkout as H56/H56B; rebuilding or renaming it would not create a scientifically unique submission. The current project evidence finds the H56B belief surface substantially worse than the H49 comparator on both locally available public-map proxies, and its zero-outside primary also conflicts with the repository's recorded outside-footprint format requirement. A NaN-outside counterpart exists, but does not repair the failed evidence gate or prove organizer acceptance.

- Download candidate (existing, not newly generated): [`GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif`](../downloads/GEMSDOE48-H56-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif).
- Better-format twin, still **not cleared to submit**: [`GEMSDOE48-H56B-ds-belief-dotted-x-tip-20261007-126ca59c2801-nan-outside.tif`](../downloads/GEMSDOE48-H56B-ds-belief-dotted-x-tip-20261007-126ca59c2801-nan-outside.tif).
- Independent existing audit: [`evidence/audit_h56b_artifact_20261007.json`](../../evidence/audit_h56b_artifact_20261007.json) and [`evidence/holdout_h56_belief_h49_20261007.json`](../../evidence/holdout_h56_belief_h49_20261007.json).

The existing H56B audit's correlation with its normalized kernel arithmetic-mean comparator is **0.98659985**, but the audit also measures a maximum absolute difference of 0.41724 and differences >0.05 at 12.46% of footprint cells. Therefore it is not literally the arithmetic mean, yet this high correlation means the requested “quick correlation check” does **not** establish that averaging was avoided in a meaningful rank/ordering sense. No correlation or dot-overlap result against the complete registry was established by this audit. Do not claim that lane-uniqueness gate passed.

The reported H56B public-proxy DTI means are 0.032347 (catalogue-derived proxy) and 0.070552 (SGMC off-catalogue >300 m proxy), compared with H49's 0.095353 and 0.100751 respectively. These are historical local proxy results, not organizer-confirmed scores. They used four fixed quadrants, core-plus-300 m halo, the configured alpha 0.2/beta 0.8 metric and 300 m radius; surfaces were not retrained per fold. The evidence provides fold-wise scores but no confidence interval. We do not invent one: a valid paired spatial-block bootstrap over independent withheld segments is not recorded. This task's required whole-segment hide-and-recover evaluator and per-feature leakage canary were not demonstrated by this receipt, so the historical figures must not be represented as satisfying that stricter protocol.

### Why the 0.2778 result is not evidence of a fusion win

The 0.2778 figure in the prompt is a reported leaderboard/site result for a particular dotted-family artifact. It does not establish that its particular spacing is physically causal, that its rank ordering generalizes to withheld faults, or that combining it with another surface improves the competition's private-label metric. Catalogue-derived raster outputs can score well by matching catalogue geometry or label-generation artifacts; spatially blocked hide-and-recover testing and off-catalogue checks are needed to test generalization. The available H56B paired public-proxy evidence argues against this fusion: it loses to H49 on both proxies and every fold (0/4 positive fold deltas on each), and the tip parent itself had near-zero SGMC improvement relative to H49. This is a negative result, not an estimate of leaderboard performance. The prompt's 0.3195/0.3774 leaderboard claims and the site values are user-provided observations; this repository review did not independently authenticate current leaderboard receipts.

## Candidate hypothesis slate (no experiment run)

Ranking is a qualitative research priority, **not a predicted score**. No additional candidate was executed: the branch's existing work is already well beyond the three-experiment cap stated in the session brief, and the requested fusion is already built and audited. Every candidate below requires a preregistered holdout and leakage canary before any submission decision.

| Rank | Hypothesis and layers | Physical signature / missing-catalogue rationale | Difference from this repo | Expected DTI change | Cost / external data |
|---|---|---|---|---|---|
| 1 | Cross-scale magnetic edge persistence: existing GeoDawn magnetic anomaly channels / numerical feature stack | Derivative ridges that persist over multiple smoothing scales may trace buried contacts/faults concealed in single-scale edges; retain only coherent edges displaced from mapped fault traces to target unmapped structures. | Current catalog contains radiometric-edge fusion experiments; this specifically tests persistent magnetic edge geometry over scale, rather than another family union or D-S mass reassignment. | Unknown; plausible but unproven. | Medium; cached feature stack required. No new third-party source if stack is locally present, but verify provenance/feature names before use. |
| 2 | Fault-tip transfer / relay geometry: existing mapped fault lines plus DEM-derived curvature or topographic position | Relay ramps and stepovers can localize strain and fluid pathways between mapped strands; focus on blind relay tips separated from catalogue pixels. | Unlike H33D's existing tip/stepover family, use curvature/topographic surface morphology as an independent corroborator rather than distance/arrangement alone. | Unknown; plausible but unproven. | Medium-high; DEM feature availability and leakage controls required. No added external dataset proposed. |
| 3 | Structural intersections conditioned on magnetic gradient direction: existing faults, magnetic gradients, and fault orientation | Co-located gradient discontinuities at cross-strike intersections may indicate disrupted basement permeability and unmapped structures. | Existing fusion treats sources as raster support; this tests orientation-aware intersection geometry, not pixelwise evidence pooling. | Unknown; exploratory, high confounding risk. | High; verify cached direction data or derive from existing magnetic channels. No additional external source proposed. |
| 4 | Terrain-conditioned negative control / relief invariance: existing DEM derivatives and fault labels | A candidate fault signature should persist after matching terrain classes; erosion scarps and lithologic contacts can otherwise mimic lineaments. | H52/H57 explored scarp-relief signals, but a preregistered *confound rejection* experiment tests stability across relief strata rather than using relief as positive evidence. | Not an uplift candidate by itself; may reduce false positives. | Low-medium; cached DEM required. |
| 5 | Geochemical/geothermal evidence as an independent target: official INGENIOUS chemistry / thermal measurements, only if their spatial coverage overlaps the prediction footprint | Geochemical anomalies or thermal manifestations may identify active hydrothermal systems not expressed by mapped faults. | The current H56 families are structural; this would be an independent process/domain signal rather than another structural transform. | Unknown; potentially useful but data availability/coverage not established here. | High. Specific needed sources: official INGENIOUS project data portal (https://gbcge.org/current-projects/ingenious/) and DOE Geothermal Data Repository submission 1391 (https://gdr.openei.org/submissions/1391). Their data must be checked for downloadable content, license, spatial coverage, and labels before this is viable; no authenticated live download check was made in this review. |

## Run card

```json
{
  "hypothesis": "Reliability-discounted Dempster-Shafer combination of dotted-spacing B2 and H33D tip/step-over supports; already implemented as H56/H56B, not a new candidate in this review.",
  "mechanism": "Combine masses and retain residual m(Theta) as unassigned belief; export raw conflict K separately. These quantities are not calibrated fault probabilities or direct measures of geological disagreement.",
  "named_non_fault_mimic": "Lithologic contacts and erosional scarps can create linear magnetic/topographic edges that resemble faults.",
  "holdout_DTI_CI": {
    "status": "historical_public_proxy_only; stricter whole-segment evaluator not verified; 95% CI unavailable",
    "evaluator": "local four-quadrant protocol in evidence/holdout_h56_belief_h49_20261007.json; alpha=0.2, beta=0.8, 300 m halo; not asserted to be the requested evaluator version",
    "withheld_positive_count": "not a unique segment-level count; receipts report per-fold n_truth for two proxy maps",
    "catalogue_proxy_mean_DTI": 0.0323469319,
    "SGMC_off_catalogue_gt300m_mean_DTI": 0.0705519972,
    "95_percent_CI": null
  },
  "correlation_overlap_vs_registry": "Not established against full registry. Correlation with normalized arithmetic-mean comparator is 0.9865998528; no registry dot-overlap audit is recorded. Lane gate therefore not cleared.",
  "raster_sha256": "4d6548d4ec07a47a25b83d28ebc05d58b57448c1507b460aed52cec395bdb6b (existing zero-outside H56B downloadable artifact)",
  "validator_output": "Local float32, EPSG:32611, 3292x3730, footprint values [0,1] and finite: pass. Zero-outside encoding: fails recorded NaN-outside rule. NaN-outside twin validates locally, but external/official acceptance is untested.",
  "submission_name": "GEMSDOE48-H56B-ds-belief-dotted-x-tip-20261007-9ec0d605c45b-zeros-outside.tif",
  "submission_note": "H56B DS belief: dotted B2 x H33D tip-stepover; research-only, public-proxy gate failed.",
  "verdict": "negative"
}
```

## Review limitations / next work

1. Do not upload H56/H56B: public-proxy gate failed, official null-outside conformity is not shown for the zero-outside file, and no current organizer receipt verifies acceptance.
2. Do not call an artifact “unique” from its name/hash. Run registry-wide rank-correlation and dot-overlap checks both before placement and on final dots; stop on the prompt's >0.90 / >70% tripwires.
3. Implement the specified whole-fault-segment buffered hide-and-recover evaluator, feature-by-feature leakage canaries, and segment/block bootstrap CIs; pin evaluator version, withheld segment IDs/count, masks, and output receipt. Do not re-use the current four-quadrant proxy numbers as if they met that protocol.
4. Retrieve candidate inputs only from documented, license-compatible official sources; authenticate, checksum, and record provenance. The DrivenData training data page requires account access in the existing project inventory; this review did not bypass that restriction.
5. Preserve output names and verdicts; a unique byte sequence is not evidence of novel science, improved DTI, permission to submit, or organizer acceptance.

Official/manual-review references recorded by the project: [DrivenData competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [DrivenData data page](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [GEMS reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), [USGS GeoDawn data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and-california), [INGENIOUS](https://gbcge.org/current-projects/ingenious/), and [DOE GDR submission 1391](https://gdr.openei.org/submissions/1391). This is a repository evidence review, not a fresh verification of every live webpage or data download.

---

## Addendum — H58-A / H59 reconciliation (2026-10-08)

This review's **negative H56/H56B verdict remains unchanged** for those artifacts.
The later H59 build added a distinct cover-rule artifact, strict segment-withheld
receipts and a registry audit. Its original build receipt used overly broad “OK TO
DOWNLOAD AND SUBMIT / portal-safe” wording. That wording is retained only as a historic
receipt; it does not satisfy the user's separate requirement to pass a comparable
spatially blocked promotion gate before spending a slot.

- H59's local strict evaluator reports 0.0974 [0.0927, 0.1023] on the catalogue proxy
  and 0.0917 [0.0844, 0.0990] on the SGMC off-catalogue proxy. On SGMC, its result is
  below dotted (0.0954), tip (0.0957) and their union (0.0975). The H59 receipts do not
  report the matched H49 comparison required by the current slot rule.
- H59's local raw-array [0,1] check and registry comparison are not organizer portal
  acceptance or global uniqueness. The file encodes zeros outside while the official
  problem page says outside values should be null/NaN; no portal upload was made.
- H58-A is a separate positive-only simple-support mass ablation and did run the matched
  H49 gate. It failed on both primary public proxies: paired mean deltas −0.040053
  (catalogue) and −0.034411 (newer SGMC off-catalogue), with 0/4 positive folds on both.
  It shares support/ranking with H56-OWDS and is not a new geological detector.
- The 2026-10-08 official leaderboard snapshot placed 0.2778 at #13 (extradr19), not
  the top row; no exact local B2 TIFF-to-row receipt exists. Official staff clarified
  known-fault masking is pixel-exact with no 300 m buffer, so nearby predictions are
  scored normally and cannot be assumed exempt.

**Current decision: download for inspection only; no weekly submission slot is cleared;
no submission was made.** See the [machine-readable reconciliation](../../evidence/submission_gate_reconciliation_20261008.json),
[H58-A report](h58-results-20261008.md), [H59 method/results](h59-method-results-20261008.md),
[leaderboard/mask clarification](leaderboard-and-mask-clarification-20261008.md), and
[official sources](../sources.md).
