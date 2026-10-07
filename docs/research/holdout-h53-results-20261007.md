# H53 three-source adaptive DS — blocked results 2026-10-07 (gate FAILED, no slot)

> **Parent-classification erratum:** the frozen H53-1 lidar candidate uses H36-1 rung30, which is an H19-5/rung-30 repacking, not the actual tip/step-over family. Its scores and source bytes are unchanged, but it must be described as B2 × H36-1 rung30 × lidar—not as B2 × the tip family. H33-D is the explicit tip/step-over parent and is used by the separate H53-RadEdge experiment. See [`evidence/h36_parent_classification_erratum_20261007.json`](../../evidence/h36_parent_classification_erratum_20261007.json) and the [H53 namespace erratum](../../evidence/h53_radedge_namespace_erratum_20261007.json).

**Decision: no weekly submission slot is cleared.** Neither the graded primary
nor the pignistic binary twin beats H49 (0.100751) on the SGMC-newer proxy
mean or on any single fold; the raw-SGMC sensitivity agrees in direction.
Both files are published as unique, honestly-labelled research candidates
with full receipts. No organizer score exists for any file in this
repository.

## 0. The brief's two questions, answered at the level of the evidence

**Why did 0.2778 win the family ladder?** Metric bookkeeping, not geology.
A(44,090 dots, 0.2600) → B(40,199, 0.2708) → C(37,654, 0.2778) is two rounds
of deleting dots within 200 m of the public catalogue, which the organizer
masks from scoring — both steps independently imply the removed dots carried
≈ zero credit (T/π = 5,073 vs 5,470, 7.5 % apart). C recovers ≈ 37 % of the
≈ 14,300 hidden kernel mass; each added dot must carry ≥ 0.056 expected
weight (0.2·DTI) to pay for itself. Full derivation:
`docs/research/why-02778-and-ceiling-20261007.md`,
`evidence/live_ladder_20261007.json`.

**Can we beat 0.2778 live?** Plausibly, but only with new information about
where hidden faults are — not with a new combination of the same two
surfaces. H53 tests exactly the most generous version of "combination":
adding a third, new-sensor (lidar) source with terrain-adaptive reliability.
It narrows the fusion deficit on the proxy (below) but still loses to both
parents, both unions, and H49. The session's consolidated finding stands and
is now stronger: **no fusion of existing surfaces — two-source or
three-source, scalar or adaptive discount — has beaten the better parent on
the blocked proxies. Raising the live score requires higher credit density
(new signal: H53-2's v2 scarp detector), not better combination.**

## 1. Candidates scored (identical folds/domain/metric as all prior runs)

| File | Construction | Support / mass |
|---|---|---|
| `GEMSDOE48-H53-3SRC-DS-20261007-9242c831-nan-outside.tif` (primary, graded) | Bel_ABC(F)/max, (B2 ⊕ H36-1) ⊕ lidar | 1,488,778 positives, mass 260,260 |
| `…-pignistic-twin-nan.tif` (binary twin) | BetP top-37,654 (parent-A budget) | 37,654 positives |
| `…-zeros-outside.tif` (encoding twin) | same graded values, zeros outside | not scored (identical in-footprint values) |

Build: `scripts/build_submission_h53.py` → `evidence/build_h53_receipt_20261007.json`
(deterministic: rebuilt byte-identical, SHA `9242c831…`). Format audits pass
for both scored files (`evidence/h53_submission_validation_20261007.json`,
`evidence/h53_twin_validation_20261007.json`).

## 2. SGMC-newer >300 m off-catalogue proxy (primary gate)

`evidence/holdout_h53_spatial_comparison_20261007.json` (graded),
`evidence/holdout_h53twin_spatial_comparison_20261007.json` (twin).
H49 folds from `evidence/holdout_h49_spatial_comparison_20261006.json`
(same protocol, same pinned truth).

| Candidate | NW | NE | SW | SE | Mean |
|---|---:|---:|---:|---:|---:|
| dotted C (parent A) | 0.1018 | 0.0991 | 0.1075 | 0.0736 | 0.095491 |
| tip H33-D (script comparator) | 0.1014 | 0.1002 | 0.1065 | 0.0739 | 0.095491 |
| prior union B2∪H33-D | 0.1025 | 0.1027 | 0.1065 | 0.0763 | 0.096992 |
| H49 (blocked best) | 0.1061 | 0.1079 | 0.1104 | 0.0786 | **0.100751** |
| **H53 graded primary** | 0.0745 | 0.0905 | 0.0499 | 0.0708 | 0.071408 |
| **H53 pignistic twin** | 0.0954 | 0.0955 | 0.0984 | 0.0689 | 0.089559 |

Paired deltas (mean, positive folds): primary vs H49 −0.029343 (0/4); twin
vs H49 −0.011192 (0/4); primary vs prior union −0.025583 (0/4); twin vs
prior union −0.007433 (0/4). **Gate fails on both criteria for both files.**

## 3. Raw-SGMC sensitivity (same direction, do not pool)

| Candidate | Newer mean | Raw mean |
|---|---:|---:|
| H53 graded primary | 0.071408 | 0.070510 |
| H53 pignistic twin | 0.089559 | 0.088542 |
| H49 | 0.100751 | 0.099768 |
| prior union | 0.096992 | 0.095957 |

Receipts: `evidence/holdout_h53_raw_sgmc_sensitivity_20261007.json`,
`evidence/holdout_h53twin_raw_sgmc_sensitivity_20261007.json`.

## 4. Catalogue proxy (diagnostic only; known leaky for C-derived surfaces)

Graded primary 0.030236, binary twin 0.007525 (twin shares 33,385/37,654
cells with C, Jaccard 0.796 — it inherits C's catalogue-blind construction).
H49 0.095353, prior union 0.085538. No gate uses this proxy.

## 5. Cross-run fusion comparison (protocol-identical absolute means)

`scripts/holdout_h51.py` asserts the same pinned SGMC truth (62,122
positives), quadrants, halo, and metric as `run_spatial_holdout.py`, so
absolute mean DTIs are comparable across runs:

| Fusion decision surface (37,654 px unless noted) | SGMC-newer mean |
|---|---:|
| H53 pignistic twin (3-source: B2 × H36 × lidar) | **0.089559** |
| H50 binary Bel-top-37,654 (2-source: B2 × H36) | 0.087161 |
| H51 binary Pl-top-37,654 (2-source: B2 × H36) | 0.086537 |
| H50 graded belief (2-source, diffuse) | 0.071553 |
| H53 graded belief (3-source, diffuse) | 0.071408 |
| H36-1 rung30 parent, not tip/step-over (37,660 px) | 0.093315 |
| dotted C parent (37,654 px) | 0.095491 |
| H49 (47,905 px) | 0.100751 |

Reading: the lidar third source makes the H53 twin the best *fusion-decision*
surface on this proxy (+0.0024 over the best 2-source twin), but it still
loses to both parents (−0.0038 vs H36, −0.0059 vs C) and to H49 (−0.0112).
For diffuse graded belief the third source is neutral (0.0714 vs 0.0716).
New-sensor information helps the decision surface a little; it does not
rescue fusion as a strategy.

## 6. Disagreement diagnostics (what the geologist sees)

In-footprint ranges from the build receipt: m_ABC(Θ) [0.00092, 0.030] —
strictly positive everywhere (the RHO_MAX ceiling + per-pixel lidar discount
keep the unassigned layer informative); K_AB max 0.88 (family-vs-family
contradiction, the brief's disagreement layer); K_ABL max 0.75 (lidar-vs-pair
contradiction); K_total max 0.93. Files:
`…-diag-unassigned-nan.tif`, `…-diag-conflict-AB-nan.tif`,
`…-diag-conflict-ABL-nan.tif`, `…-diag-plausibility-nan.tif`.

Not-an-average verification (receipt): vs the 3-belief mean, Pearson 0.860,
max |Δ| 0.469, top-37,654 Jaccard 0.550; vs the 2-family mean, Pearson 0.962,
max |Δ| 0.386, 10.5 % of cells differ by > 0.05. The combination is
genuinely not an average — it is simply not a better predictor than its
parents on these proxies.

## 7. Limitations (do not over-read)

* Public-map proxies, not private expert truth; frozen upstream surfaces not
  rebuilt per fold; C's catalogue-proximity prune makes catalogue-block
  results conditional and potentially leaky (same caveats as all prior runs).
* The SGMC proxy rewards bedrock faults by construction; lidar-friendly
  alluvium scarps are under-weighted (see H53-5's proposed alluvium proxy).
* Live-anchored discounts use owner-reported scores [OWNER-REPORT], never
  organizer file-level receipts; the lidar class discounts (0.75/0.25/0.05)
  are preregistered modelling assumptions, not calibrations.
* Determinism is verified (byte-identical rebuild); organizer portal
  acceptance is untested for every file here.
