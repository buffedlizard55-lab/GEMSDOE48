import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from refresh_leaderboard import parse
HTML = """<table><tr><th>Rank</th></tr>
<tr><td>#1</td><td><a href="/users/xiaofanhu/" title="View xiaofanhu's profile"><img></a></td>
<td><a title="View xiaofanhu's profile">xiaofanhu</a><br>6h ago ⸱ 11 submissions</td><td>0.3774</td><td></td></tr>
<tr><td>#6</td><td>a b</td><td>Batik Shirt Brothers<br>14h ago ⸱ 21 submissions</td><td>0.3218</td><td></td></tr></table>"""
def test_parse():
    r = parse(HTML)
    assert r[0]["rank"] == 1 and r[0]["best_public"] == 0.3774 and r[0]["submissions"] == 11
    assert "xiaofanhu" in r[0]["participant"]
    assert r[1]["rank"] == 6 and r[1]["best_public"] == 0.3218 and r[1]["participant"].startswith("Batik")
