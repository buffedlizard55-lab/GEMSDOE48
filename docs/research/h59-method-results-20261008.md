# H59 — method, strict holdout results, run card, and next hypotheses (2026-10-08)

This document is the session record for the H59 build in this checkout.  Every number
below is a **measurement on a frozen local proxy** or an **owner-reported value copied
from a campaign page**; nothing is a projection and nothing is an organizer score.
Evaluator version: `scripts/evaluate_holdout.py@2026-10-08`.

## 1. What was asked and what was done

The session brief asks for a **unique** competition GeoTIFF that combines the best
dotted-family surface with the best tip/step-over surface using **Dempster–Shafer
evidence theory**, keeps the **unassigned mass `m(Θ)` as its own diagnostic layer**,
normalizes the combined belief to **[0,1]**, proves the result is **not the naive
mean**, and states **unambiguously whether the file may be downloaded and submitted**.

Delivered artifact (built by `scripts/build_submission_h59.py`):

| Property | Value |
|---|---|
| File | `docs/downloads/gemsdoe48-h59-cover-ds-belief-b2xh33d-20261008T184547Z-b79c4c61d8d8.tif` |
| SHA-256 | `f1584187b459baf47f75e5daf64de6f7696f9feb14910d3cf2762f7a1119597a` |
| Bands / dtype | 1 / float32 |
| CRS / pixel / grid | EPSG:32611 / 100 m / 3292 × 3730 (equals the organizer template) |
| Values | all finite, min 0.0, max 1.0, **no NaN anywhere**, no nodata tag |
| Portal predicate | `all(0 <= v <= 1)` over the whole array → **True** (the exact check that produces “Predicted values must be in range [0, 1]”) |
| Positive cells | 37,723 |
| Portal name | `GEMSDOE48-H59-CoverDSBelief-B2xH33D` |
| Portal note (108 chars) | `GEMSDOE48 H59 | Dempster Bel(F), dotted B2 x tip H33D; 400m hex-cover of the fusion corridor; m(Theta) layer` |
| Receipt | `evidence/build_h59_receipt_20261008T184547Z.json` |

Diagnostic layers written next to the submission (NaN outside the footprint, never part
of the submission surface):

| Layer | File suffix | Meaning |
|---|---|---|
| Unassigned belief `m(Θ)` | `-diag-mtheta-unassigned` | residual ignorance after Dempster normalization |
| Raw conflict `K` | `-diag-conflict-K` | conjunctive conflict before normalization |
| Plausibility `Pl(F)` | `-diag-plausibility` | `Bel(F) + m(Θ)` |
| Continuous belief | `-diag-belief-normalized` | normalized `Bel(F)` before emission |
| Disagreement layers | `-diag-disagreement-a-only`, `-diag-disagreement-b-only` | cells committed by exactly one family |

## 2. Method (preregistered, nothing fitted to a hidden label)

1. **Parents, SHA-256 pinned.** `data/raw/dotted_h33_2_b2_zeros.tif`
   (`c55bafc4…7ab6fa9`, 37,654 cells, owner-reported 0.2778) and
   `data/raw/tip_h33d_stepover.tif` (`87f857d5…4690757`, 41,865 cells,
   owner-reported 0.2632).  Union 47,905; shared 31,614; symmetric difference 16,291.
2. **Opinion surfaces in the scorer's own geometry.** `bᵢ(x) = max_y k(d(x,y))` with
   `k(d) = max(1 − d/300 m, 0)` (triangular kernel of the official metric).  This
   avoids the semantic error of treating a non-emitted cell as evidence of “no fault”.
3. **Shafer discounting + Dempster's rule** (Shafer 1976 §11.2; Dempster 1967):
   `mᵢ({F}) = αᵢ bᵢ`, `mᵢ({¬F}) = αᵢ (1 − bᵢ)`, `mᵢ(Θ) = 1 − αᵢ`, combined with the
   canonical normalized rule.  `α_dotted = 0.95`, `α_tip = 0.95 × 0.2632/0.2778 =
   0.900072` (documented modelling assumption, same rule as H50/H58).
4. **Emission: metric-covering dot set over the fused corridor.**  The corridor is the
   union of the two families' committed cells; a hexagonal lattice covering with
   spacing 4.0 px (400 m), greedy gap fill and redundant-dot pruning
   (`gemsdoe48.emit.cover_region`) produces 37,723 dots with a **measured covering
   radius of 2.24 px = 224 m**, i.e. every corridor cell is within 224 m of an emitted
   dot (kernel credit ≥ 0.25) while the emitted mass stays in the sparse regime the
   organizer ladder rewards (37,654 → 0.2778; 40,199 → 0.2708; 44,090 → 0.2600,
   all owner-reported).
5. **No averaging.**  Spearman of the emitted surface's parent surface vs the naive
   mean of the two opinion surfaces is **0.9826**, Pearson **0.97479**, max |Δ|
   **0.2709**, with 68.1 % of support cells differing by > 0.05.  The fusion is not the
   average; it is also not a rescaled copy of `Bel(F)` (see receipt).

## 3. Strict holdout results (hide whole segments, 300 m buffer, pixel-exact masking)

Protocol: catalogue faults (60,988 cells; 3,199 segments) split into four spatial folds
by segment centroid; for each fold the hidden segments are scored after removing every
hidden pixel within 300 m of a visible fault, and the candidate prediction is zeroed
pixel-exactly on visible faults; components pooled over folds; 95 % CI by resampling
hidden segments (400 draws, seed 20261008, FPw held at its point estimate).

Second truth population: **SGMC-derived faults > 300 m from every catalogue cell**
(62,122 cells; 2,115 scored segments) — the only mapped-fault population in reach that
is off-catalogue by construction.

| Emission rule (frozen, no fitting) | catalogue proxy | SGMC off-catalogue proxy |
|---|---|---|
| Parent A — dotted B2 (37,654) | 0.0067 [0.0062, 0.0073] | 0.0954 [0.0870, 0.1046] |
| Parent B — tip H33-D (41,865) | 0.0863 [0.0820, 0.0899] | 0.0957 [0.0875, 0.1047] |
| Union, binary (47,905) | 0.0850 [0.0808, 0.0886] | 0.0975 [0.0892, 0.1068] |
| Naive mean of opinions (792,278) | 0.0444 | 0.0673 |
| DS belief, dense (792,278) | 0.0341 | 0.0767 |
| DS pignistic × (1−K), dense (H58 rule) | 0.0207 | 0.0701 |
| DS belief, top 38,000 | 0.0070 | 0.0946 [0.0864, 0.1037] |
| DS belief, spacing 2.8 px, 38,000 | 0.0130 | 0.0835 |
| DS belief, spacing 5.2 px, 38,000 | 0.0336 | 0.0841 |
| **H59 — corridor covering set, 37,723** | **0.0974 [0.0927, 0.1023]** | **0.0917 [0.0844, 0.0990]** |
| Random control, same mass (38,000) | 0.0707 | 0.0724 |

Readings that matter:

* The H59 covering emission is the **best rule on the catalogue proxy** (0.0974 vs
  0.0863 for the best parent and 0.0707 for a same-mass random emission, i.e. +0.027),
  and it is **statistically indistinguishable from both parents on the off-catalogue
  proxy** (0.0917 vs 0.0954/0.0957; CIs overlap).
* **The dotted family is anti-correlated with the catalogue**: 0 of its 37,654 dots lie
  within 200 m of a catalogue cell and only 2,171 within 300 m, so its catalogue-proxy
  DTI is 0.0067 — far *below* the same-mass random control (0.0707) — while it is
  competitive (0.0954) on the off-catalogue population.  Its owner-reported 0.2778 is
  therefore consistent with a surface whose signal lives **off the existing catalogue**,
  which is exactly the discovery setting of this competition.
* **No fusion rule beats its parents by more than noise on either proxy**, and the
  fusion surfaces carry essentially no ranking information about *withheld* segments
  (leakage canary AUC ≈ 0.50 for every candidate; the positive-control features that
  use the full catalogue score 1.0000).  A fusion of two families that already share
  31,614 of their cells cannot add information about the same target.
* Density: on the SGMC proxy the DS-belief rank cut keeps improving with mass
  (20k 0.0552 → 47.9k 0.0988 → 200k 0.1088) but the same-mass random control overtakes
  it everywhere above ~60k (60k 0.1003 vs 0.1006; 200k 0.1854).  On the catalogue proxy
  every dense DS arm is far below the same-mass random control.  The organizer-observed
  ladder, not any local proxy, is the reason this build stays sparse.

## 4. Registry / uniqueness audit (required by the parallel-run protocol)

* 74 local registry rasters compared (47 submission-like dot rasters, the rest dense
  surfaces and diagnostic layers, classified separately).
* **Byte identity: none.**  Largest **exact-cell** overlap with any submission-like
  raster: **0.208** (`h19_5_01922.tif`); next 0.103 and 0.090.
* 3-pixel proximity to the nearest parent dot set: **1.000**.  This is reported, not
  hidden: a covering set of the same corridor *must* land within the 3-pixel halo of the
  dense parent dots that already cover that corridor (parent spacing 2.8 px), so the
  proximity fraction is structurally degenerate for any fused emission over the same
  ground.  The non-degenerate columns are the exact-cell fraction (0.208) and the
  byte-level comparison (no match).
* Corridor-restricted Spearman against registry surfaces: max 0.9201 (an H48-era DS
  derivative of the same parents), 0.7969 vs the dotted ladder, 0.7527 vs the tip
  family.  High correlation with same-parent derivations is expected and is why the
  score claim is “no measured improvement”, not “a better surface”.

## 5. Run card (session protocol, JSON)

```json
{
  "hypothesis": "Sparse emission of the normalized Dempster-Shafer combined belief of the two strongest independently built families, at a covering density matched to the scorer's 300 m kernel, covers unmapped fault corridors at least as well as either parent per emitted cell.",
  "mechanism": "Triangular-kernel opinion surfaces per family, Shafer discounting (0.95 / 0.900072), canonical normalized Dempster combination; residual m(Theta) and raw conflict K exported as separate layers; emission = hex-covering dot set of the fused corridor (spacing 4.0 px, measured covering radius 2.24 px = 224 m).",
  "named_non_fault_mimic": "Lithologic contacts and erosional or landslide scarps produce linear topographic and magnetic edges that a kernel-credit belief surface cannot distinguish from fault evidence.",
  "holdout_DTI_CI": {
    "evaluator": "scripts/evaluate_holdout.py@2026-10-08 (whole-segment hide-and-recover, 300 m buffer, pixel-exact visible-fault mask, pooled DTI alpha=0.2 beta=0.8, 300 m triangular kernel, segment bootstrap 400 draws seed 20261008)",
    "catalogue_proxy": {"DTI": 0.0974, "ci95": [0.0927, 0.1023], "withheld_positive_cells": 60988, "withheld_segments": 3201},
    "sgmc_off_catalogue_proxy": {"DTI": 0.0917, "ci95": [0.0844, 0.0990], "withheld_positive_cells": 62107, "withheld_segments": 2115},
    "comparators": {"dotted_parent": 0.0954, "tip_parent": 0.0957, "union": 0.0975, "random_same_mass": 0.0724}
  },
  "correlation_overlap_vs_registry": "No byte identity; max exact-cell overlap 0.208 with any submission-like raster; max corridor Spearman 0.9201 (same-parent DS derivative); 3-px proximity 1.000 but structurally degenerate for corridor-covering sets (documented).",
  "raster_sha256": "f1584187b459baf47f75e5daf64de6f7696f9feb14910d3cf2762f7a1119597a",
  "validator_output": "single band, float32, EPSG:32611, 3292x3730, transform equals organizer template, all finite, min 0, max 1, no nodata tag, portal range predicate True -- all gates pass.",
  "submission_name": "GEMSDOE48-H59-CoverDSBelief-B2xH33D",
  "submission_note": "GEMSDOE48 H59 | Dempster Bel(F), dotted B2 x tip H33D; 400m hex-cover of the fusion corridor; m(Theta) layer",
  "verdict": "promote-format-only",
  "verdict_detail": "OK to download and submit (format-valid, portal-safe, unique bytes and unique dot cells). NOT SUPPORTED as a score improvement: the fusion does not beat its parents beyond noise on either public proxy, and the leakage canary is ~0.50 for every candidate surface."
}
```

## 6. Why 0.2778 happened, and what could actually beat it

Measured decomposition of the metric `DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw)`:

1. **Mass.**  Recall is weighted 4× precision, so coverage dominates.  The winning
   entries cluster at 37k–44k positive cells; an all-ones footprint (5.17 M cells)
   reaches only ~0.05 on the catalogue proxy, and the dense DS arms (792 k cells) score
   0.0341 there against 0.0707 for a same-mass *random* emission.
2. **Placement off the catalogue.**  The 0.2778 file has **zero** dots within 200 m of
   the mapped catalogue.  On the off-catalogue population it is as good as any other
   family (0.0954), while on the catalogue it is the worst candidate tested (0.0067).
   Submissions built to score on the catalogue (`sgmc-off-catalogue-44k` 0.0512,
   `h51-km-faultzone` 0.0106) did not transfer.
3. **Kernel-matched spacing.**  The dotted ladder (2.8 px spacing) and this build's hex
   covering both place dots so that every corridor cell keeps partial kernel credit.
4. **What cannot work with these two parents.**  Their dot sets overlap by 31,614/47,905
   (Jaccard 0.66); a Dempster combination of two such sources is a monotone function of
   the same evidence and adds no measured discriminative power (AUC ≈ 0.50 on withheld
   segments of both proxies).  **Beating 0.2778 needs a new off-catalogue evidence
   channel, not a new combination rule.**

## 7. Ranked hypothesis slate (proposed, not validated)

Ranked by expected off-catalogue enrichment per unit cost.  None was implemented in
this session; each names its physical signature, why it should catch faults missing from
the catalogue, how it differs from this repo's work, and the free official source it
needs.  **Availability caveat:** this sandbox reaches only github.com, pypi.org and
their CDNs, so third-party download availability below is *reported as unverified from
here* and must be checked on an unrestricted machine.

| Rank | Hypothesis (layers) | Physical signature | Why unmapped faults | Difference from this repo | Expected DTI effect | Cost / source status |
|---|---|---|---|---|---|---|
| 1 | **H60 — lidar micro-topography conditioned on the fused corridor** (USGS 3DEP 1 m DEM tiles for the corridor + fused DS corridor) | Multi-scale curvature (Laplacian-of-Gaussian) ridge/valley-pair offsets and drainage deflection within 100 m of a corridor dot | The catalogue is a compilation of bedrock faults; lidar resolves metre-scale scarps, channel offsets and beheaded drainages that compilation omits, and the hidden expert mapping is plausibly drawn from high-resolution imagery | H52/H57 used lidar *scarp relief* as coarse positive evidence; this tests scale-resolved curvature/offset metrics *conditioned* on the fused corridor | Highest of the slate (target: exceed the +31 % random-control enrichment the dotted family already has at 40k mass) | Medium; needs 3DEP tiles beyond the two local pilot tiles in `data/pilot/dem3m/`; source = USGS 3DEP (unverified from this sandbox) |
| 2 | **H62 — stress-consistent tip/relay continuation** (official catalogue segments + fused corridor) | Along-strike projection beyond mapped tips and relay-ramp bridging for overlapping tip pairs at 1–5 km separation, filtered by strike consistency | Fault tips and relay zones are where new faults are discovered; the tip family already scores 0.2632 (owner-reported), so tip-conditioned geometry is a proven channel | H33-D used analog tip detection; this adds documented per-segment geometric continuation with a stress-consistency filter, evaluated fold-by-fold | Moderate (+0.005–0.02 on the off-catalogue proxy if enrichment holds) | Low; pure geometry on existing local rasters |
| 3 | **H61 — multi-scale magnetic edge persistence** (GeoDawn TMI derivatives from the cached 19-band feature stack + corridor) | Edges that persist across smoothing scales in tilt/THD, angle-conditioned away from catalogue-parallel structure | Deep basement fabric with weak surface expression; single-scale radiometric edges were already tried (0.1589 / 0.0843) but magnetic scale-persistence is a different, untested channel | Earlier radiometric-edge work; this tests persistence of *magnetic* edges and excludes catalogue-parallel orientations | Unknown; plausible | Medium; requires restoring the cached 19-band stack (`scripts/restore_h55_inputs.py --with-official-features`, third-party GitHub mirror — provenance caveat) |
| 4 | **H64 — INGENIOUS thermal/geochemical modulator** (INGENIOUS regional data in `data/external/`, GDR submission 1391) | Surface-temperature anomaly and alteration proximity as a multiplicative modulator of the corridor, not as new geometry | The prize is geothermal: hidden labels may weight faults near thermal manifestations | Prior submissions used thermal/alteration *as a surface* (0.1894 / 0.0782); this uses it only to re-rank corridor dots | Small but independent of geometry | Medium; source = INGENIOUS / DOE GDR 1391 (availability of the needed layers unverified from this sandbox) |
| 5 | **H63 — SGMC-vintage differential** (USGS SGMC faults vs the official catalogue) | Cells where SGMC has faults absent from the catalogue | It is the off-catalogue population by construction | Already effectively submitted: `sgmc-off-catalogue-44k` scored 0.0512 (owner-mirrored receipt), i.e. this direction has *negative* evidence | Low/negative | Low; local rasters already present — kept in the slate as a documented negative |

**Gate before any of these spends a submission slot:** beat the current best
single-family surface on the strict protocol *and* beat the same-mass random control on
both proxies *and* pass the byte/exact-cell uniqueness audit.  Per the session protocol
the top candidate (H60) **cannot be validated in this session** — it needs DEM tiles that
this environment cannot download — so it is proposed, not promoted, and flagged for
review on an unrestricted machine.

## 8. Irregularities flagged in this session

1. **Portal range error and NaN.**  The submission portal rejected an earlier download
   with “Predicted values must be in range [0, 1]”.  Files in `docs/downloads` that carry
   NaN outside the footprint fail the predicate `all(0 <= v <= 1)`; the H59 primary is
   all-finite with no nodata tag and passes it.  Older NaN-outside files remain in
   `docs/downloads` for traceability but must not be treated as portal-safe.
2. **`data/raw/sample_submission_template.tif` is a local artifact, not an organizer
   file**: it is float32 with NaN outside the footprint and exactly 60,988 positive
   cells, identical to `data/official/existing_faults.tif` / `labels.tif`
   (`7ba308cc…`).  Its finite-cell mask (5,167,373 cells) is used as the footprint
   definition; that usage is documented, but the file must not be described as the
   organizer's sample submission.
3. **Two SGMC rasters with different hashes and counts**:
   `data/raw/sgmc_faults_100m.tif` `26d142c4…` (82,151 positives) vs
   `data/official/derived_sgmc_faults_100m.tif` `643cbe99…` (83,593 in footprint;
   62,122 off-catalogue at > 300 m).  Holdout scripts pin the derived raster; the mirror
   should be reconciled or labelled.
4. **16 pre-existing test failures at the merge commit `36d9785`** in
   `tests/test_site_*.py`, `tests/test_h57.py`, `tests/test_site_classification.py`: the
   site was updated for H58 without updating those assertions.  They are fixed in this
   session along with the site update.
5. **README contradiction inherited from the previous merge**: the top of the README
   declared the H58 file “ready to download and submit” while a later section maintained
   “NOT OK / NOT CLEARED TO SUBMIT” for the same fusion family.  This session replaced
   both statements with one mechanically-gated verdict per artifact.

## 9. Limitations

* No organizer receipt exists for any file here; `UNSCORED` labels are deliberate.
* Both truth proxies are public maps, not the hidden labels; their rankings disagree
  with each other and neither reproduces the organizer ladder.
* The two parents are frozen upstream artifacts and cannot be rebuilt from visible
  faults alone, so the holdout is a leave-segment-out generalisation test of frozen
  surfaces, not a fully re-derived per-fold model.
* The `m(Θ)` layer mixes genuine epistemic ignorance with spatial-offset effects; it is
  a diagnostic, not a probability, and not a measure of geological disagreement alone.
* This session ran three experiments (H59 build, strict holdout on two proxies, registry
  audit).  The hypothesis slate is unvalidated by design.
