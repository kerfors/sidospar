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
# A short note after the title, for pages whose titles are the same.
NOTES = {
    "viktoria/extranet.htm": "på engelska",
    "viktoria/extranet_sv.htm": "på svenska",
    "viktoria/thesis/index.htm": "avhandlingens webbsida",
    "viktoria/thesis/errata.htm": "errata",
    "viktoria/cscwnews.htm": "sammanfattning och innehåll",
    "viktoria/IRIS98_tidningar.htm": "hela artikeln",
    "viktoria/MDI15ar.htm": "bilden sparades inte i arkivet",
    "viktoria/MDI15ar_overview.htm": "översiktsbild",
    "viktoria/www9/ExtRDF.htm": (
        "hela artikeln, med Lars Dannstedt; publicerad i Computer Networks 33, 2000, "
        "[doi:10.1016/S1389-1286(00)00065-7](https://doi.org/10.1016/S1389-1286%2800%2900065-7)"
    ),
}
# Copied but not listed: index.htm is the same file as index.html.
UNLISTED = {"viktoria/index.htm"}

INTRO = """\
# Mina hemsidor från Viktoriainstitutet

Kerstin Forsberg · november 2026 · [Till Sidospår](../)

Vårt första internetabonnemang köpte vi av Netg på Bokmässan i Göteborg 1994. Det gällde tio timmar.

1997 började jag som industridoktorand på Viktoriainstitutet, senare Informatik vid Göteborgs universitet. I december 2001 tog jag min licentiatexamen med avhandlingen [*Mobile newsmaking*](https://libris.kb.se/6phfq9mj3nwcjns#it) (Papers in informatics nr 9). Forskningsområdet var datorstött samarbete (CSCW). I gruppen Mobile Informatics studerade jag vad som behövs för att mycket rörliga yrkesgrupper, som nyhetsjournalister, ska få information anpassad till sin situation genom mobila tillämpningar: *Mobile Newsmaking*. Avhandlingens egen [webbsida](sidor/viktoria/thesis/index.htm) finns kvar i arkivet, och där finns [hela avhandlingen som PDF](sidor/viktoria/thesis/bookscreen.pdf), 109 sidor.

During my PhD studies I wrote the paper [*Extensible use of RDF in a Business Context*](sidor/viktoria/www9/ExtRDF.htm) together with Lars Dannstedt at Volvo IT. I presented it at the WWW9 conference in Amsterdam in May 2000, and it was also published in Computer Networks ([doi:10.1016/S1389-1286(00)00065-7](https://doi.org/10.1016/S1389-1286%2800%2900065-7)). It was my first work with RDF and linked data, something I [still work with](https://kerfors.github.io/).

Sidorna här kommer från olika doktorandkurser och projekt. De är hämtade ur [Internet Archive](https://web.archive.org/) (Wayback Machine), som den senast sparade versionen av varje sida. *Datum* är det datum sidan själv anger ("Updated by Kerstin Forsberg …"), eller när sidan senast sparades i Word om den inte anger något. *Arkiverad* är dagen då arkivet sparade kopian. Länkar mellan mina egna sidor fungerar. Länkar ut till andra webbplatser går till arkivets kopia från ungefär samma tid, när en sådan finns. Några bilder och sidor sparades aldrig.

Hämtningen gjordes med [fetch.py](fetch.py) och kopian byggdes med [generate.py](generate.py). Rådata och en förteckning över alla sparade versioner ligger i [data/](data/manifest.json).
"""

ATTR_RE = re.compile(
    r"""(?P<name>\b(?:href|src|background)\s*=\s*)"""
    r"""(?:"(?P<dq>[^"]*)"|'(?P<sq>[^']*)'|(?P<bare>[^\s>]+))""",
    re.IGNORECASE,
)
BODY_RE = re.compile(r"<body\b[^>]*>", re.IGNORECASE)
# The date a page gives itself: "Updated by Kerstin Forsberg 13 November 1997",
# "Uppdaterad av Kerstin Forsberg, 18 mars 1998", "Updated 5 October 1997".
UPDATED_RE = re.compile(
    r"(?:Updated|Uppdaterad)(?:\s+(?:by|av)\s+Kerstin\s+Forsberg)?,?\s+"
    r"(\d{1,2})\s+([A-Za-zÅÄÖåäö]+)\s+(\d{4})",
    re.IGNORECASE,
)
LAST_SAVED_RE = re.compile(r"<o:LastSaved>(\d{4}-\d{2}-\d{2})")
MONTHS = {
    "january": 1, "januari": 1, "february": 2, "februari": 2, "march": 3, "mars": 3,
    "april": 4, "may": 5, "maj": 5, "june": 6, "juni": 6, "july": 7, "juli": 7,
    "august": 8, "augusti": 8, "september": 9, "october": 10, "oktober": 10,
    "november": 11, "december": 12,
}
HEAD_RE = re.compile(r"<head\b[^>]*>", re.IGNORECASE)
META_CHARSET_RE = re.compile(r"""(<meta\b[^>]*charset\s*=\s*["']?)[A-Za-z0-9_-]+""", re.IGNORECASE)
# The copies are written as UTF-8 (GitHub Pages serves them as UTF-8), and
# the page content is centred with a maximum width.
HEAD_EXTRA = (
    '<meta charset="utf-8">'
    "<style>body{max-width:56rem;margin-left:auto!important;margin-right:auto!important;"
    "padding:0 1rem}</style>"
)
TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)
HEADING_RE = re.compile(r"<h[1-3]\b[^>]*>(.*?)</h[1-3]>", re.IGNORECASE | re.DOTALL)
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


def banner(item, nav):
    """Archive note plus a navigation line: previous, all pages, next.

    nav is (previous, next) in the order of the table, each (title, item) or
    None; pages that are not listed get (None, None).
    """
    project = "../" * (len(copy_path(item).parts) - 1)
    here = Path(item["path"]).parent

    def link(entry, label):
        title, target = entry
        href = os.path.relpath(target["path"], here).replace(os.sep, "/")
        return (f'<a href="{html.escape(href)}" title="{html.escape(title)}">'
                f'{label}</a>')

    previous, following = nav
    parts = []
    if previous:
        parts.append(link(previous, "‹ Föregående"))
    parts.append(f'<a href="{project}"><b>Alla sidor</b></a>')
    if following:
        parts.append(link(following, "Nästa ›"))
    return (
        '<div style="font:13px/1.5 sans-serif;background:#fff8e1;color:#333;'
        'border-bottom:1px solid #e0c97a;padding:6px 10px;margin:0 0 8px 0">'
        f'<div>{" · ".join(parts)}</div>'
        f'<div style="font-size:12px;color:#666">Arkiverad kopia, sparad {archive_date(item)} i '
        f'<a href="{html.escape(wayback_url(item))}">Internet Archive</a>. '
        f'Original: {html.escape(item["original"])}.</div></div>'
    )


def rewrite_html(text, item, files_by_key, used, nav=(None, None)):
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
        parts = urllib.parse.urlsplit(absolute)
        if parts.scheme not in ("http", "https") or parts.hostname == "web.archive.org":
            return match.group(0)
        target_path = local_path(absolute)
        target = None
        if target_path is not None:
            # The Viktoria pages are a move of the netg pages with the same folder
            # layout. A link is taken to the same path in a LISTED source first
            # (also links that point to netg), then to the other sources.
            rest = Path(*target_path.parts[1:])
            folders = [SOURCES[prefix] for prefix in LISTED]
            folders += [f for f in SOURCES.values() if f not in folders]
            for folder in folders:
                target = files_by_key.get(str(Path(folder) / rest).lower())
                if target is not None:
                    break
        if target is None:
            # Not copied here: link to the Wayback Machine at the date of this
            # page; it redirects to the nearest capture, if there is one.
            # Images get the im_ form, which serves the image itself.
            flag = "" if match.group("name").lower().startswith("href") else "im_"
            wayback = f"{WAYBACK}/{item['timestamp']}{flag}/{absolute}"
            return f'{match.group("name")}"{html.escape(wayback)}"'
        used.add(target["path"].lower())
        relative = os.path.relpath(target["path"], here).replace(os.sep, "/")
        fragment = urllib.parse.urlsplit(absolute).fragment
        if fragment:
            relative += "#" + fragment
        return f'{match.group("name")}"{html.escape(relative)}"'

    text = ATTR_RE.sub(replace, text)
    # Declared charset (iso-8859-1, windows-1252) becomes utf-8; a page
    # without one gets <meta charset="utf-8">. Plus the centring style.
    text, declared = META_CHARSET_RE.subn(r"\g<1>utf-8", text)
    extra = HEAD_EXTRA if declared == 0 else HEAD_EXTRA.replace('<meta charset="utf-8">', "")
    head = HEAD_RE.search(text)
    if head:
        text = text[:head.end()] + extra + text[head.end():]
    else:
        text = extra + text
    body = BODY_RE.search(text)
    if body:
        text = text[:body.end()] + banner(item, nav) + text[body.end():]
    else:
        text = banner(item, nav) + text
    return text


def page_title(text, item):
    """<title>, or the first h1–h3 when the title is missing or "Untitled"."""
    match = TITLE_RE.search(text)
    title = " ".join(html.unescape(match.group(1)).split()) if match else ""
    if title and title.lower() != "untitled":
        return title
    heading = HEADING_RE.search(text)
    if heading:
        return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", heading.group(1))).split())
    return item["path"]


def page_date(text):
    """The date the page gives itself (last "Updated by ..." in the visible
    text), else Word's LastSaved date, else None. ISO yyyy-mm-dd."""
    visible = re.sub(r"(?is)<(script|style|xml)\b.*?</\1>|<!--.*?-->", " ", text)
    visible = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", visible)).split())
    matches = UPDATED_RE.findall(visible)
    if matches:
        day, month, year = matches[-1]
        return f"{year}-{MONTHS[month.lower()]:02d}-{int(day):02d}"
    saved = LAST_SAVED_RE.search(text)
    if saved:
        return saved.group(1)
    return None


def md_cell(text):
    return text.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def table_order(rows):
    """Oldest first by the page's own date; pages without one last, by title."""
    return sorted(rows, key=lambda row: (row[1] is None, row[1] or "", row[0].lower()))


def write_index(rows):
    rows = table_order(rows)
    dated = [date for _, date, _ in rows if date]
    lines = [INTRO]
    lines.append("## Sidorna\n")
    lines.append(f"{len(rows)} sidor. {len(dated)} av dem anger ett datum, "
                 f"från {dated[0]} till {dated[-1]}.\n")
    lines.append("| Datum | Sida | Arkiverad |")
    lines.append("| --- | --- | --- |")
    for title, date, item in rows:
        href = urllib.parse.quote(copy_path(item).as_posix())
        note = NOTES.get(item["path"])
        note = f" · *{note}*" if note else ""
        # Dates in a span that does not wrap, so 1997-04-12 stays on one line.
        nowrap = '<span style="white-space:nowrap">{}</span>'
        lines.append(
            f"| {nowrap.format(date) if date else '–'} | [{md_cell(title)}]({href}){note} "
            f"| [{nowrap.format(archive_date(item))}]({wayback_url(item)}) |"
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
    pages = []
    for key in sorted(files_by_key):
        item = files_by_key[key]
        target = ROOT / copy_path(item)
        target.parent.mkdir(parents=True, exist_ok=True)
        if not is_html(item):
            target.write_bytes((DATA_DIR / item["path"]).read_bytes())
            continue
        text, _ = read_page(item)
        if key in listed_keys and item["path"] not in UNLISTED:
            rows.append((page_title(text, item), page_date(text), item))
        pages.append((key, item, text, target))

    # Previous and next page, in the order of the table.
    ordered = [(title, item) for title, _, item in table_order(rows)]
    nav_by_key = {}
    for i, (_, item) in enumerate(ordered):
        previous = ordered[i - 1] if i > 0 else None
        following = ordered[i + 1] if i + 1 < len(ordered) else None
        nav_by_key[item["path"].lower()] = (previous, following)

    for key, item, text, target in pages:
        nav = nav_by_key.get(key, (None, None))
        text = rewrite_html(text, item, files_by_key, set(), nav)
        target.write_text(text, encoding="utf-8")

    write_index(rows)
    print(f"sidor/ and index.md written: {len(rows)} pages listed, "
          f"{len(files_by_key)} files copied ({len(files_by_key) - len(listed)} from other sources)")


if __name__ == "__main__":
    main()
