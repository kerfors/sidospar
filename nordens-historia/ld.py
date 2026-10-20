"""Linked data for Nordens historia.

Reads data/items.json, data/claims.json and data/wikidata.json and writes
  id/index.html, id/index.jsonld, id/index.ttl   register of all identifiers
  id/<nh-id>/index.html, index.jsonld, index.ttl one page per period, event,
                                                 milestone and claim
Turtle is generated from the JSON-LD with rdflib; the build fails if the two
do not give the same graph.

URI pattern (minted under w3id.org, hosted on GitHub Pages):
  thing     https://w3id.org/people/kerfors/sidospar/nordens-historia/id/nh-p0015
  page      https://w3id.org/people/kerfors/sidospar/nordens-historia/id/nh-p0015/
  data      https://w3id.org/people/kerfors/sidospar/nordens-historia/id/nh-p0015/index.jsonld
            https://w3id.org/people/kerfors/sidospar/nordens-historia/id/nh-p0015/index.ttl
w3id.org answers the thing URI with a 303 to a document about it: index.ttl
for text/turtle, index.jsonld for application/ld+json, otherwise the page.
The page and data URIs get a 302 to the same path under
https://kerfors.github.io/sidospar/. Rules: ids/people/kerfors/.htaccess in
perma-id/w3id.org.

Run: python3 ld.py
"""
import json
import re
from html import escape
from pathlib import Path
from urllib.parse import unquote

from rdflib import Graph
from rdflib.compare import isomorphic

HERE = Path(__file__).parent
BASE = "https://kerfors.github.io/sidospar/nordens-historia/"
ID = "https://w3id.org/people/kerfors/sidospar/nordens-historia/id/"
KALLOR = "https://w3id.org/people/kerfors/sidospar/kallor/id/"
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
    "time": "http://www.w3.org/2006/time#",
    "nh": ID,
    "kallor": KALLOR,
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
    "time:intervalMeets": {"@type": "@id"},
    "time:intervalMetBy": {"@type": "@id"},
    "crm:P10_falls_within": {"@type": "@id"},
    "dcterms:source": {"@type": "@id"},
    "dcterms:type": {"@type": "@id"},
    "skos:scopeNote": {"@container": "@language"},
    "mainEntity": {"@type": "@id"},
    "isPartOf": {"@type": "@id"},
    "url": {"@type": "@id"},
    "prov:wasGeneratedBy": {"@type": "@id"},
    "prov:wasDerivedFrom": {"@type": "@id"},
    "prov:wasAssociatedWith": {"@type": "@id"},
    "prov:actedOnBehalfOf": {"@type": "@id"},
    "prov:used": {"@type": "@id"},
    "publisher": {"@type": "@id"},
    "propertyID": {"@type": "@id"},
}

PREFIXES = {k: v for k, v in CONTEXT.items() if isinstance(v, str) and not k.startswith("@")}

TYPE_LABEL = {"period": "Period", "event": "Händelse", "milestone": "Milstolpe", "claim": "Kontrollerad uppgift"}

# claims.json "kind" -> concept in the scheme nh:#uppgiftstyper
CLAIM_KINDS = {
    "period": ("typ-period", "Periodens namn och gränser"),
    "detalj": ("typ-detalj", "Detalj i en periods beskrivning"),
    "händelse": ("typ-handelse", "Händelse och årtal"),
    "milstolpe": ("typ-milstolpe", "Milstolpe och årtal"),
}


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
    defs = json.loads((HERE / "data" / "definitions.json").read_text(encoding="utf-8"))["definitions"]
    return items, claims, wd, defs


def load_sources():
    """data/sources.json: what each source is and who publishes it. The IRIs are shared
    (Wikidata, and kallor/id/ for SDHK and the source types); the file is this project's own."""
    return json.loads((HERE / "data" / "sources.json").read_text(encoding="utf-8"))


SOURCES = load_sources()


def source_work(url):
    """The work a source URL is part of (an article in SBL, an entry in SDHK), or None."""
    for w in SOURCES["works"]:
        if any(url.startswith(p) for p in w["url_prefixes"]):
            return w
    return None


def article_id(w, url):
    """The article's number in its work, from the address, by the work's id_pattern
    (Wikidata's URL match pattern for the work's property). None if the address does not follow it."""
    if not w.get("id_pattern"):
        return None
    m = re.match(w["id_pattern"], unquote(url))
    return m.group(1) if m else None


def source_desc(url):
    """What a source URL is: part of a work, or a page published by an organisation.
    Empty for sources not yet described in data/sources.json."""
    types = SOURCES["types"]
    w = source_work(url)
    if w:
        t = types[w["part_type"]]
        return {"@type": t["schema"], "dcterms:type": t["iri"], "isPartOf": w["iri"]}
    host = url.split("/")[2] if url.startswith("http") else ""
    for o in SOURCES["publishers"]:
        if any(host == h or host.endswith("." + h) for h in o["hosts"]):
            t = types["webbsida"]
            return {"@type": t["schema"], "dcterms:type": t["iri"], "publisher": o["iri"]}
    return {}


def article_id_nodes(nodes):
    """The article number of each cited source, once per source and document. Kept out of the
    citations themselves: a source cited by several claims would otherwise get one blank
    PropertyValue node per citation."""
    urls = []
    for n in nodes:
        cit = n.get("citation")
        for x in (cit if isinstance(cit, list) else [cit] if cit else []):
            if x["@id"] not in urls:
                urls.append(x["@id"])
    out = []
    for url in urls:
        w = source_work(url)
        aid = article_id(w, url) if w else None
        if aid:
            out.append({"@id": url, "identifier": {"@type": "PropertyValue",
                                                   "propertyID": w["id_property"], "value": aid}})
    return out


def source_label_nodes():
    """The works and publishers: what they are, their names, and who publishes each work."""
    nodes = [{"@id": o["iri"], "@type": "Organization", "name": o["name"]} for o in SOURCES["publishers"]]
    for w in SOURCES["works"]:
        t = SOURCES["types"][w["type"]]
        node = {"@id": w["iri"], "@type": t["schema"], "dcterms:type": t["iri"], "name": w["name"]}
        if w["publisher"]:
            node["publisher"] = w["publisher"]
        nodes.append(node)
    return nodes


def load_riksarkivet():
    """data/riksarkivet.json: the second check, against SBL and SDHK via Riksarkivet's MCP service."""
    ra = json.loads((HERE / "data" / "riksarkivet.json").read_text(encoding="utf-8"))
    return {"checked": ra["checked"], "by_claim": {r["claim"]: r for r in ra["checks"]}}


# ---------------------------------------------------------------- turtle
def turtle(doc):
    """Turtle serialisation of a JSON-LD document. Fails if the two do not give the same graph."""
    g = Graph().parse(data=json.dumps(doc, ensure_ascii=False), format="json-ld")
    for prefix, ns in PREFIXES.items():
        g.bind(prefix, ns, override=True, replace=True)
    ttl = g.serialize(format="turtle")
    back = Graph().parse(data=ttl, format="turtle")
    if len(g) == 0 or not isomorphic(g, back):
        raise ValueError(f"JSON-LD and Turtle give different graphs: {doc['@graph'][0]['@id']}")
    return ttl


# ---------------------------------------------------------------- derived relations
def relations(items):
    """Derived from the poster layout, not stored:
    meets   - period a ends the year period b starts, and they share a column
    within  - an event or milestone lies inside a period in the same column"""
    periods = items["periods"]
    meets, met_by = {}, {}
    for a in periods:
        for b in periods:
            if a is not b and a["end"] == b["start"] and set(a["columns"]) & set(b["columns"]):
                meets.setdefault(a["id"], []).append(b["id"])
                met_by.setdefault(b["id"], []).append(a["id"])
    within, contains = {}, {}
    for kind in ("events", "milestones"):
        for e in items[kind]:
            cols = e.get("columns") or [e["column"]]
            for p in periods:
                last = p["end"] == max(q["end"] for q in periods)
                inside = p["start"] <= e["year"] < p["end"] or (last and e["year"] == p["end"])
                if inside and set(cols) & set(p["columns"]):
                    within.setdefault(e["id"], []).append(p["id"])
                    contains.setdefault(p["id"], []).append(e["id"])
    return {"meets": meets, "met_by": met_by, "within": within, "contains": contains}


# ---------------------------------------------------------------- sources as schemes
# Sources of boundary definitions that are not yet a work in data/sources.json.
PUBLICATIONS = [
    ("historiska.se", "historiska", "Statens historiska museer"),
    ("riksdagen.se", "riksdagen", "Sveriges riksdag"),
    ("natmus.dk", "natmus", "Nationalmuseet"),
]


def publication(url):
    """Key and name of the source a boundary definition comes from, and what the scheme points to:
    the work (dcterms:source) when it is in data/sources.json, otherwise the site's home page (url)."""
    w = source_work(url)
    if w and w.get("scheme"):
        return w["scheme"], w["name"], w["iri"]
    host = url.split("/")[2] if url.startswith("http") else ""
    for dom, key, name in PUBLICATIONS:
        if host == dom or host.endswith("." + dom):
            return key, name, f"https://{dom}/"
    raise ValueError(f"no publication for source {url}")


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
def period_node(p, wd, rel=None):
    rel = rel or {"meets": {}, "met_by": {}}
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
    if rel["meets"].get(p["id"]):
        node["time:intervalMeets"] = ["nh:" + x for x in rel["meets"][p["id"]]]
    if rel["met_by"].get(p["id"]):
        node["time:intervalMetBy"] = ["nh:" + x for x in rel["met_by"][p["id"]]]
    return node


def definition_node(d, p, wd):
    """A source's definition of the period, PeriodO style: its own concept in the
    source's scheme, matched to the poster's period."""
    key, name, _ = publication(d["source_url"])
    same = d["start"] == p["start"] and d["end"] == p["end"]
    span = {"@type": "crm:E52_Time-Span"}
    if d["start"] is not None:
        span["crm:P82a_begin_of_the_begin"] = gyear(d["start"])
    if d["end"] is not None:
        span["crm:P82b_end_of_the_end"] = gyear(d["end"])
    node = {
        "@id": f"nh:{p['id']}#{d['id']}",
        "@type": ["crm:E4_Period", "skos:Concept"],
        "dcterms:identifier": d["id"],
        "skos:prefLabel": {"sv": f"{p['label']} enligt {name}"},
        "skos:inScheme": f"nh:#kalla-{key}",
        ("skos:exactMatch" if same else "skos:closeMatch"): "nh:" + p["id"],
        "crm:P4_has_time-span": span,
        "dcterms:spatial": [x for x in (place_ref(c, wd) for c in p["columns"]) if x],
        "dcterms:source": d["source_url"],
        "prov:wasDerivedFrom": f"nh:{d['claim']}#granskning",
    }
    notes = []
    if d["as_stated"]:
        notes.append("Källans formulering: " + d["as_stated"])
    if d["approx_start"] or d["approx_end"]:
        notes.append("Ungefärligt årtal: " + ", ".join(
            x for x, f in (("start", d["approx_start"]), ("slut", d["approx_end"])) if f))
    if notes:
        node["skos:scopeNote"] = {"sv": ". ".join(notes)}
    return node


def scheme_nodes(defs):
    seen = {}
    for d in defs:
        key, name, ref = publication(d["source_url"])
        seen[key] = {"@id": f"nh:#kalla-{key}", "@type": "skos:ConceptScheme",
                     "skos:prefLabel": {"sv": f"Periodindelning enligt {name}"},
                     ("url" if ref.startswith("http") else "dcterms:source"): ref, "isPartOf": "nh:#dataset"}
    return list(seen.values())


def event_node(e, wd, kind, rel=None):
    rel = rel or {"within": {}}
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
    if rel["within"].get(e["id"]):
        node["crm:P10_falls_within"] = ["nh:" + x for x in rel["within"][e["id"]]]
    return node


def ra_citation(x):
    """A register entry: what it is, the work it is part of, and its number in that work."""
    w = source_work(x["url"])
    if not w or w["register"] != x["register"]:
        raise ValueError(f"record {x['url']} is not in work {x['register']} according to data/sources.json")
    return {"@id": x["url"], "name": x["title"], **source_desc(x["url"]),
            "dcterms:identifier": x["register"] + " " + x["id"],
            "identifier": {"@type": "PropertyValue", "propertyID": w["id_property"], "value": x["id"]}}


def ra_review_node(c, r, checked):
    """The second check of a claim, against Riksarkivet's registers."""
    node = {
        "@id": "nh:" + c["id"] + "#riksarkivet",
        "@type": ["ClaimReview", "prov:Entity"],
        "dcterms:identifier": r["id"],
        "itemReviewed": "nh:" + c["id"],
        "reviewRating": {"@type": "Rating", "alternateName": r["verdict"]},
        "reviewBody": r["evidence"],
        "datePublished": checked,
        "prov:wasGeneratedBy": "nh:#kontroll-riksarkivet-" + checked,
        "citation": [ra_citation(x) for x in r["records"]],
        "prov:wasDerivedFrom": [x["url"] for x in r["records"]],
    }
    if r["note"]:
        node["schema:comment"] = {"@type": "Comment", "text": r["note"]}
    return node


def claim_nodes(c, ra):
    claim = {
        "@id": "nh:" + c["id"],
        "@type": "Claim",
        "dcterms:identifier": [c["id"], c["check_id"]],
        "text": c["statement"],
        "about": [{"@id": "nh:" + a} for a in c["about"]],
        "dcterms:type": "nh:#" + CLAIM_KINDS[c["kind"]][0],
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
        review["citation"] = {"@id": c["source_url"], "name": c["source_title"], **source_desc(c["source_url"])}
        review["prov:wasDerivedFrom"] = c["source_url"]
    if c["correct_value"]:
        review["schema:correction"] = c["correct_value"]
    if c["action"]:
        review["schema:comment"] = {"@type": "Comment", "text": "Åtgärd på affischen: " + c["action"]}
    if c["id"] in ra["by_claim"]:
        return [claim, review, ra_review_node(c, ra["by_claim"][c["id"]], ra["checked"])]
    return [claim, review]


def shared_nodes(wd, columns, ra):
    nodes = [
        {"@id": "nh:#dataset", "@type": "Dataset",
         "name": "Nordens historia – en tidslinje",
         "description": "Perioder, händelser och milstolpar i Nordens historia, med en källkontroll per uppgift.",
         "url": BASE, "inLanguage": "sv",
         "license": "https://creativecommons.org/licenses/by/4.0/",
         "creator": {"@type": "Person", "name": "Kerstin Forsberg", "url": "https://kerfors.github.io/"},
         "isBasedOn": {"@type": "CreativeWork", "name": "Timeline of World History",
                       "creator": {"@type": "Organization", "name": "Chart Origin", "url": "https://chartorigin.com"},
                       "url": ORIGINAL_POST},
         "distribution": [{"@type": "DataDownload", "encodingFormat": "application/ld+json",
                           "contentUrl": {"@id": ID + "index.jsonld"}},
                          {"@type": "DataDownload", "encodingFormat": "text/turtle",
                           "contentUrl": {"@id": ID + "index.ttl"}}]},
        {"@id": "nh:#perioder", "@type": "skos:ConceptScheme",
         "skos:prefLabel": {"sv": "Affischens periodindelning"}, "isPartOf": "nh:#dataset",
         "dcterms:creator": {"@type": "Person", "name": "Kerstin Forsberg"},
         "skos:scopeNote": {"sv": "Affischens egna periodgränser, valda för att blocken ska gå att läsa. "
                                  "Källornas gränser finns som egna definitioner i separata scheman och är matchade mot affischens perioder."}},
        {"@id": "nh:#uppgiftstyper", "@type": "skos:ConceptScheme",
         "skos:prefLabel": {"sv": "Typer av kontrollerade uppgifter"}, "isPartOf": "nh:#dataset"},
    ] + [
        {"@id": "nh:#" + key, "@type": "skos:Concept", "skos:prefLabel": {"sv": label},
         "skos:inScheme": "nh:#uppgiftstyper"}
        for key, label in CLAIM_KINDS.values()
    ] + [
        {"@id": "nh:#kontroll-" + CHECK_DATE, "@type": "prov:Activity",
         "name": "Källkontroll av affischens uppgifter",
         "prov:startedAtTime": {"@value": CHECK_DATE, "@type": "xsd:date"},
         "prov:wasAssociatedWith": "nh:#claude-agenter"},
        {"@id": "nh:#claude-agenter", "@type": ["prov:SoftwareAgent"],
         "name": "Claude, AI-agenter med webbsökning",
         "prov:actedOnBehalfOf": {"@type": ["prov:Person", "Person"], "name": "Kerstin Forsberg"}},
        {"@id": "nh:#kontroll-riksarkivet-" + ra["checked"], "@type": "prov:Activity",
         "name": "Kontroll mot Riksarkivets SBL och SDHK",
         "prov:startedAtTime": {"@value": ra["checked"], "@type": "xsd:date"},
         "prov:wasAssociatedWith": "nh:#claude-agenter",
         "prov:used": "nh:#riksarkivets-mcp"},
        {"@id": "nh:#riksarkivets-mcp", "@type": ["WebAPI", "prov:Entity"],
         "name": "Riksarkivets MCP-tjänst (beta)",
         "provider": {"@id": "wd:Q1724971"}},
    ] + source_label_nodes()
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
  .ids { margin-top: 3em; color: #6b7682; font-size: 0.8rem; overflow-wrap: anywhere; }
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
<link rel="alternate" type="text/turtle" href="index.ttl">
<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=1)}
</script>
<style>{CSS}</style>
</head>
<body>
<main>
<p class="crumbs"><a href="{up}">Nordens historia</a> · <a href="../">Identifierare</a> · <a href="{up}kallor.html">Källäget</a> · <a href="{up}sparql.html">SPARQL</a></p>
{body}
</main>
</body>
</html>
"""


def ids_html(iri):
    """Identifier and data links, as a small line at the foot of an item or claim page."""
    return (f'<p class="ids">Identifierare <code>{iri}</code> · '
            f'Data: <a href="index.jsonld">index.jsonld</a> · <a href="index.ttl">index.ttl</a></p>')


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


def claims_table(cl, ra, show_about=False, by_id=None):
    rows = []
    for c in cl:
        about = ""
        if show_about:
            about = "<td>" + ", ".join(f'<a href="../{a}/">{escape(by_id[a]["label"])}</a>' for a in c["about"]) + "</td>"
        src = (f'<a href="{escape(c["source_url"])}">{escape(c["source_title"] or c["source_url"])}</a>'
               if c["source_url"] else escape(c["source_title"]))
        r = ra["by_claim"].get(c["id"])
        second = f'<br><span style="color:#6b7682">Riksarkivet:</span> {verdict_badge(r["verdict"])}' if r else ""
        rows.append(f'<tr><td><a href="../{c["id"]}/">{c["id"]}</a></td><td>{escape(c["statement"])}</td>'
                    f'{about}<td>{verdict_badge(c["verdict"])}{second}</td><td>{src}</td></tr>')
    head = "<th>Uppgift</th>" + ("<th>Om</th>" if show_about else "")
    return ('<div class="tw"><table><thead><tr><th>Id</th>' + head + '<th>Utlåtande</th><th>Källa</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>")


def ra_html(r, checked):
    """The second check, against Riksarkivet's registers, on a claim page."""
    recs = "<br>".join(
        f'<a href="{escape(x["url"])}">{escape(x["title"])}</a>'
        + (f' <span style="color:#6b7682">(registrets datering: {escape(x["date"])})</span>' if x.get("date") else "")
        for x in r["records"])
    note = f'<dt>Notering</dt><dd>{escape(r["note"])}</dd>' if r["note"] else ""
    return f"""<h2>Andra kontrollen: Riksarkivet</h2>
<p>Uppgiften är också kontrollerad mot två källor hos Riksarkivet, uppslagsverket Svenskt biografiskt lexikon (SBL) och
registret Svenskt Diplomatariums huvudkartotek (SDHK), genom Riksarkivets MCP-tjänst (beta). Det är en egen granskning bredvid den första.</p>
<dl>
<dt>Utlåtande</dt><dd>{verdict_badge(r["verdict"])}</dd>
<dt>Artiklar och registerposter</dt><dd>{recs}</dd>
<dt>Belägg</dt><dd>{escape(r["evidence"])}</dd>
{note}
<dt>Kontrollerad</dt><dd>{checked}</dd>
</dl>
"""


def link_list(ids, by_id):
    return ", ".join(f'<a href="../{i}/">{escape(by_id[i]["label"])}</a>' for i in ids)


def related_html(item, kind, rel, by_id):
    rows = []
    if kind == "period":
        if rel["met_by"].get(item["id"]):
            rows.append(("Föregås av", link_list(rel["met_by"][item["id"]], by_id)))
        if rel["meets"].get(item["id"]):
            rows.append(("Följs av", link_list(rel["meets"][item["id"]], by_id)))
        if rel["contains"].get(item["id"]):
            rows.append(("Under perioden", link_list(rel["contains"][item["id"]], by_id)))
    elif rel["within"].get(item["id"]):
        rows.append(("Inträffar under", link_list(rel["within"][item["id"]], by_id)))
    return "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in rows)


def definitions_html(item, defs):
    if not defs:
        return ""
    rows = []
    rows.append(f'<tr><td><strong>Affischen</strong></td><td>{escape(yr(item["start"]))} – {escape(yr(item["end"]))}</td>'
                f'<td>affischens eget val</td><td></td></tr>')
    for d in defs:
        _, name, _ = publication(d["source_url"])
        s = (("c. " if d["approx_start"] else "") + yr(d["start"]) if d["start"] is not None else "?")
        e = (("c. " if d["approx_end"] else "") + yr(d["end"]) if d["end"] is not None else "?")
        same = d["start"] == item["start"] and d["end"] == item["end"]
        rel = "samma" if same else "avviker"
        stated = f'<br><span style="color:#6b7682">{escape(d["as_stated"])}</span>' if d["as_stated"] else ""
        rows.append(f'<tr id="{escape(d["id"])}"><td><a href="{escape(d["source_url"])}">{escape(name)}</a>{stated}</td>'
                    f'<td>{escape(s)} – {escape(e)}</td><td>{rel}</td>'
                    f'<td><a href="../{d["claim"]}/">{d["claim"]}</a></td></tr>')
    return ('<h2>Källornas gränser</h2>\n<p>Affischens gräns är ett val. Här är de gränser källorna själva drar, '
            'och om de sammanfaller med affischens eller avviker.</p>\n'
            '<div class="tw"><table><thead><tr><th>Källa</th><th>Gräns</th><th>Mot affischen</th><th>Uppgift</th></tr></thead><tbody>'
            + "".join(rows) + "</tbody></table></div>\n")


def item_page(item, kind, node, cl, wd, places, ra, rel=None, by_id=None, defs=(), def_nodes=()):
    rel = rel or {"meets": {}, "met_by": {}, "within": {}, "contains": {}}
    iri = ID + item["id"]
    if kind == "period":
        when = f"{yr(item['start'])} – {yr(item['end'])}"
    else:
        when = yr(item["year"])
    desc = f"<p>{escape(item['description'])}</p>" if item.get("description") else ""
    doc = {"@context": CONTEXT, "@graph": [
        {"@id": iri + "/", "@type": "WebPage", "mainEntity": "nh:" + item["id"], "isPartOf": "nh:#dataset"},
        node] + list(def_nodes) + [n for c in cl for n in claim_nodes(c, ra)]}
    doc["@graph"] += article_id_nodes(doc["@graph"])
    ttl = turtle(doc)
    body = f"""<p class="kind">{TYPE_LABEL[kind]}</p>
<h1>{escape(item['label'])}</h1>
{desc}
<dl>
<dt>Tid</dt><dd>{escape(when)}</dd>
<dt>Plats</dt><dd>{places}</dd>
<dt>Wikidata</dt><dd>{wd_html(item['id'], wd)}</dd>
{related_html(item, kind, rel, by_id) if by_id else ""}
<dt>På affischen</dt><dd><a href="../../#{item['id']}">Visa på affischen</a></dd>
</dl>
{definitions_html(item, defs)}
<h2>Kontrollerade uppgifter</h2>
{claims_table(cl, ra)}
{ids_html(iri)}"""
    return page(item["label"], body, doc, 2), doc, ttl


def claim_page(c, by_id, ra):
    nodes = claim_nodes(c, ra)
    iri = ID + c["id"]
    about = ", ".join(f'<a href="../{a}/">{escape(by_id[a]["label"])}</a> <code>{a}</code>' for a in c["about"])
    src = (f'<a href="{escape(c["source_url"])}">{escape(c["source_title"] or c["source_url"])}</a>'
           if c["source_url"] else escape(c["source_title"]))
    doc = {"@context": CONTEXT, "@graph": [
        {"@id": iri + "/", "@type": "WebPage", "mainEntity": "nh:" + c["id"], "isPartOf": "nh:#dataset"}] + nodes}
    doc["@graph"] += article_id_nodes(doc["@graph"])
    ttl = turtle(doc)
    body = f"""<p class="kind">{TYPE_LABEL['claim']}</p>
<h1>{escape(c['statement'])}</h1>
<dl>
<dt>Kontroll-id</dt><dd><code>{escape(c['check_id'])}</code> i <a href="../../kallor.html#{c['id']}">källäget</a></dd>
<dt>Om</dt><dd>{about}</dd>
<dt>Utlåtande</dt><dd>{verdict_badge(c['verdict'])}</dd>
<dt>Källa</dt><dd>{src}</dd>
<dt>Belägg</dt><dd>{escape(c['evidence'])}</dd>
{'<dt>Annat värde</dt><dd>' + escape(c['correct_value']) + '</dd>' if c['correct_value'] else ''}
{'<dt>Notering</dt><dd>' + escape(c['note']) + '</dd>' if c['note'] else ''}
<dt>Åtgärd</dt><dd>{escape(c['action']) or '–'}</dd>
<dt>Kontrollerad</dt><dd>{c['checked']}</dd>
</dl>
{ra_html(ra["by_claim"][c["id"]], ra["checked"]) if c["id"] in ra["by_claim"] else ""}
{ids_html(iri)}"""
    return page(c["statement"], body, doc, 2), doc, ttl


REGISTER_INTRO = """<h1>Identifierare</h1>
<p>Varje period, händelse och milstolpe på <a href="../">affischen</a> och varje kontrollerad uppgift i
<a href="../kallor.html">källäget</a> har en egen beständig identifierare under
<code>{id}</code>. Identifieraren går att slå upp: den ger en sida för människor med
inbäddad JSON-LD, och en <code>index.jsonld</code> och en <code>index.ttl</code> (Turtle) bredvid för maskiner.
Hela datamängden finns i <a href="index.jsonld">index.jsonld</a> och <a href="index.ttl">index.ttl</a>,
och går att ställa frågor mot på <a href="../sparql.html">SPARQL-sidan</a>. Tankarna bakom modellen beskrivs på engelska i
<a href="../linked-data.html">The linked data behind the poster</a>. Datamängden är licensierad under
<a href="https://creativecommons.org/licenses/by/4.0/deed.sv">CC BY 4.0</a>.</p>

<h2>Hur identifierarna är gjorda</h2>
<ul>
<li><strong>Opaka nummer.</strong> <code>nh-p</code> period, <code>nh-e</code> händelse, <code>nh-m</code> milstolpe,
<code>nh-c</code> kontrollerad uppgift. Namnet ingår inte, så en period kan byta namn utan att identifieraren ändras.
Numren delas ut en gång och återanvänds aldrig.</li>
<li><strong>Sak och dokument.</strong> <code>…/id/nh-p0015</code> är perioden, <code>…/id/nh-p0015/</code> sidan om den.
w3id.org svarar på den förra med en 303-omdirigering till ett dokument om perioden: <code>index.ttl</code> för
den som ber om Turtle, <code>index.jsonld</code> för JSON-LD, annars sidan. Sidan säger uttryckligen vad den handlar om (<code>schema:mainEntity</code>).</li>
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
källkontrollen <code>Claim</code> och <code>ClaimReview</code> med utlåtande, belägg och källa. Varje uppgift har en
typ (<code>dcterms:type</code>): periodens namn och gränser, en detalj i periodens beskrivning, en händelse eller en milstolpe.</li>
<li><strong>Källornas gränser</strong> i PeriodO:s anda: varje källas periodgräns är en egen definition i ett
schema för den källan (Store norske leksikon, Lex, Uppslagsverket Finland, NE …), matchad mot affischens period med
<code>skos:exactMatch</code> när gränserna sammanfaller och <code>skos:closeMatch</code> när de avviker, och härledd
(<code>prov:wasDerivedFrom</code>) från källkontrollens granskning. Ungefärliga årtal är markerade, och källans
formulering finns i <code>skos:scopeNote</code>.</li>
<li><strong>OWL-Time och CIDOC-CRM</strong> för relationerna mellan posterna, härledda ur affischen:
<code>time:intervalMeets</code> när en period slutar samma år som nästa börjar i samma kolumn, och
<code>crm:P10_falls_within</code> för händelser och milstolpar som inträffar under en period.</li>
<li><strong>PROV-O</strong> för proveniensen: varje granskning är genererad av källkontrollen den {date}, utförd av
AI-agenter för Kerstin Forsbergs räkning, och härledd från sin källa. En del uppgifter har också en andra granskning,
mot Riksarkivets SBL och SDHK, genererad av en egen aktivitet som använde Riksarkivets MCP-tjänst.</li>
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
<link rel="alternate" type="text/turtle" href="index.ttl">
<style>{CSS}</style>
</head>
<body>
<main>
<p class="crumbs"><a href="../">Nordens historia</a> · <a href="../kallor.html">Källäget</a> · <a href="../sparql.html">SPARQL</a></p>
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
    items, claims, wd, defs = load()
    ra = load_riksarkivet()
    rel = relations(items)
    defs_by_period = {}
    for d in defs:
        defs_by_period.setdefault(d["period"], []).append(d)
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

    graph = shared_nodes(wd, items["columns"], ra) + scheme_nodes(defs)
    sections = []
    for kind, lst in kinds:
        rows = []
        for x in lst:
            node = period_node(x, wd, rel) if kind == "period" else event_node(x, wd, kind, rel)
            dnodes = [definition_node(d, x, wd) for d in defs_by_period.get(x["id"], [])]
            graph.append(node)
            graph += dnodes
            cols = x.get("columns") or [x["column"]]
            places = ", ".join(
                f'<a href="https://www.wikidata.org/wiki/{wd["place:" + c]["qid"]}">{escape(c)}</a>'
                if wd.get("place:" + c, {}).get("qid") else escape(c) for c in cols)
            html, doc, ttl = item_page(x, kind, node, claims_by_item.get(x["id"], []), wd, places, ra,
                                       rel, by_id, defs_by_period.get(x["id"], []), dnodes)
            write(out / x["id"] / "index.html", html)
            write(out / x["id"] / "index.jsonld", json.dumps(doc, ensure_ascii=False, indent=1))
            write(out / x["id"] / "index.ttl", ttl)
            when = f"{yr(x['start'])} – {yr(x['end'])}" if kind == "period" else yr(x["year"])
            rows.append(f'<tr><td><a href="{x["id"]}/">{x["id"]}</a></td><td>{escape(x["label"])}'
                        f' <span style="color:#6b7682">· {escape(", ".join(cols))}</span></td>'
                        f'<td>{escape(when)}</td><td>{wd_html(x["id"], wd)}</td></tr>')
        sections.append(({"period": "Perioder", "event": "Händelser", "milestone": "Milstolpar"}[kind],
                         ["Id", "Namn", "Tid", "Wikidata"], rows))
    rows = []
    for c in claims:
        graph += claim_nodes(c, ra)
        html, doc, ttl = claim_page(c, by_id, ra)
        write(out / c["id"] / "index.html", html)
        write(out / c["id"] / "index.jsonld", json.dumps(doc, ensure_ascii=False, indent=1))
        write(out / c["id"] / "index.ttl", ttl)
        rows.append(f'<tr><td><a href="{c["id"]}/">{c["id"]}</a></td><td>{escape(c["statement"])}</td>'
                    f'<td>{verdict_badge(c["verdict"])}</td><td><code>{escape(c["check_id"])}</code></td></tr>')
    sections.append(("Kontrollerade uppgifter", ["Id", "Uppgift", "Utlåtande", "Kontroll-id"], rows))
    full = {"@context": CONTEXT, "@graph": [
        {"@id": ID, "@type": "WebPage", "mainEntity": "nh:#dataset"}] + graph}
    full["@graph"] += article_id_nodes(full["@graph"])
    write(out / "index.jsonld", json.dumps(full, ensure_ascii=False, indent=1))
    write(out / "index.ttl", turtle(full))
    write(out / "index.html", register_page(sections, full))
    import ld_page
    ld_page.build(out / "index.jsonld", HERE / "linked-data.html")
    import sparql_page
    sparql_page.build(out / "index.ttl", HERE / "sparql.html")
    print(f"wrote id/: {len(by_id)} items, {len(claims)} claims, {len(defs)} source definitions, "
          f"{sum(map(len, rel['meets'].values()))} meets, {sum(map(len, rel['within'].values()))} falls-within")


if __name__ == "__main__":
    main()
