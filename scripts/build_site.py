"""Render docs/md/*.md -> docs/*.html with the download block filled from the receipt."""
import json, pathlib, markdown
ROOT = pathlib.Path(__file__).resolve().parents[1]; D = ROOT / "docs"
rec = json.load(open(sorted((D / "downloads").glob("receipt-*.json"))[-1]))
checks = "\n".join(f"* {'✅' if v else '❌'} `{k}`" for k, v in rec["checks"].items())
subs = {"TIF": rec["file"], "ZIP": rec["zip"], "RECEIPT": f"receipt-{rec['name']}.json",
        "BYTES": f"{rec['bytes']:,}", "SHA16": rec["sha256"][:16], "NPX": f"{rec['emitted_px']:,}",
        "NOTE": rec["portal_note"], "UNIQUE": rec["portal_unique_name"], "CHECKS": checks, "NCHK": str(len(rec["checks"]))}
lb = json.load(open(D / "data/leaderboard.json"))
lbmd = f"Retrieved **{lb['retrieved_utc']}** · {lb['method']}\n\n| rank | participant | best public DTI | submissions |\n|---:|---|---:|---:|\n" + "\n".join(
    f"| {r['rank']} | {r['participant']} | {r['best_public'] if r['best_public'] is not None else '—'} | {r['submissions'] or '—'} |" for r in lb["rows"])
subs["LEADERBOARD"] = lbmd
NAV = [("index", "Home"), ("executive-summary", "How to submit"), ("method", "Method & 0.2778 autopsy"),
       ("hypotheses", "Hypotheses"), ("irregularities", "Irregularities"), ("next-steps", "Next steps"), ("leaderboard", "Leaderboard"),
       ("sources", "Sources")]
CSS = """body{font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif;margin:0;color:#1d2330;background:#f6f7fb;line-height:1.55}
nav{background:#14213d;padding:.6rem 1rem;position:sticky;top:0}nav a{color:#fff;margin-right:1.1rem;text-decoration:none;font-size:.95rem}
nav a.on{border-bottom:2px solid #fca311}main{max-width:1050px;margin:auto;padding:1.2rem 1.4rem;background:#fff}
table{border-collapse:collapse;width:100%;font-size:.9rem;margin:.6rem 0}th,td{border:1px solid #dde;padding:.35rem .5rem;vertical-align:top}
th{background:#eef1f8}code{background:#f0f2f7;padding:.05rem .3rem;border-radius:3px;font-size:.88em;word-break:break-all}
pre{background:#f0f2f7;padding:.7rem;overflow:auto}img{max-width:100%;border:1px solid #dde;margin:.5rem 0}
.dl{background:#fff8e6;border:2px solid #fca311;border-radius:8px;padding:.6rem 1.1rem;margin-bottom:1rem}
.btn{display:inline-block;background:#fca311;color:#14213d;font-weight:700;padding:.55rem 1rem;border-radius:6px;text-decoration:none;word-break:break-all}
blockquote{border-left:4px solid #fca311;margin:.8rem 0;padding:.2rem .9rem;background:#fafafa}"""
for md in sorted((D / "md").glob("*.md")):
    txt = md.read_text()
    for k, v in subs.items(): txt = txt.replace("{{" + k + "}}", v)
    body = markdown.markdown(txt, extensions=["tables", "fenced_code"])
    nav = "".join(f'<a href="{n}.html" class="{"on" if n == md.stem else ""}">{t}</a>' for n, t in NAV)
    html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>GEMSDOE48 · {md.stem}</title><style>{CSS}</style></head><body><nav>{nav}</nav><main>{body}
<hr><p style="font-size:.8rem;color:#667">GEMSDOE48 · built from <code>docs/md/{md.name}</code> by <code>scripts/build_site.py</code></p></main></body></html>"""
    (D / f"{md.stem}.html").write_text(html)
    print("wrote", md.stem)
(D / ".nojekyll").write_text("")
