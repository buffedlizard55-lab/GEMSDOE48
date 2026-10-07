# H53-A strike-coherent LiDAR candidate — blocked proxy result — 2026-10-07 UTC

**Decision: H53-A fails its preregistered gate. No competition slot was used; do not upload this research TIFF.**

## Candidate and local artifact

H53-A starts with the owner-reported 0.2778 dotted parent C, keeps its 37,654 cells unchanged, and appends 12,000 greedily Poisson-spaced cells selected by a 100 m strike-coherence score computed from the pinned, 3DEP-derived H52 regional raster. The new binary candidate has 49,654 positive cells. Local candidate file:

- [`GEMSDOE48-H53-STRIKE-COHERENCE-20261007-de35531d3867-nan-outside.tif`](../downloads/GEMSDOE48-H53-STRIKE-COHERENCE-20261007-de35531d3867-nan-outside.tif)
- SHA-256: `de35531d386792da1950eac815f98db8f36304f78debb6b568138d070640d9bd`; 403,844 bytes.
- It is one-band float32, EPSG:32611, 100 m, 3,730 × 3,292, finite `{0,1}` inside the template footprint and NaN/nodata outside. The local format audit passes; this says nothing about DrivenData acceptance.
- Builder [`scripts/build_h53_scarp_coherence.py`](../../scripts/build_h53_scarp_coherence.py); frozen slate [`hypotheses-h53a-scarp-20261007.md`](hypotheses-h53a-scarp-20261007.md) and [`evidence/hypothesis_slate_h53a_scarp_20261007.json`](../../evidence/hypothesis_slate_h53a_scarp_20261007.json).
- Paste-ready note (133 characters): `GEMSDOE48-H53 | C + 12k Poisson dots ranked by 500m strike-coherent 3DEP scarp support; proxy-tested research only; NOT slot-cleared.`

## Preregistered test result

The exact same four geographic quadrants, held-out core + 300 m Euclidean halo, DTI parameters, truth masks, and frozen H49 TIFF were compared. The SGMC targets are public-map proxies—not private expert truth and not organizer scores. The older raw SGMC sensitivity is reported separately from the newer derived raster.

| Proxy target | H53-A mean DTI | H49 mean DTI | Paired mean Δ (H53−H49) | H53-A folds above H49 | Gate |
|---|---:|---:|---:|---:|---|
| Newer derived SGMC faults >300 m from catalogue | 0.0981104 | 0.1007512 | −0.0026408 | 1/4 | **Fail** |
| Older raw SGMC sensitivity >300 m from catalogue | 0.0970865 | 0.0997684 | −0.0026819 | 1/4 | **Fail** |
| Public catalogue labels (context only) | 0.0088985 | 0.0953532 | −0.0864548 | 0/4 | Not a promotion target; catalogue-distance pruning makes this comparator inappropriate for off-catalogue recovery |

H53-A does beat the prior full-union comparator (0.0969917 newer / 0.0959573 older) by +0.0011187 / +0.0011292 mean DTI and in 3/4 folds, but **H49 remains the current proxy-best** and the H53-A pre-registered gate required a win over H49 on both raster definitions. This is not close enough to reinterpret as a pass. Report JSONs: [`evidence/holdout_h53a_scarp_spatial_20261007.json`](../../evidence/holdout_h53a_scarp_spatial_20261007.json), [`evidence/holdout_h53a_scarp_raw_sgmc_20261007.json`](../../evidence/holdout_h53a_scarp_raw_sgmc_20261007.json), and paired decision [`evidence/h53a_scarp_vs_h49_20261007.json`](../../evidence/h53a_scarp_vs_h49_20261007.json).

## Interpretation

The result shows that adding an explicit 100 m strike-continuity filter changes the map but does **not** make the top H49 proxy score. It provides no evidence of improvement on private fault labels. A likely limitation is that the stored regional layer preserves only a single max-height strike per 100 m cell; the five-point check is not a full 3 m fault-trace reconstruction and cannot separate every scarp from terrace, channel, or anthropogenic edges. The original H52-1 region result also showed the proxy value was partly terrain-class signal, so this filtered derivative should not be treated as an independent confirmation.

The selection itself uses the full public catalogue as a 200 m exclusion mask, and parent C is a frozen full-catalogue-derived file. The fold scores are therefore conditional and potentially leaky, despite the core-plus-halo evaluation. The numerator truth is an owner-mirror SGMC raster; the second raster is a nonidentical older owner-mirror derivative. No public-proxy result alone clears a weekly competition slot.

## Source freshness and artifact checks

The official [DrivenData challenge/submission page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [USGS 3DEP products page](https://www.usgs.gov/3d-elevation-program/about-3dep-products-services) were freshly retrieved during this continuation. DrivenData specifies a single-layer float32 GeoTIFF on the EPSG:32611, 100 m grid, null/NaN outside the bounds, values in [0,1]; H53-A's local format receipt checks those local properties but is not portal acceptance. The USGS page describes 3DEP products and access, but does not independently verify the exact regional tile payloads or footprint coverage used here. The [USGS 3DHP access page](https://www.usgs.gov/3d-hydrography-program/access-3dhp-data-products) was also freshly retrieved; H53-B's exact payload and coverage remain unaudited. The frozen slate records the other official URLs (GeMS/SGMC and GeoDAWN) and their open provenance/coverage questions; H53-D remains parked.

**Prior-art boundary:** in parallel, PR #12 merged H53-1, a three-source adaptive Dempster fusion, into `main` (see [the separate H53-1 result](holdout-h53-results-20261007.md)). H53-A is a distinct binary strike-continuity filter on C; it is not that three-source fusion, and its score is evaluated independently below.


- Format receipt: [`evidence/h53a_scarp_submission_validation_20261007.json`](../../evidence/h53a_scarp_submission_validation_20261007.json) — `PASS_LOCAL_FORMAT_AUDIT_NOT_ORGANIZER_ACCEPTANCE`.
- Bounded identity receipt: [`evidence/h53a_scarp_submission_identity_20261007.json`](../../evidence/h53a_scarp_submission_identity_20261007.json) — after merging H53-1, 65 local TIFFs were attempted and 61 one-band same-grid rasters compared across `docs/downloads/` and `data/`; no exact value/support match, max positive-support Jaccard 0.7583276 to the intended parent C. This local comparison does not establish uniqueness across all linked GEMSDOE sites or organizer storage.
- Build receipt: [`evidence/build_h53a_scarp_receipt_20261007.json`](../../evidence/build_h53a_scarp_receipt_20261007.json).
- No leaderboard submission or weekly slot was used for H53-A.

## Next decision

Keep H49 as the highest same-protocol proxy result and keep all submission slots unused. The next high-value work is not another threshold sweep on the same aggregate layer: obtain a target-appropriate independent evaluation of unmapped alluvial scarps or reprocess source 3DEP profiles with a frozen dual-baseline/line-tracing detector and a scarp-specific validation set. Candidate H53-B (3DHP channel profiles) and H53-D (GeMS contact topology) remain parked because their exact usable in-footprint source payloads are not audited. See the [frozen slate](hypotheses-h53a-scarp-20261007.md) and [official source register](../sources.md).
