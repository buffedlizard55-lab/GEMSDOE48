#!/usr/bin/env bash
# Full reproducible pipeline: fetch (hash-verified) -> calibrate instruments -> fuse -> write+audit -> figures -> site -> tests
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/fetch_mirrors.py
python3 scripts/calibrate_proxy.py      # SGMC proxy vs live (evidence/proxy_calibration.json)
python3 scripts/run_lsi.py              # live-score inversion + LOO (evidence/lsi_validation.json)
python3 scripts/build_ds.py             # H48-1 variants + instruments (evidence/ds_variants.json)
python3 scripts/write_submission.py     # submission + diagnostics + receipt
python3 scripts/risk_and_figures.py     # risk bound + figures
python3 scripts/build_site.py
python3 -m pytest -q tests
