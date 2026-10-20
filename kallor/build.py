"""Källorna som sidospåren hänvisar till, som linked data.

Reads data/kallor.json and writes
  id/index.html, id/index.jsonld, id/index.ttl   all sources: types, publishers, works
  id/<local-id>/index.html, index.jsonld, index.ttl
                                                 one page per work with its own identifier
Turtle is generated from the JSON-LD with rdflib; the build fails if the two
do not give the same graph.

URI pattern, the same generic w3id rule as the projects (kallor/ is a "project"):
  thing     https://w3id.org/people/kerfors/sidospar/kallor/id/sdhk
  page      https://w3id.org/people/kerfors/sidospar/kallor/id/sdhk/
  types     https://w3id.org/people/kerfors/sidospar/kallor/id/#artikel   (fragments of the register)
Works and publishers that have a Wikidata item use the Wikidata IRI; this
graph says what they are and who publishes them.

Run: python3 build.py
"""
import json
from html import escape
from pathlib import Path

from rdflib import Graph
from rdflib.compare import isomorphic

HERE = Path(__file__).parent
ID = "https://w3id.org/people/kerfors/sidospar/kallor/id/"
WD = "http://www.wikidata.org/entity/"

CONTEXT = {
    "@vocab": "https://schema.org/",
    "schema": "https://schema.org/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "wd": WD,
    "kallor": ID,
    "skos:prefLabel": {"@container": "@language"},
    "skos:inScheme": {"@type": "@id"},
    "skos:exactMatch": {"@type": "@id"},
    "skos:closeMatch": {"@type": "@id"},
    "dcterms:type": {"@type": "@id"},
    "dcterms:relation": {"@type": "@id"},
    "publisher": {"@type": "@id"},
    "isPartOf": {"@type": "@id"},
    "mainEntity": {"@type": "@id"},
    "url": {"@type": "@id"},
}
PREFIXES = {k: v for k, v in CONTEXT.items() if isinstance(v, str) and not k.startswith("@")}


def load():
    return json.loads((HERE / "data" / "kallor.json").read_text(encoding="utf-8"))


def expand(iri):
    """Prefixed IRI from kallor.json ('wd:Q…', 'kallor:…') -> full IRI."""
    prefix, local = iri.split(":", 1)
    return {"wd": WD, "kallor": ID}[prefix] + local


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


# ---------------------------------------------------------------- nodes
def type_nodes(data):
    nodes = [{"@id": "kallor:#kalltyper", "@type": "skos:ConceptScheme",
              "skos:prefLabel": {"sv": "Typer av källor"}}]
    for t in data["types"]:
        node = {"@id": "kallor:#" + t["id"], "@type": "skos:Concept",
                "skos:prefLabel": {"sv": t["label"]}, "skos:inScheme": "kallor:#kalltyper"}
        if t["qid"]:
            node["skos:" + t["match"]] = "wd:" + t["qid"]
        nodes.append(node)
    return nodes


def publisher_node(p):
    return {"@id": p["iri"], "@type": "Organization", "name": p["name"], "url": p["url"]}


def work_node(w, types):
    node = {"@id": w["iri"], "@type": types[w["type"]]["schema"], "dcterms:type": "kallor:#" + w["type"],
            "name": w["name"], "url": w["url"], "publisher": next(
                p["iri"] for p in DATA["publishers"] if p["id"] == w["publisher"]),
            "description": w["description"]}
    if w.get("related"):
        node["dcterms:relation"] = w["related"]
    return node


# ---------------------------------------------------------------- html
CSS = """
  body { margin: 0; background: #fbfaf7; color: #1d2733;
         font-family: Inter, "Helvetica Neue", Arial, sans-serif; line-height: 1.5; }
  main { max-width: 860px; margin: 0 auto; padding: 24px 16px 48px; }
  a { color: #2f6db5; }
  .kind { color: #6b7682; font-size: 0.85rem; text-transform: uppercase; letter-spacing: 0.06em; margin: 0; }
  h1 { margin: 0.1em 0 0.4em; }
  dl { display: grid; grid-template-columns: 11em 1fr; gap: 4px 12px; }
  dt { color: #6b7682; } dd { margin: 0; overflow-wrap: anywhere; }
  .ids { margin-top: 3em; color: #6b7682; font-size: 0.8rem; overflow-wrap: anywhere; }
  code { font-size: 0.85em; background: #f1eee7; padding: 1px 4px; border-radius: 3px; }
  table { border-collapse: collapse; width: 100%; font-size: 0.88rem; }
  th, td { text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid #e3e0d8; }
  th { background: #f1eee7; }
  .tw { overflow-x: auto; }
  @media (max-width: 600px) { dl { grid-template-columns: 1fr; } dt { margin-top: 6px; } }
"""


def page(title, crumbs, body, jsonld):
    script = ""
    if jsonld is not None:
        script = ('<script type="application/ld+json">\n'
                  + json.dumps(jsonld, ensure_ascii=False, indent=1) + "\n</script>\n")
    return f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{escape(title)} – Sidospår</title>
<link rel="alternate" type="application/ld+json" href="index.jsonld">
<link rel="alternate" type="text/turtle" href="index.ttl">
{script}<style>{CSS}</style>
</head>
<body>
<main>
<p class="crumbs">{crumbs}</p>
{body}
</main>
</body>
</html>
"""


def link(iri, text=None):
    """A prefixed IRI as a link, from the register page, to where it can be looked up."""
    full = expand(iri)
    if full.startswith(ID):
        local = full[len(ID):]
        href = local if local.startswith("#") else local + "/"
    else:
        href = "https://www.wikidata.org/wiki/" + full[len(WD):]
    return f'<a href="{escape(href)}">{escape(text or iri)}</a>'


def wd_link(qid, label):
    return f'<a href="https://www.wikidata.org/wiki/{qid}">{qid}</a> {escape(label)}'


def work_page(w, node, types):
    iri = expand(w["iri"])
    pub = next(p for p in DATA["publishers"] if p["id"] == w["publisher"])
    doc = {"@context": CONTEXT, "@graph": [
        {"@id": iri + "/", "@type": "WebPage", "mainEntity": w["iri"], "isPartOf": ID}, node]}
    ttl = turtle(doc)
    related = ""
    if w.get("related"):
        related = f'<dt>Se också</dt><dd><a href="https://www.wikidata.org/wiki/{expand(w["related"])[len(WD):]}">' \
                  f'Diplomatarium Suecanum</a> (utgåvan i bokform)</dd>'
    body = f"""<p class="kind">{escape(types[w["type"]]["label"])}</p>
<h1>{escape(w["name"])}</h1>
<p>{escape(w["description"])}</p>
<dl>
<dt>Utgivare</dt><dd>{wd_link(expand(pub["iri"])[len(WD):], pub["name"])}</dd>
<dt>Webbplats</dt><dd><a href="{escape(w["url"])}">{escape(w["url"])}</a></dd>
<dt>Delarna är</dt><dd>{escape(types[w["part_type"]]["label"].lower())}</dd>
{related}
</dl>
<p class="ids">Identifierare <code>{iri}</code> · Data: <a href="index.jsonld">index.jsonld</a> · <a href="index.ttl">index.ttl</a></p>"""
    crumbs = '<a href="../../../">Sidospår</a> · <a href="../">Källor</a>'
    return page(w["name"], crumbs, body, doc), doc, ttl


def register_page(data, types):
    rows_t = "".join(
        f'<tr id="{t["id"]}"><td>{escape(t["label"])}</td>'
        f'<td>{wd_link(t["qid"], t["wikidata_label"]) + " (" + ("samma som" if t["match"] == "exactMatch" else "närliggande") + ")" if t["qid"] else "<em>ingen matchning</em>"}</td></tr>'
        for t in data["types"])
    rows_w = "".join(
        f'<tr><td>{link(w["iri"], w["name"])}</td><td>{escape(types[w["type"]]["label"])}</td>'
        f'<td>{escape(next(p["name"] for p in data["publishers"] if p["id"] == w["publisher"]))}</td></tr>'
        for w in data["works"])
    rows_p = "".join(
        f'<tr><td>{link(p["iri"], p["name"])}</td><td><a href="{escape(p["url"])}">{escape(p["url"])}</a></td></tr>'
        for p in data["publishers"])
    body = f"""<h1>Källor</h1>
<p>Källorna som sidospåren hänvisar till: vad varje källa är och vem som ger ut den. Verk och utgivare
som finns i Wikidata har Wikidatas identifierare. De som saknas där har en egen identifierare under
<code>{ID}</code>, som går att slå upp på samma sätt som perioderna i Nordens historia.
Sidospåren pekar på identifierarna här, på samma sätt som på Wikidata, men läser inte filerna här när de
byggs: varje sidospår bygger från sin egen mapp.</p>
<h2>Verk</h2>
<div class="tw"><table><thead><tr><th>Verk</th><th>Typ</th><th>Utgivare</th></tr></thead><tbody>{rows_w}</tbody></table></div>
<h2>Utgivare</h2>
<div class="tw"><table><thead><tr><th>Utgivare</th><th>Webbplats</th></tr></thead><tbody>{rows_p}</tbody></table></div>
<h2 id="kalltyper">Typer av källor</h2>
<div class="tw"><table><thead><tr><th>Typ</th><th>Wikidata</th></tr></thead><tbody>{rows_t}</tbody></table></div>
<p class="ids">Data: <a href="index.jsonld">index.jsonld</a> · <a href="index.ttl">index.ttl</a></p>"""
    return page("Källor", '<a href="../../">Sidospår</a>', body, None)


# ---------------------------------------------------------------- main
def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


DATA = load()


def main():
    types = {t["id"]: t for t in DATA["types"]}
    out = HERE / "id"
    graph = type_nodes(DATA) + [publisher_node(p) for p in DATA["publishers"]]
    for w in DATA["works"]:
        node = work_node(w, types)
        graph.append(node)
        if expand(w["iri"]).startswith(ID):
            local = expand(w["iri"])[len(ID):]
            html, doc, ttl = work_page(w, node, types)
            write(out / local / "index.html", html)
            write(out / local / "index.jsonld", json.dumps(doc, ensure_ascii=False, indent=1))
            write(out / local / "index.ttl", ttl)
    full = {"@context": CONTEXT, "@graph": [{"@id": ID, "@type": "WebPage", "name": "Källor"}] + graph}
    write(out / "index.jsonld", json.dumps(full, ensure_ascii=False, indent=1))
    write(out / "index.ttl", turtle(full))
    write(out / "index.html", register_page(DATA, types))
    print(f"wrote kallor/id/: {len(DATA['types'])} types, {len(DATA['publishers'])} publishers, "
          f"{len(DATA['works'])} works")


if __name__ == "__main__":
    main()
