"""Make ``src/`` importable and expose shared paths to the test suite.

The suite uses only the standard library plus the repository's existing
dependencies (numpy, rasterio, scipy) so that it runs with

    python3 -m unittest discover -s tests -t .

from a clean checkout, with no installation step and no network access.
"""
from __future__ import annotations

import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
SRC = REPO / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

DOCS = REPO / "docs"
DOWNLOADS = DOCS / "downloads"
REGISTRY = REPO / "registry"
EVIDENCE = REPO / "evidence"
DATA = REPO / "data"


def repo_path(*parts: str) -> pathlib.Path:
    return REPO.joinpath(*parts)
