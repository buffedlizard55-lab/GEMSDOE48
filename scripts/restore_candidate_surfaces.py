#!/usr/bin/env python3
"""Restore SHA-256-pinned public owner-mirror candidate surfaces.

These are third-party research artifacts, not organizer-provided datasets. Their
provenance is tied to exact public repository commits; no license grant is inferred.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FILES = {
    "gemsdoe32-h33-h33-2-b2.tif": {
        "repo": "buffedlizard55-lab/GEMSDOE32",
        "ref": "b983924b57781edd29b8e249c4923bf33d9902f6",
        "path": "docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "bytes": 219065,
        "sha256": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    },
    "GEMSDOE33-h33d-tip-stepover.tif": {
        "repo": "buffedlizard55-lab/GEMSDOE33",
        "ref": "f52533110fe62cd03e77f1228e9e5ecac412c463",
        "path": "docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
        "bytes": 917544,
        "sha256": "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757",
    },
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fetch(record: dict, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".partial")
    partial.unlink(missing_ok=True)
    try:
        downloaded = False
        if shutil.which("gh"):
            endpoint = f"repos/{record['repo']}/contents/{record['path']}?ref={record['ref']}"
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
            url = f"https://raw.githubusercontent.com/{record['repo']}/{record['ref']}/{record['path']}"
            request = urllib.request.Request(url, headers={"User-Agent": "GEMSDOE48-research/1.0"})
            with urllib.request.urlopen(request, timeout=180) as response, partial.open("wb") as output:
                shutil.copyfileobj(response, output, length=1 << 20)
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=ROOT / "data/source_mirrors")
    args = parser.parse_args()
    args.data_dir.mkdir(parents=True, exist_ok=True)
    for name, record in FILES.items():
        target = args.data_dir / name
        if not target.is_file() or target.stat().st_size != record["bytes"] or sha256_file(target) != record["sha256"]:
            fetch(record, target)
        digest = sha256_file(target)
        if target.stat().st_size != record["bytes"] or digest != record["sha256"]:
            target.unlink(missing_ok=True)
            raise SystemExit(f"Integrity check failed for {name}: {digest}")
        print(f"PASS {target} ({target.stat().st_size:,} bytes; sha256={digest})")
    print("NOTICE: public owner mirrors only; the competitions organizer has not authenticated these artifacts.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
