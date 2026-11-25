# Testverslag prototype 0.1
Debian GNU/Linux 13 x86-64, CPython 3.12.14, Vosk 0.3.45, twee echte gedownloade modellen. Beide scripts zijn ingesproken met twee Nederlandse synthese-stemmen (eSpeak 1.48). De WAV is verliesvrij gecomprimeerd in tests/audio. tests/benchmark.py reproduceert de synthese en rapporteert herkenning en sprekerlabels. De tests bevatten uitsluitend fictieve tekst.

| Simulatie | Audio | ASR + sprekervectoren incl. laden | Waarneming |
|---|---:|---:|---|
| Voorkeur voor papier | 18,67 s | 9,60 s | 5 beurten, A/B/A/B/A correct. ASR miste o.a. “Voor thuis”. |
| Wandeling | 15,09 s | 7,99 s | 5 segmenten voor 4 beurten. |

De wandeling leverde **5 segmenten voor 4 beurten** op: de begroeting werd apart herkend als “de” met onbekende spreker. De volgende vier labels A/B/A/B waren juist. Piek-RSS van het Python-proces voor beide analyses samen was 320764 KiB (313 MiB). Geen meting van de gehele Windows-app. Bij korte synthetische zinnen zijn herkenningsfouten aanzienlijk.

De drie geautomatiseerde regeltests slagen. Op het gecontroleerde eerste script verwijzen de kaarten naar beurten 1+2, 2+3 en 2+5. Bij de wandeling zijn drie criteria niet te beoordelen. Het aparte voorbeeld met “Dan schrijven we ze op” levert alleen een reactiekaart. Een onbekende beurt-ID wordt geweigerd. Deze regeltests valideren geen ASR.

De Windows-workflow bouwt een installer, test installatie en vensterstart, en test echte modellen via de WAV-import in de geïnstalleerde desktopapp. tests/accept.py gebruikt referentietekst voor de correctiestap en onderschept de luidsprekeruitvoer om de samples te vergelijken. Een succesvolle CI-uitvoering is geen microfoon- of luistertest. Probeer op de HU-laptop offline installatie met beperkte rechten, werkelijke twee stemmen en overlap, microfoonkeuze en -niveau, pauze/hervatten, fragmentweergave, afsluiten en starten na geforceerde beëindiging. Noteer ook duur, verwerkingstijd en piekwerkset van de geïnstalleerde toepassing bij een langer gesprek.

## Windows-acceptatie geslaagd op 25 november 2026
[Volledige Windows-run en installer](https://github.com/jaapjansen1977/inclusieve_coach/actions/runs/45587136993), geteste bronversie e537e8a. GitHub-hosted Windows Server 2022 x64, gebundelde Python 3.11.9. Installatie per gebruiker en vensterstart zijn geslaagd. De geïnstalleerde exe doorliep beide scenario’s met lokaal geïnstalleerde echte modellen en een Windows Firewall-regel die uitgaand verkeer voor de exe blokkeerde.

| Scenario | Audio | Verwerking inclusief modellen laden | Uitkomst na transcriptcontrole |
|---|---:|---:|---|
| Uitleg op papier | 18,7 s | 8,2 s | Drie kaarten. De automatische A/B-indeling klopte voor de vijf beurten. |
| Wandeling | 15,1 s | 6,6 s | Alle drie de criteria niet te beoordelen. |

Gemeten piekwerkset van de geïnstalleerde exe tijdens beide scenario’s samen: 353533952 bytes (337 MiB). De test wees de rollen toe aan de hand van de bekende spreektijden en corrigeerde in scenario 1 de tekst naar het fictieve script. Daarna zijn alle zes fragmentknoppen aangeroepen. De weergegeven spreker, het letterlijke citaat, de start- en eindtijd en de doorgegeven audiosamples klopten. Dit bewijst de koppeling aan het gecontroleerde transcript. De microfoon, hoorbare luidsprekerweergave en Windows 10 van de HU zijn nog niet beproefd.
