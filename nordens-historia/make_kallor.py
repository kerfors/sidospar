"""Generate kallor.html from check/kallkontroll.json.

Run: python3 make_kallor.py  ->  writes kallor.html next to this script.
"""
import json
from html import escape
from pathlib import Path
from collections import Counter

HERE = Path(__file__).parent
CLAIMS = json.loads((HERE / "check" / "kallkontroll.json").read_text(encoding="utf-8"))

GROUP_ORDER = ["Island", "Danmark", "Norge", "Sverige", "Finland", "Sápmi", "Gemensamt", "Milstolpar"]
GROUP_TITLE = {"Gemensamt": "Gemensamma block och händelser"}

# What was changed on the poster after the check (id -> text)
ACTIONS = {
    "IS01": "Start 870; 874 anges som traditionellt år.",
    "IS05": "Ändrat till 999/1000.",
    "IS07": "Behållet; tillägg om gemensam kung med Danmark från 1380.",
    "IS09": "Behållet; 1814 som gräns följer SNL.",
    "IS10": "Ändrat till ”sammanträder åter 1845” (beslut 1843).",
    "DA01": "Behållet; affischens axel börjar 10 000 f.Kr.",
    "DA06": "Slut ändrat till 1050.",
    "DA09": "Ändrat: England 1016, Danmark c. 1018.",
    "DA10": "Start ändrat till 1050.",
    "DA15": "Delat i 1241–1340 och 1340–1380 efter lex.dk.",
    "DA18": "Behållet; titeln ändrad till ”Enväldets sista decennier”.",
    "DA20": "Delat i 1849–1914 och 1914–1945 efter lex.dk.",
    "DA22": "Tillägg: Holsten och Lauenburg.",
    "DA24": "Delat i 1945–1973 och 1973–.",
    "NO01": "Start ändrat till 10 000 f.Kr.",
    "NO03": "Behållet 1700; SNL anger 1800, gemensamt bronsåldersblock följer 1700.",
    "NO06": "Ändrat till ”slutet av 800-talet”.",
    "NO18": "Behållet; tillägg ”utsedd 1343, ensam kung från 1355”.",
    "SV06": "Slut ändrat till 1050.",
    "SV09": "Start ändrat till 1050.",
    "SV12": "Behållet; tillägg ”folkungaätten regerar 1250–1363”.",
    "SV15": "Titeln ändrad till ”Nytt statsskick: 1809 års RF”.",
    "SV16": "Delat i 1905–1921 och 1921–1945.",
    "FI01": "Ändrat till 8600–5000 f.Kr.",
    "FI02": "Beskrivningen ändrad till ”mesolitisk jägarkultur efter isavsmältningen”.",
    "FI03": "Start ändrat till 5000 f.Kr.",
    "FI04": "Ändrat till båtyxe- och Kiukaiskultur 2800–1600 f.Kr. med not om överlappet.",
    "FI05": "Start ändrat till 1600 f.Kr.",
    "FI08": "Titeln ändrad till ”Äldre järnålder”; not om att järnåldern fortsätter.",
    "FI11": "Slut ändrat till 1300; not om väst/öst; nytt block 1300–1319.",
    "FI24": "Start ändrat till 1944 (”Andra republiken”).",
    "SÁ01": "Slut ändrat till 500 f.Kr.",
    "SÁ04": "Ändrat till 500 f.Kr.–1050; ”ursamiska”.",
    "SÁ05": "Ändrat till ”ursamiska”.",
    "SÁ07": "Start ändrat till 1050.",
    "SÁ09": "Ändrat till ”flera riken”.",
    "SÁ10": "Titeln ändrad till ”Skatt, handel och mission”; nybyggen i nästa block.",
    "SÁ15": "Ändrat till ”Finland 1996 (delegation från 1973)”.",
    "GE12": "Behållet; 793 knyts till Lindisfarne.",
    "GE14": "Behållet; delningen 1355 anges i Håkon VI-blocket.",
    "GE16": "Behållet som affischens egen sammanfattning.",
    "GE26": "Ändrat till 1536/37.",
    "GE30": "Titeln ändrad till ”Äldre Vasatiden”.",
    "GE32": "Ändrat till ”reformationen inleds 1527”.",
    "GE38": "Start ändrat till 1719.",
    "MI13": "Etikett ”(patent)”.",
    "MI20": "Etikett ”första maskinen”.",
    "MI21": "Etikett ”(patentansökan)”.",
}

VERDICT_CLASS = {"bekräftad": "ok", "omdiskuterad": "disp", "avvikande": "bad", "ej verifierad": "unk"}


def strip_ctx(claim):
    # "[Danmark, inom 'X'] text" -> ("Danmark, inom 'X'", "text")
    ctx, _, text = claim.partition("] ")
    return ctx.lstrip("["), text


def row(c):
    ctx, text = strip_ctx(c["claim"])
    url = c["url"]
    src = escape(c["source_title"] or url)
    link = f'<a href="{escape(url)}">{src}</a>' if url else src
    action = ACTIONS.get(c["id"], "")
    v = c["verdict"]
    return (f'<tr><td class="id">{escape(c["id"])}</td>'
            f'<td><span class="ctx">{escape(ctx)}</span><br>{escape(text)}</td>'
            f'<td><span class="v {VERDICT_CLASS[v]}">{escape(v)}</span></td>'
            f'<td>{link}<div class="ev">{escape(c["evidence"])}</div></td>'
            f'<td>{escape(action)}</td></tr>')


def main():
    counts = Counter(c["verdict"] for c in CLAIMS)
    sections = []
    for g in GROUP_ORDER:
        rows = [row(c) for c in CLAIMS if c["group"] == g]
        sections.append(
            f'<h2>{escape(GROUP_TITLE.get(g, g))}</h2>\n<div class="tw"><table>'
            f'<thead><tr><th>Id</th><th>Uppgift (som den stod vid kontrollen)</th><th>Utlåtande</th>'
            f'<th>Källa och belägg</th><th>Åtgärd på affischen</th></tr></thead><tbody>\n'
            + "\n".join(rows) + "\n</tbody></table></div>")
    summary = ", ".join(f"{counts[k]} {k}" for k in ("bekräftad", "omdiskuterad", "avvikande", "ej verifierad") if counts[k])
    page = PAGE.format(n=len(CLAIMS), summary=summary, sections="\n".join(sections))
    (HERE / "kallor.html").write_text(page, encoding="utf-8")
    print("wrote kallor.html", summary)


PAGE = """<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nordens historia – källäget</title>
<style>
  body {{ margin: 0; background: #fbfaf7; color: #1d2733;
         font-family: Inter, "Helvetica Neue", Arial, sans-serif; line-height: 1.5; }}
  main {{ max-width: 1120px; margin: 0 auto; padding: 24px 16px 48px; }}
  .intro {{ max-width: 760px; }}
  a {{ color: #2f6db5; }}
  h2 {{ font-size: 1.15rem; margin-top: 2em; }}
  .tw {{ overflow-x: auto; }}
  table {{ border-collapse: collapse; width: 100%; min-width: 760px; font-size: 0.85rem; }}
  th, td {{ text-align: left; vertical-align: top; padding: 6px 8px; border-bottom: 1px solid #e3e0d8; }}
  th {{ background: #f1eee7; font-weight: 700; }}
  td.id {{ color: #6b7682; white-space: nowrap; }}
  .ctx {{ color: #6b7682; font-size: 0.78rem; }}
  .ev {{ color: #4a5764; margin-top: 2px; }}
  .v {{ display: inline-block; padding: 1px 6px; border-radius: 3px; font-size: 0.78rem; white-space: nowrap; }}
  .v.ok {{ background: #d8efdc; }} .v.disp {{ background: #f7e3b5; }}
  .v.bad {{ background: #f6c9c4; }} .v.unk {{ background: #e3e3e3; }}
  .back {{ font-size: 0.9rem; }}
</style>
</head>
<body>
<main>
<p class="back"><a href="./">← Nordens historia – tidslinjen</a></p>
<h1>Nordens historia – källäget</h1>
<div class="intro">
<p>Affischens innehåll skrevs först ur Claudes allmänna kunskap, utan källor. Därefter delades alla {n}
uppgifter (perioder, detaljer, händelser och milstolpar) upp per land, och AI-agenter med webbsökning
fick leta en källa per uppgift. Kravet var att uppgiften faktiskt skulle synas på en hämtad sida.
Nordiska uppslagsverk hade företräde: Store norske leksikon, lex.dk, Uppslagsverket Finland och
Nationalencyklopedin, samt myndigheter, museer och sametingen.</p>
<p>Resultat: {summary}. Ingen uppgift visade sig direkt fel. De omdiskuterade är nästan alla
periodgränser, där uppslagsverken i olika länder drar gränserna olika. Kolumnen ”Åtgärd” visar vad
som ändrades på affischen efter kontrollen.</p>
<p>Begränsningar: beläggen är agenternas egna sammanfattningar av källsidan, inte citat. Några sidor i
NE ligger bakom betalvägg och kontrollerades bara mot den fria ingressen. Ett fåtal uppgifter vilar på
svagare källor, till exempel Britannica eller en tidskriftsartikel, vilket syns i källkolumnen.
Kontrollen gjordes 18 oktober 2026.</p>
<p>Hela kontrollen finns också maskinläsbar: <a href="check/kallkontroll.json">kallkontroll.json</a>
(en post per uppgift med id, uppgift, utlåtande, källa, URL och belägg).</p>
</div>
{sections}
</main>
</body>
</html>
"""

if __name__ == "__main__":
    main()
