"""English page about the linked data behind the poster: linked-data.html.

Numbers on the page are computed from the data at build time.
Called from ld.main(); can also run on its own: python3 ld_page.py
"""
import json
from collections import Counter
from html import escape
from pathlib import Path

HERE = Path(__file__).parent

CSS = """
  body { margin: 0; background: #fbfaf7; color: #1d2733;
         font-family: Inter, "Helvetica Neue", Arial, sans-serif; line-height: 1.55; }
  main { max-width: 820px; margin: 0 auto; padding: 24px 16px 56px; }
  a { color: #2f6db5; }
  .crumbs { font-size: 0.9rem; }
  h1 { margin: 0.2em 0 0.3em; }
  h2 { margin-top: 1.8em; font-size: 1.25rem; }
  .lead { font-size: 1.08rem; color: #33404d; }
  code { font-size: 0.85em; background: #f1eee7; padding: 1px 4px; border-radius: 3px; overflow-wrap: anywhere; }
  pre { background: #f1eee7; padding: 12px 14px; border-radius: 4px; overflow-x: auto; font-size: 0.8rem; line-height: 1.45; }
  table { border-collapse: collapse; width: 100%; font-size: 0.9rem; }
  th, td { text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid #e3e0d8; }
  th { background: #f1eee7; }
  .tw { overflow-x: auto; }
  .chain { display: flex; flex-wrap: wrap; align-items: center; gap: 6px; margin: 14px 0; font-size: 0.88rem; }
  .chain span.box { background: #fff; border: 1px solid #d6d2c8; border-radius: 4px; padding: 6px 10px; }
  .chain span.box b { display: block; font-size: 0.75rem; color: #6b7682; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; }
  .chain span.arrow { color: #6b7682; font-size: 0.8rem; }
  .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin: 14px 0; }
  .stats div { background: #fff; border: 1px solid #e3e0d8; border-radius: 4px; padding: 10px 12px; }
  .stats strong { display: block; font-size: 1.5rem; }
  .stats span { color: #4a5764; font-size: 0.85rem; }
"""


def stats():
    items = json.loads((HERE / "data" / "items.json").read_text(encoding="utf-8"))
    claims = json.loads((HERE / "data" / "claims.json").read_text(encoding="utf-8"))
    wd = json.loads((HERE / "data" / "wikidata.json").read_text(encoding="utf-8"))
    defs = json.loads((HERE / "data" / "definitions.json").read_text(encoding="utf-8"))["definitions"]
    import ld
    rel = ld.relations(items)
    periods = {p["id"]: p for p in items["periods"]}
    n_items = sum(len(items[k]) for k in ("periods", "events", "milestones"))
    item_ids = [x["id"] for k in ("periods", "events", "milestones") for x in items[k]]
    linked = [i for i in item_ids if wd.get(i, {}).get("match") not in (None, "none") and wd.get(i, {}).get("qid")]
    same = sum(1 for d in defs if (d["start"], d["end"]) == (periods[d["period"]]["start"], periods[d["period"]]["end"]))
    moved = [d for d in defs if d["basis"].startswith("bekräftad")
             and (d["start"], d["end"]) != (periods[d["period"]]["start"], periods[d["period"]]["end"])]
    hosts = Counter(c["source_url"].split("/")[2].removeprefix("www.") for c in claims if c["source_url"])
    ra = json.loads((HERE / "data" / "riksarkivet.json").read_text(encoding="utf-8"))["checks"]
    return {
        "periods": len(items["periods"]), "events": len(items["events"]), "milestones": len(items["milestones"]),
        "items": n_items, "claims": len(claims), "verdicts": Counter(c["verdict"] for c in claims),
        "period_claims": sum(1 for c in claims if c["kind"] == "period"),
        "period_disputed": sum(1 for c in claims if c["kind"] == "period" and c["verdict"] == "omdiskuterad"),
        "defs": len(defs), "defs_same": same, "defs_diff": len(defs) - same,
        "defs_periods": len({d["period"] for d in defs}), "moved": [(periods[d["period"]]["label"], d) for d in moved],
        "wd_items": len(linked), "places": sum(1 for c in items["columns"] if wd.get("place:" + c, {}).get("qid")),
        "meets": sum(map(len, rel["meets"].values())), "within": sum(map(len, rel["within"].values())),
        "hosts": hosts.most_common(6),
        "ra": len(ra), "ra_verdicts": Counter(r["verdict"] for r in ra),
        "ra_records": Counter(x["register"] for r in ra for x in r["records"]),
    }


def example(ld_graph_path):
    """The Swedish Viking Age, its source definition and the review it came from, as they are in the data."""
    g = json.loads(ld_graph_path.read_text(encoding="utf-8"))["@graph"]
    by = {n.get("@id"): n for n in g}
    period = next(n for n in g if n.get("name") == "Vikingatid" and "wd:Q34" in n.get("crm:P7_took_place_at", []))
    pid = period["@id"]
    dfn = next(n for n in g if str(n.get("@id", "")).startswith(pid + "#def-"))
    review = by[dfn["prov:wasDerivedFrom"]]
    keep_p = {k: period[k] for k in ("@id", "@type", "name", "skos:inScheme", "crm:P4_has_time-span",
                                     "crm:P7_took_place_at", "skos:exactMatch", "time:intervalMeets",
                                     "time:intervalMetBy") if k in period}
    return json.dumps([keep_p, dfn, review], ensure_ascii=False, indent=1)


def yr(v):
    return f"{-v} BCE" if v < 0 else str(v)


def build(ld_graph_path, out_path):
    import sparql_page
    s = stats()
    v = s["verdicts"]
    periods = {p["id"]: p for p in json.loads((HERE / "data" / "items.json").read_text(encoding="utf-8"))["periods"]}
    moved = "".join(
        f"<li>{escape(lbl)} ({escape(', '.join(periods[d['period']]['columns']))}): the source confirmed "
        f"{yr(d['start'])}–{yr(d['end'])}, the poster now has "
        f"{yr(periods[d['period']]['start'])}–{yr(periods[d['period']]['end'])}.</li>"
        for lbl, d in s["moved"])
    hosts = ", ".join(f"{escape(h)} ({n})" for h, n in s["hosts"])
    html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Linked data – Nordens historia</title>
<link rel="alternate" type="application/ld+json" href="id/index.jsonld">
<link rel="alternate" type="text/turtle" href="id/index.ttl">
<style>{CSS}</style>
</head>
<body>
<main>
<p class="crumbs"><a href="./">Nordens historia (poster, in Swedish)</a> · <a href="kallor.html">Source check</a> · <a href="id/">Identifiers</a> · <a href="sparql.html">SPARQL</a></p>
<h1>The linked data behind the poster</h1>
<p class="lead">A poster is a picture. The facts behind it should be possible to look up, check and reuse.
This page explains how the timeline <a href="./">Nordens historia</a> is published as linked data,
what we learned on the way, and what comes next. The poster and the other pages are in Swedish; this page is in English.</p>

<div class="stats">
<div><strong>{s['items']}</strong><span>periods, events and milestones, each with its own identifier</span></div>
<div><strong>{s['claims']}</strong><span>checked statements, each with a source</span></div>
<div><strong>{s['defs']}</strong><span>period boundaries as stated by a source</span></div>
<div><strong>{s['wd_items']}</strong><span>items linked to Wikidata</span></div>
</div>

<h2>Background</h2>
<p>The poster is a Nordic version of <em>Timeline of World History</em> by
<a href="https://chartorigin.com">Chart Origin</a>, <a href="https://lnkd.in/p/ePw54Bpe">shared on LinkedIn</a>.
The idea and the form are theirs. The content is my own selection: {s['periods']} periods,
{s['events']} cross-border events and {s['milestones']} milestones in six columns, Iceland, Denmark, Norway, Sweden,
Finland and Sápmi.</p>
<p>I made it together with Claude. The first version was written from general knowledge, without sources.
Then every statement on the poster was checked against a reference source by AI agents with web search.
After that, every item got a persistent identifier and was described as linked data.</p>

<h2>What the data showed</h2>
<p>The source check gave {v['bekräftad']} confirmed and {v['omdiskuterad']} disputed statements, and no statement
that was simply wrong. The disputed ones are almost all period boundaries: {s['period_disputed']} of the
{s['period_claims']} checked boundaries do not match what the source says. The Swedish, Danish and Norwegian reference works
do not draw the lines in the same places. The Viking Age ends in 1066 in English convention, but around 1050 in
the Nordic reference works. Finnish prehistory has its own chronology, where the Iron Age continues through the Viking
and Crusade periods.</p>
<p>This is a typical linked data experience. When the data has to be explicit, the fine details come up early, at the
data level, instead of being handled later in software or hidden in footnotes. A period boundary is not a fact.
It is a choice made by someone, in a source.</p>
<p>So the model now says exactly that. The poster has its own boundaries, as one choice among others.
Each source's boundary is a separate definition: {s['defs']} definitions for {s['defs_periods']} of the
{s['periods']} periods. {s['defs_same']} of them agree with the poster and {s['defs_diff']} differ.
Three boundaries were confirmed by the source and then moved by me afterwards, to make the poster consistent.
The data shows this openly:</p>
<ul>{moved}</ul>

<h2>Identifiers</h2>
<p>Every item has an identifier under <code>https://kerfors.github.io/sidospar/nordens-historia/id/</code>.</p>
<ul>
<li><strong>Opaque numbers.</strong> <code>nh-p</code> period, <code>nh-e</code> event, <code>nh-m</code> milestone,
<code>nh-c</code> checked statement. The name is not part of the identifier, so a period can be renamed or re-dated
without breaking links. Numbers are never reused. They are stored in the data, not generated at build time.</li>
<li><strong>Thing and page.</strong> <code>…/id/nh-p0030</code> is the period. <code>…/id/nh-p0030/</code> is the page
about it, with embedded JSON-LD, and <code>index.jsonld</code> next to it. GitHub Pages answers the first with a 301
redirect to the second. Linked data practice says 303. The page states what it is about (<code>schema:mainEntity</code>).</li>
<li><strong>Years.</strong> The poster writes "500 f.Kr." (500 BCE). The data uses <code>xsd:gYear</code> with
astronomical numbering, where 1 BCE is year 0. So 500 BCE is <code>-0499</code>.</li>
</ul>

<h2>The model</h2>
<p>The model reuses existing vocabularies. Each one does the job it was made for.</p>
<div class="tw"><table>
<thead><tr><th>What</th><th>Vocabulary</th><th>Why</th></tr></thead>
<tbody>
<tr><td>Periods and events</td><td>CIDOC-CRM: <code>E4_Period</code>, <code>E5_Event</code>, time-span with
<code>P82a</code>/<code>P82b</code>, place with <code>P7_took_place_at</code></td>
<td>The cultural heritage standard for things that happen in time and space.</td></tr>
<tr><td>The poster's periodisation</td><td>SKOS: each period is a concept in the poster's own scheme</td>
<td>A periodisation is a classification of time. The scheme carries the poster's choice and its creator.</td></tr>
<tr><td>Sources' boundaries</td><td>SKOS in the style of <a href="https://perio.do">PeriodO</a>: one definition
per source, in a scheme per source, matched to the poster's period with <code>skos:exactMatch</code> or
<code>skos:closeMatch</code></td>
<td>PeriodO's insight: a period is a definition made by an authority, not a fact. Conflicting boundaries are data.</td></tr>
<tr><td>Checked statements</td><td>schema.org: <code>Claim</code> and <code>ClaimReview</code> with verdict,
evidence and source. Each claim has a kind (<code>dcterms:type</code>), a concept in a small SKOS scheme:
a period's name and boundaries, a detail in a period's description, an event, or a milestone</td>
<td>The vocabulary made for fact checking. Readable by search engines too.</td></tr>
<tr><td>Provenance</td><td>PROV-O: each review is generated by the source check (an activity by AI agents on my
behalf) and derived from its source. Each definition is derived from its review.</td>
<td>The chain from source to data is explicit and can be followed.</td></tr>
<tr><td>Relations between items</td><td>OWL-Time <code>intervalMeets</code> ({s['meets']}) and CIDOC-CRM
<code>P10_falls_within</code> ({s['within']})</td>
<td>Derived from the poster at build time: which period follows which in the same column, and which events happen
during which period.</td></tr>
<tr><td>Links out</td><td>Wikidata: <code>skos:exactMatch</code>, <code>skos:closeMatch</code>, and
<code>schema:about</code> for milestones</td>
<td>A milestone is an event, for example the founding of Uppsala University in 1477. Wikidata has the university,
not the founding, so the link says "about", not "same as".</td></tr>
</tbody></table></div>

<p>The chain for one period boundary:</p>
<div class="chain">
<span class="box"><b>Source</b>Statens historiska museer</span><span class="arrow">derived from →</span>
<span class="box"><b>Review</b>ClaimReview: "omdiskuterad"</span><span class="arrow">derived from →</span>
<span class="box"><b>Definition</b>Vikingatid 793–1050, per the museum</span><span class="arrow">exactMatch →</span>
<span class="box"><b>Period</b>Vikingatid, Sverige, on the poster</span><span class="arrow">exactMatch →</span>
<span class="box"><b>Wikidata</b>Viking Age Sweden</span>
</div>
<p>As it is in the data (JSON-LD, shortened to these three nodes):</p>
<pre>{escape(example(ld_graph_path))}</pre>

<h2>A second check, against the archives</h2>
<p>The first check used reference works: encyclopaedias and museum pages, sources that summarise other sources.
For {s['ra']} statements about Swedish persons and medieval documents, a second check went one step closer to the
sources, to two registers at Riksarkivet, the Swedish National Archives: Svenskt biografiskt lexikon (SBL) and
Diplomatarium Suecanum (SDHK), the register of medieval Swedish charters. They were reached through Riksarkivet's MCP
service (beta), which lets an AI agent search the registers directly. The check cites
{s['ra_records']['SBL']} SBL articles and {s['ra_records']['SDHK']} SDHK charters.</p>
<p>{s['ra_verdicts']['bekräftad']} statements were confirmed and {s['ra_verdicts']['ej verifierad']} could not be
checked, because the service gives SBL's summary and bibliography, not the full biography. No statement was
contradicted. But the registers add details the reference works leave out:</p>
<ul>
<li>The year 1164 for the archbishopric in Uppsala is not in the papal letter. SDHK says the year was supplied by the editors.</li>
<li>The peace of Nöteborg is dated 12 August 1323 by the editors, and SDHK marks one of the medieval copies as a forgery.</li>
<li>Erik of Pomerania was crowned in Kalmar on 17 June 1397 according to SBL. SDHK dates his coronation letter 13 July 1397.
Same year, different day.</li>
<li>Stockholm appears in two letters dated at Stockholm in 1252. That they are the first mentions is a conclusion
drawn by historians, not something the register says.</li>
</ul>
<p>It is the same lesson as with the period boundaries, one level down: a date can also be a choice, made by an
editor. In the data, the second check is its own <code>ClaimReview</code> next to the first, generated by its own PROV
activity that used (<code>prov:used</code>) the MCP service, and derived from the register entries it cites.
The first review is unchanged.</p>

<h2>Turtle and SPARQL</h2>
<p>The same graph is published in two serialisations. JSON-LD is the source: the build writes it, and it is embedded
in every page. Turtle is generated from the JSON-LD with <a href="https://github.com/RDFLib/rdflib">rdflib</a>, and the
build checks that the two give the same graph. The check is graph isomorphism, not text comparison, because the
time-spans and ratings are blank nodes. Every item page shows both formats side by side.</p>
<p>The <a href="sparql.html">SPARQL page</a> loads <code>id/index.ttl</code> into
<a href="https://github.com/oxigraph/oxigraph">Oxigraph</a>, a SPARQL engine compiled to WebAssembly, in the browser.
There is no server. The page has {len(sparql_page.QUERIES)} example queries, for example the disputed boundaries in
Finland, periods without a Wikidata link, and the sources' boundaries for the Viking Age. The build runs every example
query with rdflib and fails if one returns no rows.</p>

<h2>How it was made, and the limits</h2>
<ul>
<li>The source check split the {s['claims']} statements by country and gave each group to an AI agent with web search.
Each statement needed a source where the agent had actually seen the fact. Nordic reference works came first.
The most used sources: {hosts}.</li>
<li>The evidence texts are the agents' own summaries of the source, not quotes. Some Nationalencyklopedin pages are
behind a paywall and were checked only against the free introduction.</li>
<li>Each Wikidata link was found with Wikidata's own search service and then checked against wikidata.org.
{s['wd_items']} of {s['items']} items are linked, and all {s['places']} columns point to their place.
Most items without a link are my own descriptive period names, and the six Sápmi periods, where no matching Wikidata item was found.</li>
<li>Boundaries from disputed statements were read from the evidence text, for the cited source only. Approximate years
are marked, and the source's own wording is kept.</li>
</ul>

<h2>Data and code</h2>
<ul>
<li><a href="id/index.jsonld">id/index.jsonld</a> and <a href="id/index.ttl">id/index.ttl</a>: the whole dataset
as JSON-LD and as Turtle. Every item also has its own <code>index.jsonld</code> and <code>index.ttl</code>.</li>
<li><code>data/items.json</code>, <code>data/claims.json</code>, <code>data/definitions.json</code>,
<code>data/wikidata.json</code>: the source data. <code>data/riksarkivet.json</code>: the second check, against
Riksarkivet's registers. <code>check/</code>: the agents' unedited answers from the first check.</li>
<li><code>build.py</code> builds everything: the poster, the source check page, the identifier pages, the SPARQL page and this page.
The code is in the <a href="https://github.com/kerfors/sidospar">sidospar repository</a>.</li>
<li>License: <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.</li>
</ul>

<h2>Next steps</h2>
<ul>
<li><strong>SHACL shapes.</strong> The model described as shapes, and the build validated against them.</li>
<li><strong>More languages.</strong> Labels in Danish, Norwegian, Finnish, English and Northern Sami.</li>
<li><strong>A persistent base.</strong> A <a href="https://w3id.org">w3id.org</a> redirect, so the identifiers survive
a change of host and can answer with 303.</li>
</ul>
<p style="color:#6b7682; font-size:0.9rem">Kerstin Forsberg, October 2026.</p>
</main>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    print(f"wrote {out_path.name}")


if __name__ == "__main__":
    build(HERE / "id" / "index.jsonld", HERE / "linked-data.html")
