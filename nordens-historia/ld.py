"""Linked data for Nordens historia.

Reads data/items.json, data/claims.json and data/wikidata.json and writes
  id/index.html, id/index.jsonld                 register of all identifiers
  id/<nh-id>/index.html, id/<nh-id>/index.jsonld one page per period, event,
                                                 milestone and claim

URI pattern (static hosting, no content negotiation):
  thing     https://kerfors.github.io/sidospar/nordens-historia/id/nh-p0015
  page      https://kerfors.github.io/sidospar/nordens-historia/id/nh-p0015/
  data      https://kerfors.github.io/sidospar/nordens-historia/id/nh-p0015/index.jsonld
GitHub Pages answers the thing URI with a 301 redirect to the page.

Run: python3 ld.py
"""
import json
from html import escape
from pathlib import Path

HERE = Path(__file__).parent
BASE = "https://kerfors.github.io/sidospar/nordens-historia/"
ID = BASE + "id/"
CHECK_DATE = "2026-10-18"
ORIGINAL_POST = "https://lnkd.in/p/ePw54Bpe"
ORIGINAL_POSTER = "https://media.licdn.com/dms/image/v2/D4E22AQHrvGeeC1Ylvg/feedshare-shrink_480/B4EaFEPazcKoAg-/0/1792146255419?e=1793836800&v=beta&t=dkVaqlOlNRKleqIJVH9ou7Dd-xSD3iDiva5qpIxfqi4"

CONTEXT = {
    "@vocab": "https://schema.org/",
    "schema": "https://schema.org/",
    "crm": "http://www.cidoc-crm.org/cidoc-crm/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "prov": "http://www.w3.org/ns/prov#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "wd": "http://www.wikidata.org/entity/",
    "nh": ID,
    "skos:prefLabel": {"@container": "@language"},
    "skos:definition": {"@container": "@language"},
    "skos:inScheme": {"@type": "@id"},
    "skos:exactMatch": {"@type": "@id"},
    "skos:closeMatch": {"@type": "@id"},
    "dcterms:spatial": {"@type": "@id"},
    "crm:P7_took_place_at": {"@type": "@id"},
    "crm:P82a_begin_of_the_begin": {"@type": "xsd:gYear"},
    "crm:P82b_end_of_the_end": {"@type": "xsd:gYear"},
    "startDate": {"@type": "xsd:gYear"},
    "endDate": {"@type": "xsd:gYear"},
    "about": {"@type": "@id"},
    "itemReviewed": {"@type": "@id"},
    "citation": {"@type": "@id"},
    "isBasedOn": {"@type": "@id"},
    "license": {"@type": "@id"},
    "mainEntity": {"@type": "@id"},
    "isPartOf": {"@type": "@id"},
    "url": {"@type": "@id"},
    "prov:wasGeneratedBy": {"@type": "@id"},
    "prov:wasDerivedFrom": {"@type": "@id"},
    "prov:wasAssociatedWith": {"@type": "@id"},
    "prov:actedOnBehalfOf": {"@type": "@id"},
}

TYPE_LABEL = {"period": "Period", "event": "Händelse", "milestone": "Milstolpe", "claim": "Kontrollerad uppgift"}


# ---------------------------------------------------------------- years
def gyear(v):
    """Poster year (no year 0; -500 = 500 f.Kr.) -> astronomical xsd:gYear ('-0499')."""
    a = v + 1 if v < 0 else v
    return f"-{-a:04d}" if a < 0 else f"{a:04d}"


def yr(v):
    return f"{-v} f.Kr." if v < 0 else str(v)


# ---------------------------------------------------------------- load
def load():
    items = json.loads((HERE / "data" / "items.json").read_text(encoding="utf-8"))
    claims = json.loads((HERE / "data" / "claims.json").read_text(encoding="utf-8"))
    wpath = HERE / "data" / "wikidata.json"
    wd = json.loads(wpath.read_text(encoding="utf-8")) if wpath.exists() else {}
    return items, claims, wd


def place_ref(col, wd):
    m = wd.get("place:" + col)
    return f"wd:{m['qid']}" if m and m.get("qid") else None


def wd_links(item_id, kind, wd):
    """Wikidata link for an item. Periods/events: skos match. Milestones: schema:about
    (the milestone is the event of founding/inventing; Wikidata has the thing itself)."""
    m = wd.get(item_id)
    if not m or m.get("match") in (None, "none") or not m.get("qid"):
        return {}
    ref = {"@id": f"wd:{m['qid']}"}
    if kind == "milestone" or m.get("relation") == "about":
        return {"about": ref}
    return {f"skos:{m['match']}": f"wd:{m['qid']}"}


# ---------------------------------------------------------------- nodes
def period_node(p, wd):
    places = [x for x in (place_ref(c, wd) for c in p["columns"]) if x]
    node = {
        "@id": "nh:" + p["id"],
        "@type": ["crm:E4_Period", "skos:Concept"],
        "dcterms:identifier": p["id"],
        "name": p["label"],
        "skos:prefLabel": {"sv": p["label"]},
        "skos:inScheme": "nh:#perioder",
        "temporalCoverage": f"{gyear(p['start'])}/{gyear(p['end'])}",
        "crm:P4_has_time-span": {
            "@type": "crm:E52_Time-Span",
            "crm:P82a_begin_of_the_begin": gyear(p["start"]),
            "crm:P82b_end_of_the_end": gyear(p["end"]),
        },
        "crm:P7_took_place_at": places,
        "dcterms:spatial": places,
    }
    if p["description"]:
        node["description"] = p["description"]
        node["skos:definition"] = {"sv": p["description"]}
    node.update(wd_links(p["id"], "period", wd))
    return node


def event_node(e, wd, kind):
    cols = e["columns"] if kind == "event" else [e["column"]]
    places = [x for x in (place_ref(c, wd) for c in cols) if x]
    node = {
        "@id": "nh:" + e["id"],
        "@type": ["crm:E5_Event", "Event"],
        "dcterms:identifier": e["id"],
        "name": e["label"],
        "startDate": gyear(e["year"]),
        "crm:P4_has_time-span": {"@type": "crm:E52_Time-Span",
                                 "crm:P82a_begin_of_the_begin": gyear(e["year"])},
        "crm:P7_took_place_at": places,
    }
    node.update(wd_links(e["id"], kind, wd))
    return node


def claim_nodes(c):
    claim = {
        "@id": "nh:" + c["id"],
        "@type": "Claim",
        "dcterms:identifier": [c["id"], c["check_id"]],
        "text": c["statement"],
        "about": [{"@id": "nh:" + a} for a in c["about"]],
    }
    review = {
        "@id": "nh:" + c["id"] + "#granskning",
        "@type": ["ClaimReview", "prov:Entity"],
        "itemReviewed": "nh:" + c["id"],
        "reviewRating": {"@type": "Rating", "alternateName": c["verdict"]},
        "reviewBody": c["evidence"],
        "datePublished": c["checked"],
        "prov:wasGeneratedBy": "nh:#kontroll-" + CHECK_DATE,
    }
    if c["source_url"]:
        review["citation"] = {"@id": c["source_url"], "name": c["source_title"]}
        review["prov:wasDerivedFrom"] = c["source_url"]
    if c["correct_value"]:
        review["schema:correction"] = c["correct_value"]
    if c["action"]:
        review["schema:comment"] = {"@type": "Comment", "text": "Åtgärd på affischen: " + c["action"]}
    return [claim, review]


def shared_nodes(wd, columns):
    nodes = [
        {"@id": "nh:#dataset", "@type": "Dataset",
         "name": "Nordens historia – en tidslinje",
         "description": "Perioder, händelser och milstolpar i Nordens historia, med en källkontroll per uppgift.",
         "url": BASE, "inLanguage": "sv",
         "license": "https://creativecommons.org/licenses/by/4.0/",
         "creator": {"@type": "Person", "name": "Kerstin Forsberg", "url": "https://kerfors.github.io/"},
         "isBasedOn": {"@type": "CreativeWork", "name": "Timeline of World History",
                       "creator": {"@type": "Organization", "name": "Chart Origin", "url": "https://chartorigin.com"},
                       "url": ORIGINAL_POST,
                       "image": {"@type": "ImageObject", "contentUrl": {"@id": ORIGINAL_POSTER},
                                 "description": "Signerad LinkedIn-länk, giltig till 2026-11-05."}},
         "distribution": {"@type": "DataDownload", "encodingFormat": "application/ld+json",
                          "contentUrl": {"@id": ID + "index.jsonld"}}},
        {"@id": "nh:#perioder", "@type": "skos:ConceptScheme",
         "skos:prefLabel": {"sv": "Affischens periodindelning"}, "isPartOf": "nh:#dataset"},
        {"@id": "nh:#kontroll-" + CHECK_DATE, "@type": "prov:Activity",
         "name": "Källkontroll av affischens uppgifter",
         "prov:startedAtTime": {"@value": CHECK_DATE, "@type": "xsd:date"},
         "prov:wasAssociatedWith": "nh:#claude-agenter"},
        {"@id": "nh:#claude-agenter", "@type": ["prov:SoftwareAgent"],
         "name": "Claude, AI-agenter med webbsökning",
         "prov:actedOnBehalfOf": {"@type": ["prov:Person", "Person"], "name": "Kerstin Forsberg"}},
    ]
    for c in columns:
        ref = place_ref(c, wd)
        if ref:
            nodes.append({"@id": ref, "name": c})
    return nodes


# ---------------------------------------------------------------- html
CSS = """
  body { margin: 0; background: #fbfaf7; color: #1d2733;
         font-family: Inter, "Helvetica Neue", Arial, sans-serif; line-height: 1.5; }
  main { max-width: 860px; margin: 0 auto; padding: 24px 16px 48px; }
  a { color: #2f6db5; }
  .crumbs { font-size: 0.9rem; }
  .kind { color: #6b7682; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.06em; margin: 0; }
  h1 { margin: 0.1em 0 0.4em; }
  dl { display: grid; grid-template-columns: 11em 1fr; gap: 4px 12px; }
  dt { color: #6b7682; } dd { margin: 0; overflow-wrap: anywhere; }
  code { font-size: 0.85em; background: #f1eee7; padding: 1px 4px; border-radius: 3px; }
  table { border-collapse: collapse; width: 100%; font-size: 0.88rem; }
  th, td { text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid #e3e0d8; }
  th { background: #f1eee7; }
  .v { display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 0.78rem; white-space: nowrap; }
  .v.bekräftad { background: #d8efdc; } .v.omdiskuterad { background: #f7e3b5; }
  .v.avvikande { background: #f6c9c4; } .v.ej { background: #e3e3e3; }
  .tw { overflow-x: auto; }
  @media (max-width: 600px) { dl { grid-template-columns: 1fr; } dt { margin-top: 6px; } }
"""


def page(title, body, jsonld, depth):
    up = "../" * depth
    return f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} – Nordens historia</title>
<link rel="alternate" type="application/ld+json" href="index.jsonld">
<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=1)}
</script>
<style>{CSS}</style>
</head>
<body>
<main>
<p class="crumbs"><a href="{up}">Nordens historia</a> · <a href="../">Identifierare</a> · <a href="{up}kallor.html">Källäget</a></p>
{body}
</main>
</body>
</html>
"""


def verdict_badge(v):
    cls = "ej" if v == "ej verifierad" else v
    return f'<span class="v {cls}">{escape(v)}</span>'


def wd_html(item_id, wd):
    m = wd.get(item_id)
    if not m or m.get("match") in (None, "none") or not m.get("qid"):
        return "<em>ingen matchning</em>"
    rel = {"exactMatch": "samma som", "closeMatch": "närliggande"}.get(m["match"], m["match"])
    lab = escape(m.get("wikidata_label", ""))
    return f'<a href="https://www.wikidata.org/wiki/{m["qid"]}">{m["qid"]}</a> {lab} ({rel})'


def claims_table(cl, show_about=False, by_id=None):
    rows = []
    for c in cl:
        about = ""
        if show_about:
            about = "<td>" + ", ".join(f'<a href="../{a}/">{escape(by_id[a]["label"])}</a>' for a in c["about"]) + "</td>"
        src = (f'<a href="{escape(c["source_url"])}">{escape(c["source_title"] or c["source_url"])}</a>'
               if c["source_url"] else escape(c["source_title"]))
        rows.append(f'<tr><td><a href="../{c["id"]}/">{c["id"]}</a></td><td>{escape(c["statement"])}</td>'
                    f'{about}<td>{verdict_badge(c["verdict"])}</td><td>{src}</td></tr>')
    head = "<th>Uppgift</th>" + ("<th>Om</th>" if show_about else "")
    return ('<div class="tw"><table><thead><tr><th>Id</th>' + head + '<th>Utlåtande</th><th>Källa</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def item_page(item, kind, node, cl, wd, places):
    iri = ID + item["id"]
    if kind == "period":
        when = f"{yr(item['start'])} – {yr(item['end'])}"
        iso = f"<code>{gyear(item['start'])}/{gyear(item['end'])}</code>"
    else:
        when = yr(item["year"])
        iso = f"<code>{gyear(item['year'])}</code>"
    desc = f"<p>{escape(item['description'])}</p>" if item.get("description") else ""
    body = f"""<p class="kind">{TYPE_LABEL[kind]}</p>
<h1>{escape(item['label'])}</h1>
{desc}
<dl>
<dt>Identifierare</dt><dd><code>{iri}</code></dd>
<dt>Tid</dt><dd>{escape(when)} &nbsp;{iso}</dd>
<dt>Plats</dt><dd>{places}</dd>
<dt>Wikidata</dt><dd>{wd_html(item['id'], wd)}</dd>
<dt>På affischen</dt><dd><a href="../../#{item['id']}">Visa på affischen</a></dd>
<dt>Data</dt><dd><a href="index.jsonld">index.jsonld</a></dd>
</dl>
<h2>Kontrollerade uppgifter</h2>
{claims_table(cl)}
"""
    doc = {"@context": CONTEXT, "@graph": [
        {"@id": iri + "/", "@type": "WebPage", "mainEntity": "nh:" + item["id"], "isPartOf": "nh:#dataset"},
        node] + [n for c in cl for n in claim_nodes(c)]}
    return page(item["label"], body, doc, 2), doc


def claim_page(c, by_id):
    nodes = claim_nodes(c)
    iri = ID + c["id"]
    about = ", ".join(f'<a href="../{a}/">{escape(by_id[a]["label"])}</a> <code>{a}</code>' for a in c["about"])
    src = (f'<a href="{escape(c["source_url"])}">{escape(c["source_title"] or c["source_url"])}</a>'
           if c["source_url"] else escape(c["source_title"]))
    body = f"""<p class="kind">{TYPE_LABEL['claim']}</p>
<h1>{escape(c['statement'])}</h1>
<dl>
<dt>Identifierare</dt><dd><code>{iri}</code></dd>
<dt>Kontroll-id</dt><dd><code>{escape(c['check_id'])}</code> i <a href="../../kallor.html#{c['id']}">källäget</a></dd>
<dt>Om</dt><dd>{about}</dd>
<dt>Utlåtande</dt><dd>{verdict_badge(c['verdict'])}</dd>
<dt>Källa</dt><dd>{src}</dd>
<dt>Belägg</dt><dd>{escape(c['evidence'])}</dd>
{'<dt>Annat värde</dt><dd>' + escape(c['correct_value']) + '</dd>' if c['correct_value'] else ''}
{'<dt>Notering</dt><dd>' + escape(c['note']) + '</dd>' if c['note'] else ''}
<dt>Åtgärd</dt><dd>{escape(c['action']) or '–'}</dd>
<dt>Kontrollerad</dt><dd>{c['checked']}</dd>
<dt>Data</dt><dd><a href="index.jsonld">index.jsonld</a></dd>
</dl>
"""
    doc = {"@context": CONTEXT, "@graph": [
        {"@id": iri + "/", "@type": "WebPage", "mainEntity": "nh:" + c["id"], "isPartOf": "nh:#dataset"}] + nodes}
    return page(c["statement"], body, doc, 2), doc


REGISTER_INTRO = """<h1>Identifierare</h1>
<p>Varje period, händelse och milstolpe på <a href="../">affischen</a> och varje kontrollerad uppgift i
<a href="../kallor.html">källäget</a> har en egen beständig identifierare under
<code>{id}</code>. Identifieraren går att slå upp: den ger en sida för människor med
inbäddad JSON-LD, och en <code>index.jsonld</code> bredvid för maskiner. Hela datamängden finns i
<a href="index.jsonld">index.jsonld</a>. Den är licensierad under
<a href="https://creativecommons.org/licenses/by/4.0/deed.sv">CC BY 4.0</a>.</p>

<h2>Hur identifierarna är gjorda</h2>
<ul>
<li><strong>Opaka nummer.</strong> <code>nh-p</code> period, <code>nh-e</code> händelse, <code>nh-m</code> milstolpe,
<code>nh-c</code> kontrollerad uppgift. Namnet ingår inte, så en period kan byta namn utan att identifieraren ändras.
Numren delas ut en gång och återanvänds aldrig.</li>
<li><strong>Sak och dokument.</strong> <code>…/id/nh-p0015</code> är perioden, <code>…/id/nh-p0015/</code> sidan om den.
GitHub Pages svarar på den förra med en 301-omdirigering till den senare, inte den 303 som Linked Data-praxis
föreskriver. Sidan säger uttryckligen vad den handlar om (<code>schema:mainEntity</code>).</li>
<li><strong>Årtal.</strong> Affischen skriver 500 f.Kr.; datan använder astronomisk årsnumrering enligt
<code>xsd:gYear</code>, där 1 f.Kr. är år 0. 500 f.Kr. blir alltså <code>-0499</code>.</li>
</ul>

<h2>Vokabulär</h2>
<ul>
<li><strong>CIDOC-CRM</strong> för perioder och händelser: <code>crm:E4_Period</code>, <code>crm:E5_Event</code>,
tidsspann med <code>crm:P82a</code>/<code>P82b</code> och plats med <code>crm:P7_took_place_at</code>.</li>
<li><strong>SKOS</strong> i PeriodO:s anda: varje period är ett begrepp i affischens egen periodindelning
(<code>skos:inScheme</code>), med <code>dcterms:spatial</code>. Periodgränser är ett val av en viss källa, inte ett faktum.</li>
<li><strong>schema.org</strong> för det läsbara: <code>name</code>, <code>temporalCoverage</code>, och för
källkontrollen <code>Claim</code> och <code>ClaimReview</code> med utlåtande, belägg och källa.</li>
<li><strong>PROV-O</strong> för proveniensen: varje granskning är genererad av källkontrollen den {date}, utförd av
AI-agenter för Kerstin Forsbergs räkning, och härledd från sin källa.</li>
<li><strong>Wikidata</strong> som länk utåt. Perioder och händelser länkas med <code>skos:exactMatch</code> eller
<code>skos:closeMatch</code>. Milstolpar är händelser (grundandet, uppfinningen) och pekar på saken med
<code>schema:about</code>. Varje länk är hittad med Wikidatas sökverktyg och kontrollerad mot wikidata.org.</li>
</ul>
"""


def register_page(sections, doc):
    body = REGISTER_INTRO.format(id=ID, date=CHECK_DATE)
    for title, heads, rows in sections:
        th = "".join(f"<th>{h}</th>" for h in heads)
        body += f"<h2>{escape(title)}</h2>\n<div class=\"tw\"><table><thead><tr>{th}</tr></thead><tbody>"
        body += "".join(rows) + "</tbody></table></div>\n"
    html = f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Identifierare – Nordens historia</title>
<link rel="alternate" type="application/ld+json" href="index.jsonld">
<style>{CSS}</style>
</head>
<body>
<main>
<p class="crumbs"><a href="../">Nordens historia</a> · <a href="../kallor.html">Källäget</a></p>
{body}
</main>
</body>
</html>
"""
    return html


# ---------------------------------------------------------------- main
def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main():
    items, claims, wd = load()
    out = HERE / "id"
    by_id = {}
    kinds = [("period", items["periods"]), ("event", items["events"]), ("milestone", items["milestones"])]
    for kind, lst in kinds:
        for x in lst:
            by_id[x["id"]] = x
    claims_by_item = {}
    for c in claims:
        for a in c["about"]:
            claims_by_item.setdefault(a, []).append(c)

    graph = shared_nodes(wd, items["columns"])
    sections = []
    for kind, lst in kinds:
        rows = []
        for x in lst:
            node = period_node(x, wd) if kind == "period" else event_node(x, wd, kind)
            graph.append(node)
            cols = x.get("columns") or [x["column"]]
            places = ", ".join(
                f'<a href="https://www.wikidata.org/wiki/{wd["place:" + c]["qid"]}">{escape(c)}</a>'
                if wd.get("place:" + c, {}).get("qid") else escape(c) for c in cols)
            html, doc = item_page(x, kind, node, claims_by_item.get(x["id"], []), wd, places)
            write(out / x["id"] / "index.html", html)
            write(out / x["id"] / "index.jsonld", json.dumps(doc, ensure_ascii=False, indent=1))
            when = f"{yr(x['start'])} – {yr(x['end'])}" if kind == "period" else yr(x["year"])
            rows.append(f'<tr><td><a href="{x["id"]}/">{x["id"]}</a></td><td>{escape(x["label"])}'
                        f' <span style="color:#6b7682">· {escape(", ".join(cols))}</span></td>'
                        f'<td>{escape(when)}</td><td>{wd_html(x["id"], wd)}</td></tr>')
        sections.append(({"period": "Perioder", "event": "Händelser", "milestone": "Milstolpar"}[kind],
                         ["Id", "Namn", "Tid", "Wikidata"], rows))
    rows = []
    for c in claims:
        graph += claim_nodes(c)
        html, doc = claim_page(c, by_id)
        write(out / c["id"] / "index.html", html)
        write(out / c["id"] / "index.jsonld", json.dumps(doc, ensure_ascii=False, indent=1))
        rows.append(f'<tr><td><a href="{c["id"]}/">{c["id"]}</a></td><td>{escape(c["statement"])}</td>'
                    f'<td>{verdict_badge(c["verdict"])}</td><td><code>{escape(c["check_id"])}</code></td></tr>')
    sections.append(("Kontrollerade uppgifter", ["Id", "Uppgift", "Utlåtande", "Kontroll-id"], rows))
    full = {"@context": CONTEXT, "@graph": [
        {"@id": ID, "@type": "WebPage", "mainEntity": "nh:#dataset"}] + graph}
    write(out / "index.jsonld", json.dumps(full, ensure_ascii=False, indent=1))
    write(out / "index.html", register_page(sections, full))
    print(f"wrote id/: {len(by_id)} items, {len(claims)} claims")


if __name__ == "__main__":
    main()
