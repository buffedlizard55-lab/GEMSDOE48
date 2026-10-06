import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from refresh_leaderboard import parse_leaderboard_html, refresh


def test_parse_public_leaderboard_rows_and_user_profiles():
    html = """<!doctype html><table>
      <thead><tr><th>Rank</th><th>Team members</th><th>Participant</th>
      <th>Best public DW-Tversky (in descending order)</th><th>Shared work</th></tr></thead>
      <tbody>
        <tr><td>#1</td><td></td><td><a href="/users/alice/">alice</a><br>6h ago</td><td>0.3774</td><td></td></tr>
        <tr><td>#2</td><td></td><td>Team Geology<br>14h 49min ago</td><td>0.3195</td><td></td></tr>
      </tbody>
    </table>"""
    rows = parse_leaderboard_html(html)
    assert rows[0] == {
        "rank": 1,
        "participant": "alice",
        "score": 0.3774,
        "participant_url": "https://www.drivendata.org/users/alice/",
    }
    assert rows[1]["rank"] == 2
    assert rows[1]["participant"] == "Team Geology"
    assert rows[1]["score"] == 0.3195


def test_refresh_writes_auditable_feed(tmp_path):
    html = """<table><tr><th>Rank</th><th>Members</th><th>Participant</th>
      <th>Best public DW-Tversky</th></tr>
      <tr><td>#1</td><td></td><td><a href="/users/a/">a</a></td><td>0.4</td></tr></table>"""
    output = tmp_path / "leaderboard.json"
    result = refresh(output, html)
    stored = json.loads(output.read_text())
    assert stored["source_url"].endswith("/leaderboard/")
    assert stored["refresh_mode"] == "provided-html-fixture"
    assert stored["leader"]["score"] == 0.4
    assert result["entries"] == stored["entries"]


def test_unknown_or_invalid_leaderboard_fails_closed():
    with pytest.raises(ValueError, match="no leaderboard records"):
        parse_leaderboard_html("<html><body>Leaderboard changed</body></html>")

    html = """<table><tr><th>Rank</th><th>Members</th><th>Participant</th>
      <th>Best public DW-Tversky</th></tr>
      <tr><td>#1</td><td></td><td>team</td><td>1.2</td></tr></table>"""
    with pytest.raises(ValueError, match=r"outside \[0,1\]"):
        parse_leaderboard_html(html)
