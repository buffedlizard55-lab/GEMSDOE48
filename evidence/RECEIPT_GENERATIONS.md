# Audit receipt generations (read before citing anything in `evidence/`)

The mass-neutral audit tool (`scripts/audit_candidate.py`) was patched during the 2026-10-07
session. Two generations of receipts exist on disk; **only one is authoritative.**

| generation | file pattern | status |
|---|---|---|
| pre-patch | `audit_*_gate2_20261007.json` (5 files) and `audit_b2_02778_tif_gate2_20261007.json` (single `break_even_bar_per_cell` = 0.0191, tolerance −0.001) | **SUPERSEDED — never cite.** Kept only so the change is auditable. |
| patched (authoritative) | `audit_gate2_<tag>_20261007.json` (11 files, two bars 0.01912 / 0.0556, tolerance −0.002, `--support-threshold`, `--random-control`) | current |

Index of the authoritative set: `evidence/credit_density_audit_20261007.json`.
Frontier probe (does *any* new dot pay?): `evidence/lam3_residual_probe_20261007.json`.
Document: `docs/research/credit-density-audit-20261007.md`.

## The pre-patch receipts, listed (do not quote)

- `evidence/audit_gemsdoe48_h49_ds_conflic_gate2_20261007.json`
- `evidence/audit_gemsdoe48_h50_ds_b2xh36r_gate2_20261007.json`
- `evidence/audit_gemsdoe48_h51_plausibili_gate2_20261007.json`
- `evidence/audit_h52_gate2_20261007.json`
- `evidence/audit_b2_02778_tif_gate2_20261007.json` (wrote a 1.4e-17 delta for an identical support)

They were produced before `decide()` was extracted and before the density-matched (live-scaled)
bar existed; their verdicts and bars are wrong, so any number taken from them is invalid. They are
left in place deliberately (removing them silently would hide the correction); a test
(`tests/test_audit_candidate.py::test_gate2_receipts_are_internally_consistent`) globs only the
authoritative pattern, so the superseded files cannot leak into checks.
