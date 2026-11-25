# Inclusieve Coach 0.1
Lokale Windows-desktopapp voor het nabespreken van Nederlandstalige simulatieconsulten. De drie demonstratiecriteria staan met hun patronen en reflectievragen in rubric.json. De versie is bedoeld om samen met cliënten en therapeuten te beproeven.

## Installeren zonder internet op de doellaptop
Neem InclusieveCoach-Setup.exe uit het uitgepakte GitHub Actions-artifact InclusieveCoach-Windows-x64 en de volgende twee modelarchieven mee. Download de archieven eenmalig op een apparaat met internet van [Vosk Models](https://alphacephei.com/vosk/models). Controleer de SHA-256 van de oorspronkelijke zipbestanden.

| Archief | Omvang volgens uitgever | SHA-256 |
|---|---:|---|
| vosk-model-small-nl-0.22.zip | 39 MB | 039811c3b829de64e4f123a9f684a53784005b212a346ac0b899dc7efce2ed0a |
| vosk-model-spk-0.4.zip | 13 MB | a74d8f51144484813e16af689bb0f916b7a111e2347f467c4933c1166097b5a7 |

Installeer de exe onder je eigen Windows-account. Pak beide archieven uit onder %LOCALAPPDATA%\InclusieveCoach\modellen. De twee modelmappen moeten direct onder modellen staan. Een voorbereide lokale map werkt ook: klik bij elke start op **Kies lokale modelmap** en selecteer de bovenliggende map. Gebruik geen netwerkschijf. Start de app via het startmenu. HU-applicatiebeheer kan een uitzondering voor de ongesigneerde installer vereisen.

## Een gesprek terugkijken
1. Klik op **Microfoon instellen**, kies de ingang en spreek kort. Controleer de niveaubalk. Start de opname. Pauzes worden uit de tijdlijn geknipt. Klik na afloop op **Gesprek beëindigen**. Via **WAV importeren** kun je dezelfde oefenopname opnieuw gebruiken.
2. Beluister beurten, wijs A en B aan hun rollen toe en corrigeer losse beurtlabels en tekst. Een vraagteken vraagt om handmatige toewijzing. Tijd is gerekend vanaf het begin van de bewaarde audio. Spreek voor de demonstratie om de beurt en laat een korte stilte vallen tussen beurten.
3. Bevestig de transcriptcontrole. Klik bij ieder citaat op de afspeelknop. De tekst komt rechtstreeks uit de gecontroleerde beurt. Via **Terug naar transcript** kun je een correctie aanbrengen en de kaarten opnieuw berekenen.
4. Klik op **Sessie afsluiten en gegevens verwijderen**. Een geïmporteerd bronbestand blijft bij de gebruiker.

## Componenten en vervanging
Vosk API 0.3.45 (Apache-2.0) verwerkt audio in blokken op de CPU. Het Nederlandse kleine model 0.22 beperkt geheugen en rekentijd. Spreker-model 0.4 levert per spraaksegment een vector. Twee clusters op basis van cosinusgelijkenis geven A/B, zonder stemregistratie vooraf. Beide modellen zijn Apache-2.0: behoud licenties, auteursrechtvermeldingen en toepasselijke NOTICE bij doorleveren en vermeld wijzigingen. Modelgewichten worden apart geleverd. Versies en bron staan hierboven. De functie transcribe in engine.py is het vervangpunt en geeft Turn-objecten in samples op 16 kHz terug.

De tekstanalyse gebruikt Python re (CPython 3.11.9, PSF-licentie) en een eigen regelsysteem 0.1 met leesbare Nederlandse patronen. Extra modeldownload 0 MB. evidence geeft uitsluitend beurt-ID's terug. references controleert de verwijzingen vóór weergave. Niets genereert vrije tekst over personen. Het regelsysteem kan ontkenningen en ironie verkeerd duiden of parafrases missen. Een ontbrekende match levert ‘Niet te beoordelen uit dit gesprek’ op. Een aanpassing kan al voor de opname zijn uitgevoerd. Er is geen totaalscore. Een voorstel op zichzelf zegt niets over de geschiktheid voor de cliënt.

## Gegevens en beperkingen
Microfoon → werkgeheugen → mono 16-bit PCM op 16 kHz → ASR en tijdelijke sprekervectoren → gecontroleerde beurten → kaarten en lokaal afspelen. WAV-import leest alleen het gekozen bronbestand. Bewerkingen, vectoren, audio en feedback worden niet door de app naar schijf geschreven. Er is geen sessiemap om na een crash op te schonen. De app wist referenties bij sessie-einde, Windows geeft procesgeheugen terug bij afsluiten. Dit is geen gegarandeerd overschrijven van geheugen. Windows-wisselbestand, slaapstand, crashdumps, endpointsoftware, bronbestanden en synchronisatie van door de gebruiker gekozen mappen vragen afzonderlijke beoordeling. Geen account, netwerkdienst, telemetrie of inhoudelijke applicatielogs. De modelkeuze is tijdelijk. Installatiebestanden staan onder %LOCALAPPDATA%\Programs\InclusieveCoach.

Gebruik voorlopig korte, fictieve gesprekken. Geheugengebruik groeit met de opnameduur. De segmentgrenzen volgen spraakpauzes. Bij doorpraten of overlap kunnen twee sprekers in één beurt terechtkomen. Deze versie kan tekst en rollen corrigeren, maar geen beurt splitsen of grenzen verschuiven. Weinig stemmateriaal of twee gelijkende stemmen maken de verdeling onzeker. Controleer de fragmenten voordat je de kaarten interpreteert.

## Bouwen en testen
Op Windows x64 met Python 3.11.9 x64, Inno Setup 6 in de standaardlocatie en internet: voer build.ps1 uit in PowerShell. De build installeert de ontwikkelafhankelijkheden, draait de tests, bundelt Python, Tcl/Tk, PortAudio en Vosk en maakt output/ inclusieve installer (InclusieveCoach-Setup.exe). De eindgebruiker heeft geen Python nodig. De workflow Windows installer voert dit uit op windows-2022. Dit is een herhaalbaar bouwrecept, geen bit-identieke build. Zie tests/scenarios.json en TESTVERSLAG.md voor acceptatie.
