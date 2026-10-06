#!/usr/bin/env bash
# Reproduce the exact hash-pinned inputs. Requires authenticated GitHub CLI.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; D="$ROOT/data/raw"; mkdir -p "$D/external"
fetch(){ local repo="$1" path="$2" ref="$3" out="$4" want="$5"; gh api "repos/$repo/contents/$path?ref=$ref" -H 'Accept: application/vnd.github.raw' > "$out.partial"; got="$(sha256sum "$out.partial"|cut -d' ' -f1)"; test "$got" = "$want" || { echo "HASH MISMATCH $out" >&2; rm -f "$out.partial"; exit 1; }; mv "$out.partial" "$out"; }
fetch buffedlizard55-lab/GEMSDOE32 docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif b983924b57781edd29b8e249c4923bf33d9902f6 "$D/dotted.tif" c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9
fetch buffedlizard55-lab/GEMSDOE33 docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif f52533110fe62cd03e77f1228e9e5ecac412c463 "$D/tip.tif" 87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757
REF=07345ea0604953d7efb858d9cfbc21e20c7aca0b
fetch buffedlizard55-lab/GEMSDOE24 data/bridge/sample_submission.tif "$REF" "$D/sample_submission.tif" 2176d08e485aa2cd2860ce8df539db4faf4d76163b38a4dd8c30a40454d35cbc
fetch buffedlizard55-lab/GEMSDOE24 data/bridge/labels.tif "$REF" "$D/labels.tif" 7ba308ccdc4418b31a178f4f1ef21aaa6e152e4028f2f6f64b01f7eb25ae4093
fetch buffedlizard55-lab/GEMSDOE24 data/external/derived_sgmc_faults_100m_u8.tif "$REF" "$D/external/derived_sgmc_faults_100m_u8.tif" 643cbe992ef4ba37588fb469163ed8291e3ceb23d6c1f78a3cfaa462430c2da0
echo 'All five inputs restored and SHA-256 verified.'
