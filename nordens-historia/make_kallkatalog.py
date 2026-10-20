"""Generate kallkatalog.html: all sources, grouped by the work they are part of or the publisher of their site.

Built from data/sources.json, data/source_titles.json, data/claims.json (source_url and also_sources)
and data/riksarkivet.json (the second check). Writes no graph: everything shown is already in id/.

Run: python3 make_kallkatalog.py  ->  writes kallkatalog.html next to this script.
"""
import json
from html import escape
from pathlib import Path

import ld

HERE = Path(__file__).parent
CLAIMS = json.loads((HERE / "data" / "claims.json").read_text(encoding="utf-8"))
RA = json.loads((HERE / "data" / "riksarkivet.json").read_text(encoding="utf-8"))
TYPES = ld.SOURCES["types"]
PUBLISHERS = {o["iri"]: o for o in ld.SOURCES["publishers"]}

# Sections in page order: the work's type, or "webbsida" for sources grouped by publisher.
SECTIONS = [("uppslagsverk", "Uppslagsverk"), ("register", "Register"),
            ("periodikum", "Tidskrifter och tidningar"), ("webbsida", "Webbplatser")]

SV_ORDER = {"å": "{", "ä": "|", "ö": "}", "æ": "|", "ø": "}"}


def sv_key(text):
    """Sort key in Swedish alphabetical order (å, ä, ö after z), ignoring case and quotation marks."""
    t = text.lower().replace('"', "").replace("”", "")
    return "".join(SV_ORDER.get(ch, ch) for ch in t)


def iri_link(iri):
    """A Wikidata or kallor/id/ IRI as a link with its short form."""
    if iri.startswith("wd:"):
        q = iri[3:]
        return f'<a href="https://www.wikidata.org/wiki/{q}">Wikidata {q}</a>'
    if iri.startswith("kallor:"):
        return f'<a href="{ld.KALLOR}{iri[7:]}">kallor/id/{iri[7:]}</a>'
    raise ValueError(f"unknown IRI prefix: {iri}")


def anchor(iri):
    return iri.split(":", 1)[1]


def citations():
    """Per source address: the claims citing it, in the first check and in the second (Riksarkivet)."""
    first, second, numbers = {}, {}, {}
    for c in CLAIMS:
        for u in ([c["source_url"]] if c["source_url"] else []) + c["also_sources"]:
            first.setdefault(u, []).append(c["id"])
    for r in RA["checks"]:
        for x in r["records"]:
            second.setdefault(x["url"], []).append((r["claim"], r["id"]))
            numbers[x["url"]] = x["id"]
    return first, second, numbers


def groups(first, second):
    """The sources grouped by work, or by the publisher of their site."""
    out = {}
    for u in set(first) | set(second):
        w = ld.source_work(u)
        if w:
            key, g = w["iri"], {"iri": w["iri"], "name": w["name"], "section": w["type"],
                                "part_type": w["part_type"], "publisher": w["publisher"], "work": w}
        else:
            o = ld.source_publisher(u)
            if not o:
                raise ValueError(f"source has neither work nor publisher: {u}")
            key, g = o["iri"], {"iri": o["iri"], "name": o["name"], "section": "webbsida",
                                "part_type": "webbsida", "publisher": None, "work": None}
        out.setdefault(key, g).setdefault("urls", []).append(u)
    for g in out.values():
        ids = {cid for u in g["urls"] for cid in first.get(u, [])}
        ids |= {cid for u in g["urls"] for cid, _ in second.get(u, [])}
        g["n_claims"] = len(ids)
    return out


def claim_list(u, first, second, by_id):
    """The claims citing a source, by claim id, with the second check marked."""
    ra = {}
    for cid, rid in second.get(u, []):
        ra.setdefault(cid, rid)
    ids = sorted(set(first.get(u, [])) | set(ra))
    items = []
    for cid in ids:
        c = by_id[cid]
        mark = (f' <a class="ra" href="kallor.html#{ra[cid]}">andra kontrollen, Riksarkivet</a>'
                if cid in ra else "")
        items.append(f'<li><a href="id/{cid}/">{escape(c["statement"])}</a>'
                     f' <span class="ctx">{escape(c["context"])}</span>{mark}</li>')
    return '<ul class="cl">' + "".join(items) + "</ul>"


def group_html(g, first, second, numbers, by_id):
    sources = sorted(g["urls"], key=lambda u: sv_key(ld.source_title(u)))
    w = g["work"]
    nums = {u: (ld.article_id(w, u) if w else None) or numbers.get(u) for u in sources}
    show_num = any(nums.values())
    meta = [TYPES[g["section"]]["label"] if g["section"] != "webbsida" else "Utgivare",
            iri_link(g["iri"])]
    pub = PUBLISHERS[g["publisher"]] if g["publisher"] else None
    if pub and pub["name"] != g["name"]:
        meta.append(f'utges av {escape(pub["name"])} ({iri_link(pub["iri"])})')
    n_src = len(sources)
    meta.append(f'{n_src} {"källa" if n_src == 1 else "källor"}, '
                f'{g["n_claims"]} {"uppgift" if g["n_claims"] == 1 else "uppgifter"}')
    rows = []
    for u in sources:
        num = f'<td class="num">{escape(nums[u] or "–")}</td>' if show_num else ""
        rows.append(f'<tr><td><a href="{escape(u)}">{escape(ld.source_title(u))}</a></td>{num}'
                    f'<td>{claim_list(u, first, second, by_id)}</td></tr>')
    num_head = "<th>Nummer</th>" if show_num else ""
    return (f'<h3 id="{anchor(g["iri"])}">{escape(g["name"])}</h3>\n'
            f'<p class="meta">{" · ".join(meta)}</p>\n'
            f'<p class="meta">Varje källa: {escape(TYPES[g["part_type"]]["label"].lower())}</p>\n'
            f'<div class="tw"><table><thead><tr><th>Titel</th>{num_head}<th>Uppgifter som hänvisar hit</th>'
            f'</tr></thead><tbody>\n' + "\n".join(rows) + "\n</tbody></table></div>")


def main():
    first, second, numbers = citations()
    gs = groups(first, second)
    by_id = {c["id"]: c for c in CLAIMS}
    n_all = len(set(first) | set(second))
    n_first, n_second = len(first), len(second)
    n_both = len(set(first) & set(second))
    toc, body = [], []
    for sec, title in SECTIONS:
        part = sorted((g for g in gs.values() if g["section"] == sec),
                      key=lambda g: (-g["n_claims"], sv_key(g["name"])))
        if not part:
            continue
        toc.append(f'<p><strong>{escape(title)}:</strong> '
                   + ", ".join(f'<a href="#{anchor(g["iri"])}">{escape(g["name"])}</a> <span class="ctx">{g["n_claims"]}</span>'
                               for g in part) + "</p>")
        body.append(f'<h2>{escape(title)}</h2>\n' + "\n".join(group_html(g, first, second, numbers, by_id)
                                                          for g in part))
    page = PAGE.format(n=n_all, n_first=n_first, n_second=n_second, n_both=n_both,
                       n_claims=len(CLAIMS), n_groups=len(gs), toc="\n".join(toc), body="\n".join(body))
    (HERE / "kallkatalog.html").write_text(page, encoding="utf-8")
    print(f"wrote kallkatalog.html: {n_all} sources in {len(gs)} groups")


PAGE = """<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nordens historia – källorna</title>
<style>
  body {{ margin: 0; background: #fbfaf7; color: #1d2733;
         font-family: Inter, "Helvetica Neue", Arial, sans-serif; line-height: 1.5; }}
  main {{ max-width: 1120px; margin: 0 auto; padding: 24px 16px 48px; }}
  .intro {{ max-width: 760px; }}
  a {{ color: #2f6db5; }}
  h2 {{ font-size: 1.25rem; margin-top: 2.2em; }}
  h3 {{ font-size: 1.05rem; margin: 1.8em 0 0.2em; }}
  .meta {{ color: #6b7682; font-size: 0.85rem; margin: 0.1em 0; }}
  .toc p {{ margin: 0.4em 0; font-size: 0.9rem; }}
  .tw {{ overflow-x: auto; margin-top: 0.5em; }}
  table {{ border-collapse: collapse; width: 100%; min-width: 640px; font-size: 0.85rem; }}
  th, td {{ text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid #e3e0d8; }}
  th {{ background: #f1eee7; font-weight: 700; }}
  td:first-child {{ width: 34%; }}
  td.num {{ color: #6b7682; white-space: nowrap; }}
  .ctx {{ color: #6b7682; font-size: 0.78rem; }}
  ul.cl {{ margin: 0; padding-left: 1.1em; }}
  a.ra {{ font-size: 0.78rem; }}
  .back {{ font-size: 0.9rem; }}
  h3:target {{ background: #fff6d6; }}
</style>
</head>
<body>
<main>
<p class="back"><a href="./">← Nordens historia – tidslinjen</a> · <a href="kallor.html">Källäget</a></p>
<h1>Nordens historia – källorna</h1>
<div class="intro">
<p>Här är alla {n} källor som affischens uppgifter vilar på, samlade per uppslagsverk, register,
tidskrift eller utgivare. {n_first} kommer från den första kontrollen av de {n_claims} uppgifterna,
{n_second} från den andra kontrollen mot Riksarkivet ({n_both} finns i båda). Vid varje källa står
vilka uppgifter som hänvisar till den. Hur varje uppgift bedömdes står i <a href="kallor.html">källäget</a>.</p>
<p>Varje verk och utgivare har en länk till Wikidata, där den finns. Svenskt Diplomatariums huvudkartotek
saknas i Wikidata och har i stället en egen identifierare. Grupperna står i ordning efter hur många
uppgifter som hänvisar till dem.</p>
</div>
<div class="toc">
{toc}
</div>
{body}
</main>
</body>
</html>
"""


if __name__ == "__main__":
    main()
