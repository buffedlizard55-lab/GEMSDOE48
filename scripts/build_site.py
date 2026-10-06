"""Retired legacy Markdown site generator.

The upstream generator consumed superseded alpha=.99 experiment pages and would
overwrite the current hand-maintained overview/validation pages. Those sources are
preserved under ``docs/archive-main-pages/md``. Current pages are maintained in
``docs/*.html`` and ``docs/research``; this entry point intentionally does not write.
"""


def main() -> int:
    print(
        "Legacy site generation is disabled to avoid publishing superseded claims. "
        "See docs/index.html, docs/validation.html, and docs/archive-main-pages/."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
