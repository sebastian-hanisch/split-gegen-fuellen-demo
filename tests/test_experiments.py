"""Aufbau der App: Abschnitte, Diagramme, Verdikte; Reihenfolge, Flottengrenze-Regler, Preis-Auswahl, Band-Auswahl, Permalink und PDF (AppTest, DEMO-PLAYBOOK §5).

Expander werden per Titel gesucht, nie per Index (neue Expander verschieben sonst die Positionen)."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import sgf_constants as C
import sgf_evaluation as ev
from sgf_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
SUBHEADERS = ["🔬 Dieselbe Reihenfolge, drei Zerlegungen", "🔬 Die Flottengrenze", "🔬 Gleichstand und Leserichtung", "🔬 Wie viel spart der Split?", "🚧 Wo die Annahmen enden"]


def _app() -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    return " ".join(m.value for group in (at.success, at.info, at.warning) for m in group)


def _messages(at) -> int:
    return len(at.success) + len(at.info) + len(at.warning) + len(at.error)


def test_sections_charts_and_verdicts_are_all_there():
    at = _app()
    assert [s.value for s in at.subheader] == SUBHEADERS
    assert len(at.get("plotly_chart")) == 6                    # drei Karten, Flottengrenze-Karte, Kostenkurve, Bänder
    assert _messages(at) == 6                                  # Kernfrage, Flottengrenze, Zusammenfassung, Preis, Spiegelpaar, Bänder
    labels = [e.label for e in at.expander]
    for wanted in ("So zerlegen „Füllen bis voll“ und der Split", "⚠️ Annahmen, Grenzen und bekannte Probleme", "📐 Mathematische Formulierung"):
        assert wanted in labels


def test_metrics_show_optimum_split_and_both_fill_directions_with_consistent_deltas():
    at = _app()
    assert [m.value for m in at.metric] == ["444,40", "446,42", "503,04", "487,77"]
    assert at.metric[1].delta == "+2,02 gegen Optimum" and at.metric[2].delta == "+56,62 gegen Split" and at.metric[3].delta == "+41,35 gegen Split"   # aus den angezeigten Werten


@pytest.mark.parametrize("index", range(len(C.ORDER_KEYS)))
def test_every_order_runs_and_the_verdicts_stay_complete(index):
    at = _app()
    at.sidebar.selectbox(key="order_select").set_value(index).run()
    assert not at.exception, [str(e) for e in at.exception]
    # Der Regler B behält seinen Wert beim Wechsel der Reihenfolge: liegt er unter dem Greedy-Wert der neuen Reihenfolge, steht statt der Karte ein Hinweis (eine Meldung mehr, eine Karte weniger)
    assert (_messages(at), len(at.get("plotly_chart"))) in ((6, 6), (7, 5))


def test_fleet_slider_below_the_greedy_count_shows_a_hint_instead_of_a_map():
    at = _app()
    at.slider(key="fleet_slider_8").set_value(1).run()
    assert not at.exception
    assert "nicht zerlegbar" in _texts(at) and len(at.get("plotly_chart")) == 5
    at.slider(key="fleet_slider_8").set_value(8).run()
    assert not at.exception and "dasselbe wie ohne Grenze" in _texts(at) and len(at.get("plotly_chart")) == 6


def test_price_and_band_selections_switch_the_verdicts():
    at = _app()
    at.radio(key="price_fill").set_value(100).run()
    assert not at.exception and "Bei Auslastung 100 %" in _texts(at) and "in 2 Instanzen gibt es mit der Mindestroutenzahl gar keinen zulässigen Plan" in _texts(at)
    for n in C.BAND_SIZES:
        at.radio(key="band_n").set_value(n).run()
        assert not at.exception and f"Bei n = {n}, Auslastung 90 %" in _texts(at)
    at.radio(key="band_fill").set_value(60).run()
    assert not at.exception and "Auslastung 60 %" in _texts(at)


def test_utilization_slider_changes_the_capacity():
    at = _app()
    capacity = lambda a: next(c.value for c in a.caption if c.value.startswith("Reihenfolge ("))
    low = capacity(at)
    at.sidebar.slider(key="fill_slider").set_value(100).run()
    assert not at.exception and capacity(at) != low


def test_permalink_sets_the_controls_from_the_address():
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    at.query_params["n"] = "6"
    at.query_params["fill"] = "70"
    at.query_params["order"] = "2"
    at.run()
    assert not at.exception
    assert at.sidebar.slider(key="n_slider").value == 6 and at.sidebar.slider(key="fill_slider").value == 70 and at.sidebar.selectbox(key="order_select").value == 2


def test_pdf_export_has_a_pdf_header():
    s = ev.Settings()
    data = build_pdf(s, ev.analyse(s))
    assert data[:5] == b"%PDF-" and len(data) > 1500
