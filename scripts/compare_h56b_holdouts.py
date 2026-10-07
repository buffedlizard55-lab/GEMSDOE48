#!/usr/bin/env python3
"""Create an auditable, matched-protocol H56B vs H49 holdout comparison.

The spatial holdout DTI is a similarity score: higher is better. This script
fails closed if the two receipts do not share their spatial protocol, source
pins, or proxy truth pins. These public-map diagnostics cannot clear a private
label submission slot.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_H56B_PATH = ROOT / "evidence/holdout_h56b_currentprotocol_20261007.json"
DEFAULT_H49_PATH = ROOT / "evidence/holdout_h49_currentprotocol_20261007.json"
DEFAULT_OUT_PATH = ROOT / "evidence/holdout_h56b_vs_h49_currentprotocol_20261007.json"
FOLDS = ("NW", "NE", "SW", "SE")
TARGETS = {
    "catalogue_proxy": ("results", "h56b_belief_normalized_dempster", "h49_balanced_reference"),
    "sgmc_off_catalogue_proxy": (
        "sgmc_off_catalogue_results",
        "h56b_belief_normalized_dempster",
        "h49_balanced_reference",
    ),
}


def load(path: Path) -> dict:
    return json.loads(path.read_text())


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--h56b", type=Path, default=DEFAULT_H56B_PATH)
    parser.add_argument("--h49", type=Path, default=DEFAULT_H49_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT_PATH)
    parser.add_argument("--h56b-key", default="h56b_belief_normalized_dempster",
                        help="candidate key in each holdout result mapping")
    parser.add_argument("--h56b-label", default="H56B", help="label in the comparison receipt")
    args = parser.parse_args()
    h56b_path, h49_path, out_path = args.h56b.resolve(), args.h49.resolve(), args.output.resolve()
    h56b, h49 = load(h56b_path), load(h49_path)
    for field in ("fold_protocol", "truth_sources"):
        if h56b[field] != h49[field]:
            raise SystemExit(f"Receipts are not matched: {field} differs")
    for source in ("dotted", "tip_stepover"):
        if h56b["source_inputs"][source] != h49["source_inputs"][source]:
            raise SystemExit(f"Receipts are not matched: source pin {source} differs")
    if h56b.get("status") != "CONDITIONAL_SPATIAL_BLOCK_DIAGNOSTIC_NOT_SLOT_CLEARED":
        raise SystemExit("Unexpected H56B receipt status")
    if h49.get("status") != "CONDITIONAL_SPATIAL_BLOCK_DIAGNOSTIC_NOT_SLOT_CLEARED":
        raise SystemExit("Unexpected H49 receipt status")

    targets = {}
    for target, (section, default_key56, key49) in TARGETS.items():
        key56 = args.h56b_key or default_key56
        try:
            a = h56b[section][key56]
            b = h49[section][key49]
            fold_values = {
                fold: {
                    "h56b_dti": float(a[fold]["dti"]),
                    "h49_dti": float(b[fold]["dti"]),
                    "delta_h56b_minus_h49": float(a[fold]["dti"] - b[fold]["dti"]),
                    "h56b_wins": bool(a[fold]["dti"] > b[fold]["dti"]),
                }
                for fold in FOLDS
            }
        except (KeyError, TypeError) as exc:
            raise SystemExit(f"Missing fold values for {target}: {exc}") from exc
        mean56 = sum(fold_values[x]["h56b_dti"] for x in FOLDS) / len(FOLDS)
        mean49 = sum(fold_values[x]["h49_dti"] for x in FOLDS) / len(FOLDS)
        stored_mean56, stored_mean49 = float(a["mean_dti"]), float(b["mean_dti"])
        if abs(mean56 - stored_mean56) > 1e-12 or abs(mean49 - stored_mean49) > 1e-12:
            raise SystemExit(f"Stored mean does not reproduce from folds for {target}")
        wins = sum(v["h56b_wins"] for v in fold_values.values())
        targets[target] = {
            "folds": fold_values,
            "mean_h56b_dti": mean56,
            "mean_h49_dti": mean49,
            "mean_delta_h56b_minus_h49": mean56 - mean49,
            "h56b_wins": wins,
            "fold_count": len(FOLDS),
            "higher_is_better": True,
            "result": f"{args.h56b_label} loses on every fold" if wins == 0 else f"{args.h56b_label} wins at least one fold",
        }

    protocol_blob = json.dumps(h56b["fold_protocol"], sort_keys=True).encode()
    protocol_id = hashlib.sha256(protocol_blob).hexdigest()
    no_wins = all(v["h56b_wins"] == 0 for v in targets.values())
    report = {
        "schema_version": 1,
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "MATCHED_HOLDOUT_COMPARISON_NOT_SLOT_CLEARED",
        "metric_direction": {
            "metric": "official distance-weighted Tversky index (DTI)",
            "formula": "TPw / (TPw + 0.2*FPw + 0.8*FNw + epsilon)",
            "higher_is_better": True,
            "source": "src/gemsdoe48/metric.py and the official problem metric page",
        },
        "protocol": h56b["fold_protocol"],
        "protocol_sha256": protocol_id,
        "receipt_inputs": {
            "h56b": {"path": str(h56b_path.relative_to(ROOT)), "sha256": sha256(h56b_path)},
            "h49": {"path": str(h49_path.relative_to(ROOT)), "sha256": sha256(h49_path)},
        },
        "candidates": {
            "h56b": h56b["candidate"],
            "h49": h49["candidate"],
        },
        "shared_source_inputs": {
            source: h56b["source_inputs"][source]
            for source in ("dotted", "tip_stepover")
        },
        "shared_public_proxy_truth_sources": h56b["truth_sources"],
        "targets": targets,
        "slot_decision": {
            "cleared": False,
            "submit_recommended": False,
            "reason": (
                "H56B has no fold wins versus H49 on either public-map proxy under the matched protocol; "
                "the proxies are not private expert truth and the receipts explicitly prohibit slot clearance."
                if no_wins else
                "A proxy win is not private-label evidence and cannot clear the submission slot."
            ),
        },
        "limitations": [
            "Catalogue and SGMC are public-map proxies, not private competition labels.",
            "Upstream candidate surfaces are frozen and not rebuilt independently within folds; potential leakage remains.",
            "The SGMC mask is filtered to >300 m from the public catalogue; this is not independent private-label validation.",
            "No score, rank, or organizer acceptance is estimated by these holdouts.",
        ],
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({
        "output": str(out_path.relative_to(ROOT)),
        "protocol_sha256": protocol_id,
        "targets": {
            k: {
                "mean_h56b_dti": v["mean_h56b_dti"],
                "mean_h49_dti": v["mean_h49_dti"],
                "fold_wins": v["h56b_wins"],
                "deltas": {fold: val["delta_h56b_minus_h49"] for fold, val in v["folds"].items()},
            }
            for k, v in targets.items()
        },
        "submit_recommended": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
