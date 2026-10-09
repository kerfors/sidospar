# Kameramuseet: peka på en kamera i hyllan

Kerstin Forsberg · augusti 2026, publicerad 9 oktober 2026 · [Till Sidospår](../)

**[Öppna den klickbara hyllan](contax-hyllan.html)**

## Sammanfattning

CyberPhoto har ett kameramuseum på sin blogg Captains log, med översiktsbilder av skåp fulla med kameror. Man vill peka på en kamera och få veta vad den är. Det här är ett experiment som gör det för den första bilden, Contax-skåpet.

- **18 objekt** är utpekade i bilden. Klick i bilden eller i listan ger tillverkare, modell, objektiv, serienummer och en flagga för hur säker uppgiften är.
- **Avläsningarna och koden är gjorda av Claude**, Anthropics AI-modell. Mitt bidrag är upplägget och besluten om hur osäkerhet ska hanteras.
- **Ingen sakkunnig har granskat identifieringarna.** Jag kan inte tillräckligt om kameror för att göra det själv. Behandla ingen uppgift som fastställd.
- **Bilden tillhör Thomas Lövgren, CyberPhoto**, och används här med hans tillstånd.

## Bakgrund

Sidan jag utgick från är [Kameramuseum](https://www.cyberphoto.se/captains-log/kameramuseum) i Captains log. Min kameraintresserade man satt och tittade på den, och jag blev nyfiken på om det gick att göra översiktsbilderna klickbara.

Jag arbetar med informationsarkitektur och kliniska datastandarder. Det här är en helt annan sorts data, och det var skälet att prova.

Experimentet gjordes i augusti 2026 i ett samtal med Claude. Jag skickade resultatet till Thomas Lövgren den 19 augusti. Filerna på den här sidan byggdes om den 8 oktober 2026 från samma underlag.

## Vem gjorde vad

| Del | Gjord av |
| --- | --- |
| Idén, valet av bild, upplägget med data skilt från sidan | Kerstin |
| Beslutet att osäkerhet ska vara ett eget fält, och att modellen inte får gissa | Kerstin |
| Idén att stämma av objektiven mot bloggens egen objektivlista | Kerstin |
| Avläsning av text i bilden, klickytornas läge | Claude |
| All kod | Claude |
| Sakkunnig granskning av de 18 identifieringarna | Inte gjord |

## Hur det är byggt

Det som är värt något är datat, inte sidan. Varje kamera är en post i [annotations.json](annotations.json), med rutans läge i bilden och de avlästa uppgifterna. Den klickbara sidan är genererad ur den filen. Samma data kan lika gärna visas som kortgalleri eller tabell.

Två val i datat:

- **Osäkerhet är ett eget fält.** Varje uppgift har en flagga: *avläst*, *osäker* eller *ej läsbar*. Går texten inte att läsa står det så, i stället för en kvalificerad gissning.
- **Modell och objektiv har var sin flagga.** Objektivtexten går nästan alltid att läsa i bilden. Kroppens beteckning är ofta skymd. Med en gemensam flagga hade flera poster fått sämre betyg än de förtjänar.

## Utfall

### Modellbeteckningar

| Flagga | Antal av 18 |
| --- | --- |
| avläst | 8 |
| ej läsbar | 8 |
| osäker | 2 |

På flera Contax-kroppar skyms modellnamnet av objektivet i den här fotovinkeln. De två som står som osäkra är identifierade som Contax Preview på kroppens form, utan någon synlig modelltext.

För objektiven är 16 av 18 avlästa och 2 osäkra.

### Objektiven mot Captains log

Objektivbeteckningarna matchades mot objektivlistan i Captains log. Den matchningen är vanlig regelkod och ingen AI. Den jämför brännvidd, bländare och serienamn. Bara entydiga träffar länkas.

Bloggindexet har 462 länkar, varav 332 är objektiv med brännvidd i namnet.

| Utfall | Antal av 18 |
| --- | --- |
| Entydig träff, länkad till bloggsidan | 10 |
| Trolig träff, indexet saknar serienamn | 3 |
| Brännvidden finns men bländartalet skiljer | 2 |
| Flera kandidater, går inte att skilja på bilden | 2 |
| Ingen motsvarighet i indexet | 1 |

Två iakttagelser:

- **Två objektiv saknas i indexet.** Carl Zeiss Distagon 28 mm f/2 och Yashica DSB 28 mm f/2,8 finns inte med i listan. Det kan vara en lucka i listan eller ett fel i avläsningen. Det är inte kontrollerat.
- **Kravet på entydighet stoppade en felaktig länk.** Canomatic M70 har ett fast objektiv, 40 mm f/2,8. Det matchade indexposten ”Canon 40mm f/2,8 från A35F” på märke, brännvidd och bländare, men är ett annat objektiv. Posten länkas inte.

Hela rapporten finns i [matchning.csv](matchning.csv).

### De 18 posterna

Tabellen är genererad ur annotations.json. Serienummer och noteringar finns i datat och i den klickbara sidan.

| Nr | Id | Tillverkare | Modell | Modell, flagga | Objektiv | Matchning mot bloggen |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `h1-1` | Contax | RTS | avläst | Yashica ML 50 mm f/1,9 | exakt |
| 2 | `h1-2` | Contax | RTS | avläst | Carl Zeiss Sonnar T* 2,8/85 | trolig - indexet saknar serienamn |
| 3 | `h1-3` | Contax | – | ej läsbar | Carl Zeiss Sonnar T* 3,5/100 | exakt |
| 4 | `h1-4` | Contax | – | ej läsbar | Carl Zeiss Distagon T* 2/28 | brännvidd finns men bländartalet skiljer |
| 5 | `h2-1` | Contax | 167MT | avläst | Yashica ML 35 mm f/2,8 | exakt |
| 6 | `h2-2` | Contax | RTS | avläst | Carl Zeiss Planar T* 1,4/50 | exakt |
| 7 | `h2-3` | Contax | – | ej läsbar | Carl Zeiss Tessar T* 2,8/45 | exakt |
| 8 | `h3-1` | Contax | – | ej läsbar | Yashica ML Zoom 42-75 mm f/3,5-4,5 | brännvidd finns men bländartalet skiljer |
| 9 | `h3-2` | Contax | RTS (guldpläterad specialutgåva) | avläst | Carl Zeiss Planar T* 1,4/50, guldutförande | exakt |
| 10 | `h3-3` | Contax | – | ej läsbar | Carl Zeiss Planar T* 1,7/50 | exakt |
| 11 | `h4-1` | Contax | – | ej läsbar | Yashica ML Macro 55 mm f/4 | exakt |
| 12 | `h4-2` | Contax | RTS | avläst | Yashica DSB 28 mm f/2,8 | ingen träff i indexet |
| 13 | `h4-3` | Contax | Aria | avläst | Carl Zeiss Planar T* 1,7/50 | exakt |
| 14 | `h5-1` | Contax | – | ej läsbar | Yashica ML 50 mm f/2 | exakt |
| 15 | `h5-2` | Contax | – | ej läsbar | Yashica ML 50 mm, bländartal ej läsbart | tvetydig - flera kandidater |
| 16 | `h5-3` | Canon | Canomatic M70 | avläst | Canon Lens 40 mm f/2,8 (fast) | trolig - indexet saknar serienamn |
| 17 | `h5-4` | Contax | Preview | osäker | Carl Zeiss Planar, brännvidd ej läsbar | tvetydig - brännvidd ej avläst |
| 18 | `h5-5` | Contax | Preview | osäker | Carl Zeiss Sonnar 2,8/85 | trolig - indexet saknar serienamn |

Numren följer ordningen i datat. Id är stabilt (`h3-2` är hyllplan 3, position 2) och är det som ska användas vid hänvisning.

## Begränsningar

- **Ogranskat.** Allt ovan är avläst av en AI-modell ur ett fotografi. Thomas Lövgren har sagt att han ska titta på identifieringarna, men har inte gjort det än (8 oktober 2026).
- **En bild av flera.** Bara Contax-skåpet är gjort. Metoden går att använda på resten av museet, men det är ett större arbete.
- **Rektanglar, inte konturer.** Varje objekt har en rektangulär klickyta. Canomatic M70 står bakom två andra kameror och har en klickyta som bara täcker den fria delen.
- **Bloggindexet är en ögonblicksbild.** Det hämtades den 8 oktober 2026 och följer inte med om bloggen ändras.

## Filer

| Fil | Innehåll |
| --- | --- |
| [contax-hyllan.html](contax-hyllan.html) | Den klickbara sidan. Bilden ligger inbakad i filen |
| [annotations.json](annotations.json) | Datat, en post per objekt |
| [matchning.csv](matchning.csv) | Rapport från objektivmatchningen |
| [generate.py](generate.py) | Bygger sidan ur datat. Kräver Pillow och källbilden som `m_first.jpg`, som inte ligger här |
| [matcha_blogg.py](matcha_blogg.py) | Matchar objektiven mot bloggindexet |
| [bloggindex.json](bloggindex.json) | Länkarna under Captains log som matchningen körs mot |

## Bild och tillstånd

Översiktsbilden (DSCF3157) är fotograferad av Thomas Lövgren och kommer från [Kameramuseum](https://www.cyberphoto.se/captains-log/kameramuseum) i CyberPhotos Captains log. Den publiceras här med hans tillstånd, givet per e-post den 8 oktober 2026.

Objektivlänkarna i den klickbara sidan går till respektive sida i Captains log.
