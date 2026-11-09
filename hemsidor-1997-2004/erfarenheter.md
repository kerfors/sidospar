# Så grävde vi fram sidorna

Kerstin Forsberg · november 2026 · [Till Mina hemsidor från Viktoriainstitutet](./)

> **Faktaruta: Wayback Machine**
>
> Wayback Machine är webbarkivet hos Internet Archive, en ideell organisation i San Francisco som Brewster Kahle grundade 1996. Samma år började arkivet samla in webbsidor automatiskt, och sedan 2001 kan vem som helst bläddra i det. I oktober 2025 passerade arkivet en biljon sparade webbsidor.
>
> Man skriver in en webbadress och får en kalender med de dagar då sidan sparades. Det går inte att söka på innehåll eller namn, bara på adress.
>
> [web.archive.org](https://web.archive.org/)

## Arbetsgången

Arbetet gjordes en söndagseftermiddag och kväll, i ett samtal med Claude (Anthropic):

1. Sökning på öppna webben efter spår av hemsidan. Det jag mindes ("Netguide") ledde ingenstans. Det som till slut gav träff var ordet *extranet*: en länksida vid University of the West of England länkade till min sida på Viktoria, och där stod e-postadressen kerfor@netg.se.
2. Med adresserna kända listades alla sparade kopior i Wayback Machine. Claude skrev skripten, och jag körde dem på min egen dator, eftersom Claudes arbetsmiljö inte nådde arkivet.
3. Kopian byggdes, granskades sida för sida och rättades i flera omgångar.

Skripten och rådata ligger på GitHub: [fetch.py](https://github.com/kerfors/sidospar/blob/main/hemsidor-1997-2004/fetch.py) hämtar sidorna, [generate.py](https://github.com/kerfors/sidospar/blob/main/hemsidor-1997-2004/generate.py) bygger kopian och sidan med tabellen, och [data/](https://github.com/kerfors/sidospar/tree/main/hemsidor-1997-2004/data) innehåller de hämtade filerna och en förteckning över alla sparade versioner.

## Vad vi lärde oss om att gräva fram gamla webbsidor

- **Arkivet söks på adress, inte på namn.** Wayback Machine går inte att söka i på innehåll, och vanliga sökmotorer indexerar inte arkivet. Utan en adress kommer man ingenstans. Vägen in var någon annans sida som länkade till min.
- **Det man minns är inte alltid rätt.** Leverantören hette Netg, inte Netguide. Det var sidans eget innehåll, e-postadressen, som visade det.
- **Senast sparad är inte alltid bäst.** När sidorna flyttade till Viktoria ersatte jag de gamla med en flyttlapp, och det är den arkivet sparade sist. Den riktiga sidan fanns i en äldre kopia.
- **Förteckningen och arkivet stämmer inte alltid.** Ibland säger förteckningen att en kopia finns, men arkivet svarar att den saknas. Då hjälper det att pröva äldre kopior av samma adress.
- **Två platser är bättre än en.** Bilder som aldrig sparades på Viktoria fanns kvar från netg, eftersom mappstrukturen var densamma.
- **Gamla sidor behöver lite hjälp för att visas rätt.** Teckenkodningen var Windows-standard från 1990-talet, så å, ä och ö måste räknas om. Sidor sparade från Word hade länkar med bakåtsnedstreck.
- **Det tidigaste är borta.** Arkivet började samla 1996, och mina sidor från 1997 och början av 1998 sparades aldrig. Den äldsta kopian är från december 1998.
