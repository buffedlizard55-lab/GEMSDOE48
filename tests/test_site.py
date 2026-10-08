"""Integrity tests for the manually maintained DS48 forensic archive.

The old generator embedded invalidated live-score inferences and must never
rewrite the corrected pages. These tests check page integrity, safe links,
explicit archive/decision status, and the builder's fail-closed behavior.
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
import unittest
from html.parser import HTMLParser

import conftest  # noqa: F401

SUB = conftest.DOCS / "ds48-fusion"
PAGES = ["index.html", "executive-summary.html", "research.html",
         "hypotheses.html", "sources.html", "irregularities.html"]
FOREIGN_PAGES = ["index.html", "executive-summary.html", "hypotheses.html",
                 "irregularities.html", "method.html", "leaderboard.html"]
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link",
        "meta", "param", "source", "track", "wbr"}


class _Nesting(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack: list[tuple[str, tuple[int, int]]] = []
        self.errors: list[str] = []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if not self.stack:
            self.errors.append(f"stray </{tag}> at {self.getpos()}")
        elif self.stack[-1][0] != tag:
            self.errors.append(f"</{tag}> closes <{self.stack[-1][0]}> at {self.getpos()}")
            self.stack.pop()
        else:
            self.stack.pop()


class TestArchivePages(unittest.TestCase):
    def test_all_pages_exist_and_are_well_formed(self):
        for name in PAGES:
            with self.subTest(page=name):
                path = SUB / name
                self.assertTrue(path.exists(), f"missing {name}")
                self.assertGreater(path.stat().st_size, 900)
                parser = _Nesting()
                parser.feed(path.read_text(encoding="utf-8"))
                self.assertEqual(parser.errors, [])
                self.assertEqual(parser.stack, [])

    def test_every_page_has_historical_archive_context(self):
        for name in PAGES:
            with self.subTest(page=name):
                text = (SUB / name).read_text(encoding="utf-8")
                lower = text.lower()
                self.assertTrue("historical" in lower or "archive" in lower)
                self.assertIn("not", lower)
                self.assertTrue("not cleared" in lower or "not ok to submit" in lower
                                or "not current" in lower or "withdrawn" in lower
                                or "not verified" in lower)

    def test_metric_inversion_and_universal_threshold_are_withdrawn(self):
        research = (SUB / "research.html").read_text(encoding="utf-8")
        index = (SUB / "index.html").read_text(encoding="utf-8")
        self.assertIn("FPw", research)
        self.assertIn("not a general identity", research)
        self.assertIn("private-label", research)
        self.assertIn("fpw=s−tpw", index.lower())
        self.assertIn("generally not complements", index.lower())
        self.assertIn("private-label", index.lower())
        self.assertIn("universal", research.lower())
        self.assertIn("not verified", index.lower())

    def test_ignorance_conflict_terminology_is_distinguished(self):
        index = (SUB / "index.html").read_text(encoding="utf-8")
        corrections = (SUB / "irregularities.html").read_text(encoding="utf-8")
        self.assertIn("ignorance", index.lower())
        self.assertIn("separate raw conjunctive conflict", index.lower())
        self.assertIn("Yager", corrections)
        self.assertIn("m(Θ)+K", corrections)

    def test_current_project_links_are_present(self):
        index = (SUB / "index.html").read_text(encoding="utf-8")
        hypotheses = (SUB / "hypotheses.html").read_text(encoding="utf-8")
        self.assertIn("../index.html", index)
        self.assertIn("../validation.html", index)
        self.assertIn("../hypotheses.html", hypotheses)
        self.assertIn("h56-pruning-ladder-results-20261007.md", hypotheses)
        self.assertIn("h57-results-20261007.md", hypotheses)

    def test_no_unresolved_placeholders(self):
        for name in PAGES:
            text = (SUB / name).read_text(encoding="utf-8")
            for bad in ("TODO", "XXX", "{esc(", "{fmt("):
                with self.subTest(page=name, marker=bad):
                    self.assertNotIn(bad, text)

    def test_stylesheet_and_nojekyll_are_present(self):
        self.assertTrue((SUB / ".nojekyll").exists())
        css = conftest.DOCS / "assets/ds48-fusion/site.css"
        self.assertTrue(css.exists())
        self.assertGreater(css.stat().st_size, 1000)

    def test_other_site_pages_remain_present(self):
        for name in FOREIGN_PAGES:
            with self.subTest(page=name):
                self.assertTrue((conftest.DOCS / name).exists())

    def test_preserved_main_pages_are_visibly_historical(self):
        archive = conftest.DOCS / "archive-main-pages"
        files = [p for p in archive.rglob("*") if p.is_file()]
        self.assertGreater(len(files), 50)
        for path in files:
            text = path.read_text(encoding="utf-8", errors="replace")
            if path.suffix.lower() == ".html":
                start = text.lower().find("<body")
                visible = text[start:start + 1600].lower() if start >= 0 else ""
            elif path.suffix.lower() == ".md":
                visible = text[:700].lower()
            else:
                continue
            with self.subTest(path=path.relative_to(conftest.DOCS)):
                self.assertTrue(any(marker in visible for marker in
                                    ("historical archive", "forensic only", "historical snapshot", "not current")))

    def test_markdown_site_paths_are_current_bridges_not_stale_live_pages(self):
        next_steps = (conftest.DOCS / "md/next-steps.md").read_text(encoding="utf-8").lower()
        slate = (conftest.DOCS / "md/hypotheses.md").read_text(encoding="utf-8").lower()
        corrections = (conftest.DOCS / "md/irregularities.md").read_text(encoding="utf-8").lower()
        self.assertIn("no weekly slot is cleared", next_steps)
        self.assertIn("newly derived, validated mass-neutral audit", next_steps)
        self.assertIn("h57", slate)
        self.assertNotIn("the active h48 slate", slate)
        self.assertIn("inferred hidden-truth density", corrections)
        self.assertIn("0.2778", corrections)


class TestLinksAndArtifacts(unittest.TestCase):
    def test_every_local_href_resolves(self):
        for name in PAGES:
            text = (SUB / name).read_text(encoding="utf-8")
            for href in re.findall(r'href="([^"#]+)"', text):
                if href.startswith(("http://", "https://", "mailto:")):
                    continue
                # Strip an optional query component without dropping a fragment already excluded.
                href = href.split("?", 1)[0]
                with self.subTest(page=name, href=href):
                    self.assertTrue((SUB / href).resolve().exists(), f"broken local link: {href}")

    def test_four_archived_ds_layers_are_available_for_audit(self):
        names = ["gemsdoe48-ds48-belief.tif", "gemsdoe48-ds48-conflict.tif",
                 "gemsdoe48-ds48-emission.tif", "gemsdoe48-ds48-mtheta.tif"]
        for name in names:
            with self.subTest(file=name):
                path = conftest.DOWNLOADS / name
                self.assertTrue(path.exists())
                self.assertGreater(path.stat().st_size, 100_000)
        index = (SUB / "index.html").read_text(encoding="utf-8")
        for name in names:
            self.assertIn(f"../downloads/{name}", index)
        self.assertIn("OK TO DOWNLOAD FOR AUDIT; NOT CLEARED TO SUBMIT", index)

    def test_root_sources_still_link_primary_sources(self):
        text = (conftest.DOCS / "sources.html").read_text(encoding="utf-8")
        urls = re.findall(r'href="(https?://[^"]+)"', text)
        self.assertGreaterEqual(len(urls), 10)
        self.assertTrue(any("sciencebase.gov" in url or "usgs.gov" in url for url in urls))
        self.assertTrue(any("drivendata" in url for url in urls))


class TestReceiptAndBuilderSafety(unittest.TestCase):
    def test_registry_receipt_is_explicitly_invalidated_for_promotion(self):
        receipt = json.loads((conftest.REGISTRY / "submission_build.json").read_text())
        self.assertEqual(receipt["validity_status"], "INVALIDATED_FORENSIC_ONLY_DO_NOT_USE_FOR_PROMOTION")
        self.assertIn("NOT CLEARED TO SUBMIT", receipt["submission_decision"])
        self.assertIn("does not establish", receipt["headline_negative_result"]["claim_withdrawn"])

    def test_retired_builder_refuses_and_leaves_pages_unchanged(self):
        before = {name: (SUB / name).read_bytes() for name in PAGES}
        script = conftest.repo_path("scripts/build_site_ds48.py")
        result = subprocess.run([sys.executable, str(script)], cwd=str(conftest.repo_path(".")),
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("retired", result.stderr + result.stdout)
        after = {name: (SUB / name).read_bytes() for name in PAGES}
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
