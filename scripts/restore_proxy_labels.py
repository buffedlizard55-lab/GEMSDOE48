#!/usr/bin/env python3
"""Restore hash-pinned public owner mirrors for a catalogue-proxy holdout.

This script does NOT contact DrivenData. The mirrors below are not organizer-
authenticated; hashes establish equality with the named public GitHub commit only.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPO = "buffedlizard55-lab/GEMSDOE24"
REF = "07345ea0604953d7efb858d9cfbc21e20c7aca0b"
FILES = {
    "labels.tif": {
        "path": "data/bridge/labels.tif",
        "bytes": 425830,
        "sha256": "7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093",
    },
    "sample_submission.tif": {
        "path": "data/bridge/sample_submission.tif",
        "bytes": 1599597,
        "sha256": "2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc",
    },
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(path: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    partial.unlink(missing_ok=True)
    try:
        downloaded = False
        if shutil.which("gh"):
            endpoint = f"repos/{REPO}/contents/{path}?ref={REF}"
            try:
                with partial.open("wb") as output:
                    subprocess.run(
                        ["gh", "api", endpoint, "-H", "Accept: application/vnd.github.raw"],
                        stdout=output,
                        check=True,
                    )
                downloaded = True
            except subprocess.CalledProcessError:
                partial.unlink(missing_ok=True)
        if not downloaded:
            url = f"https://raw.githubusercontent.com/{REPO}/{REF}/{path}"
            request = urllib.request.Request(url, headers={"User-Agent": "GEMSDOE48-research/1.0"})
            with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as output:
                shutil.copyfileobj(response, output, length=1 << 20)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data" / "proxy")
    args = parser.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    for name, record in FILES.items():
        target = args.data_dir / name
        if not target.is_file() or target.stat().st_size != record["bytes"] or sha256_file(target) != record["sha256"]:
            fetch(record["path"], target)
        actual_hash = sha256_file(target)
        if target.stat().st_size != record["bytes"] or actual_hash != record["sha256"]:
            target.unlink(missing_ok=True)
            raise SystemExit(f"Integrity check failed for {name}: {actual_hash}")
        print(f"PASS {target} ({target.stat().st_size:,} bytes; sha256={actual_hash})")
    print("WARNING: owner-mirror catalogue labels only; not organizer-authenticated private competition truth.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
