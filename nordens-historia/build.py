"""Generate index.html: a Nordic timeline poster in the style of
Chart Origin's "Timeline of World History".

Data lives in COLUMNS, BLOCKS, BARS and MILESTONES below.
Run: python3 build.py  ->  writes index.html next to this script.
"""
from pathlib import Path
from html import escape

# ---------------------------------------------------------------- layout
COLUMNS = ["Island", "Danmark", "Norge", "Sverige", "Finland", "Sápmi"]
X0 = 120          # left edge of first column (axis to the left)
COL_W = 158
GAP = 2
TOP = 480         # y of year -10000
WIDTH = X0 + len(COLUMNS) * COL_W + 30

# Piecewise linear, non-uniform time scale (year -> offset from TOP)
ANCHORS = [
    (-10000, 0), (-4000, 170), (-1700, 290), (-500, 450), (400, 650),
    (793, 770), (1050, 990), (1520, 1520), (1809, 2110), (2026, 2700),
]
BOTTOM = TOP + ANCHORS[-1][1]
HEIGHT = BOTTOM + 190


def y(year):
    for (y0, p0), (y1, p1) in zip(ANCHORS, ANCHORS[1:]):
        if y0 <= year <= y1:
            return TOP + p0 + (year - y0) * (p1 - p0) / (y1 - y0)
    raise ValueError(f"year out of range: {year}")


def col_x(c):
    return X0 + c * COL_W


# ---------------------------------------------------------------- palette
P = {
    "stone": "#c9b79c", "stone2": "#d9c9ad", "bronze": "#e6a85a",
    "iron1": "#b7a7d9", "iron2": "#a3c4e8", "iron3": "#9fd3c7",
    "iron4": "#a8cf9a", "viking": "#5f9ea0", "red": "#f07a6e",
    "dk": "#f29b88", "no": "#7fb3e6", "se": "#f6d06f", "fi": "#9ec9f0",
    "is": "#8fd0d8", "union": "#e8606a", "dkno": "#f2a65a",
    "sefi": "#f9dc8a", "seno": "#c7b3e6", "modern": "#86c99a",
    "war": "#9aa7b4", "sapmi": "#c8a2c8", "sapmi2": "#e3b7cf",
    "green": "#6cc08b", "teal": "#5bc0be", "pink": "#f2b5c4",
    "sand": "#e9c99b", "mint": "#a9e2d0", "gold": "#e6b85c",
}

# ---------------------------------------------------------------- data
# (first_col, last_col, start, end, title, description, colour)
# Columns: 0 Island, 1 Danmark, 2 Norge, 3 Sverige, 4 Finland, 5 Sápmi
BLOCKS = [
    # --- Island
    (0, 0, 870, 930, "Landnámstiden", "Traditionellt 874: Ingólfur Arnarson i Reykjavík", P["mint"]),
    (0, 0, 930, 1262, "Fristaten", "Alltinget på Þingvellir; kristendomen antas 999/1000; sagalitteraturen", P["is"]),
    (0, 0, 1262, 1380, "Under norska kronan", "Gamli sáttmáli 1262–64; gemensam kung med Danmark från 1380", P["no"]),
    (0, 0, 1814, 1918, "Under danska kronan", "Alltinget sammanträder åter 1845; hemmastyre 1904", P["dk"]),
    (0, 0, 1918, 1944, "Konungariket Island", "Personalunion med Danmark", P["teal"]),
    (0, 0, 1944, 2026, "Republiken Island", "Utropas 17 juni 1944; Nato 1949", P["is"]),

    # --- Danmark
    (1, 1, -10000, -3900, "Jägarstenålder", "Maglemose-, Kongemose- och Ertebøllekultur", P["stone"]),
    (1, 1, -3900, -1700, "Bondestenålder", "Trattbägarkultur; dösar och gånggrifter", P["stone2"]),
    (1, 1, 793, 1050, "Vikingatid", "Hedeby; Jellingestenen c. 965; Knut den store, kung i England 1016 och Danmark c. 1018", P["viking"]),
    (1, 1, 1050, 1157, "Tidig medeltid", "Ärkesäte i Lund 1103/04", P["dk"]),
    (1, 1, 1157, 1241, "Valdemarstiden", "Absalon och Köpenhamn; Jyske Lov 1241", P["pink"]),
    (1, 1, 1241, 1340, "Strid och rikets upplösning", "Kunglös tid 1332–40", P["dk"]),
    (1, 1, 1340, 1380, "Riket återupprättas", "Valdemar Atterdag; digerdöden", P["sand"]),
    (1, 1, 1814, 1849, "Enväldets sista decennier", "Kielfreden 1814: Norge avträds", P["pink"]),
    (1, 1, 1849, 1914, "Grundlov och 1864", "Grundloven 1849; Slesvig, Holsten och Lauenburg förloras 1864", P["dk"]),
    (1, 1, 1914, 1945, "Världskrigens tid", "Sønderjylland åter 1920", P["pink"]),
    (1, 1, 1945, 1973, "Välfärdsstaten byggs", "", P["modern"]),
    (1, 1, 1973, 2026, "I EG/EU", "EG 1973; Grönlands hjemmestyre 1979", P["green"]),

    # --- Norge
    (2, 2, -10000, -4000, "Jägarstenålder", "Fosna- och Komsakultur längs kusten", P["stone"]),
    (2, 2, -4000, -1700, "Yngre stenålder", "Jordbruket når Sydnorge", P["stone2"]),
    (2, 2, 793, 1050, "Vikingatid", "Hafrsfjord slutet av 800-talet; Stiklestad 1030", P["viking"]),
    (2, 2, 1050, 1130, "Riket konsolideras", "Olav Kyrre; Bergen växer fram", P["no"]),
    (2, 2, 1130, 1240, "Inbördeskrigstiden", "Ärkesäte i Nidaros 1152/53; Sverre", P["iron2"]),
    (2, 2, 1240, 1319, "Storhetstiden", "Håkon IV; Grönland 1261, Island 1262–64; Magnus Lagabøtes landslov 1274", P["no"]),
    (2, 2, 1343, 1380, "Håkon VI", "Utsedd 1343, ensam kung från 1355; digerdöden 1349", P["iron2"]),
    (2, 2, 1905, 1945, "Självständigt kungarike", "Haakon VII; kvinnlig rösträtt 1913", P["no"]),
    (2, 2, 1945, 2026, "Olja och välfärd", "Ekofisk 1969; nej till EG/EU 1972 och 1994", P["modern"]),

    # --- Sverige
    (3, 3, -10000, -4000, "Jägarstenålder", "Inlandsisen drar sig tillbaka; Hensbackakultur på Västkusten", P["stone"]),
    (3, 3, -4000, -1700, "Bondestenålder", "Trattbägar-, gropkeramisk och stridsyxekultur", P["stone2"]),
    (3, 3, 793, 1050, "Vikingatid", "Birka; Olof Skötkonung", P["viking"]),
    (3, 3, 1050, 1250, "Riket växer fram", "Erikska och sverkerska ätterna; ärkesäte i Uppsala 1164", P["se"]),
    (3, 3, 1250, 1319, "Folkungatid", "Folkungaätten regerar 1250–1363; Birger jarl; Stockholm nämns 1252", P["gold"]),
    (3, 3, 1809, 1814, "Nytt statsskick: 1809 års RF", "", P["se"]),
    (3, 3, 1905, 1921, "Demokratins genombrott", "Allmän och lika rösträtt 1918–21", P["se"]),
    (3, 3, 1921, 1945, "Mellankrigstid och krig", "Neutralitet under andra världskriget", P["gold"]),
    (3, 3, 1945, 2026, "Välfärdsstat", "EU 1995; Nato 2024", P["modern"]),

    # --- Finland
    (4, 4, -8600, -5000, "Suomusjärvikultur", "Mesolitisk jägarkultur efter isavsmältningen", P["stone"]),
    (4, 4, -5000, -2800, "Kamkeramisk kultur", "", P["stone2"]),
    (4, 4, -2800, -1600, "Båtyxe- och Kiukaiskultur", "Båtyxkulturen från c. 3200 f.Kr., parallellt med sen kamkeramik", P["stone"]),
    (4, 4, -1600, -500, "Bronsålder", "Rösen vid kusten; Sammallahdenmäki", P["bronze"]),
    (4, 4, -500, 800, "Äldre järnålder", "Förromersk till merovingisk tid; järnåldern fortsätter genom vikinga- och korstågstid", P["iron1"]),
    (4, 4, 800, 1025, "Vikingatid", "", P["viking"]),
    (4, 4, 1025, 1300, "Korstågstid", "Till c. 1150 i väster och c. 1300 i öster", P["fi"]),
    (4, 4, 1300, 1319, "Svenska riket", "Åbo domkyrka invigs 1300", P["sefi"]),
    (4, 4, 1809, 1917, "Storfurstendömet Finland", "Under Ryssland efter freden i Fredrikshamn; Borgå lantdag 1809; enkammarlantdag och kvinnlig rösträtt 1906", P["iron1"]),
    (4, 4, 1917, 1939, "Självständigt Finland", "6 dec 1917; inbördeskriget 1918; republik 1919", P["fi"]),
    (4, 4, 1939, 1944, "Krigsåren", "Vinter- och fortsättningskriget", P["war"]),
    (4, 4, 1944, 2026, "Andra republiken", "Vapenstillestånd 1944; Lapplandskriget 1944–45; EU 1995; Nato 2023", P["modern"]),

    # --- Sápmi
    (5, 5, -9000, -500, "Fångstkulturer i norr", "Komsakultur; hällkonst i Alta", P["sapmi2"]),
    (5, 5, -500, 1050, "Samisk kultur tar form", "Ursamiska sprids under äldre järnålder; dateringen omdiskuterad", P["sapmi"]),
    (5, 5, 1050, 1550, "Siidasamhällen", "Fångst, fiske och handel; skatt till flera riken", P["sapmi2"]),
    (5, 5, 1550, 1751, "Skatt, handel och mission", "Lappmarksplakatet 1673", P["sapmi"]),
    (5, 5, 1751, 1917, "Gränser och nybyggen", "Lappkodicillen 1751; nybyggen breder ut sig", P["sapmi2"]),
    (5, 5, 1917, 2026, "Samisk organisering", "Sameting: Norge 1989, Sverige 1993, Finland 1996 (delegation från 1973)", P["sapmi"]),

    # --- shared blocks (adjacent columns)
    (1, 3, -1700, -500, "Nordisk bronsålder", "Solvagnen från Trundholm; hällristningarna i Tanum", P["bronze"]),
    (1, 3, -500, 1, "Förromersk järnålder", "Hjortspringbåten", P["iron1"]),
    (1, 3, 1, 400, "Romersk järnålder", "Handel med Romarriket; runskriften tas i bruk", P["iron2"]),
    (1, 3, 400, 550, "Folkvandringstid", "Guldbrakteater; guldhornen från Gallehus", P["iron3"]),
    (1, 3, 550, 793, "Vendeltid / merovingertid", "Gamla Uppsala, Vendel och Valsgärde", P["iron4"]),
    (2, 4, 1319, 1343, "Magnus Eriksson: Sverige och Norge", "Freden i Nöteborg 1323", P["seno"]),
    (3, 4, 1343, 1397, "Sverige med Finland", "Magnus Erikssons landslag; digerdöden 1350; Albrekt av Mecklenburg 1364–89", P["sefi"]),
    (0, 2, 1380, 1397, "Danmark–Norge", "", P["dkno"]),
    (0, 4, 1397, 1523, "Kalmarunionen", "Margareta och Erik av Pommern; Sverige bryter sig ur 1523", P["union"]),
    (0, 2, 1523, 1660, "Danmark–Norge", "Reformationen 1536; Norges riksråd avskaffas 1536/37; Kristian IV", P["dkno"]),
    (0, 2, 1660, 1814, "Danmark–Norge under enväldet", "Kongeloven 1665", P["sand"]),
    (3, 4, 1523, 1611, "Äldre Vasatiden", "Gustav Vasa; reformationen inleds 1527; Uppsala möte 1593", P["se"]),
    (3, 4, 1611, 1718, "Stormaktstiden", "Gustav II Adolf; westfaliska freden 1648; Karl XII", P["gold"]),
    (3, 4, 1719, 1772, "Frihetstiden", "Riksdagsstyre; hattar och mössor", P["sefi"]),
    (3, 4, 1772, 1809, "Gustavianska tiden", "Gustav III:s statskupp 1772; finska kriget 1808–09", P["se"]),
    (2, 3, 1814, 1905, "Unionen Sverige–Norge", "Två riken, en kung; Norge med egen grundlov (Eidsvoll 17 maj 1814)", P["seno"]),
]

# Thin dark bars for short, cross-border events: (first_col, last_col, year, label)
BARS = [
    (1, 3, 793, "793 Lindisfarne – vikingatiden börjar"),
    (3, 3, 1520, "1520 Stockholms blodbad"),
    (1, 2, 1658, "1658 Roskildefreden – Skånelandskapen och Bohuslän till Sverige"),
    (2, 3, 1905, "1905 Unionsupplösningen"),
    (1, 2, 1940, "1940–45 Tysk ockupation"),
    (0, 3, 1952, "1952 Nordiska rådet (Finland ansluter 1955)"),
]

# Numbered milestones: (column, year, label)
MILESTONES = [
    (0, 930, "Alltinget instiftas"),
    (1, 965, "Jellingestenen"),
    (0, 1230, "Snorres Heimskringla (c.)"),
    (3, 1477, "Uppsala universitet"),
    (1, 1479, "Köpenhamns universitet"),
    (1, 1576, "Tycho Brahes Uraniborg"),
    (1, 1676, "Rømer mäter ljusets hastighet"),
    (3, 1735, "Linnés Systema Naturae"),
    (3, 1742, "Celsiusskalan"),
    (3, 1766, "Tryckfrihetsförordningen"),
    (3, 1809, "Justitieombudsmannen"),
    (4, 1835, "Kalevala"),
    (3, 1867, "Nobels dynamit (patent)"),
    (2, 1888, "Nansen över Grönland"),
    (3, 1901, "Nobelpriset"),
    (4, 1906, "Kvinnlig rösträtt och valbarhet"),
    (2, 1911, "Amundsen på Sydpolen"),
    (1, 1913, "Bohrs atommodell"),
    (5, 1917, "Första samiska landsmötet"),
    (3, 1952, "Tetra Pak, första maskinen"),
    (1, 1958, "LEGO-klossen (patentansökan)"),
    (3, 1958, "Pacemakern"),
    (3, 1959, "Trepunktsbältet"),
    (2, 1969, "Ekofiskfyndet"),
    (4, 1991, "Linux"),
    (3, 2008, "Spotify"),
]

ERAS = [
    (-10000, -1700, "STENÅLDER"), (-1700, -500, "BRONSÅLDER"),
    (-500, 793, "JÄRNÅLDER"), (793, 1050, "VIKINGATID"),
    (1050, 1520, "MEDELTID"), (1520, 1809, "TIDIGMODERN TID"),
    (1809, 2026, "MODERN TID"),
]

TICKS = [-10000, -8000, -6000, -4000, -3000, -2000, -1000, -500, 1, 200, 400,
         600, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1550, 1600, 1650,
         1700, 1750, 1800, 1850, 1900, 1950, 2000]

CREDIT_IMG = "https://media.licdn.com/dms/image/v2/D4E22AQHrvGeeC1Ylvg/feedshare-image-high-res/B4EaFEPazcKoAU-/0/1792146255419"
CREDIT_POST = "https://lnkd.in/p/ePw54Bpe"

INK = "#1d2733"


# ---------------------------------------------------------------- helpers
def yr(v):
    if v < 0:
        return f"{-v:,}".replace(",", " ") + " f.Kr."
    return str(v)


def wrap(text, width_px, fs):
    max_chars = max(4, int(width_px / (fs * 0.53)))
    lines, cur = [], ""
    for word in text.split():
        cand = (cur + " " + word).strip()
        if len(cand) <= max_chars:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def text_lines(x, y0, lines, fs, weight="400", style="normal", fill=INK, anchor="middle", lh=1.18):
    out = []
    for i, ln in enumerate(lines):
        out.append(
            f'<text x="{x:.1f}" y="{y0 + i * fs * lh:.1f}" font-size="{fs}" '
            f'font-weight="{weight}" font-style="{style}" fill="{fill}" '
            f'text-anchor="{anchor}">{escape(ln)}</text>'
        )
    return out


def render_block(b):
    c0, c1, s, e, title, desc, colour = b
    x = col_x(c0) + GAP / 2
    w = (c1 - c0 + 1) * COL_W - GAP
    y0, y1 = y(s), y(e)
    h = y1 - y0 - GAP
    out = [f'<g><title>{escape(title)} ({yr(s)}–{yr(e)}). {escape(desc)}</title>',
           f'<rect x="{x:.1f}" y="{y0 + GAP / 2:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{colour}"/>']
    cx = x + w / 2
    span = c1 - c0 + 1
    tfs = 13 if span == 1 else (15 if span <= 2 else 19)
    if h < 16:
        tfs = 9 if span == 1 else 11
        one = title if span > 1 else wrap(title, w - 8, tfs)[0]
        out += text_lines(cx, y0 + h / 2 + tfs * 0.4, [one], tfs, "700")
        out.append("</g>")
        return out
    # start-year tag
    if h >= 34:
        out.append(f'<text x="{x + 4:.1f}" y="{y0 + 11:.1f}" font-size="8.5" fill="{INK}" opacity="0.75">{escape(yr(s))}</text>')
    tl = wrap(title, w - 14, tfs)
    dfs = 9.5 if span == 1 else 11.5
    dl = wrap(desc, w - 16, dfs) if desc else []
    need_t = len(tl) * tfs * 1.18
    need_d = len(dl) * dfs * 1.2
    avail = h - (16 if h >= 34 else 4)
    if need_t + need_d + 4 > avail:
        # drop whole "; "-separated phrases from the end until it fits
        phrases = desc.split("; ")
        while phrases and need_t + len(wrap("; ".join(phrases), w - 16, dfs)) * dfs * 1.2 + 4 > avail:
            phrases = phrases[:-1]
        dl = wrap("; ".join(phrases), w - 16, dfs) if phrases else []
        need_d = len(dl) * dfs * 1.2
        if need_t > avail:
            tl = tl[:max(1, int(avail // (tfs * 1.18)))]
            need_t = len(tl) * tfs * 1.18
    total = need_t + (need_d + 4 if dl else 0)
    top_pad = 16 if h >= 34 else 2
    start = y0 + top_pad + max(0, (h - top_pad - total) / 2) + tfs * 0.85
    if span == 1 and h > 140:
        start = y0 + top_pad + 26 + tfs * 0.85
    out += text_lines(cx, start, tl, tfs, "800")
    if dl:
        out += text_lines(cx, start + need_t + 2, dl, dfs, "400", "normal", "#33404d", lh=1.2)
    out.append("</g>")
    return out


def render_bar(bar):
    c0, c1, year, label = bar
    x = col_x(c0) + GAP / 2
    w = (c1 - c0 + 1) * COL_W - GAP
    yy = y(year)
    return [f'<rect x="{x:.1f}" y="{yy - 6:.1f}" width="{w:.1f}" height="12" fill="#1f2a36" rx="1"/>',
            f'<text x="{x + w / 2:.1f}" y="{yy + 3:.1f}" font-size="8.5" font-weight="700" fill="#fff" text-anchor="middle">{escape(label)}</text>']


def render_milestones():
    out, placed = [], {}
    for i, (c, year, label) in enumerate(MILESTONES, 1):
        yy = y(year)
        mb = [b for b in BLOCKS if b[0] <= c <= b[1] and b[1] > b[0] and b[2] <= year < b[3]]
        # inside a merged block, put the marker on the column edge away from the centred text
        left = bool(mb) and c <= (mb[0][0] + mb[0][1]) / 2
        cx = col_x(c) + (13 if left else COL_W - 13)
        if any(b0 <= c <= b1 and abs(y(by) - yy) < 10 for b0, b1, by, _ in BARS):
            yy += 13
        for py, px in placed.get(c, []):
            if abs(py - yy) < 15 and abs(px - cx) < 15:
                cx -= 17
        placed.setdefault(c, []).append((yy, cx))
        out.append(f'<g><title>{i}. {escape(label)} ({year})</title>'
                   f'<circle cx="{cx:.1f}" cy="{yy:.1f}" r="7" fill="#fff" stroke="{INK}" stroke-width="1.2"/>'
                   f'<text x="{cx:.1f}" y="{yy + 3:.1f}" font-size="8" font-weight="700" fill="{INK}" text-anchor="middle">{i}</text></g>')
    return out


def render_axis():
    out = []
    for t in TICKS:
        yy = y(t)
        out.append(f'<line x1="{X0 - 8}" y1="{yy:.1f}" x2="{X0 - 2}" y2="{yy:.1f}" stroke="{INK}" stroke-width="1"/>')
        lab = "1 e.Kr." if t == 1 else yr(t)
        out.append(f'<text x="{X0 - 11}" y="{yy + 3:.1f}" font-size="8.5" fill="{INK}" text-anchor="end">{lab}</text>')
    for s, e, name in ERAS:
        y0, y1 = y(s), y(e)
        out.append(f'<line x1="22" y1="{y0 + 2:.1f}" x2="22" y2="{y1 - 2:.1f}" stroke="{INK}" stroke-width="1.5"/>')
        out.append(f'<line x1="16" y1="{y0 + 2:.1f}" x2="28" y2="{y0 + 2:.1f}" stroke="{INK}" stroke-width="1.5"/>')
        mid = (y0 + y1) / 2
        fs = 11 if (y1 - y0) > 110 else 9
        out.append(f'<text x="12" y="{mid:.1f}" font-size="{fs}" font-weight="800" letter-spacing="1.5" fill="{INK}" '
                   f'text-anchor="middle" transform="rotate(-90 12 {mid:.1f})">{name}</text>')
    return out


# ---------------------------------------------------------------- icons
def icon(c, top_year):
    cx = col_x(c) + COL_W / 2
    base = y(top_year) - 3
    st = f'fill="#fff" stroke="{INK}" stroke-width="1.6" stroke-linejoin="round"'
    g = []
    if c == 0:  # Hallgrímskirkja-like stepped tower
        b = base
        g.append(f'<path d="M{cx-46},{b} L{cx-46},{b-22} L{cx-34},{b-22} L{cx-34},{b-34} L{cx-24},{b-34} L{cx-24},{b-48} '
                 f'L{cx-14},{b-48} L{cx-14},{b-66} L{cx-7},{b-66} L{cx-7},{b-104} L{cx},{b-122} L{cx+7},{b-104} L{cx+7},{b-66} '
                 f'L{cx+14},{b-66} L{cx+14},{b-48} L{cx+24},{b-48} L{cx+24},{b-34} L{cx+34},{b-34} L{cx+34},{b-22} '
                 f'L{cx+46},{b-22} L{cx+46},{b} Z" {st}/>')
        g.append(f'<rect x="{cx-3}" y="{b-96}" width="6" height="8" fill="{INK}"/>')
        g.append(f'<path d="M{cx-6},{b} L{cx-6},{b-12} Q{cx},{b-18} {cx+6},{b-12} L{cx+6},{b} Z" fill="{INK}"/>')
    elif c == 1:  # Rundetårn
        b = base
        g.append(f'<rect x="{cx-22}" y="{b-92}" width="44" height="92" {st}/>')
        g.append(f'<rect x="{cx-25}" y="{b-98}" width="50" height="7" {st}/>')
        for k in range(-20, 21, 8):
            g.append(f'<line x1="{cx+k}" y1="{b-98}" x2="{cx+k}" y2="{b-91}" stroke="{INK}" stroke-width="1"/>')
        g.append(f'<path d="M{cx-9},{b-98} L{cx-9},{b-110} L{cx+9},{b-110} L{cx+9},{b-98}" {st}/>')
        g.append(f'<path d="M{cx-11},{b-110} Q{cx},{b-122} {cx+11},{b-110} Z" {st}/>')
        for yy in (b-78, b-55, b-32):
            g.append(f'<rect x="{cx-4}" y="{yy}" width="8" height="12" rx="4" fill="{INK}"/>')
        g.append(f'<path d="M{cx-7},{b} L{cx-7},{b-14} Q{cx},{b-20} {cx+7},{b-14} L{cx+7},{b} Z" fill="{INK}"/>')
    elif c == 2:  # stave church
        b = base
        def roof(w, top, h):
            return f'<path d="M{cx-w},{top+h} L{cx},{top} L{cx+w},{top+h} Z" {st}/>'
        g.append(f'<rect x="{cx-38}" y="{b-26}" width="76" height="26" {st}/>')
        g.append(roof(46, b-46, 20))
        g.append(f'<rect x="{cx-26}" y="{b-58}" width="52" height="12" {st}/>')
        g.append(roof(32, b-76, 18))
        g.append(f'<rect x="{cx-15}" y="{b-86}" width="30" height="10" {st}/>')
        g.append(roof(20, b-102, 16))
        g.append(f'<rect x="{cx-6}" y="{b-110}" width="12" height="8" {st}/>')
        g.append(f'<path d="M{cx-8},{b-110} L{cx},{b-136} L{cx+8},{b-110} Z" {st}/>')
        for sx in (-1, 1):
            for (w, top, h) in ((46, b-46, 20), (32, b-76, 18), (20, b-102, 16)):
                xx = cx + sx * w * 0.55
                g.append(f'<path d="M{xx},{top+h*0.45} q{sx*6},-6 {sx*4},-12" fill="none" stroke="{INK}" stroke-width="1.4"/>')
        g.append(f'<path d="M{cx-6},{b} L{cx-6},{b-14} Q{cx},{b-20} {cx+6},{b-14} L{cx+6},{b} Z" fill="{INK}"/>')
    elif c == 3:  # Stockholm City Hall tower with three crowns
        b = base
        g.append(f'<rect x="{cx-48}" y="{b-22}" width="96" height="22" {st}/>')
        g.append(f'<rect x="{cx-14}" y="{b-100}" width="28" height="78" {st}/>')
        g.append(f'<rect x="{cx-17}" y="{b-106}" width="34" height="7" {st}/>')
        g.append(f'<path d="M{cx-11},{b-106} L{cx-11},{b-116} L{cx+11},{b-116} L{cx+11},{b-106}" {st}/>')
        g.append(f'<path d="M{cx-5},{b-116} L{cx},{b-128} L{cx+5},{b-116} Z" {st}/>')
        for k, dy in ((-7, 0), (7, 0), (0, -9)):
            yy = b - 134 + dy
            g.append(f'<path d="M{cx+k-4},{yy+6} L{cx+k-4},{yy} L{cx+k-2},{yy+3} L{cx+k},{yy-1} L{cx+k+2},{yy+3} L{cx+k+4},{yy} L{cx+k+4},{yy+6} Z" fill="#e6b85c" stroke="{INK}" stroke-width="1"/>')
        for yy in (b-90, b-70, b-50):
            g.append(f'<rect x="{cx-4}" y="{yy}" width="8" height="10" fill="{INK}"/>')
        for k in range(-40, 41, 12):
            g.append(f'<rect x="{cx+k-2}" y="{b-16}" width="4" height="9" fill="{INK}"/>')
    elif c == 4:  # Helsinki Cathedral
        b = base
        g.append(f'<rect x="{cx-50}" y="{b-36}" width="100" height="36" {st}/>')
        g.append(f'<path d="M{cx-22},{b-36} L{cx},{b-50} L{cx+22},{b-36} Z" {st}/>')
        for k in range(-16, 17, 8):
            g.append(f'<line x1="{cx+k}" y1="{b-34}" x2="{cx+k}" y2="{b-4}" stroke="{INK}" stroke-width="1.2"/>')
        g.append(f'<rect x="{cx-14}" y="{b-74}" width="28" height="22" {st}/>')
        g.append(f'<path d="M{cx-16},{b-74} Q{cx-16},{b-100} {cx},{b-102} Q{cx+16},{b-100} {cx+16},{b-74} Z" fill="#9fd3c7" stroke="{INK}" stroke-width="1.6"/>')
        g.append(f'<line x1="{cx}" y1="{b-102}" x2="{cx}" y2="{b-114}" stroke="{INK}" stroke-width="1.6"/>')
        g.append(f'<line x1="{cx-4}" y1="{b-110}" x2="{cx+4}" y2="{b-110}" stroke="{INK}" stroke-width="1.6"/>')
        for sx in (-40, 40):
            g.append(f'<rect x="{cx+sx-6}" y="{b-50}" width="12" height="14" {st}/>')
            g.append(f'<path d="M{cx+sx-7},{b-50} Q{cx+sx},{b-64} {cx+sx+7},{b-50} Z" fill="#9fd3c7" stroke="{INK}" stroke-width="1.4"/>')
    elif c == 5:  # lavvu
        b = base
        g.append(f'<path d="M{cx-34},{b} L{cx-2},{b-70} L{cx+2},{b-70} L{cx+34},{b} Z" {st}/>')
        for dx in (-8, -3, 3, 8):
            g.append(f'<line x1="{cx}" y1="{b-68}" x2="{cx+dx}" y2="{b-82}" stroke="{INK}" stroke-width="1.6"/>')
        g.append(f'<path d="M{cx-8},{b} L{cx},{b-22} L{cx+8},{b} Z" fill="{INK}"/>')
        g.append(f'<path d="M{cx-22},{b-26} L{cx+22},{b-26}" stroke="#d6453d" stroke-width="2"/>')
        g.append(f'<path d="M{cx-19},{b-32} L{cx+19},{b-32}" stroke="#2f6db5" stroke-width="2"/>')
    return g


# ---------------------------------------------------------------- flags
def flag(c, x, yy, w=46, h=30):
    out = []
    def cross(bg, outer, inner, vx=0.36, tw=0.25, iw=0.12):
        out.append(f'<rect x="{x}" y="{yy}" width="{w}" height="{h}" fill="{bg}" stroke="#ccd" stroke-width="0.5"/>')
        if outer:
            out.append(f'<rect x="{x + w*vx - w*tw/2}" y="{yy}" width="{w*tw}" height="{h}" fill="{outer}"/>')
            out.append(f'<rect x="{x}" y="{yy + h/2 - h*tw*0.8/2*1.55}" width="{w}" height="{h*tw*1.24}" fill="{outer}"/>')
        out.append(f'<rect x="{x + w*vx - w*iw/2}" y="{yy}" width="{w*iw}" height="{h}" fill="{inner}"/>')
        out.append(f'<rect x="{x}" y="{yy + h/2 - h*iw*1.55/2}" width="{w}" height="{h*iw*1.55}" fill="{inner}"/>')
    if c == 0:
        cross("#02529c", "#ffffff", "#dc1e35")
    elif c == 1:
        out.append(f'<rect x="{x}" y="{yy}" width="{w}" height="{h}" fill="#c8102e"/>')
        out.append(f'<rect x="{x + w*0.36 - w*0.06}" y="{yy}" width="{w*0.12}" height="{h}" fill="#fff"/>')
        out.append(f'<rect x="{x}" y="{yy + h/2 - h*0.09}" width="{w}" height="{h*0.18}" fill="#fff"/>')
    elif c == 2:
        cross("#ba0c2f", "#ffffff", "#00205b")
    elif c == 3:
        out.append(f'<rect x="{x}" y="{yy}" width="{w}" height="{h}" fill="#006aa7"/>')
        out.append(f'<rect x="{x + w*0.36 - w*0.07}" y="{yy}" width="{w*0.14}" height="{h}" fill="#fecc02"/>')
        out.append(f'<rect x="{x}" y="{yy + h/2 - h*0.1}" width="{w}" height="{h*0.2}" fill="#fecc02"/>')
    elif c == 4:
        out.append(f'<rect x="{x}" y="{yy}" width="{w}" height="{h}" fill="#fff" stroke="#ccd" stroke-width="0.5"/>')
        out.append(f'<rect x="{x + w*0.36 - w*0.08}" y="{yy}" width="{w*0.16}" height="{h}" fill="#002f6c"/>')
        out.append(f'<rect x="{x}" y="{yy + h/2 - h*0.13}" width="{w}" height="{h*0.26}" fill="#002f6c"/>')
    elif c == 5:  # Sámi flag (Sámi Council proportions)
        out.append(f'<rect x="{x}" y="{yy}" width="{w*0.319}" height="{h}" fill="#d7262e"/>')
        out.append(f'<rect x="{x + w*0.319}" y="{yy}" width="{w*0.07}" height="{h}" fill="#007a3d"/>')
        out.append(f'<rect x="{x + w*0.389}" y="{yy}" width="{w*0.069}" height="{h}" fill="#ffce00"/>')
        out.append(f'<rect x="{x + w*0.458}" y="{yy}" width="{w*0.542}" height="{h}" fill="#0035ad"/>')
        r = h * 0.29
        ccx = x + w * 0.389
        ccy = yy + h / 2
        out.append(f'<path d="M{ccx},{ccy - r} A{r},{r} 0 0 0 {ccx},{ccy + r}" fill="none" stroke="#0035ad" stroke-width="1.6"/>')
        out.append(f'<path d="M{ccx},{ccy - r} A{r},{r} 0 0 1 {ccx},{ccy + r}" fill="none" stroke="#d7262e" stroke-width="1.6"/>')
    return out


# ---------------------------------------------------------------- page
def column_top(c):
    return min(b[2] for b in BLOCKS if b[0] <= c <= b[1])


def build_svg():
    s = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
         f'font-family="Inter, \'Helvetica Neue\', Arial, sans-serif" role="img" '
         f'aria-label="Nordens historia – en tidslinje">',
         f'<rect width="{WIDTH}" height="{HEIGHT}" fill="#fbfaf7"/>',
         f'<text x="{WIDTH/2}" y="62" font-size="44" font-weight="900" fill="{INK}" text-anchor="middle" letter-spacing="1">NORDENS HISTORIA</text>',
         f'<text x="{WIDTH/2}" y="88" font-size="15" fill="#4a5764" text-anchor="middle">En tidslinje över Island, Danmark, Norge, Sverige, Finland och Sápmi</text>']
    # milestone legend
    s.append(f'<text x="40" y="122" font-size="11" font-weight="800" fill="{INK}">Milstolpar</text>')
    per_col = 9
    for i, (c, year, label) in enumerate(MILESTONES, 1):
        col, row = divmod(i - 1, per_col)
        lx = 40 + col * 300
        ly = 140 + row * 16
        s.append(f'<circle cx="{lx + 6}" cy="{ly - 3.5}" r="6" fill="#fff" stroke="{INK}" stroke-width="1"/>')
        s.append(f'<text x="{lx + 6}" y="{ly - 0.8}" font-size="7.5" font-weight="700" fill="{INK}" text-anchor="middle">{i}</text>')
        s.append(f'<text x="{lx + 17}" y="{ly}" font-size="10" fill="{INK}">{escape(label)} <tspan fill="#6b7682">({year})</tspan></text>')
    s += render_axis()
    for b in BLOCKS:
        s += render_block(b)
    for bar in BARS:
        s += render_bar(bar)
    s += render_milestones()
    for c in range(len(COLUMNS)):
        s += icon(c, column_top(c))
    # bottom labels + flags
    for c, name in enumerate(COLUMNS):
        cx = col_x(c) + COL_W / 2
        s += flag(c, cx - 23, BOTTOM + 14)
        s.append(f'<text x="{cx}" y="{BOTTOM + 64}" font-size="15" font-weight="800" fill="{INK}" text-anchor="middle">{escape(name)}</text>')
    s.append(f'<text x="{WIDTH/2}" y="{BOTTOM + 104}" font-size="10" fill="#4a5764" text-anchor="middle">'
             f'Inspirerad av "Timeline of World History" av Chart Origin (chartorigin.com). Förenklad framställning; '
             f'periodgränser är konventionella och ofta glidande.</text>')
    s.append(f'<text x="{WIDTH/2}" y="{BOTTOM + 122}" font-size="10" fill="#4a5764" text-anchor="middle">'
             f'Kolumnordningen är vald så att unionerna blir sammanhängande block, inte geografisk. Kerstin Forsberg, sidospår, oktober 2026.</text>')
    s.append("</svg>")
    return "\n".join(x for x in s if x)


PAGE = """<!doctype html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Nordens historia – en tidslinje</title>
<style>
  body {{ margin: 0; background: #fbfaf7; color: #1d2733;
         font-family: Inter, "Helvetica Neue", Arial, sans-serif; line-height: 1.5; }}
  main {{ max-width: 1120px; margin: 0 auto; padding: 24px 16px 48px; }}
  .intro, .notes {{ max-width: 760px; }}
  a {{ color: #2f6db5; }}
  .poster {{ overflow-x: auto; margin: 20px 0; border: 1px solid #e3e0d8; background: #fbfaf7; }}
  .poster svg {{ display: block; width: 100%; min-width: 760px; height: auto; }}
  .notes h2 {{ font-size: 1.05rem; margin-top: 1.6em; }}
  .notes li {{ margin-bottom: 0.3em; }}
  .back {{ font-size: 0.9rem; }}
</style>
</head>
<body>
<main>
<p class="back"><a href="../">← Sidospår</a></p>
<h1>Nordens historia – en tidslinje</h1>
<div class="intro">
<p>En nordisk variant av Chart Origins affisch <em>Timeline of World History</em>:
en kolumn per land, ett block per riksbildning eller period, och sammanslagna block
där länderna delat rike – Kalmarunionen, Danmark–Norge, Sverige med Finland och unionen Sverige–Norge.
Håll muspekaren över ett block för datum.</p>
<p><strong>Originalet:</strong> <a href="{img}">Timeline of World History</a> av
<a href="https://chartorigin.com">Chart Origin</a>, delad på <a href="{post}">LinkedIn</a>.
Idén och formen är deras; innehållet här är mitt eget urval.</p>
<p><strong>Källäget:</strong> varje uppgift är kontrollerad mot en uppslagskälla, se <a href="kallor.html">källförteckningen</a>.</p>
</div>
<div class="poster">
{svg}
</div>
<div class="notes">
<h2>Om urvalet</h2>
<ul>
<li>Tidsaxeln är inte linjär: stenåldern är hårt komprimerad och de senaste femhundra åren utdragna, som i originalet.</li>
<li>Kolumnerna står i ordningen Island, Danmark, Norge, Sverige, Finland, Sápmi. Det är inte geografi utan ett sätt att få varje union att bli ett sammanhängande block.</li>
<li>Förhistoriska perioder och kulturnamn följer konventionell skandinavisk arkeologisk periodindelning. Gränserna är glidande och skiljer sig mellan regioner.</li>
<li>Sápmi är ingen stat utan ett kulturområde som delas av Norge, Sverige, Finland och Ryssland. Kolumnen visar samisk historia vid sidan av riksbildningarna; dateringen av de tidiga perioderna är omdiskuterad.</li>
<li>Grönland, Färöarna och Åland har ingen egen kolumn.</li>
</ul>
</div>
</main>
</body>
</html>
"""


def main():
    out = Path(__file__).with_name("index.html")
    out.write_text(PAGE.format(svg=build_svg(), img=CREDIT_IMG, post=CREDIT_POST), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
