import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_project_scripts_parse():
    for path in (ROOT / "scripts").glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
