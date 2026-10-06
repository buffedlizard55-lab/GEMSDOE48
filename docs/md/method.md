# Method, the 0.2778 autopsy, and validation

Evidence classes used on this page: **[MEASURED]** = computed this session by code in this repo
from hash-pinned bytes. **[OWNER-REPORT]** = live score pasted by the project owner (DrivenData
history needs a login, so we cannot re-verify it). **[OFFICIAL]** = quoted from a DrivenData or
USGS page, linked.

## 1. The metric [OFFICIAL]

From [page 967](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric):
`k(d) = max(1 − d/300 m, 0)`, `DTI = TP_w / (TP_w + 0.2·FP_w + 0.8·FN_w)`. It is implemented in
`src/gems48/metric.py` and tested against a literal O(N²) transcription and the organiser's
worked example (3.00 / 1.89 / 2.00 → 0.60) in `tests/test_metric.py`.

Two consequences, both algebraic:

* **Scale identity.** `T` and `F` are degree-1 in `p`, so for a fixed support `DTI(λp)` increases
  with λ. Binary 0/1 values beat graded values on the same support. That is why the shipped file
  is binary, and why the normalised belief is published as a *diagnostic layer* rather than as
  the emission.
* **Marginal rule.** A unit dot with kernel credit `k` pays only if `k > α·DTI` = 0.0556 at
  0.2778.

## 2. Why h33-2-b2 scored 0.2778 — the highest in the GEMSDOE family [MEASURED + OWNER-REPORT]

Re-measured from the bytes (`b2_02778.tif`, sha256 `c55bafc4…`):

| raster | dots | live | relation (exact set algebra, measured) |
|---|---:|---:|---|
| h19-5 backbone | 121,131 | 0.1922 | ridge backbone |
| d2.8 | 44,090 | 0.2600 | ⊂ h19-5 (Poisson-disk thin, min spacing √8 px) |
| h27-4-r1-solo | 40,199 | 0.2708 | ⊂ d2.8 (3,891 dots removed) |
| **h33-2-b2** | **37,654** | **0.2778** | ⊂ r1 (the 2,545 dots with d(catalogue) ≤ 2 px removed) |

**Why:** every step from 0.1922 to 0.2778 *removed* mass. No step added a newly discovered fault.
In `1/DTI = 1 + α·F/T + β·(K−T)/T` the only term that moved is `F/T`, the wasted mass per unit
credit. The last step deleted dots 100–200 m from mapped faults. The scorer masks the catalogue
itself (DrivenData staff, [thread 11516](https://community.drivendata.org/t/scoring-clarification-masked-pixels-and-re-evaluation/11516)).
Dots hugging it therefore mostly earn credit only against already-masked pixels, while still
paying α. The tip family carries 3,894–4,637 such flank dots and scored lower (0.2632–0.2649).
That is consistent with this explanation.

**Can this family beat 0.2778? Marginally at best.** It is ~98 % one dot pattern. The h32-1 tip
raster shares 36,874 of b2's 37,654 dots *at exactly the same pixels*. Any recombination moves a
few hundred dots, and §5 bounds that effect at roughly ±0.003. The leaderboard moved on: **#1 is
0.3774** ([leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/),
read 2026-10-06), not the 0.3195 quoted in the brief. Beating 0.32–0.38 needs new information,
most plausibly native 1 m LiDAR (H48-2), not a better recombination of 100 m layers.

## 3. H48-1 Dempster–Shafer fusion

Frame `{F, N}`. For source `i` with dots `D_i`, `s_i(x) = k(d(x, D_i))`:

```
m_i(F) = r_i · s_i(x)
m_i(N) = r_i · (1 − s_i(x)) · a_i(x)
m_i(Θ) = 1 − m_i(F) − m_i(N)
```

| parameter | value | justification (fixed before any instrument reading) |
|---|---|---|
| `r_b2` | 0.900 | reliability of the best live source |
| `r_tip` | 0.858 | `0.9 × 0.2649/0.2778`, proportional to live score |
| `a` off / on backbone | 0.2 / 0.5 | absence is weak evidence off the backbone (low recall) and stronger where the source examined the ridge and declined |
| `a_b2` on flank (d ≤ 2 px) | 1.0 | the dotted family's explicit, live-validated rejection (+0.0070) |
| decision | `BetP(F) = m(F) + m(Θ)/2 > 0.5` | Smets' pignistic rule, no tuned threshold |
| candidates | pixels where ≥ 1 source placed a dot | no invented positions |
| NMS radius | 2.8 px | the families' own minimum spacing is √8 = 2.83 px |

**Dempster's rule:** `K = f1·n2 + n1·f2`, `m(F) = (f1f2 + f1u2 + u1f2)/(1−K)`,
`m(N) = (n1n2 + n1u2 + u1n2)/(1−K)`, `m(Θ) = u1u2/(1−K)`.

> **Correction to the brief (IR-48-04).** Dempster's normalised rule does **not** carry the
> disagreement forward as unassigned mass. It divides the conflict `K` out and redistributes it.
> That is Zadeh's classic criticism. Yager (1987) is the rule that assigns `K` to Θ. We therefore
> publish **both**: `conflict_K.tif` (where the families disagree) and
> `unassigned_yager_mTheta_incl_conflict.tif`. Dempster's `m(Θ)` is also published for
> completeness.

> **Dependence (IR-48-03).** Dempster's rule assumes distinct evidence. b2 ⊂ r1 ⊂ d2.8 ⊂ h19-5,
> and h32-1 shares 97.9 % of b2's pixels, so agreement is double-counted. Denœux's (2008)
> cautious rule is the principled fix. Double counting inflates belief on *agreed* dots, which
> are kept anyway. It does not change the ordering of the *disagreement* dots, which are the only
> decisions the rule actually makes here.

### Not an average [MEASURED]

| statistic | value |
|---|---:|
| Pearson(belief, naive mean of supports), all supported px (769,098) | 0.962 |
| **Pearson, disagreement region** `|s1 − s2| ≥ 1/3` (44,626 px) | **0.715** |
| Spearman, disagreement region | 0.629 |
| mean conflict K: disagreement / agreement | 0.372 / 0.103 |
| mean belief where the dotted source is stronger (naive mean) | 0.620 (0.467) |
| mean belief where the tip source is stronger (naive mean) | 0.229 (0.313) |
| emission Jaccard vs naive-mean emission at equal count (V1 / V2) | 0.982 / 0.818 |

Averaging is symmetric. The fusion is not: it raises belief where the more reliable source
speaks and lowers it on the 30,304 disagreement pixels inside the catalogue flank, where the
dotted family has an explicit veto.

## 4. Validation — two instruments, both reported

### 4a. SGMC spatially-blocked 4-quadrant holdout — *computed, but not predictive*

Truth = SGMC geologic-map faults more than 3 px from the catalogue (62,122 px), scored per
footprint quadrant. **Calibration against 17 live-scored files: Spearman −0.17 (p = 0.53)**, and
−0.20 within the family. The r13-lattice file scores 0.250 on it but 0.0904 live. The instrument
is reported for transparency and **must not be used for selection** (IR-48-05).

| quadrant | b2 | V1 (shipped) | Δ |
|---|---:|---:|---:|
| Q0 | 0.09798 | 0.09815 | +0.00016 |
| Q1 | 0.09753 | 0.09750 | −0.00003 |
| Q2 | 0.11840 | 0.11848 | +0.00008 |
| Q3 | 0.07396 | 0.07394 | −0.00002 |

### 4b. LSI — Live-Score Inversion (new here)

`TP_w` is linear in the truth. Model the hidden truth as a Bernoulli field with intensity `q_b`
per bin (7 distance-to-catalogue bands × on/off the backbone). `Φ = T/ρ` is estimated with the
dot pattern's measured geometric ratio. `q ≥ 0` is fit to the 17 live scores
(`src/gems48/lsi.py`).

| ridge | LOO MAE | LOO Spearman (17) | LOO Spearman (top 8) |
|---|---:|---:|---:|
| 1e-4 | 0.0216 | 0.760 | −0.738 |
| **1e-3** | **0.0183** | **0.806** | **−0.690** |
| 1e-2 | 0.0189 | 0.804 | −0.714 |

LSI ranks coarse quality well but **cannot rank within the family**. Predictions: b2 0.26351,
V1 0.26336, V2 0.26305, V3 0.26295. Every difference is far below the instrument's resolution.

### 4c. Verdict

**H48-1 did not beat the holdout best (b2).** Under the project rule it should not take a slot
from a candidate that has. It is shipped because the brief requires a unique fused file. It is
the safest possible unique file: every one of its 37,754 dots is a dot of a live-scored file, and
it is a strict superset of the 0.2778 file plus 100 dots.

## 5. Risk bound for the shipped file [MEASURED, algebra]

`den = T/0.2778`. 100 added dots, 0 removed. If all 100 earn nothing: DTI ≥ **0.2773–0.2776**,
across the LSI-estimated `T` of 5,763 ×0.5…×1.5. If each sits on a straight 1-px truth line it
alone credits (credit 3.0): DTI ≤ 0.287–0.305. A dot is break-even at a mean credit of 0.0556.
Receipt: `evidence/risk_bound.json`.

## 6. Three GEMSDOE48 DS files on the same instruments [MEASURED]

Three sessions produced Dempster–Shafer files for this repo. Same instruments, same bytes logic
(`scripts/compare_ds_files.py` → `evidence/ds_file_comparison.json`):

| file | px | mass | values | b2 dots kept at 1.0 | within 200 m of catalogue | LSI pred. | SGMC mean |
|---|---:|---:|---|---:|---:|---:|---:|
| b2 (live 0.2778, reference) | 37,654 | 37,654 | {1} | 37,654 | 0 | 0.26351 | 0.09697 |
| **H48-1, this file (primary)** | 37,754 | 37,754 | {1} | **37,654** | **0** | **0.26336** | 0.09702 |
| PR #1 on main (Yager, graded) | 47,905 | 33,326 | {0.086, 0.137, 1} | 31,614 | 3,894 | 0.23826 | 0.08539 |
| PR #2 (b2 × h33-d decision) | 47,905 | 47,905 | {1} | 37,654 | 3,894 | 0.25903 | 0.09863 |

LSI cannot rank within ±0.003, but the PR #1 gap (−0.025) is coarse-scale, the kind of
difference LSI does resolve (LOO MAE 0.018 across 17 files). The mechanism is also explicit:
down-weighted validated dots plus re-added flank mass.
