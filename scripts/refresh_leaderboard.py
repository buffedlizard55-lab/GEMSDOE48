#!/usr/bin/env python3
"""Offline parser for archived public-leaderboard HTML fixtures.

No retrieval, polling, or scraping is implemented. ``parse`` and
``parse_leaderboard_html`` operate only on caller-supplied strings; ``refresh``
requires an explicit local fixture. Direct execution exits with a disabled notice.
"""

from __future__ import annotations

from datetime import datetime, timezone
from html.parser import HTMLParser
import json
from pathlib import Path
import re

LEADERBOARD_URL = "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "docs/data/leaderboard.json"
MIN_ROWS = 5


class TableParser(HTMLParser):
    """Collect visible table rows, cell text, and anchor text/URLs."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tables: list[list[list[dict[str, object]]]] = []
        self._table: list[list[dict[str, object]]] | None = None
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
        elif tag == "br" and self._cell is not None:
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


def _header_columns(
    rows: list[list[dict[str, object]]],
) -> tuple[int | None, int | None, int | None]:
    """Return (header row, participant column, score column), when discoverable."""
    for row_index, row in enumerate(rows):
        if not any(cell.get("tag") == "th" for cell in row):
            continue
        header = [_clean(str(cell.get("text", ""))).lower() for cell in row]
        if not any(value.startswith("rank") for value in header):
            continue
        participant_col = next(
            (i for i, value in enumerate(header) if value.startswith("participant")), None
        )
        score_col = next(
            (i for i, value in enumerate(header) if "dw-tversky" in value or "tversky" in value),
            None,
        )
        return row_index, participant_col, score_col
    return None, None, None


def _participant_name(value: str) -> str:
    # Activity timestamps and submission counts are metadata, not part of a team name.
    value = re.split(r"\s*[·⸱•]\s*", value, maxsplit=1)[0]
    value = re.split(
        r"\s+\d+\s*(?:m|min|h|hr|d|day|w|week)s?(?:\s+\d+\s*(?:m|min|h|hr))?\s+ago\b",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    value = re.split(r"\s+\d+\s+submissions?\b", value, maxsplit=1, flags=re.IGNORECASE)[0]
    return _clean(value)


def _numeric_value(value: str) -> float | None:
    if re.fullmatch(r"\s*[+-]?(?:\d+(?:\.\d*)?|\.\d+)\s*", value):
        return float(value)
    return None


def _score_from_row(row: list[dict[str, object]], rank_index: int, score_col: int | None) -> float | None:
    if score_col is not None and score_col < len(row):
        score = _numeric_value(str(row[score_col].get("text", "")))
        if score is not None:
            return score
    for index, cell in enumerate(row):
        if index == rank_index:
            continue
        score = _numeric_value(str(cell.get("text", "")))
        if score is not None:
            return score
    return None


def _table_records(rows: list[list[dict[str, object]]]) -> list[dict[str, object]]:
    header_row, participant_col, score_col = _header_columns(rows)
    records: list[dict[str, object]] = []
    for row_index, row in enumerate(rows):
        if row_index == header_row:
            continue
        texts = [str(cell.get("text", "")) for cell in row]
        rank_index = next(
            (i for i, text in enumerate(texts) if re.search(r"#\s*\d+", text)), None
        )
        if rank_index is None:
            continue
        rank_match = re.search(r"#\s*(\d+)", texts[rank_index])
        if rank_match is None:
            continue
        rank = int(rank_match.group(1))

        score = _score_from_row(row, rank_index, score_col)
        full_text = " ".join(texts)
        submission_match = re.search(r"(\d+)\s+submissions?\b", full_text, flags=re.IGNORECASE)

        participant_cell: dict[str, object] | None = None
        if participant_col is not None and participant_col < len(row):
            participant_cell = row[participant_col]
        if participant_cell is None or not str(participant_cell.get("text", "")).strip():
            linked = [
                (cell, link)
                for i, cell in enumerate(row)
                if i != rank_index
                for link in cell.get("links", [])
                if isinstance(link, dict) and str(link.get("text", "")).strip()
            ]
            if linked:
                participant_cell = linked[0][0]
                participant_text = str(linked[0][1].get("text", ""))
            else:
                candidates = [
                    cell for i, cell in enumerate(row)
                    if i != rank_index
                    and str(cell.get("text", "")).strip()
                    and not re.fullmatch(r"\s*(?:0(?:\.\d+)?|1(?:\.0+)?)\s*", str(cell.get("text", "")))
                ]
                participant_cell = max(candidates, key=lambda cell: len(str(cell.get("text", ""))), default=None)
                participant_text = str(participant_cell.get("text", "")) if participant_cell else ""
        else:
            links = participant_cell.get("links", [])
            linked_text = next(
                (str(link.get("text", "")) for link in links
                 if isinstance(link, dict) and str(link.get("text", "")).strip()),
                "",
            ) if isinstance(links, list) else ""
            participant_text = linked_text or str(participant_cell.get("text", ""))

        participant = _participant_name(participant_text)
        if not participant:
            continue

        if score is not None and not 0.0 <= score <= 1.0:
            raise ValueError(f"score outside [0,1] at rank {rank}: {score}")
        record: dict[str, object] = {
            "rank": rank,
            "participant": participant,
            "best_public": score,
            "submissions": int(submission_match.group(1)) if submission_match else None,
        }
        if participant_cell is not None:
            links = participant_cell.get("links", [])
            first_link = next(
                (link for link in links if isinstance(link, dict) and link.get("href")), None
            ) if isinstance(links, list) else None
            if first_link:
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
    parser.close()
    candidates = [_table_records(table) for table in parser.tables]
    records = max(candidates, key=len, default=[])
    records.sort(key=lambda record: int(record["rank"]))
    if not records:
        raise ValueError("no leaderboard rows recognized; page structure may have changed")
    ranks = [int(record["rank"]) for record in records]
    if len(set(ranks)) != len(ranks):
        raise ValueError("duplicate rank values found in leaderboard")
    return records


def parse(html: str) -> list[dict[str, object]]:
    """Backward-compatible entry point used by the main-branch parser tests."""
    return parse_leaderboard_html(html)




def refresh(output: Path = DEFAULT_OUTPUT, html: str | None = None) -> dict[str, object]:
    """Write a fixture-derived snapshot only; never retrieve a page."""
    if html is None:
        raise RuntimeError("leaderboard retrieval is disabled; supply a local HTML fixture")
    rows = parse_leaderboard_html(html)
    if len(rows) < MIN_ROWS:
        raise ValueError(f"only {len(rows)} ranked rows parsed; refusing to replace the snapshot")
    payload: dict[str, object] = {
        "schema": "GEMSDOE48-leaderboard-v2",
        "source": LEADERBOARD_URL,
        "retrieved_utc": datetime.now(timezone.utc).isoformat(),
        "method": "offline parser on caller-supplied HTML fixture; no network fetch",
        "refresh_mode": "provided-html-fixture",
        "rows": rows,
        "attribution_warning": "Public leaderboard scores do not identify any local TIFF hash or owner-site artifact.",
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    return payload


def main() -> int:
    raise SystemExit(
        "Leaderboard retrieval is disabled. This module only parses supplied fixtures; "
        "no polling or scraping is implemented."
    )


if __name__ == "__main__":
    main()
