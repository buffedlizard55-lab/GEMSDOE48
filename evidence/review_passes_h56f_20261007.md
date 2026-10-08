# Three review passes — H56B/H56-F follow-up (2026-10-07 UTC)

## Scope and status

This follow-up audited the project brief retained in `README.md`, the H56B Dempster-belief artifact, the H56-F pruning hypothesis, the same-protocol blocked-proxy receipt, and the active landing/validation/submission/research pages. No competition slot was used. This is a research/documentation/code change; it does not assert organizer acceptance or private-label validation.

## Pass 1 — implement and verify

- Read the full `README.md` and preserved brief before editing.
- Added `src/gemsdoe48/h56f.py` and `scripts/evaluate_h56f_pruning.py` for the frozen 0.90/0.95/0.99 dotted-parent-only pruning ladder; thresholds cannot add cells or alter the parent.
- Rebuilt H56B with `scripts/build_submission_h56_belief.py`; primary zeros-outside TIFF SHA-256 remained `4d6548d4ec07a47a25b83d28ebc05d58b57448c1507b460aed52cec395bdb6b5`. Added a fourth diagnostic, direct support-field difference `|s_dot - s_tip|`, separate from residual `m(Theta)` and pre-normalization conflict `K`.
- Changed the NaN-outside twin to declare `nodata=NaN`; it now passes the masked local format checker. The zeros-outside candidate passes the whole-raster `[0,1]` check. Neither result establishes portal acceptance; the former can fail an unmasked NaN range check and the latter does not follow official null/NaN outside-bounds wording.
- Evaluated the frozen ladder with the same four-quadrant/core-plus-300 m-halo DTI protocol used for the H49 reference; wrote `evidence/h56f_pruning_holdout_20261007.json` and its research report. Every rung is below H49 on both public-map proxies in all four folds.
- Updated the root brief, current HTML pages, source bibliography, and H56 validator to make the download/submit distinction explicit and not authorize a slot based on the retired live-model projection.

## Pass 2 — assumptions, bugs, and edge cases

- Re-read the official DTI equations and found the old score-like projection used the generally invalid identity `FPw = S - TPw`. Retired the 0.0649 projection and removed it as a submission gate; preserved its prior analysis only with correction banners/errata.
- Corrected evidence semantics in `src/gemsdoe48/evidence.py`, `src/gemsdoe48/dempster_shafer.py`, the H56B builder, site copy, and source notes: normalized Dempster combination divides by `1-K`; `m(Theta)` is residual ignorance under the chosen BPAs, not a direct disagreement map; raw pre-normalization `K` and direct support disagreement are separately identified.
- Reconciled the H56-F report table against the machine receipt; corrected the H56B row to catalogue `0.032347` and SGMC-off `0.070552` (not the stale `0.032069` / `0.073501`). Added a report-to-receipt regression test.
- Fixed the malformed validation holdout list item, removed obsolete “G3 FAIL” wording, and replaced unsupported leaderboard score-inversion/reachability prose with the dated public snapshot and attribution caveats. The current page states #1 `0.3774`, #7 `0.3195`, and #13 `extradr19` `0.2778`; none is an exact local TIFF receipt.
- Audited active copy for stale 0.0649, 0.2843, 0.0556, “format PASS,” and disagreement terminology. Historical model quantities are marked retired; local checks are not represented as portal acceptance. Added a correction banner to preserved H55/H56 frozen slates rather than silently rewriting their historical preregistrations.
- HTML structure check (Python standard-library parser): no mismatched or unclosed tags in `index`, `executive-summary`, `submission-guide`, `validation`, `hypotheses`, `method`, `next-steps`, `leaderboard`, `research`, or `sources`.

## Pass 3 — end-to-end acceptance recheck

- Re-ran the H56B builder; the primary candidate hash is stable. Re-ran the H56-F evaluator; the machine receipt remains `OFFLINE_SPATIAL_PROXY_TEST_ONLY_NOT_SLOT_CLEARED`.
- Revalidated the zeros-outside primary and NaN/nodata twin independently with `scripts/validate_submission.py`; both pass their respective *local* encoding checks, with the known outside-bounds / unmasked-NaN trade-off recorded.
- Focused tests: `tests/test_h56.py`, `tests/test_h56f.py`, `tests/test_site_h56.py`, `tests/test_site_h55.py`, `tests/test_leaderboard.py`, `tests/test_metric_identity.py` — passed.
- Full suite: `.venv/bin/python -m pytest -o addopts='' -q` — **372 passed, 3 skipped, 185 subtests passed**.
- `git diff --check` passed. Local uniqueness remains bounded to this repository's audited file set. H53 already contains a Dempster diagnostic for B2 × H33-D; H56B is a distinct parameterized artifact, not a novel fusion concept.

## Remaining limitations / next work

1. Neither variant has been accepted by the competition portal. Do not submit either: H56B and H56-F lose to H49 on the tested proxies, and the public proxies are not private-label validation.
2. The public leaderboard does not map team rows to TIFF hashes; B2's 0.2778 remains owner-reported with unresolved exact-byte attribution.
3. Source-mirror licensing, organizer authenticity, potential spatial leakage from frozen full-scene masks, and global uniqueness remain unverified.
4. Next candidate work should preregister a new geological signal (the H56-C 3 m DEM channel-knickpoint idea is a candidate, not a validated detector), use independent lineage and leakage reviews, equal-mass controls, and the same/fresh spatial blocks before considering any slot.
5. PR/merge state is tracked outside this review note; no claim of merge or portal submission is made here.
