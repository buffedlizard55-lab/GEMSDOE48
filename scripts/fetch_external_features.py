#!/usr/bin/env python3
"""Fetch hash-pinned external feature mirrors needed by the H50 lidar-kinematic detector.

Only GitHub egress is used (``gh api``); DrivenData is never contacted. Every file is
verified against the SHA-256 recorded in ``registry/data_manifest_gemsdoe32.json`` and the
script FAILS CLOSED on any mismatch. Files land in ``data/raw/external/`` (git-ignored).

Usage: python scripts/fetch_external_features.py [--with-training-features]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
DEST = ROOT / "data" / "raw" / "external"
MANIFEST = ROOT / "registry" / "data_manifest_gemsdoe32.json"

DEFAULT_IDS = [
    "ext_lidar_scarp_features_u8",
    "ext_geodawn_rad_u8",
    "ext_geodawn_extensions_u8",
    "ext_gdr_qfaults_traces",
    "ext_gdr_wellspring_in_footprint",
    "ext_gdr_volcanic_vents_in_footprint",
]


def sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gh_raw(repo: str, path: str, ref: str | None, out: pathlib.Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    query = f"repos/{repo}/contents/{path}" + (f"?ref={ref}" if ref else "")
    with out.open("wb") as fh:
        subprocess.run(
            ["gh", "api", query, "-H", "Accept: application/vnd.github.raw"],
            stdout=fh,
            check=True,
        )


def fetch_entry(entry: dict) -> tuple[pathlib.Path, bool]:
    dest = DEST / pathlib.Path(entry.get("dest") or entry["path"]).name
    if dest.exists() and sha256(dest) == entry["sha256"]:
        return dest, True
    if "parts" in entry:
        with dest.open("wb") as out:
            for part in entry["parts"]:
                tmp = dest.with_suffix(dest.suffix + ".part")
                gh_raw(entry["repo"], part, entry.get("ref"), tmp)
                out.write(tmp.read_bytes())
                tmp.unlink()
    else:
        gh_raw(entry["repo"], entry["path"], entry.get("ref"), dest)
    return dest, sha256(dest) == entry["sha256"]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--with-training-features", action="store_true",
                    help="also fetch the 418 MB 19-band training_features mirror")
    ap.add_argument("--receipt", default=str(ROOT / "evidence" / "external_fetch_receipt.json"))
    args = ap.parse_args()

    wanted = list(DEFAULT_IDS)
    if args.with_training_features:
        wanted.append("training_features")
    spec = json.load(MANIFEST.open())
    by_id = {f["id"]: f for f in spec["files"]}
    receipt = {"manifest": str(MANIFEST.relative_to(ROOT)), "files": []}
    failed = []
    for fid in wanted:
        entry = by_id[fid]
        dest, ok = fetch_entry(entry)
        receipt["files"].append({
            "id": fid, "path": str(dest.relative_to(ROOT)), "expected_sha256": entry["sha256"],
            "actual_sha256": sha256(dest) if dest.exists() else None, "bytes": dest.stat().st_size if dest.exists() else None,
            "verified": ok, "repo": entry["repo"], "ref": entry.get("ref"), "provenance": entry.get("provenance"),
        })
        print(("PASS" if ok else "FAIL"), fid, dest)
        if not ok:
            failed.append(fid)
    pathlib.Path(args.receipt).write_text(json.dumps(receipt, indent=2))
    if failed:
        print("HASH MISMATCH:", failed, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
