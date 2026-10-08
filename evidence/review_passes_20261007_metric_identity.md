# Three cumulative review passes — metric-identity correction and archive safety

**Date:** 2026-10-07
**Reviewer:** Arena coding agent (sequential self-review; not independent human, organizer, or scientific peer review)
**Scope:** README/current pages, archived research pages, metric-inversion tools and receipts, H50–H57 evidence summaries, and regression/format/link checks. The unrelated pre-existing `registry/inputs.json` worktree change was intentionally left unstaged.

## Pass 1 — metric algebra, thresholds, and executable paths

- Rechecked the metric distinction used across the errata and code: `TPw=T` is truth-centred; `FPw=S−Q` is prediction-centred; `T` and `Q` maximize over different axes and are not generally equal. The old `FPw=S−TPw` substitution therefore does not identify hidden-truth counts, per-dot credit, recall, ceilings, or leaderboard reachability.
- Audited Gate-2, H55/H56 live-model outputs, the H52 ladder calculation, and H50/H53 narratives for dependent values: the 14,307 inferred Gate-2 mass, universal `0.0556`/`0.052` thresholds, 0.2843 ceiling, 0.0649/0.2747 projections, and associated score/reachability scenarios are marked invalid/forensic and no longer used as promotion evidence.
- Corrected residual H50 binary-optimality and credit-bar language; H52/H56 historical ladder interpretations and kill rules; H53's “new signal required” conclusion; and H49's live-change/resolution bracket. Public-proxy fold results remain only as protocol-specific measurements.
- Verified regression coverage for explicit forensic opt-in, default refusal of the retired DS48 site builder, guarded README commands, and archived-page notices.

## Pass 2 — attribution, scientific scope, and user-facing status

- Re-read the current README status, original-brief appendix, executive summary, submission guide, research summaries, dated leaderboard context, and the old H49–H57 slates/results.
- Confirmed the 2026-10-07 leaderboard snapshot remains dated context (#1 `0.3774`, #7 `0.3195`, #13 `0.2778`/`extradr19`). The `0.2778` row and owner-reported A/B/C ladder remain **unverified at local-file level**; no exact file-to-score or private-label claim is made.
- Kept H56B's **OK TO DOWNLOAD FOR INSPECTION · NOT OK / NOT CLEARED TO SUBMIT** verdict conspicuous. No candidate is cleared; H56-F's three threshold outcomes and H57-A's failed two-proxy/control comparison are preserved as measured public-proxy results, not organizer scores.
- Checked Dempster–Shafer wording: `m(Θ)` is residual unassigned/ignorance mass; raw `K` is conflict; direct parent-support difference is a separate non-mass diagnostic. Updated README H50 wording and retained naive-mean comparisons.
- Confirmed former README/site content and the original prompt are preserved in the dated archive/appendix with visible historical/forensic notices; current Markdown paths point to maintained pages rather than stale H48/H50 recommendations.

## Pass 3 — reproducibility, regression, and packaging

- Full tests: `./.venv/bin/python -m pytest -q` — **passed; 3 skipped** (the repository's raw-input pipeline cases).
- JSON parse audit: **168 files, 0 errors**.
- Python compile audit: `python3 -m compileall -q scripts src tests` — passed.
- Active HTML link audit: **36 files, 540 local references, 0 missing**.
- Current Markdown link audit: **40 files, 326 local links, 0 missing** (README and maintained Markdown; excludes visibly archived `docs/archive-main-pages/` and `docs/prev-pr*` snapshots).
- `git diff --check` — passed. Builder/CLI regression tests confirm the retired DS48 generator writes nothing and invalidated inversion commands refuse by default unless an explicit `--legacy-audit-only` flag is supplied.
- No TIFF, private-label data, or generated large dataset was created by these review changes. `registry/inputs.json` remains a pre-existing, unstaged worktree change.

## Disposition

The historical numerical receipts remain available for forensic reproducibility, not decision evidence. Current clearance still requires a comparable blocked-holdout win and a newly derived, validated mass-neutral audit independent of the invalid score inversion. No organizer acceptance, private-label performance, or local-file-to-leaderboard linkage is established.
