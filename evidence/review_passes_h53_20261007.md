# H53 end-to-end review log — 2026-10-07 UTC

## Pass 1 — implementation and verification

- Kept the slate frozen and implemented only H53-A, not H53-B/C/D or proposed raw-DEM H52-v2.
- Rebuilt H53-A from the locally hash-pinned H52-derived 3DEP raster, dotted parent C, public catalogue exclusion mirror, and footprint. Deterministic rebuild reproduced the same candidate SHA-256 `de35531d386792da1950eac815f98db8f36304f78debb6b568138d070640d9bd` and 12,000 additions.
- Re-ran the independent local submission validator: one-band float32, 3,730 × 3,292, EPSG:32611, 100 m, in-footprint range [0,1], NaN outside. This is not organizer acceptance.
- Ran the paired H53/H49 report with candidate/label/SGMC hashes and identical fold geometry, evaluation domain, and DTI semantics checked. Both SGMC comparisons failed the preregistered promotion gate. No submission slot was used.
- Scanned 58 local TIFFs under `docs/downloads/` and `data/`; 54 one-band rasters were on the exact comparison grid. No exact in-footprint value or positive-support match was found. This is not a global uniqueness proof.
- Updated the repository README, live static landing page, executive summary, hypotheses page, research status, and next-steps page to put the H53 download and explicit do-not-upload decision first. The H50 Dempster-Shafer diagnostic deliverables remain linked and described separately.

## Pass 2 — bug, assumption, edge-case review

- Reviewed the strike-bin quantization, unoriented 0°/180° wrap, deterministic integer offsets, support-count threshold, stable score tie-break, 200 m exclusions, and NaN-outside export. Confirmed the actual stored `strike_at` values are 0, 15, …, 165 degrees after scale decoding; the source does retain only one best strike per 100 m cell.
- Found and fixed an edge case in the Poisson thinning helper: a zero-cell budget could previously keep one cell. Added zero-budget, occupied-cell, Euclidean-spacing, malformed-shape, and out-of-bounds tests. The frozen 12,000-cell build and TIFF bytes are unchanged.
- Made the bounded identity auditor's optional candidate path safe when supplied outside the checkout; its report still limits its scan to local `docs/downloads/` and `data/`.
- The frozen construction permits qualifying source samples outside the official output footprint to support an in-footprint center; only candidate centers and emitted predictions are footprint-masked. The regional product has valid data beyond that footprint. This is a construction assumption, not a footprint-output violation, and source cells are not independent observations.
- Construction uses the full public catalogue as a distance-exclusion mask and parent C is catalogue-derived; spatial scores are conditional and potentially leaky. The four folds use fixed surfaces rather than reconstructing source models inside folds.
- Local source hashes were checked, but the USGS/DrivenData/3DHP/GeMS/GeoDAWN pages and raw upstream payloads were not freshly fetched in this pass. The H53 slate keeps their official URLs and marks H53-B/H53-D unavailable pending payload/coverage checks; no unsupported viability claim was added.

## Pass 3 — full acceptance-criteria recheck

- **Unique local TIFF:** content-derived H53 filename, 403,844 bytes, unique from the bounded set of local same-grid files; organizer/other-site uniqueness is unverified.
- **Format:** one-band float32, exact grid, [0,1] finite inside, NaN outside; independent receipt passes.
- **Name/note:** distinct H53-A filename and 133-character note in the build receipt, README, and site.
- **Promotion:** H53-A loses to H49 in mean DTI and in 3/4 folds on each separate SGMC proxy. No promotion, upload, or slot use; H49 remains the best same-protocol public-proxy result, not a private-label/organizer result.
- **Disagreement diagnostics:** H50's `m(Theta)` and raw conflict `K` remain separate downloadable diagnostics; no naive mean was substituted for that work.
- **Site:** one-click H53 download is at the top; gate failure and no-upload instruction are next to it; the portal guide is explicitly reference-only, not authorization.
- **Tests/compile:** `.venv/bin/python -m pytest -o addopts= -q -ra` — 290 passed, 3 skipped, 185 subtests passed. The skips are pipeline tests requiring raw inputs not restored (`scripts/fetch_inputs.sh`). `compileall` and changed-script `py_compile` pass.
- **Decision:** all remaining H53 slate ideas stay parked/unimplemented until their exact data payloads and validation plans are checked. Public proxy results do not authorize any competition slot.
