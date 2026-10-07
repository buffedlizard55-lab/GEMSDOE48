# H56-F pruning ladder — blocked proxy result and no-slot decision

Date: 2026-10-07 UTC. This is the follow-up to the H56 five-hypothesis slate, not a modification of its frozen preregistration. The first-ranked candidate was tested offline before any competition slot was used.

## Decision

**H56-F fails the pre-upload screen. Do not spend a competition slot on the H56-F ladder or the H56B Dempster-belief fusion on the evidence currently available.** The ladder never beats the H49 same-protocol public-proxy reference; its most aggressive rung (`Bel(F) >= 0.99`) materially degrades performance against the SGMC off-catalogue proxy. No candidate here has private-label evidence or a competition score.

## Frozen test

- **Parents:** local, SHA-pinned dotted C mask (H33-2-B2; owner-reported 0.2778) and H33-D tip/step-over mask (owner-reported 0.2632). Neither association between the owner-reported score and exact local bytes is organizer-authenticated.
- **Rule:** use the already-built H56B normalized `Bel(F)` field, and at *dotted-parent positive cells only* keep cells with Bel at least `0.90`, `0.95`, or `0.99`. This can only remove C pixels; it cannot add predictions. Thresholds were frozen in the H56 slate before this result. The 0.90 rung retained every C cell and is therefore exactly the dotted-parent baseline, not a new model.
- **Evaluation:** four fixed EPSG:32611 grid quadrants; held-out core plus 300 m halo clipped to the footprint; only truth in the core; official distance-weighted Tversky implementation (`alpha=0.2`, `beta=0.8`, triangular 300 m kernel). Every comparator in the receipt is evaluated by the same code, masks, folds, and metric.
- **Comparators:** dotted, tip/step-over, binary union, arithmetic binary mean, H56B graded belief, and H49's same-protocol reference.

Reproduce with:

```bash
.venv/bin/python scripts/evaluate_h56f_pruning.py
.venv/bin/python -m pytest tests/test_h56f.py -q
```

Machine-readable output: [`evidence/h56f_pruning_holdout_20261007.json`](../../evidence/h56f_pruning_holdout_20261007.json). The script writes only ignored research rasters under `scratch/h56f-pruning/`; it does not add another public submission artifact.

## Results

Each value is a mean of the four equally weighted fold DTIs; the receipt includes each fold and paired deltas.

| Candidate | Dotted cells retained | Catalogue proxy DTI | SGMC off-catalogue proxy DTI |
|---|---:|---:|---:|
| H49 same-protocol reference | 47,905 predicted cells | 0.095353 | **0.100751** |
| Dotted C parent | 37,654 | 0.006831 | 0.095491 |
| Tip/step-over parent | 41,865 | 0.086820 | 0.095491 |
| Binary parent union | 47,905 | 0.085538 | 0.096992 |
| Naive binary mean | weighted total 39,759.5 | 0.046406 | 0.088755 |
| H56B graded belief | graded | 0.032347 | 0.070552 |
| H56-F, threshold 0.90 | 37,654 (removed 0) | 0.006831 | 0.095491 |
| H56-F, threshold 0.95 | 37,142 (removed 512) | 0.006744 | 0.094821 |
| H56-F, threshold 0.99 | 31,614 (removed 6,040) | 0.005337 | 0.081123 |

All three rungs are below H49 on both proxy means; every rung's paired delta against H49 is negative in all four folds for both truth sources. At threshold 0.99, the 6,040 deleted cells are the C-only portion outside the parent intersection; the remaining 31,614 cells equal the dotted/tip intersection. On the SGMC proxy, this costs `0.014369` mean DTI versus dotted C and `0.019629` versus H49. The mild 0.95 rung is also below dotted C on mean SGMC DTI (`−0.000670`) and below H49 (`−0.005930`).

The four-quadrant catalogue proxy is exceptionally sparse for C (0.0068) and should not be interpreted as a live-score estimate: it is largely known-map material. The off-catalogue SGMC surface is a **public map proxy**, not the organizer's private expert labels. All parents and candidate surfaces are frozen full-scene mirrors; they were not independently reconstructed inside folds. The parent construction is known to use catalogue-distance pruning, so these blocked results remain conditional and potentially leaky. These limitations reduce the strength of conclusions but do not turn any negative measurement into evidence of improvement.

## Metric and evidence-theory corrections

1. The live-model projection formerly reported for H56B (`0.0649`) is retired as a score-like estimate. Its algebra used `FPw = S - TPw`, which is generally false for the official distance-weighted metric: the official page defines prediction-centred false-positive weight separately from truth-centred true-positive credit. Do **not** cite 0.0649 as a projected score, ceiling, or ranking prediction. The exact same-protocol proxy measurements above are the valid local evidence currently used for the no-slot decision.
2. Under normalized Dempster combination, raw conflict `K` is the mass on mutually exclusive focal-set intersections and is removed by the normalization factor `1-K`; standard Dempster combination does not transfer this conflict into `m(Theta)`. The canonical `m(Theta)` is residual unassigned/ignorance mass under the selected BPAs, and can be high even when the sources do not directly disagree. H56B correctly exports `m(Theta)` separately and also exports raw `K`; read `K` (and the source fields) as conflict/disagreement diagnostics rather than claiming that `m(Theta)` alone is a disagreement map. The unrelated H56-OWDS builder additionally has an absolute support-disagreement layer.
3. D-S combination is not new in this repository: H53 already contains the same B2 × H33-D family diagnostic. H56B is a parameterization/output distinction, not a new geological signal. It is not pixel-identical to the arithmetic mean (the H56B receipt reports Pearson `r=0.38865` against the binary mean and `r=0.98660` against the metric-kernel mean), but high correlation with the kernel-mean field remains; nonidentity does not imply better ranking or score.

## Hypothesis slate and next work

The five-candidate slate remains in [`hypotheses-h56-20261007.md`](hypotheses-h56-20261007.md) and [`evidence/hypothesis_slate_h56b_20261007.json`](../../evidence/hypothesis_slate_h56b_20261007.json). It ranks:

1. H56-F absence-driven pruning using the local dotted and tip-family fields — **now tested and rejected for slot use on these proxies**.
2. 3 m DEM channel-knickpoint clusters using USGS 3DEP — source-access pipeline is available, but the fault-detector hypothesis is unvalidated.
3. Conduit-anchor stepping-stone traces from the public GDR INGENIOUS wellsprings table plus magnetic horizontal gradient — local inputs exist; any result needs leakage and source-lineage audit.
4. Radiometric K-residual alteration halos crossed with magnetic horizontal gradient — local mirror exists, but source authenticity/asset reuse terms and uint8 quantization remain caveats.
5. Basement-depth cover gating — use as a preregistered sampling modifier, not as a claim that deep cover itself locates a fault.

The highest-value next experiment is not a live slot for H56-F. It is an offline, preregistered detector that contributes *new* off-catalogue geology (e.g., a channel-profile operator over the verified 3DEP region mosaic), followed by the same blocked proxies, equal-mass controls, independent provenance/leakage review, and a fresh holdout if feasible. Only after it clears those gates should a slot be considered. External-source availability does not establish that any hypothesis will improve DTI.

## Official/manual-review sources

- [DrivenData problem, metric, and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/): official `DTI`, `TPw`, `FPw`, `FNw`, 300 m kernel, alpha/beta, raster CRS/resolution/range/outside-bounds requirements.
- [Current public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), read once for this session: #1 shows 0.3774; 0.3195 is #7. A leaderboard row does not identify any local GeoTIFF.
- [Dempster (1967), DOI 10.1214/aoms/1177698950](https://doi.org/10.1214/aoms/1177698950), and Shafer, [*A Mathematical Theory of Evidence*](https://www.jstor.org/stable/j.ctv10vm1qb) (Princeton University Press, 1976). These ground the combination framework; the implementation's semantics are recorded above and tested in `src/gemsdoe48/h56.py` / `src/gems48/ds.py`.
- [USGS 3DEP program](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services): official data availability reference, not evidence for the knickpoint detector's performance.
