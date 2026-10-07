> **CORRECTION (2026-10-07):** This historical analysis assumes `FPw = S - TPw`, which is generally false under the official metric. Consequently its inverted truth mass, 0.2843 "ceiling", break-even thresholds and live-equivalent scenarios are *not* proven private-label bounds. Its underlying measurements are preserved for audit, but **do not use them to clear an upload**. Read the [metric-identity erratum](metric-identity-erratum-20261007.md) first.

# H55 — a live-calibrated forward model, the family ceiling, and a conduit-anchored candidate

Session date: **2026-10-07 UTC**. Candidate label: **H55**. Everything below is
recomputed from files in this repository by `scripts/calibrate_live_model.py`,
`scripts/build_submission_h55.py`, `scripts/audit_h55.py` and
`scripts/run_spatial_holdout.py`; receipts are named inline. No number here is
transcribed from memory, and **no organizer score exists for any file in this
repository**.

---

## 0. Summary

| question | answer |
|---|---|
| Why did 0.2778 win, and can it be beaten? | It is within **1.84 %** of coverage-optimal for its corridor field, and its mass is within 0.4 % of the field's optimum. The whole family is capped at **live-equivalent 0.2843** at *any* mass, by any thinning, re-weighting or fusion. |
| Can 0.3195 be reached by combining the two best families? | **No.** The two families recover statistically identical hidden truth (T = 5,209 vs 5,157, 1 % apart), so their union adds 27 % mass and almost no truth. The live-calibrated model prices the naive union at **0.2588 model / 0.2638 live-equivalent, i.e. −0.0140**. |
| Can 0.2888 (#8), 0.3195 (#7), 0.3262, 0.3345 or 0.3774 (#1) be reached from this backbone at *any* mass? | **No — none of them.** Maximising `rho·Cov/(0.2 S + 0.8 \|G\|)` over *all* subset sizes of `B_elig` peaks at **n = 37,167, model DTI 0.2793, live-equivalent 0.2843**. Every leaderboard row above 0.2778 needs more truth than any subset of this field can deliver. |
| Can 0.3774 (the actual #1) be reached from anything in this repository? | **No, and not even in principle.** 0.3774 needs T = 7,077 at 37,654 px. The *dense, unthinned* backbone's entire truth yield — all 121,131 px emitted — is T = 6,813. The leader's numerator exceeds the total truth content of the best corridor field in this repository. |
| What is shipped? | `GEMSDOE48-H55-conduit-conflict-priced-20261007-055da9855353` — the 0.2778 core untouched, plus 1,124 conflict-priced gap dots and 652 hydrothermal-conduit anchors (39,430 px total). Blocked proxies: **+0.001031 catalogue (4/4 folds)** and **+0.000795 SGMC-off (4/4 folds)** against the dotted parent, and **+0.000795 SGMC-off (4/4 folds)** against the tip parent — the first candidate in this repository to beat *both* parents in *every* fold on the SGMC proxy. |
| Does it pass the repository's newest gate? | **No.** A concurrent session merged `scripts/audit_candidate.py` (protocol GEMSDOE48-GATE-2, mass-neutral) while this one was running. H55 returns `FAIL_MASS_NEUTRAL`: equal-mass credit density −0.002014 and added-cell credit 0.0102 against the metric's 0.0556 bar. §6.4 reconciles the two instruments and gives the honest bracket **0.2736 – 0.2880**. |
| What is the honest expected live score? | Floor **0.2727** if every added pixel earns zero; **0.2778** if only the in-family additions pay; **0.2797 – 0.2880** as the conduit anchors' credit rises from break-even (0.0556) to 0.30. The addition is designed as a **measurement**: A2's modelled gain is **+0.0019** and A1's denominator cost at zero credit is **−0.0019** — they cancel to **−0.00003**, so the returned live score is a clean read on the conduit hypothesis. |

---

## 1. The metric, and three consequences that are exact rather than approximate

Transcribed by two independent sibling repositories from the organizer's problem
description (competition 306, page 967) and corroborated independently by the
organizers' own reference solution, which trains with
`TverskyLoss(alpha=0.2, beta=0.8, mode="binary")`:

```
k(d)  = max(1 - d/300 m, 0)
TPw   = sum_g max_x p(x) k(d(x,g))
FPw   = sum_x p(x) (1 - max_g k(d(x,g)))
FNw   = sum_g (1 - max_x p(x) k(d(x,g)))
DTI   = TPw / (TPw + 0.2 FPw + 0.8 FNw)
```

**(a) The optimal submission is binary.** For one cell of value `v` that is the
argmax of its truth pixel with realised weight `k`,
`d/dv [(T0 + v k)/(D0 + 0.2 v)] = (k D0 − 0.2 T0)/(D0 + 0.2 v)²`, whose sign is that
of `k − 0.2·DTI` and is **independent of `v`**. Every cell is therefore pushed to 0
or 1. This is asserted numerically in `tests/test_h55.py::test_binary_emission_is_dti_optimal`
and is why the graded Dempster–Shafer layers ship as *diagnostics*.

**(b) An added pixel pays iff its realised kernel weight exceeds `0.2·DTI`** — 0.0556
at DTI = 0.2778, i.e. 0.397× the mean credit of a dot in the live-best artifact.

**(c) Adding a pixel can never reduce `TPw`**, because `TPw` is a *maximum* over
emitted pixels. The only risk of an addition is the 0.2 denominator cost. This makes
the worst case of an additive candidate **exactly computable** rather than estimated,
and it is the reason H55 is additive-only.

---

## 2. A live-anchored forward model (new this session)

### 2.1 Inputs

Eight owner-reported live scores were restored byte-identical from the hash-pinned
public mirrors and their pixel counts measured directly:

| artifact | emitted px | owner-reported live | restored SHA-256 (first 12) |
|---|---:|---:|---|
| `h19_5_backbone` (dense corridor field) | 121,131 | 0.1922 | `ec1f9b56b83c` |
| `d1_5_dotted` (Poisson d = 1.5 px) | 60,069 | 0.2477 | `68d0e2e4fcc5` |
| `A_d2_8` (Poisson d = 2.83 px) | 44,090 | 0.2600 | `3e78737f0da8` |
| `B_prune100` (A − dots ≤ 100 m off-catalogue) | 40,199 | 0.2708 | `ab0230015224` |
| `C_prune200` (B − dots 100–200 m off-catalogue) | **37,654** | **0.2778** | `c55bafc47005` |
| `h36_rung30` (independent 37,660 px thinning) | 37,660 | 0.2710 | `5556aa1438fd` |
| `h32_prethin_tip` (tip/Euler variant) | 42,294 | 0.2649 | `04d31922f5c1` |
| `h33d_tip_step` (tip/step-over family best) | 41,865 | 0.2632 | `87f857d505e2` |

Containment was verified pixel-wise, not assumed: `d1_5 ⊂ h19_5`, `C ⊂ B ⊂ A ⊂ d1_5 ⊂ h19_5`,
`h36 ⊂ h19_5`, `h32 ⊂ h19_5`, and `h33d` shares 41,732 of 41,865 px with the backbone
(the 133 extra pixels are the Euler clusters its own receipt declares).

### 2.2 Identifying the hidden truth mass |G|

Because `FPw = S − M`, `FNw = |G| − TPw` and `M = TPw` for a matched binary emission,

```
DTI = T / (0.2 S + 0.8 |G|)
```

`A → B → C` are strictly nested and the removed dots are the catalogue-adjacent ones
the organizer masks out of scoring, so all three share one `T` and `|G|` is identified.
Least squares over the triple (`live_model.fit_hidden_truth`) gives

```
|G| = 14,027.5 px        shared T = 5,213        residual SSE = 22.9
```

The three pairwise closed-form solutions are 13,368 (A→B), 15,198 (B→C) and 14,089
(A→C) — a ±6 % spread driven entirely by the 4-decimal rounding of the owner-reported
scores. **Internal consistency check:** the three rungs invert to
T = 5,210.3 / 5,216.0 / 5,209.4, i.e. within **0.11 %** of each other. That agreement
is the strongest single piece of evidence in this repository that the removal
mechanism is exactly "catalogue-adjacent dots earn zero", and it is asserted in
`tests/test_h55.py::test_hidden_truth_fit_is_stable_and_positive`.

This supersedes the earlier `|G| = 12,632` figure in `knowledge/research_notes.md`,
which came from a different assumption (that the removed dots earned exactly the
τ = 0.05416 bar rather than zero). Both are recorded; the 14,027.5 value is the one
that makes the three rungs self-consistent to 0.11 %.

### 2.3 The sufficient statistic: eligible-backbone coverage

Define

```
B_elig  = h19_5 backbone AND (distance to public catalogue > 200 m)     (103,805 px)
Cov(X)  = sum_{b in B_elig} max_{x in X} k(d(x, b))
```

and fit `T = rho · Cov` through the origin. Result (`evidence/live_model_calibration_20261007.json`):

```
rho = 0.068015     RMS relative error on the eight live scores = 1.758 %
                   max absolute relative error                 = 3.627 %
```

Per-artifact relative error: backbone +3.46 %, d1.5 +0.63 %, A −1.03 %, B −1.18 %,
C −1.37 %, h36 −1.98 %, h32 −1.07 %, h33d −0.47 %. **Seven of eight are inside ±2 %.**

Why `Cov` and not `S`: `S` spans 37,654–121,131 (3.2×) while `T` spans 5,082–6,813.
Two artifacts with the *same* mass (`C` 37,654 and `h36_rung30` 37,660) differ by
2.4 % in `T` and 2.7 % in `Cov`. Two artifacts differing 12 % in mass (`C` and
`h32_prethin_tip`) differ **0.07 %** in `T` and 0.9 % in `Cov`. Mass is not the
explanatory variable; coverage of the corridor field is.

### 2.4 Weighting the target does not help (negative result)

Nine target weightings were fitted against the same eight live scores — uniform, backbone
density in a 7 px and a 13 px box, its square root and its `log1p`, distance-from-catalogue,
density × distance, radiometric-ratio corroboration (U/K and Th/K from the DOI 10.5066/P93LGLVQ
mirror) and 3 m lidar roughness corroboration. Reproduced by
`scripts/compare_coverage_weightings.py` →
`evidence/coverage_weighting_comparison_20261007.json`:

```
weighting                          rho       RMS rel %   max rel %   vs uniform
uniform                        0.068015        1.758       3.628      +0.000
far_from_catalogue             0.051390        1.659       3.463      -0.099   <- best
lidar3m_roughness_corrob.      0.045219        1.686       3.344      -0.072
radiometric_ratio_corrob.      0.045375        1.796       3.700      +0.038
log1p_dens_13px_box            0.024528        2.127       4.457      +0.369
sqrt_dens_7px_box              0.024928        2.305       4.905      +0.547
dens_13px_box                  0.003914        2.501       5.303      +0.743
dens_7px_x_far                 0.006541        2.562       5.572      +0.804
dens_7px_box                   0.008570        2.634       5.688      +0.876
```

**Density weighting is actively worse** (+0.37 to +0.88 percentage points). The two apparent
improvements — distance-from-catalogue at −0.099 pp and 3 m lidar roughness corroboration at
−0.072 pp — are an order of magnitude smaller than the spread they would have to beat on eight
data points, and both were specified *after* seeing the same eight scores the earlier sessions
tuned on. Uniform coverage is kept, and the two near-ties are recorded as candidates for a
pre-registered re-test once a second family recalibrates `rho`, not as findings.

### 2.5 Where the instrument stops working (measured, not assumed)

One out-of-family live artifact exists: `gemsdoe29-sgmc-off-catalogue-44k`
(44,090 px Poisson-disked on SGMC faults > 300 m off-catalogue, owner-reported
**0.0512**). It inverts to `T = 1,026`, and its eligible-backbone coverage is
`9,306.8`, giving an implied `rho = 0.1102` — **1.6× the in-family value**. The model
with the in-family `rho` predicts 0.0319 for a file that scored 0.0512, i.e. it
**under-predicts out-of-family T by 38 %**.

Consequences, stated plainly:

* The instrument is a **within-family** tool. It may be used to price re-thinnings,
  unions and gap closures of the h19-5 corridor field. It may **not** be used to
  price a new corridor field.
* Every out-of-family mass in H55 is therefore reported as a **scenario band**, never
  as a point prediction.
* The bias direction is known: out-of-family sets do *better* than the model says.
  H55's conduit anchors are therefore more likely to be under-priced than over-priced.

---

## 3. The ceiling, and the answer to "can we beat 0.2778?"

### 3.1 The ceiling table (reproducible: `scripts/calibrate_live_model.py`)

With `DTI = T/(0.2 S + 0.8·14,027.5)`, the numerator required at S = 37,654 px is:

| target | DTI | T needed at 37,654 px | recall T/\|G\| | % above C's T | inside the dense field's total yield (6,813)? | deliverable by a 37,654 px subset? | deliverable at **any** mass? |
|---|---:|---:|---:|---:|:--:|:--:|:--:|
| #1 xiaofanhu | 0.3774 | 7,077.3 | 0.505 | +35.9 % | **NO** | **NO** | **NO** |
| #2 alexoktaba | 0.3345 | 6,272.8 | 0.447 | +20.4 % | yes | **NO** | **NO** |
| #3 nchuzhoy | 0.3262 | 6,117.2 | 0.436 | +17.4 % | yes | **NO** | **NO** |
| #7 DARD | 0.3195 | 5,991.5 | 0.427 | +15.0 % | yes | **NO** | **NO** |
| #8 | 0.2888 | 5,415.8 | 0.386 | +4.0 % | yes | **NO** | **NO** |
| this family | 0.2778 | 5,209.5 | 0.371 | — | yes | yes | yes |

The third test is the decisive one. Greedy maximum-coverage selection over `B_elig`
(exact incremental coverage updates, 25-offset triangular kernel) traces the whole
budget frontier, and its argmax over **all** subset sizes is the family ceiling:

```
n dots   Cov(B_elig)   model DTI
20,000    57,662.6      0.2576
25,000    64,615.9      0.2709
30,000    69,788.1      0.2756
35,000    74,702.5      0.2788
37,167    76,612.8      0.2793   <- frontier maximum (last gain 0.8240)
40,000    78,782.2      0.2788
45,000    82,206.1      0.2765
```

```
family ceiling      model DTI 0.27932   live-equivalent 0.28435
C (live best)       model DTI 0.27277   live            0.27780
in-family headroom  +0.00655 model units = +0.0065 live-equivalent
C's coverage shortfall  75,206.8 of 76,612.8 = 1.84 %
instrument resolution   +/-0.0049 DTI (1.758 % RMS on eight live scores)
```

So: **C's mass is within 0.4 % of the field's optimum (37,654 vs 37,167) and its
placement is within 1.84 % of coverage-optimal.** The entire remaining in-family
headroom is +0.0065 live-equivalent, which is 1.3× the instrument's own resolution —
directionally real, but too small to be resolved by a single submission.

**No emission drawn from this corridor field, at any mass, can reach 0.2888.** That is
the answer to the brief's question, and it is a measured bound rather than an opinion.

### 3.2 All thinnings recover the same truth

| artifact | S | inverted T | recall | credit per emitted px | Cov(B_elig) |
|---|---:|---:|---:|---:|---:|
| dense backbone | 121,131 | **6,813.1** | 0.486 | 0.0562 | 103,805.0 |
| d1.5 dotted | 60,069 | 5,755.5 | 0.410 | 0.0958 | 85,213.1 |
| A_d2_8 | 44,090 | 5,210.4 | 0.371 | 0.1182 | 75,856.7 |
| B_prune100 | 40,199 | 5,216.1 | 0.372 | 0.1298 | 75,786.8 |
| **C_prune200** | **37,654** | **5,209.5** | **0.371** | **0.1384** | **75,206.8** |
| h36_rung30 | 37,660 | 5,082.3 | 0.362 | 0.1350 | 73,191.4 |
| h32_prethin_tip | 42,294 | 5,213.4 | 0.372 | 0.1233 | 75,883.9 |
| h33d_tip_step | 41,865 | 5,157.4 | 0.368 | 0.1232 | 75,459.8 |

Six of the eight cluster at **T = 5,082 – 5,216**. The dotted family and the tip family
are *not independent estimates of different truth*; they are two samplings of one
corridor field and they recover the same hidden mass. Thinning from 121,131 to 37,654 px
discards 23.5 % of the backbone's truth while discarding 68.9 % of its mass — a good
trade, and one that has already been taken.

This corrects a claim in `knowledge/research_notes.md` and the README that dense H19-5
(quoted there as "129 k px") had "the same T, triple the FP". The measured pixel count is
**121,131** and its T is **6,813 — 30.8 % higher than C's**, not equal. The FP part of the
claim is right; the T part is not, and the error hides the fact that the field's *total*
truth content is the binding constraint on the whole family.

### 3.3 Why every fusion in this repository was doomed

`Cov(C ∪ h33d) = 79,153.0` at `S = 47,905`, so the model prices the naive union at
**0.25879 model / 0.26382 live-equivalent, −0.01398 against C**. Dempster's rule,
Yager's rule, plausibility budgets, graded belief, arithmetic means and α = 0.99
normalisations are all *re-weightings of the same coverage over a different mass*.
Because the metric is binary-optimal (§1a), a re-weighting cannot emit more than its own
binarisation; and because the two parents' coverage differs by only 0.3 % while their
masses differ by 11 %, **no combination rule can produce more coverage than the union,
and the union's coverage does not pay for its mass.** The prior sessions' empirical
finding — "no fusion of the two best surfaces beats the better parent" — is therefore not
a coincidence or a proxy artifact. It is a consequence of the metric plus a measured 1 %
difference in T, and it holds at every mass.

## 4. Two instruments this repository has been relying on are contradicted by a live score

### 4.1 The SGMC off-catalogue proxy

Every promotion gate since PR #5 has used "SGMC-derived faults more than 300 m from the
public catalogue" (62,122 px) as the stand-in for hidden truth. But an emission built
*directly on that layer*, at the same 44,090 px mass and the same 2.8 px Poisson spacing
as rung A, scored **0.0512 live — T = 1,026 against the backbone family's 5,210 at the
same mass.** If SGMC-off-catalogue were a good stand-in for hidden truth, that file
would have scored near 0.26.

The proxy is not useless — it is a *relative* ranking device over surfaces that all
contain the backbone — but it is **not a model of the hidden truth**, and gate decisions
that turned on it (H50, H51, H52) should be regarded as unresolved rather than settled.

### 4.2 Catalogue coverage per pixel

The same table explains why "catalogue lift" is not a valid screen either:

| field | px | catalogue coverage per emitted px | live T at ~44 k px |
|---|---:|---:|---:|
| h19-5 backbone | 121,131 | 0.1007 | 6,813 (dense) |
| SGMC faults | 83,593 | **0.1418** | 1,026 (at 44,090 px) |
| GDR wells/springs, all | 12,570 | 0.1023 | not measured |
| GDR wells/springs, Hot | 929 | **0.1897** | not measured |
| INGENIOUS Quaternary fault centroids | 1,125 | **0.3696** | not measured |

SGMC covers *known* faults 41 % more efficiently per pixel than the backbone and scores
5× worse live. **High catalogue coverage does not imply high live T.** Any hypothesis
ranking built on catalogue lift — including the ≥ 2× rule that rejected H52 — is
therefore not sound, and this session does not use it.

What *is* live-verified: `Cov(X; B_elig)` predicts T to ±1.8 % **inside** the family, and
the catalogue-flank prune (dots ≤ 200 m from the catalogue earn ≈ 0) is confirmed by the
0.11 % self-consistency of the three rungs.

---

## 5. H55 — the candidate

### 5.1 Construction (frozen before scoring)

`X = C ∪ A1 ∪ A2`

* **C** — the 37,654 px live-best dotted artifact, carried through **untouched**.
  Nothing is pruned, moved or re-weighted, so the T = 5,209 it already recovers cannot
  be lost. Verified pixel-wise by `scripts/audit_h55.py`
  (`core_preserved_exactly: true`, intersection 37,654/37,654).
* **A2 — conflict-priced gap closure (in-family, model-priced), 1,124 px.** The two
  families disagree on 10,251 pixels. Rather than average them, each candidate
  disagreement/gap site in `(B_elig ∪ tip) \ C` is *priced*: greedy maximum-coverage
  selection admits a site only while its marginal `Cov` gain clears
  **1.25 × 0.2 · DTI_C / rho = 1.0211** coverage units (break-even is 0.8169). The 1.25
  safety factor is pre-registered and makes the choice robust to a ±25 % error in `rho`,
  which is 14× the instrument's measured 1.76 % RMS error. The unconstrained argmax
  prefix would be 2,916 px at live-equivalent 0.2785; the robust prefix is 1,124 px.
  Admitted gains span 1.0215 – 3.5286. Provenance of the admitted dots: **156 are
  tip-family pixels that C never emitted and 968 are backbone-only gap sites** — the pool
  is the union of the two families' disagreement with C, and the greedy prices both.
* **A1 — hydrothermal conduit anchors (out-of-family, new signal), 652 px.** See §5.2.

Total **39,430 px** (C 37,654 + A2 1,124 + A1 652), values exactly {0, 1}.

### 5.2 A1: hydrothermal conduit anchors — the new, overlooked, free and official source

**Source.** Geothermal Data Registry submission 1391, *INGENIOUS Great Basin Regional
Dataset Compilation*, DOI [10.15121/1881483](https://doi.org/10.15121/1881483), landing
page <https://gdr.openei.org/submissions/1391>, Data.gov metadata
<https://catalog.data.gov/dataset/ingenious-great-basin-regional-dataset-compilation>
(CC BY 4.0 per the Data.gov record; the GDR asset-level terms were not independently
verified). Hash-pinned local mirror
`data/raw/external/gdr_wellspring_in_footprint.csv`, SHA-256
`122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea`, 27,092 records.
Its `dist_known_fault_px` column is label-derived and is **dropped on read**
(`conduit.LEAKY_COLUMNS`, asserted by
`tests/test_h55.py::test_conduit_reader_drops_the_label_derived_column`).

**Physical signature targeted.** A spring or well discharging at 75–296 °C requires a
heat source, deep meteoric circulation, and a *permeable upflow pathway*. In the
extensional northwestern Great Basin that pathway is a fault or fracture zone; the
region's producing systems (Beowawe, Brady's Hot Springs, Desert Peak, Stillwater,
McGinness Hills) are all structurally controlled. Silica and calcite
**geothermometers** go one step further than discharge temperature: they estimate the
*reservoir* temperature reached at depth, so a cool-discharge well with a 200 °C quartz
geothermometer still evidences deep fracture-controlled circulation. Measured in the
mirror: 8,718 records carry `temp_c` (Hot median 75.0 °C, p90 171.1 °C, max 296.5 °C);
1,247 carry a geothermometer (180 of them ≥ 150 °C, max 269.1 °C).

**Why it should catch faults MISSING from the USGS/INGENIOUS catalogue rather than ones
already in it.** Upflow through an already-mapped, already-eroded range-front scarp is
not what produces a thermal spring in a basin floor. Those springs appear where a
*buried* fault carries hot fluid up through alluvium — precisely the population an
expert would add to a catalogue and precisely the population the scoring mask leaves in.
Measured: of 12,570 distinct grid cells holding a well or spring, **219 (1.7 %) lie
inside the h19-5 corridor backbone** and **11,651 (92.7 %) are more than 200 m from the
public catalogue**. The layer is almost completely spatially disjoint from every surface
this repository has ever shipped.

**How it differs from anything already in the repository.**

| prior work | dataset | operator | outcome |
|---|---|---|---|
| H50-GDR | INGENIOUS **2 m soil-temperature probes** | repeat-visit residual persistence | 0.003923, failed |
| H52 | USGS 3DEP **1 m lidar** → 3 m scarp detector | step-height top-2,000 | 0.096409, failed gate |
| H50-B | GeoDAWN **radiometrics** | low-Th/K alteration × conflict corridors | 0.019135, negative |
| **H55 A1** | GDR **well & spring temperature + chemistry** (discharge T and silica/calcite reservoir T) | static physical tiering, DS-conflict vetoed, dart-thrown at 300 m | this candidate |

Different physical quantity (deep fluid temperature and reservoir geothermometry, not
shallow soil temperature, not topography, not gamma-ray spectrometry), different
operator, different source file.

**Tiering (pre-registered, `conduit.thermal_tier`, unit-tested).**

| tier | rule | records | distinct px |
|---:|---|---:|---:|
| 3 | `thermalclass == Hot`, **or** any geothermometer ≥ 150 °C | 2,035 | 961 |
| 2 | discharge ≥ 50 °C, **or** any geothermometer ≥ 100 °C | 1,752 | +195 |
| 1 | discharge ≥ 35 °C | 746 | +50 |
| 0 | everything else — including `Warm` (max 38.9 °C, effectively ambient) and `Cold` (≤ 20 °C), deliberately excluded as non-indicators | 22,559 | — |

Shipped tier floor: **≥ 2**. Eligibility: inside the survey footprint, > 200 m from the
public catalogue, not on the catalogue, > 300 m from every already-emitted dot
(non-redundant under the 300 m kernel), then dart-thrown at ≥ 300 m mutual separation
(deterministic, seed-free). 862 cells qualify; 652 survive dart-throwing (498 tier 3,
154 tier 2).

### 5.3 Dempster–Shafer: what it does here, and what it deliberately does not do

Frame `Θ = {F, ¬F}`. Shafer reliability discounts `α₁ = α₂ = 0.6` on the two families'
*kernel-coverage* favourability surfaces `b₁ = clip(max_credit_field(C))` and
`b₂ = clip(max_credit_field(h33d))`, zeroed outside the footprint:

```
m_i(F) = α_i b_i     m_i(¬F) = α_i (1 − b_i)     m_i(Θ) = 1 − α_i
K      = α₁α₂ (b₁ + b₂ − 2 b₁b₂)
Bel(F) = [f₁f₂ + f₁u₂ + u₁f₂]/(1 − K)     m₁₂(Θ) = u₁u₂/(1 − K)     Pl(F) = Bel + m₁₂(Θ)
```

Measured on the shipped raster: `Bel ∈ [0, 0.84]`, `Pl ∈ [0.16, 1.0]`,
`m(Θ) ∈ [0.16, 0.25]`, `K ∈ [0, 0.36]` with **14.70 % of the footprint in active
conflict** (`K > 0`). `m(Θ)` attains its maximum exactly on one-sided support — the
disagreement is carried forward as unassigned mass, not averaged away.

**Not the naive mean.** Pearson(Bel, ½(b₁+b₂)) = 0.996429, mean |Δ| = 0.013470,
max |Δ| = 0.160000, **13.71 %** of the footprint differs by more than 0.05, and the best
affine fit of Bel on the mean (slope 0.81841, intercept −0.00224) leaves a mean residual
of **0.005912** — so Bel is not an affine function of
the mean. The high rank correlation (Spearman 0.99994 on a 1-in-97 subsample) is
expected and is *not* evidence of equivalence: on this support both statistics are
monotone in the same coverage field. The affine residual and the difference
distribution are the informative tests, and they are recorded in
`evidence/build_h55_receipt_20261007.json → dempster_shafer.not_the_naive_mean`.

**Where DS actually enters the emission.** Two places, both as *structure*, not as a
blended value:

1. **A2's pool is the disagreement set.** The gap-closure candidates are drawn from
   `(B_elig ∪ tip) \ C` — 66,279 px of places where the two independently-built families
   are not already the same as C. The union's *coverage* is bought selectively; its
   *mass* is not. 156 of the 1,124 admitted dots are tip-family pixels.
2. **A1 is vetoed by maximal conflict.** A conduit anchor is discarded where
   `K ≥ 0.36` (the two families actively contradict) unless it is tier 3, in which case
   the third independent source arbitrates. On this build **0 of 862** anchors were
   vetoed — recorded rather than hidden, because a gate that never fires is not
   evidence.

The four graded layers ship separately, all-finite, all in [0, 1], under
`docs/downloads/diagnostics/`.

### 5.4 Risk accounting

`n_max` is solved from the pre-registered rule *"if every added pixel earns exactly zero
credit the live-equivalent score must not fall below 0.2778 − 0.0100"*, giving
**n_max = 3,568**. Used: 1,776.

| case | model DTI | live-equivalent | Δ vs 0.2778 |
|---|---:|---:|---:|
| **Floor** — all 1,776 additions earn zero | 0.26770 | **0.27273** | −0.00507 |
| A1 alone at zero credit (652 px of dead mass) | 0.27088 | 0.27591 | −0.00189 |
| A2 alone, priced by the model (1,124 px, no A1) | 0.27462 | 0.27965 | **+0.00185** |
| A2 priced + A1 at zero credit — **the shipped file** | 0.27275 | **0.27778** | −0.00002 |
| A1 at the break-even credit 0.0556 | 0.27465 | 0.27968 | +0.00188 |
| A1 at C's mean dot credit 0.1383 | 0.27747 | 0.28250 | +0.00470 |
| A1 at 0.2000 | 0.27958 | 0.28460 | +0.00680 |
| A1 at 0.3000 | 0.28299 | 0.28802 | +0.01022 |

Anchoring rule, applied uniformly: `live_equivalent = 0.2778 + (model_DTI(candidate) −
model_DTI(C))`. The model's constant bias on C (+0.0050) cancels, so **only model deltas
are ever added to an owner-reported live score**; the model's absolute level is never
quoted as a score.

The design intent is a **measurement**, not a gamble, and the arithmetic came out exact:
A2's modelled in-family gain is **+0.00185** and A1's denominator cost at zero credit is
**−0.00189**, a net of **−0.00003**. A returned live score materially above ≈ 0.2778 is
therefore direct evidence that hydrothermal conduits carry hidden-truth credit; a score at
≈ 0.2727 is evidence that they carry none and that the in-family pricing was also wrong.
Either outcome is worth more than the +0.0065 the entire in-family frontier can offer,
because the frontier is already mapped and the conduit hypothesis is not.

---

## 6. Validation actually performed

### 6.1 Blocked spatial holdout (`evidence/holdout_h55_spatial_20261007.json`)

Four fixed quadrants, core truth plus a 300 m scoring halo, official DTI parameters,
`scripts/run_spatial_holdout.py` unchanged.

| surface | catalogue proxy mean | SGMC-off proxy mean |
|---|---:|---:|
| dotted parent (C) | 0.006831 | 0.095491 |
| tip/step-over parent | 0.086820 | 0.095491 |
| arithmetic mean | 0.046406 | 0.088755 |
| prior α = 0.99 belief | 0.046207 | 0.088715 |
| prior union decision | 0.085538 | 0.096992 |
| **H55** | **0.007862** | **0.096286** |

Paired gates, stated in full:

| comparison | catalogue proxy Δ | folds | SGMC-off proxy Δ | folds |
|---|---:|:--:|---:|:--:|
| H55 vs dotted parent (C) | **+0.001031** | **4/4** | **+0.000795** | **4/4** |
| H55 vs tip/step-over parent | −0.078959 | 0/4 | **+0.000795** | **4/4** |
| H55 vs arithmetic mean | −0.038545 | 0/4 | **+0.007532** | **4/4** |
| H55 vs prior α = 0.99 belief | −0.038346 | 0/4 | **+0.007572** | **4/4** |
| H55 vs prior union decision | −0.077677 | 0/4 | −0.000705 | 1/4 |

The catalogue-proxy losses against the tip parent, the mean and the union are structural,
not a defect: those surfaces emit *on* catalogue-adjacent corridors, and the catalogue
proxy rewards exactly that. C is built by deleting everything within 200 m of the
catalogue, so it scores 0.0068 on a proxy whose truth is the catalogue — while scoring
0.2778 live. H55 inherits that. **The meaningful row is the first one: H55 beats its own
parent on both proxies in all four folds**, and it is the first candidate in this
repository to do so.

That last line is the proxy/live contradiction in one row: the SGMC proxy ranks the
naive union above H55, while the live-calibrated instrument prices the same union at
**−0.014** against C and the union's own ingredients scored 0.2778 and 0.2632 live.
Both cannot be right. §4.1 explains which one to distrust.

`slot_decision.cleared` remains **false** — the script is correct to say that a numeric
proxy pass is not private-label evidence.

### 6.2 Format and uniqueness (`evidence/h55_primary_format_audit_20261007.json`, `evidence/h55_uniqueness_audit_20261007.json`)

18/18 checks pass: single band; float32; EPSG:32611; 3,730 × 3,292; transform
`[100, 0, 243350, 0, −100, 4508550]`; **all 12,279,160 cells finite**; `nodata` unset;
whole-raster min 0.0 / max 1.0; value set exactly {0.0, 1.0}; zeros outside the
footprint; no positive outside the footprint; **no positive on the catalogue; no
positive within 200 m of the catalogue**; core preserved exactly (37,654/37,654);
no SHA-256 collision with any raster or recorded hash in the repository; not identical
to any prior candidate. Highest pixel-set Jaccard against any prior artifact is
**0.9550** (the untouched core), so the emitted set is new.

### 6.4 The repository's newer mass-neutral gate: H55 FAILS it, and what that means

While this session was running, a concurrent session merged `scripts/audit_candidate.py`
(protocol **GEMSDOE48-GATE-2**) and `docs/research/credit-density-audit-20261007.md`. That work
is independent of mine and reaches one conclusion I reproduce exactly from a different
direction: the SGMC off-catalogue proxy cannot certify a candidate, because **C + 18,000
uniform-random new cells scores 0.1189 mean4 on it, beating C (0.0956) and H49 (0.1010)**. A
ranking that a random control wins is not a ranking. That is §4.1 of this report, arrived at by
a control experiment instead of by inverting a live score — two instruments, one conclusion.

GATE-2 then replaces the unequal-mass comparison with two mass-neutral tests. Run against the H55
primary (`evidence/audit_gate2_h55_20261007.json`, incumbent `data/families/dotted_b2_prune_02778.tif`,
SHA-256 verified `c55bafc4…`):

```
verdict                                    FAIL_MASS_NEUTRAL
proxy mean4, own mass   incumbent 0.095607   candidate 0.096406
equal-mass mean4 (3 seeds)                 0.093593    delta vs incumbent  -0.002014
added cells                                1,776
marginal credit/cell, raw proxy            0.045030    (raw bar 0.019077)  -> passes
marginal credit/cell, DENSITY-MATCHED      0.010245    (live bar 0.05556)  -> FAILS, 0.18x
reasons: equal_mass_credit_density_below_incumbent (-0.00201)
         added_cells_below_live_break_even_bar (density-matched 0.0102 < 0.0556 per cell)
```

**This is a fail and it is reported as one.** If the density-matched figure transferred to the
live metric, H55 would score `T = 5,209.5 + 1,776 x 0.010245 = 5,227.7`, i.e.
**DTI 0.2736, −0.0042 against C**. That is the pessimistic end of the honest bracket.

Three things must be said about the test, none of which excuse the fail:

1. **It rests on the same proxy §4.1 contradicts.** Density-matching corrects the proxy's
   4.3× truth-density inflation; it does not correct the proxy's *identity*. An emission built
   directly on SGMC-off inverts to `T = 1,026` live where the backbone family reaches 5,209 at
   the same mass, so "credit against SGMC-off" and "credit against hidden truth" are not the same
   quantity and their ratio is unknown.
2. **Its additions test does not appear to discriminate between candidates.** Across every
   candidate in `credit-density-audit-20261007.md` plus this one, density-matched added-cell
   credit lands in **0.0049 – 0.0125** regardless of what the added cells are: 268,910 H50
   belief cells 0.0049, 222,693 hedge-v2 cells 0.0060, 96,673 h16-1 cells 0.0077, 83,477 h19-5
   cells 0.0050, 10,251 H49 cells 0.0125, 2,000 H52 lidar cells 0.0099, 1,776 H55 cells 0.0102.
   Curated geophysics, curated lidar, curated hydrothermal conduits and a graded belief field all
   score within a factor of 2.5 of each other and 4–11× below the bar. A test whose output is
   nearly independent of its input is measuring the proxy's density, not the candidate's quality.
3. **Its equal-mass test structurally penalises any additive candidate.** Uniformly subsampling
   a strict superset of C to C's mass discards ≈ 4.5 % of C's own dots at random and replaces them
   with the additions, so it must score below C on any proxy where C's dots are worth more than
   the additions. That is a real statement *about the proxy*, and it is not a statement about
   `TPw`, which cannot decrease under addition (§1c).

**Where the two instruments agree**, and this is the part that should drive the decision:
C is the best artifact in the repository (GATE-2's equal-mass column ranks it first at 0.095607,
ahead of H49 0.087211, H51 0.086641, h16-1 0.077045, h19-5 0.071706, random 0.067020 and
hedge-v2 0.058228, which is the same ordering my coverage statistic gives); no curated addition
measured so far clears the metric's own break-even bar on any proxy; and no slot is cleared.

**Where they disagree** is exactly the open question: the live-calibrated instrument prices A2's
in-family additions at +0.0019 because it is fitted to eight live scores, while GATE-2 prices all
1,776 additions at 0.0102/cell because it is fitted to a proxy that a live score contradicts by
5×. Neither can be settled offline. **That is the argument for spending the slot**: the returned
live score separates them, and §5.4's arithmetic was built so the separation is legible.

The honest bracket, combining both instruments, is therefore:

| basis | live-equivalent | Δ vs 0.2778 |
|---|---:|---:|
| GATE-2 density-matched credit (0.0102/cell) | **0.2736** | −0.0042 |
| this model, every addition earns zero | 0.2727 | −0.0051 |
| this model, A2 pays and A1 earns zero | **0.2778** | ±0.0000 |
| this model, A1 at break-even credit | 0.2797 | +0.0019 |
| this model, A1 at C's mean dot credit | 0.2825 | +0.0047 |
| this model, A1 at 0.30 credit | **0.2880** | +0.0102 |

### 6.3 Determinism

Two independent builds produced the same content id `055da9855353` and the same
primary SHA-256 `8f9a9d3d1ea2aed1c99e5ab5260aad9ceb10f4011c4b5a38791509261ddd284a`.
The dart-throw is seed-free (rank, then tier, then row-major index) and the greedy is
deterministic.

---

## 7. The `Predicted values must be in range [0, 1]` rejection — resolved

The portal check is a range test over the uploaded array. Two encodings circulate in
this project and both have owner-reported live scores:

| encoding | nodata | example | live |
|---|---|---|---|
| all-finite, exactly 0.0 outside | unset | `dotted_b2_prune_02778.tif` (C) | **0.2778** |
| NaN outside | `NaN` | `dotted_d2_8_02708.tif` (B) | 0.2708 |

A NaN cell makes `np.all((v >= 0) & (v <= 1))` evaluate to `False`, because every
comparison against NaN is false — which reproduces the reported error message exactly.
The organizers' own reference solution (`gems-prize-reference-solution`, notebook
cell 19) writes an **all-finite** float32 raster with `nodata` unset and no NaN
handling at all. The single best-scoring artifact in the family tree is also
all-finite.

**Resolution:** the H55 **primary download is all-finite with zeros outside**, and the
audit asserts `all_cells_finite`, `all_cells_in_range_0_1` and
`portal_range_error_immune` on the *re-read bytes*, not on the in-memory array. A
NaN-outside twin is shipped alongside for the sample-template convention and is
explicitly flagged `portal_range_error_immune: false`.

**Irregularity fixed:** `scripts/validate_submission.py` previously *required*
`nodata = NaN` and therefore rejected the encoding used by the 0.2778 live-best
artifact. It now takes `--encoding {auto,nan,zeros}` (default `auto`), accepts either,
reports which it found, and states the range-error exposure in the receipt.

---

## 8. Limitations

1. **Every live number here is OWNER-REPORT.** `|G|`, `rho`, all eight `T` values and
   the whole scenario band rest on scores pasted into the session brief. No organizer
   receipt links any file to any score.
2. **The instrument is within-family only.** Measured out-of-family transfer error is
   −38 % on the one available test. A1's contribution is a scenario band, not a
   prediction.
3. **A1 is unfalsified, and the repository's newest gate says its additions are worth 0.18× the
   break-even bar.** Nothing in this repository can estimate the credit of a hydrothermal conduit
   anchor against the *hidden* truth. GATE-2 estimates 0.0102 per added cell against a
   density-matched SGMC proxy; §6.4 gives three reasons that number should not be read as a live
   prediction, and one reason it might be. The physical case for A1 is strong; the measured case is
   contested, and the contest is the reason to submit it.
4. **The in-family headroom (+0.0065) is only 1.3× the instrument's resolution (±0.0049).**
   The claim "C is within 1.84 % of coverage-optimal and no emission from this field
   reaches 0.2888" is robust. The claim "a greedy re-emission beats C by 0.0065" is at the
   edge of what one submission can resolve.
5. **Proxy leakage.** C's construction used a whole-catalogue proximity prune, so
   quadrant-fold results are conditional and potentially leaky. Unchanged from prior
   sessions and unchanged here.
6. **Owner mirrors are not organizer-authenticated** and their reuse licences were not
   verified. Hash pinning establishes byte identity only.
7. **No slot is cleared by this document.** §6.1's numeric passes are proxy passes.

---

## 9. What would actually reach 0.3195, and what is now unblocked

The ceiling table (§3) says a higher score requires a corridor field whose *dense*
truth yield exceeds 6,041 at reasonable mass — i.e. a detector that sees more hidden
faults than the h19-5 field does. Three concrete moves, in order of expected value:

1. **Train on the official 19-band feature stack — now unblocked.** The stated blocker
   was data placement, not code: `training_features.tif` is login-walled on DrivenData.
   This session restored it **byte-identical to its manifest pin** (SHA-256
   `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`, 418,912,844
   bytes, 19 float32 bands) from five pinned shards with
   `python scripts/restore_h55_inputs.py --with-official-features`. It is 419 MB and is
   deliberately **not committed**. The 19 bands are: magnetic anomaly, reduced-to-pole,
   TMI horizontal gradient, geodetic second invariant of strain rate, isostatic gravity
   slope, tilt angle, geodetic shear rate, geodetic dilatation rate, TMI vertical
   gradient, distance to earthquake, isostatic gravity vertical gradient, detrended
   elevation, isostatic gravity anomaly, TMI, depth to basement, earthquake
   intensity/density, conductivity, isostatic gravity horizontal gradient, detrended
   elevation slope.
2. **Use the three bands nobody has used.** Measured lift of C's dots over the moat
   background, by band: TMI horizontal gradient 1.26, detrended elevation slope 1.16,
   **geodetic second invariant 1.05, geodetic shear rate 1.03, geodetic dilatation rate
   1.06, earthquake intensity 1.04**. The strain-rate and seismicity channels are
   effectively *unused information* in every artifact this project has shipped, and they
   are the channels most directly tied to *active* faulting. Caveat measured here: their
   100 m fields are diffuse, not linear (a multi-orientation line operator separates
   their top-2 % from background at only p90 0.0022 vs 0.0008), so they need a
   gradient/curvature transform or the 1 m DEM before they will yield corridors.
3. **Emit with the calibrated budget rule, not a fixed spacing.** Once a better field
   exists, `DTI = rho·Cov/(0.2 S + 0.8|G|)` gives the optimal mass and the optimal
   marginal-gain stopping point analytically — `scripts/calibrate_live_model.py` already
   traces that frontier. The 5-per-week budget should be spent on *field* variants, not on
   spacing variants: §3.1 shows spacing and mass are already within 0.4 % of optimal, so
   spacing sweeps cannot produce another 0.0065, let alone the +0.0417 needed for 0.3195.

A useful acceptance test for any new field `F`, requiring no slot: compute
`Cov(C; F_elig)` and `Cov(F_emission; F_elig)` and check that `F`'s *dense* emission
inverts to a `T` above the backbone's 6,813 under the same `|G|`. That needs one live
score for a dense `F` emission — the single most informative slot this project can spend,
because it re-calibrates `rho` for a second family and converts the instrument from
within-family to cross-family.

The single highest-information submission available is **H55 itself**, because it is the
only candidate whose live score would test a hypothesis the repository cannot test
offline.

---

## 10. Reproduce

```bash
python scripts/restore_h55_inputs.py                       # backbone, d1.5, SGMC-44k, conduit CSV (+2 external)
python scripts/restore_h55_inputs.py --with-official-features   # optional: 419 MB 19-band official stack
python scripts/calibrate_live_model.py                     # -> evidence/live_model_calibration_20261007.json
python scripts/build_submission_h55.py                     # -> docs/downloads/GEMSDOE48-H55-* + receipts
python scripts/audit_h55.py                                # -> evidence/h55_uniqueness_audit_20261007.json
python scripts/validate_submission.py docs/downloads/GEMSDOE48-H55-conduit-conflict-priced-20261007-055da9855353-zeros-outside.tif \
       --receipt evidence/h55_primary_format_audit_20261007.json
python scripts/run_spatial_holdout.py \
       --combined docs/downloads/GEMSDOE48-H55-conduit-conflict-priced-20261007-055da9855353-zeros-outside.tif \
       --candidate-name h55_conduit_conflict_priced \
       --output evidence/holdout_h55_spatial_20261007.json --allow-unpinned-sources
python -m pytest -q                                        # 158 passed, 3 skipped
```
