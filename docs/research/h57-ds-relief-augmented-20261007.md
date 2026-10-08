# H57-RELIEF — Dempster–Shafer two-family fusion gated by lidar relief

> **Namespace collision — read this first.** Three same-day records use H57 labels. This page is
> only the built relief artifact `GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07` from
> source branch `arena/567db1fc-gemsdoe48`. The upstream `h57-hypothesis-slate-20261007.md` is a
> separate, unbuilt H57-A–E slate. The current branch's `hypotheses-h57-20261007.md` is another
> H57-A–D slate; its H57-A radiometric-residual × magnetic-gradient screen failed and produced no
> TIFF. Neither H57-A refers to this relief artifact. The cited local 100 m scarp mosaic exists,
> but its historical source receipt is not independent source authentication or a coverage/license
> audit.

> **Superseding correction.** This `H57-RELIEF` artifact is distinct from both H57-A slates
> referenced in the repository. Its former **SUBMIT RECOMMENDED** banner and all live-equivalent
> projections/thresholds are invalidated. **OK TO DOWNLOAD FOR INSPECTION · NOT OK / NOT CLEARED TO
> SUBMIT.** The corrected builder does not regenerate those projections. Start with the
> [metric-identity erratum](h57-relief-metric-erratum-20261007.md); the remainder of this page is
> historical/forensic evidence, not current submission guidance.

**Session date:** 2026-10-07 (UTC) · **Source branch:** `arena/567db1fc-gemsdoe48` · **Artifact id:** `e6b785718c07` · **Current label:** H57-RELIEF

**Current verdict: OK TO DOWNLOAD FOR INSPECTION · NOT OK / NOT CLEARED TO SUBMIT. No weekly slot is cleared.** The former live projection and recommendation are withdrawn by the [metric-identity correction](h57-relief-metric-erratum-20261007.md). The remaining report is a historical forensic record, not current decision guidance.

| | value |
|---|---|
| Research artifact name | `GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07` |
| File | `docs/downloads/GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07.tif` |
| SHA-256 | `28a51fb032b8f2cfd1f04ad3bd429c29d7bb780d36961fea783ff8099130986e` |
| Positive cells | **58,031** (37,654 parent + 20,377 new) |
| Format | single band float32, EPSG:32611, 100 m, 3,730 × 3,292, **all 12,279,160 cells finite, all inside [0, 1]** |
| Uniqueness | **UNIQUE** against 99 tracked artefacts (`evidence/h57_uniqueness_20261007.json`) |
| Former projected DTI / marginal-credit / floor claims | **INVALIDATED — FORENSIC ONLY**; see the metric-identity correction |

> **Nothing on this page is an organizer score.** The former live-equivalent estimates and
> threshold-derived decisions are invalidated. Owner-reported ladder values are not tied by an
> organizer receipt to exact local parent-file bytes.

---

## 1. What the brief asked for, and where each requirement is satisfied

| Brief requirement | Where |
|---|---|
| Combine the selected dotted and tip/step-over families with Dempster–Shafer | §2 — historical recipe; owner-reported scores do not verify these exact bytes as the two best families |
| Export Dempster diagnostics separately | `m(Θ)` is residual unassigned/ignorance mass; raw conflict `K` is a separate diagnostic, not a disagreement or acceptance metric |
| Normalize combined belief to [0, 1] | `…-diag-belief.tif`, max = 1.0 |
| Verify it is not the naive mean | §6 — r = 0.789, mean \|Δ\| = 0.097 on positive cells, max \|Δ\| = 0.907 |
| Bounded local uniqueness check | `evidence/h57_uniqueness_20261007.json` → UNIQUE / 99 compared files; not organizer verification |
| Local range audit | `evidence/h57_format_audit_20261007.json` records finite [0,1] values; this is not portal acceptance |
| Historical name/note | retained in the prior concurrent-session page; not submission clearance |
| Public-proxy diagnostics | §4 — four recorded blocks; old break-even and PASS/FAIL labels withdrawn; not a comparable H49 promotion holdout |
| Recorded source trail | §3 — previous session cites USGS 3DEP pages and receipts; authentication, completeness and use rights not re-verified here |

---

## 2. Construction

Three mass functions on the frame Θ = {F = "new fault here", N = "not a new fault"}:

**A — dotted family.** `data/families/dotted_b2_prune_02778.tif`, 37,654 dots; its **0.2778**
score is owner-reported and not linked by organizer receipt to these exact bytes. The recipe used
Shafer reliability discount **r_A = 1.0** as an assumption, not a validated reliability.

**B — tip / step-over family.** `data/families/tip_stepover_r30_02632.tif`, 41,865 dots; its
**0.2632** score is likewise owner-reported and unverified at file level. The recipe used
**r_B = 0.2632 / 0.2778 = 0.9474** as a heuristic weight, not a calibrated likelihood.

**C — lidar relief.** `data/external/h52_scarp3m_100m.tif`, band `sigma_mean`, stored in
**centimetres** per the docstring of `scripts/dem_region_merge.py`
(`h_gate07, h_gate12, h_all, sigma_mean : centimetres (value/100 = m)`). Admitted cells satisfy
all four gates:

1. `sigma_mean ≥ 200` → **mean 3 m context roughness ≥ 2.0 m**;
2. **no kernel support from either family** — `max_kernel_to_truth(A ∪ B) = 0`, i.e. more than
   300 m from any existing dot;
3. `d(catalogue) > 2` cells, i.e. **more than 200 m from the published USGS/INGENIOUS catalogue**;
4. `cover ≥ 50` — at least half the 100 m cell is covered by valid 3 m samples —
   then a 3-cell non-maximum suppression.

That yields **20,377** cells in the recorded build. Discount **r_C = 0.95** was a recipe
parameter; the former marginal-credit argument for it is invalidated and does not show that the
weight is optimal.

**Absence assignment.** The historical recipe set `a(x) = 0` inside the 200 m catalogue flank.
This was motivated by an owner-reported ladder, not by verified score-to-file attribution. It is an
assumption for the artifact, not measured proof that excluded dots earned zero live credit.

Dempster's rule is applied **A ⊕ B**, then **⊕ C** (`src/gems48/ds.py`), which is why the
diagnostics carry a real conflict field (K max 0.947) instead of a smoothed average.

### Former per-dot decision analysis — withdrawn

The former statement that arbitrary additions are profitable iff `credit > 0.2·DTI`, and its
application to the three sources, was generalized beyond its one-variable assumptions and then
calibrated through the invalid `FPw = S − TPw` inversion. The resulting 0.0549 break-even,
per-source live-credit figures, admission/rejection decisions, and explanation of the emission as
an optimized A ∪ C selection are withdrawn. The recipe and emitted file remain reproducible
historical artifacts; they are not established as metric-optimal. See the [metric-identity
correction](h57-relief-metric-erratum-20261007.md).

---

## 3. External-data notes as recorded (not independently source-verified here)

**USGS 3D Elevation Program (3DEP), 1 m lidar.** Official programme page (already cited in
`docs/sources.html`): <https://www.usgs.gov/3d-elevation-program/about-3dep-products-services>.
The prior session's receipts record that tiles were obtained from a URL pattern attributed to a
USGS staging bucket for The National Map elevation products. This correction has not independently
re-fetched or authenticated those source bytes. The recorded URLs have the form

```
https://prd-tnm.s3.amazonaws.com/StagedProducts/Elevation/1m/Projects/<PROJECT>/TIFF/USGS_1M_11_<tile>_<PROJECT>.tif
```

e.g. `…/1m/Projects/NV_WestCentral_EarthMRI_2020_D20/TIFF/USGS_1M_11_x42y425_NV_WestCentral_EarthMRI_2020_D20.tif`
(source SHA-256 `110073d0…`, 262,121,460 bytes, EPSG:26911, 1.0 m pixels — `data/pilot/dem3m/dem_pilot_receipt.json`).
`scripts/dem_region_scarp.py` downloads and reduces each tile to 3 m, `scripts/dem_region_merge.py`
mosaics them onto the official 100 m grid. Merged product: `data/external/h52_scarp3m_100m.tif`
(43 MB, 7 bands, int16), from **697 tiles, 0 failures**
(<https://github.com/buffedlizard55-lab/GEMSDOE48/actions/runs/37565284104>; per-tile source
SHA-256 recorded in `data/external/h52_scarp3m_100m.json`). No per-project DOI is asserted here
because none is recorded in this repository's receipts.

The prior local mosaic receipt reports `cover > 0` over **5,900,588 cells = 48.1 % of the grid and
73.8 % of the footprint**; `sigma_mean ≥ 2.0 m` over 2,300,700 cells. These are recorded artifact
measurements, not an independent completeness or source-authentication check.

**Geological reading.** In the Basin and Range, a 100 m cell whose *mean* 3 m context roughness
exceeds 2 m is bare, blocky, steep terrain: range fronts, triangular facets, and young fault
scarps too recent to be planed smooth. The original report cited forum topic 11536 for an interpretation that "new fault" can include
geometry not captured by the published USGS/INGENIOUS mask, including newly mapped geometry of an
existing system. This correction does not independently verify that interpretation or infer that
the selected high-relief cells are faults.

Selected cells: median roughness **7.67 m**, range 2.00–173.44 m.

---

## 4. Historical validation work — live interpretation withdrawn

### 4.1 Retired live-equivalent surrogate

The prior report fitted `T_live = 0.9324 × T_SGMC` and a DTI denominator constant from owner-
reported scores, then used the results to infer hidden-truth totals, per-dot break-even and a live
score. The construction substituted `FPw = S − TPw`; this is invalid because the official metric
uses `FPw = S − Q`, and `TPw` and `Q` are generally unequal. The former fit and derived numbers
are retained under `historical_invalid_projection_forensic_only` in
[`evidence/build_h57_receipt_20261007.json`](../../evidence/build_h57_receipt_20261007.json), but
the corrected builder does not regenerate them. See the [erratum](h57-relief-metric-erratum-20261007.md).

### 4.2 Conditional public-proxy arithmetic

The earlier calculation recorded `T_SGMC(parent) = 5,517.6`, `T_SGMC(H57-RELIEF) = 9,409.7`,
and a difference of 3,892.0 on its named SGMC-derived public proxy. These kernel sums are conditional
proxy measurements, not private-label credit or live score. The old conversion to `T_live`,
`0.1781` marginal live credit per new dot, and DTI `0.2744 → 0.3844` is withdrawn.

### 4.3 Four disjoint proxy blocks — descriptive counts only

The prior run recorded the following block counts and raw public-proxy credit-per-dot arithmetic.
The table is retained as a historical calculation; no universal threshold or PASS/FAIL status
follows from it.

| block | lidar dots | proxy-truth cells | recorded raw proxy credit/dot |
|---|---:|---:|---:|
| 0 (SW) | 9,148 | 23,130 | 0.1318 |
| 1 (NE) | 2,867 | 2,353 | 0.0520 |
| 2 (NW) | 4,087 | 23,192 | 0.2587 |
| 3 (SE) | 4,275 | 13,447 | 0.2847 |

The former comparisons with 0.0549 and the 3/4 “pass” interpretation are invalidated. These
calculations are not the required like-for-like H49 promotion holdout across both proxy regimes.

### 4.4 Retired sensitivity scenarios

The former sensitivity table (including the 0.3844 projection, 0.2254 floor and 0.30 scale
break-even) reused the invalid surrogate and has no valid score-estimate or decision-bound meaning.
Exact recorded values remain only in the explicitly invalidated forensic receipt and erratum.
---

## 5. Historical ladder note — no causal or ceiling inference

The original report recorded an owner-reported 0.2600 → 0.2708 → 0.2778 sequence and a dated
2026-10-06 leaderboard read. The ladder is not tied by an organizer receipt to exact local TIFF
bytes. The old inverse fit, inferred hidden-truth totals, spacing saturation, false-positive
interpretation, ideal-coverage ceiling, and leaderboard-reachability calculation are all withdrawn;
see the [metric-identity correction](h57-relief-metric-erratum-20261007.md). The dated public row
remains historical context only and does not verify a score for this artifact.
---

## 6. Not the naive mean

| comparison | value |
|---|---|
| Pearson r, Bel vs ½(A+B) over all 12,279,160 cells | 0.7890 |
| Pearson r on the 756,450 positive cells | 0.7978 |
| Spearman ρ | 0.8821 |
| mean \|Δ\| on positive cells | 0.0971 (24 % of the 0.4099 mean positive belief) |
| max \|Δ\| | 0.9069 |
| mean \|Δ\| vs any affine rescaling of ½(K_A + K_B) | 0.0198 |

About 21 % of the belief's variance is not explained by the naive mean, and the recorded
affine-residual test found it was not a rescaled kernel average. This is a construction comparison
only; it does not establish prediction quality or validate the owner-score-derived recipe weights.

Dempster internals: m(Θ) mean 0.0221, max 1.0, 756,450 positive cells; raw conflict K mean 0.0212,
max 0.9474.

---

## 7. Historical lever measurements — generalized/refutation claims withdrawn

The previous session compared multiple variants on public-proxy calculations. Only the named
measurements are retained; the old universal break-even, “exhausted,” “every emission loses,” and
“do not retry” verdicts are not current scientific or promotion conclusions.

| lever | recorded measurement | current interpretation |
|---|---|---|
| Redundancy sparsification | a recorded holdout retained 69.60 % of the chosen public-proxy coverage (one fold −91 %) | conditional result for this tested proxy/protocol; not a live-score bound |
| Coverage-neutral removals | the recorded kernel calculation found no zero-cost removal among the tested parent dots | finite calculation on the named artifact/proxy, not a universal impossibility result |
| Rigid-shift registration | best tested shift (0, −1) changed recorded `T_SGMC` by +0.72 % | public-proxy diagnostic only; the old live-score comparison is withdrawn |
| Dempster consensus emissions | recorded union 0.2617 and intersection 0.2458 in the old proxy analysis | do not generalize to every fusion or geological candidate |
| Bulk lidar additions | prior screen recorded 44 candidates | the invalid break-even cannot classify them as profitable/unprofitable |
| Catalogue-flank pruning ladder | the old nested-chain analysis used owner-reported scores | score attribution and live-credit interpretation remain unresolved |
| ρ-weighted coverage-greedy placement | the prior run reported reduced `T_SGMC` | conditional algorithm comparison, not live performance |
---

## 8. Original self-correction notes — later metric correction supersedes the projections

1. Exploratory scripts initially accumulated marginal gain per kernel offset and double-counted
   truth pixels reached by multiple dots. The later exact public-proxy calculation used
   `Σ_g max(K_S − K_A, 0)` and recorded `T_SGMC` as a sum of kernel credits. This corrected the
   scratch arithmetic, but **did not validate the live-score inversion**.
2. The subsequently identified metric-identity error invalidates the fitted `T_live` scale,
   `0.1781` live credit/dot, `0.3844` projection, `0.0549` threshold, block pass labels, ceiling,
   floor and associated recommendations. They are preserved only in the forensic receipt and
   [`h57-relief-metric-erratum-20261007.md`](h57-relief-metric-erratum-20261007.md).
3. The source audit records unresolved attribution between the owner-reported 0.2778 score and
   exact local B2 bytes. No organizer receipt ties that row or the owner-reported ladder to the
   shipped H57-RELIEF TIFF or its parent.
4. The local uniqueness receipt compares 99 tracked artifacts and records no byte- or support-
   identical duplicate. This is a bounded local comparison, not organizer-side uniqueness.
5. No organizer score or portal-acceptance result is recorded for H57-RELIEF. The builder emits
   local format and construction receipts only.
---

## 9. Receipts

| file | content |
|---|---|
| `evidence/build_h57_receipt_20261007.json` | construction, emission counts, Dempster internals, local format, per-file SHA-256s; former projection retained only under an explicitly invalid forensic key |
| `evidence/h57_format_audit_20261007.json` | independent re-open and grid/range audit |
| `evidence/h57_metric_identity_erratum_20261007.json` | machine-readable withdrawal of the former inverse-model claims |
| `docs/research/h57-relief-metric-erratum-20261007.md` | current verdict, invalidated quantities and corrected scope |
| `evidence/h57_uniqueness_20261007.json` | bounded 99-file local byte/support comparison; not organizer verification |
| `scratch/h57_exact.py` / `scratch/h57_exact.json` | corrected marginal-credit derivation and block table |
| `scratch/h57_block1.py` | the truth-density diagnosis of block 1 |

Reproduce with:

```bash
python scripts/build_submission_h57.py
python scripts/validate_submission.py docs/downloads/GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07.tif
python scripts/check_candidate_uniqueness.py docs/downloads/GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07.tif --receipt /tmp/u.json
```

The builder now writes a rebuild and receipt under the ignored `scratch/h57-relief-rebuild/`
folder by default. It does not overwrite the retained download or dated forensic receipt in
`evidence/`; it also does not regenerate any invalidated live-score projection.
