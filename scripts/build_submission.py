#!/usr/bin/env python3
"""GEMSDOE48 historical Dempster-Shafer research-artifact builder.

Artifacts written by this script are not cleared for a competition slot; see
README.md and docs/md/index.md for the current decision.

Inputs (sha256-pinned to owner-published receipts):
  dotted family : GEMSDOE32 h33-h33-2-b2 zeros        (owner-reported live 0.2778)
  tip family    : GEMSDOE33 h33d analog tip-stepover  (owner-reported live 0.2632)

Historical Dempster-Shafer research outputs:
  DS-DECISION -- the binary union of cells with committed fault mass, retained
      as a comparison artifact. It is not a current submission recommendation.
  DS-BELIEF -- normalized combined belief Bel_ds in [0,1] (intersection tier
      1.0, single-source tier alpha/(1+alpha) ~ 0.4975), retained as a graded
      research surface per Shafer (1976).
  DIAGNOSTICS -- unassigned mass m12(Theta), conflict K, plausibility Pl(F),
      and raw belief. These expose disagreement; they do not establish that
      the evidence sources are statistically independent.

The historical SGMC tier sweep is not private truth or reliable enough to
clear a slot. See docs/data/proxy-validation.json for the corrected Yager v2
result and README.md for the current no-go decision.

Evidence written:
  evidence/build_submission.json  -- full receipt incl. not-the-naive-mean check
"""
import datetime as dt
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from gemsdoe48 import dataio
from gemsdoe48.dempster_shafer import dempster_combine, normalize_bel
from gemsdoe48.format_checks import audit_submission, dump_json, sha256_file

ROOT = os.path.join(os.path.dirname(__file__), "..")
RAW = os.path.join(ROOT, "data", "raw")
OUT = os.path.join(ROOT, "docs", "downloads")
EVIDENCE = os.path.join(ROOT, "evidence")

INPUTS = {
    "dotted_h33_2_b2": {
        "path": os.path.join(RAW, "dotted_h33_2_b2_zeros.tif"),
        "sha256": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
        "origin": "GEMSDOE32 h33-h33-2-b2 (spacing-tuned dotted family)",
        "owner_reported_score": 0.2778,
        "site": "https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html",
    },
    "tip_h33d": {
        "path": os.path.join(RAW, "tip_h33d_stepover.tif"),
        "sha256": "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
        "origin": "GEMSDOE33 h33d analog tip-stepover r30 (tip/step-over family)",
        "owner_reported_score": 0.2632,
        "site": "https://buffedlizard55-lab.github.io/GEMSDOE33/",
    },
}
TEMPLATE = os.path.join(RAW, "sample_submission_template.tif")
TEMPLATE_SHA = "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc"
ALPHA1 = 0.99  # dotted source reliability (discounting)
ALPHA2 = 0.99  # tip source reliability (discounting)


def main():
    os.makedirs(OUT, exist_ok=True)
    os.makedirs(EVIDENCE, exist_ok=True)
    ev = {"generated_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
          "alpha_dotted": ALPHA1, "alpha_tip": ALPHA2}

    # ---- verify pinned inputs ------------------------------------------------
    for k, meta in INPUTS.items():
        h = sha256_file(meta["path"])
        assert h == meta["sha256"], f"input hash mismatch for {k}: {h}"
        ev.setdefault("inputs", {})[k] = {**meta, "sha256_verified": True}
        print(f"[ok] input pinned: {k} sha256={h[:16]}...")
    h = sha256_file(TEMPLATE)
    assert h == TEMPLATE_SHA, f"template hash mismatch: {h}"
    ev["template"] = {"path": TEMPLATE, "sha256": h, "sha256_verified": True}

    footprint = dataio.footprint_from_template(TEMPLATE)
    s_dot = (dataio.load(INPUTS["dotted_h33_2_b2"]["path"]) > 0).astype(np.float64)
    s_tip = (dataio.load(INPUTS["tip_h33d"]["path"]) > 0).astype(np.float64)
    ev["counts"] = {
        "footprint_cells": int(footprint.sum()),
        "dotted_positive": int(s_dot.sum()),
        "tip_positive": int(s_tip.sum()),
        "intersection": int(((s_dot > 0) & (s_tip > 0)).sum()),
        "dotted_only": int(((s_dot > 0) & (s_tip == 0)).sum()),
        "tip_only": int(((s_tip > 0) & (s_dot == 0)).sum()),
        "union": int(((s_dot > 0) | (s_tip > 0)).sum()),
    }
    print("[ok] counts:", json.dumps(ev["counts"]))

    # ---- Dempster-Shafer combination ------------------------------------------
    ds = dempster_combine(s_dot, s_tip, ALPHA1, ALPHA2)
    bel_raw = ds["bel"]
    bel = normalize_bel(bel_raw, footprint)
    ev["ds_tiers"] = {
        "raw_belief_intersection": float(bel_raw[(s_dot > 0) & (s_tip > 0)].max()),
        "raw_belief_single_source": float(bel_raw[(s_dot > 0) != (s_tip > 0)].max()),
        "normalized_intersection": float(bel[(s_dot > 0) & (s_tip > 0)].max()),
        "normalized_single_source": float(bel[(s_dot > 0) != (s_tip > 0)].max()),
    }
    print("[ok] DS tiers:", json.dumps(ev["ds_tiers"]))

    # ---- not-the-naive-mean check ----------------------------------------------
    naive = 0.5 * (s_dot + s_tip)  # values 0, 0.5, 1
    diff = np.abs(bel.astype(np.float64) - naive)
    sup = ((s_dot > 0) | (s_tip > 0)) & footprint
    r_support = float(np.corrcoef(bel[sup], naive[sup])[0, 1])
    r_footprint = float(np.corrcoef(bel[footprint], naive[footprint])[0, 1])
    ev["not_the_naive_mean"] = {
        "naive_mean_definition": "(dotted + tip) / 2  (values 0, 0.5, 1)",
        "pearson_r_on_support": r_support,
        "pearson_r_in_footprint": r_footprint,
        "mae_in_footprint": float(diff[footprint].mean()),
        "max_abs_diff": float(diff.max()),
        "cells_differing_gt_1e6": int((diff > 1e-6).sum()),
        "cells_differing_equals_single_source_dots":
            int((diff > 1e-6).sum()) == ev["counts"]["dotted_only"] + ev["counts"]["tip_only"],
        "is_identical_to_naive_mean": bool((diff <= 1e-6).all()),
        "interpretation": (
            "Dempster's rule is nonlinear. For binary source surfaces with "
            "discount alpha, the combined belief has tiers {0, alpha/(1+alpha)="
            "0.49749, alpha(2-alpha)=0.9999}, whereas the naive mean has tiers "
            "{0, 0.5, 1}. The two surfaces agree on which cells are positive "
            "(monotone relation -> Pearson r ~ 1 on support), but the values "
            "differ at exactly the 16,291 single-source disagreement dots "
            "(0.49754 vs 0.5), and the DS construction additionally carries "
            "unassigned-mass and conflict layers that no average possesses. "
            "We report r ~ 1 honestly rather than hiding it: the evidence-theoretic "
            "content of this historical artifact is in the tier structure and "
            "preserved ignorance mass. Its full-confidence emission is not cleared "
            "by a reliable spatial holdout."),
    }
    print("[ok] not-naive-mean:", json.dumps(ev["not_the_naive_mean"], indent=1))

    # ---- historical binary emission --------------------------------------------
    # Retain the old full-confidence union output for reproducibility and audit;
    # the current proxy and format evidence do not clear it for a weekly slot.
    decision = np.where((bel_raw > 0) & footprint, 1.0, 0.0)
    ev["decision_rule"] = {
        "support": "m12(F) > 0 (combined committed fault evidence present)",
        "value_policy": "full confidence 1.0 (historical comparison only; not slot-cleared)",
        "emitted_pixels": int(decision.sum()),
    }

    # ---- write all artifacts ------------------------------------------------------
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cid = hashlib.sha256(decision.astype(np.float32).tobytes()).hexdigest()[:12]
    base = f"gemsdoe48-ds-dotted-x-tipstepover-{stamp}-{cid}"

    primary_path = os.path.join(OUT, base + "-decision-zeros.tif")
    dataio.write_submission(primary_path, decision, footprint)
    ev["primary"] = {"filename": os.path.basename(primary_path),
                     "kind": "historical DS-DECISION research artifact (not slot-cleared)"}
    ev["primary"].update(audit_submission(primary_path, footprint))
    print(f"[ok] PRIMARY {os.path.basename(primary_path)}")

    bel_path = os.path.join(OUT, base + "-belief-zeros.tif")
    dataio.write_submission(bel_path, bel, footprint)
    ev["belief"] = {"filename": os.path.basename(bel_path),
                    "kind": "normalized combined belief (graded)"}
    ev["belief"].update(audit_submission(bel_path, footprint))
    print(f"[ok] BELIEF {os.path.basename(bel_path)}")

    layers = [
        ("unc", "ds-unassigned-mass", ds["unc"]),
        ("conflict", "ds-conflict", ds["conflict"]),
        ("pl", "ds-plausibility", ds["pl"]),
        ("bel_raw", "ds-belief-raw", bel_raw),
    ]
    ev["diagnostic_layers"] = {}
    for key, tag, arr in layers:
        p = os.path.join(OUT, f"gemsdoe48-{tag}-{stamp}-{cid}.tif")
        dataio.write_submission(p, arr, footprint)
        rec = audit_submission(p, footprint)
        ev["diagnostic_layers"][key] = {
            "filename": os.path.basename(p), "sha256": rec["sha256"],
            "min": rec["min"], "max": rec["max"],
            "positive_cells": rec["positive_cells"]}
        print(f"[ok] layer {key}: {os.path.basename(p)}")

    ev["content_id"] = cid
    ev["base_name"] = base
    dump_json(ev, os.path.join(EVIDENCE, "build_submission.json"))
    print("\nprimary all_checks_passed:", ev["primary"]["all_checks_passed"])
    print("belief  all_checks_passed:", ev["belief"]["all_checks_passed"])
    print("primary:", os.path.basename(primary_path))
    print("belief :", os.path.basename(bel_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
