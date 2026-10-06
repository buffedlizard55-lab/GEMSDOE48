> **Historical archive.** This earlier upstream page is preserved for provenance and may contain superseded claims. Do not treat it as the current submission or validation decision. See the [current overview](../../index.html) and [current validation](../../validation.html). Any six-hour leaderboard-feed instructions are obsolete: the current branch disables the workflow under its Terms-of-Use review, and the retained parser has no network-fetch path.

---

# GEMSDOE48 — DOE GEMS Prize fault-discovery system

<div class="dl">
<h2>⬇ Submission file (click to download)</h2>
<p><a class="btn" href="downloads/{{TIF}}">Download {{TIF}}</a></p>
<p>{{BYTES}} bytes · sha256 <code>{{SHA16}}…</code> · {{NPX}} dots · all-finite float32 in [0, 1] · EPSG:32611 · 3730 × 3292 · all {{NCHK}} checks PASS · <a href="downloads/{{ZIP}}">.zip</a> · <a href="downloads/{{RECEIPT}}">receipt</a></p>
<p><b>Note to paste:</b> <code>{{NOTE}}</code></p>
<p><a href="executive-summary.html">→ Step-by-step: how to submit</a></p>
</div>

## Executive summary

* **What it is.** A Dempster–Shafer fusion of the two strongest families: dotted **h33-2-b2
  (0.2778)** × tip **h32-1 (0.2649)**. Disagreement is preserved as its own layer. Unique: no
  identical support among the 80 sibling GeoTIFFs compared.
* **Why 0.2778 won.** Precision, not discovery. Mass fell from 121,131 to 37,654 dots while the
  score rose 0.1922 → 0.2778. The last step deleted the dots within 200 m of the catalogue
  ([method §2](method.html)).
* **Holdout verdict for this file: tie with 0.2778.** The downside is bounded at ≥ 0.2773: it is
  b2 plus 100 dots. No offline instrument can rank differences this small. The SGMC holdout does
  not predict live scores at all (ρ = −0.17), and the new live-score inversion predicts coarse
  quality (LOO ρ = 0.81) but not within-family order.
* **The board.** #1 is **0.3774**, not 0.3195 (IR-48-01). The gap is ~0.10. The 100 m layers
  plateau at 0.26–0.28 across 40+ repos, so the realistic route is **native 1 m LiDAR scarp
  detection** (H48-2, data verified obtainable).

![DS layers](assets/fig1_ds_layers.png)
![zoom](assets/fig2_ds_zoom.png)
![LSI](assets/fig3_lsi_calibration.png)

> **Our Core Values.** *Maximize P(Win)*: every slot is an experiment, chosen by measured
> evidence. *Own the Outcome*: every number links to the code and receipt that produced it, and
> our own instruments' failures are published ([irregularities](irregularities.html)).
