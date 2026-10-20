"""SPARQL page: sparql.html.

Loads id/index.ttl into Oxigraph (WebAssembly) in the browser. No server.
The build runs every example query with rdflib and fails if one returns no rows.
Called from ld.main(); can also run on its own: python3 sparql_page.py
"""
import json
from html import escape
from pathlib import Path

from rdflib import Graph

import ld

HERE = Path(__file__).parent
OXIGRAPH = "https://cdn.jsdelivr.net/npm/oxigraph@0.5.11/web.js"
SCHEME = f"<{ld.ID}#perioder>"

PREFIXES = "".join(f"PREFIX {p}: <{ns}>\n" for p, ns in ld.PREFIXES.items())

# (id, title, description, query body)
QUERIES = [
    ("finland", "Omdiskuterade periodgränser i Finland",
     "Uppgifter av typen periodens namn och gränser (dcterms:type) om perioder i Finlands kolumn, där källkontrollen "
     "gav utlåtandet omdiskuterad. Affischens gräns och, där den finns, källans gräns som härletts från granskningen.",
     f"""SELECT ?period ?namn ?affischStart ?affischSlut ?uppgift ?kalla ?kallStart ?kallSlut ?mot WHERE {{
  ?finland schema:name "Finland" .
  ?period skos:inScheme {SCHEME} ;
          schema:name ?namn ;
          crm:P7_took_place_at ?finland ;
          crm:P4_has_time-span [ crm:P82a_begin_of_the_begin ?affischStart ;
                                 crm:P82b_end_of_the_end ?affischSlut ] .
  ?uppgift dcterms:type <{ld.ID}#typ-period> ;
           schema:about ?period .
  ?granskning schema:itemReviewed ?uppgift ;
              schema:reviewRating/schema:alternateName "omdiskuterad" .
  OPTIONAL {{
    ?def prov:wasDerivedFrom ?granskning ;
         ?match ?period ;
         skos:inScheme/skos:prefLabel ?kalla ;
         crm:P4_has_time-span ?tid .
    FILTER (?match IN (skos:exactMatch, skos:closeMatch))
    OPTIONAL {{ ?tid crm:P82a_begin_of_the_begin ?kallStart }}
    OPTIONAL {{ ?tid crm:P82b_end_of_the_end ?kallSlut }}
  }}
  BIND (IF(?match = skos:exactMatch, "samma", "avviker") AS ?mot)
}}
ORDER BY ?affischStart
"""),
    ("utan-wikidata", "Perioder utan Wikidata-länk",
     "Affischens perioder som varken har skos:exactMatch eller skos:closeMatch till Wikidata.",
     f"""SELECT ?period ?namn (GROUP_CONCAT(?plats; separator=", ") AS ?platser) WHERE {{
  ?period skos:inScheme {SCHEME} ;
          schema:name ?namn ;
          crm:P7_took_place_at/schema:name ?plats .
  FILTER NOT EXISTS {{
    ?period skos:exactMatch|skos:closeMatch ?w .
    FILTER (STRSTARTS(STR(?w), STR(wd:)))
  }}
}}
GROUP BY ?period ?namn
ORDER BY ?period
"""),
    ("vikingatid", "Källornas gränser för vikingatiden",
     "Vikingatiden i varje kolumn: affischens gräns och varje källas egen definition, med källans formulering.",
     f"""SELECT ?period ?plats ?affischStart ?affischSlut ?kalla ?kallStart ?kallSlut ?formulering WHERE {{
  ?period skos:inScheme {SCHEME} ;
          schema:name "Vikingatid" ;
          crm:P7_took_place_at/schema:name ?plats ;
          crm:P4_has_time-span [ crm:P82a_begin_of_the_begin ?affischStart ;
                                 crm:P82b_end_of_the_end ?affischSlut ] .
  ?def skos:exactMatch|skos:closeMatch ?period ;
       skos:inScheme/skos:prefLabel ?kalla ;
       crm:P4_has_time-span ?tid .
  OPTIONAL {{ ?tid crm:P82a_begin_of_the_begin ?kallStart }}
  OPTIONAL {{ ?tid crm:P82b_end_of_the_end ?kallSlut }}
  OPTIONAL {{ ?def skos:scopeNote ?formulering }}
}}
ORDER BY ?plats ?kalla
"""),
    ("kalmarunionen", "Händelser och milstolpar under Kalmarunionen",
     "Relationen crm:P10_falls_within är härledd ur affischen vid bygget.",
     f"""SELECT ?post ?namn ?ar WHERE {{
  ?kalmar skos:inScheme {SCHEME} ;
          schema:name "Kalmarunionen" .
  ?post crm:P10_falls_within ?kalmar ;
        schema:name ?namn ;
        schema:startDate ?ar .
}}
ORDER BY ?ar
"""),
    ("norge", "Periodföljden i Norge",
     "Vilken period som följer på vilken i Norges kolumn (time:intervalMeets), med året då den ena slutar och nästa börjar.",
     """SELECT ?fore ?foreNamn ?efter ?efterNamn ?ar WHERE {
  ?norge schema:name "Norge" .
  ?fore time:intervalMeets ?efter ;
        schema:name ?foreNamn ;
        crm:P7_took_place_at ?norge ;
        crm:P4_has_time-span/crm:P82b_end_of_the_end ?ar .
  ?efter schema:name ?efterNamn ;
         crm:P7_took_place_at ?norge .
}
ORDER BY ?ar
"""),
    ("kallor", "Utlåtanden per källa",
     "Antal granskningar i den första kontrollen per webbplats, och hur många som blev bekräftade och omdiskuterade.",
     f"""SELECT ?kalla (COUNT(?granskning) AS ?granskningar)
       (SUM(IF(?utlatande = "bekräftad", 1, 0)) AS ?bekraftade)
       (SUM(IF(?utlatande = "omdiskuterad", 1, 0)) AS ?omdiskuterade) WHERE {{
  ?granskning a schema:ClaimReview ;
              prov:wasGeneratedBy <{ld.ID}#kontroll-{ld.CHECK_DATE}> ;
              schema:citation ?url ;
              schema:reviewRating/schema:alternateName ?utlatande .
  BIND (REPLACE(STRBEFORE(STRAFTER(STR(?url), "://"), "/"), "^www[.]", "") AS ?kalla)
}}
GROUP BY ?kalla
ORDER BY DESC(?granskningar) ?kalla
"""),
    ("typer", "Utlåtanden per typ av uppgift",
     "Hur utlåtandena i den första kontrollen fördelar sig på uppgiftens typ (dcterms:type). De omdiskuterade är till största delen periodgränser.",
     f"""SELECT ?typ ?typNamn ?utlatande (COUNT(?uppgift) AS ?antal) WHERE {{
  ?uppgift a schema:Claim ;
           dcterms:type ?typ .
  ?typ skos:prefLabel ?typNamn .
  ?granskning schema:itemReviewed ?uppgift ;
              prov:wasGeneratedBy <{ld.ID}#kontroll-{ld.CHECK_DATE}> ;
              schema:reviewRating/schema:alternateName ?utlatande .
}}
GROUP BY ?typ ?typNamn ?utlatande
ORDER BY ?typ ?utlatande
"""),
    ("riksarkivet", "Två kontroller av samma uppgift",
     "Uppgifter som också är kontrollerade mot Riksarkivets SBL och SDHK, med utlåtandet från båda kontrollerna.",
     f"""SELECT ?uppgift ?text ?forsta ?riksarkivet (GROUP_CONCAT(DISTINCT ?kallNamn; separator=", ") AS ?kallor) WHERE {{
  ?uppgift a schema:Claim ;
           schema:text ?text .
  ?g1 schema:itemReviewed ?uppgift ;
      prov:wasGeneratedBy <{ld.ID}#kontroll-{ld.CHECK_DATE}> ;
      schema:reviewRating/schema:alternateName ?forsta .
  ?g2 schema:itemReviewed ?uppgift ;
      prov:wasGeneratedBy/prov:used <{ld.ID}#riksarkivets-mcp> ;
      schema:reviewRating/schema:alternateName ?riksarkivet ;
      schema:citation/schema:isPartOf/schema:name ?kallNamn .
}}
GROUP BY ?uppgift ?text ?forsta ?riksarkivet
ORDER BY ?uppgift
"""),
    ("milstolpar", "Milstolpar och vad de handlar om i Wikidata",
     "En milstolpe är en händelse, till exempel grundandet av ett universitet. Wikidata har saken, inte händelsen, "
     "så länken är schema:about och inte skos:exactMatch.",
     """SELECT ?milstolpe ?namn ?ar ?wikidata WHERE {
  ?milstolpe a crm:E5_Event ;
             schema:about ?wikidata ;
             schema:name ?namn ;
             schema:startDate ?ar .
  FILTER (STRSTARTS(STR(?wikidata), STR(wd:)))
}
ORDER BY ?ar
"""),
]

CSS = """
  body { margin: 0; background: #fbfaf7; color: #1d2733;
         font-family: Inter, "Helvetica Neue", Arial, sans-serif; line-height: 1.5; }
  main { max-width: 1100px; margin: 0 auto; padding: 24px 16px 56px; }
  a { color: #2f6db5; }
  .crumbs { font-size: 0.9rem; }
  h1 { margin: 0.2em 0 0.3em; }
  h2 { font-size: 1.15rem; margin-top: 1.6em; }
  .lead { max-width: 760px; }
  code { font-size: 0.85em; background: #f1eee7; padding: 1px 4px; border-radius: 3px; overflow-wrap: anywhere; }
  .examples { display: flex; flex-wrap: wrap; gap: 6px; margin: 10px 0; }
  .examples button { font: inherit; font-size: 0.88rem; background: #fff; border: 1px solid #d6d2c8;
                     border-radius: 4px; padding: 5px 10px; cursor: pointer; color: #1d2733; }
  .examples button[aria-pressed="true"] { background: #1d2733; color: #fff; border-color: #1d2733; }
  #desc { color: #4a5764; font-size: 0.92rem; min-height: 1.5em; margin: 6px 0; }
  textarea { width: 100%; box-sizing: border-box; min-height: 18em; font-family: ui-monospace, Menlo, Consolas, monospace;
             font-size: 0.8rem; line-height: 1.45; background: #f1eee7; border: 1px solid #d6d2c8; border-radius: 4px;
             padding: 10px 12px; color: #1d2733; resize: vertical; tab-size: 2; }
  .bar { display: flex; flex-wrap: wrap; align-items: center; gap: 12px; margin: 8px 0 14px; }
  .bar button { font: inherit; font-weight: 600; background: #2f6db5; color: #fff; border: 0; border-radius: 4px;
                padding: 7px 18px; cursor: pointer; }
  .bar button:disabled { background: #9aa7b4; cursor: default; }
  #status { color: #4a5764; font-size: 0.9rem; }
  #status.err { color: #b3261e; white-space: pre-wrap; font-family: ui-monospace, Menlo, Consolas, monospace; font-size: 0.8rem; }
  .tw { overflow-x: auto; }
  table { border-collapse: collapse; width: 100%; font-size: 0.86rem; }
  th, td { text-align: left; vertical-align: top; padding: 5px 8px; border-bottom: 1px solid #e3e0d8; }
  th { background: #f1eee7; font-family: ui-monospace, Menlo, Consolas, monospace; font-weight: 600; font-size: 0.8rem; white-space: nowrap; }
  td .lang, td .dt { color: #6b7682; font-size: 0.75rem; }
  ul.model li { margin-bottom: 0.3em; }
"""

INTRO = f"""<h1>Fråga datan med SPARQL</h1>
<p class="lead">Den här sidan laddar hela datamängden bakom <a href="./">affischen</a>,
<a href="id/index.ttl">id/index.ttl</a>, i <a href="https://github.com/oxigraph/oxigraph">Oxigraph</a>,
en SPARQL-motor som körs som WebAssembly direkt i webbläsaren. Det finns ingen server: frågorna körs
på din dator. Välj en exempelfråga, ändra i den eller skriv en egen, och tryck <strong>Kör</strong>
(eller Ctrl+Enter). Modellen beskrivs på engelska i
<a href="linked-data.html">The linked data behind the poster</a>.</p>
"""

MODEL = f"""<h2>Modellen i korthet</h2>
<ul class="model">
<li><strong>Affischens perioder</strong>: <code>skos:inScheme &lt;{ld.ID}#perioder&gt;</code>, typ
<code>crm:E4_Period</code>, namn i <code>schema:name</code>, plats i <code>crm:P7_took_place_at</code>
(Wikidata-id med <code>schema:name</code> "Finland" osv.).</li>
<li><strong>Tid</strong>: <code>crm:P4_has_time-span</code> med <code>crm:P82a_begin_of_the_begin</code> och
<code>crm:P82b_end_of_the_end</code>, som <code>xsd:gYear</code> med astronomisk numrering (500 f.Kr. är
<code>-0499</code>). Resultattabellen visar årtalen som på affischen.</li>
<li><strong>Händelser och milstolpar</strong>: <code>crm:E5_Event</code> med <code>schema:startDate</code>,
och <code>crm:P10_falls_within</code> till perioden.</li>
<li><strong>Källornas gränser</strong>: egna definitioner i ett schema per källa, kopplade till affischens period med
<code>skos:exactMatch</code> (samma gräns) eller <code>skos:closeMatch</code> (avviker), och
<code>prov:wasDerivedFrom</code> till granskningen.</li>
<li><strong>Kontrollerade uppgifter</strong>: <code>schema:Claim</code> med <code>schema:about</code> till posten
och typen i <code>dcterms:type</code> (begrepp i <code>&lt;{ld.ID}#uppgiftstyper&gt;</code>);
granskningen är en <code>schema:ClaimReview</code> med <code>schema:itemReviewed</code>, utlåtandet i
<code>schema:reviewRating/schema:alternateName</code> och källan i <code>schema:citation</code>.</li>
<li><strong>Två kontroller</strong>: granskningarna skiljs åt av <code>prov:wasGeneratedBy</code>. Den första kontrollen
är <code>&lt;{ld.ID}#kontroll-{ld.CHECK_DATE}&gt;</code>; den andra, mot Riksarkivets SBL och SDHK, använde
(<code>prov:used</code>) <code>&lt;{ld.ID}#riksarkivets-mcp&gt;</code>.</li>
</ul>
"""

SCRIPT = """<script type="module">
import init, { Store } from "__OXIGRAPH__";
const Q = JSON.parse(document.getElementById("queries").textContent);
const ID = "__ID__";
const PREFIXES = __PREFIXES__;
const $ = (id) => document.getElementById(id);
const status = (text, err) => { $("status").textContent = text; $("status").className = err ? "err" : ""; };
const fmt = new Intl.NumberFormat("sv-SE");

function pick(id) {
  const q = Q.find((x) => x.id === id) || Q[0];
  $("query").value = q.query;
  $("desc").textContent = q.description;
  $("results").textContent = "";
  status(store ? "Tryck Kör för att köra frågan." : "");
  document.querySelectorAll(".examples button").forEach((b) => b.setAttribute("aria-pressed", b.dataset.id === q.id));
  history.replaceState(null, "", "#" + q.id);
}

function year(lex) {
  const n = parseInt(lex, 10);
  return n <= 0 ? (1 - n) + " f.Kr." : String(n);
}

function link(iri) {
  if (iri.startsWith(ID)) {
    const [base, frag] = iri.slice(ID.length).split("#");
    if (!base) return "id/" + (frag ? "#" + frag : "");
    return "id/" + base + "/" + (frag ? "#" + frag : "");
  }
  const m = iri.match(/^http:\\/\\/www\\.wikidata\\.org\\/entity\\/(Q\\d+)$/);
  return m ? "https://www.wikidata.org/wiki/" + m[1] : iri;
}

function short(iri) {
  for (const [p, ns] of PREFIXES) {
    if (iri.startsWith(ns)) {
      const local = iri.slice(ns.length);
      if (/^[A-Za-z0-9_][A-Za-z0-9_.-]*$/.test(local)) return p + ":" + local;
    }
  }
  return "<" + iri + ">";
}

function cell(t) {
  const td = document.createElement("td");
  if (!t) return td;
  if (t.termType === "NamedNode") {
    const a = document.createElement("a");
    a.href = link(t.value);
    a.textContent = short(t.value);
    a.title = t.value;
    td.appendChild(a);
  } else if (t.termType === "Literal") {
    const dt = t.datatype ? t.datatype.value : "";
    if (dt.endsWith("#gYear")) {
      td.textContent = year(t.value);
      td.title = t.value + "^^xsd:gYear";
    } else {
      td.textContent = t.value;
      if (t.language) {
        const s = document.createElement("span");
        s.className = "lang";
        s.textContent = " @" + t.language;
        td.appendChild(s);
      }
    }
  } else {
    td.textContent = "_:" + t.value;
  }
  return td;
}

function table(heads, rows) {
  const tbl = document.createElement("table");
  const tr = document.createElement("tr");
  for (const h of heads) {
    const th = document.createElement("th");
    th.textContent = h;
    tr.appendChild(th);
  }
  tbl.createTHead().appendChild(tr);
  const tb = tbl.createTBody();
  for (const r of rows) {
    const row = document.createElement("tr");
    for (const t of r) row.appendChild(cell(t));
    tb.appendChild(row);
  }
  return tbl;
}

let store;
function run() {
  const out = $("results");
  out.textContent = "";
  const t0 = performance.now();
  let res;
  try {
    res = store.query($("query").value);
  } catch (e) {
    status(String(e), true);
    return;
  }
  const ms = Math.round(performance.now() - t0);
  if (typeof res === "boolean") {
    status("Svar: " + (res ? "ja (true)" : "nej (false)") + " · " + ms + " ms");
    return;
  }
  if (typeof res === "string") {
    const pre = document.createElement("pre");
    pre.textContent = res;
    out.appendChild(pre);
    status(ms + " ms");
    return;
  }
  if (res.length && res[0].subject) {
    out.appendChild(table(["subjekt", "predikat", "objekt"], res.map((q) => [q.subject, q.predicate, q.object])));
    status(fmt.format(res.length) + " tripplar · " + ms + " ms");
    return;
  }
  const heads = [];
  for (const r of res) for (const k of r.keys()) if (!heads.includes(k)) heads.push(k);
  out.appendChild(table(heads.map((h) => "?" + h), res.map((r) => heads.map((h) => r.get(h)))));
  status(fmt.format(res.length) + " rader · " + ms + " ms");
}

for (const q of Q) {
  const b = document.createElement("button");
  b.type = "button";
  b.dataset.id = q.id;
  b.textContent = q.title;
  b.addEventListener("click", () => pick(q.id));
  $("examples").appendChild(b);
}
pick(location.hash.slice(1));
$("run").addEventListener("click", run);
$("query").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && (e.ctrlKey || e.metaKey) && store) { e.preventDefault(); run(); }
});

try {
  status("Laddar Oxigraph och datan …");
  const [, ttl] = await Promise.all([init(), fetch("id/index.ttl").then((r) => {
    if (!r.ok) throw new Error("id/index.ttl: HTTP " + r.status);
    return r.text();
  })]);
  store = new Store();
  store.load(ttl, { format: "text/turtle", base_iri: ID + "index.ttl" });
  $("loaded").textContent = fmt.format(store.size) + " tripplar laddade från id/index.ttl.";
  $("run").disabled = false;
  status("Tryck Kör för att köra frågan.");
} catch (e) {
  status("Kunde inte ladda: " + e, true);
}
</script>
"""


def check(ttl_path):
    """Every example query must return at least one row against the published Turtle."""
    g = Graph().parse(ttl_path, format="turtle")
    counts = {}
    for qid, _, _, body in QUERIES:
        n = len(list(g.query(PREFIXES + body)))
        if n == 0:
            raise ValueError(f"example query '{qid}' returns no rows")
        counts[qid] = n
    return len(g), counts


def build(ttl_path, out_path):
    triples, counts = check(ttl_path)
    data = [{"id": qid, "title": title, "description": desc, "query": PREFIXES + "\n" + body}
            for qid, title, desc, body in QUERIES]
    script = (SCRIPT.replace("__OXIGRAPH__", OXIGRAPH).replace("__ID__", ld.ID)
              .replace("__PREFIXES__", json.dumps(list(ld.PREFIXES.items()))))
    queries = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    html = f"""<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SPARQL – Nordens historia</title>
<link rel="alternate" type="text/turtle" href="id/index.ttl">
<style>{CSS}</style>
</head>
<body>
<main>
<p class="crumbs"><a href="./">Nordens historia</a> · <a href="id/">Identifierare</a> · <a href="kallor.html">Källäget</a> · <a href="linked-data.html">Linked data (English)</a></p>
{INTRO}
<h2>Exempelfrågor</h2>
<div class="examples" id="examples"></div>
<p id="desc"></p>
<textarea id="query" spellcheck="false" aria-label="SPARQL-fråga"></textarea>
<div class="bar"><button id="run" type="button" disabled>Kör</button><span id="status"></span></div>
<div class="tw" id="results"></div>
<p id="loaded" style="color:#6b7682; font-size:0.85rem"></p>
{MODEL}
</main>
<script type="application/json" id="queries">{queries}</script>
{script}</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path.name}: {len(QUERIES)} example queries against {triples} triples, rows {counts}")


if __name__ == "__main__":
    build(HERE / "id" / "index.ttl", HERE / "sparql.html")
