# GEMSDOE48 — a Dempster–Shafer fusion submission system for the DOE GEMS Prize

**Read this file first, every session.** Section 1 is the standing brief, verbatim in intent and
complete in scope. Sections 2–6 are the state of the work.

- **Downloadable submission:** [`docs/downloads/gemsdoe48-ds48-emission.tif`](docs/downloads/gemsdoe48-ds48-emission.tif)
- **Site (GitHub Pages, `docs/`):** [`docs/index.html`](docs/index.html) ·
  [how to submit](docs/executive-summary.html) · [why 0.2778 won](docs/research.html) ·
  [hypotheses](docs/hypotheses.html) · [sources](docs/sources.html) ·
  [irregularities](docs/irregularities.html)
- **Unique submission name:** `GEMSDOE48-DS48-FUSION`

---

## 1. The standing brief

> **Primary deliverable.** Generate a **unique** (non-copied) competition-legal TIF submission for
> the DOE GEMS Prize (DrivenData #306) and make it trivially downloadable, and answer with
> PhD-level reasoning **why and how the 0.2778 (`GEMSDOE32` H33-2-B2) submission scored highest**,
> and whether > 0.2778 is achievable. The current leaderboard best is 0.3195, and it must be beaten.
>
> **Specifically required.**
>
> 1. **Combine the two best-performing families with Dempster–Shafer evidence theory**
>    (Dempster 1967; Shafer 1976): the best spacing-tuned "dotted" family (up to 0.2778) and the
>    best tip/step-over family (0.26–0.27). **Preserve disagreement rather than averaging it away**
>    — explicitly, a naive weighted average washes out the disagreement information. Carry forward
>    the unassigned/uncertain mass as its own diagnostic layer. Normalise the combined belief to
>    [0, 1]. Write the required format. **Verify the result is NOT just the average** (correlation
>    check against the naive mean) before presenting it for download.
> 2. **Study the whole GEMSDOE site list and the leaderboard.** Deep research into scientific
>    discovery of geothermal vents from official/verified free sources; find overlooked data
>    sources.
> 3. **Produce 3–5 new candidate geological hypotheses**, each naming: the specific layer(s), the
>    physical signature targeted (edge/curvature transform etc.), why it catches a fault missing
>    from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from
>    anything already in the repository. **Rank by expected DTI improvement vs implementation
>    cost.** **Validate the top candidate on the spatially-blocked holdout before touching a weekly
>    submission slot.** If a candidate needs new external data, name the specific free official
>    source and **verify obtainability** before proposing it.
> 4. **Site.** A GitHub Page for this repository, clean/simple UI, **all sources linked for manual
>    review**, and an executive-summary subpage explaining **exactly how to submit** (the
>    submission form rejects out-of-range values: *"Predicted values must be in range [0, 1]"*),
>    plus unique-submission-name and short-comment-field guidance.
> 5. **Put the full prompt into the repository README** as the standing starting point, read every
>    session.
> 6. **Run the task through multiple passes** — Pass 1 implement + verify, Pass 2 bug/edge-case
>    review + fix, Pass 3 re-check against the original request and improve
>    accuracy/reliability/completeness/code quality. Do not stop after the first pass.
> 7. **Create a pull request and merge it onto `main`.** List remaining work and limitations for
>    this or the next session.
> 8. Also outstanding from the prompt: `bash scripts/download_competition_data.sh` → `data/`, then
>    `python scripts/prepare_data.py`, then the full train → inference → validate pipeline (GPU
>    needed for training).
>
> **Standing quality bar.** Work verified line by line against official/trusted sources with links
> for manual review. Autonomous — **no manual input required from the user**. Flag irregularities.
> **No hallucinations.**
>
> **Hard constraints (highest urgency, verbatim intent).**
>
> - Must generate a **UNIQUE TIF submission**. Do **not** copy a previous submission except for
>   learning/education. It must be an **easy-to-download** submission TIF as the prompt describes.
> - The submission must exist as an easy-to-download TIF file and the site must make this obvious
>   at the very top. A previous upload failed with *"Predicted values must be in range [0, 1]"* —
>   the output must be within [0, 1] and format-valid.
> - Give the submission a **unique name** and a **short distinguishing comment**
>   (e.g. "clustering with k=25").
> - **No hallucinations.** Verify line by line. Provide official/verified source links for manual
>   review. Flag irregularities for review.
> - **No manual input required from the user** — complete tasks autonomously.
> - Combine the two best families with a rule that **preserves disagreement instead of averaging
>   it away** (explicitly: a naive weighted average washes out disagreement information).
> - **Do not spend a weekly submission slot on an idea that has not beaten the current holdout
>   best.**
> - Keep the Arena Core Values **"Maximize P(Win)"** and **"Own the Outcome"** as the focal point
>   for all building, research and decisions.
> - Two prior sessions' outputs must be honoured: the repository should be the unique
>   next-generation submission system (unique approaches, aiming to beat 0.3195), and the
>   competition-data download/prepare scripts remain an explicit required task.

---

## 2. What is shipped

Four single-band float32 GeoTIFFs on the official grid (`EPSG:32611`, 100 m, 3292 × 3730),
written by `scripts/build_submission.py` and verified from the bytes on disk by
`tests/test_submission.py`. Every value is finite and inside [0, 1]; the portal's own rule is
satisfied exactly.

| file | what it is | range | positive px |
|---|---|---|---|
| [`gemsdoe48-ds48-emission.tif`](docs/downloads/gemsdoe48-ds48-emission.tif) | **portal candidate** — DS-ranked off-flank emission, mass-matched to the live-best artifact | [0, 1] binary | **37,654** |
| [`gemsdoe48-ds48-belief.tif`](docs/downloads/gemsdoe48-ds48-belief.tif) | `Bel(F)`, the Dempster–Shafer combined belief (diagnostic) | [0.0000, 0.8400] | 794,250 |
| [`gemsdoe48-ds48-mtheta.tif`](docs/downloads/gemsdoe48-ds48-mtheta.tif) | `m₁₂(Θ)`, the unassigned belief mass (the disagreement layer) | [0.1600, 0.2500] | — |
| [`gemsdoe48-ds48-conflict.tif`](docs/downloads/gemsdoe48-ds48-conflict.tif) | `K`, Shafer's conflict mass | [0.0000, 0.3600] | 760,580 |

**Why nothing here beats 0.2778, stated plainly.** No arm tested in this repository beats the
0.2778 artifact on any instrument that has been validated against the live leaderboard. Three arms
were built, measured and falsified: DS corroboration removal (safety 0.64 at its best operating
point, against a required 2.0), hexagonally covering-optimal re-emission at eleven spacings, and
DS-ranked re-emission at matched mass. The binding constraint is **detector quality on the
~12,632-pixel hidden new-truth population**, not emission style — the emission is already at a
local optimum. See `registry/submission_build.json → headline_negative_result`.

---

## 3. The Dempster–Shafer fusion, and the honest correlation check

The two families were built independently and agree on 69.6 % of their pixels (33,670 of a
48,394-pixel union), disagreeing on 14,724. Each supplies a belief surface `bᵢ(x)` in the metric's
own geometry; with a Shafer reliability discount `aᵢ = 0.6` the mass function is

```
mᵢ({F}) = aᵢ bᵢ(x)      mᵢ({¬F}) = aᵢ (1 − bᵢ(x))      mᵢ(Θ) = 1 − aᵢ
```

and Dempster's rule gives `K = m₁(F)m₂(¬F) + m₁(¬F)m₂(F)` — the conflict — and the normalised
combination. Worked values, all asserted in `tests/test_ds.py`:

| `(b₁, b₂)` | `K` | `Bel(F)` | `m₁₂(Θ)` |
|---|---|---|---|
| (1, 1) full agreement | 0.0000 | **0.8400** | 0.1600 |
| (1, 0) total disagreement | 0.3600 | **0.3750** | 0.2500 |
| (0.5, 0.5) | 0.1800 | 0.4024 | — |

**Is it just the average? No — and this is measured, not claimed.** On the union support,
Pearson r = 0.991085, mean |Bel − mean| = 0.1423, and 100 % of union pixels differ by more than
0.05. Bel is *not* an affine function of the mean (best-fit residual > 0.01). But the **Spearman
rank correlation is 1.000000**, because a union pixel has belief exactly 1 in its own family, so
both statistics are monotone in the other family's belief alone. The repository therefore states
in `registry/submission_build.json → not_the_mean → verdict` that DS **"does NOT change the ranking
… and does not claim that it does"**. What DS adds is the calibrated belief value, the conflict
mass `K`, and the unassigned mass `m₁₂(Θ)`, none of which has a counterpart in an average.

**On "normalise to [0, 1]".** Dempster's rule *is* a normalisation — it divides by `(1 − K)` — and
the result obeys the mass-function axioms at every pixel, so every component lies in [0, 1] by
construction. No affine rescale is applied to any layer, because rescaling a belief or a mass
surface destroys the calibration that is the only reason to ship it, and a rescaled mass is not a
mass. `registry/submission_build.json → normalisation` records the natural range of every layer and
the min–max affine map that would take it to [0, 1], so the alternative is auditable.

---

## 4. Why 0.2778 won, and whether > 0.2778 is achievable

The official metric is the Tversky index with α = 0.2 (false positives) and β = 0.8 (false
negatives) over a 300 m triangular kernel:

```
TPw = Σ_g max_x p(x) k(d(x,g))      FPw = Σ_x p(x) (1 − max_g k(d(x,g)))      FNw = |G| − TPw
DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw + eps)
```

Three exact consequences, all proved in `src/gemsdoe48/metric.py` and asserted in
`tests/test_metric.py`:

1. **The DTI-optimal submission is binary {0, 1}.** The derivative of the score in a pixel value
   `v` is `(k − 0.2·DTI)·D₀ / (D₀ + 0.2v)²`, whose sign is independent of `v`. Every pixel is
   pushed to 0 or 1. A graded probability surface is strictly worse than its own binarisation —
   which is why `-belief.tif`, `-mtheta.tif` and `-conflict.tif` are labelled diagnostic.
2. **Emit a dot iff its realised kernel weight exceeds `0.2 · DTI`.** At 0.2778 that bar is
   **0.0556**. The live-anchored break-even measured from the two owner-reported scores is
   τ_live = 0.05416 credit per dot.
3. **The owner's live ladder is a removal ladder.** 44,090 px → 0.2600; −3,891 px → 40,199 px →
   0.2708; catalogue-flank buffer B = 2 → 37,654 px → **0.2778**. No addition has ever improved a
   live score.

**Achievability.** In the removal regime the denominator collapses to `D = 0.2·S + 0.8·|G|`, with
`|G| = 12,632` recovered by inverting the anchor pair to 0.13 % internal consistency. That gives
`D = 18,145.4` at the 0.2708 anchor and `T = 4,913.8`, i.e. 0.122236 credit per emitted dot against
the τ_live = 0.05416 bar. At the live-best mass of 37,654 px, `D = 17,636.4` and `T = 4,899.4`.
To reach the current leader's 0.3262 **on that same mass budget** the numerator must rise to
**5,753.0** — **+853.6 weighted units, +17.4 %**, at unchanged precision. That is a detector
problem, not an emission problem: the two families' own spacing sweeps already bracket their
optimum, and all three covering-theorem re-emission arms are worse per unit mass. The remaining
headroom is in the ~12,632 hidden new-truth pixels that no file in this repository can see.

---

## 5. Repository layout

```
docs/                      the GitHub Pages site (published from /docs on main)
  index.html               submission + one-click downloads + the one-table answer
  executive-summary.html   exactly how to submit, portal-rejection causes, format proof
  research.html            the metric, the mechanism, the instrument defect
  hypotheses.html          5 ranked candidate hypotheses + the promotion gate
  sources.html             every claim, its official source, and that source's limit
  irregularities.html      IR-48-01 … IR-48-09
  downloads/               the four GeoTIFFs
data/official/             labels, existing faults, SGMC faults (the truth layers)
data/families/             the four extracted parent emissions
src/gemsdoe48/             metric, ds, emit, families, grid, holdout, live_anchor
scripts/                   build_submission, build_site, hash_inputs, run_* experiments
tests/                     83 stdlib-unittest tests; run with: python3 -m unittest discover -s tests -t tests
registry/                  machine-written receipts (inputs.json, submission_build.json)
evidence/                  experiment receipts (holdout_antimonotone, selection, ds_layers)
knowledge/                 the research notes behind the site
```

## 6. Reproduce everything

```bash
python3 scripts/hash_inputs.py        # SHA-256 receipt for every input raster
python3 scripts/build_submission.py   # writes the four GeoTIFFs + registry/submission_build.json
python3 scripts/build_site.py         # regenerates docs/*.html from the registry
python3 -m unittest discover -s tests -t tests
```

No network access is required for any of the above, and no organizer endpoint is ever contacted
(see `IR-DRIVENDATA-AUTOMATION` — the DrivenData terms of use prohibit automatic access).

## 7. Remaining work and limitations

- `bash scripts/download_competition_data.sh` and `python scripts/prepare_data.py` have **not been
  run**: the DrivenData data page is auth-walled and the terms of use prohibit robots. This is the
  single remaining blocker to training a detector.
- `scripts/run_ds_fusion.py` is superseded by the fusion now inside `build_submission.py`;
  `evidence/ds_fusion.json` and `evidence/ds_layers/*.tif` are not produced.
- The external GeoDAWN layers are **not** copied into `data/external/`; hypothesis H48-D's
  obtainability is explicitly **not verified** from this sandbox (every science host returns
  HTTP 000).
- Rank 1 (`H48-A`, the 200–300 m catalogue-companion band) is derived from the B = 2 → B = 3 live
  pair and is the recommended next build, but it has **not** been validated on a spatially-blocked
  holdout. **Do not spend a submission slot on it until it has.**
