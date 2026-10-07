# Agent start here

Read `README.md` in full before changing this project. Preserve both the current H48 research workflow and the historical upstream experiments; do not conflate their outputs or scoring protocols.

- Never call a public-proxy score an organizer score or private-label validation.
- Do not spend a competition slot unless a candidate beats the current best under comparable spatially blocked semantics and the source construction is defensible against leakage.
- **Gate-2 (2026-10-07, required).** Proxy comparisons at unequal emitted mass are invalid: the frozen SGMC
  off-catalogue proxy is ~4.3× denser than the live truth, so random mass wins it (C + 18,000 random cells =
  0.1189 vs C 0.0956). Run `python scripts/audit_candidate.py <candidate>.tif --receipt <receipt>` before any
  promotion claim: equal-mass credit density must be within −0.002 of the incumbent and added cells must earn
  ≥ 0.0556 marginal credit per cell on a density-matched truth (≈0.24/cell on the raw proxy). Any older
  "+delta, 4/4 folds" claim that predates Gate-2 must be re-measured, not quoted.
- Do not overwrite the primary candidate without rebuilding its receipt, independent format audit, and blocked evidence.
- Candidate downloads are built with `scripts/build_submission.py`; the prior alpha=.99 pipeline is preserved at `scripts/previous_build_submission.py`.
- The current static pages are manually maintained; update them alongside `docs/research/` and the evidence receipts when results change. Historical upstream pages are under `docs/archive-main-pages/`.
- Run `python -m pytest -q`, compile checks, and the relevant artifact validators before proposing a merge.
