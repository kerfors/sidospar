"""Generate index.html: a Nordic timeline poster in the style of
Chart Origin's "Timeline of World History".

Data lives in data/items.json and data/claims.json.
Run: python3 build.py  ->  writes index.html, kallor.html, kallkatalog.html, id/, linked-data.html and sparql.html
(via make_kallor.py, make_kallkatalog.py, ld.py, ld_page.py and sparql_page.py).

nordens-historia-affisch.png is a snapshot of the poster (1200 px wide, rendered
from the SVG with cairosvg). This script does not re-render it: render it again
by hand when the poster changes.
"""
import json
import sys
from pathlib import Path
from html import escape

# ---------------------------------------------------------------- layout
COLUMNS = ["Island", "Danmark", "Norge", "Sverige", "Finland"]
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


# ---------------------------------------------------------------- data
# All content lives in data/items.json, each item with an opaque id (see ld.py).
DATA = json.loads((Path(__file__).parent / "data" / "items.json").read_text(encoding="utf-8"))
assert DATA["columns"] == COLUMNS, "column order in data/items.json differs from COLUMNS"
P = DATA["palette"]
CI = {name: i for i, name in enumerate(COLUMNS)}
# (first_col, last_col, start, end, title, description, colour)
BLOCKS = [(CI[p["columns"][0]], CI[p["columns"][-1]], p["start"], p["end"], p["label"], p["description"], P[p["colour"]])
          for p in DATA["periods"]]
BLOCK_IDS = [p["id"] for p in DATA["periods"]]
# (first_col, last_col, year, label)
BARS = [(CI[e["columns"][0]], CI[e["columns"][-1]], e["year"], e["label"]) for e in DATA["events"]]
BAR_IDS = [e["id"] for e in DATA["events"]]
# (column, year, label)
MILESTONES = [(CI[m["column"]], m["year"], m["label"]) for m in DATA["milestones"]]
MS_IDS = [m["id"] for m in DATA["milestones"]]

ERAS = [
    (-10000, -1700, "STENÅLDER"), (-1700, -500, "BRONSÅLDER"),
    (-500, 793, "JÄRNÅLDER"), (793, 1050, "VIKINGATID"),
    (1050, 1520, "MEDELTID"), (1520, 1809, "TIDIGMODERN TID"),
    (1809, 2026, "MODERN TID"),
]

TICKS = [-10000, -8000, -6000, -4000, -3000, -2000, -1000, -500, 1, 200, 400,
         600, 800, 900, 1000, 1100, 1200, 1300, 1400, 1500, 1550, 1600, 1650,
         1700, 1750, 1800, 1850, 1900, 1950, 2000]

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


def item_attrs(item_id, label):
    return f'class="item" data-id="{item_id}" tabindex="0" role="button" aria-label="{escape(label)}"'


def render_block(b, item_id):
    c0, c1, s, e, title, desc, colour = b
    x = col_x(c0) + GAP / 2
    w = (c1 - c0 + 1) * COL_W - GAP
    y0, y1 = y(s), y(e)
    h = y1 - y0 - GAP
    out = [f'<g {item_attrs(item_id, title)}><title>{escape(title)} ({yr(s)}–{yr(e)}). {escape(desc)}</title>',
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


def render_bar(bar, item_id):
    c0, c1, year, label = bar
    x = col_x(c0) + GAP / 2
    w = (c1 - c0 + 1) * COL_W - GAP
    yy = y(year)
    return [f'<g {item_attrs(item_id, label)}><title>{escape(label)}</title>',
            f'<rect x="{x:.1f}" y="{yy - 6:.1f}" width="{w:.1f}" height="12" fill="#1f2a36" rx="1"/>',
            f'<text x="{x + w / 2:.1f}" y="{yy + 3:.1f}" font-size="8.5" font-weight="700" fill="#fff" text-anchor="middle">{escape(label)}</text>', '</g>']


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
        out.append(f'<g {item_attrs(MS_IDS[i - 1], label)}><title>{i}. {escape(label)} ({year})</title>'
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
         f'<text x="{WIDTH/2}" y="88" font-size="15" fill="#4a5764" text-anchor="middle">En tidslinje över Island, Danmark, Norge, Sverige och Finland</text>']
    # milestone legend
    s.append(f'<text x="40" y="122" font-size="11" font-weight="800" fill="{INK}">Milstolpar</text>')
    per_col = 9
    for i, (c, year, label) in enumerate(MILESTONES, 1):
        col, row = divmod(i - 1, per_col)
        lx = 40 + col * 300
        ly = 140 + row * 16
        s.append(f'<g {item_attrs(MS_IDS[i - 1], label)}>')
        s.append(f'<rect x="{lx - 2}" y="{ly - 12}" width="280" height="15" fill="#fbfaf7" opacity="0"/>')
        s.append(f'<circle cx="{lx + 6}" cy="{ly - 3.5}" r="6" fill="#fff" stroke="{INK}" stroke-width="1"/>')
        s.append(f'<text x="{lx + 6}" y="{ly - 0.8}" font-size="7.5" font-weight="700" fill="{INK}" text-anchor="middle">{i}</text>')
        s.append(f'<text x="{lx + 17}" y="{ly}" font-size="10" fill="{INK}">{escape(label)} <tspan fill="#6b7682">({year})</tspan></text>')
        s.append('</g>')
    s += render_axis()
    for b, item_id in zip(BLOCKS, BLOCK_IDS):
        s += render_block(b, item_id)
    for bar, item_id in zip(BARS, BAR_IDS):
        s += render_bar(bar, item_id)
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
Klicka på ett block, en händelse eller en siffra för datum, källor och identifierare.</p>
<p><strong>Originalet:</strong> <a href="{post}">Timeline of World History</a> av
<a href="https://chartorigin.com">Chart Origin</a>.
Idén och formen är deras; innehållet här är mitt eget urval.</p>
<p><strong>Källäget:</strong> varje uppgift är kontrollerad mot en uppslagskälla, se <a href="kallor.html">källförteckningen</a>, och alla källor samlade per uppslagsverk och utgivare finns i <a href="kallkatalog.html">källorna</a>.</p>
<p><strong>Länkade data:</strong> varje period, händelse, milstolpe och kontrollerad uppgift har en egen beständig
identifierare som går att slå upp, med JSON-LD, Turtle och länkar till Wikidata. Se <a href="id/">identifierarna</a>
och, på engelska, <a href="linked-data.html">The linked data behind the poster</a>. Datan går att ställa frågor mot
direkt i webbläsaren på <a href="sparql.html">SPARQL-sidan</a>.
Innehåll och data är licensierade under <a href="https://creativecommons.org/licenses/by/4.0/deed.sv">CC BY 4.0</a>.</p>
<p><strong>Som bild:</strong> affischen finns också som <a href="nordens-historia-affisch.png">PNG-fil</a> (1200 px bred).</p>
</div>
<div class="poster">
{svg}
</div>
<div class="notes">
<h2>Om urvalet</h2>
<ul>
<li>Tidsaxeln är inte linjär: stenåldern är hårt komprimerad och de senaste femhundra åren utdragna, som i originalet.</li>
<li>Kolumnerna står i ordningen Island, Danmark, Norge, Sverige, Finland. Det är inte geografi utan ett sätt att få varje union att bli ett sammanhängande block.</li>
<li>Förhistoriska perioder och kulturnamn följer konventionell skandinavisk arkeologisk periodindelning. Gränserna är glidande och skiljer sig mellan regioner.</li>
<li>Grönland, Färöarna och Åland har ingen egen kolumn.</li>
</ul>
</div>
</main>
</body>
</html>
"""


EXTRA_HEAD = """<style>
  .poster .item { cursor: pointer; }
  .poster .item:focus { outline: none; }
  .poster .item:hover > rect, .poster .item:hover > circle { filter: brightness(0.93); }
  .poster .item.sel > rect, .poster .item.sel > circle { stroke: #1d2733; stroke-width: 2.5; }
  .poster .item.sel > circle { fill: #ffd84d; }
  .poster .item:focus-visible > rect, .poster .item:focus-visible > circle { stroke: #2f6db5; stroke-width: 3; }
  #panel { position: fixed; left: 50%; bottom: 16px; transform: translateX(-50%); width: min(640px, calc(100% - 32px));
           box-sizing: border-box; background: #fff; border: 1px solid #d6d2c8; border-radius: 6px;
           box-shadow: 0 6px 24px rgba(0,0,0,0.15); padding: 14px 16px; z-index: 10; max-height: 60vh; overflow: auto; }
  #panel[hidden] { display: none; }
  #panel .kind { color: #6b7682; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.06em; margin: 0; }
  #panel h2 { margin: 2px 0 4px; font-size: 1.2rem; padding-right: 28px; }
  #panel p { margin: 4px 0; }
  #panel .meta { color: #4a5764; font-size: 0.9rem; }
  #panel code { font-size: 0.8rem; background: #f1eee7; padding: 1px 4px; border-radius: 3px; overflow-wrap: anywhere; }
  #panel .close { position: absolute; top: 8px; right: 10px; border: 0; background: none; font-size: 1.4rem; cursor: pointer; color: #4a5764; }
  .v { display: inline-block; padding: 0 6px; border-radius: 3px; font-size: 0.78rem; margin-right: 4px; }
  .v.bekräftad { background: #d8efdc; } .v.omdiskuterad { background: #f7e3b5; }
</style>
"""

PANEL = """<aside id="panel" hidden aria-live="polite">
<button class="close" type="button" aria-label="Stäng">×</button>
<p class="kind" id="p-kind"></p>
<h2 id="p-label"></h2>
<p class="meta" id="p-meta"></p>
<p id="p-desc"></p>
<p id="p-defs" class="meta"></p>
<p id="p-claims"></p>
<p id="p-wd"></p>
<p><a id="p-link" href="#">Öppna posten</a> · <code id="p-iri"></code></p>
</aside>
"""

SCRIPT = """<script>
(function () {
  const D = JSON.parse(document.getElementById('nh-data').textContent);
  const panel = document.getElementById('panel');
  const $ = (id) => document.getElementById(id);
  function show(id, scroll) {
    const d = D[id];
    if (!d) return;
    $('p-kind').textContent = d.kind;
    $('p-label').textContent = d.label;
    $('p-meta').textContent = d.when + ' · ' + d.where;
    $('p-desc').textContent = d.desc || '';
    $('p-defs').textContent = d.defs && d.defs.length ? 'Källornas gränser: ' + d.defs.join('; ') : '';
    const c = $('p-claims');
    c.textContent = '';
    for (const [v, n] of Object.entries(d.verdicts)) {
      const s = document.createElement('span');
      s.className = 'v ' + v;
      s.textContent = n + ' ' + v;
      c.appendChild(s);
    }
    const k = document.createElement('a');
    k.href = d.url;
    k.textContent = 'källor och utlåtanden';
    c.appendChild(document.createTextNode(' '));
    c.appendChild(k);
    const w = $('p-wd');
    w.textContent = '';
    if (d.wd) {
      w.appendChild(document.createTextNode('Wikidata (' + d.wd.rel + '): '));
      const a = document.createElement('a');
      a.href = 'https://www.wikidata.org/wiki/' + d.wd.qid;
      a.textContent = d.wd.qid + ' ' + d.wd.label;
      w.appendChild(a);
    }
    $('p-link').href = d.url;
    $('p-iri').textContent = d.iri;
    panel.hidden = false;
    document.querySelectorAll('.item.sel').forEach((e) => e.classList.remove('sel'));
    const els = document.querySelectorAll('.poster .item[data-id="' + id + '"]');
    els.forEach((e) => e.classList.add('sel'));
    history.replaceState(null, '', '#' + id);
    if (scroll && els.length) els[els.length - 1].scrollIntoView({ block: 'center' });
  }
  const svg = document.querySelector('.poster svg');
  svg.addEventListener('click', (e) => {
    const g = e.target.closest('.item');
    if (g) show(g.dataset.id, false);
  });
  svg.addEventListener('keydown', (e) => {
    const g = e.target.closest('.item');
    if (g && (e.key === 'Enter' || e.key === ' ')) { e.preventDefault(); show(g.dataset.id, false); }
  });
  panel.querySelector('.close').addEventListener('click', () => {
    panel.hidden = true;
    document.querySelectorAll('.item.sel').forEach((e) => e.classList.remove('sel'));
    history.replaceState(null, '', location.pathname);
  });
  const fromHash = () => { const h = location.hash.slice(1); if (D[h]) show(h, true); };
  window.addEventListener('hashchange', fromHash);
  fromHash();
})();
</script>
"""

ID_BASE = "https://w3id.org/people/kerfors/sidospar/nordens-historia/id/"


def panel_data():
    sys.dont_write_bytecode = True
    here = Path(__file__).parent
    claims = json.loads((here / "data" / "claims.json").read_text(encoding="utf-8"))
    wpath = here / "data" / "wikidata.json"
    wd = json.loads(wpath.read_text(encoding="utf-8")) if wpath.exists() else {}
    import ld
    _, _, _, defs = ld.load()
    defs_by = {}
    for d in defs:
        p = next(x for x in DATA["periods"] if x["id"] == d["period"])
        s = (("c. " if d["approx_start"] else "") + yr(d["start"]) if d["start"] is not None else "?")
        e = (("c. " if d["approx_end"] else "") + yr(d["end"]) if d["end"] is not None else "?")
        same = " (samma)" if (d["start"], d["end"]) == (p["start"], p["end"]) else ""
        defs_by.setdefault(d["period"], []).append(f"{ld.publication(d['source_url'])[1]} {s}–{e}{same}")
    verdicts = {}
    for c in claims:
        for a in c["about"]:
            v = verdicts.setdefault(a, {})
            v[c["verdict"]] = v.get(c["verdict"], 0) + 1
    out = {}
    def add(x, kind, when, where):
        m = wd.get(x["id"])
        link = None
        if m and m.get("qid") and m.get("match") not in (None, "none"):
            rel = "handlar om" if kind == "Milstolpe" or m.get("relation") == "about" else \
                {"exactMatch": "samma som", "closeMatch": "närliggande"}[m["match"]]
            link = {"qid": m["qid"], "label": m.get("wikidata_label", ""), "rel": rel}
        out[x["id"]] = {"kind": kind, "label": x["label"], "when": when, "where": where,
                        "desc": x.get("description", ""), "verdicts": verdicts.get(x["id"], {}),
                        "wd": link, "url": "id/" + x["id"] + "/", "iri": ID_BASE + x["id"],
                        "defs": defs_by.get(x["id"], [])}
    for x in DATA["periods"]:
        add(x, "Period", f"{yr(x['start'])} – {yr(x['end'])}", ", ".join(x["columns"]))
    for x in DATA["events"]:
        add(x, "Händelse", yr(x["year"]), ", ".join(x["columns"]))
    for x in DATA["milestones"]:
        add(x, "Milstolpe", yr(x["year"]), x["column"])
    return out


def main():
    out = Path(__file__).with_name("index.html")
    html = PAGE.format(svg=build_svg(), post=CREDIT_POST)
    data = json.dumps(panel_data(), ensure_ascii=False).replace("</", "<\\/")
    html = html.replace("</head>", EXTRA_HEAD + "</head>", 1)
    html = html.replace("</main>", PANEL + "</main>", 1)
    html = html.replace("</body>", f'<script type="application/json" id="nh-data">{data}</script>\n' + SCRIPT + "</body>", 1)
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out}")
    sys.dont_write_bytecode = True
    import make_kallor
    import make_kallkatalog
    import ld
    make_kallor.main()
    make_kallkatalog.main()
    ld.main()


if __name__ == "__main__":
    main()
