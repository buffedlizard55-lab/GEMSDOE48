# H48-1 blocked diagnostic — 2026-10-06

**Result: H48-1 fails the numeric promotion gate and remains ineligible for a submission slot.** The score is a conditional catalogue-proxy diagnostic, not a competition score or a leakage-free validation.

## Protocol actually run

- Truth: 60,988 positive pixels in the public owner-mirror label raster (SHA-256 `7ba308…4093`). The source is not organizer-authenticated and represents existing mapped catalogue faults, not the private expert-labelled target.
- Blocks: four fixed quadrants (`NW`, `NE`, `SW`, `SE`) of the full 3,730 × 3,292 EPSG:32611 grid.
- Each evaluation domain: one held-out quadrant plus a 300 m Euclidean halo, clipped to the 5,167,373-cell finite sample-template footprint. Held-out positives are only those in the core quadrant; predictions in the halo are available to receive the official distance kernel.
- Metric: official distance-weighted Tversky equation, 300 m triangular kernel, `alpha=0.2`, `beta=0.8`. Its implementation was compared with an independent brute-force oracle on synthetic rasters.
- Candidates: dotted input, tip/stepover input, arithmetic mean, and fixed `rho=0.5` Dempster fusion.

## Results

| Candidate | NW | NE | SW | SE | Mean DTI |
|---|---:|---:|---:|---:|---:|
| Dotted input | 0.006140 | 0.008567 | 0.007524 | 0.005091 | 0.006831 |
| Tip/stepover input | 0.082720 | 0.102030 | 0.089601 | 0.072930 | **0.086820** |
| Arithmetic mean | 0.0439999 | 0.054671 | 0.048245 | 0.038710 | 0.046406 |
| Discounted Dempster fusion | 0.030871 | 0.038664 | 0.033773 | 0.027043 | 0.032588 |

### Paired deltas for fusion

| Comparator | NW | NE | SW | SE | Mean delta | Positive folds |
|---|---:|---:|---:|---:|---:|---:|
| Dotted input | +0.024731 | +0.030097 | +0.026248 | +0.021952 | +0.025757 | 4/4 |
| Tip/stepover input | −0.051849 | −0.063366 | −0.055828 | −0.045886 | −0.054232 | 0/4 |
| Arithmetic mean | −0.013129 | −0.016007 | −0.014472 | −0.011666 | −0.013819 | 0/4 |

The fused candidate improves on the much weaker dotted input but loses to the tip/stepover surface and to arithmetic averaging in every block. This fails the preregistered requirement to improve over each input on at least three of four blocks; it also does not beat the arithmetic-mean baseline. No owner-reported historical best was promoted to an authenticated comparator. **Do not use a weekly submission slot for this candidate.** The raw conflict and ignorance layers remain useful diagnostics, but disagreement awareness alone is not evidence of a higher DTI.

The exact per-fold TP/FP/FN, prediction mass, fold sizes, deltas, source hashes, and gate decision are in [`evidence/holdout_20261006.json`](../../evidence/holdout_20261006.json).

## Leakage and interpretation limits

1. The H33-2-B2 and H33-D surfaces are frozen upstream owner-mirror artifacts and were not reconstructed independently in each fold.
2. The H33-2-B2 owner audit describes removing candidate pixels within 200 m of the **full** catalogue. Therefore withheld catalogue geometry was available during upstream source construction. A quadrant score on the resulting surfaces is conditional and potentially leaky even though the local metric only counts truth in each held-out quadrant.
3. The labels are existing public USGS/INGENIOUS catalogue traces. They cannot establish recovery of new expert-labelled private test faults or discovery of off-catalogue faults.
4. The surface mirrors and labels are third-party owner copies; hash pinning does not establish organizer authentication, accuracy, or license permission.
5. No leaderboard score, hidden-test score, or expected win probability is inferred from these values.

The preregistered `rho=0.5` was not retuned in response to this result. See [`hypotheses-20261006.md`](hypotheses-20261006.md) for the pre-result hypotheses and gate.
