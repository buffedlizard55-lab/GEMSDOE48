# Gate-2 receipt generations — forensic index only

> **No Gate-2 receipt is currently authoritative for promotion.** Both the pre-patch and patched
> 2026-10-07 JSON generations record historical tool output. The patched set is more complete as a
> record of what the script computed, but its inferred 14,307-pixel live-truth density and
> universal 0.0556 break-even depend on the invalid `FPw = S − TPw` substitution. All prior
> PASS/FAIL, density-matched values, thresholds and promotion interpretations are
> **INVALIDATED / FORENSIC ONLY**. See [`docs/research/credit-density-audit-20261007.md`](../docs/research/credit-density-audit-20261007.md)
> and [`docs/research/metric-identity-erratum-20261007.md`](../docs/research/metric-identity-erratum-20261007.md).

| generation | file pattern | current use |
|---|---|---|
| pre-patch | `audit_*_gate2_20261007.json` (5 files) and `audit_b2_02778_tif_gate2_20261007.json` | Retained as historical output; not current clearance. |
| patched | `audit_gate2_<tag>_20261007.json` and related rollups | More complete historical reproduction; explicitly invalidated for promotion and private-truth inference. |

Index of the old rollup: [`evidence/credit_density_audit_20261007.json`](credit_density_audit_20261007.json). Its opening warning, per-result `validity_status`, and invalidation reason govern every embedded verdict/value. The frontier probe [`evidence/lam3_residual_probe_20261007.json`](lam3_residual_probe_20261007.json) is likewise forensic-only.

## Pre-patch files, retained (do not quote as decisions)

- `evidence/audit_gemsdoe48_h49_ds_conflic_gate2_20261007.json`
- `evidence/audit_gemsdoe48_h50_ds_b2xh36r_gate2_20261007.json`
- `evidence/audit_gemsdoe48_h51_plausibili_gate2_20261007.json`
- `evidence/audit_h52_gate2_20261007.json`
- `evidence/audit_b2_02778_tif_gate2_20261007.json` (recorded a near-zero delta for identical support)

They predate the later audit implementation; their verdicts/bars remain historical output only. The patched receipts are also not a valid gate despite being the more complete record. Regression coverage asserts that receipts preserve their former verdicts only as `legacy_verdict` and mark their current `verdict` invalidated.

## Required before any replacement gate

Re-derive the estimand without inferring private-label truth density from an unverified score; validate against synthetic cases with known truth; independently check the exact official `T` and `Q` computations; then evaluate frozen, comparable public-proxy holdouts. Until those steps are complete, no candidate has a promotion-grade Gate-2 pass or a weekly-slot clearance.
