"""Genererar en fristaende HTML-sida med klickbara falt per kamera.

In:  annotations.json + m_first.jpg
Ut:  contax-hyllan.html (allt inbakat, inga externa beroenden)
"""

import base64
import io
import json

from PIL import Image

ANNOTATIONS = 'annotations.json'
SOURCE_IMAGE = 'm_first.jpg'
OUTPUT = 'contax-hyllan.html'
MAX_WIDTH = 1600
JPEG_QUALITY = 85


def bild_som_data_url(path, max_width, quality):
    im = Image.open(path).convert('RGB')
    w, h = im.size
    if w > max_width:
        im = im.resize((max_width, round(h * max_width / w)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, 'JPEG', quality=quality, optimize=True)
    b64 = base64.b64encode(buf.getvalue()).decode('ascii')
    return f'data:image/jpeg;base64,{b64}', len(buf.getvalue())


def till_procent(kameror, bredd, hojd):
    for k in kameror:
        x, y, w, h = k['bbox']
        k['pct'] = {
            'left': round(100 * x / bredd, 3),
            'top': round(100 * y / hojd, 3),
            'width': round(100 * w / bredd, 3),
            'height': round(100 * h / hojd, 3),
        }
    return kameror


def main():
    data = json.load(open(ANNOTATIONS, encoding='utf-8'))
    bild = data['bild']
    kameror = till_procent(data['kameror'], bild['bredd_px'], bild['hojd_px'])

    data_url, byte_storlek = bild_som_data_url(SOURCE_IMAGE, MAX_WIDTH, JPEG_QUALITY)

    hotspots = []
    for i, k in enumerate(kameror, start=1):
        p = k['pct']
        etikett = k['modell'] or 'modell ej läsbar'
        hotspots.append(
            f'<button class="hot" data-id="{k["id"]}" '
            f'style="left:{p["left"]}%;top:{p["top"]}%;'
            f'width:{p["width"]}%;height:{p["height"]}%" '
            f'aria-label="{i}. {k["tillverkare"]} {etikett}">'
            f'<span class="nr">{i}</span></button>'
        )

    rader = []
    for i, k in enumerate(kameror, start=1):
        etikett = k['modell'] or '<em>modell ej läsbar</em>'
        rader.append(
            f'<li><button class="listrad" data-id="{k["id"]}">'
            f'<span class="listnr">{i}</span>'
            f'<span class="listtext"><strong>{k["tillverkare"]} {etikett}</strong>'
            f'<span class="listobj">{k["objektiv"]}</span></span>'
            f'<span class="flagga f-{k["modell_sakerhet"].replace(" ", "-")}">'
            f'{k["modell_sakerhet"]}</span></button></li>'
        )

    poster = {k['id']: {
        'nr': i,
        'hylla': k['hylla'],
        'pos': k['pos'],
        'tillverkare': k['tillverkare'],
        'modell': k['modell'],
        'modell_sakerhet': k['modell_sakerhet'],
        'objektiv': k['objektiv'],
        'objektiv_sakerhet': k['objektiv_sakerhet'],
        'objektiv_url': k.get('objektiv_url'),
        'objektiv_blogg': k.get('objektiv_blogg'),
        'objektiv_match': k.get('objektiv_match'),
        'objektiv_kandidater': k.get('objektiv_kandidater', []),
        'serienummer': k['serienummer'],
        'notering': k['notering'],
    } for i, k in enumerate(kameror, start=1)}

    html = MALL.format(
        titel=bild['beskrivning'],
        data_url=data_url,
        hotspots='\n            '.join(hotspots),
        rader='\n            '.join(rader),
        poster=json.dumps(poster, ensure_ascii=False),
        antal=len(kameror),
        kalla=bild['kalla'],
        fotograf=bild['fotograf'],
    )

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f'{OUTPUT}: {len(html) / 1024:.0f} kB (varav bild {byte_storlek / 1024:.0f} kB)')


MALL = """<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{titel}</title>
<style>
    :root {{
        --bg: #14161a;
        --panel: #1e2229;
        --linje: #2f353f;
        --text: #e8eaed;
        --dammpad: #9aa2ae;
        --markering: #ffc94d;
        --vald: #ff6b4a;
    }}
    * {{ box-sizing: border-box; }}
    body {{
        margin: 0;
        background: var(--bg);
        color: var(--text);
        font: 15px/1.5 -apple-system, "Segoe UI", Roboto, sans-serif;
    }}
    header {{
        padding: 20px 24px 12px;
        border-bottom: 1px solid var(--linje);
    }}
    h1 {{ margin: 0 0 4px; font-size: 19px; font-weight: 600; }}
    header p {{ margin: 0; color: var(--dammpad); font-size: 13px; }}
    .verktyg {{ margin-top: 12px; display: flex; gap: 16px; align-items: center; flex-wrap: wrap; }}
    .verktyg label {{ font-size: 13px; color: var(--dammpad); cursor: pointer; user-select: none; }}
    main {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) 360px;
        gap: 24px;
        padding: 24px;
        align-items: start;
    }}
    .scen {{ position: relative; line-height: 0; }}
    .scen img {{ width: 100%; height: auto; display: block; border-radius: 6px; }}
    .hot {{
        position: absolute;
        margin: 0;
        padding: 0;
        border: 2px solid transparent;
        border-radius: 5px;
        background: transparent;
        cursor: pointer;
        transition: background .12s, border-color .12s;
    }}
    .hot .nr {{
        position: absolute;
        top: -11px;
        left: -11px;
        width: 22px;
        height: 22px;
        border-radius: 50%;
        background: var(--markering);
        color: #1a1a1a;
        font: 600 12px/22px sans-serif;
        text-align: center;
        opacity: 0;
        transition: opacity .12s;
    }}
    .hot:hover, .hot:focus-visible {{
        border-color: var(--markering);
        background: rgba(255, 201, 77, .16);
        outline: none;
    }}
    .hot:hover .nr, .hot:focus-visible .nr {{ opacity: 1; }}
    .hot.vald {{ border-color: var(--vald); background: rgba(255, 107, 74, .2); }}
    .hot.vald .nr {{ opacity: 1; background: var(--vald); color: #fff; }}
    body.rutor .hot {{ border-color: rgba(255, 255, 255, .4); }}
    body.rutor .hot .nr {{ opacity: 1; }}

    aside {{ position: sticky; top: 24px; }}
    .kort {{
        background: var(--panel);
        border: 1px solid var(--linje);
        border-radius: 8px;
        padding: 18px;
        min-height: 190px;
    }}
    .kort .tom {{ color: var(--dammpad); font-size: 14px; margin: 0; }}
    .kort h2 {{ margin: 0 0 2px; font-size: 18px; }}
    .kort .plats {{ color: var(--dammpad); font-size: 12px; margin: 0 0 14px; }}
    dl {{ margin: 0; display: grid; grid-template-columns: 92px 1fr; gap: 6px 12px; font-size: 14px; }}
    dt {{ color: var(--dammpad); font-size: 12px; padding-top: 2px; }}
    dd {{ margin: 0; }}
    .notering {{
        margin: 14px 0 0;
        padding-top: 12px;
        border-top: 1px solid var(--linje);
        color: var(--dammpad);
        font-size: 13px;
    }}
    .flagga {{
        display: inline-block;
        padding: 1px 7px;
        border-radius: 10px;
        font-size: 11px;
        white-space: nowrap;
    }}
    .blogglank {{
        display: block;
        margin-top: 4px;
        color: #8ab4f8;
        font-size: 12px;
        text-decoration: none;
    }}
    .blogglank:hover {{ text-decoration: underline; }}
    .matchnot {{ display: block; margin-top: 4px; color: var(--dammpad); font-size: 12px; }}
    .kandidater {{ margin: 4px 0 0; padding-left: 16px; font-size: 12px; }}
    .kandidater a {{ color: #8ab4f8; text-decoration: none; }}
    .kandidater a:hover {{ text-decoration: underline; }}

    .f-avläst {{ background: #1d4429; color: #8fe0a6; }}
    .f-osäker {{ background: #4a3a12; color: #f0cd77; }}
    .f-ej-läsbar {{ background: #3a3f47; color: #b6bec9; }}

    .lista {{ margin-top: 18px; }}
    .lista h3 {{ font-size: 12px; text-transform: uppercase; letter-spacing: .06em; color: var(--dammpad); margin: 0 0 8px; }}
    .lista ol {{ list-style: none; margin: 0; padding: 0; }}
    .listrad {{
        width: 100%;
        display: flex;
        gap: 10px;
        align-items: center;
        padding: 7px 8px;
        background: transparent;
        border: 0;
        border-radius: 5px;
        color: inherit;
        font: inherit;
        text-align: left;
        cursor: pointer;
    }}
    .listrad:hover, .listrad:focus-visible {{ background: #262b33; outline: none; }}
    .listrad.vald {{ background: #33261f; }}
    .listnr {{ width: 20px; color: var(--dammpad); font-size: 12px; flex: none; }}
    .listtext {{ flex: 1; min-width: 0; }}
    .listtext strong {{ display: block; font-weight: 500; font-size: 13px; }}
    .listobj {{ display: block; color: var(--dammpad); font-size: 12px; }}

    footer {{ padding: 0 24px 32px; color: var(--dammpad); font-size: 12px; }}
    footer a {{ color: #8ab4f8; }}

    @media (max-width: 900px) {{
        main {{ grid-template-columns: 1fr; }}
        aside {{ position: static; }}
    }}
</style>
</head>
<body>
<header>
    <h1>{titel}</h1>
    <p>{antal} objekt. Klicka på en kamera i bilden eller i listan.</p>
    <div class="verktyg">
        <label><input type="checkbox" id="visaRutor"> Visa alla klickytor</label>
    </div>
</header>

<main>
    <div class="scen" id="scen">
        <img src="{data_url}" alt="{titel}">
        {hotspots}
    </div>

    <aside>
        <div class="kort" id="kort">
            <p class="tom">Ingen kamera vald.</p>
        </div>
        <div class="lista">
            <h3>Alla objekt</h3>
            <ol>
            {rader}
            </ol>
        </div>
    </aside>
</main>

<footer>
    Bild och identifieringar bygger på <a href="{kalla}">{kalla}</a>. Foto: {fotograf}.
    Fältet <em>säkerhet</em> anger om beteckningen är avläst i bilden, osäker eller inte läsbar alls.
</footer>

<script>
const POSTER = {poster};
const kort = document.getElementById('kort');
let vald = null;

function visa(id) {{
    const p = POSTER[id];
    if (!p) return;

    document.querySelectorAll('.vald').forEach(el => el.classList.remove('vald'));
    document.querySelectorAll('[data-id="' + id + '"]').forEach(el => el.classList.add('vald'));
    vald = id;

    const rader = [
        ['Tillverkare', p.tillverkare],
        ['Modell', p.modell || '<em>ej läsbar i bilden</em>'],
        ['Objektiv', objektivfalt(p)],
        ['Serienr', p.serienummer || '\\u2014'],
        ['Säkerhet', flagga(p.modell_sakerhet)]
    ];

    kort.innerHTML =
        '<h2>' + p.tillverkare + ' ' + (p.modell || '') + '</h2>' +
        '<p class="plats">Nr ' + p.nr + ' \\u00b7 hyllplan ' + p.hylla + ', position ' + p.pos + '</p>' +
        '<dl>' + rader.map(r => '<dt>' + r[0] + '</dt><dd>' + r[1] + '</dd>').join('') + '</dl>' +
        (p.notering ? '<p class="notering">' + p.notering + '</p>' : '');
}}

function flagga(v) {{
    return '<span class="flagga f-' + v.replace(/ /g, '-') + '">' + v + '</span>';
}}

function objektivfalt(p) {{
    if (p.objektiv_url) {{
        return p.objektiv + '<a class="blogglank" href="' + p.objektiv_url +
            '" target="_blank" rel="noopener">' + p.objektiv_blogg + ' \\u2197</a>';
    }}
    if (!p.objektiv_kandidater.length) {{
        return p.objektiv + '<span class="matchnot">Ingen motsvarighet i bloggindexet.</span>';
    }}
    const lista = p.objektiv_kandidater.map(k =>
        '<li><a href="' + k.url + '" target="_blank" rel="noopener">' + k.namn + '</a></li>'
    ).join('');
    return p.objektiv +
        '<span class="matchnot">Ej entydig match (' + p.objektiv_match + '). Kandidater:</span>' +
        '<ul class="kandidater">' + lista + '</ul>';
}}

document.addEventListener('click', e => {{
    const knapp = e.target.closest('[data-id]');
    if (knapp) visa(knapp.dataset.id);
}});

document.getElementById('visaRutor').addEventListener('change', e => {{
    document.body.classList.toggle('rutor', e.target.checked);
}});

document.addEventListener('keydown', e => {{
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const ids = Object.keys(POSTER);
    const i = ids.indexOf(vald);
    const nasta = e.key === 'ArrowRight' ? i + 1 : i - 1;
    visa(ids[(nasta + ids.length) % ids.length]);
}});
</script>
</body>
</html>
"""


if __name__ == '__main__':
    main()
