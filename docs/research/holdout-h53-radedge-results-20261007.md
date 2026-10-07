# H53-RadEdge-1 blocked-holdout result — 2026-10-07

> **Post-merge namespace note:** this H33-D × GeoDAWN radiometric-edge experiment was frozen as `H53-1` on its original branch. The merged repository already contains a different lidar experiment using that local identifier; this report therefore calls the experiment **H53-RadEdge-1**. The namespace change does not alter the preregistered source, parameters, gates, TIFF bytes, or scores. See [`evidence/h53_radedge_namespace_erratum_20261007.json`](../../evidence/h53_radedge_namespace_erratum_20261007.json).

## Decision

**H53-RadEdge-1 fails the preregistered promotion gate. Do not spend a weekly submission slot on it.** It does not beat the current blocked-proxy best H49; it underperforms H49 by `−0.038930` mean DTI on the primary newer-SGMC off-catalogue proxy (0/4 folds positive), repeats the loss on the older-SGMC sensitivity, and the radiometric addition is slightly worse than the two-family D-S-only and naive-mean baselines. No organizer score or leaderboard improvement is claimed.

## Candidate and reproducibility

- Unique research artifact: **`GEMSDOE48-H53-DS-RadEdge-B2xH33D-4c01fcf2ad8c`**.
- Main TIFF: [`GEMSDOE48-H53-DS-RadEdge-B2xH33D-20261007-4c01fcf2ad8c-nan-outside.tif`](../downloads/GEMSDOE48-H53-DS-RadEdge-B2xH33D-20261007-4c01fcf2ad8c-nan-outside.tif), 17,382,618 bytes, SHA-256 `4c01fcf2ad8c1d2bd487bc4d07c85e57b2a256296586d4817b58079b0ccd7a1f`.
- It is single-band float32 on the 3,292 × 3,730 EPSG:32611 100 m grid. The 5,167,373 in-footprint cells are finite in [0,1]; the 7,111,787 outside cells are NaN. Local format validation passes; this is not organizer acceptance.
- Parents: H33-2-B2 SHA `c55bafc4…` (owner registry value 0.2778, exact file-to-score attribution unverified) and H33-D SHA `87f857d5…` (owner-reported 0.2632). Radiometry: GeoDAWN K/Th/U/TC SHA `c22420f7…`, with zero treated as nodata.
- Build recipe and complete hashes/parameters: [`scripts/build_h53_candidate.py`](../../scripts/build_h53_candidate.py) and [`evidence/build_h53_radedge_receipt_20261007.json`](../../evidence/build_h53_radedge_receipt_20261007.json). The pre-build slate is [`hypotheses-h53-radedge-20261007.md`](hypotheses-h53-radedge-20261007.md); machine-readable preregistration is [`evidence/h53_preregistration_20261007.json`](../../evidence/h53_preregistration_20261007.json). In the build receipt, top-level `status` is the original build-stage value; `current_disposition` and `candidate.holdout_status` record the later failed gate. The build and holdout scripts now distinguish those states explicitly.

## Why these two parents

B2 is the strongest dotted-family parent by the owner-reported family ladder, although its 0.2778 attribution to the exact local bytes is unresolved. For the requested *tip/step-over* family, H33-D (owner-reported 0.2632) was selected as the explicitly identified tip/step-over construction and the more complementary surface: it shares 31,614 of 37,654 B2 cells (Jaccard 0.659931). The owner-reported H32-1 prethin-tip/Euler surface is slightly higher at 0.2649, but 97.93% of B2 cells overlap it, and B2×H32 had already been explored in H48; its exact local file was fetched only into scratch and not used here. H36-1's 0.2710 row is a rung-30 H19-5 repacking, not the actual tip/step-over family. Separate build pipelines are not evidence of statistical independence. This is a documented choice of family identity and complementarity—not a claim that H33-D has the highest numerical owner-reported score among every tip-adjacent artifact.

## Frozen validation protocol

The evaluator reuses `scripts/run_spatial_holdout.py`'s four fixed geographic quadrants, held-out core plus a 300 m halo, core-only truth, and the challenge's triangular 300 m DTI kernel (α=0.2, β=0.8). The primary target is the pinned newer SGMC raster with positive cells >300 m from the public catalogue; the prior raw-SGMC raster is reported separately, not pooled. H49 is rescored on the same folds as the current local public-proxy best. Source surfaces are frozen, were not rebuilt in each fold, and are potentially leaky because B2 was pruned using full catalogue geometry.

## Primary newer-SGMC off-catalogue proxy

| Candidate | Mean DTI | NW | NE | SW | SE |
|---|---:|---:|---:|---:|---:|
| H49 current proxy-best | **0.100751188** | 0.106053414 | 0.107901401 | 0.110413525 | 0.078636413 |
| B2 dotted parent | 0.095491168 | 0.101822069 | 0.099124646 | 0.107460816 | 0.073557139 |
| H33-D tip/step-over parent | 0.095491074 | 0.101428732 | 0.100171744 | 0.106455468 | 0.073908351 |
| Binary union | 0.096991657 | 0.102528375 | 0.102656235 | 0.106519977 | 0.076262041 |
| Two-family naive mean of 300 m supports | 0.062518807 | 0.064109350 | 0.080690556 | 0.041208991 | 0.064066330 |
| Two-family D-S, no radiometry | 0.063864556 | 0.065829488 | 0.081979529 | 0.042809954 | 0.064839254 |
| **H53-RadEdge-1 D-S plus radiometric edges** | **0.061821062** | 0.062374798 | 0.079089486 | 0.038245201 | 0.067574764 |

Paired H53-minus-H49 deltas are `−0.043678616`, `−0.028811915`, `−0.072168324`, and `−0.011061649` (mean `−0.038930126`, 0/4 positive). Relative to the two-family D-S baseline, H53-RadEdge-1 is `−0.002043494` mean; relative to the two-family support mean it is `−0.000697745`.

## Older raw-SGMC sensitivity and catalogue proxy

On the older raw-SGMC off-catalogue raster, H53-RadEdge-1 mean DTI is **0.061098918** vs H49 **0.099768355** (paired `−0.038669437`, 0/4 positive). Fold scores for H53 are 0.062374798 / 0.076225020 / 0.038245201 / 0.067550654.

On the public catalogue-label proxy, H53-RadEdge-1 scores **0.041245051** vs H49 0.095353248, the H33-D parent 0.086820186, and the union 0.085538370. These proxy labels are not the private expert-labelled competition truth.

Full fold records, pinned truth counts, paired deltas, and gate evaluation are in [`evidence/holdout_h53_radedge_20261007.json`](../../evidence/holdout_h53_radedge_20261007.json). The frozen gate required +0.005 over H49 on the primary target, ≥3/4 positive folds, a positive older-raster sensitivity in ≥3/4 folds, and positive gains over both the two-family D-S and mean. **All key primary conditions failed.**

## Was it merely the mean? Is it meaningfully new?

The main TIFF is **not pixelwise equal** to the average of the two family kernel-support fields: 5,144,439 of 5,167,373 in-footprint cells differ, MAE is 0.01844, maximum absolute difference 0.09654, and 7.17% of cells differ by more than 0.05. But this is not strong evidence of useful new information: Pearson correlation is **0.99446** and the budget-matched top-37,654 Jaccard is **0.97685**. Against the two-family D-S-only output, Pearson is 0.99603 and top-k Jaccard is 0.97737. The radiometric term changed values more than it changed the leading locations.

A bounded local audit compared the output with 41 same-grid TIFFs in the repository's top-level `docs/downloads` and `data/families`: no exact SHA or in-footprint pixel match was found. The closest is the historical H49 belief field (Pearson **0.99471**, top-37,654 Jaccard **0.97685**). Thus H53-RadEdge-1 is a newly constructed, pixel-distinct artifact, but not a practically distinct top-budget ranking from that local prior. This is a bounded repository check only—not a claim of global or organizer-side uniqueness. See [`evidence/h53_radedge_submission_validation_20261007.json`](../../evidence/h53_radedge_submission_validation_20261007.json).

The H53 surface assigns positive weight to **5,144,440 of 5,167,373** valid cells (99.56%) and has total in-footprint prediction mass ≈ **354,931**, versus 47,905 unit-valued pixels in H49. The dense low-level field is a poor match for this metric's false-positive penalty. That, rather than a TIFF-format issue, is a likely proximate cause of the low DTI.

## Dempster diagnostics and interpretation

- The two family masks share 31,614 cells (Jaccard 0.659931; 83.96% of B2 and 75.51% of H33-D), so source independence is not established.
- Mean final residual Dempster `m(Theta)` is 0.24535. Mean cumulative raw conflict `K` is 0.04713 (P95 0.14034). These are exported as separate diagnostic TIFFs: [`m(Theta)`](../downloads/diagnostics/GEMSDOE48-H53-DS-RadEdge-B2xH33D-20261007-4c01fcf2ad8c-mtheta-dempster.tif) and [raw `K`](../downloads/diagnostics/GEMSDOE48-H53-DS-RadEdge-B2xH33D-20261007-4c01fcf2ad8c-conflict-total-K.tif). The family-pair conflict is also available [here](../downloads/diagnostics/GEMSDOE48-H53-DS-RadEdge-B2xH33D-20261007-4c01fcf2ad8c-conflict-b2-h33d-K.tif).
- Canonical Dempster `m(Theta)` excludes conflict `K`; it is not the conflict transferred into ignorance. The Yager-style transfer is computed only as an internal sensitivity and is not exported under the Dempster label.
- The result is a normalized belief surface, not an empirically calibrated probability map. The edge score is a normalized geophysical contrast field; radiometric contacts, weathering, quantization, and survey artifacts can look like faults.

## Final disposition

A post-slate official-data availability check for H53-RadEdge-2/H53-RadEdge-3 is recorded separately in [`data-availability-geochem-magnetic-20261007.md`](data-availability-geochem-magnetic-20261007.md). It does not alter the frozen preregistration or use any newly downloaded data in H53-RadEdge-1.

Keep H53-RadEdge-1 as a negative research result and retain its exact receipt. **Do not upload it, do not spend a weekly slot, and do not describe the holdout as a leaderboard score.** A proxy win would still need independent/private evidence, organizer file-to-score confirmation, license review, format review, and an explicit go/no-go decision. The `GEMSDOE48-H53` portal note in the build receipt is a draft only; it is not a recommendation to submit.
