"""Matchar avlasta objektivbeteckningar mot CyberPhotos bloggindex.

Matchning sker pa strukturerade falt (brannvidd, blandare, serienamn), inte pa
fritextlikhet. Varje traff far en klassificering som gar att granska manuellt.

In:  annotations.json, bloggindex.json
Ut:  matchning.csv (rapport) + uppdaterad annotations.json med objektiv_url
"""

import csv
import json
import re

ANNOTATIONS = 'annotations.json'
INDEX = 'bloggindex.json'
RAPPORT = 'matchning.csv'
BAS = 'https://www.cyberphoto.se'

SERIER = {
    'planar', 'sonnar', 'tessar', 'distagon', 'biogon', 'flektogon',
    'skoparex', 'pancolar', 'biotar', 'macro', 'zoom', 'ml', 'dsb', 'lens',
}

# Ord som inte sager nagot om identiteten och darfor inte far bara en match
BRUS = {'mm', 'f', 'till', 'och', 'med', 'fran', 'från', 'fast', 'm', 'c', 't'}


def parse(text):
    """Plockar ut brannvidd(er) och blandare ur en objektivbeteckning."""
    t = text.lower()

    zeiss = re.search(r'\b(\d+[,.]?\d*)\s*/\s*(\d+)\b', t)
    if zeiss:
        blandare = [zeiss.group(1).replace('.', ',')]
        brannvidd = [zeiss.group(2)]
    else:
        brannvidd = re.findall(r'(\d+)\s*-\s*(\d+)\s*mm', t)
        if brannvidd:
            brannvidd = list(brannvidd[0])
        else:
            brannvidd = re.findall(r'(\d+)\s*mm', t)
        blandare = re.findall(r'f/\s*(\d+[,.]?\d*)', t)
        blandare = [b.replace('.', ',') for b in blandare]

    ord_ = set(re.findall(r'[a-zåäö]+', t))
    return {
        'brannvidd': sorted(brannvidd),
        'blandare': sorted(blandare),
        'serie': ord_ & SERIER,
        'ord': ord_,
    }


def klassificera(avlast, kandidater):
    """Returnerar (status, traffar) for en avlast beteckning."""
    a = parse(avlast)

    if not a['brannvidd']:
        mojliga = [k for k in kandidater
                   if parse(k['namn'])['ord'] & a['ord'] & SERIER
                   and (a['ord'] & parse(k['namn'])['ord']) - SERIER - BRUS]
        return 'tvetydig - brännvidd ej avläst', mojliga

    traffar = []
    for k in kandidater:
        b = parse(k['namn'])
        if b['brannvidd'] != a['brannvidd']:
            continue
        # Market maste finnas i bada (carl/zeiss, yashica, canon ...)
        if not (a['ord'] & b['ord']) - SERIER - BRUS:
            continue
        traffar.append((k, b))

    if not traffar:
        return 'ingen träff i indexet', []

    if a['blandare']:
        exakt = [k for k, b in traffar if b['blandare'] == a['blandare']]
        if not exakt:
            return 'brännvidd finns men bländartalet skiljer', [k for k, _ in traffar]
        traffar = [(k, parse(k['namn'])) for k in exakt]

    if a['serie']:
        med_serie = [k for k, b in traffar if b['serie'] & a['serie']]
        utan_serie = [k for k, b in traffar if not b['serie']]
        if len(med_serie) == 1:
            return 'exakt', med_serie
        if not med_serie and len(utan_serie) == 1:
            return 'trolig - indexet saknar serienamn', utan_serie
        if len(med_serie) > 1:
            return 'tvetydig - flera kandidater', med_serie

    kvar = [k for k, _ in traffar]
    if len(kvar) == 1:
        return 'exakt', kvar
    return 'tvetydig - flera kandidater', kvar


def main():
    data = json.load(open(ANNOTATIONS, encoding='utf-8'))
    index = json.load(open(INDEX, encoding='utf-8'))
    # Artiklar utan objektivnamn filtreras bort
    kandidater = [i for i in index if re.search(r'\d+\s*mm|\d+-\d+mm', i['namn'])]

    rader = []
    for k in data['kameror']:
        status, traffar = klassificera(k['objektiv'], kandidater)
        k['objektiv_match'] = status
        k['objektiv_kandidater'] = [
            {'namn': t['namn'], 'url': BAS + t['href']} for t in traffar
        ]
        # Endast entydiga traffar lankas automatiskt. Ovriga kraver granskning.
        if status == 'exakt' and len(traffar) == 1:
            k['objektiv_url'] = BAS + traffar[0]['href']
            k['objektiv_blogg'] = traffar[0]['namn']
        else:
            k['objektiv_url'] = None
            k['objektiv_blogg'] = None
        rader.append({
            'id': k['id'],
            'avläst': k['objektiv'],
            'status': status,
            'kandidater': ' | '.join(t['namn'] for t in traffar) or '-',
        })

    json.dump(data, open(ANNOTATIONS, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=4)

    with open(RAPPORT, 'w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=['id', 'avläst', 'status', 'kandidater'])
        w.writeheader()
        w.writerows(rader)

    print(f'{len(kandidater)} objektiv i bloggindexet\n')
    for r in rader:
        print(f'{r["id"]:6} {r["status"]:38} {r["avläst"]}')
        if r['status'] != 'exakt' and r['kandidater'] != '-':
            print(f'{"":45} → {r["kandidater"]}')


if __name__ == '__main__':
    main()
