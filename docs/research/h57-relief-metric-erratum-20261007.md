# Metric-identity correction — H57 relief-augmented artifact

**Correction date:** 2026-10-07<br>
**Disposition:** **OK TO DOWNLOAD FOR INSPECTION · NOT OK / NOT CLEARED TO SUBMIT. No weekly slot is cleared.**<br>
**Scope:** the distinct H57 Dempster–Shafer/lidar-relief artifact built in the concurrent session on `arena/567db1fc-gemsdoe48`, candidate id `e6b785718c07`. This is not the H57-A radiometric-residual candidate in [`h57-results-20261007.md`](h57-results-20261007.md), nor the separate unbuilt H57-A–E slate in [`h57-hypothesis-slate-20261007.md`](h57-hypothesis-slate-20261007.md). See the namespace note in the [retained original report](h57-ds-relief-augmented-20261007.md).

The original report and receipts are retained for forensic reproducibility. Its prior **SUBMIT RECOMMENDED** verdict and the live-score, marginal-credit, threshold, ceiling, floor, and sensitivity claims below are withdrawn. The primary TIFF remains a reproducible local research artifact; this correction is not organizer verification, a new score, or a claim of scientific performance.

## Why the prior projection is invalid

The old projector inferred hidden-truth totals and a live-equivalent score by substituting `FPw = S − TPw`. The official metric instead defines prediction-centred `FPw = S − Q`, while truth-centred `TPw = T`; `Q` and `T` maximize over different axes and are not generally equal. Consequently the inverse fit does not identify `T`, `|G|`, hidden-truth density, false-positive mass, or a transferable live score. The owner-reported 0.2600 → 0.2708 → 0.2778 ladder is not file-attributed to the exact local B2 TIFF bytes, so it cannot validate the fitted constants either. See [`metric-identity-erratum-20261007.md`](metric-identity-erratum-20261007.md).

The following quantities in the original H57 report and `evidence/build_h57_receipt_20261007.json` are therefore **INVALIDATED / FORENSIC ONLY** and must not be used as score estimates, a candidate ranking, or a submission gate:

- the fitted `T_live = 0.9324 × T_SGMC` scale and any use of the 62,122-cell SGMC proxy mask as a substitute for live truth (62,122 is a count on the public proxy, not a measured private-label count);
- the fitted denominator constant `11,215.3` and `DTI(S) = T_live(S) / (0.2·|S| + 11,215.3)`;
- the parent value `0.2744`, candidate projection `0.3844`, “all-new-dots-worthless” floor `0.2254`, and scale-sensitivity/break-even scenario;
- the `0.0549` per-dot threshold, `0.1781` marginal live-credit-per-dot figure, its `3.24×` ratio, and all “PASS” labels or 3/4-fold promotion conclusions that depend on that threshold;
- deductions that the owner-reported ladder proves catalogue-flank pruning, that excluded dots had near-zero live credit, or that a 0.2778 ceiling/headroom/leaderboard reachability follows from the fit.

The corrected builder no longer generates those projections as current evidence. The archived build receipt preserves the original numbers with an explicit invalidation record; they are not recomputed or endorsed.

## What remains in the record

- **Artifact identity:** `docs/downloads/GEMSDOE48-H57-ds-relief-augmented-20261007-e6b785718c07.tif`, SHA-256 `28a51fb032b8f2cfd1f04ad3bd429c29d7bb780d36961fea783ff8099130986e`. The recorded format and bounded local uniqueness checks are local audits only; portal acceptance and organizer-side uniqueness were not tested.
- **Construction:** a normalized Dempster–Shafer belief surface and a separately selected binary emission are retained as the historical recipe. The reported `m(Θ)` is residual unassigned/ignorance mass, not conflict or direct family disagreement; raw conflict `K` is a separate diagnostic. The belief surface differs from the arithmetic mean, which is a construction check, not evidence of improved prediction.
- **Public-proxy arithmetic:** recorded `T_SGMC`/block computations may be reproduced as conditional measurements on the named public proxy and the exact code/data recipe. They do not estimate private-label or live leaderboard performance. The old per-dot comparison and PASS/FAIL interpretation are withdrawn.
- **Source provenance:** the prior report cites a USGS 3DEP staging-bucket URL pattern and a local 100 m scarp mosaic receipt. This repository record is not an independent re-fetch, source-authentication, complete-coverage, or licence/use-rights audit. No source-specific DOI or challenge-use permission is established here.

## Correct disposition

The prior four-block calculation is not the required comparable promotion holdout: its pass labels depended on the invalid universal break-even threshold and it did not establish a like-for-like win over the current H49 reference under both frozen proxy regimes. No candidate in this record is cleared to spend a weekly slot. Any future evaluation needs a freshly derived, independently checked metric protocol and spatially blocked comparisons against the current comparable H49 best, plus source and format review. A public-proxy result would still not be organizer acceptance or private-label evidence.

The dated leaderboard is context only: the 2026-10-07 snapshot recorded 0.3774 at #1, 0.3195 at #7, and the 0.2778 `extradr19` row at #13. No receipt links any row or owner-reported ladder to the exact local artifact bytes.
