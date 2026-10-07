#!/usr/bin/env python3
"""Restore the H55 inputs that live under the git-ignored ``data/raw/`` tree.

Each file is fetched from a hash-pinned public GitHub mirror with ``gh api`` and
**fails closed** if the restored bytes do not match the pinned SHA-256.  No
DrivenData host is ever contacted (its terms of use prohibit automatic access);
the mirrors are third-party owner copies and are *not* organizer-authenticated.

Usage:  python scripts/restore_h55_inputs.py [--only KEY ...] [--force]

Optional heavy extra (off by default, 419 MB in five shards):
        python scripts/restore_h55_inputs.py --with-official-features
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GEMSDOE24_REF = "07345ea0604953d7efb858d9cfbc21e20c7aca0b"
GEMSDOE_REF = "c0c06ac82178f26b94fce3397036ef8f12a2f3a0"
GEMSDOE29_REF = "main"

MIRRORS = {
    "backbone_dense": dict(
        repo="buffedlizard55-lab/GEMSDOE24", ref=GEMSDOE24_REF,
        path="inputs/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif",
        dest="data/raw/scored/h19_5_01922.tif",
        sha256="ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d",
        live=0.1922),
    "d15_dotted": dict(
        repo="buffedlizard55-lab/GEMSDOE24", ref=GEMSDOE24_REF,
        path="docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
        dest="data/raw/scored/d15_02477.tif",
        sha256="68d0e2e4fcc594f9a23f56c44b885fee733d026d39be55e18ad2a07289525310",
        live=0.2477),
    "sgmc_offcat_44k": dict(
        repo="buffedlizard55-lab/GEMSDOE29", ref=GEMSDOE29_REF,
        path="docs/downloads/gemsdoe29-sgmc-off-catalogue-44k-20261003-c8dcd780e3fd-nan.tif",
        dest="data/raw/scored/sgmc44k_00512.tif",
        sha256="9b83158bde01cd5d42e38229d70d01e67cecd2514eeb5fa8d1f3ab6851469dad",
        live=0.0512),
    "h36_rung30": dict(
        repo="buffedlizard55-lab/GEMSDOE28", ref="main",
        path="docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
        dest="data/raw/scored/h36_rung30_02710.tif",
        sha256="5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641",
        live=0.2710),
    "h32_prethin_tip": dict(
        repo="buffedlizard55-lab/GEMSDOE28", ref="main",
        path="docs/downloads/gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif",
        dest="data/raw/scored/h32_prethin_tip_02649.tif",
        sha256="04d31922f5c1ea4016984fc470ab2b0ff8e266c615792f0e86020da3b940d3ff",
        live=0.2649),
    "conduit_csv": dict(
        repo="buffedlizard55-lab/GEMSDOE24", ref=GEMSDOE24_REF,
        path="data/external/gdr_wellspring_in_footprint.csv",
        dest="data/raw/external/gdr_wellspring_in_footprint.csv",
        sha256="122718e65bdf55aab0ee12ad20d80062f0deb1de957225a61ad880dd5dc196ea",
        live=None),
    "geodawn_extensions_u8": dict(
        repo="buffedlizard55-lab/GEMSDOE24", ref=GEMSDOE24_REF,
        path="data/external/geodawn_extensions_u8.tif",
        dest="data/raw/external/geodawn_extensions_u8.tif",
        sha256="a35a9c6d2a14786f4dab85481ee59769213072f5dab5b2535ea82ae4d9bb7d9b",
        live=None),
    "qfaults_traces": dict(
        repo="buffedlizard55-lab/GEMSDOE24", ref=GEMSDOE24_REF,
        path="data/external/gdr_qfaults_traces.csv",
        dest="data/raw/external/gdr_qfaults_traces.csv",
        sha256="9702f2e5c382a4f472ae834d22b94990983b059677a37adfafd51c50f75e643c",
        live=None),
    "volcanic_vents": dict(
        repo="buffedlizard55-lab/GEMSDOE24", ref=GEMSDOE24_REF,
        path="data/external/gdr_volcanic_vents_in_footprint.csv",
        dest="data/raw/external/gdr_volcanic_vents.csv",
        sha256="f91bafbaccaaf2754e71d60434fc0f9eb2c7b880c6e714883f4974542ff6a0bf",
        live=None),
}

OFFICIAL_FEATURES = dict(
    repo="buffedlizard55-lab/GEMSDOE", ref=GEMSDOE_REF,
    parts=[f"data/bridge/gems-geodawn-numerical-features.tif.part-{i:03d}" for i in range(5)],
    dest="data/raw/training_features.tif",
    sha256="4371c82e3b8339b807bdffcf4ef59a225520fe2988d521be208ae33743123bc5",
    bytes=418912844)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def gh_raw(repo: str, path: str, ref: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    query = f"repos/{repo}/contents/{path}?ref={ref}"
    with dest.open("wb") as handle:
        subprocess.run(["gh", "api", query, "-H", "Accept: application/vnd.github.raw"],
                       stdout=handle, check=True)


def restore(spec: dict, *, force: bool = False) -> bool:
    dest = ROOT / spec["dest"]
    if dest.exists() and not force and sha256_file(dest) == spec["sha256"]:
        print(f"CACHED  {spec['dest']}")
        return True
    try:
        gh_raw(spec["repo"], spec["path"], spec["ref"], dest)
    except subprocess.CalledProcessError as exc:  # pragma: no cover - network dependent
        print(f"FAIL    {spec['dest']}: {exc}", file=sys.stderr)
        return False
    got = sha256_file(dest)
    if got != spec["sha256"]:
        dest.unlink(missing_ok=True)
        print(f"MISMATCH {spec['dest']}: expected {spec['sha256']}, got {got}", file=sys.stderr)
        return False
    print(f"OK      {spec['dest']}  {dest.stat().st_size} bytes  {got[:12]}")
    return True


def restore_official_features(*, force: bool = False) -> bool:
    dest = ROOT / OFFICIAL_FEATURES["dest"]
    if dest.exists() and not force and sha256_file(dest) == OFFICIAL_FEATURES["sha256"]:
        print(f"CACHED  {OFFICIAL_FEATURES['dest']}")
        return True
    tmp = dest.parent / ".training_features.parts"
    tmp.mkdir(parents=True, exist_ok=True)
    with dest.open("wb") as out:
        for part in OFFICIAL_FEATURES["parts"]:
            shard = tmp / Path(part).name
            try:
                gh_raw(OFFICIAL_FEATURES["repo"], part, OFFICIAL_FEATURES["ref"], shard)
            except subprocess.CalledProcessError as exc:  # pragma: no cover
                print(f"FAIL    {part}: {exc}", file=sys.stderr)
                return False
            with shard.open("rb") as handle:
                while chunk := handle.read(1 << 22):
                    out.write(chunk)
            shard.unlink()
    tmp.rmdir()
    got = sha256_file(dest)
    if got != OFFICIAL_FEATURES["sha256"]:
        print(f"MISMATCH {dest}: expected {OFFICIAL_FEATURES['sha256']}, got {got}", file=sys.stderr)
        return False
    print(f"OK      {OFFICIAL_FEATURES['dest']}  {dest.stat().st_size} bytes  {got[:12]}  "
          f"(19 bands, official GeoDAWN numerical features; NOT organizer-authenticated)")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--only", nargs="*", default=None, help="subset of mirror keys")
    parser.add_argument("--force", action="store_true", help="re-download even if the hash matches")
    parser.add_argument("--with-official-features", action="store_true",
                        help="also restore the 419 MB 19-band training_features.tif (5 shards)")
    args = parser.parse_args()
    keys = args.only or list(MIRRORS)
    unknown = [k for k in keys if k not in MIRRORS]
    if unknown:
        raise SystemExit(f"unknown mirror keys: {unknown}; available: {sorted(MIRRORS)}")
    failures = [k for k in keys if not restore(MIRRORS[k], force=args.force)]
    if args.with_official_features and not restore_official_features(force=args.force):
        failures.append("official_features")
    if failures:
        raise SystemExit(f"FAILED to restore: {failures}")
    print("all requested mirrors restored and SHA-256 verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
