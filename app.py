"""Split gegen Füllen bis voll - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 3 der Reihe „Tourenbildung“: Dieselbe Reihenfolge aller Kunden wird auf drei Arten in Routen zerlegt: „Füllen bis voll“ (vorwärts und rückwärts gelesen) und der Split
aus Stück 1. Die Demo zeigt, was der Split gegenüber „Füllen bis voll“ bringt, was eine Flottengrenze kostet und warum die Leserichtung nur „Füllen“ ändert.

Lauffähig mit: streamlit run app.py
"""

import math

import streamlit as st

import sgf_algorithm as A
import sgf_constants as C
from sgf_evaluation import (
    Settings,
    analyse,
    band_rows,
    de,
    gap_percent,
    mirror_rows,
    order_stats,
    order_text,
    pct,
    price_rows,
    price_stats,
    routes_word,
    verdict_bands,
    verdict_fill,
    verdict_fleet,
    verdict_fleet_summary,
    verdict_mirror,
    verdict_price,
)
from sgf_layout import dunkles_design, kopf_css
from sgf_pdf_export import build_pdf
from sgf_presets import (
    bounds,
    init_session_state_defaults,
    load_permalink_settings,
    randomize_seed,
    sidebar_presets,
    sync_query_params,
)
from sgf_visualization import build_bands, build_fleet_curve, build_map

st.set_page_config(page_title="Split gegen Füllen bis voll – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _mirror(settings):
    return mirror_rows(settings)


@st.cache_data(show_spinner=False)
def _band_stats(n, fill):
    rows = band_rows(n, fill)
    return {k: order_stats(rows, k) for k in C.BAND_KEYS if order_stats(rows, k)}


@st.cache_data(show_spinner=False)
def _price_stats(fill):
    rows = price_rows(fill)
    return price_stats(rows) if rows else {}


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in sgf_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🧮 Split gegen Füllen bis voll")
st.markdown(
    """
**Was bringt es, eine Reihenfolge optimal zu zerlegen?** Eine Riesentour ist eine Reihenfolge aller Kunden. **„Füllen bis voll“** beginnt eine neue Route, sobald der nächste Kunde nicht mehr passt, und schaut nie auf Entfernungen.
Der **Split** aus Stück 1 schneidet dieselbe Reihenfolge dort, wo es am billigsten ist. Die Demo vergleicht beide auf derselben Reihenfolge, fragt, was eine **Flottengrenze** (höchstens B Fahrzeuge) kostet,
und zeigt, dass die **Leserichtung** der Reihenfolge nur „Füllen bis voll“ ändert, nie den Split.

Weiter unten: **🔬 Dieselbe Reihenfolge, drei Zerlegungen**, **🔬 Die Flottengrenze**, **🔬 Gleichstand und Leserichtung**, **🔬 Wie viel spart der Split?**,
**🚧 Wo die Annahmen enden**, der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So zerlegen „Füllen bis voll“ und der Split", expanded=True):
    st.markdown(
        """
1. **Füllen bis voll:** Die Kunden werden in der Reihenfolge in ein Fahrzeug geladen, bis der nächste nicht mehr passt; dann beginnt die nächste Route. Das ergibt die **kleinste Zahl von Routen**, in die die Reihenfolge überhaupt passt
   (an der Aufzählung aller Schnittmengen geprüft), aber die Schnitte liegen dort, wo die Kapazität sie erzwingt, nicht dort, wo sie billig sind.
2. **Split:** Der kürzeste Weg im Hilfsgraphen (Stück 1) wählt die Schnitte nach den Kosten und darf dafür **mehr Routen** fahren.
3. **Flottengrenze:** Mit höchstens B Routen sucht der Split den billigsten Weg mit höchstens B Bögen; unter dem Wert von „Füllen bis voll“ ist die Reihenfolge nicht mehr zerlegbar.
4. **Leserichtung:** „Füllen bis voll“ beginnt am Anfang der Folge; liest man sie rückwärts, entstehen andere Routen. Der Split sucht über alle Schnitte und ändert sich nicht.
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Instanz**")
    n = st.slider("Kunden n", *bounds("n_slider"), key="n_slider", help=f"Bis n = {C.N_MAX} rechnet die App das exakte Optimum, auch mit Flottengrenze.")
    family = st.selectbox("Art der Karte", list(range(len(C.FAMILIES))), key="family_select", format_func=lambda i: C.FAMILIES[i],
                          help="„Kleine Karte“: ganze Koordinaten 0 bis 16, Nachfragen 1 bis 4. Die beiden anderen: Karte 0 bis 100, Nachfragen 1 bis 10; „In Gruppen“: drei Häufungen von Kunden.")
    depot = st.selectbox("Lage des Depots", list(range(len(C.DEPOTS))), key="depot_select", format_func=lambda i: C.DEPOTS[i])
    routes = st.slider("Zielroutenzahl", *bounds("routes_slider"), key="routes_slider", help="Legt zusammen mit der Auslastung die Kapazität fest.")
    fill = st.slider("Auslastung (%)", *bounds("fill_slider"), step=C.FILL_STEP, key="fill_slider",
                     help="Kapazität = aufgerundet Gesamtnachfrage geteilt durch (Zielroutenzahl mal Auslastung). Bei 100 % ist die Kapazität knapp: Mit der Mindestroutenzahl passt nicht immer ein Plan.")
    seed = st.number_input("Zufalls-Seed der Instanz", *bounds("seed_input"), key="seed_input", step=1, help="Bei „Zufällige Reihenfolge“ bestimmt der Seed auch die Reihenfolge.")
    st.button("🎲 Neue Instanz generieren", width="stretch", on_click=randomize_seed)
    st.markdown("**Reihenfolge**")
    order_kind = st.selectbox("Reihenfolge", list(range(len(C.ORDER_KEYS))), key="order_select", format_func=lambda i: C.ORDER_NAMES[C.ORDER_KEYS[i]],
                              help="Welche Reihenfolge zerlegt wird: die Erzeuger aus Stück 2, die kürzeste Rundreise, die Routen des Optimums hintereinander oder der Zufall.")

sync_query_params({"n_slider": int(n), "family_select": int(family), "depot_select": int(depot), "routes_slider": int(routes), "fill_slider": int(fill), "seed_input": int(seed),
                   "order_select": int(order_kind)})

settings = Settings(int(n), int(family), int(depot), int(routes), int(fill), int(seed), int(order_kind))
a = _analysis(settings)
inst = a.inst

# --- Ergebnis ------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis: dieselbe Reihenfolge, drei Zerlegungen")
m1, m2, m3, m4 = st.columns(4)
# Delta immer als „mein Wert minus Referenz“; die Farbe regelt delta_color="inverse" (Vorzeichen-Falle, DEMO-PLAYBOOK §2). Die Differenz aus den angezeigten, gerundeten Werten, damit Zahl und Delta zusammenpassen.
m1.metric("Optimum (alle Tourenpläne)", de(a.exact.cost), delta="Referenz", delta_color="off")
m2.metric("Split der Reihenfolge", de(a.split.cost), delta=f"{round(a.split.cost, 2) - round(a.exact.cost, 2):+.2f} gegen Optimum".replace(".", ","), delta_color="inverse")
m3.metric("Füllen bis voll, vorwärts", de(a.fill_fwd.cost), delta=f"{round(a.fill_fwd.cost, 2) - round(a.split.cost, 2):+.2f} gegen Split".replace(".", ","), delta_color="inverse")
m4.metric("Füllen bis voll, rückwärts", de(a.fill_bwd.cost), delta=f"{round(a.fill_bwd.cost, 2) - round(a.split.cost, 2):+.2f} gegen Split".replace(".", ","), delta_color="inverse")
st.caption(f"Reihenfolge ({C.ORDER_NAMES[a.order_key]}): {order_text(a.order)}. Kapazität {inst.capacity}, Gesamtnachfrage {sum(inst.demand)}, Mindestroutenzahl {a.min_routes}; "
           f"das Optimum fährt {routes_word(len(a.exact.routes))}.")
st.download_button("📄 Ergebnis als PDF", data=build_pdf(settings, a), file_name="split-gegen-fuellen.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Was bringt der Split gegenüber „Füllen bis voll“?")
kind, text = verdict_fill(a)
getattr(st, kind)(text)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Dieselbe Reihenfolge, drei Zerlegungen")
st.caption("Links „Füllen bis voll“ vorwärts gelesen, in der Mitte rückwärts gelesen, rechts der Split. Alle drei zerlegen dieselbe Reihenfolge in aufeinanderfolgende Routen.")
c1, c2, c3 = st.columns(3)
for col, title, result, chart_key in ((c1, "Füllen vorwärts", a.fill_fwd, "map_fwd"), (c2, "Füllen rückwärts", a.fill_bwd, "map_bwd"), (c3, "Split", a.split, "map_split")):
    with col:
        st.markdown(f"**{title}: {de(result.cost)}** ({routes_word(len(result.routes))})")
        st.plotly_chart(build_map(inst, result.routes), width="stretch", key=chart_key)
table = ["| Zerlegung | Routen | Kosten | über Split | über Optimum |", "|---|---|---|---|---|"]
for name, result in (("Füllen bis voll, vorwärts", a.fill_fwd), ("Füllen bis voll, rückwärts", a.fill_bwd), ("Split", a.split)):
    table.append(f"| **{name}** | {' ‖ '.join('(' + order_text(r) + ')' for r in result.routes)} | {de(result.cost)} | {pct(gap_percent(result.cost, a.split.cost))} | {pct(gap_percent(result.cost, a.exact.cost))} |")
st.markdown("\n".join(table))

st.markdown("---")

st.subheader("🔬 Die Flottengrenze")
st.caption("Mit höchstens B Routen sucht der Split den billigsten Weg mit höchstens B Bögen. Unter der Zahl von „Füllen bis voll“ lässt sich die Reihenfolge gar nicht zerlegen; "
           "das exakte Optimum mit höchstens B Routen steht zum Vergleich (gestrichelt).")
bound = st.slider("Höchstzahl der Routen B", 1, inst.n, min(inst.n, max(a.greedy, 1)), key=f"fleet_slider_{inst.n}")
result = a.fleet[bound]
f1, f2 = st.columns([1, 1])
with f1:
    if result is None:
        st.markdown(f"**B = {bound}: nicht zerlegbar**")
        st.info(f"Die Reihenfolge braucht mindestens {routes_word(a.greedy)}.")
    else:
        st.markdown(f"**B = {bound}: {de(result.cost)}** ({routes_word(len(result.routes))})")
        st.plotly_chart(build_map(inst, result.routes), width="stretch", key="map_fleet")
with f2:
    st.plotly_chart(build_fleet_curve(a.fleet, a.exact_costs, a.greedy), width="stretch", key="fleet_curve")
kind, text = verdict_fleet(a, bound)
getattr(st, kind)(text)
rows_f = ["| B | Split mit höchstens B Routen | Routen | Optimum mit höchstens B Routen |", "|---|---|---|---|"]
for b in range(1, min(inst.n, max(a.exact_max, a.greedy + 2)) + 1):
    r = a.fleet[b]
    exact_b = a.exact_costs[b - 1] if b <= a.exact_max else None
    rows_f.append(f"| {b} | {'nicht zerlegbar' if r is None else de(r.cost)} | {'–' if r is None else len(r.routes)} | "
                  f"{'–' if exact_b is None else ('kein Plan' if math.isinf(exact_b) else de(exact_b))} |")
st.markdown("\n".join(rows_f))
kind, text = verdict_fleet_summary(a)
getattr(st, kind)(text)

st.markdown("**Preis der Mindestflotte im Optimum** (n = 12, exakt, vorberechnet)")
price_fill = st.radio("Auslastung (%)", list(C.PRICE_FILLS), index=2, horizontal=True, key="price_fill",
                      help="80 feste Instanzen (vier Zellen mal 20), drei Zielrouten; bei höherer Auslastung ist die Kapazität knapper.")
kind, text = verdict_price(int(price_fill), _price_stats(int(price_fill)))
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Gleichstand und Leserichtung")
st.caption("Dieselbe Reihenfolge vorwärts und rückwärts: „Füllen bis voll“ ändert sich, der Split nicht. Einfügen nach Split löst Gleichstände nach der kleineren oder der größeren Stelle auf; "
           "die beiden Reihenfolgen sind Spiegelbilder, und die Werte von „Füllen bis voll“ vertauschen sich.")
mrows = _mirror(settings)
table = ["| Reihenfolge | Folge | Füllen vorwärts | Füllen rückwärts | Split |", "|---|---|---|---|---|"]
for r in mrows:
    table.append(f"| **{r['name']}** | {order_text(r['order'])} | {de(r['fwd'])} | {de(r['bwd'])} | {de(r['split'])} |")
st.markdown("\n".join(table))
kind, text = verdict_mirror(mrows)
getattr(st, kind)(text)

st.markdown("---")

st.subheader("🔬 Wie viel spart der Split?")
band_n = st.radio("Kunden n", list(C.BAND_SIZES), index=2, horizontal=True, key="band_n",
                  help="Feste Instanzen, vorberechnet (generate_precomputed.py): Reihenfolgen aus den Erzeugern von Stück 2, beide Zerlegungen auf derselben Reihenfolge.")
band_fill = st.radio("Auslastung (%)", list(C.BAND_FILLS), index=2, horizontal=True, key="band_fill")
stats = _band_stats(int(band_n), int(band_fill))
if stats:
    count = next(iter(stats.values()))["count"]
    st.caption(f"Je {count // 4} feste Instanzen je Zelle (Kunden zufällig oder in Gruppen, Depot in der Mitte oder in der Ecke, drei Zielrouten), alle vier Zellen zusammen ({count} Instanzen). "
               "Die Zahlen sind Spannen über Instanzen, kein Satz; „Einfügen nach Split“ ist wegen des Gleichstand-Artefakts (Experiment oben) mit Vorsicht zu lesen und fehlt bei 100 Kunden.")
    st.plotly_chart(build_bands(stats), width="stretch", key="band_chart")
    table = ["| Reihenfolge | Vorwärts: Median | Minimum bis Maximum | Mittel | gleich | Rückwärts: Median | Richtung ändert | Split fährt mehr Routen | Grenze g bindet | Grenze g + 1 bindet |",
             "|---|---|---|---|---|---|---|---|---|---|"]
    for key in C.BAND_KEYS:
        if key in stats:
            s = stats[key]
            table.append(f"| **{C.ORDER_NAMES[key]}** | {pct(s['fwd']['median'])} | {pct(s['fwd']['min'])} bis {pct(s['fwd']['max'])} | {pct(s['fwd']['mean'])} | {s['fwd']['equal']} von {s['count']} | "
                         f"{pct(s['bwd']['median'])} | {s['direction_changes']} | {s['split_over_greedy']} | {s['g_bound']['binds']} (Max {pct(s['g_bound']['max'])}) | {s['g1_bound']['binds']} (Max {pct(s['g1_bound']['max'])}) |")
    st.markdown("\n".join(table))
kind, text = verdict_bands(int(band_n), int(band_fill), stats)
getattr(st, kind)(text)

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist | Wer setzt an |
|---|---|---|
| **Die Reihenfolge ist gegeben** | Beide Verfahren zerlegen nur; wer die Reihenfolge ändert, ändert beide Ergebnisse und die Leserichtung. Die Reihenfolgen stammen hier aus den Erzeugern von Stück 2 | Stück 11 (Riesentour suchen) |
| **Zusammenhängende Routen** | Best Fit und First Fit packen Kunden außerhalb der Reihenfolge in Fahrzeuge und lösen die Reihenfolge auf | online-packen-demo (Online-Algorithmen) |
| **Nur Kapazität, keine Zeitfenster** | Mit Zeitfenstern genügt der Bogen *i → j* nicht mehr: Er braucht Etiketten, und „Füllen bis voll“ muss auch die Zeit prüfen | Stück 8 (Zeitfenster) |
| **Gleiche Fahrzeuge, nur eine Flottengrenze** | Mit verschiedenen Fahrzeugtypen (Kapazität, Kosten) wächst der Hilfsgraph um die Fahrzeugart | – |
| **Bänder nur für drei Zielrouten und vier Auslastungen** | Andere Zielroutenzahlen (kürzere Routen) wurden nur bei n = 50 mit 8 Zielrouten angesehen; sie sind nicht in der App | – |
| **Kein Vergleich mit Savings und Sweep** | Beide sind keine Zerlegungen einer Reihenfolge im engen Sinn und folgen in Stück 4 und 6 | Stück 4, Stück 6 |
"""
)

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(C.ASSUMPTIONS_MARKDOWN)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Lesehilfe.** Wie in Stück 1 und 2: Ein Depot $0$, Kunden $1, \dots, n$ mit Nachfragen $q_i$, Kapazität $Q$, euklidische Entfernungen. Eine Riesentour $\pi$ ist eine Reihenfolge aller Kunden.

| Symbol | Bedeutung |
|---|---|
| $\pi = (\pi_1, \dots, \pi_n)$ | Reihenfolge aller Kunden; $\pi^{R}$ die rückwärts gelesene |
| $c(i, j)$ | Länge der Route, die die Kunden $\pi_{i+1}, \dots, \pi_j$ bedient |
| $\mathrm{Split}_B(\pi)$ | kleinste Gesamtlänge einer Zerlegung von $\pi$ in höchstens $B$ aufeinanderfolgende Routen |
| $\mathrm{Fill}(\pi)$ | Gesamtlänge der Routen von „Füllen bis voll“ auf $\pi$; $g(\pi)$ ihre Zahl |
| $m$ | Mindestroutenzahl $\lceil \sum_i q_i / Q \rceil$ |

**Füllen bis voll.** Beginne eine neue Route, sobald der nächste Kunde nicht mehr passt. Die Schnitte folgen allein den Nachfragen: $\mathrm{Fill}(\pi)$ hängt von $\pi$ ab und von der Leserichtung, $\mathrm{Fill}(\pi^{R}) \ne \mathrm{Fill}(\pi)$ im Allgemeinen.

**Satz (Greedy ist optimal in der Routenzahl).** $g(\pi)$ ist die kleinste Zahl aufeinanderfolgender Routen, in die $\pi$ passt. *Beweisidee (Austausch):* Nach $k$ Routen hat „Füllen bis voll“ mindestens so viele Kunden bedient wie jede andere Zerlegung in $k$ aufeinanderfolgende Routen;
das folgt durch Induktion über $k$, weil jede andere Zerlegung ihre $k$-te Route höchstens an derselben Stelle schließen darf wie Greedy, ohne die Kapazität zu verletzen. Folgerung: Unter $g(\pi)$ Routen ist $\pi$ nicht zerlegbar. Das Argument ist hier selbst formuliert und durch das Orakel (Aufzählung aller Schnittmengen) an Mini-Instanzen geprüft.
Außerdem gilt $g(\pi) = g(\pi^{R})$: Eine Zerlegung von $\pi$ ist rückwärts gelesen eine Zerlegung von $\pi^{R}$ mit denselben Routen.

**Split mit Flottengrenze.** Im Hilfsgraphen (Stück 1) mit Schichten nach der Zahl der Bögen:
$$f_0(0) = 0, \qquad f_k(j) = \min_{i < j,\ (i, j)\ \text{zulässig}} \big( f_{k-1}(i) + c(i, j) \big), \qquad \mathrm{Split}_B(\pi) = \min_{1 \le k \le B} f_k(n).$$
$\mathrm{Split}_B(\pi)$ ist endlich genau für $B \ge g(\pi)$ und nicht wachsend in $B$; für $B \ge n$ ist es der Split ohne Grenze. $\mathrm{Split}_B(\pi) = \mathrm{Split}_B(\pi^{R})$.

**Dominanz mit Flottengrenze.** Das Minimum von $\mathrm{Split}_B(\pi)$ über alle $\pi$ ist das Optimum über alle Pläne mit höchstens $B$ Routen: Aus einem solchen Plan ergibt die Aneinanderreihung seiner Routen eine Reihenfolge, deren Weg im Hilfsgraphen höchstens $B$ Bögen hat.
Dieselbe Aussage ohne Grenze steht in Stück 1; mit Grenze ist sie an Mini-Instanzen gegen den exakten Löser geprüft.

**Exakter Löser mit Flottengrenze.** Beste Route je Kundenmenge (Held–Karp), dann Zerlegung der Menge aller Kunden in genau $k$ Teilmengen, $k = 1, \dots, B$; das Optimum mit höchstens $B$ Routen ist das Minimum über $k \le B$. Gibt es keine zulässige Zerlegung (Bin Packing), ist der Wert unendlich.

**Gleichstandsregel und Spiegelbild.** Wählt Einfügen nach Split bei gleichen Split-Kosten die größere statt der kleineren Stelle, entsteht genau das Spiegelbild der Reihenfolge: Der Split ist richtungsunabhängig, also sind die Kandidaten gespiegelt gleich teuer, und die Regel wählt jeweils das Spiegelbild. Deshalb vertauschen sich die Werte von „Füllen bis voll“.

**Literatur.** Der Split mit begrenzter Flotte (eine Schicht je Route) geht laut Sekundärquellen auf Prins (2004) zurück, eine Version in O(n) auf Vidal (2016); beide wurden nur auf Abstract-Ebene gesehen, die Demo übernimmt keine Zahl daraus. „Füllen bis voll“ ist Next-Fit auf einer festen Folge; Gütegarantien des Online-Packens werden hier nicht behauptet.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
