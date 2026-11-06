"""Konstanten: Regler-Grenzen, feste Annahmen, Farben und Presets."""

N_MIN, N_MAX, DEFAULT_N = 6, 12, 8
SEED_MAX, DEFAULT_SEED = 999999, 0
ROUTES_MIN, ROUTES_MAX, DEFAULT_ROUTES = 2, 4, 3
FILL_MIN, FILL_MAX, FILL_STEP, DEFAULT_FILL = 60, 100, 2, 90   # Auslastung in Prozent: Kapazität = aufgerundet Gesamtnachfrage / (Zielroutenzahl · Auslastung)
CLUSTERS, CLUSTER_SIGMA = 3, 7.0              # Familie „In Gruppen“
FAMILIES = ("Kleine Karte (ganze Zahlen)", "Zufällig verteilt (0 bis 100)", "In Gruppen (0 bis 100)")
FAMILY_KEYS = ("small", "random", "clustered")
DEFAULT_FAMILY = 1
DEPOTS = ("In der Mitte", "In der Ecke")
DEFAULT_DEPOT = 0

# Reihenfolgen: Schlüssel und Namen (die sechs Zeilen der Handtabelle im Plan)
ORDER_KEYS = ("tour", "nn", "farthest", "insert_split", "random", "optimum")
ORDER_NAMES = {
    "tour": "Kürzeste Rundreise",
    "nn": "Nächster Nachbar",
    "farthest": "Fernstes Einfügen",
    "insert_split": "Einfügen nach Split",
    "random": "Zufällige Reihenfolge",
    "optimum": "Optimum hintereinander",
}
DEFAULT_ORDER = 0
TOL = 1e-9                                    # Gleichstände und Gleichheit von Kosten: absolut
TIE = 1e-12                                   # Beim Einfügen zählt ein Kandidat nur als besser, wenn er um mehr als TIE besser ist
GAP_WARN = 5.0                                # Abstand in Prozent, ab dem das Verdikt warnt

# Bänder (vorberechnet, sgf_bands.json): feste Instanzen, vier Zellen (Kunden zufällig/Gruppen mal Depot Mitte/Ecke), Zielroutenzahl 3
BAND_FILE = "sgf_bands.json"
BAND_SIZES = (12, 25, 50, 100)
BAND_FILLS = (60, 75, 90, 98)
BAND_CELLS = ((1, 0), (2, 0), (1, 1), (2, 1))
BAND_ROUTES = 3
BAND_SEEDS = {12: tuple(range(300000, 300020)), 25: tuple(range(300000, 300008)), 50: tuple(range(300000, 300008)), 100: tuple(range(300000, 300008))}
BAND_KEYS = ("farthest", "nn", "random", "insert_split")
BAND_ES_MAX_N = 50                            # Einfügen nach Split rechnet bei 100 Kunden zu lange (etwa 10 s je Instanz)
PRICE_FILLS = (90, 95, 98, 100)               # Preis der Mindestflotte im Optimum (n = 12, exakt)
PRICE_SEEDS = tuple(range(300000, 300020))

COLOR_SPLIT = "#2F6B65"
COLOR_FWD = "#d8a13a"
COLOR_BWD = "#4c78a8"
COLOR_OPT = "#c0504d"
ROUTE_COLORS = ("#2F6B65", "#c0504d", "#4c78a8", "#d8a13a", "#7b5ea7", "#8c564b")
ORDER_COLORS = {"farthest": "#1f4e8c", "nn": "#4c78a8", "random": "#999999", "insert_split": "#2F6B65"}

PRESETS = {
    "Füllen kostet mehr (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 0, "order": 0},
    "Die Richtung entscheidet (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 23, "order": 0},
    "Der Split fährt mehr Routen (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 17, "order": 0},
    "Das Optimum braucht eine Route mehr (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 24, "order": 0},
    "Füllen trifft den Split (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 2, "order": 0},
    "Gleichstand spiegelt die Reihenfolge (n = 8)": {"n": 8, "family": 1, "depot": 0, "routes": 3, "fill": 90, "seed": 13, "order": 3},
    "Mindestflotte unzulässig (n = 12)": {"n": 12, "family": 1, "depot": 0, "routes": 3, "fill": 100, "seed": 300002, "order": 0},
}
PRESET_HELP = {
    "Füllen kostet mehr (n = 8)": "Auf der kürzesten Rundreise kostet „Füllen bis voll“ vorwärts 12,7 % mehr als der Split, rückwärts 9,3 %.",
    "Die Richtung entscheidet (n = 8)": "Vorwärts gelesen kostet „Füllen bis voll“ 22,7 % mehr als der Split, rückwärts trifft es ihn genau: dieselbe Reihenfolge, andere Kosten.",
    "Der Split fährt mehr Routen (n = 8)": "„Füllen bis voll“ braucht 3 Routen, der Split fährt 4; auf 3 Routen beschränkt kostet der Split 15,8 % mehr.",
    "Das Optimum braucht eine Route mehr (n = 8)": "Die Mindestroutenzahl ist 3, das Optimum fährt aber 4 Routen; auf 3 beschränkt kostet es 1,2 % mehr.",
    "Füllen trifft den Split (n = 8)": "Hier fallen „Füllen bis voll“ in beiden Richtungen und der Split zusammen: Die Schnitte, die die Kapazität erzwingt, sind auch die billigsten.",
    "Gleichstand spiegelt die Reihenfolge (n = 8)": "Einfügen nach Split: „Füllen bis voll“ vorwärts 24,6 % über dem Split, rückwärts 0,0 %; mit der anderen Gleichstandsregel vertauschen sich die Werte.",
    "Mindestflotte unzulässig (n = 12)": "Bei 100 % Auslastung passen die Kunden nicht in die Mindestroutenzahl 3: Das Optimum fährt 4 Routen, mit höchstens 3 gibt es keinen Plan.",
}

# Text des Expanders „Annahmen, Grenzen und bekannte Probleme“; derselbe Text steht in der README (tests/test_readme.py vergleicht beide)
ASSUMPTIONS_MARKDOWN = """**Annahmen**
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
- Die Diagramme wurden im Browser nur angesehen und per Rauchtest bedient, nicht mit echtem Mausklick auf einzelne Punkte geprüft."""
