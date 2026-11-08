"""Bygg den bläddringsbara kopian och projektsidan.

Build the browseable copy in sidor/ and the project page index.md.

Reads data/manifest.json and the raw files written by fetch.py. The files of
the LISTED sources are copied to sidor/<folder>/<path>, and so are the files
of the other sources that a listed page links to directly (netg pages and
images the Viktoria pages use but the archive only kept at netg). In HTML pages:
- links and images that point to another downloaded file are made relative,
  so the copy works on GitHub Pages and locally; other links are left as they were;
- a small banner after <body> says when the page was archived and links to
  the snapshot in the Wayback Machine.
The raw files in data/ are never changed.

index.md (the project page) is written from INTRO below plus a table of the
pages of the LISTED sources. Python 3 standard library only. Run from any directory:

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
# Sources whose pages are listed on the project page.
LISTED = ["viktoria.informatik.gu.se/~kerstinf/"]

INTRO = """\
# Mina hemsidor från Viktoriainstitutet

Kerstin Forsberg · november 2026 · [Till Sidospår](../)

Vårt första internetabonnemang köpte vi av Netg på Bokmässan i Göteborg 1994. Det gällde tio timmar.

1997 började jag som industridoktorand på Viktoriainstitutet, senare Informatik vid Göteborgs universitet. I december 2001 tog jag min licentiatexamen med avhandlingen [*Mobile newsmaking*](https://libris.kb.se/6phfq9mj3nwcjns#it) (Papers in informatics nr 9). Forskningsområdet var datorstött samarbete (CSCW). I gruppen Mobile Informatics studerade jag vad som behövs för att mycket rörliga yrkesgrupper, som nyhetsjournalister, ska få information anpassad till sin situation genom mobila tillämpningar: *Mobile Newsmaking*.

Sidorna här kommer från olika doktorandkurser och projekt. De är hämtade ur [Internet Archive](https://web.archive.org/) (Wayback Machine). Varje sida är den senast sparade versionen, och datumet är dagen då arkivet sparade sidan, inte när jag skrev den. Länkar mellan mina egna sidor fungerar. Länkar ut till andra webbplatser leder oftast ingenstans i dag, och några bilder sparades aldrig.

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


def rewrite_html(text, item, files_by_key, used):
    """Relative links to downloaded files; banner after <body>.

    The files linked to are added to used.
    """
    here = Path(item["path"]).parent

    def replace(match):
        value = match.group("dq") or match.group("sq") or match.group("bare") or ""
        # Some pages were saved from Word with Windows paths (images\fig1.gif);
        # browsers read the backslash as a slash, and so does this.
        value = html.unescape(value).replace("\\", "/")
        absolute = urllib.parse.urljoin(item["original"], value)
        target_path = local_path(absolute)
        if target_path is None:
            return match.group(0)
        # The Viktoria pages are a move of the netg pages with the same folder
        # layout. A link is taken to the same path in a LISTED source first
        # (also links that point to netg), then to the other sources.
        rest = Path(*target_path.parts[1:])
        folders = [SOURCES[prefix] for prefix in LISTED]
        folders += [f for f in SOURCES.values() if f not in folders]
        target = None
        for folder in folders:
            target = files_by_key.get(str(Path(folder) / rest).lower())
            if target is not None:
                break
        if target is None:
            return match.group(0)
        used.add(target["path"].lower())
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


def write_index(rows):
    dates = sorted(archive_date(item) for _, item in rows)
    lines = [INTRO]
    lines.append("## Sidorna\n")
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


def read_page(item):
    raw = (DATA_DIR / item["path"]).read_bytes()
    encoding = page_encoding(raw)
    return raw.decode(encoding, errors="replace"), encoding


def main():
    manifest = json.loads((DATA_DIR / "manifest.json").read_text(encoding="utf-8"))
    all_files = {}
    for source in manifest["sources"].values():
        for item in source["files"]:
            all_files[item["path"].lower()] = item
    listed = [item for prefix in LISTED for item in manifest["sources"][prefix]["files"]]

    # Pass 1: the listed files plus every file a listed page links to directly.
    included = {item["path"].lower() for item in listed}
    for item in listed:
        if is_html(item):
            text, _ = read_page(item)
            rewrite_html(text, item, all_files, included)
    files_by_key = {key: all_files[key] for key in included}

    # Pass 2: copy them; links are rewritten only to files that are copied.
    if COPY_DIR.exists():
        shutil.rmtree(COPY_DIR)
    listed_keys = {item["path"].lower() for item in listed}
    rows = []
    for key in sorted(files_by_key):
        item = files_by_key[key]
        target = ROOT / copy_path(item)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not is_html(item):
            target.write_bytes((DATA_DIR / item["path"]).read_bytes())
            continue
        text, encoding = read_page(item)
        if key in listed_keys:
            rows.append((page_title(text, item), item))
        text = rewrite_html(text, item, files_by_key, set())
        target.write_bytes(text.encode(encoding, errors="xmlcharrefreplace"))

    write_index(rows)
    print(f"sidor/ and index.md written: {len(rows)} pages listed, "
          f"{len(files_by_key)} files copied ({len(files_by_key) - len(listed)} from other sources)")


if __name__ == "__main__":
    main()
