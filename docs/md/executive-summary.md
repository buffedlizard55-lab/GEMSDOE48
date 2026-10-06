# Executive summary — how to submit in 5 steps

## ⬇ The file

**[Download {{TIF}}](downloads/{{TIF}})** ({{BYTES}} bytes · sha256 `{{SHA16}}…`) ·
[.zip alternative](downloads/{{ZIP}}) · [audit receipt](downloads/{{RECEIPT}})

| field on the DrivenData form | paste this |
|---|---|
| **File to submit** | `{{TIF}}` (or the `.zip`, which holds the same single GeoTIFF) |
| **Unique name** (start of the note) | `{{UNIQUE}}` |
| **Note (optional)** | `{{NOTE}}` |

> **Upload the file above, not** `gemsdoe48-h48-ds-yager-conflict-20261006.tif` (an earlier
> session's file still in `downloads/`). See IR-48-13 in [irregularities](irregularities.html).

## Steps

1. Log in at <https://www.drivendata.org/competitions/306/competition-doe-gems/> (your account).
2. Open **Submissions → Submit**
   ([page](https://www.drivendata.org/competitions/306/competition-doe-gems/submissions/)).
3. **File to submit:** choose the downloaded `.tif`. A single-band GeoTIFF or a `.zip` holding
   one GeoTIFF are both accepted, according to the form text the owner quoted.
4. **Note:** paste the note above. It carries the unique name and a short comment, as the form
   asks ("e.g. clustering with k=25").
5. Click **Submit** and record the score in `registry/live_scores.json` (the next session reads
   it).

## Why this file will not trigger "Predicted values must be in range [0, 1]"

That error happens when cells contain NaN, which fails a `0 ≤ p ≤ 1` check. This file is
**all-finite float32**: 0 outside the footprint, no nodata tag, min 0.0, max 1.0. That is the
same encoding as the 0.2778 file that scored. All {{NCHK}} checks were re-run on the bytes on disk:

{{CHECKS}}

## What it is, in one paragraph

A Dempster–Shafer fusion of the group's best dotted file (h33-2-b2, live 0.2778) and best tip
file (h32-1, live 0.2649). It emits **{{NPX}}** dots: all 37,654 of b2, plus 100 tip-family dots
that the fusion accepted, with 0 dots within 200 m of the catalogue. The disagreement between
the two families is published as its own layer. Verdict from the holdout: **tie with 0.2778,
downside bounded at ≥ 0.2773** ([method](method.html)). Leaderboard #1 is 0.3774. Reaching it
needs new data (see [hypotheses](hypotheses.html) and [next steps](next-steps.html)).

## Diagnostic layers (not for submission, for geologists)

| layer | meaning |
|---|---|
| [belief m(F), normalised 0–1](downloads/diagnostics/gemsdoe48-h48-1-belief_dempster_mF_norm01.tif) | where the fused model believes there is a fault |
| [conflict K](downloads/diagnostics/gemsdoe48-h48-1-conflict_K.tif) | **where the two strongest approaches actively disagree** |
| [Yager m(Θ)](downloads/diagnostics/gemsdoe48-h48-1-unassigned_yager_mTheta_incl_conflict.tif) | unassigned belief including conflict |
| [Dempster m(Θ)](downloads/diagnostics/gemsdoe48-h48-1-unassigned_dempster_mTheta.tif) | unassigned belief after normalisation |

The belief layer is technically in the submission format, but it spreads mass over ~770k pixels.
By the scale identity and marginal rule that would score far below the binary file. Do not
submit it.
