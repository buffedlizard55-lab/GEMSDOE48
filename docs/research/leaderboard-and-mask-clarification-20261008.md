# Official leaderboard and fault-mask clarification — 2026-10-08

This dated addendum updates earlier repository language that treated catalogue-adjacent pruning as
“consistent with” a broad known-fault mask. The new statement is based on a direct read of the
current official competition pages and the DrivenData staff forum reply linked below; it does not
change or rewrite prior archived receipts.

## Current public leaderboard (single read)

The [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
was fetched on 2026-10-08 UTC. The visible rows included #1 `xiaofanhu` at 0.3774, #2
`alexoktaba` at 0.3345, #3 `nchuzhoy` at 0.3262, #4 `joeyfezster` at 0.3260, #5
`kinghorton42` at 0.3222, #6 Batik Shirt Brothers at 0.3221, #7 DARD at 0.3195 and #13
`extradr19` at 0.2778. The date is recorded but exact fetch time was not; the live page is dynamic.
See [`docs/data/leaderboard_20261008.json`](../data/leaderboard_20261008.json).

The 0.2778 public row is not linked to the local H33-2-B2 file (SHA-256
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9`); the local audit says
`UNSCORED`. Similarly, the user-reported 0.2600→0.2708→0.2778 ladder is a lead, not a verified
file-level organizer receipt or controlled experiment. The 0.3195 row is a dated public score,
not a verified private-score threshold and not evidence that a local model can reach it.

## Correct geometry of the known-fault evaluation mask

In the [official DrivenData community thread](https://community.drivendata.org/t/scoring-clarification-are-known-usgs-ingenious-faults-masked-when-scoring-and-are-they-in-the-final-round-label-set/11516/4),
DrivenData staff state:

1. The known-fault mask is **pixel-exact** and identical to the provided training-fault labels.
2. There is **no 300 m mask buffer** around known fault traces. Predictions outside those exact
   masked pixels are evaluated normally against the new-fault truth; proximity to a known trace
   does not itself exempt them from false-positive scoring.
3. A new-fault truth pixel can occur within 300 m of a known trace.

Therefore, earlier text suggesting that a 200–300 m catalogue-flank exclusion is directly
“rewarded” because the organizer masks the whole flank is unsupported and is corrected here.
A pruning transformation can still change the submitted values and thus change performance on
unseen new faults; without the exact submitted rasters, test labels and organizer receipts, the
direction and cause of the reported score ladder cannot be inferred. **The reason for the 0.2778
result remains unknown.** This update does not invalidate the fact that the local B2 bytes are
marked `UNSCORED`; it strengthens the caution against attributing a mechanism.

## Official output requirements and the reported range error

The [official problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
says EPSG:32611, 100 m resolution, the same bounds, one float32 raster layer, values between 0
and 1, and null/NaN outside the bounds. The H58 builder supplies two byte-distinct format
variants with identical in-footprint values: a zero-outside version that is locally all-finite
and range-safe for raw-array checks, and a NaN/nodata-outside version that follows the published
outside convention. No portal test was performed. Because the earlier rejected file is not
available, this project cannot identify whether that rejection was caused by an in-footprint
out-of-range value, NaN handling, or another upload issue. No variant is represented as
organizer-accepted.

The September 2026 [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf) says one
final selected GeoTIFF is used across prize phases, permits multiple platform submissions subject
to the current three-per-week limit, and requires disclosure of generative-AI use in the solution
narrative when applicable. It also makes clear that public scores are not the final private
expert-label evaluation. This is guidance, not a legal eligibility determination.

## Other official-source checks

- The [competition data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
  redirected to a DrivenData login page during this check; no credentials were used.
- USGS documents 3DEP products as free and without use restrictions, but full 1 m target-area
  coverage was not verified in this checkout: [USGS 3DEP products](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services).
- USGS ComCat documents event focal-mechanism products and query parameters, but event counts do
  not establish quality/completeness in the target area: [ComCat API](https://earthquake.usgs.gov/fdsnws/event/1/).
- USGS Landsat Collection 2 surface-temperature products are publicly accessible and have
  documented missing-data/cloud caveats; no target-area scene stack was audited:
  [Landsat Collection 2 ST](https://www.usgs.gov/landsat-missions/landsat-collection-2-surface-temperature).
- The official 2026 GeMS-SGMC release is described at [DOI 10.5066/P1A3DQZK](https://www.usgs.gov/data/geologic-map-schema-gems-version-state-geologic-map-compilation-sgmc-geodatabase-conterminous).
  That page does not by itself authenticate the locally pinned derived SGMC proxy TIFFs.

H58-A's complete scored result and no-slot decision are in [`h58-results-20261008.md`](h58-results-20261008.md).
