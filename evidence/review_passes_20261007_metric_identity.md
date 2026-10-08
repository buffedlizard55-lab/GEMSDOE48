# Three cumulative review passes — metric-identity correction and archive safety

**Date:** 2026-10-07 (America/Los_Angeles; final local audits continued through 2026-10-08 UTC)<br>
**Reviewer:** Arena coding agent (sequential self-review; not independent human, organizer, or scientific peer review)<br>
**Scope:** preserved README brief and active pages; H49–H57 historical evidence; Gate-2/H55/H57 builders, receipts, and tests; Dempster–Shafer semantics; local artifact/link/format checks. The existing merge of `origin/main` is being resolved on `arena/068cab7d-gemsdoe48`; no other branch was used.

## Pass 1 — metric algebra, thresholds, builders, and receipts

- Rechecked the official weighted-metric terms against `src/gemsdoe48/metric.py` and the explanatory counterexample: `TPw=T` is truth-centred, `FPw=S−Q` is prediction-centred, and `T` and `Q` maximize over different axes. Therefore the old `FPw=S−TPw` inversion does not identify private truth density, per-cell live credit, a ceiling, a floor, a score scenario, or leaderboard reachability.
- Audited Gate-2 receipts, H55/H56 live-model records, H49 proxy/calibration JSON, H57-RELIEF's prior build receipt, and their downstream documentation. The inferred 14,307-cell Gate-2 live-truth count, universal 0.05556/0.0549 bars, H55 0.2843 ceiling, H56B 0.0649 projection, H57-RELIEF 0.3844 projection, inferred counts, live-equivalent scenarios, and dependent PASS/FAIL/recommendation fields are now labelled invalid/forensic-only and are not promotion evidence. Directly measured public-proxy values remain scoped to their recorded protocol.
- Rewrote `evidence/RECEIPT_GENERATIONS.md` so neither historical Gate-2 generation is presented as a current/authoritative promotion gate. The rollup and all 17 individual audit receipts carry invalidation status and preserved legacy verdict fields; `scripts/audit_candidate.py` requires explicit `--legacy-audit-only` for forensic reproduction.
- Corrected the H57-RELIEF builder so it emits no score inversion, private-truth density, threshold, ceiling, floor, or recommendation. Its default artifact and receipt output is the ignored `scratch/h57-relief-rebuild/` directory, so it cannot silently overwrite the dated download or historical evidence receipt. Regression tests check these safeguards.
- Corrected the H56B builder's total-conflict handling: normalized Dempster combination raises at total/numerical conflict instead of silently substituting vacuous mass. Regression coverage now agrees with the shared Dempster implementations.

## Pass 2 — attribution, scientific scope, and user-facing status

- Re-read the current README and its preserved original brief, executive/submission guidance, active overview/research/hypothesis/validation pages, and the full H55/H56/H57 reports and errata. The dated 2026-10-07 leaderboard context remains #1 `0.3774`, #7 `0.3195`, and #13 `0.2778` (`extradr19`). The owner-reported 0.2600→0.2708→0.2778 ladder and 0.2778 row remain **unverified at local-file level**; no receipt links them to exact local B2 bytes.
- Kept three H57 namespaces distinct: the earlier 17:43 H57-A–E unbuilt slate; the current-branch H57-A screen, which failed the two-proxy/random-control review and emitted no TIFF; and the separate H57-RELIEF TIFF, whose old live projection/recommendation are withdrawn. H56-F's three preregistered pruning failures are preserved as public-proxy results. No weekly slot is cleared.
- Confirmed conspicuous, unambiguous artifact wording: **OK TO DOWNLOAD FOR INSPECTION · NOT OK / NOT CLEARED TO SUBMIT.** Local SHA/format/uniqueness checks do not establish organizer acceptance or a score. H57-RELIEF's local TIFF SHA-256 remains `28a51fb032b8f2cfd1f04ad3bd429c29d7bb780d36961fea783ff8099130986e`.
- Checked Dempster–Shafer semantics throughout: `m(Θ)` is residual unassigned/ignorance mass; raw `K` is pre-normalization conflict; any absolute support-difference raster is a separate non-mass diagnostic. No page treats `m(Θ)` alone as direct source disagreement or a probability.
- Preserved the four-hypothesis current H57 slate and the separate five-hypothesis earlier slate with planning-only ranges, data-readiness caveats, and blocked-H49 gates. Public-source availability is not represented as source-byte authentication, complete target coverage, challenge-use rights, private-label evidence, or organizer acceptance.
- Corrected the broken relative link from `docs/sources.md` to the H56B-NF TIFF and made the H56B review verdict explicitly “NOT CLEARED TO SUBMIT.”

## Pass 3 — reproducibility, regression, and packaging

- Full suite: `./.venv/bin/python -m pytest -q -ra` — **passed; 3 skipped** because raw-input pipeline mirrors are not restored. (The skips are reported, not counted as successes.)
- JSON parse audit: **194 files, 0 errors**.
- Python syntax audit: `python3 -m compileall -q scripts src tests` — passed.
- Active HTML local-link audit: **36 files, 563 local references, 0 missing** (archived-main-page snapshots excluded).
- Maintained Markdown local-link audit: **58 files, 391 local references, 0 missing** (includes README, AGENTS, maintained docs and evidence notes; visibly archived/previous-PR snapshots excluded).
- H57-RELIEF local format validator: `PASS_LOCAL_FORMAT_AUDIT_NOT_ORGANIZER_ACCEPTANCE`, one-band float32 EPSG:32611, 3,730×3,292, all values finite/in `[0,1]`, 58,031 positive cells; SHA-256 matches the report. This is a local check, not a portal test.
- Refreshed bounded uniqueness comparison: **99 local TIFFs scanned**, no byte- or support-identical duplicate in the configured scan. The receipt now explicitly states `organizer_uniqueness_tested=false` and `global_uniqueness_established=false`.
- Full/staged diff checks are completed before the merge commit. The incoming mainline registry timestamp is retained in the merge index; the unrelated pre-existing timestamp edit is not staged and will be restored from `stash@{0}` after the merge commit.

## Disposition and remaining limitations

No candidate has a promotion-grade Gate-2 pass and no weekly slot is cleared. H57-RELIEF is available only for inspection. The raw-input end-to-end pipeline cases are skipped because their source mirrors are absent; no private labels, organizer scoring, portal acceptance, organizer-side uniqueness, source-license clearance, or exact local-file-to-leaderboard linkage has been established. A future candidate still needs an independently derived/validated metric gate, a comparable spatially blocked win, source/provenance review, and explicit owner clearance.
