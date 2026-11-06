"""Jede Zahl der README („Befunde“) und der Preset-Hilfen, nachgerechnet mit denselben Funktionen wie die App (DEMO-PLAYBOOK §4).

Die Bänder kommen aus sgf_bands.json (tests/test_bands.py rechnet Stichproben davon frisch nach); Werte werden auf eine Stelle verglichen. Die Zahlen für n = 12, 25 und 50
wurden in der Vormessung (vormessung/messreihe_tb8 bis tb12 der Planung) mit eigenen Skripten unabhängig bestimmt und stimmen überein."""

import math

import numpy as np
import pytest

import sgf_algorithm as A
import sgf_constants as C
import sgf_construct as K
import sgf_evaluation as ev
from conftest import OPTIMUM
from sgf_scenario import make_instance

KEYS = list(C.BAND_KEYS)        # farthest, nn, random, insert_split


def _stats(n, fill, key):
    return ev.order_stats(ev.band_rows(n, fill), key)


def r1(x):
    return round(x, 1)


# ----------------------------------------------------------------------------------------------------------------------------------- n = 12, Auslastung 90 %

# Reihenfolge -> Füllen vorwärts (Min, Median, Mittel, Max, gleich), rückwärts (Median, Mittel, Max, gleich), bessere Richtung (Median, Mittel, Max, gleich),
# Richtung ändert Kosten in, Greedy über Mindestroutenzahl, Split über Greedy, Grenze g (Max, Mittel, bindet), g+1 bindet
N12 = {
    "insert_split": ((0.0, 3.1, 6.9, 30.8, 32), (0.0, 3.1, 26.3, 55), (0.0, 1.2, 19.6, 65), 58, 1, 1, (12.0, 0.2, 1), 0),
    "farthest": ((0.0, 0.3, 4.3, 35.5, 38), (0.8, 3.3, 21.7, 35), (0.0, 1.3, 15.7, 53), 56, 19, 10, (10.4, 0.4, 10), 0),
    "nn": ((0.0, 3.1, 5.9, 36.5, 25), (0.6, 3.7, 26.0, 35), (0.0, 2.8, 26.0, 45), 51, 15, 22, (26.0, 1.8, 22), 0),
    "random": ((0.0, 2.7, 4.3, 19.9, 31), (2.2, 4.1, 22.6, 25), (0.2, 2.8, 16.3, 39), 48, 20, 21, (10.7, 1.3, 21), 0),
}


@pytest.mark.parametrize("key", list(N12))
def test_n12_fill_over_split_at_ninety_percent(key):
    s = _stats(12, 90, key)
    fwd, bwd, best, changes, g_over_m, k_over_g, gb, g1 = N12[key]
    assert s["count"] == 80
    assert (r1(s["fwd"]["min"]), r1(s["fwd"]["median"]), r1(s["fwd"]["mean"]), r1(s["fwd"]["max"]), s["fwd"]["equal"]) == fwd
    assert (r1(s["bwd"]["median"]), r1(s["bwd"]["mean"]), r1(s["bwd"]["max"]), s["bwd"]["equal"]) == bwd
    assert (r1(s["best"]["median"]), r1(s["best"]["mean"]), r1(s["best"]["max"]), s["best"]["equal"]) == best
    assert (s["direction_changes"], s["greedy_over_min"], s["split_over_greedy"]) == (changes, g_over_m, k_over_g)
    assert (r1(s["g_bound"]["max"]), r1(s["g_bound"]["mean"]), s["g_bound"]["binds"], s["g1_bound"]["binds"]) == (gb[0], gb[1], gb[2], g1)


def test_n12_other_utilizations_direction_changes_and_mean_over_split():
    mean_60 = {k: r1(_stats(12, 60, k)["fwd"]["mean"]) for k in KEYS}
    mean_98 = {k: r1(_stats(12, 98, k)["fwd"]["mean"]) for k in KEYS}
    assert mean_60 == {"farthest": 2.4, "nn": 3.1, "random": 3.3, "insert_split": 7.2}
    assert mean_98 == {"farthest": 5.8, "nn": 9.5, "random": 6.5, "insert_split": 8.3}
    assert [_stats(12, 60, k)["direction_changes"] for k in ("insert_split", "farthest", "nn", "random")] == [57, 37, 31, 50]
    assert [_stats(12, 98, k)["direction_changes"] for k in ("insert_split", "farthest", "nn", "random")] == [42, 68, 63, 60]


def test_a_fleet_of_greedy_plus_one_never_binds_at_twelve_customers():
    total = sum(_stats(12, fill, k)["g1_bound"]["binds"] for fill in C.BAND_FILLS for k in KEYS)
    assert total == 0 and len(C.BAND_FILLS) * len(KEYS) * 80 == 1280


# ----------------------------------------------------------------------------------------------------------------------------------- größere Instanzen

# (n, Auslastung) -> je Reihenfolge (Median, Maximum) der Mehrkosten von „Füllen bis voll“ vorwärts über dem Split
LARGE = {
    (25, 60): {"farthest": (1.2, 21.6), "nn": (2.5, 16.3), "random": (1.2, 11.2), "insert_split": (4.2, 30.4)},
    (25, 75): {"farthest": (6.5, 27.8), "nn": (13.4, 33.6), "random": (4.2, 23.0), "insert_split": (18.8, 52.7)},
    (25, 90): {"farthest": (1.1, 19.2), "nn": (3.5, 21.0), "random": (2.5, 18.5), "insert_split": (14.1, 52.1)},
    (25, 98): {"farthest": (5.2, 26.6), "nn": (12.7, 32.1), "random": (5.1, 13.8), "insert_split": (0.0, 26.0)},
    (50, 60): {"farthest": (2.9, 10.4), "nn": (3.8, 12.9), "random": (1.5, 5.2), "insert_split": (5.1, 29.1)},
    (50, 75): {"farthest": (5.4, 19.8), "nn": (13.2, 30.4), "random": (2.2, 7.7), "insert_split": (17.8, 42.9)},
    (50, 90): {"farthest": (4.7, 19.9), "nn": (4.8, 15.3), "random": (2.7, 7.6), "insert_split": (17.1, 32.7)},
    (50, 98): {"farthest": (2.9, 11.7), "nn": (2.0, 21.0), "random": (1.6, 13.0), "insert_split": (4.8, 19.1)},
    (100, 60): {"farthest": (3.6, 10.7), "nn": (2.5, 22.6), "random": (0.9, 3.7)},
    (100, 75): {"farthest": (7.6, 16.6), "nn": (10.6, 26.8), "random": (1.4, 4.3)},
    (100, 90): {"farthest": (5.7, 17.1), "nn": (7.0, 13.3), "random": (0.8, 4.8)},
    (100, 98): {"farthest": (1.6, 13.4), "nn": (2.5, 13.5), "random": (1.4, 6.2)},
}


@pytest.mark.parametrize("n,fill", list(LARGE))
def test_larger_instances_fill_over_split_median_and_maximum(n, fill):
    rows = ev.band_rows(n, fill)
    assert len(rows) == 32
    got = {k: (r1(ev.order_stats(rows, k)["fwd"]["median"]), r1(ev.order_stats(rows, k)["fwd"]["max"])) for k in KEYS if ev.order_stats(rows, k)}
    assert got == LARGE[(n, fill)]


def test_larger_instances_at_ninety_percent_means_and_equal_counts():
    assert [(r1(_stats(50, 90, k)["fwd"]["mean"]), _stats(50, 90, k)["fwd"]["equal"]) for k in ("farthest", "nn", "random")] == [(5.7, 2), (6.1, 1), (3.1, 0)]
    assert [(r1(_stats(100, 90, k)["fwd"]["mean"]), _stats(100, 90, k)["fwd"]["equal"]) for k in ("farthest", "nn", "random")] == [(5.5, 1), (6.6, 1), (1.2, 1)]
    assert _stats(50, 90, "random")["split_over_greedy"] == 20


def test_fleet_limit_at_larger_instances():
    expected = {
        (25, 90): {"farthest": (9.4, 8, 0.0, 0), "nn": (11.5, 7, 0.0, 0), "random": (7.3, 17, 0.2, 1), "insert_split": (0.0, 0, 0.0, 0)},
        (25, 98): {"farthest": (7.9, 3, 0.0, 0), "nn": (10.6, 3, 0.0, 0), "random": (3.6, 9, 0.0, 0), "insert_split": (9.3, 1, 0.0, 0)},
        (50, 90): {"farthest": (6.8, 8, 0.0, 0), "nn": (6.6, 12, 0.9, 2), "random": (3.4, 20, 0.0, 1), "insert_split": (4.1, 2, 0.0, 0)},
        (50, 98): {"farthest": (10.5, 11, 0.0, 0), "nn": (7.1, 12, 0.0, 0), "random": (9.1, 16, 0.5, 3), "insert_split": (10.1, 3, 0.0, 0)},
        (100, 90): {"farthest": (4.6, 7, 0.4, 1), "nn": (7.5, 13, 0.0, 0), "random": (0.6, 17, 0.0, 2)},
    }
    for (n, fill), per_key in expected.items():
        got = {k: (r1(_stats(n, fill, k)["g_bound"]["max"]), _stats(n, fill, k)["g_bound"]["binds"], r1(_stats(n, fill, k)["g1_bound"]["max"]), _stats(n, fill, k)["g1_bound"]["binds"]) for k in per_key}
        assert got == per_key, (n, fill)
    assert max(_stats(n, fill, k)["g1_bound"]["max"] for n in (25, 50, 100) for fill in (90, 98) for k in KEYS if _stats(n, fill, k)) < 1.0      # g + 1 kostet höchstens 0,9 %


# ----------------------------------------------------------------------------------------------------------------------------------- Preis der Mindestflotte

def test_price_of_the_minimum_fleet():
    got = {}
    for fill in C.PRICE_FILLS:
        s = ev.price_stats(ev.price_rows(fill))
        got[fill] = (s["count"], s["more_than_min"], s["infeasible"], r1(s["mean"]), r1(s["max"]), r1(s["median"]))
    assert got == {90: (80, 0, 0, 0.0, 0.0, 0.0), 95: (80, 7, 0, 0.3, 8.3, 0.0), 98: (80, 14, 0, 0.7, 17.5, 0.0), 100: (80, 25, 2, 1.6, 23.7, 0.0)}


# ----------------------------------------------------------------------------------------------------------------------------------- Gleichstand: Spiegelpaar (frisch gerechnet)

def test_tie_rule_swaps_forward_and_backward_values():
    """Einfügen nach Split, Auslastung 90, 32 Instanzen (vier Zellen mal Seeds 300000 bis 300007), n = 12 und 25: die Zahlen vertauschen sich beim Spiegeln der Gleichstandsregel."""
    for n, expected in ((12, (8.0, 8.9, 0.0, 4.1)), (25, (14.1, 15.5, 4.4, 7.9))):
        small_f, small_b, large_f, large_b = [], [], [], []
        for family, depot in C.BAND_CELLS:
            for seed in range(300000, 300008):
                inst = make_instance(n, family, depot, 3, seed, 90)
                for larger, fwd, bwd in ((False, small_f, small_b), (True, large_f, large_b)):
                    order = K.insert_split_order(inst, larger)
                    split = A.split(inst, order).cost
                    fwd.append(ev.gap_percent(A.fill_until_full(inst, order).cost, split))
                    bwd.append(ev.gap_percent(A.fill_until_full(inst, order[::-1]).cost, split))
        med = lambda v: r1(float(np.median(v)))
        mean = lambda v: r1(float(np.mean(v)))
        assert (med(small_f), mean(small_f), med(small_b), mean(small_b)) == expected
        assert (med(large_f), mean(large_f), med(large_b), mean(large_b)) == (expected[2], expected[3], expected[0], expected[1])


# ----------------------------------------------------------------------------------------------------------------------------------- Presets

def _preset(name):
    return ev.analyse(ev.Settings(**C.PRESETS[name]))


def test_preset_help_numbers():
    a = _preset("Füllen kostet mehr (n = 8)")
    assert (r1(ev.gap_percent(a.fill_fwd.cost, a.split.cost)), r1(ev.gap_percent(a.fill_bwd.cost, a.split.cost))) == (12.7, 9.3) and (round(a.exact.cost, 2), a.greedy, len(a.split.routes)) == (444.40, 3, 3)
    a = _preset("Die Richtung entscheidet (n = 8)")
    assert r1(ev.gap_percent(a.fill_fwd.cost, a.split.cost)) == 22.7 and ev.gap_percent(a.fill_bwd.cost, a.split.cost) == 0.0
    a = _preset("Der Split fährt mehr Routen (n = 8)")
    assert (a.greedy, len(a.split.routes), r1(ev.gap_percent(a.fleet[a.greedy].cost, a.split.cost)), ev.gap_percent(a.fleet[a.greedy + 1].cost, a.split.cost)) == (3, 4, 15.8, 0.0)
    a = _preset("Das Optimum braucht eine Route mehr (n = 8)")
    assert (a.min_routes, len(a.exact.routes), r1(ev.gap_percent(a.exact_costs[a.min_routes - 1], a.exact.cost))) == (3, 4, 1.2)
    a = _preset("Füllen trifft den Split (n = 8)")
    assert ev.gap_percent(a.fill_fwd.cost, a.split.cost) == 0.0 == ev.gap_percent(a.fill_bwd.cost, a.split.cost)
    a = _preset("Gleichstand spiegelt die Reihenfolge (n = 8)")
    assert a.order_key == "insert_split" and r1(ev.gap_percent(a.fill_fwd.cost, a.split.cost)) == 24.6 and ev.gap_percent(a.fill_bwd.cost, a.split.cost) == 0.0
    rows = ev.mirror_rows(ev.Settings(**C.PRESETS["Gleichstand spiegelt die Reihenfolge (n = 8)"]))
    assert rows[2]["order"] == rows[3]["order"][::-1] and rows[2]["fwd"] == pytest.approx(rows[3]["bwd"])
    a = _preset("Mindestflotte unzulässig (n = 12)")
    assert a.min_routes == 3 and math.isinf(a.exact_costs[2]) and len(a.exact.routes) == 4 and C.PRESETS["Mindestflotte unzulässig (n = 12)"]["fill"] == 100


def test_default_preset_numbers():
    a = ev.analyse(ev.Settings())
    assert a.inst.n == 8 and round(a.exact.cost, 2) == 444.40 and round(a.split.cost, 2) == 446.42 and round(a.fill_fwd.cost, 2) == 503.04 and round(a.fill_bwd.cost, 2) == 487.77
    assert (a.greedy, len(a.split.routes), a.min_routes, len(a.exact.routes)) == (3, 3, 3, 3)
    assert [r1(ev.gap_percent(a.fleet[b].cost, a.split.cost)) for b in (3, 4)] == [0.0, 0.0] and all(a.fleet[b] is None for b in (1, 2))


# ----------------------------------------------------------------------------------------------------------------------------------- Handinstanz (Fixture)

def test_hand_example_table_of_the_plan(hand):
    """PLAN-03: Rundreise braucht drei Routen, Rückwärts-„Füllen“ trifft den Split; Mindestroutenzahl 2, exakt mit höchstens 1 / 2 / 3 Routen: unzulässig / 44,36 / 44,36."""
    order = (5, 1, 4, 3, 6, 2)
    f, b, s = A.fill_until_full(hand, order), A.fill_until_full(hand, order[::-1]), A.split(hand, order)
    assert (round(f.cost, 2), round(b.cost, 2), round(s.cost, 2)) == (55.26, 47.19, 47.19)
    assert (round(A.fill_until_full(hand, (2, 6, 3, 4, 1, 5)).cost, 2), round(A.fill_until_full(hand, (5, 3, 4, 1, 2, 6)).cost, 2), round(A.fill_until_full(hand, (6, 2, 1, 4, 3, 5)).cost, 2)) == (47.19, 49.45, 53.75)
    assert round(100 * (55.26 / 47.19 - 1), 1) == 17.1
    costs = A.exact_fleet_costs(hand, 3)
    assert math.isinf(costs[0]) and round(costs[1], 2) == 44.36 == round(costs[2], 2) and hand.min_routes == 2 and OPTIMUM == pytest.approx(44.3623, abs=1e-4)
    assert [None if A.split_by_fleet(hand, order, 4)[b] is None else round(A.split_by_fleet(hand, order, 4)[b].cost, 2) for order in ((5, 1, 4, 3, 6, 2),) for b in (1, 2, 3, 4)] == [None, None, 47.19, 47.19]
