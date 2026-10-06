# H48-1 spatial-block diagnostics — 2026-10-06

**Result: H48-1 fails the preregistered promotion gate and remains ineligible for a submission slot.** Both targets are conditional public-map proxies, not private expert truth or competition scores. The paired rows below use one fold implementation for every prediction surface and both targets.

## Common fold protocol

- Four fixed quadrants (`NW`, `NE`, `SW`, `SE`) on the full 3,730 × 3,292 EPSG:32611 grid at 100 m.
- Each score domain is the held-out quadrant plus a 300 m Euclidean halo, clipped to the finite 5,167,373-cell sample-template footprint. Truth positives are restricted to the held-out core; prediction values are available in the halo for the official distance kernel and set to zero outside the domain.
- Metric: official distance-weighted Tversky, triangular 300 m kernel, `alpha=0.2`, `beta=0.8`. The implementation is tested against an independent brute-force oracle.
- Each fold score is calculated separately. Reported mean DTI is the unweighted mean of the four folds, not a pooled pixel or tier-sweep score.
- Every candidate, comparator, and truth layer uses these same folds, domains, and metric. The prediction rasters are frozen upstream products; they were not rebuilt independently within folds.

## Proxy truth definitions

1. **Catalogue labels:** 60,988 positive cells from the public owner-mirror label raster (SHA-256 `7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093`). It represents known public catalogue faults, not the private expert-labelled competition target.
2. **SGMC off-catalogue faults (primary):** 62,122 positive cells in the newer pinned derivative (SHA-256 `643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0`), inside the footprint and more than 300 m from every positive catalogue-label cell. This is still an owner-mirror public-map proxy; its source-vector derivation was not independently rebuilt.

A prior raw SGMC raster (SHA-256 `26d142c4c93282cd94f6950ab96f22aeff59fbbea523d43d662e76fa1b161b5c`) yields 61,664 target cells under the same distance rule. Though dimensions, CRS, and affine transform match, the rasters differ in nodata metadata and 1,450 positive-mask cells (1,446 newer-only; 4 raw-only). The discrepancy is unresolved. The newer derivative is primary because it is pinned in `registry/inputs.json`; the old raster's separate sensitivity run is preserved in `evidence/holdout_raw_sgmc_20261006.json` and the comparison receipt is `evidence/sgmc_raster_comparison_20261006.json`.

Neither mirror is organizer-authenticated. Filtering SGMC by catalogue distance does not undo candidate-model leakage or turn the proxy into private expert truth.

## Catalogue-proxy results

| Candidate | NW | NE | SW | SE | Mean DTI |
|---|---:|---:|---:|---:|---:|
| Dotted input | 0.00614017 | 0.00856664 | 0.00752446 | 0.00509091 | 0.00683054 |
| Tip/stepover input | 0.08272042 | 0.10202996 | 0.08960076 | 0.07292961 | 0.08682019 |
| Arithmetic mean | 0.04399987 | 0.05467085 | 0.04824520 | 0.03870969 | 0.04640640 |
| Prior alpha=.99 normalized belief | 0.04380968 | 0.05443621 | 0.04804228 | 0.03854156 | 0.04620743 |
| Prior full-union decision | 0.08147706 | 0.10045926 | 0.08828044 | 0.07193671 | 0.08553837 |
| **Current rho=.5 Dempster fusion** | **0.03087113** | **0.03866373** | **0.03377285** | **0.02704332** | **0.03258776** |

### Paired deltas: current fusion minus comparator

| Comparator | NW | NE | SW | SE | Mean delta | Positive folds |
|---|---:|---:|---:|---:|---:|---:|
| Dotted input | +0.02473096 | +0.03009710 | +0.02624839 | +0.02195242 | +0.02575722 | 4/4 |
| Tip/stepover input | −0.05184928 | −0.06336623 | −0.05582791 | −0.04588629 | −0.05423243 | 0/4 |
| Arithmetic mean | −0.01312874 | −0.01600712 | −0.01447235 | −0.01166636 | −0.01381864 | 0/4 |
| Prior full-union decision | −0.05060593 | −0.06179553 | −0.05450759 | −0.04489339 | −0.05295061 | 0/4 |

The fusion improves over the weak dotted baseline but loses to tip/stepover, arithmetic averaging, and the prior union in every fold. It does not meet the minimum three-of-four win rule against each input.

## SGMC off-catalogue results under the same fold protocol

| Candidate | NW | NE | SW | SE | Mean DTI |
|---|---:|---:|---:|---:|---:|
| Dotted input | 0.10182207 | 0.09912465 | 0.10746082 | 0.07355714 | 0.09549117 |
| Tip/stepover input | 0.10142873 | 0.10017174 | 0.10645547 | 0.07390835 | 0.09549107 |
| Arithmetic mean | 0.09605623 | 0.09240516 | 0.09748449 | 0.06907247 | 0.08875458 |
| Prior alpha=.99 normalized belief | 0.09602486 | 0.09235530 | 0.09744063 | 0.06903737 | 0.08871454 |
| Prior full-union decision | 0.10252838 | 0.10265624 | 0.10651998 | 0.07626204 | **0.09699166** |
| Historical Yager alternative (not slot-cleared) | 0.09147422 | 0.08502775 | 0.09113135 | 0.06393249 | 0.08289145 |
| **Current rho=.5 Dempster fusion** | **0.07481534** | **0.07033302** | **0.07938167** | **0.05251519** | **0.06926131** |

### Paired deltas: current fusion minus comparator

| Comparator | NW | NE | SW | SE | Mean delta | Positive folds |
|---|---:|---:|---:|---:|---:|---:|
| Dotted input | −0.02700673 | −0.02879163 | −0.02807914 | −0.02104195 | −0.02622986 | 0/4 |
| Tip/stepover input | −0.02661339 | −0.02983873 | −0.02707379 | −0.02139316 | −0.02622977 | 0/4 |
| Arithmetic mean | −0.02124089 | −0.02207214 | −0.01810281 | −0.01655728 | −0.01949328 | 0/4 |
| Prior alpha=.99 normalized belief | −0.02120952 | −0.02202228 | −0.01805896 | −0.01652218 | −0.01945324 | 0/4 |
| Prior full-union decision | −0.02771303 | −0.03232322 | −0.02713830 | −0.02374685 | −0.02773035 | 0/4 |

The current rho=.5 candidate fails every paired SGMC-proxy comparison. Yager improves over that Dempster candidate by +0.01363015 (4/4), but its mean delta versus dotted is −0.01259971 (0/4), versus tip/stepover −0.01259962 (0/4), versus arithmetic mean −0.00586313 (0/4), and versus prior union −0.01410020 (0/4). The prior union has the highest comparator mean on this proxy, not evidence that it wins on private labels or should be submitted.

## Older raw-raster sensitivity and PR #5 protocol distinction

The same blocked-fold script was also run against `data/raw/sgmc_faults_100m.tif`; the complete paired report is separate at [`evidence/holdout_raw_sgmc_20261006.json`](../../evidence/holdout_raw_sgmc_20261006.json). Its mean DTI values were dotted 0.09450317, tip/stepover 0.09449144, arithmetic mean 0.08784120, prior union 0.09595726, Yager 0.08206068, and rho=.5 Dempster 0.06857388. The fusion still loses to each parent, arithmetic mean, and prior union in all four folds; Yager improves over Dempster but loses to the parents and mean in all four. Do not pool these scores with the newer-raster results.

The archived PR #5 proxy evaluator also used the newer derived raster but counted cells at `>=300 m` (63,121 cells) and used full-scene quadrant domains. It reported Yager 0.08407042, dotted 0.09613246, tip/stepover 0.09709394, and arithmetic mean 0.09030297. Those results are historical, are not comparable to this core-plus-halo protocol, and do not clear a slot gate.

## Reconciliation with the previous main-branch experiment

The earlier alpha=.99 tier sweep reported pooled SGMC off-catalogue scores of 0.093965 (dotted), 0.094245 (tip), 0.096047 (full union), and 0.088005 (normalized DS belief). The selected tier came from pooled proxy scores, not from independent blocked selection. Its stored `holdout_validation.json` explicitly records `F_beats_A_folds=0`, `F_beats_B_folds=0`, `F_geq_D_folds=0`, and `PASS_offcat_blocked=false`.

The earlier quadrant evaluator used full-grid predictions while masking truth to one quadrant; its fold-domain semantics differ from this report. Those old fold values are retained for provenance, not compared numerically with the current table. Here the prior union and alpha=.99 belief are reconstructed from the same pinned inputs and scored alongside rho=.5 with identical core-plus-halo semantics. That apples-to-apples check confirms the rho=.5 candidate is weaker than the prior union as well.

## Leakage and interpretation limits

1. H33-2-B2 and H33-D are frozen upstream owner-mirror surfaces and were not reconstructed independently in each fold.
2. The H33-2-B2 owner audit describes removing candidate pixels within 200 m of the **full** catalogue. Withheld catalogue geometry was therefore available during source construction. These catalogue-block numbers are conditional and potentially leaky even though scoring truth is core-restricted.
3. The catalogue labels are existing public USGS/INGENIOUS traces; the SGMC raster is also a public map proxy. Neither measures discovery of new private expert-labelled faults.
4. Source mirrors are not organizer-authenticated. Hash pins do not establish accuracy, source-vector lineage, or licensing/permission to submit or redistribute.
5. No leaderboard score, hidden-test estimate, private truth, or expected win probability is inferred.

The fixed rho=.5 was not retuned after observing these results. Machine-readable per-fold DTI, TP/FP/FN, prediction mass, fold sizes, hashes, comparisons, and the no-slot decision are in [`evidence/holdout_20261006.json`](../../evidence/holdout_20261006.json). The frozen hypotheses and numeric gate are in [`hypotheses-20261006.md`](hypotheses-20261006.md).
