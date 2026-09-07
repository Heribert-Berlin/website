#!/usr/bin/env python3
"""Baut sitemap.xml aus den versionierten HTML-Seiten im Wurzelverzeichnis.

Sprachgruppen kommen aus dem Dateinamen: ein Namensteil "eng"/"chi"/"deu"
ist die Sprache, der Rest ist der Gruppenschluessel
(roman-eng-hoerbuch und roman-hoerbuch gehoeren also zusammen).
lastmod ist das Datum des letzten Commits, der die Datei geaendert hat.
Aufruf: python sitemap-build.py
"""
import re, subprocess
from collections import defaultdict
from pathlib import Path

BASE = "https://www.heribert-berlin.de/"
LANGS = {"eng": "en", "chi": "zh", "deu": "de"}
# Weiterleitungsseite und Google-Bestaetigungsdatei gehoeren nicht in die Sitemap
SKIP = {"index.html"}

root = Path(__file__).parent
files = subprocess.run(["git", "ls-files", "*.html"], cwd=root,
                       capture_output=True, text=True, check=True).stdout.split()
pages = []
for f in files:
    if "/" in f or f in SKIP or f.startswith("google"):
        continue
    if re.search(r'name=["\']robots["\'][^>]*noindex', (root / f).read_text(encoding="utf-8"), re.I):
        continue
    pages.append(f)

groups = defaultdict(dict)
for f in pages:
    parts = f[:-5].split("-")
    lang = next((LANGS[p] for p in parts if p in LANGS), "de")
    key = "-".join(p for p in parts if p not in LANGS)
    groups[key][lang] = f

def lastmod(f):
    return subprocess.run(["git", "log", "-1", "--format=%ad", "--date=short", "--", f],
                          cwd=root, capture_output=True, text=True, check=True).stdout.strip()

out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
       '        xmlns:xhtml="http://www.w3.org/1999/xhtml">']
for key in sorted(groups):
    g = groups[key]
    for lang in ("de", "en", "zh"):
        if lang not in g:
            continue
        out.append("  <url>")
        out.append(f"    <loc>{BASE}{g[lang]}</loc>")
        if len(g) > 1:
            if "de" in g:
                out.append(f'    <xhtml:link rel="alternate" hreflang="x-default" href="{BASE}{g["de"]}"/>')
            for l in ("de", "en", "zh"):
                if l in g:
                    out.append(f'    <xhtml:link rel="alternate" hreflang="{l}" href="{BASE}{g[l]}"/>')
        out.append(f"    <lastmod>{lastmod(g[lang])}</lastmod>")
        out.append("  </url>")
out.append("</urlset>")
Path(root / "sitemap.xml").write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"sitemap.xml: {len(pages)} Seiten in {len(groups)} Gruppen")
