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
    hosts = Counter(ld.source_name(u) for c in claims if c["source_url"] for u in [c["source_url"]] + c["also_sources"])
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
        "sources": len({u for c in claims for u in [c["source_url"]] + c["also_sources"]}
                       | {x["url"] for r in ra for x in r["records"]}),
    }


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
<p class="crumbs"><a href="./">Nordens historia (poster, in Swedish)</a> · <a href="kallor.html">Source check</a> · <a href="kallkatalog.html">Sources</a> · <a href="id/">Identifiers</a> · <a href="sparql.html">SPARQL</a></p>
<h1>The linked data behind the poster</h1>
<p class="lead">A poster is a picture. The facts behind it should be possible to look up, check and reuse.
This page explains how the timeline <a href="./">Nordens historia</a> is published as linked data,
what we learned on the way, and what comes next. The poster and the other pages are in Swedish; this page is in English.</p>

<div class="stats">
<div><strong>{s['items']}</strong><span>periods, events and milestones, each with its own identifier</span></div>
<div><strong>{s['claims']}</strong><span>checked statements, each with a source</span></div>
<div><strong>{s['defs']}</strong><span>period boundaries as stated by a source</span></div>
<div><strong>{s['sources']}</strong><span><a href="kallkatalog.html">sources</a>, each with what it is and its work or publisher</span></div>
<div><strong>{s['wd_items']}</strong><span>items linked to Wikidata</span></div>
</div>

<h2>Background</h2>
<p>The poster is a Nordic version of <em>Timeline of World History</em> by
<a href="https://chartorigin.com">Chart Origin</a>, <a href="https://lnkd.in/p/ePw54Bpe">shared on LinkedIn</a>.
The idea and the form are theirs. The content is my own selection: {s['periods']} periods,
{s['events']} cross-border events and {s['milestones']} milestones in five columns, Iceland, Denmark, Norway, Sweden
and Finland.</p>
<p>I made it together with Claude. The first version was written from general knowledge, without sources.
Then every statement was checked against a reference source by AI agents with web search, and described as linked data.</p>

<h2>What the data showed</h2>
<p>The source check gave {v['bekräftad']} confirmed and {v['omdiskuterad']} disputed statements, and no statement
that was simply wrong. The disputed ones are almost all period boundaries: {s['period_disputed']} of the
{s['period_claims']} checked boundaries do not match what the source says. The Swedish, Danish and Norwegian reference works
do not draw the lines in the same places. The Viking Age ends in 1066 in English convention, but around 1050 in
the Nordic reference works.</p>
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
<p>Every item has a persistent identifier under <code>https://w3id.org/people/kerfors/sidospar/nordens-historia/id/</code>,
an opaque number such as <code>nh-p0030</code>, so a period can be renamed or re-dated without breaking links.
w3id.org answers with a 303 to the page, or to Turtle or JSON-LD. More on the <a href="id/">identifier page</a>.
The sources, their works and their publishers use Wikidata's identifiers. The few that are missing there, such as
the register SDHK, have one under <a href="https://w3id.org/people/kerfors/sidospar/kallor/id/"><code>https://w3id.org/people/kerfors/sidospar/kallor/id/</code></a>.</p>

<h2>The model</h2>
<p>The model reuses existing vocabularies. Each one does the job it was made for.</p>
<div class="tw"><table>
<thead><tr><th>What</th><th>Vocabulary</th><th>Why</th></tr></thead>
<tbody>
<tr><td>Periods and events</td><td>CIDOC-CRM: <code>E4_Period</code>, <code>E5_Event</code>, time-span with
<code>P82a</code>/<code>P82b</code>, place with <code>P7_took_place_at</code></td>
<td>The cultural heritage standard for things in time and space.</td></tr>
<tr><td>The poster's periodisation</td><td>SKOS: each period is a concept in the poster's own scheme</td>
<td>A periodisation is a classification of time.</td></tr>
<tr><td>Sources' boundaries</td><td>SKOS in the style of <a href="https://perio.do">PeriodO</a>: one definition
per source, matched to the poster's period with <code>skos:exactMatch</code> or <code>skos:closeMatch</code></td>
<td>A period is a definition made by an authority, not a fact.</td></tr>
<tr><td>Checked statements</td><td>schema.org: <code>Claim</code> and <code>ClaimReview</code> with verdict,
evidence and source</td>
<td>The vocabulary made for fact checking.</td></tr>
<tr><td>Sources</td><td>schema.org: each cited source is an article in a reference work, an article in a periodical,
a register entry or a web page, <code>isPartOf</code> a work or with a <code>publisher</code>; works, publishers and
article numbers use Wikidata's identifiers and properties</td>
<td>A source is an article in a reference work by a publisher, not just a web address. The article number is the
one Wikidata uses, so the same article can be found from Wikidata.</td></tr>
<tr><td>Provenance</td><td>PROV-O: each review is generated by the source check and derived from its source</td>
<td>The chain from source to data can be followed.</td></tr>
<tr><td>Relations between items</td><td>OWL-Time <code>intervalMeets</code> ({s['meets']}) and CIDOC-CRM
<code>P10_falls_within</code> ({s['within']})</td>
<td>Derived from the poster: which period follows which, and what happens during a period.</td></tr>
<tr><td>Links out</td><td>Wikidata: <code>skos:exactMatch</code>, <code>skos:closeMatch</code>, and
<code>schema:about</code> for milestones</td>
<td>Wikidata has Uppsala University, not its founding in 1477, so a milestone links "about", not "same as".</td></tr>
</tbody></table></div>

<p>The chain for one period boundary:</p>
<div class="chain">
<span class="box"><b>Source</b>"Tidsåldrar", a page by Historiska museet</span><span class="arrow">derived from →</span>
<span class="box"><b>Review</b>ClaimReview: "omdiskuterad"</span><span class="arrow">derived from →</span>
<span class="box"><b>Definition</b>Vikingatid 793–1050, per the museum</span><span class="arrow">exactMatch →</span>
<span class="box"><b>Period</b>Vikingatid, Sverige, on the poster</span><span class="arrow">exactMatch →</span>
<span class="box"><b>Wikidata</b>Viking Age Sweden</span>
</div>

<h2>A second check, against the archives</h2>
<p>For {s['ra']} statements about Swedish persons and medieval documents, a second check went one step closer to the
sources: the biographical dictionary Svenskt biografiskt lexikon (SBL) and the register <a href="https://w3id.org/people/kerfors/sidospar/kallor/id/sdhk">Svenskt Diplomatariums huvudkartotek (SDHK)</a> at Riksarkivet, the Swedish National Archives, searched
through Riksarkivet's MCP service (beta). {s['ra_verdicts']['bekräftad']} were confirmed, {s['ra_verdicts']['ej verifierad']}
could not be checked, and none was contradicted. But SBL and SDHK add details the reference works leave out. The year
1164 for the archbishopric in Uppsala, for example, is not in the papal letter; the editors supplied it. A date can
also be a choice. All {s['ra']} are listed, in Swedish, on the <a href="kallor.html#riksarkivet">source check page</a>.</p>

<h2>What the sources showed</h2>
<p>At first a source was mostly a web address with a title. Now each of the {s['sources']} sources says what it is, and which
work it is part of or who publishes it, with Wikidata's identifiers. An article also has its number in the work, with
the property Wikidata uses for that work, so the same article can be found from Wikidata. The same thing happened as
with the periods: the questions came early. All {s['sources']} are listed, in Swedish, on the
<a href="kallkatalog.html">sources page</a>, by work and publisher.</p>
<ul>
<li>Svenskt biografiskt lexikon is a reference work, not a register. SDHK is a register, and Diplomatarium Suecanum is
the printed edition, not the register.</li>
<li>Lex is three things in Wikidata: the printed Den Store Danske, the portal lex.dk, and the reference work Lex. The
addresses cited here are the reference work.</li>
<li>Who publishes a web page? Here, the Wikidata item whose official website it is. historiska.se is Historiska museet's
site; Statens historiska museer, the agency it is part of, has its own.</li>
<li>Some things are not in Wikidata. SDHK has no item, so it got <a href="https://w3id.org/people/kerfors/sidospar/kallor/id/sdhk">its own identifier</a>. Nationalencyklopedin has no
publisher there, and the site does not name one, so the data leaves it out.</li>
</ul>

<h2>Turtle and SPARQL</h2>
<p>The whole dataset is published as JSON-LD and as Turtle, and the build checks that the two give the same graph.
The <a href="sparql.html">SPARQL page</a> runs queries in the browser, with {len(sparql_page.QUERIES)} examples.</p>

<h2>How it was made, and the limits</h2>
<ul>
<li>The {s['claims']} statements were split by country and checked by AI agents with web search. Each statement needed
a source where the agent had actually seen the fact, with Nordic reference works first. The most used sources, by number of citations: {hosts}.</li>
<li>The evidence texts are the agents' own summaries, not quotes. Some Nationalencyklopedin pages were checked only
against the free introduction.</li>
<li>{s['wd_items']} of {s['items']} items link to Wikidata. Most of the others are my own descriptive period names.</li>
</ul>

<h2>Data and code</h2>
<p>The dataset: <a href="id/index.jsonld">id/index.jsonld</a> and <a href="id/index.ttl">id/index.ttl</a>.
The source data and the code are in the <a href="https://github.com/kerfors/sidospar">sidospar repository</a>.
License: <a href="https://creativecommons.org/licenses/by/4.0/">CC BY 4.0</a>.</p>

<h2>Next steps</h2>
<ul>
<li><strong>SHACL shapes.</strong> The model described as shapes, and the build validated against them.</li>
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
