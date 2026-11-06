"""Verdikte an von Hand gesetzten Werten (DEMO-PLAYBOOK §12): jede Zahl im Text und jede Schwelle der Art steht hier.

Ein Verdikt ist eine reine Funktion (Art, Text) und bekommt eine Analyse mit gesetzten Zahlen, nicht Seeds. Split 100,00; Optimum 90,00."""

import math

import sgf_algorithm as A
import sgf_constants as C
import sgf_evaluation as ev
from sgf_scenario import Instance

INST = Instance(((0.0, 0.0), (1.0, 0.0), (2.0, 0.0), (3.0, 0.0)), (1, 1, 1), 2)
SPLIT = 100.0


def _res(cost, routes):
    return A.SplitResult(cost, routes)


def _a(fwd=100.0, bwd=100.0, greedy=2, split_routes=((1, 2), (3,)), fleet=None, exact_costs=(math.inf, 90.0, 90.0), exact_max=3, m=2, opt_routes=((1, 2), (3,))) -> ev.Analysis:
    fleet = fleet or {1: None, 2: _res(100.0, ((1, 2), (3,))), 3: _res(100.0, ((1, 2), (3,)))}
    return ev.Analysis(ev.Settings(), INST, A.ExactResult(90.0, opt_routes), 80.0, (1, 2, 3), "tour", (1, 2, 3), _res(SPLIT, split_routes),
                       _res(fwd, tuple((i,) for i in range(1, greedy + 1))), _res(bwd, tuple((i,) for i in range(1, greedy + 1))), greedy, m, fleet, tuple(exact_costs), exact_max)


# ----------------------------------------------------------------------------------------------------------------------------------- Füllen

def test_fill_verdict_when_both_directions_hit_the_split():
    kind, text = ev.verdict_fill(_a())
    assert kind == "success" and "trifft den Split in beiden Leserichtungen (100,00)" in text and "braucht 2 Routen, der Split 2 Routen" in text


def test_fill_verdict_names_both_directions_and_the_thresholds():
    kind, text = ev.verdict_fill(_a(fwd=104.9, bwd=110.0, greedy=3))
    assert kind == "info"                                                      # beste Richtung 4,9 % unter der Schwelle
    assert "vorwärts 104,90 (4,9 % über dem Split 100,00), rückwärts 110,00 (10,0 %)" in text and "Der Split hängt nicht von der Leserichtung ab" in text
    assert "„Füllen bis voll“ braucht 3 Routen, der Split 2 Routen" in text and "Nur in einer Leserichtung" not in text
    kind, text = ev.verdict_fill(_a(fwd=105.0, bwd=120.0))
    assert kind == "warning" and "5,0 %" in text and "20,0 %" in text            # beste Richtung genau 5,0 %: ab der Schwelle Warnung


def test_fill_verdict_when_only_one_direction_hits_the_split():
    kind, text = ev.verdict_fill(_a(fwd=100.0, bwd=130.0))
    assert kind == "info" and "Nur in einer Leserichtung trifft es den Split." in text and "rückwärts 130,00 (30,0 %)" in text


# ----------------------------------------------------------------------------------------------------------------------------------- Flottengrenze

def test_fleet_verdict_not_decomposable_below_the_greedy_count():
    kind, text = ev.verdict_fleet(_a(), 1)
    assert kind == "warning" and "Mit höchstens 1 Route ist diese Reihenfolge nicht zerlegbar" in text and "braucht 2 Routen" in text


def test_fleet_verdict_same_cost_as_without_a_limit_and_the_exact_optimum():
    kind, text = ev.verdict_fleet(_a(), 2)
    assert kind == "success" and "Mit höchstens 2 Routen kostet der Split 100,00 in 2 Routen: dasselbe wie ohne Grenze (100,00)" in text
    assert "Das exakte Optimum mit höchstens so vielen Routen: 90,00." in text


def test_fleet_verdict_with_extra_cost_and_without_an_exact_value():
    fleet = {1: None, 2: _res(104.0, ((1,), (2, 3))), 3: _res(100.0, ((1, 2), (3,)))}
    kind, text = ev.verdict_fleet(_a(fleet=fleet, exact_max=1, exact_costs=(math.inf,)), 2)
    assert kind == "info" and "kostet der Split 104,00: 4,0 % mehr als ohne Grenze (100,00 in 2 Routen)" in text and "Optimum" not in text
    kind, text = ev.verdict_fleet(_a(fleet={1: None, 2: _res(105.0, ((1,), (2, 3))), 3: None}), 2)
    assert kind == "warning" and "5,0 % mehr" in text
    kind, text = ev.verdict_fleet(_a(exact_costs=(math.inf, math.inf, 90.0)), 2)
    assert "Das exakte Optimum mit höchstens so vielen Routen: kein Plan." in text


def test_fleet_summary_names_greedy_split_and_limit_costs():
    fleet = {1: None, 2: _res(110.0, ((1,), (2, 3))), 3: _res(100.0, ((1, 2), (3,)))}
    kind, text = ev.verdict_fleet_summary(_a(fleet=fleet, split_routes=((1,), (2,), (3,))))
    assert kind == "warning"                                                   # 10 % Mehrkosten bei g Routen
    assert "passt in mindestens 2 Routen" in text and "der Split fährt 3 Routen" in text
    assert "Mit höchstens 2 Routen kostet der Split 10,0 % mehr, mit 3 Routen 0,0 % mehr" in text


def test_fleet_summary_with_the_minimum_fleet_in_the_optimum():
    kind, text = ev.verdict_fleet_summary(_a(exact_costs=(math.inf, 99.0, 90.0), opt_routes=((1,), (2,), (3,))))
    assert kind == "info"
    assert "Die Mindestroutenzahl der Instanz ist 2; das Optimum fährt 3 Routen, auf höchstens 2 Routen beschränkt kostet es 10,0 % mehr." in text
    kind, text = ev.verdict_fleet_summary(_a(exact_costs=(math.inf, math.inf, 90.0), opt_routes=((1,), (2,), (3,))))
    assert "aber mit höchstens 2 Routen gibt es keinen zulässigen Plan; das Optimum fährt 3 Routen" in text
    kind, text = ev.verdict_fleet_summary(_a(exact_costs=(math.inf,), exact_max=1))
    assert "Die Mindestroutenzahl der Instanz ist 2; das Optimum fährt 2 Routen." in text


# ----------------------------------------------------------------------------------------------------------------------------------- Spiegelpaar

def _row(name, order, fwd, bwd, split=100.0):
    return {"name": name, "order": order, "fwd": fwd, "bwd": bwd, "split": split}


def test_mirror_verdict_names_the_swap_and_the_direction_difference():
    rows = [_row("gewählt", (1, 2, 3), 110.0, 100.0), _row("rückwärts", (3, 2, 1), 100.0, 110.0), _row("klein", (1, 3, 2), 108.0, 100.0), _row("groß", (2, 3, 1), 100.0, 108.0)]
    kind, text = ev.verdict_mirror(rows)
    assert kind == "info"
    assert "um 10,0 % (110,00 gegen 100,00); der Split bleibt 100,00" in text
    assert "genau das Spiegelbild" in text and "(108,00 / 100,00 gegen 100,00 / 108,00)" in text and "gehört also zur Gleichstandsregel" in text


def test_mirror_verdict_with_mirrored_orders_but_equal_fill_values():
    rows = [_row("gewählt", (1, 2, 3), 110.0, 100.0), _row("rückwärts", (3, 2, 1), 100.0, 110.0), _row("klein", (1, 3, 2), 100.0, 100.0), _row("groß", (2, 3, 1), 100.0, 100.0)]
    kind, text = ev.verdict_mirror(rows)
    assert kind == "info" and "liefert genau das Spiegelbild, aber „Füllen bis voll“ ist hier in beiden Richtungen gleich (100,00); der Split bleibt 100,00." in text
    assert "vertauscht" not in text


def test_mirror_verdict_without_ties():
    rows = [_row("gewählt", (1, 2, 3), 100.0, 100.0), _row("rückwärts", (3, 2, 1), 100.0, 100.0), _row("klein", (1, 2, 3), 100.0, 100.0), _row("groß", (1, 2, 3), 100.0, 100.0)]
    kind, text = ev.verdict_mirror(rows)
    assert kind == "info" and "um 0,0 %" in text and "keine Gleichstände" in text


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

def _item(split, fwd, bwd, g=3, k=3, cost_g=None, cost_g1=None):
    return {"split": split, "fwd": fwd, "bwd": bwd, "g": g, "k": k, "cost_g": cost_g or split, "cost_g1": cost_g1 or split}


def _rows():
    return [{"seed": 1, "m": 3, "orders": {"farthest": _item(100.0, 100.0, 110.0), "nn": _item(100.0, 104.0, 100.0, g=4, k=4)}},
            {"seed": 2, "m": 3, "orders": {"farthest": _item(100.0, 120.0, 100.0, g=3, k=4, cost_g=110.0, cost_g1=102.0), "nn": _item(100.0, 100.0, 100.0)}},
            {"seed": 3, "m": 3, "orders": {"farthest": _item(100.0, 110.0, 130.0, g=4, k=4), "nn": _item(100.0, 108.0, 100.0)}}]


def test_order_stats_by_hand():
    s = ev.order_stats(_rows(), "farthest")
    assert s["count"] == 3
    assert (s["fwd"]["min"], s["fwd"]["median"], s["fwd"]["max"], s["fwd"]["equal"]) == (0.0, 10.0, 20.0, 1) and abs(s["fwd"]["mean"] - 10.0) < 1e-9
    assert (s["bwd"]["median"], s["bwd"]["equal"]) == (10.0, 1) and (s["best"]["median"], s["best"]["max"], s["best"]["equal"]) == (0.0, 10.0, 2)
    assert s["direction_changes"] == 3 and s["greedy_over_min"] == 1 and s["split_over_greedy"] == 1
    assert (s["g_bound"]["max"], s["g_bound"]["binds"]) == (10.0, 1) and (s["g1_bound"]["max"], s["g1_bound"]["binds"]) == (2.0, 1)
    assert ev.order_stats(_rows(), "insert_split") == {}


def test_band_verdict_lists_the_medians_maxima_and_equal_counts():
    stats = {k: ev.order_stats(_rows(), k) for k in ("farthest", "nn")}
    kind, text = ev.verdict_bands(50, 90, stats)
    assert kind == "info"
    assert text.startswith("Bei n = 50, Auslastung 90 % (3 Instanzen):")
    assert "Median je Reihenfolge: Fernstes Einfügen 10,0 % (Maximum 20,0 %, gleich in 1); Nächster Nachbar 4,0 % (Maximum 8,0 %, gleich in 1)" in text
    assert ev.verdict_bands(50, 90, {})[0] == "warning" and C.BAND_FILE in ev.verdict_bands(50, 90, {})[1]


def test_price_stats_and_verdict_by_hand():
    rows = [{"seed": 1, "m": 3, "opt": 100.0, "k_opt": 3, "opt_m": 100.0}, {"seed": 2, "m": 3, "opt": 100.0, "k_opt": 4, "opt_m": 110.0},
            {"seed": 3, "m": 3, "opt": 100.0, "k_opt": 4, "opt_m": None}]
    s = ev.price_stats(rows)
    assert (s["count"], s["more_than_min"], s["infeasible"]) == (3, 2, 1) and abs(s["mean"] - 5.0) < 1e-9 and s["max"] == 10.0
    kind, text = ev.verdict_price(100, s)
    assert kind == "warning"                                                   # Maximum 10 % ab der Schwelle
    assert "Bei Auslastung 100 % (3 Instanzen, n = 12) fährt das Optimum in 2 Instanzen mehr Routen" in text and "im Mittel 5,0 % mehr (Maximum 10,0 %)" in text
    assert "in 1 Instanzen gibt es mit der Mindestroutenzahl gar keinen zulässigen Plan" in text
    assert ev.verdict_price(90, {})[0] == "warning"
    kind, text = ev.verdict_price(90, ev.price_stats([{"seed": 1, "m": 3, "opt": 100.0, "k_opt": 3, "opt_m": 100.0}]))
    assert kind == "info" and "keinen zulässigen" not in text
