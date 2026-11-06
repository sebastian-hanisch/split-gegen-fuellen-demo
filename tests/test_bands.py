"""Die vorberechneten Bänder (sgf_bands.json) gegen eine frische Rechnung: je Größe eine Stichprobe der Zeilen und die Preiszeilen einer Zelle."""

import json
from pathlib import Path

import pytest

import sgf_constants as C
import sgf_evaluation as ev

STORED = json.loads((Path(__file__).resolve().parent.parent / C.BAND_FILE).read_text(encoding="utf-8"))
FIELDS = ("split", "fwd", "bwd", "g", "k", "cost_g", "cost_g1")


def _cell(n, fill, family, depot):
    return next(c for c in STORED["cells"] if (c["n"], c["fill"], c["family"], c["depot"]) == (n, fill, family, depot))


def _same_row(fresh, stored):
    assert fresh["seed"] == stored["seed"] and fresh["m"] == stored["m"] and set(fresh["orders"]) == set(stored["orders"])
    for key, item in stored["orders"].items():
        for field in FIELDS:
            assert fresh["orders"][key][field] == pytest.approx(item[field], abs=1e-9), (key, field)


@pytest.mark.parametrize("n,fill,family,depot,seeds", [(12, 98, 2, 1, range(300000, 300006)), (25, 75, 1, 0, range(300000, 300004)), (50, 90, 2, 0, range(300000, 300002)),
                                                        (100, 60, 1, 1, range(300000, 300003))])
def test_stored_rows_match_a_fresh_computation(n, fill, family, depot, seeds):
    rows = {r["seed"]: r for r in _cell(n, fill, family, depot)["rows"]}
    for seed in seeds:
        _same_row(ev.instance_row(n, family, depot, seed, fill), rows[seed])


def test_stored_price_rows_match_a_fresh_computation():
    cell = next(c for c in STORED["price"] if (c["fill"], c["family"], c["depot"]) == (100, 1, 0))
    rows = {r["seed"]: r for r in cell["rows"]}
    for seed in (300002, 300000):                                               # Seed 300002: die Mindestflotte ist unzulässig (None)
        fresh = ev.price_row(1, 0, seed, 100)
        assert fresh["m"] == rows[seed]["m"] and fresh["k_opt"] == rows[seed]["k_opt"] and fresh["opt"] == pytest.approx(rows[seed]["opt"])
        assert (fresh["opt_m"] is None) == (rows[seed]["opt_m"] is None)
        if fresh["opt_m"] is not None:
            assert fresh["opt_m"] == pytest.approx(rows[seed]["opt_m"])
    assert rows[300002]["opt_m"] is None


def test_file_has_all_cells_with_the_expected_instance_counts():
    assert {(c["n"], c["fill"], c["family"], c["depot"]) for c in STORED["cells"]} == {(n, f, fam, dep) for n in C.BAND_SIZES for f in C.BAND_FILLS for fam, dep in C.BAND_CELLS}
    for c in STORED["cells"]:
        assert [r["seed"] for r in c["rows"]] == list(C.BAND_SEEDS[c["n"]])
        assert all(set(r["orders"]) == {k for k in C.BAND_KEYS if not (k == "insert_split" and c["n"] > C.BAND_ES_MAX_N)} for r in c["rows"])
    assert {(c["fill"], c["family"], c["depot"]) for c in STORED["price"]} == {(f, fam, dep) for f in C.PRICE_FILLS for fam, dep in C.BAND_CELLS}
    assert all([r["seed"] for r in c["rows"]] == list(C.PRICE_SEEDS) for c in STORED["price"])
    assert STORED["meta"]["routes"] == C.BAND_ROUTES


def test_stored_numbers_are_consistent_with_the_theory():
    """Greedy-Zahl über der Mindestroutenzahl, der Split nie über „Füllen“ und nie unter dem Wert ohne Grenze; Preiszeilen: Optimum mit Mindestflotte nie unter dem Optimum."""
    for c in STORED["cells"]:
        for r in c["rows"]:
            for item in r["orders"].values():
                assert item["g"] >= r["m"] and item["k"] >= item["g"]
                assert item["split"] <= min(item["fwd"], item["bwd"]) + 1e-9 and item["cost_g"] >= item["split"] - 1e-9 and item["cost_g1"] <= item["cost_g"] + 1e-9
    for c in STORED["price"]:
        for r in c["rows"]:
            assert r["k_opt"] >= r["m"] and (r["opt_m"] is None or r["opt_m"] >= r["opt"] - 1e-9)


def test_band_rows_are_sorted_like_the_cell_order_and_empty_for_other_sizes():
    assert len(ev.band_rows(25, 90)) == 32 and ev.band_rows(7, 90) == [] and ev.price_rows(77) == []
    rows = ev.band_rows(12, 90)
    assert [r["seed"] for r in rows[:20]] == list(C.BAND_SEEDS[12]) and len(rows) == 80
