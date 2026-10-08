# Agent start here

Read `README.md` in full before changing this project. Preserve both the current H48 research workflow and the historical upstream experiments; do not conflate their outputs or scoring protocols.

- Never call a public-proxy score an organizer score or private-label validation.
- Do not spend a competition slot unless a candidate beats the current best under comparable spatially blocked semantics and the source construction is defensible against leakage.
- **Gate-2 (2026-10-07, required policy; historical calibration currently unusable).** Proxy comparisons at unequal emitted mass can be misleading; an archived control (C + 18,000 random cells) scored 0.1189 vs C 0.0956 on the frozen SGMC proxy. The original `scripts/audit_candidate.py` protocol uses an inferred live-truth count of 14,307 and treats 0.0556 as a universal live break-even bar. The metric-identity erratum invalidates that inferred count and the universal interpretation of the bar. Preserve the Gate-2 safeguard and equal-mass/random-control intent, but **do not use the old audit script's PASS/FAIL, density-matched score, or 0.0556 threshold to promote a candidate** until the protocol is re-derived and validated without the invalid inversion. No candidate can be promoted under current evidence. Any older "+delta, 4/4 folds" claim predating Gate-2 still requires remeasurement; a public-proxy pass alone is never private-label validation or organizer acceptance.
- Do not overwrite the primary candidate without rebuilding its receipt, independent format audit, and blocked evidence.
- Candidate downloads are built with `scripts/build_submission.py`; the prior alpha=.99 pipeline is preserved at `scripts/previous_build_submission.py`.
- The current static pages are manually maintained; update them alongside `docs/research/` and the evidence receipts when results change. Historical upstream pages are under `docs/archive-main-pages/`.
- Run `python -m pytest -q`, compile checks, and the relevant artifact validators before proposing a merge.
