import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from refresh_leaderboard import parse, parse_leaderboard_html, refresh


def test_parse_public_leaderboard_rows_and_user_profiles():
    html = """<!doctype html><table>
      <thead><tr><th>Rank</th><th>Team members</th><th>Participant</th>
      <th>Best public DW-Tversky (in descending order)</th><th>Shared work</th></tr></thead>
      <tbody>
        <tr><td>#1</td><td></td><td><a href="/users/alice/">alice</a><br>6h ago · 4 submissions</td><td>0.3774</td><td></td></tr>
        <tr><td>#2</td><td></td><td>Team Geology<br>14h 49min ago</td><td>0.3195</td><td></td></tr>
        <tr><td>#3</td><td></td><td>pending team</td><td></td><td></td></tr>
      </tbody>
    </table>"""
    rows = parse_leaderboard_html(html)
    assert rows[0] == {
        "rank": 1,
        "participant": "alice",
        "best_public": 0.3774,
        "submissions": 4,
        "participant_url": "https://www.drivendata.org/users/alice/",
    }
    assert rows[1]["rank"] == 2
    assert rows[1]["participant"] == "Team Geology"
    assert rows[1]["best_public"] == 0.3195
    assert rows[2]["participant"] == "pending team"
    assert rows[2]["best_public"] is None


def test_main_branch_fixture_compatibility():
    html = """<table><tr><th>Rank</th></tr>
      <tr><td>#1</td><td><a href="/users/xiaofanhu/" title="View xiaofanhu's profile"><img></a></td>
      <td><a title="View xiaofanhu's profile">xiaofanhu</a><br>6h ago · 11 submissions</td><td>0.3774</td><td></td></tr>
      <tr><td>#6</td><td>a b</td><td>Batik Shirt Brothers<br>14h ago · 21 submissions</td><td>0.3218</td><td></td></tr></table>"""
    rows = parse(html)
    assert rows[0]["rank"] == 1 and rows[0]["best_public"] == 0.3774
    assert rows[0]["submissions"] == 11 and "xiaofanhu" in rows[0]["participant"]
    assert rows[1]["rank"] == 6 and rows[1]["best_public"] == 0.3218
    assert rows[1]["participant"].startswith("Batik")


def test_refresh_writes_main_site_feed_schema(tmp_path):
    body = "".join(
        f"<tr><td>#{rank}</td><td>Team {rank}</td><td>0.{rank:04d}</td><td>{rank} submissions</td></tr>"
        for rank in range(1, 6)
    )
    html = (
        "<table><tr><th>Rank</th><th>Participant</th>"
        "<th>Best public DW-Tversky</th><th>Submissions</th></tr>"
        + body + "</table>"
    )
    output = tmp_path / "leaderboard.json"
    result = refresh(output, html)
    stored = json.loads(output.read_text())
    assert stored["source"].endswith("/leaderboard/")
    assert stored["refresh_mode"] == "provided-html-fixture"
    assert len(stored["rows"]) == 5
    assert stored["rows"][0]["best_public"] == 0.0001
    assert result["rows"] == stored["rows"]


def test_unknown_or_invalid_leaderboard_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="no leaderboard rows"):
        parse_leaderboard_html("<html><body>Leaderboard changed</body></html>")

    html = """<table><tr><th>Rank</th><th>Participant</th><th>Best public DW-Tversky</th></tr>
      <tr><td>#1</td><td>team</td><td>1.2</td></tr></table>"""
    with pytest.raises(ValueError, match=r"outside \[0,1\]"):
        parse_leaderboard_html(html)

    output = tmp_path / "keep.json"
    output.write_text('{"old": true}\n')
    with pytest.raises(ValueError, match="only 1 ranked rows"):
        refresh(output, "<table><tr><th>Rank</th><th>Participant</th></tr><tr><td>#1</td><td>team</td></tr></table>")
    assert json.loads(output.read_text()) == {"old": True}
