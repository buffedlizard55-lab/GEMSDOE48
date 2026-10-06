> **Historical archive.** This earlier upstream page is preserved for provenance and may contain superseded claims. Do not treat it as the current submission or validation decision. See the [current overview](../../index.html) and [current validation](../../validation.html).

---

# Irregularities flagged for manual review

| ID | Severity | Finding | Evidence | Action |
|---|---|---|---|---|
| IR-48-01 | High | **The brief's "highest score 0.3195" is stale.** The live board on 2026-10-06 shows #1 xiaofanhu 0.3774, #2 0.3345, #3 0.3262; 0.3195 is #7 | [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) | Target updated to > 0.3774 |
| IR-48-02 | Info | The board lists **extradr19 at 0.2778 (#13)**. That matches the owner-reported best, but whether this is the owner's account is not verified | same | Owner to confirm |
| IR-48-03 | High | **The "two independent families" are not independent.** b2 ⊂ r1 ⊂ d2.8 ⊂ h19-5 exactly. h32-1 shares 36,874 of b2's 37,654 pixels (97.9 %), h33-d 31,614 (84.0 %). This violates Dempster's distinctness assumption | `scripts/build_ds.py` output | Documented. The cautious rule is listed as a next step |
| IR-48-04 | Medium | **Theory correction.** Dempster's rule normalises conflict away. Keeping conflict as unassigned mass is **Yager's** rule | Dempster 1967; Yager 1987 | Both layers published |
| IR-48-05 | High | **The SGMC holdout does not predict live scores** (Spearman −0.17, n = 17; r13-lattice 0.250 proxy vs 0.0904 live). Sibling repos used SGMC-based instruments for promotion | `evidence/proxy_calibration.json` | Not used for selection |
| IR-48-06 | High | **No available instrument ranks within the 0.245–0.278 family.** LSI top-8 LOO Spearman is −0.69. "Beat the holdout" decisions at the ±0.003 scale are therefore not decidable offline | `evidence/lsi_validation.json` | The λ-probe (3 slots) is the fix |
| IR-48-07 | Medium | **Sandbox egress is GitHub/PyPI only.** USGS, AWS, ScienceBase, GDR and DrivenData community all return HTTP 000. Obtainability was checked through the web tool instead | `curl` log in session | Data fetches must run in GitHub Actions |
| IR-48-08 | Low | The uniqueness and "not done before" checks covered 4 cloned sibling repos (80 GeoTIFFs), not all ~47 | `receipt-*.json` | Extend in the next session |
| IR-48-09 | Low | `map_scale = 250` read as 1:250,000 is an interpretation of the field | `gdr_qfaults_traces.csv` | Confirm with USGS Qfault metadata |
| IR-48-10 | Info | `labels.tif` and `existing_faults.tif` mirrors are byte-identical (sha256 `7ba308cc…`) | `registry/data_manifest_gemsdoe32.json` | Expected (same label raster) |
| IR-48-11 | Medium | **Data are owner-supplied GitHub mirrors, not organiser bytes.** No DrivenData login is available here. Integrity rests on the sha256 pins recorded by GEMSDOE32. The scored-file names do not prove which bytes were uploaded | manifest | Owner to confirm the uploaded hashes |
| IR-48-12 | Info | GEMSDOE47 notes that "x at ρ = 8.02" implies an 88 % recall for 0.2778. That conflicts with this repo's LSI estimate (T/K ≈ 0.34). Both are model-dependent | GEMSDOE47 `knowledge/02` | The λ-probe settles it |
| IR-48-13 | **High** | **The file merged to `main` by an earlier session (PR #1, `gemsdoe48-h48-ds-yager-conflict-20261006.tif`, sha256 `fe68ae6f…`) is not recommended.** It down-weights **6,040 of b2's 37,654 live-validated dots to 0.137**, losing ~86 % of their credit by the scale identity. It also adds 10,251 px at 0.086, **3,894 of them within 200 m of the catalogue**, which re-adds the mass whose removal earned +0.0070 live. It was promoted on the SGMC proxy, which does not predict live scores (IR-48-05). LSI predicts 0.2383 for it vs 0.2635 for b2 | `evidence/ds_file_comparison.json` | Kept for audit in `docs/downloads/` + `docs/prev-pr1/`. **The H48-1 file replaces it as the primary download** |
| IR-48-14 | Medium | A third session's PR #2 (b2 × h33-d, `gemsdoe48-ds-dotted-x-tipstepover-20261006T201749Z-95897e3f8125-decision-zeros.tif`, 47,905 px binary) was **merged to main while this session was working**. It carries the same 3,894 flank dots (LSI 0.2590 vs b2 0.2635). Its README called it PRIMARY | `evidence/ds_file_comparison.json` | Kept for audit (`docs/downloads/`, `docs/prev-pr2/`). Superseded as primary by H48-1 |
