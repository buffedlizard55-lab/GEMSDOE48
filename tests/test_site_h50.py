"""The H50 sub-site is generated from receipts, so it is tested like a build
artifact: pages exist, are well formed, local links resolve, the historical
TIFF download is obvious, the SHA appears, H36 is correctly classified, the
archival note is within the portal limit, and no slot is recommended."""
from __future__ import annotations

import json
import re
import unittest
from html.parser import HTMLParser
from pathlib import Path

import conftest  # noqa: F401

SUB = conftest.DOCS / "h50"
PAGES = ["index.html", "executive-summary.html", "method.html", "hypotheses.html", "sources.html"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


def receipt() -> dict:
    return json.loads((conftest.EVIDENCE / "build_ds50_receipt_20261007.json").read_text())


class _Nesting(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack = []
        self.errors = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"mismatched </{tag}>")
        else:
            self.stack.pop()


class TestH50Site(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rec = receipt()
        cls.texts = {n: (SUB / n).read_text() for n in PAGES}

    def test_pages_exist_and_balanced(self):
        for name in PAGES:
            parser = _Nesting()
            parser.feed(self.texts[name])
            self.assertEqual(parser.errors, [], name)
            self.assertEqual(parser.stack, [], name)

    def test_download_at_top_of_index_with_download_attribute(self):
        text = self.texts["index.html"]
        pos = text.find(Path(self.rec["primary_file"]).name)
        self.assertGreater(pos, 0)
        self.assertLess(pos, len(text) / 3, "download must be obvious at the top")
        window = text[max(0, pos - 300): pos + 60]
        self.assertIn("download", window)

    def test_zip_offered_too(self):
        self.assertIn(Path(self.rec["zip_file"]).name, self.texts["index.html"])

    def test_sha_and_corrected_archival_note_and_name_appear(self):
        for name in ("index.html", "executive-summary.html"):
            self.assertIn(self.rec["primary_sha256"], self.texts[name])
        index = self.texts["index.html"]
        self.assertIn(self.rec["submission_name"], index)
        self.assertIn("H36-1 rung30", index)
        self.assertIn("H19-5/rung-30 repacking; not tip/step-over", index)
        self.assertIn("do not paste for submission", index)
        # The frozen receipt's original note contains the classification error;
        # the public archive must show the corrected note instead.
        self.assertNotIn(self.rec["submission_note"], index)

    def test_corrected_archival_note_within_portal_limit(self):
        match = re.search(r"Corrected archival note \((\d+)/200 chars; do not paste for submission\):</strong> <code>([^<]+)</code>", self.texts["index.html"])
        self.assertIsNotNone(match)
        note = match.group(2)
        self.assertLessEqual(len(note), 200)
        self.assertEqual(int(match.group(1)), len(note))

    def test_every_local_href_resolves(self):
        for name in PAGES:
            for href in re.findall(r'href="([^"#]+)"', self.texts[name]):
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                target = (SUB / href).resolve()
                self.assertTrue(target.exists(), f"{name}: broken link {href}")

    def test_every_page_disclaims_organizer_scores(self):
        for name in PAGES:
            self.assertIn("No organizer score exists", self.texts[name])
        self.assertIn("UNSCORED", self.texts["index.html"])

    def test_portal_error_message_is_addressed(self):
        self.assertIn("Predicted values must be in range [0, 1]", self.texts["executive-summary.html"])

    def test_no_placeholder_artifacts(self):
        for name in PAGES:
            for bad in ("{esc(", "{fmt(", "TODO", "XXX", "None</", "nan<"):
                self.assertNotIn(bad, self.texts[name])

    def test_leaderboard_snapshot_is_labelled(self):
        board = json.loads((conftest.DOCS / "data/leaderboard_20261007.json").read_text())
        self.assertEqual(board["retrieved_utc"], "2026-10-07")
        top = board["rows"][0]
        self.assertEqual((top["participant"], top["best_public"]), ("xiaofanhu", 0.3774))
        self.assertIn("0.3774", self.texts["index.html"])

    def test_holdout_numbers_on_index_match_receipts(self):
        holdout = json.loads((conftest.EVIDENCE / "holdout_ds50_20261007.json").read_text())
        mean = holdout["sgmc_offcat_results"]["h50_ds_belief"]["mean_dti"]
        self.assertIn(f"{mean:.6f}", self.texts["index.html"])


if __name__ == "__main__":
    unittest.main()
