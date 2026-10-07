> **CORRECTION (2026-10-07; read first):** This archive's H55/H54 live-model inversion uses `FPw = S - TPw`, generally false under the official metric. Its inferred truth masses, fitted `rho`, 0.2843 “ceiling,” live-equivalent scenarios, per-cell credit bars, and slot decisions are withdrawn as private-label estimates or promotion criteria. The model table and conclusions below are historical calculations, not score predictions. Raw raster facts and direct public-proxy results remain for audit only. A separate coordinate-wise proof that some binary maximizer exists does not reinstate any H55 forecast or fixed threshold. See the [metric-identity erratum](metric-identity-erratum-20261007.md), [corrected 0.2778 note](why-02778-and-ceiling-20261007.md), and [current H56B-NF review](h56b-review-erratum-20261007.md). **No weekly slot is cleared.**

# H55 — historical artifact and withdrawn live-model analysis

Session date: **2026-10-07 UTC**. Candidate label: **H55**. Everything below is
recomputed from files in this repository by `scripts/calibrate_live_model.py`,
`scripts/build_submission_h55.py`, `scripts/audit_h55.py` and
`scripts/run_spatial_holdout.py`; receipts are named inline. No number here is
transcribed from memory, and **no organizer score exists for any file in this
repository**.

---

## 0. Summary

| question | corrected answer |
|---|---|
| Why may the owner-reported 0.2778 have scored well? | The 300 m tapered metric and catalogue-flank pruning make a plausible mechanism, not a proven cause; no organizer receipt ties 0.2778 to the local B2 bytes. See the [corrected note](why-02778-and-ceiling-20261007.md). |
| Can a local file be predicted to exceed 0.2778 or 0.3195? | No numerical prediction is supportable from the available evidence. A higher score is possible in principle; the historical ceiling and reachability calculations are invalid. |
| What did H55 measure? | It built a local research TIFF and recorded direct public-proxy results. These are reproducible diagnostics against public maps, not private-label validation or organizer score. See the linked build and holdout receipts in the historical sections below. |
| Was H55 slot-cleared by GATE-2? | No. The old receipt records a failure under a mass-neutral/density-matched interpretation whose threshold depended on the withdrawn model; that interpretation is not a valid promotion gate. |
| Is there an organizer score for H55 or the B2 input? | No. The local producer labels the B2 input `UNSCORED`; no organizer receipt links exact local bytes to 0.2778. |

---

## 1. Official metric and corrected implications

Transcribed by two independent sibling repositories from the organizer's problem description and corroborated by the organizers' reference solution:

```
k(d)  = max(1 - d/300 m, 0)
TPw   = sum_g max_x p(x) k(d(x,g))
Q     = sum_x p(x) max_g k(d(x,g))
FPw   = S - Q,  where S = sum_x p(x)
FNw   = |G| - TPw
DTI   = TPw / (TPw + 0.2 FPw + 0.8 FNw)
```

The two maxima use different axes, so `Q` and `TPw` are generally unequal. The former H55 inversion substituted `S−TPw` for `FPw`, invalidating the inferred hidden-truth mass, fitted reliability, ceiling, score bands, and universal break-even claims. Do not use this archived model to forecast or rank candidates.

**Binary-valued optimum (separate mathematical result):** for the official weights, holding all other pixels fixed, the score as a function of one prediction value has a derivative whose sign is constant between breakpoints and can only move from negative to positive at breakpoints. Thus replacing coordinates by their better endpoint yields a binary `{0,1}` raster with no lower DTI, under nonempty truth and `[0,1]` predictions. This establishes that a binary maximizer exists; it does **not** show that thresholding a particular graded D-S field at a fixed value improves it. The full derivation and small-raster test are in the [metric-identity erratum](metric-identity-erratum-20261007.md) and `tests/test_metric_main.py`.

The former per-pixel `0.2×DTI` break-even rule is valid only in a restricted one-pixel setup with specified TP/FP/FN changes; it is not a universal threshold for arbitrary candidate additions. Adding a prediction can increase both truth-centred `TPw` and prediction-centred false-positive cost. Direct proxy scores also cannot prove transfer to unknown private faults.

---

## 2. Historical live-score forward model (withdrawn; retained to reproduce prior calculations)

> The remainder of this section uses owner-reported scores and additional model assumptions. Its inferred `|G|`, `rho`, `TPw`, scenario values, and cross-family conclusions are not identified by the official metric. Do not quote them as measurements, predictions, or bounds.

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

### 2.5 Out-of-family transfer — not identified

The registry contains an owner-reported **0.0512** association for a proxy-built SGMC-off-catalogue emission. No organizer receipt links that value to exact local TIFF bytes. The former conversion to `T=1,026`, fitted out-of-family `rho`, 38% transfer error, and bias-direction claims used the withdrawn identity. They are not evidence for a transfer factor or expected score. This limits any claim about H55's conduit additions; it does not show they help or hurt. The raw owner report is retained in `registry/live_scores.json` for provenance only.

---

## 3. Historical ceiling / reachability calculation — retracted

> Every score conversion and “unreachable” conclusion in this section depends on the invalid `FPw=S−TPw` substitution. Preserve the receipts as a record of prior calculations only; they are not private-label bounds or candidate-ranking evidence.

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

### 3.3 Historical family-fusion interpretation — no impossibility result

The former live-equivalent union score, inferred parent truth masses, and conclusion that “every fusion was doomed” are retracted. Pixelwise support unions and parent-overlap statistics are reproducible raster facts, but they do not establish private-label DTI or rule out a beneficial fusion. The coordinate-wise binary-maximizer result in the [metric-identity erratum](metric-identity-erratum-20261007.md) proves only that a binary maximizer exists; it does not justify fixed-thresholding a graded fusion or rank D-S against other methods. For the current post-hoc H56B-NF artifact, consult its direct matched public-proxy holdout, which is negative against H49; this is not a global impossibility claim.

## 4. Public-proxy measurements and owner reports — not a hidden-truth instrument

### 4.1 SGMC off-catalogue proxy

The blocked SGMC-off-catalogue layer is a public-map proxy. Its direct DTI values can compare candidate rasters under a fixed protocol, but do not identify private labels. `registry/live_scores.json` separately includes an owner-reported 0.0512 association for a proxy-built emission; no organizer receipt links exact local bytes to that score. The earlier inversion of 0.0512 to `T=1,026`, and any inferred score gap or claim that SGMC “systematically selects bad live candidates,” are withdrawn. Treat the mismatch as a reason to state transfer limits, not as proxy calibration.

### 4.2 Catalogue coverage ratios

The following ratios are public-catalogue measurements from the archived audit. They are not estimates of private-truth yield, and do not validate the former ≥2× catalogue-lift rule:

| field | positive pixels | catalogue coverage per emitted pixel |
|---|---:|---:|
| h19-5 backbone | 121,131 | 0.1007 |
| SGMC faults | 83,593 | 0.1418 |
| GDR wells/springs, all | 12,570 | 0.1023 |
| GDR wells/springs, Hot | 929 | 0.1897 |
| INGENIOUS Quaternary fault centroids | 1,125 | 0.3696 |

These are descriptions of coverage against public catalogue pixels only. Do not infer that higher/lower values predict private scores or candidate utility. H52/H54/H55 GATE-2 interpretations and any “live-validated screen” language are withdrawn; see the [historical credit-density audit correction](credit-density-audit-20261007.md), [irregularities ledger](../irregularities.md), and [metric-identity erratum](metric-identity-erratum-20261007.md).

---

## 5. H55 — historical artifact construction (score interpretations withdrawn)

> The following pins, exact pixel counts, source descriptions, and D-S operations document what was built. Any model-priced admission rule, expected score, claimed new-signal benefit, or slot rationale is withdrawn; this build is not recommended for submission.

### 5.1 Construction (historical recipe; not a current recommendation)

`X = C ∪ A1 ∪ A2`

* **C** — a 37,654 px dotted raster associated by the owner with the 0.2778 row. The
  producer marks the exact local B2 bytes `UNSCORED`; there is no organizer file-to-score
  receipt. This H55 build preserves the C pixel mask exactly, verified by
  `scripts/audit_h55.py` (`core_preserved_exactly: true`, intersection 37,654/37,654).
  That fact does not identify the truth credit already present in C.
* **A2 — historical conflict/gap selection, 1,124 px.** The two family rasters overlap
  and disagree as recorded by the build receipt. The builder selected candidates from
  `(B_elig ∪ tip) \ C` with a greedy coverage heuristic. The old price/bar, `rho`, and
  model-derived candidate score are withdrawn; the selected pixel count and provenance
  remain reproducible build facts. The 1,124 selected cells comprise 156 tip-family
  pixels not in C and 968 other gap sites, according to the historical receipt.
* **A1 — hydrothermal conduit anchors, 652 px.** This is a new input-layer experiment,
  not a validated “new signal” or evidence of private-label credit. See §5.2 and the
  source/coverage caveats below.

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
m(Θ) is residual ignorance under the selected BPAs, not a direct disagreement measure; standard Dempster normalization removes raw conflict K, which is reported separately.

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

### 5.4 Historical risk-budget calculation — withdrawn

The original H55 builder recorded a 39,430-pixel binary output with 1,776 additions beyond the preserved C mask. Its `n_max`, floor, break-even scenarios, live-equivalent table, and “measurement”/slot rationale were computed from the withdrawn hidden-truth model. Do not use the old `0.2727–0.2880` table or `0.2778` cancellation claim as forecast, lower bound, score attribution, or experiment justification. The original [`build receipt`](../../evidence/build_h55_receipt_20261007.json) and [`GATE-2 receipt`](../../evidence/audit_gate2_h55_20261007.json) are preserved for reproducibility; see the [metric-identity erratum](metric-identity-erratum-20261007.md).

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

These are direct computations against the historical public-proxy rasters under the stated four-quadrant protocol. They show how this H55 surface compared with its selected parents on those proxies; they do not establish private-label ranking or the organizer score. The owner-reported score associations belong to separate artifacts and have no verified exact-byte receipt, so they cannot resolve transfer from either proxy to hidden labels. The historical `slot_decision.cleared=false` remains correct; no weekly slot is cleared.

### 6.2 Format and uniqueness (`evidence/h55_primary_format_audit_20261007.json`, `evidence/h55_uniqueness_audit_20261007.json`)

18/18 checks pass: single band; float32; EPSG:32611; 3,730 × 3,292; transform
`[100, 0, 243350, 0, −100, 4508550]`; **all 12,279,160 cells finite**; `nodata` unset;
whole-raster min 0.0 / max 1.0; value set exactly {0.0, 1.0}; zeros outside the
footprint; no positive outside the footprint; **no positive on the catalogue; no
positive within 200 m of the catalogue**; core preserved exactly (37,654/37,654);
no SHA-256 collision with any raster or recorded hash in the repository; not identical
to any prior candidate. Highest pixel-set Jaccard against any prior artifact is
**0.9550** (the untouched core), so the emitted set is new.

### 6.3 Determinism

Two independent builds produced the same content id `055da9855353` and the same
primary SHA-256 `8f9a9d3d1ea2aed1c99e5ab5260aad9ceb10f4011c4b5a38791509261ddd284a`.
The dart-throw is seed-free (rank, then tier, then row-major index) and the greedy is
deterministic.

### 6.4 Historical GATE-2 receipt — not a validated promotion test

The historical [`audit_gate2_h55_20261007.json`](../../evidence/audit_gate2_h55_20261007.json) records `FAIL_MASS_NEUTRAL` and its underlying public-proxy computations. Its density-matched proxy was thinned to an assumed hidden-truth count inferred with the withdrawn `FPw=S−TPw` model, and its 0.0556 comparison was treated as a universal break-even bar. Those threshold/gate interpretations are withdrawn. Equal-mass and own-mass DTI values in the receipt remain public-proxy diagnostics only; they do not establish private-label performance or a score bound.

The original roll-up, per-candidate values, and builder are preserved for provenance. See the corrected [credit-density audit](credit-density-audit-20261007.md), [metric-identity erratum](metric-identity-erratum-20261007.md), and the [current H56B-NF matched holdout](h56b-review-erratum-20261007.md). No weekly slot is cleared.

---

## 7. H55 local range audit — not portal acceptance

The archived H55 primary TIFF is all-finite float32 with values in `[0,1]`, zero outside the footprint, and `nodata` unset; its local receipt verifies those byte-level facts. This makes it immune to a simple whole-array finite/range predicate, but **does not establish organizer acceptance**. The official problem page describes null/NaN outside the data bounds, so the zero-outside encoding remains an acceptance ambiguity. The repository does not have an organizer response tied to this TIFF, and no portal rejection cause is established by the local checks. H55 is not recommended for submission.

A NaN fails a naïve `(v >= 0) & (v <= 1)` all-pixel predicate in ordinary NumPy, so it is one plausible reason for a range error—but this is not evidence of the actual portal implementation or the cause of any reported rejection. The current H56B-NF file uses NaN outside and its receipt explicitly reports `portal_range_error_immune: false`; see the [format-validation receipt](../../evidence/h56b_noflank_format_validation_20261007.json). Do not substitute H55's historical encoding or describe it as accepted.

---

## 8. Limitations and correction summary

1. **No organizer score exists for H55 or any local file.** Registry values are owner-reported; no organizer receipt links exact TIFF bytes to a score. The local B2 producer text says `UNSCORED`.
2. **Private labels are unavailable.** H55's inferred `|G|`, `TPw`, `rho`, recall, live-equivalent scores, and scenario bands are withdrawn under the metric-identity erratum.
3. **Public-proxy transfer is unresolved.** Direct catalogue/SGMC DTI results are protocol-specific and cannot identify which proxy better represents private labels. The H55 holdout surfaces were not reconstructed inside every fold, leaving a leakage/transfer limitation.
4. **H55 is not slot-cleared or recommended.** Its local build/format/uniqueness checks do not establish organizer acceptance. The old GATE-2 threshold is not a valid private-label promotion rule.
5. **Input provenance is limited.** Several inputs are owner mirrors; hash pinning establishes byte identity, not organizer provenance, licence, or permission to reuse. The GDR asset-level terms were not independently verified.
6. **A binary maximizer exists, but no fixed threshold is justified.** The coordinate-wise proof does not show that thresholding H55's or H56B-NF's graded raster improves DTI. See §1 and the [metric-identity erratum](metric-identity-erratum-20261007.md).

---

## 9. Current research direction — not a score/reachability plan

The former H55 recommendations to train on particular bands, infer dense hidden-truth yield, tune a model-priced budget, or spend a slot on H55 are not supported. The historical source and build facts remain in this archive; they do not establish score potential or organizer acceptance.

The current five previously untried hypotheses are H57-A through H57-E, each documented with source availability and limitations, expected DTI impact, prior-art distinction, and cost in the [H57 slate](h57-hypothesis-slate-20261007.md) and [machine-readable record](../../evidence/hypothesis_slate_h57_20261007.json). Before implementation: verify the source payload, units, masks, coverage and licence; freeze the physical operator and comparable spatial blocks; then test against H49 using the same public-proxy protocol. Do not spend a weekly slot unless a candidate beats the comparable blocked best. No proxy result is a private-label prediction, and no current result supports a numerical claim above 0.2778 or 0.3195.

---

## 10. Audit references

This report remains as a historical audit record; its original model outputs are not endorsed. Reproduction and interpretation should start from the corrected sources:

- [Metric-identity erratum and executable counterexample](metric-identity-erratum-20261007.md)
- [Corrected explanation of the owner-reported 0.2778](why-02778-and-ceiling-20261007.md)
- [Historical H55 build receipt](../../evidence/build_h55_receipt_20261007.json)
- [Historical local format audit](../../evidence/h55_primary_format_audit_20261007.json)
- [Historical public-proxy holdout](../../evidence/holdout_h55_spatial_20261007.json)
- [Historical GATE-2 receipt (threshold interpretation withdrawn)](../../evidence/audit_gate2_h55_20261007.json)
- [Current H56B-NF review and matched holdout](h56b-review-erratum-20261007.md)

The H55 builder (`scripts/build_submission_h55.py`) and calibration tools are preserved for audit; do not treat their score outputs as valid predictions. Current tests should run in the repository's `.venv` with `python -m pytest -q`.
