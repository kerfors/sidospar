"""Bygg den bläddringsbara kopian och projektsidan.

Build the browseable copy in sidor/ and the project page index.md.

Reads data/manifest.json and the raw files written by fetch.py. Each file is
copied to sidor/<folder>/<path>. In HTML pages:
- links and images that point to another downloaded file are made relative,
  so the copy works on GitHub Pages and locally; other links are left as they were;
- a small banner after <body> says when the page was archived and links to
  the snapshot in the Wayback Machine.
The raw files in data/ are never changed.

index.md (the project page) is written from INTRO below plus one table per
source. Python 3 standard library only. Run from any directory:

    python3 generate.py
"""

import html
import json
import os
import re
import shutil
import urllib.parse
from pathlib import Path

from fetch import SOURCES, local_path

ROOT = Path(__file__).parent
DATA_DIR = ROOT / "data"
COPY_DIR = ROOT / "sidor"
WAYBACK = "https://web.archive.org/web"

INTRO = """\
# Mina hemsidor 1997–2004

Kerstin Forsberg · november 2026 · [Till Sidospår](../)

Under webbens första år hade jag en egen hemsida. Jag mindes att leverantören hette ungefär Netguide. Fanns det några spår kvar i webbarkiven?

Det fanns det. En länksida vid University of the West of England, senast ändrad i januari 2000, länkade till min sida *Extranet – a reference page* på Viktoriainstitutet i Göteborg. På den sidan stod min gamla e-postadress, kerfor@netg.se. Leverantören hette alltså Netg, och hemsidan låg på netg.se/~kerfor/. Extranetsidan säger själv att jag uppdaterade den från mars 1997.

Sidorna nedan är hämtade ur [Internet Archive](https://web.archive.org/) (Wayback Machine). Varje sida är den senast sparade versionen. Datumet är dagen då arkivet sparade sidan, inte när jag skrev den. Länkar mellan mina egna sidor fungerar; länkar ut till andra webbplatser leder oftast ingenstans i dag.

Hämtningen gjordes med [fetch.py](fetch.py) och kopian byggdes med [generate.py](generate.py). Rådata och en förteckning över alla sparade versioner ligger i [data/](data/manifest.json).
"""

ATTR_RE = re.compile(
    r"""(?P<name>\b(?:href|src|background)\s*=\s*)"""
    r"""(?:"(?P<dq>[^"]*)"|'(?P<sq>[^']*)'|(?P<bare>[^\s>]+))""",
    re.IGNORECASE,
)
BODY_RE = re.compile(r"<body\b[^>]*>", re.IGNORECASE)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
CHARSET_RE = re.compile(rb"""charset\s*=\s*["']?([A-Za-z0-9_-]+)""", re.IGNORECASE)


def is_html(item):
    return item["mimetype"] == "text/html" or item["path"].lower().endswith((".htm", ".html"))


def page_encoding(raw):
    match = CHARSET_RE.search(raw[:2048])
    if match:
        return match.group(1).decode("ascii").lower()
    return "cp1252"


def wayback_url(item):
    return f"{WAYBACK}/{item['timestamp']}/{item['original']}"


def archive_date(item):
    ts = item["timestamp"]
    return f"{ts[0:4]}-{ts[4:6]}-{ts[6:8]}"


def copy_path(item):
    """Path of the copy, relative to the project folder."""
    return Path("sidor") / item["path"]


def banner(item):
    project = "../" * (len(copy_path(item).parts) - 1)
    return (
        '<div style="font:13px/1.4 sans-serif;background:#fff8e1;color:#333;'
        'border-bottom:1px solid #e0c97a;padding:6px 10px;margin:0 0 8px 0">'
        f'Arkiverad kopia, sparad {archive_date(item)} i '
        f'<a href="{html.escape(wayback_url(item))}">Internet Archive</a>. '
        f'Original: {html.escape(item["original"])}. '
        f'<a href="{project}">Alla sidor</a></div>'
    )


def rewrite_html(text, item, files_by_key):
    """Relative links to downloaded files; banner after <body>."""
    here = Path(item["path"]).parent

    def replace(match):
        value = match.group("dq") or match.group("sq") or match.group("bare") or ""
        absolute = urllib.parse.urljoin(item["original"], html.unescape(value))
        target_path = local_path(absolute)
        if target_path is None:
            return match.group(0)
        target = files_by_key.get(str(target_path).lower())
        if target is None:
            # The Viktoria pages are a move of the netg pages with the same
            # folder layout: a file missing in one source is taken from the
            # same path in the other, when it is there.
            rest = Path(*target_path.parts[1:])
            for folder in SOURCES.values():
                target = files_by_key.get(str(Path(folder) / rest).lower())
                if target is not None:
                    break
        if target is None:
            return match.group(0)
        relative = os.path.relpath(target["path"], here).replace(os.sep, "/")
        fragment = urllib.parse.urlsplit(absolute).fragment
        if fragment:
            relative += "#" + fragment
        return f'{match.group("name")}"{html.escape(relative)}"'

    text = ATTR_RE.sub(replace, text)
    body = BODY_RE.search(text)
    if body:
        text = text[:body.end()] + banner(item) + text[body.end():]
    else:
        text = banner(item) + text
    return text


def page_title(text, item):
    match = TITLE_RE.search(text)
    if match and match.group(1).strip():
        return " ".join(html.unescape(match.group(1)).split())
    return item["path"]


def md_cell(text):
    return text.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def write_index(rows_by_source):
    lines = [INTRO]
    for prefix, rows in rows_by_source.items():
        dates = sorted(archive_date(item) for _, item in rows)
        lines.append(f"## {prefix}\n")
        lines.append(f"{len(rows)} sidor, sparade i arkivet {dates[0]} – {dates[-1]}.\n")
        lines.append("| Sparad | Sida | I arkivet |")
        lines.append("| --- | --- | --- |")
        for title, item in rows:
            href = urllib.parse.quote(copy_path(item).as_posix())
            lines.append(
                f"| {archive_date(item)} | [{md_cell(title)}]({href}) "
                f"| [Wayback]({wayback_url(item)}) |"
            )
        lines.append("")
    (ROOT / "index.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    manifest = json.loads((DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
    files_by_key = {}
    for source in manifest["sources"].values():
        for item in source["files"]:
            files_by_key[item["path"].lower()] = item

    if COPY_DIR.exists():
        shutil.rmtree(COPY_DIR)

    rows_by_source = {}
    for prefix, source in manifest["sources"].items():
        rows = []
        for item in source["files"]:
            raw = (DATA_DIR / item["path"]).read_bytes()
            target = ROOT / copy_path(item)
            target.parent.mkdir(parents=True, exist_ok=True)
            if not is_html(item):
                target.write_bytes(raw)
                continue
            encoding = page_encoding(raw)
            text = raw.decode(encoding, errors="replace")
            rows.append((page_title(text, item), item))
            text = rewrite_html(text, item, files_by_key)
            target.write_bytes(text.encode(encoding, errors="xmlcharrefreplace"))
        rows.sort(key=lambda row: row[1]["path"].lower())
        rows_by_source[prefix] = rows

    write_index(rows_by_source)
    pages = sum(len(r) for r in rows_by_source.values())
    print(f"sidor/ and index.md written: {pages} pages, {len(files_by_key)} files in total")


if __name__ == "__main__":
    main()
