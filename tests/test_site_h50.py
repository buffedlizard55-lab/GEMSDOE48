"""Integrity tests for the manually maintained, non-submission H50 archive."""
from __future__ import annotations

import json
import re
import subprocess
import sys
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
        cls.texts = {n: (SUB / n).read_text(encoding="utf-8") for n in PAGES}

    def test_pages_exist_are_balanced_and_archived(self):
        for name in PAGES:
            with self.subTest(page=name):
                text = self.texts[name]
                self.assertTrue((SUB / name).exists())
                parser = _Nesting()
                parser.feed(text)
                self.assertEqual(parser.errors, [], name)
                self.assertEqual(parser.stack, [], name)
                self.assertIn("archive", text.lower())
                self.assertTrue("not cleared" in text.lower() or "not ok to submit" in text.lower()
                                or "not current" in text.lower() or "withdrawn" in text.lower())

    def test_archived_downloads_are_explicitly_not_submission_recommendations(self):
        text = self.texts["index.html"]
        self.assertIn("NOT OK TO SUBMIT", text)
        self.assertIn("OK TO DOWNLOAD FOR AUDIT; NOT CLEARED TO SUBMIT", text)
        names = ["gemsdoe48-h50-ds-b2xh36rung30-20261007-5b59e106-nan.tif",
                 "gemsdoe48-h50-ds-b2xh36rung30-20261007-5b59e106-zeros.zip"]
        for name in names:
            self.assertIn(name, text)
            self.assertTrue((conftest.DOWNLOADS / name).exists())
        self.assertIn(self.rec["primary_sha256"], text)

    def test_h50_parent_attribution_is_clearly_unverified(self):
        text = self.texts["index.html"]
        self.assertIn("owner-reported", text)
        self.assertIn("No organizer receipt links either score to these local parent bytes", text)
        self.assertIn("No organizer score", text)

    def test_metric_and_ds_terms_are_correct(self):
        method = self.texts["method.html"]
        self.assertIn("FPw=S−TPw", method)
        self.assertIn("not a general identity", method)
        self.assertIn("not a universal", method)
        self.assertIn("m(Θ)", method)
        self.assertIn("K", method)
        self.assertIn("ignorance", method.lower())
        self.assertIn("conflict", method.lower())
        self.assertNotIn("break-even credit bar (0.2·0.26", method)

    def test_current_hypothesis_links_preserve_failures_and_gate(self):
        hypotheses = self.texts["hypotheses.html"]
        self.assertIn("../hypotheses.html", hypotheses)
        self.assertIn("H56-F", hypotheses)
        self.assertIn("H57-A", hypotheses)
        self.assertIn("not a universal per-dot threshold", self.texts["method.html"])
        self.assertIn("withdrawn", hypotheses.lower())
        self.assertIn("NOT CLEARED TO SUBMIT", self.texts["executive-summary.html"])
        self.assertIn("NOT CLEARED TO SUBMIT", self.texts["sources.html"])
        self.assertIn("NOT CLEARED TO SUBMIT", self.texts["executive-summary.html"])

    def test_all_local_links_resolve(self):
        for name, text in self.texts.items():
            for href in re.findall(r'href="([^"#]+)"', text):
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                with self.subTest(page=name, href=href):
                    self.assertTrue((SUB / href).resolve().exists(), f"broken link: {href}")

    def test_receipts_distinguish_local_validation_from_performance(self):
        build = self.rec
        self.assertEqual(build["validity_status"], "HISTORICAL_LOCAL_BUILD_AND_PROXY_DIAGNOSTICS_ONLY_NOT_CLEARED_TO_SUBMIT")
        self.assertIn("NOT CLEARED TO SUBMIT", build["promotion_decision"])
        self.assertIn("no organizer receipt", build["leaderboard_linkage"])
        self.assertIn("not verified as portal-safe", build["encoding"].lower())
        self.assertIn("not evidence of organizer acceptance", build["encoding"].lower())
        superseded = json.loads((conftest.EVIDENCE / "build_ds50_v1_anchor100_withdrawn_receipt_20261007.json").read_text())
        self.assertEqual(superseded["validity_status"], "WITHDRAWN_HISTORICAL_BUILD_FORENSIC_ONLY")
        self.assertEqual(superseded["promotion_decision"], "NOT CLEARED TO SUBMIT")
        self.assertIn("not verified as portal-safe", superseded["encoding"].lower())
        self.assertIn("not evidence of organizer acceptance", superseded["encoding"].lower())
        holdout = json.loads((conftest.EVIDENCE / "holdout_ds50_20261007.json").read_text())
        self.assertEqual(holdout["validity_status"], "PUBLIC_PROXY_DIAGNOSTIC_ONLY_NOT_PRIVATE_LABEL_PERFORMANCE")
        self.assertEqual(holdout["promotion_decision"], "NOT CLEARED TO SUBMIT")

    def test_retired_builder_refuses_and_leaves_pages_unchanged(self):
        before = {name: (SUB / name).read_bytes() for name in PAGES}
        script = conftest.repo_path("scripts/build_site_h50.py")
        result = subprocess.run([sys.executable, str(script)], cwd=str(conftest.repo_path(".")),
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retired", result.stderr + result.stdout)
        self.assertEqual(before, {name: (SUB / name).read_bytes() for name in PAGES})

    def test_no_stale_upload_note_or_score_projection_is_visible(self):
        joined = "\n".join(self.texts.values())
        self.assertNotIn("do not paste for submission", joined)
        self.assertIn("live-equivalent", joined.lower())
        self.assertIn("withdrawn", self.texts["hypotheses.html"].lower())
        self.assertNotIn("0.0247±0.0005", joined)


if __name__ == "__main__":
    unittest.main()
