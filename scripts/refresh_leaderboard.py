"""Snapshot the public leaderboard into docs/data/leaderboard.json (runs in GitHub Actions).

Tolerant HTML parse: each <tr> with a '#<rank>' cell; participant = first "View X's profile" title
or the participant cell text; score = first 0.dddd number.  Keeps the old file if parsing yields
< 5 rows (fail-safe, never blanks the feed)."""
import re, json, sys, datetime, pathlib, urllib.request, html as H
URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
OUT = pathlib.Path(__file__).resolve().parents[1] / "docs/data/leaderboard.json"
def parse(page):
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        m = re.search(r"#\s*(\d+)", tr)
        if not m: continue
        who = re.search(r"title=\"View ([^\"]+?)'s profile\"", tr)
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        txt = [re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", t))).strip() for t in tds]
        score = re.search(r"\b0\.\d{4}\b", " ".join(txt[3:4] or txt))
        part = (txt[2].split(" ")[0] if len(txt) > 2 and txt[2] else (who.group(1) if who else ""))
        if len(txt) > 2 and who is None: part = txt[2]
        nsub = re.search(r"(\d+)\s+submissions", " ".join(txt))
        rows.append(dict(rank=int(m.group(1)), participant=part or (who.group(1) if who else ""),
                         best_public=float(score.group(0)) if score else None,
                         submissions=int(nsub.group(1)) if nsub else None))
    return rows
if __name__ == "__main__":
    page = urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=60).read().decode("utf-8", "replace")
    rows = parse(page)
    if len(rows) < 5: print("parse yielded", len(rows), "rows; keeping previous snapshot"); sys.exit(0)
    json.dump({"source": URL, "retrieved_utc": datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z",
               "method": "scripts/refresh_leaderboard.py (GitHub Actions)", "rows": rows}, open(OUT, "w"), indent=1)
    print("rows", len(rows), rows[:3])
