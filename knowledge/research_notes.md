# Research notes — GEMSDOE48

These are the notes behind the site. Every number here is reproducible from the repository;
nothing is quoted from memory. Sources are listed with the limit of what each one can support.

---

## 1. The metric, exactly

DrivenData competition 306 (DOE GEMS Prize), problem-description page 967, transcribed verbatim
by two independent sibling repositories:

```
k(d)  = max(1 - d / 300 m, 0)                                      300 m triangular kernel
TPw   = sum over truth pixels g of   max over prediction pixels x of  p(x) * k(d(x, g))
FPw   = sum over prediction pixels x of  p(x) * (1 - max over truth pixels g of k(d(x, g)))
FNw   = sum over truth pixels g of  (1 - max over prediction pixels x of p(x) * k(d(x, g)))
DTI   = TPw / (TPw + 0.2 * FPw + 0.8 * FNw + eps)
```

Grid: single band, float32, `EPSG:32611`, 100 m, values in [0, 1], 3292 columns × 3730 rows.
Independent official corroboration of the weights: the organizers' own reference solution trains
with `TverskyLoss(alpha=0.2, beta=0.8)`, i.e. the metric's α and β, read from the reference
notebook.

### Three exact consequences

**(a) The DTI-optimal submission is binary {0, 1}.** For one pixel of value `v` that is the argmax
of its truth pixel with realised kernel weight `k`,

```
d/dv [ (T0 + v k) / (D0 + 0.2 v) ]  =  (k D0 - 0.2 T0) / (D0 + 0.2 v)^2
```

which has the sign of `k - 0.2 · DTI` and is **independent of v**. Every pixel is pushed to 0 or 1.
A graded belief surface is therefore strictly worse than its own binarisation. This is why the
`-belief.tif`, `-mtheta.tif` and `-conflict.tif` layers are documented as diagnostics and
`-emission.tif` is the portal candidate.

**(b) Emit a dot iff its realised kernel weight exceeds `0.2 · DTI`.** Adding one unit of mass at a
pixel that becomes the argmax of its truth pixel changes `TPw` by `k`; the denominator changes by
exactly `0.2`, because `dS = +1` and `dM = +k` so `dFP = 1 - k`, and the β term cancels:
`0.2k + 0.2(1-k) - 0.8k = 0.2 - 0.8k`. The score rises iff `k / 0.2 > DTI`. At 0.2778 the bar is
**0.0556**.

**(c) In the removal regime the denominator collapses to `D = 0.2·S + 0.8·|G|`.** Two exact
identities make this exact rather than approximate: `FPw = S - M` and `FNw = |G| - TPw`, and for a
matched emission `M = TPw` to within 0.2 %. So

```
DTI = T / (0.2 (S - T) + 0.2 T + 0.8 |G|) = T / (0.2 S + 0.8 |G|)
```

and **in the regime where `T` is essentially a constant**,

```
dDTI/dS = -0.2 T / D^2        =>        budget = DTI * 0.2 * n_removed
```

That is the "hidden credit budget": each dot deleted buys `DTI · 0.2` of numerator that may be lost.

There is one correction to make to the first reading of identity (c). The formula
`dDTI/dn = (-0.2 T + 0.2 S dT/dS) / D^2` gives, at `DTI = 0.2708`, `ΔDTI ≈ +0.0105` per 3,891
dots removed. **The observed gain is +0.0108.** The agreement is close but not because `T` is
constant: it is because the dots removed earned almost exactly the `τ_live = 0.05416` bar. Both
readings agree at the anchor, which is the honest statement — the second-order term is not
negligible and the exact value must be computed per candidate.

### The live anchor

Owner-reported scores `[OWNER-REPORT]`: 0.2600 at 44,090 px, 0.2708 at 40,199 px.

| quantity | value |
|---|---|
| `dn_removed` | 3,891 |
| implied `TPw` from the small artifact | 4,913.77 |
| implied `TPw` from the large artifact | 4,920.14 |
| internal consistency | 0.129 % |
| implied credit per dot | 0.122236 |
| `τ_live = 0.2 × 0.2708` | 0.05416 |
| numerator budget for a 3,891-dot removal | 210.7 |

Calibrated hidden-truth size: **|G| = 12,632 px**, i.e. 0.245 % of the 5,167,373-pixel footprint
against the catalogue's 60,988 px (1.18 %). Supporting derivation: a spacing-5 blind lattice
against a 0.0904 baseline.

### Achievability of > 0.2778

`D = 17,636.4` at `S = 37,654`; `T = 4,899.4` at 0.2778. To reach the current leader's 0.3262 on
the same mass budget, `T` must reach `5,753.0` — **+853.6 weighted units, +17.4 % recall on the
hidden new-truth population at unchanged precision.** That is a detector problem, and the 12,632
hidden pixels are exactly what no file in this repository can see.

---

## 2. Why 0.2778 was the top score

The owner's live ladder is entirely a **removal** ladder. No addition has ever improved a live
score.

| artifact | emitted px | live | what changed |
|---|---|---|---|
| `gems25-dotted-h19-5-d2-8` | 44,090 | 0.2600 | spacing-tuned dotting of the H19-5 habitat field |
| `gems28-h27-4-r1-solo-d2-8` | 40,199 | 0.2708 | remove every dot within 100 m of the catalogue (B = 1) |
| `gems32-h33-2-b2` | 37,654 | **0.2778** | catalogue-flank buffer to B = 2 (200 m) |
| B = 3 — rejected | 35,483 | not shipped | safety 1.27 < 2.0; wins only 3 of 4 blocks |

Note what the rejection of B = 3 implies: **the 200–300 m band still contains credit.** Removing it
destroyed more than the budget allowed. That is the single most actionable lead this project has
produced and it is why `H48-A` is ranked first on the hypotheses page.

Supporting geometry, from `emit.coverage_profile`: 7.0 % of `dotted_02708` dots are more than 600 m
from their nearest neighbour. Because the kernel reach is 300 m, the midpoint of such a gap earns
**zero** credit while both bounding dots still cost 0.2 each. The delivered live scores are
consistent with this and are **not** reproduced by a uniform-density argument: the mission
published a 5–7 % uplift from spacing alone, which is a *tuning* result on a specific field.

---

## 3. Dempster–Shafer: what it adds and what it does not

Frame `Θ = {F, ¬F}` per pixel. With Shafer reliability discounts `a₁ = a₂ = 0.6`:

```
mᵢ({F}) = aᵢ bᵢ     mᵢ({¬F}) = aᵢ (1 - bᵢ)     mᵢ(Θ) = 1 - aᵢ        (sums to 1 by construction)
K       = m₁({F}) m₂({¬F}) + m₁({¬F}) m₂({F})   = a₁a₂ (b₁ + b₂ - 2 b₁b₂)
```

| `(b₁, b₂)` | `K` | `Bel(F)` | `m₁₂(Θ)` |
|---|---|---|---|
| (1, 1) | 0.0000 | **0.8400** | 0.1600 |
| (1, 0) | 0.3600 | **0.3750** | 0.2500 |
| (0.5, 0.5) | 0.1800 | 0.4024 | — |

`K` vanishes only at the two corners `(0,0)` and `(1,1)` and is maximal at `(1,0)` — verified
against the shipped raster on every pixel in `tests/test_submission.py`.

**Measured against the naive mean.** Pearson r = 0.991085, mean |Bel − mean| = 0.142255, 100 % of
the 48,394 union pixels differ by more than 0.05. Bel is not an affine function of the mean (best
affine fit misses by > 0.01). **But Spearman ρ = 1.000000**, because a union pixel has belief
exactly 1 in its own family, so both statistics are monotone functions of the other family's belief
alone on that support. The repository states this as a finding, not a defeat: what DS adds is the
calibrated belief, the conflict mass `K`, and the unassigned mass `m₁₂(Θ)` — none of which an
average has.

**Dempster's rule is not idempotent, and with a discount it deflates.** For `b₁ = b₂ = b` and
`a₁ = a₂ = a`: `Bel = [a²b² + 2ab(1-a)] / (1 - 2a²b(1-b))`, which is below `b` for every `b` in
(0, 1]. At `b = 1` it is 0.84; at `b = 0.5` it is 0.4024. Two equally-discounted identical opinions
move belief *towards* the frame.

**Implementation note.** Zadeh's (1984) paradox is exactly a consequence of Dempster's
normalisation, and Sentz & Ferson (2002, Sandia SAND2002-0835) document the alternatives. This is
why both diagnostic layers are shipped: `m₁₂(Θ)` is the post-normalisation unassigned belief and
`K` is the pre-normalisation conflict. Where `K = 1` the rule is undefined and the code falls back
to vacuous mass rather than dividing by zero.

---

## 4. Candidate hypotheses

Ranked by expected DTI improvement over implementation cost. Full detail and the promotion gate on
`docs/hypotheses.html`.

| rank | id | candidate | expected ΔDTI | cost | data obtainable from here? |
|---|---|---|---|---|---|
| 1 | H48-A | 200–300 m catalogue-companion band, curvature-gated | +0.003 to +0.010 | medium | yes, already materialised |
| 2 | H48-B | Curie-depth lateral gradient from the RTP/TMI spectral inversion | not quantified | medium | yes, already materialised |
| 3 | H48-C | Frangi vesselness on the K/Th and U/Th ratios | +0.002 to +0.008 | low | yes, same ScienceBase release |
| 4 | H48-D | χ-anomaly and knickpoint clustering on the 1 m DEM | unknown; potentially the largest | high | **NOT verified — every host returns HTTP 000** |
| 5 | H48-E | strike-coherent skeleton of the upward-continued TMI | +0.001 to +0.004 | low | yes, already materialised |

**H48-A is ranked first on measured evidence, not on theory.** The B = 2 → B = 3 live pair says the
200–300 m catalogue-companion band still carries credit; the staff clarification says a new-truth
pixel *can* lie within 300 m of a known trace and names "corrections or modifications to existing
fault traces". The expected gain uses the marginal-value rule: `ΔDTI ≈ (c - 0.2·DTI)·n / D`. At
`c = 0.07` and `n = 4,000`, `ΔDTI = +0.0031`; at `c = 0.10`, `ΔDTI = +0.0095`.

**The promotion gate a candidate must clear before a slot is spent** — all four, on the spatially
blocked holdout:

1. mass ≤ the 37,654 px of the live-best artifact;
2. ≥ 99 % of the live-best artifact's weighted credit retained on the SGMC off-catalogue layer
   (the only non-catalogue truth available);
3. live-anchored safety factor ≥ 2.0 (budget ÷ measured credit destroyed);
4. the improvement reproduces in ≥ 3 of 4 spatial blocks.

**And a warning about the gate itself.** Two of those four are degenerate on this base and are
recorded as such in `evidence/selection.json → gate_caveat`: the catalogue term divides by the
base's own catalogue credit (378.0, essentially zero by construction) and the safety term saturates
at its 99.0 ceiling whenever the measured SGMC credit loss is 0.0, so it cannot fail.
`scripts/run_selection.py` therefore promotes nothing. That is a defect in the instrument, not a
result.

---

## 5. Sources, and the limit of each

| id | source | verified statement | limit |
|---|---|---|---|
| DD-SPEC | organizer problem description | float32 single band, UTM 11N, 100 m, [0,1]; 300 m triangular DTI, α = 0.2, β = 0.8 | host unreachable from this sandbox (HTTP 000); read from sibling transcriptions |
| REF-LOSS | organizers' reference solution | cell 16 sets `alpha = 0.2`, `beta = 0.8` — the metric's own weights | `data/` empty; training data not distributed with it |
| DD-MASK | organizer staff, 2026-09-16 / 09-21 | the mask is pixel-exact and identical to the training labels; a new-truth pixel CAN lie within 300 m of a known trace | recorded transcription |
| DD-POOL | organizer staff, 2026-10-01 | public and private scores pool all subset pixels into one Tversky index | recorded transcription |
| DD-TEST | organizer staff | fault types and source coverage are not disclosed | do not assume Quaternary scarps or geothermal conduits |
| DD-LB | leaderboard snapshot, 2026-10-02 | #1 nchuzhoy 0.3262; #2 kinghorton42 0.3222; #3 DARD 0.3195 | stale; and the DrivenData ToU prohibits automatic access |
| USGS-GD | USGS GeoDAWN release, DOI 10.5066/P93LGLVQ | four blocks N→S: Winnemucca, Fallon, Hawthorne, Tonopah; base stations given in UTM 11N | block boundaries not published |
| USGS-3DEP | USGS 3D Elevation Program | the free official source behind the organizer `1m_DEM_links.csv` | obtainability NOT verified — every 3DEP host returns HTTP 000 here |
| SGMC | USGS State Geologic Map Compilation | independent non-catalogue fault layer (`derived_sgmc_faults_100m.tif`, 83,593 px) | the SGMC-only arm scored 0.0512 live, near random |
| INGENIOUS | gdr.openei.org/submissions/1391 | the competition's own contextual catalogue | superseded by the organizer labels in the data drop |
| MRDS | USGS Mineral Resources Data System | — | **excluded**: updates ceased in 2011 |
| BLM-CLOSED | BLM closed-case spatial data | 702,794 case IDs → 197,346 geometries, 20 km seed buffer | used for the footprint-adjacency screen |
| PFA-2015 / PFA-2020 | USGS play fairway analyses, OSTI 1724082 / 1724109 | regional geothermal favourability | regional scale, not 100 m |

**Blocked from this sandbox (all HTTP 000):** `prd-tnm.s3.amazonaws.com`,
`earthexplorer.usgs.gov`, `portal.opentopography.org`, `earthquake.usgs.gov`, and every other
science-data host tested. **Deliberately not fetched:** anything under `drivendata.org` — the terms
of use prohibit robots and automatic access, and a past push-triggered Actions run in this project
did fetch the leaderboard.
