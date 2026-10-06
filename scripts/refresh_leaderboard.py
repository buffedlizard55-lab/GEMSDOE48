#!/usr/bin/env python3
"""Fetch the public DrivenData leaderboard and write a small static JSON feed.

No login or cookies are used. A failed or unrecognized page is a hard error so
an HTML redesign cannot silently publish a stale or fabricated leaderboard.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.error import URLError
from urllib.request import Request, urlopen

LEADERBOARD_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "docs/data/leaderboard.json"


class TableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[dict[str, object]]] = []
        self._table: list[dict[str, object]] | None = None
        self._row: list[dict[str, object]] | None = None
        self._cell: dict[str, object] | None = None
        self._anchor: dict[str, object] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table":
            self._table = []
        elif tag == "tr" and self._table is not None:
            self._row = []
        elif tag in {"th", "td"} and self._row is not None:
            self._cell = {"tag": tag, "parts": [], "links": []}
        elif tag == "a" and self._cell is not None:
            self._anchor = {"href": attributes.get("href"), "parts": []}
        elif tag in {"br", "img"} and self._cell is not None:
            self._cell["parts"].append(" ")

    def handle_data(self, data: str) -> None:
        if self._cell is not None:
            self._cell["parts"].append(data)
            if self._anchor is not None:
                self._anchor["parts"].append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag == "a" and self._anchor is not None and self._cell is not None:
            self._cell["links"].append({
                "href": self._anchor.get("href"),
                "text": _clean("".join(self._anchor["parts"])),
            })
            self._anchor = None
        elif tag in {"th", "td"} and self._cell is not None and self._row is not None:
            self._cell["text"] = _clean("".join(self._cell["parts"]))
            self._row.append(self._cell)
            self._cell = None
        elif tag == "tr" and self._row is not None and self._table is not None:
            if self._row:
                self._table.append(self._row)
            self._row = None
        elif tag == "table" and self._table is not None:
            self.tables.append(self._table)
            self._table = None


def _clean(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def _table_records(rows: list[list[dict[str, object]]]) -> list[dict[str, object]]:
    if not rows:
        return []
    header = [_clean(str(cell.get("text", ""))).lower() for cell in rows[0]]
    rank_col = next((i for i, value in enumerate(header) if value.startswith("rank")), None)
    participant_col = next((i for i, value in enumerate(header) if value.startswith("participant")), None)
    score_col = next((i for i, value in enumerate(header) if "dw-tversky" in value or "tversky" in value), None)
    if rank_col is None or participant_col is None or score_col is None:
        return []

    records: list[dict[str, object]] = []
    for row in rows[1:]:
        if max(rank_col, participant_col, score_col) >= len(row):
            continue
        rank_text = str(row[rank_col].get("text", ""))
        rank_match = re.search(r"#?\s*(\d+)", rank_text)
        if not rank_match:
            continue
        participant_cell = row[participant_col]
        links = participant_cell.get("links", [])
        first_link = next((link for link in links if link.get("text")), None) if isinstance(links, list) else None
        participant_text = str(first_link["text"]) if first_link else str(participant_cell.get("text", ""))
        # Public rows sometimes append activity/submission counts to the name.
        participant = re.split(r"\s+(?:\d+\s*(?:m|min|h|hr|d|day|w|week)\b|\d+\s+submissions?\b|\u00b7)", participant_text, maxsplit=1, flags=re.I)[0].strip()
        if not participant:
            continue
        score_text = str(row[score_col].get("text", ""))
        score_match = re.search(r"(?<!\d)(\d+(?:\.\d+)?)(?!\d)", score_text)
        if not score_match:
            continue
        record: dict[str, object] = {
            "rank": int(rank_match.group(1)),
            "participant": participant,
            "score": float(score_match.group(1)),
        }
        if first_link and first_link.get("href"):
            href = str(first_link["href"])
            if href.startswith("/"):
                href = "https://www.drivendata.org" + href
            if href.startswith("https://www.drivendata.org/"):
                record["participant_url"] = href
        records.append(record)
    return records


def parse_leaderboard_html(html: str) -> list[dict[str, object]]:
    parser = TableParser()
    parser.feed(html)
    candidates = [_table_records(table) for table in parser.tables]
    records = max(candidates, key=len, default=[])
    records.sort(key=lambda record: int(record["rank"]))
    if not records:
        raise ValueError("no leaderboard records recognized; page structure may have changed")
    if len({record["rank"] for record in records}) != len(records):
        raise ValueError("duplicate rank values found in leaderboard")
    if any(not 0.0 <= float(record["score"]) <= 1.0 for record in records):
        raise ValueError("leaderboard score outside [0,1]")
    return records


def fetch_html(url: str = LEADERBOARD_URL) -> str:
    request = Request(url, headers={"User-Agent": "GEMSDOE48-public-leaderboard-feed/1.0"})
    try:
        with urlopen(request, timeout=45) as response:
            if response.status != 200:
                raise RuntimeError(f"leaderboard HTTP status {response.status}")
            return response.read().decode("utf-8", errors="replace")
    except URLError as error:
        raise RuntimeError(f"could not retrieve public leaderboard: {error}") from error


def refresh(output: Path = DEFAULT_OUTPUT, html: str | None = None) -> dict[str, object]:
    page = fetch_html() if html is None else html
    records = parse_leaderboard_html(page)
    payload: dict[str, object] = {
        "schema": "GEMSDOE48-leaderboard-v1",
        "observed_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_url": LEADERBOARD_URL,
        "refresh_mode": "live-http-fetch" if html is None else "provided-html-fixture",
        "count": len(records),
        "leader": records[0],
        "entries": records,
        "attribution_warning": "Public leaderboard scores are participant scores and are not linked to any local TIFF hash or owner-site artifact.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--html-file", type=Path, help="parse a saved page (for tests/offline verification)")
    args = parser.parse_args()
    html = args.html_file.read_text(encoding="utf-8") if args.html_file else None
    payload = refresh(args.output, html)
    print(json.dumps({
        "output": str(args.output),
        "observed_at_utc": payload["observed_at_utc"],
        "entries": payload["count"],
        "leader": payload["leader"],
    }, indent=2))


if __name__ == "__main__":
    main()
