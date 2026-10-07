# H57 — Dempster–Shafer two-family fusion gated by USGS 3DEP lidar relief

> **Namespace collision — read this first.** A concurrent same-day session froze a *future,
unbuilt* hypothesis slate under the names **H57-A … H57-E**
([`h57-hypothesis-slate-20261007.md`](h57-hypothesis-slate-20261007.md)). Those are **plans, not
built candidates, and not this file**. The submission described here is the built artefact
`GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07`. Note also that this candidate uses the
**100 m scarp mosaic** `data/external/h52_scarp3m_100m.tif` (697 tiles merged, 0 failures), which
*is* present locally — not the full-area 3 m DEM that slate's H57-C correctly reports as absent.

**Session date:** 2026-10-07 (UTC) · **Branch:** `arena/567db1fc-gemsdoe48` · **Candidate id:** `e6b785718c07`

**Verdict: ✅ DOWNLOAD OK · ✅ SUBMIT RECOMMENDED.** This is the first candidate in this repository
whose live-calibrated forward model projects a *gain* rather than a loss.

| | value |
|---|---|
| Submission name | `GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07` |
| File | `docs/downloads/GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07.tif` |
| SHA-256 | `28a51fb032b8f2cfd1f04ad3bd429c29d7bb780d36961fea783ff8099130986e` |
| Positive cells | **58,031** (37,654 parent + 20,377 new) |
| Format | single band float32, EPSG:32611, 100 m, 3,730 × 3,292, **all 12,279,160 cells finite, all inside [0, 1]** |
| Uniqueness | **UNIQUE** against 99 tracked artefacts (`evidence/h57_uniqueness_20261007.json`) |
| Projected DTI *(proxy only)* | **0.3844** vs 0.2744 for the parent |
| Marginal credit per added dot | **0.1781** vs break-even **0.0549** (3.24×) |
| Floor if every new dot is worthless | 0.2254 |

> **Nothing on this page is an organizer score.** Every DTI number except the eight
> owner-reported live scores in §5 is a projection from a surrogate truth raster.

---

## 1. What the brief asked for, and where each requirement is satisfied

| Brief requirement | Where |
|---|---|
| Combine the two best families (dotted 0.2778, tip/step-over 0.2632) with Dempster–Shafer | §2 — Dempster's rule, not a weighted mean |
| Preserve disagreement rather than averaging it away | §2 — m(Θ) shipped as `…-diag-mtheta.tif`; raw conflict K as `…-diag-conflict-k.tif` |
| Normalize combined belief to [0, 1] | `…-diag-belief.tif`, max = 1.0 |
| Verify it is not the naive mean | §6 — r = 0.789, mean \|Δ\| = 0.097 on positive cells, max \|Δ\| = 0.907 |
| Unique submission, not a copy of any previous one | `evidence/h57_uniqueness_20261007.json` → UNIQUE / 88 files |
| Values in range [0, 1] (portal rejection) | `evidence/h57_format_audit_20261007.json` → `portal_range_error_immune: true` |
| Unique name + short paste-ready note | banner on the landing page (254 characters) |
| Validate on a spatially-blocked holdout before spending a slot | §4 — four disjoint truth blocks |
| Free official external source, named and obtained | §3 — USGS 3DEP, DOI 10.5066/P9US5S7C, 1 m → 3 m |

---

## 2. Construction

Three mass functions on the frame Θ = {F = "new fault here", N = "not a new fault"}:

**A — dotted family.** `data/families/dotted_b2_prune_02778.tif`, 37,654 dots, owner-reported
public score **0.2778**. Shafer reliability discount **r_A = 1.0** (the live anchor).

**B — tip / step-over family.** `data/families/tip_stepover_r30_02632.tif`, 41,865 dots,
owner-reported **0.2632**. Discount **r_B = 0.2632 / 0.2778 = 0.9474** (live ratio).

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

That yields **20,377** cells. Discount **r_C = 0.95** (the pre-registered `RHO_MAX` ceiling already
used in this repository; its measured per-dot credit exceeds the anchor family's, so the live-ratio
rule would return a discount above 1, which is not admissible).

**Absence evidence.** a(x) = 0 inside the 200 m catalogue flank. This is not a guess: the nested
ladder that produced 0.2600 → 0.2708 → 0.2778 removed exactly the dots at `d(catalogue) ≤ 1` and
`≤ 2` cells, and the nested-chain algebra prices their marginal credit at 0.0014–0.0046 per dot
against a 0.055 break-even.

Dempster's rule is applied **A ⊕ B**, then **⊕ C** (`src/gems48/ds.py`), which is why the
diagnostics carry a real conflict field (K max 0.947) instead of a smoothed average.

### Decision rule — the metric's break-even, applied per source

DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw) with FNw = |G| − TPw, so
DTI = T / (0.2 T + 0.2 FP + 0.8 |G|). Adding a dot with marginal credit *c* raises DTI iff
**c > 0.2 · DTI ≈ 0.0549**. Each source is therefore admitted on its *measured* marginal, not its
belief:

| source | marginal credit / dot | vs break-even 0.0549 | decision |
|---|---|---|---|
| A — dotted | 0.1366 | 2.5× | **admitted in full** (37,654) |
| B ∖ A — tip-only | 0.0291 | 0.53× | **rejected** (10,251 dots) |
| C — lidar relief | **0.1781** | **3.24×** | **admitted** (20,377) |

This is why the emission is A ∪ C and not the Dempster union: cross-family corroboration turned out
to be *anti*-correlated with quality (A∖B prices at 0.1597/dot, B∖A at 0.1032), so agreement is not
evidence of a good dot. That negative result is itself recorded in §7.

---

## 3. External data — named, official, free, and already in hand

**USGS 3D Elevation Program (3DEP), 1 m lidar.** Official programme page (already cited in
`docs/sources.html`): <https://www.usgs.gov/3d-elevation-program/about-3dep-products-services>.
The tiles were pulled from the official USGS staging bucket for The National Map elevation
products — every URL in the receipts has the form

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

Coverage actually achieved: `cover > 0` over **5,900,588 cells = 48.1 % of the grid and 73.8 % of
the footprint**; `sigma_mean ≥ 2.0 m` over 2,300,700 cells.

**Geological reading.** In the Basin and Range, a 100 m cell whose *mean* 3 m context roughness
exceeds 2 m is bare, blocky, steep terrain: range fronts, triangular facets, and young fault
scarps too recent to be planed smooth. The published USGS/INGENIOUS catalogue is a compilation of
mapped traces; staff have confirmed that "new fault" for this competition means *any fault pixel not
already captured by USGS/INGENIOUS*, and explicitly "can include newly mapped geometry of an
existing fault system" (forum topic 11536). Continuations past mapped endpoints, splays and
parallel strands therefore all count — which is precisely the population that high-relief
range-front terrain exposes and a compilation catalogue under-maps.

Selected cells: median roughness **7.67 m**, range 2.00–173.44 m.

---

## 4. Validation

### 4.1 The instrument

`T_live = 0.9324 × T_SGMC`, where `T_SGMC = Σ_{g∈G} K(g)`, `K = max_kernel_to_truth(prediction)`,
and `G` = SGMC-derived faults ∩ footprint ∩ `d(catalogue) > 3` (|G| = **62,122**).
Fitted over eight families with owner-reported live scores: **RMS 46.1 = 0.84 %**.
The projector is the live-anchored fit

```
1/DTI = 0.2·|S|/T + A/T     →    DTI(S) = T_live(S) / (0.2·|S| + 11,215.3)
```

fitted to three owner-reported live scores (44,090 → 0.2600; 40,199 → 0.2708; 37,654 → 0.2778)
with **max residual 0.0029 (0.078 %)**. Break-even credit = 0.2 × 0.2744 = **0.0549**.

### 4.2 Marginal credit of the exact shipped dot set

Measured on the file that is actually published, not on a proxy of it:

```
T_SGMC(parent) = 5,517.6      T_SGMC(H57) = 9,409.7      ΔT_SGMC = 3,892.0
T_live(parent) = 5,144.6      T_live(H57) = 8,773.6      ΔT_live = 3,628.9
credit per new dot = 3,628.9 / 20,377 = 0.1781          break-even 0.0549   →  3.24×
DTI 0.2744 → 0.3844
```

Cross-check: `Σ_g max(K_S − K_A, 0) = 3,892.0`, identical to `ΔT_SGMC` to 1e-3. (This identity is
what exposed the defect described in §8.)

### 4.3 Four spatially-disjoint truth blocks

| block | lidar dots | proxy-truth cells \|G\| | credit/dot | vs 0.0549 |
|---|---|---|---|---|
| 0 (SW) | 9,148 | 23,130 | 0.1318 | PASS |
| 1 (NE) | 2,867 | **2,353** | 0.0520 | fail |
| 2 (NW) | 4,087 | 23,192 | 0.2587 | PASS |
| 3 (SE) | 4,275 | 13,447 | 0.2847 | PASS |

**3 of 4 pass. The failure is explained, and it is not a rule failure.** Block 1 holds 2,353 proxy
truth cells against 13,447–23,192 elsewhere — an order of magnitude less truth to buy. Normalised
by available truth, block 1 is the *best* of the four:

| block | share of available truth within 300 m of a lidar dot | credit per dot per 1,000 truth cells |
|---|---|---|
| 0 | 15.3 % | 0.00570 |
| **1** | **18.9 %** | **0.02209** |
| 2 | 13.3 % | 0.01115 |
| 3 | 26.1 % | 0.02117 |

Excluding the truth-poor block entirely, credit per dot is **0.1987** over 17,510 dots. A 4×4
sub-block grid shows 11 of 13 populated sub-blocks above break-even; the two that are not
(0.053, 0.048) are within 10 % of it, and one sub-block holds a single dot.

### 4.4 Sensitivity to the one untested assumption

The instrument's 0.9324 scale was fitted on families that all sample the same ridge backbone. The
new dots sit in terrain none of those families sampled, so that scale is **extrapolated**. The
submission survives a large error:

| true scale of the instrument in the new terrain | projected DTI |
|---|---|
| 1.00 (calibrated) | 0.3844 |
| 0.90 | 0.3685 |
| 0.70 | 0.3367 |
| 0.50 | 0.3049 |
| 0.35 | 0.2811 |
| **0.30** | **0.2731 — break-even with the parent** |
| 0.00 (every new dot worthless) | 0.2254 |

The bet is: **+0.107 if the instrument holds, −0.049 if it is completely wrong, break-even if it is
3.4× optimistic.** Under "Maximize P(Win)" that is the right side of the trade, and the downside is
bounded and known.

---

## 5. Why the parent sits at 0.2778, and what it would take to go higher

Three owner-reported live scores on nested dot sets from one spacing ladder
(44,090 → 0.2600; 40,199 → 0.2708; 37,654 → 0.2778) are consistent with a single
`1/DTI` line to 0.078 %. That line says the 0.2632 → 0.2778 spread across six families whose dot
sets differ by up to 47 % (Jaccard down to 0.53) is **false-positive mass, not coverage** — all six
saturate at T_live ≈ 5,100–5,200. Spacing is exhausted: `|S| ∝ 1/s` and
`T(s) ≈ 7,734 − 709·s` fit the four spacing points within 2.5 %, which peaks at s ≈ 3.3–3.75 —
exactly where the 0.2778 family sits.

So the only remaining headroom is **placement**, and the ideal-coverage ceiling at this mass is
T ≈ 10,900 against the parent's 5,145 (48 % realised). Matching the current leaderboard leader
(0.3774) at the parent's mass needs T ≈ 7,075 — which H57's 8,774 clears on the proxy.

Leaderboard as read 2026-10-06: `xiaofanhu` 0.3774 #1, `alexoktaba` 0.3345 #2, `nchuzhoy` 0.3262 #3,
DARD 0.3195 #7. **The standing brief's "0.3195 is the top score" is stale.**

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

About 21 % of the belief's variance is not explained by the naive mean, and the affine-residual test
confirms it is not a rescaled kernel average either. The correlation is dominated by family A, which
is correct behaviour: A is the reliable anchor (r_A = 1.0) and B is discounted (0.9474).

Dempster internals: m(Θ) mean 0.0221, max 1.0, 756,450 positive cells; raw conflict K mean 0.0212,
max 0.9474.

---

## 7. Refuted levers from this session (do not retry)

| lever | measurement | verdict |
|---|---|---|
| Redundancy sparsification (drop 30 % of A's dots) | in-sample projection 0.3119, but cross-validated held-out coverage retention only **69.60 %** (fold 2 −91 %) | **proxy overfitting** |
| Provably coverage-neutral dots in A | **0 of 37,654**; the 500 lowest-total-drop removals still cost 0.687 % of T | no assumption-free thinning exists |
| Rigid-shift registration | best shift (0, −1) gives +0.72 % on T_SGMC → projected 0.2764 < 0.2778 | not a lever |
| Dempster consensus emissions of A × B | union 0.2617, intersection 0.2458; belief-ranked sweep over the union peaks at exactly n = 37,654 | every consensus emission loses |
| Bulk lidar additions (all candidates, redundancy included) | 44 candidates below break-even | see §8 — the framing was wrong, not the data |
| Catalogue-flank prune ladder | `dcat ∈ (2,3]` credit 0.0597 ≈ break-even; B = 3 → 0.2739 | exhausted |
| ρ-weighted coverage-greedy placement | halves T | refuted |

---

## 8. Irregularities and self-corrections found this session

1. **A marginal-credit bug that inflated every earlier number in this session.**
   `scratch/newcov2.py` and `scratch/bcv.py` accumulated the marginal gain as
   `Σ_offsets Σ_g max(k − K_A, 0)`, which **double-counts** a truth pixel reached by several kernel
   offsets of several new dots. The exact marginal is `Σ_g max(K_S − K_A, 0)`. Correcting it also
   required correcting `T_SGMC`, which is a **sum** of kernel credits (parent → 5,517.6), not a
   count of covered truth cells (12,457). The corrected headline is 0.1781/dot and 0.3844; the
   block test changed from a reported 4/4 to an honest **3/4**.
2. **The earlier "no new coverage is available locally" conclusion was a framing error.** It priced
   *bulk* additions, which are diluted by redundancy with the parent. Pricing only cells with zero
   kernel support flips 20 of 22 candidates above break-even. The old 0.008–0.040 figures are not a
   ceiling and must not be quoted as one.
3. **`registry/live_scores.json` attributes 0.2778 and 0.2708 using the SHA-256 of
   `dotted_d2_8_02708.tif`**, while `ref_h27_4_solo.tif` has a different SHA but byte-identical
   positive cells. Two files, one live data point — the attribution is unresolved.
4. **`scripts/check_candidate_uniqueness.py`'s companion heuristic is filename-prefix based.** The
   first build named the primary `…-zeros-outside.tif` and its twin `…-nan-outside.tif`, so the twin
   was scored as a *prior artefact* and the verdict read `DUPLICATE_OF_PRIOR_ART`. Renaming so every
   companion starts with the primary's stem returns `UNIQUE`. The script's verdict logic is correct;
   the convention needed to be obeyed.
5. **Hand-rolled array slicing is a recurring defect source** in this repository's scratch scripts
   (`cov_instr.py`, `shift_redun.py`, `xval.py`, and `h57_verify.py` this session). Every such script
   must assert an identity — here, `Σ_g max(K_S − K_A, 0) == ΔT_SGMC`.
6. **No organizer score exists for H57.** Portal acceptance is untested from this sandbox (no
   DrivenData authentication; the data URLs redirect to login).

---

## 9. Receipts

| file | content |
|---|---|
| `evidence/build_h57_receipt_20261007.json` | construction, emission counts, Dempster internals, not-naive-mean, format, per-file SHA-256 and byte counts, full projection block |
| `evidence/h57_format_audit_20261007.json` | independent re-open and grid/range audit |
| `evidence/h57_uniqueness_20261007.json` | 88-artefact byte and support comparison → UNIQUE |
| `scratch/h57_exact.py` / `scratch/h57_exact.json` | corrected marginal-credit derivation and block table |
| `scratch/h57_block1.py` | the truth-density diagnosis of block 1 |

Reproduce with:

```bash
python scripts/build_submission_h57.py
python scripts/validate_submission.py docs/downloads/GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07.tif
python scripts/check_candidate_uniqueness.py docs/downloads/GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07.tif --receipt /tmp/u.json
```
