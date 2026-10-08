# Retired Gate-2 / credit-density audit — invalidated 2026-10-07

> **INVALIDATED — FORENSIC RECEIPTS ONLY. No result in the former Gate-2 audit is a promotion-grade pass/fail or a claim about hidden/private truth.** The historical density-matching protocol derived a notional live-truth count from owner-reported scores using `FPw = S − TPw`; that is generally false for the official metric. The same protocol then treated `0.05556` as a universal per-cell break-even threshold. Neither basis is valid as a general promotion rule. Do not interpret old `PASS_MASS_NEUTRAL` / `FAIL_MASS_NEUTRAL` values as current clearance.

## What was invalidated

The earlier version of this report treated the following as measured or decision-ready. They are **historical calculations under a now-invalid assumption**, not established facts:

- SGMC public-proxy density compared with a purported live hidden-truth density of about 14,307 pixels;
- the resulting density-matched proxy means, marginal-credit figures, and candidate verdicts;
- the universal `0.05556` per-cell bar and the associated raw-proxy scaling;
- inferred hidden-truth counts, inverted true-positive totals, live-equivalent scenarios, reachability/ceiling statements, and H55's mass-neutral verdict;
- any conclusion that these quantities establish a general promotion gate or private-label performance.

For the exact metric and a counterexample showing why `FPw = S − TPw` fails, see the [metric-identity erratum](metric-identity-erratum-20261007.md). In the official metric, `TPw = T` is truth-centred and `FPw = S − Q` is prediction-centred; `Q` and `T` are generally unequal. An owner-reported leaderboard value and emitted-pixel count do not identify the hidden truth count.

## What remains reproducible

The original JSON receipts and candidate rasters are retained as dated forensic artifacts. They document what the old implementation computed, but the stored values must be read with the invalidation fields and this warning:

- [`evidence/credit_density_audit_20261007.json`](../../evidence/credit_density_audit_20261007.json) — historical summary table and protocol inputs.
- [`evidence/audit_gate2_h55_20261007.json`](../../evidence/audit_gate2_h55_20261007.json) — H55's historical equal-mass delta `−0.002014`, density-matched credit `0.010245`, and old `0.05556` threshold; **not a valid promotion decision**.
- [`evidence/live_ladder_20261007.json`](../../evidence/live_ladder_20261007.json), [`evidence/live_model_calibration_20261007.json`](../../evidence/live_model_calibration_20261007.json), and [`evidence/lam3_residual_probe_20261007.json`](../../evidence/lam3_residual_probe_20261007.json) — historical inversions/fits and downstream scenarios, invalidated for score estimation and promotion.
- [`scripts/audit_candidate.py`](../../scripts/audit_candidate.py) — refuses to run unless `--legacy-audit-only` is supplied. That option reproduces the former calculations for forensic comparison only; its output is not a gate.
- [`scripts/calibrate_live_model.py`](../../scripts/calibrate_live_model.py), [`scripts/live_ladder_analysis.py`](../../scripts/live_ladder_analysis.py), and [`scripts/lam3_residual_probe.py`](../../scripts/lam3_residual_probe.py) — historical model tools; their score-inversion outputs must not be used as truth estimates or promotion evidence.

Equal-emitted-mass scores and ordinary blocked-holdout scores against the named public masks are direct **public-proxy observations** under their recorded evaluation protocol. They are not private-label scores, a hidden-truth density estimate, an organizer score, or proof that an equal-mass gate is sufficient for promotion. Random controls remain useful diagnostics, but cannot rehabilitate the invalid density conversion or threshold.

## Current decision and replacement requirements

**No candidate has a promotion-grade Gate-2 pass. No weekly submission slot is cleared.** The H56B, H56 open-world, H56-F, and current-branch H57-A evidence is summarized in the [current validation page](../validation.html); those reports compare candidates with H49 on fixed public proxies and are explicitly conditional diagnostics. A separate H57-RELIEF artifact has a dedicated [metric-identity erratum](h57-relief-metric-erratum-20261007.md); its old live projection is withdrawn.

Before any future Gate-2-style policy can be used for promotion, its estimand and pass rule must be re-derived without inferring private truth density from an unverified score. It must be validated against synthetic cases with known truth, checked against the exact official `T` and `Q` computations, compared on spatially blocked public proxies, and reviewed separately from portal acceptance and owner slot authorization. Until that work is completed, the legacy tool and its PASS/FAIL labels cannot clear a candidate.
