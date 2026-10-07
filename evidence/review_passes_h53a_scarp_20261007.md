# H53-A end-to-end review log — 2026-10-07 UTC (post-merge continuation)

## Pass 1 — implementation and verification

- Kept the H53-A slate frozen and implemented no new H53-B/C/D or raw-DEM H53-2 candidate. The merge preserves main's separate H53-1 fusion and records H53-A alongside it without replacing its canonical receipts.
- Rebuilt H53-A from the locally hash-pinned H52-derived 3DEP raster, dotted parent C, public catalogue exclusion mirror, and footprint. Deterministic rebuild reproduced the same candidate SHA-256 `de35531d386792da1950eac815f98db8f36304f78debb6b568138d070640d9bd` and 12,000 additions.
- Re-ran the independent local submission validator: one-band float32, 3,730 × 3,292, EPSG:32611, 100 m, in-footprint range [0,1], NaN outside. This is not organizer acceptance.
- Re-ran `scripts/compare_h53a_scarp_with_h49.py` after merge. It verifies candidate/label/SGMC hashes and matching fold geometry, evaluation domain, and DTI semantics. Both SGMC comparisons still fail the preregistered promotion gate; the regenerated report now points only to namespaced H53-A reports. No submission slot was used.
- After merging PR #12's H53-1 artifacts, reran the bounded scan: 65 local TIFFs attempted and 61 one-band rasters on the exact comparison grid. No exact in-footprint value or positive-support match was found; the closest is intended parent C (positive-support Jaccard 0.758327627). This is not a global uniqueness proof.
- Updated README, landing page, executive summary, method, validation, hypotheses, research status, next steps, submission guide, and retired `docs/md/index.md` pointers to keep H53-A and H53-1 distinct and make the no-upload decision prominent. `docs/md/index.html` does not exist and is not a build input. H50/H53 Dempster-Shafer diagnostic deliverables remain linked separately.

## Pass 2 — bug, assumption, edge-case review

- Reviewed the strike-bin quantization, unoriented 0°/180° wrap, deterministic integer offsets, support-count threshold, stable score tie-break, 200 m exclusions, and NaN-outside export. Confirmed the actual stored `strike_at` values are 0, 15, …, 165 degrees after scale decoding; the source does retain only one best strike per 100 m cell.
- Found and fixed an edge case in the Poisson thinning helper: a zero-cell budget could previously keep one cell. Added zero-budget, occupied-cell, Euclidean-spacing, malformed-shape, and out-of-bounds tests. The frozen 12,000-cell build and TIFF bytes are unchanged.
- Made the bounded identity auditor's optional candidate path safe when supplied outside the checkout; its report still limits its scan to local `docs/downloads/` and `data/`.
- The frozen construction permits qualifying source samples outside the official output footprint to support an in-footprint center; only candidate centers and emitted predictions are footprint-masked. The regional product has valid data beyond that footprint. This is a construction assumption, not a footprint-output violation, and source cells are not independent observations.
- Construction uses the full public catalogue as a distance-exclusion mask and parent C is catalogue-derived; spatial scores are conditional and potentially leaky. The four folds use fixed surfaces rather than reconstructing source models inside folds.
- Local source hashes were checked. Official DrivenData submission rules, USGS 3DEP products, and USGS 3DHP access pages were freshly retrieved; they do not verify the exact local 3DEP mosaic tiles or footprint coverage. GeMS/SGMC and GeoDAWN DOI metadata and raw source payloads were not freshly retrieved. The slate keeps H53-B/H53-D parked pending exact payload/coverage checks; no unsupported viability claim was added.

## Pass 3 — full acceptance-criteria recheck

- **Unique local TIFF:** content-derived H53 filename, 403,844 bytes, unique from the bounded set of local same-grid files; organizer/other-site uniqueness is unverified.
- **Format:** one-band float32, exact grid, [0,1] finite inside, NaN outside; independent receipt passes.
- **Name/note:** distinct H53-A filename and 133-character note in the build receipt, README, and site.
- **Promotion:** H53-A loses to H49 in mean DTI and in 3/4 folds on each separate SGMC proxy. No promotion, upload, or slot use; H49 remains the best same-protocol public-proxy result, not a private-label/organizer result.
- **Disagreement diagnostics:** H50's `m(Theta)` and raw conflict `K` remain separate downloadable diagnostics; no naive mean was substituted for that work.
- **Site:** H53-A's separate one-click research download and do-not-upload decision lead the landing page; H53-1 remains separately linked with its own results and diagnostics. The portal guide is explicitly reference-only, not authorization.
- **Tests/compile/links:** `PYTHONPATH=src .venv/bin/python -m pytest -o addopts= -q -ra` — 300 passed, 3 skipped, 185 subtests passed. The skips are pipeline tests requiring raw inputs not restored (`scripts/fetch_inputs.sh`). `compileall`, changed-script `py_compile`, and a nine-page local path/HTML-fragment audit pass.
- **Decision:** all remaining H53 slate ideas stay parked/unimplemented until their exact data payloads and validation plans are checked. Public proxy results do not authorize any competition slot.
