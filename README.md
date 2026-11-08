# Split gegen Füllen bis voll – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-split-gegen-fuellen-demo.streamlit.app/)** -->

Drittes Stück der **Tourenbildung**-Linie in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“ (Verfahren: **Riesentour und Split**, ein Verfahren mit wachsendem Beispiel). Stück 1 ([riesentour-split-demo](https://github.com/sebastian-hanisch/riesentour-split-demo)) zeigt, dass eine Reihenfolge aller Kunden genügt, weil der **Split** sie optimal in Routen zerlegt; Stück 2 ([riesentouren-erzeugen-demo](https://github.com/sebastian-hanisch/riesentouren-erzeugen-demo)) baut solche Reihenfolgen. Dieses Stück vergleicht den Split auf derselben Reihenfolge mit **„Füllen bis voll“** (Next-Fit) und fragt, was eine **Flottengrenze** kostet.

## Kernfrage

Was bringt es, eine Reihenfolge optimal zu zerlegen, statt eine neue Route zu beginnen, sobald der nächste Kunde nicht mehr passt? Die Demo zerlegt dieselbe Reihenfolge auf drei Arten („Füllen bis voll“ vorwärts und rückwärts gelesen, Split), rechnet den Split mit höchstens B Routen samt exaktem Optimum mit derselben Grenze, zeigt die Wirkung der Leserichtung und der Gleichstandsregel und fasst Zerlegungen von Reihenfolgen bis 100 Kunden in Bändern zusammen.

## Modell

Wie in Stück 1 und 2: ein Depot, n Kunden mit ganzzahliger Nachfrage, gleiche Fahrzeuge der Kapazität Q, euklidische Entfernungen. Die Kapazität folgt aus der **Auslastung**: aufgerundet Gesamtnachfrage geteilt durch (Zielroutenzahl mal Auslastung), mindestens die größte Nachfrage. **Füllen bis voll:** neue Route, sobald der nächste Kunde nicht mehr passt; die Zahl g der Routen ist die kleinste, in die die Reihenfolge überhaupt passt. **Split mit Flottengrenze:** kürzester Weg mit höchstens B Bögen im Hilfsgraphen, eine Schicht je Route; endlich genau für B ≥ g. Formeln, Lesehilfe und das Austauschargument für g stehen im 📐-Expander der App.

## Methodik

- **Kern** (`sgf_algorithm.py`): aus Stück 1 und 2 kopiert und umbenannt; neu sind `fill_until_full`, `split_by_fleet` (alle B bis zu einer Höchstzahl in einem Durchgang), `exact_fleet_costs` (Optimum mit höchstens B Routen über Teilmengen, eine Schicht je Route).
- **Reihenfolgen** (`sgf_construct.py`): kürzeste Rundreise, Nächster Nachbar, fernstes Einfügen, Einfügen nach Split (mit wählbarer Gleichstandsregel), Zufall, Optimum hintereinander; die Erzeuger sind aus Stück 2.
- **Vier Experimente:** dieselbe Reihenfolge in drei Zerlegungen; die Flottengrenze (Regler B, Kurve, exaktes Optimum, Preis der Mindestflotte); Gleichstand und Leserichtung; Bänder über feste Instanzen.
- **Bänder** (`sgf_bands.json`, erzeugt von `generate_precomputed.py`): n = 12 mit 20 Instanzen je Zelle (80 gesamt), n = 25, 50, 100 mit 8 je Zelle (32 gesamt); vier Zellen (Kunden zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke); Zielroutenzahl 3; Auslastung 60, 75, 90, 98 %; Reihenfolgen fernstes Einfügen, Nächster Nachbar, Zufall und (bis n = 50) Einfügen nach Split. Dazu der **Preis der Mindestflotte** im Optimum (n = 12, exakt, Auslastung 90, 95, 98, 100 %, 80 Instanzen).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen sind Messungen an festen Seeds (Mehrkosten in Prozent), nachgerechnet in `tests/test_claims.py`, `tests/test_bands.py`, `tests/test_algorithm.py` und `tests/test_oracle_split_gegen_fuellen.py`. Die Bänder für n = 12, 25 und 50 wurden in der Planung mit eigenen Skripten unabhängig vorgerechnet und stimmen überein.

| Frage | Befund |
|---|---|
| Ist „Füllen bis voll“ optimal in der Routenzahl? | Ja: Es ergibt die kleinste Zahl aufeinanderfolgender Routen, in die eine Reihenfolge passt; geprüft an 288 Reihenfolgen (n = 7) gegen die Aufzählung aller Schnittmengen. Mit weniger Routen ist die Reihenfolge nicht zerlegbar. Dieselbe Zahl gilt rückwärts gelesen |
| Gilt die Dominanz mit Flottengrenze? | Ja: Das Minimum von Split mit höchstens B Routen über alle Reihenfolgen ist gleich dem exakten Optimum mit höchstens B Routen (54 Fälle, n = 6, B von der Mindestroutenzahl bis +2) |
| „Füllen bis voll“ über Split, n = 12, Auslastung 90 %, 80 Instanzen (vorwärts gelesen: Median / Mittel / Maximum; gleich in) | fernstes Einfügen **0,3 / 4,3 / 35,5**, gleich in 38; Nächster Nachbar **3,1 / 5,9 / 36,5**, gleich in 25; Zufall **2,7 / 4,3 / 19,9**, gleich in 31; Einfügen nach Split 3,1 / 6,9 / 30,8, gleich in 32 |
| Ohne Optimum, n = 50 und 100 (Auslastung 90 %, 32 Instanzen, Median / Maximum) | n = 50: fernstes Einfügen 4,7 / 19,9, Nächster Nachbar 4,8 / 15,3, Zufall 2,7 / 7,6; n = 100: 5,7 / 17,1, 7,0 / 13,3, 0,8 / 4,8. Gleich in höchstens 2 von 32 |
| Leserichtung | Rückwärts gelesen ändert „Füllen bis voll“ die Kosten bei n = 12 (90 %) in 56 / 51 / 48 von 80 Instanzen (fernstes Einfügen / Nächster Nachbar / Zufall); die bessere der beiden Richtungen liegt im Mittel noch 1,3 / 2,8 / 2,8 % über dem Split (Maximum 15,7 / 26,0 / 16,3 %) und trifft ihn in 53 / 45 / 39 von 80. **Der Split ändert sich nicht** (`tests/test_properties.py`) |
| **Artefakt der Gleichstandsregel** | Einfügen nach Split (n = 12, 90 %, die 32 Instanzen mit den Seeds 300000 bis 300007; über alle 80 Instanzen liegt der Median vorwärts bei 3,1 %): „Füllen“ vorwärts Median 8,0 % (Mittel 8,9), rückwärts 0,0 % (4,1); mit der **größeren statt der kleineren Stelle** bei Gleichstand vertauschen sich die Zahlen genau (0,0 / 4,1 und 8,0 / 8,9); bei n = 25: 14,1 / 4,4 und umgekehrt. Die zweite Reihenfolge ist exakt das Spiegelbild der ersten (60 Instanzen, n = 7). Der Richtungsunterschied ist ein Leserichtungseffekt von „Füllen“, den die Gleichstandsregel nur auswählt; beide Reihenfolgen sind Spiegelbilder und für den Split gleich gut |
| Zusammenhang mit der Kapazitätsenge | Median vorwärts bei Auslastung 60 / 75 / 90 / 98 %: n = 50: fernstes Einfügen 2,9 / 5,4 / 4,7 / 2,9, Nächster Nachbar 3,8 / 13,2 / 4,8 / 2,0, Zufall 1,5 / 2,2 / 2,7 / 1,6; n = 100: 3,6 / 7,6 / 5,7 / 1,6, 2,5 / 10,6 / 7,0 / 2,5, 0,9 / 1,4 / 0,8 / 1,4: **kein einfacher Zusammenhang** |
| Routenzahlen (n = 12, 90 %; fernstes Einfügen / Nächster Nachbar / Zufall) | „Füllen“ braucht mehr als die Mindestroutenzahl m in 19 / 15 / 20 von 80; der Split fährt mehr Routen als „Füllen“ in **10 / 22 / 21** von 80 (n = 50, Zufall: 20 von 32) |
| Flottengrenze g = Routenzahl von „Füllen“ (n = 12, 90 %) | Mehrkosten gegenüber dem Split ohne Grenze: Maximum **10,4 / 26,0 / 10,7 %**, Mittel 0,4 / 1,8 / 1,3 %, die Grenze bindet in 10 / 22 / 21 von 80. **Mit g + 1 Routen bindet sie bei n = 12 in keiner der 1 280 Kombinationen** (4 Auslastungen × 4 Reihenfolgen × 80 Instanzen); bei n ≥ 25 bindet sie in einzelnen Fällen (siehe unten) |
| Flottengrenze bei größeren Instanzen (Auslastung 90 %, 32 Instanzen) | g bindet bei n = 25 in 8 / 7 / 17 und bei n = 50 in 8 / 12 / 20 von 32 (Maximum 9,4 / 11,5 / 7,3 % und 6,8 / 6,6 / 3,4 %); g + 1 bindet nur selten (n = 25: Zufall 1 von 32; n = 50: Nächster Nachbar 2, Zufall 1) mit höchstens 0,9 % |
| **Preis der Mindestflotte im Optimum** (n = 12, exakt, 80 Instanzen, Mindestroutenzahl m = 3) | Das Optimum fährt mehr Routen als m in **0 / 7 / 14 / 25** von 80 bei Auslastung 90 / 95 / 98 / 100 %; auf höchstens m beschränkt kostet es im Mittel (über die zulässigen Instanzen) 0,0 / 0,3 / 0,7 / 1,6 % mehr, im Maximum 0,0 / 8,3 / 17,5 / 23,7 %. Bei 100 % ist die Mindestflotte in **2 von 80** Instanzen gar nicht zulässig |
| Voreinstellung (n = 8, zufällig verteilt, Depot in der Mitte, Auslastung 90 %, Seed 0, kürzeste Rundreise) | Optimum 444,40, Split 446,42; „Füllen bis voll“ vorwärts 503,04 (+12,7 % über dem Split), rückwärts 487,77 (+9,3 %); alle drei in 3 Routen, die Flottengrenze 3 und 4 kostet nichts |
| Handinstanz aus Stück 1 (n = 6, Optimum 44,36, Mindestroutenzahl 2) | Rundreise, gelesen als 5 1 4 3 6 2 (die App liest sie als 2 6 3 4 1 5, dann sind vorwärts und rückwärts vertauscht): „Füllen“ vorwärts 55,26, rückwärts 47,19, Split 47,19 in **drei** Routen (+17,1 % für „Füllen“ vorwärts); Split mit höchstens 1 / 2 / 3 / 4 Routen: nicht zerlegbar / nicht zerlegbar / 47,19 / 47,19; exakt mit höchstens 1 / 2 / 3 Routen: unzulässig / 44,36 / 44,36 |

## Ehrliche Grenzen

- Die Aussagen gelten für die gemessenen Größen (12, 25, 50, 100 Kunden), drei Zielrouten und die drei Kartenarten; sie sind keine Aussagen über echte Daten oder andere Zielroutenzahlen.
- Die Bänder vergleichen „Füllen bis voll“ und Split auf **derselben Reihenfolge**; die Reihenfolgen stammen aus den Erzeugern von Stück 2, nicht aus einer Suche.
- „Einfügen nach Split“ ist wegen des Gleichstand-Artefakts in der Spalte „vorwärts“ mit Vorsicht zu lesen und fehlt bei 100 Kunden (zu langsam).
- Die Auslastung wirkt nicht einfach: Die Bänder zeigen Zahlen je Auslastung, keinen Trend; die Hypothese „der Vorteil des Splits wächst mit der Enge“ trägt nicht.
- Die Mindestroutenzahl ist nur eine untere Schranke; bei knapper Kapazität kann ein Plan mit so vielen Routen fehlen (Bin Packing).
- „Füllen bis voll“ meint die Zerlegung einer festen Reihenfolge; Best Fit und First Fit lösen die Reihenfolge auf und gehören nicht dazu.
- Die Rechenzeiten (Größenordnung) sind eine Messung unter Windows, nicht festgeschrieben.
- Die Diagramme wurden im Browser angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft.

### Annahmen, Grenzen und bekannte Probleme (Text wie in der App)

**Annahmen**
- Ein Depot, beliebig viele gleiche Fahrzeuge (außer im Experiment zur Flottengrenze), euklidische und symmetrische Entfernungen, keine Zeitfenster; jeder Kunde wird genau einmal von einem Fahrzeug bedient, seine Nachfrage ist nicht teilbar.
- Alles ist simuliert: Karten aus Zufallszahlen, kein Straßennetz, keine echten Aufträge.
- „Füllen bis voll“ meint hier die Zerlegung einer festen Reihenfolge in aufeinanderfolgende Routen (Next-Fit); andere Packregeln (Best Fit, First Fit) lösen die Reihenfolge auf und gehören nicht dazu.

**Grenzen**
- Live rechnet die App bis zu 12 Kunden mit exaktem Optimum und exaktem Optimum mit Flottengrenze. Die Bänder gelten für 12, 25, 50 und 100 Kunden an je 20 (n = 12) beziehungsweise 8 festen Instanzen je Zelle, drei Zielrouten und vier Auslastungen; Einfügen nach Split fehlt bei 100 Kunden (zu langsam).
- Die Bänder vergleichen „Füllen bis voll“ mit dem Split auf derselben Reihenfolge; die Reihenfolgen stammen aus den Erzeugern von Stück 2, nicht aus einer Suche.
- Die Leserichtung der kürzesten Rundreise ist in der App die lexikographisch kleinere; „Füllen bis voll“ hängt von ihr ab, der Split nicht. Beim Einfügen nach Split entscheidet die Gleichstandsregel (kleinere Stelle) über die Richtung.
- Die Mindestroutenzahl m = aufgerundet Gesamtnachfrage / Kapazität ist nur eine untere Schranke; ob ein Plan mit m Routen existiert, ist ein Packproblem.

**Bekannte Probleme und Unsicherheiten**
- Die Bänder sind Spannen über feste Instanzen, keine Trends und keine Aussagen über andere Kartenarten oder Zielroutenzahlen; zur Auslastung steht keine Trendaussage in der App.
- Die Rechenzeiten (Größenordnung) sind eine Messung unter Windows, nicht festgeschrieben.
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft.

## Befunde und Korrekturen gegenüber dem Plan

- **Auslastung 75 % in der Zählung „g + 1 bindet nie“:** Der Plan nannte 0 von 960 Kombinationen (Auslastung 0,6 / 0,9 / 0,98); die Demo hat 75 % als vierte Stufe, die Zählung lautet 0 von 1 280 und bleibt 0.
- **g + 1 bei n = 100:** Die Vormessung deckte nur n = 25 und 50 ab; bei n = 100 bindet g + 1 in einzelnen Instanzen (Auslastung 90 %: fernstes Einfügen 1, Zufall 2 von 32) mit höchstens 0,4 %.
- **Raster des Auslastungsreglers:** Der Regler läuft in Schritten von 2 Prozentpunkten ab 60; die Bandstufen 75 und 95 % liegen nicht auf dem Raster und stehen deshalb nur in den vorberechneten Bändern.
- **Reglerzustand bei Wechsel der Reihenfolge:** Der Regler B behält seinen Wert, wenn man die Reihenfolge wechselt; liegt er dann unter dem Greedy-Wert der neuen Reihenfolge, zeigt die App statt der Karte den Hinweis „nicht zerlegbar“ (im AppTest als eine Meldung mehr und eine Karte weniger zu sehen).
- **Ein Skriptfehler der Vormessung** (ein Zähler lief nach einer Ersetzung in einen Block und gab 23 statt 25 aus) wurde in der Planung gefunden und behoben; die Demo rechnet die Zahl getestet: 25 von 80 bei Auslastung 100 %.

## Verifikation

- **Kern:** „Füllen bis voll“ in beiden Richtungen, Split mit Flottengrenze und exakter Löser mit Flottengrenze an der Handinstanz, aus Wurzeln von Hand zusammengesetzt (`tests/test_algorithm.py`).
- **Orakel:** Greedy gegen die kleinste Routenzahl über alle Schnittmengen; Split mit Flottengrenze gegen die Aufzählung aller Schnittmengen (72 Instanzen mal 7 Grenzen); exakter Löser mit Flottengrenze gegen die Aufzählung aller Zerlegungen; Dominanz mit Flottengrenze; das Spiegelbild beim Einfügen nach Split (`tests/test_oracle_split_gegen_fuellen.py`).
- **Eigenschaften:** Split nie schlechter als „Füllen“ in beiden Richtungen, Greedy-Zahl richtungsunabhängig und mindestens m, Split mit Grenze nicht steigend in B und endlich genau ab g, Richtungsunabhängigkeit des Splits, mehr Kapazität, Verschieben und Skalieren, Kapazität fällt mit der Auslastung (`tests/test_properties.py`).
- **Randfälle:** ein und zwei Kunden, Kapazität gleich Gesamtnachfrage, Nachfrage gleich Kapazität, alle Kunden am selben Ort, Grenze 1, unzulässige Mindestflotte, Reglergrenzen (`tests/test_edge_cases.py`).
- **Verdikte:** jede Schwelle und jede Zahl im Text an gesetzten Werten (`tests/test_verdicts.py`).
- **Zahlen der README:** `tests/test_claims.py`; die vorberechneten Bänder und Preiszeilen gegen eine frische Rechnung je Größe (`tests/test_bands.py`).
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler am Minimum und Maximum), Aufbau, jede Reihenfolge, Flottengrenze-Regler, Preis- und Band-Auswahl, Permalink, PDF (`tests/test_app.py`, `tests/test_experiments.py`), Footer, Layout, Laufzeit-Importe.

## Tests

588 Tests. Laufzeit lokal rund zwei Minuten (gemessen: 136 Sekunden).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App |
| `generate_precomputed.py` | erzeugt `sgf_bands.json` (Zerlegungen und Preis der Mindestflotte; Teile lassen sich parallel rechnen) |
| `requirements-dev.txt` | Laufzeit plus pytest |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `sgf_algorithm.py` | Kern: Split, Füllen bis voll, Split mit Flottengrenze, exakter Löser (auch mit Flottengrenze), Held–Karp |
| `sgf_bands.json` | vorberechnete Bänder (4 Größen × 4 Auslastungen × 4 Zellen) und Preiszeilen |
| `sgf_constants.py` | Regler-Grenzen, Reihenfolgen, Bänder, Farben, Presets, Annahmentext |
| `sgf_construct.py` | die Reihenfolgen (Erzeuger aus Stück 2, Einfügen nach Split mit Gleichstandsregel) |
| `sgf_evaluation.py` | Analyse, Bänder, Verdikt-Logik |
| `sgf_layout.py` | Fester Kopf und Tabellenregel (Stylesheet) |
| `sgf_pdf_export.py` | PDF-Export des Ergebnisses |
| `sgf_presets.py` | Permalink, Presets (Schnellstart in der Seitenleiste), Zufalls-Seed-Button |
| `sgf_scenario.py` | Instanzen (aus Stück 1, mit Auslastung als Parameter) |
| `sgf_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `tests/` | Handinstanz, Orakel, Eigenschaften, Randfälle, Verdikte, Claims, Bänder, Presets, Layout, AppTest, Footer, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Savings und Sweep** (Stück 4 und 6); die Fall-Demo [vrp_demo](https://sebastianhanisch-vrp-demo.streamlit.app/) rechnet beide und kennt eine gierige und eine optimale Zerlegung einer Riesentour mit Fahrzeuggrenze.
- **Best Fit und First Fit:** lösen die Reihenfolge auf; Online-Packen: [online-packen-demo](https://github.com/sebastian-hanisch/online-packen-demo).
- **Zeitfenster** (Stück 8): der Hilfsgraph bräuchte Etiketten, „Füllen bis voll“ eine Zeitprüfung.
- **Suche über Reihenfolgen** (Stück 11): die Reihenfolge ist hier gegeben.
- **Verschiedene Fahrzeugtypen:** nur gleiche Fahrzeuge mit einer Höchstzahl.
- **Instanzen über 12 Kunden live:** größere Instanzen stehen nur in den vorberechneten Bändern.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly, NumPy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
