# H56 hypothesis slate — five new candidates, frozen 2026-10-07, top two already measured and failed

Machine-readable twin: [`evidence/hypothesis_slate_h56_20261007.json`](../../evidence/hypothesis_slate_h56_20261007.json).
Measured screen and battery: [`evidence/h56_research_battery_20261007.json`](../../evidence/h56_research_battery_20261007.json)
and [`evidence/h56_band_screen_20261007.json`](../../evidence/h56_band_screen_20261007.json).

Each entry names the layers, the physical signature and its transform, why it should catch a
fault **missing** from the USGS/INGENIOUS catalogue, how it differs from everything in this
repository, its data-obtainability status, and its expected ΔDTI against implementation cost.

## What this session measured before ranking (so the ranking is not opinion)

The 419 MB official 19-band GeoDAWN features raster was restored byte-identical from the
hash-pinned mirror (SHA-256 `4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5`,
manifest `registry/data_manifest_gemsdoe32.json`) and screened band by band against the
incumbent C (37,654 dots) over the >200 m catalogue moat:

| band | description (official tag) | lift | AUC |
|---:|---|---:|---:|
| 3 | TMI horizontal gradient | 1.264 | 0.576 |
| 19 | detrended elevation slope | 1.160 | **0.660** |
| 12 | detrended elevation | −0.463 | 0.560 |
| 13 | isostatic gravity anomaly | 0.773 | 0.549 |
| 10 | distance to earthquake | 1.441 | 0.532 |
| 8 | geodetic dilatation rate | 1.095 | 0.535 |
| 4 | geodetic second invariant | 1.082 | 0.529 |
| 7 | geodetic shear rate | 1.081 | 0.519 |
| 16 | earthquake intensity | 1.082 | 0.522 |
| 14 | total magnetic intensity | 0.954 | 0.509 |
| 17 | conductivity | 0.981 | 0.474 |
| 15 | depth to basement | 0.751 | 0.469 |
| 6 | tilt angle / total curvature | 0.906 | 0.373 |

Reproductions of the H55 session's independent measurements validate the pipeline line by
line: band-3 lift 1.264 vs their 1.26; band-19 1.160 vs 1.16; band-10 1.441 vs 1.44;
band-4/7/8 1.08 vs 1.03–1.06; C's mean basement depth 402.4 m vs moat 534.9 m (their
402 m vs 535 m); the live-model projection of C recomputed at **0.2728** with
`Cov(X;B_elig) = 75,206.82` identical to the calibration to 14 decimal places.

Two candidate fields were then **built and evaluated offline** (this is the
"validate before spending a slot" step the brief requires):

* **H55-B strain-rate ridge field (previous session's Priority 3, implemented here):**
  structure-tensor coherence > p95 on |second invariant|+|shear rate| gives 258,369 px
  (5 % of the footprint) of which only 1,886 of C's dots (5.0 %) lie inside — genuinely
  unused geometry. But Poisson dots drawn from it score **live-model projection 0.0152**
  standalone and drag C+field to 0.2152 (< 0.2728): ≈ 0.017 credit per dot against the
  0.0556 break-even bar. **Offline FAIL.** The slate's formal kill criterion (a live dense
  emission inverted under calibrated |G|) remains the only way to overturn this, and the
  projection says the slot is not worth spending.
* **H56-A DEMGLOW (new, below):** the primary rung z ≤ −1.5 & HG ≥ p75 yields only
  5,944 conjunction pixels → 1,991 Poisson dots. Standalone projection 0.0028 vs the
  same-mass random control 0.0023 (within noise of it); C+field 0.2673 < 0.2728.
  **Offline FAIL.** Demagnetisation lows at this conjunction definition are too sparse
  and not credit-bearing enough under the family model.

Both failures are the system working: no weekly slot was spent, and the instruments that
failed them are the ones calibrated against eight live scores.

---

## Rank 1 — H56-F: absence-driven Dempster pruning ladder (the one untested DS direction)

| field | value |
|---|---|
| **Layers** | `data/families/dotted_b2_prune_02778.tif` (C, live 0.2778) × `data/families/tip_stepover_r30_02632.tif` (H33-D, live 0.2632) — the two pinned family surfaces this session already combines |
| **Physical signature and transform** | Not a new geophysical transform — the evidence-theoretic dual of everything tried so far. Every fusion in this repository has been **additive**; Dempster's rule also defines **removal**. Where C emits a dot and the tip family's kernel support and backbone-absence evidence say "no fault", the combined belief Bel(F) at that dot drops. Emit a ladder of pruned surfaces: keep C's dots with combined belief ≥ τ for τ ∈ {0.90, 0.95, 0.99}, exactly as rungs A→B→C pruned catalogue flanks. |
| **Why it catches MISSING truth (or rather, stops paying for absent truth)** | The live ladder already proved the mechanism: deleting ~3,900 dots that carried ~0 kernel credit raised the score +0.0108 (0.2600→0.2708) with no new geology. The organizer masks catalogue pixels, so predictions there are pure 0.2-weight false positives; any *other* dot population whose realised kernel weight is below 0.2·DTI = 0.0556 is equally worthless. Tip-family disagreement is the only independent, already-downloaded estimate of which C-dots those are. |
| **Difference from anything in the repository** | H49/H53/H54/H55 and this session's H56 all ADD or REWEIGHT. No artifact has ever removed C dots using the other family's evidence. The H55 slate explicitly left 200–300 m flank pruning as "owner decision, not recommendation" — this is a different, evidence-weighted removal rule with a ladder, not a spatial band. |
| **Data obtainable?** | YES — both parents are pinned and local; builder cost is one script reusing `scripts/build_submission_h56_belief.py`'s BPA. |
| **Expected ΔDTI / cost** | If even half of the 6,040 C-only dots are sub-bar, model value ≈ +0.002 to +0.005; if they carry average credit (0.138), removal costs ≈ −0.003. **The widest two-sided bet available inside the family.** Cost low; needs ONE live slot to resolve — the removal ladder is exactly the experiment shape that produced the family's best three scores. |
| **Kill criterion (pre-registered)** | Do not prune below τ = 0.90 in one rung; if the first rung returns below 0.2727 the hypothesis is dead (removals were credit-bearing) and the ladder stops. |

## Rank 2 — H56-C: 3 m DEM channel-knickpoint clusters

| field | value |
|---|---|
| **Layers** | USGS 3DEP 1 m DEM (the same official source already fetched for H52/H54: 706 of 716 zone-11 tiles via `.github/workflows/dem-region-scarp.yml`), block-averaged to 3 m |
| **Physical signature and transform** | Stream-network extraction on the 3 m mosaic, then knickpoint detection as local maxima of the profile second derivative exceeding a 3σ noise floor, then RANSAC line-clustering of knickpoints into azimuth-coherent sets (≥ 4 knickpoints within a 300 m corridor of a common azimuth). Emit one Poisson dot per cluster centroid. |
| **Why it catches a MISSING fault** | A young fault perturbing base level leaves knickpoints in channel long-profiles **upstream of any mappable scarp** — including faults mantled by alluvium that show no trace at the surface and are therefore absent from the USGS Quaternary catalogue and the INGENIOUS inventory. Scarps (H52/H54) look at hillslopes; knickpoints look inside the drainage network — a disjoint observation space. |
| **Difference from anything in the repository** | H52/H54 used a step-height detector on hillslope cells; no channel-profile operator exists in `src/`. The H52 lesson (terrain class beat step height) is incorporated: clusters are the estimator, not individual detections. |
| **Data obtainable?** | YES — proven: the same workflow already downloaded and mosaicked 706 tiles on hosted runners (sandbox cannot reach USGS; runners can), compact products committed back. |
| **Expected ΔDTI / cost** | Unknown but structurally similar to the lidar family that produced 0.0921–0.1294 scores from scarps; upside +0.002 to +0.010 if knickpoint clusters carry credit. Cost **medium-high**: one runner mosaic + one new detector module (~1 session). |

## Rank 3 — H56-D: conduit stepping-stone trace propagation

| field | value |
|---|---|
| **Layers** | `data/raw/external/gdr_wellspring_in_footprint.csv` (GDR/INGENIOUS wells and springs, local and hash-pinned) × official band 3 (TMI horizontal gradient) |
| **Physical signature and transform** | Tier-≥2 conduit anchors (1,005 off-catalogue, measured this session) paired within 15 cells; each pair joined by the straight segment, scored by mean band-3 HG along it (anchors sit at HG 28.77 vs moat background 26.33, a 1.09× lift — weak); emit dots along the top segments at Poisson spacing, ≥ 300 m from existing C dots. |
| **Why it catches a MISSING fault** | Hydrothermal discharge is point evidence of a fault's *existence*; the fault *trace* connecting two conduits is what the metric's 300 m kernel actually rewards. H55-A dart-threw anchors; this proposes the connective tissue between them, most of which is unmapped because hot-spring alignments are not in the surface-trace catalogue. |
| **Difference from anything in the repository** | H55-A emitted isolated anchors (modelled ≈ −0.00003 net); no session has connected anchors into traces. |
| **Data obtainable?** | YES — all inputs local. |
| **Expected ΔDTI / cost** | Small in both directions (mass ≤ ~500 dots): worst ≈ −0.001, upside ≈ +0.002 if conduit pairs straddle hidden faults. The measured 1.09× HG lift at anchors is weak, so rank 3. Cost low. Best spent only after Rank 1's live result says whether conduit evidence carries credit at all. |

## Rank 4 — H56-B: radiometric K-residual alteration halos

| field | value |
|---|---|
| **Layers** | `data/source_mirrors/geodawn_rad_u8.tif` (GeoDAWN K/Th/U/TC, uint8 1st–99th percentile quantisation, band order K, Th, U, TC per the mirror's own metadata; source DOI [10.5066/P93LGLVQ](https://doi.org/10.5066/P93LGLVQ)) |
| **Physical signature and transform** | Robust regression K ~ Th (lithology control; both quantised), residual field R_K; anomaly = robust z of R_K; emit where z ≥ 2 AND band-3 HG ridge ≥ p75 (conjunction with structure). |
| **Why it catches a MISSING fault** | Potassic metasomatism along upflow zones persists under cover long after surface expression erodes; the catalogue is a surface-trace compilation. K enrichment *at constant Th* is a chemistry signal no geomorphic layer sees. |
| **Difference from anything in the repository** | H50-B used the Th/K *ratio* inside DS conflict corridors (failed its gate); GEMSDOE46 used scarp∩radiometric coincidence; H53-RadEdge used radiometric *edges*. A lithology-regressed K **residual** is a different operator with a different null. |
| **Data obtainable?** | YES — mirror already local and hash-pinned. Caveat: uint8 quantisation coarsens the regression; flagged as an implementation risk. |
| **Expected ΔDTI / cost** | Small-to-moderate: alteration halos are diffuse; expected +0.000 to +0.003. Cost low. |

## Rank 5 — H56-E: cover-gated additions (basement-depth prior)

| field | value |
|---|---|
| **Layers** | official band 15 (depth to basement) × any future addition candidate |
| **Physical signature and transform** | Not a detector: a **gate**. Measured this session: C's dots sit at mean basement depth 402.4 m vs 534.9 m for the moat background; only 42.5 % of C's dots are below the moat median depth. The family systematically under-emits deep basins — exactly where the trace-based catalogue is blind. Gate future additions to depths above the moat median and re-measure. |
| **Why it catches MISSING faults** | Deep alluvial basins bury faults beyond any surface mapping; the catalogue's incompleteness is maximal where cover is thickest, so that is where new dots have the highest prior probability of being genuinely new. |
| **Difference from anything in the repository** | H55-C proposed basement-depth × gravity × conductivity *conjunction as a detector*; this uses depth as a **sampling prior on additions**, which no session has done. |
| **Data obtainable?** | YES — band 15 is in the restored official raster. |
| **Expected ΔDTI / cost** | A modifier, not a source: ±0.001 on whatever it gates. Cost trivial. |

---

## Rejected before ranking, with measured reasons

| idea | why rejected (this session's measurement) |
|---|---|
| H55-B strain-rate ridge emission | **Built and measured this session:** 25,837 Poisson dots score live-model projection 0.0152 standalone; C+field 0.2152 < 0.2728. ≈ 0.017 credit/dot vs the 0.0556 bar. Only a live dense emission could overturn; the projection says not worth the slot. |
| H56-A DEMGLOW emission | **Built and measured this session:** 1,991 dots, projection 0.0028 vs same-mass random 0.0023; C+field 0.2673 < 0.2728. The conjunction is real but sparse and sub-bar. Kept as rank-ineligible measurement, not promoted. |
| Band-16 seismicity dots | Lift 1.082 / AUC 0.522 — inside the unused-band noise band of the strain bands that just failed; no reason to expect better. |
| Band-17 conductivity ridge | AUC 0.474 — C's dots sit *below* background conductivity; the sign is inverted, and H55-C already owns the conductivity-conjunction idea. |
| Any further re-weighting/fusion of dotted × tip | Closed by three instruments now: union priced −0.0140 (live model), graded belief 0.0649 (this session), parents' inverted T differ by 1 %. |

## Validation rule carried forward

No weekly slot is spent on a candidate that has not (a) passed the blocked holdout on both
truths ≥ 3/4 folds against both parents, AND (b) shown a live-model projection at or above
the 0.2778 incumbent — except that the **first** rung of the Rank-1 removal ladder is
explicitly exempted by design: it is the one experiment whose *information value* (which
C-dots carry credit) exceeds its expected score, mirroring how A→B→C was discovered.
