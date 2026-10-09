# Kameramuseet: peka på en kamera i hyllan

Kerstin Forsberg · augusti 2026, publicerad 9 oktober 2026 · [Till Sidospår](../)

CyberPhoto har ett [kameramuseum](https://www.cyberphoto.se/captains-log/kameramuseum) på sin blogg Captains log, med översiktsbilder av skåp fulla med kameror. Man vill peka på en kamera och få veta vad den är. Det här är ett experiment som gör det för den första bilden, Contax-skåpet.

Klicka på en kamera i bilden eller i listan. Avläsningarna är gjorda av en AI-modell och är inte granskade av någon sakkunnig.

<iframe src="contax-hyllan.html" title="Klickbar bild av Contax-skåpet" loading="lazy" style="width: 100%; height: 820px; border: 1px solid #d0d7de; border-radius: 6px;"></iframe>

[Öppna hyllan i ett eget fönster](contax-hyllan.html)

## Om experimentet

Min kameraintresserade man satt och tittade på kameramuseet, och jag blev nyfiken på om det gick att göra översiktsbilderna klickbara. Jag arbetar med informationsarkitektur och kliniska datastandarder, så det här var en helt annan sorts data att prova på.

Experimentet gjordes i augusti 2026 i ett samtal med Claude, Anthropics AI-modell. Avläsningarna av bilden och all kod är gjorda av Claude. Mitt bidrag är upplägget och besluten om hur osäkerhet ska hanteras. Jag kan inte tillräckligt om kameror för att granska de 18 identifieringarna själv.

Två val bär upplägget:

- **Datat ligger skilt från sidan.** Varje kamera är en post i [annotations.json](annotations.json). Den klickbara sidan är genererad ur den filen.
- **Osäkerhet är ett eget fält.** Varje uppgift är märkt *avläst*, *osäker* eller *ej läsbar*. Modellen fick inte gissa. Modell och objektiv har var sin flagga, eftersom objektivtexten oftast går att läsa medan kroppens beteckning ofta är skymd.

## Utfall

Av 18 modellbeteckningar är 8 avlästa, 8 ej läsbara och 2 osäkra. Av objektiven är 16 avlästa och 2 osäkra.

Objektiven matchades sedan mot objektivlistan i Captains log, med vanlig regelkod och ingen AI. Bara entydiga träffar länkas till bloggen.

| Utfall | Antal av 18 |
| --- | --- |
| Entydig träff, länkad till bloggsidan | 10 |
| Trolig träff, indexet saknar serienamn | 3 |
| Brännvidden finns men bländartalet skiljer | 2 |
| Flera kandidater, går inte att skilja på bilden | 2 |
| Ingen motsvarighet i indexet | 1 |

Bara Contax-skåpet är gjort. Metoden går att använda på resten av museet, men det är ett större arbete.

## Filer

- [annotations.json](annotations.json), datat
- [matchning.csv](matchning.csv), rapport från objektivmatchningen
- [generate.py](generate.py), bygger sidan ur datat (källbilden ligger inte här)
- [matcha_blogg.py](matcha_blogg.py) och [bloggindex.json](bloggindex.json), matchningen mot Captains log

## Bild och tillstånd

Översiktsbilden är fotograferad av Thomas Lövgren och kommer från [Kameramuseum](https://www.cyberphoto.se/captains-log/kameramuseum) i CyberPhotos Captains log. Den publiceras här med hans tillstånd, givet per e-post den 8 oktober 2026.
