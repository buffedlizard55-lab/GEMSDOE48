"""Parser-only compatibility for an archived leaderboard snapshot workflow.

Network retrieval and publication are intentionally disabled. The official
Terms of Use were reviewed and this repository does not poll or scrape the site.
The pure ``parse(page)`` helper remains for tests of the old fixture parser only.
"""
import html as H
import re

URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"


def parse(page: str) -> list[dict]:
    """Parse a supplied HTML fixture; this function performs no network access."""
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", page, re.S):
        m = re.search(r"#\s*(\d+)", tr)
        if not m:
            continue
        who = re.search(r"title=\"View ([^\"]+?)'s profile\"", tr)
        tds = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        txt = [re.sub(r"\s+", " ", H.unescape(re.sub(r"<[^>]+>", " ", t))).strip() for t in tds]
        score = re.search(r"\b0\.\d{4}\b", " ".join(txt[3:4] or txt))
        part = (txt[2].split(" ")[0] if len(txt) > 2 and txt[2] else (who.group(1) if who else ""))
        if len(txt) > 2 and who is None:
            part = txt[2]
        nsub = re.search(r"(\d+)\s+submissions", " ".join(txt))
        rows.append(dict(
            rank=int(m.group(1)),
            participant=part or (who.group(1) if who else ""),
            best_public=float(score.group(0)) if score else None,
            submissions=int(nsub.group(1)) if nsub else None,
        ))
    return rows


if __name__ == "__main__":
    raise SystemExit(
        "Leaderboard retrieval is disabled. No polling or scraping is implemented; "
        "review the official Terms of Use before any future one-time observation."
    )
