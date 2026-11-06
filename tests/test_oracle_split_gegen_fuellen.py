"""Orakel-Tests split-gegen-fuellen-demo: „Füllen bis voll“, Split mit Flottengrenze und exakter Löser mit Flottengrenze gegen unabhängige Rechenwege (ORACLE-PLAYBOOK §2).

- Greedy-Satz: „Füllen bis voll“ ergibt die kleinste Routenzahl über ALLE Schnittmengen der Folge (reines Python, keine Instanzmatrix).
- Split mit Flottengrenze: Aufzählung aller Schnittmengen mit höchstens B Routen, Kosten mit math.hypot.
- Exakter Löser mit Flottengrenze: Aufzählung aller Zerlegungen der Kundenmenge mit höchstens B Routen und aller Reihenfolgen je Route.
- Dominanz mit Flottengrenze: Minimum über ALLE Reihenfolgen von Split(B) gleich dem exakten Optimum mit höchstens B Routen.
- Spiegelbild: Einfügen nach Split mit der größeren Stelle ist die gespiegelte Reihenfolge der kleineren Stelle.
Mini-Instanzen mit festen Seeds (range), insgesamt wenige Sekunden."""

import itertools
import math

import numpy as np
import pytest

import sgf_algorithm as A
import sgf_construct as K
from sgf_scenario import make_instance

CELLS = [(f, d, r) for f in (0, 1, 2) for d in (0, 1) for r in (2, 3)]


def _dist(inst, a, b):
    (xa, ya), (xb, yb) = inst.xy[a], inst.xy[b]
    return math.hypot(xa - xb, ya - yb)


def _route(inst, customers):
    path = (0, *customers, 0)
    return sum(_dist(inst, u, v) for u, v in zip(path, path[1:]))


def _cuts(inst, order):
    """Alle Schnittmengen: Liste der zulässigen Zerlegungen in aufeinanderfolgende Routen."""
    n = len(order)
    for mask in range(1 << (n - 1)):
        routes, current = [], [order[0]]
        for t in range(1, n):
            if (mask >> (t - 1)) & 1:
                routes.append(current)
                current = []
            current.append(order[t])
        routes.append(current)
        if all(sum(inst.demand[c - 1] for c in r) <= inst.capacity for r in routes):
            yield routes


def _min_routes(inst, order):
    return min(len(r) for r in _cuts(inst, order))


def _split_bound(inst, order, bound):
    options = [sum(_route(inst, r) for r in routes) for routes in _cuts(inst, order) if len(routes) <= bound]
    return min(options) if options else math.inf


def _exact_bound(inst, bound):
    cust = list(range(1, inst.n + 1))
    cache = {}

    def best(group):
        if group not in cache:
            cache[group] = min(_route(inst, p) for p in itertools.permutations(group))
        return cache[group]

    def partitions(rest, left):
        if not rest:
            yield []
            return
        if left == 0:
            return
        first, others = rest[0], rest[1:]
        for k in range(len(others) + 1):
            for comb in itertools.combinations(others, k):
                group = (first, *comb)
                if sum(inst.demand[c - 1] for c in group) <= inst.capacity:
                    for tail in partitions(tuple(c for c in others if c not in comb), left - 1):
                        yield [group, *tail]

    options = [sum(best(g) for g in part) for part in partitions(tuple(cust), bound)]
    return min(options) if options else math.inf


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_greedy_gives_the_smallest_number_of_consecutive_routes(family, depot, routes):
    for seed in range(8):
        inst = make_instance(7, family, depot, routes, seed, 60 + 10 * (seed % 5))
        rng = np.random.default_rng(seed)
        for _ in range(3):
            order = tuple(int(c) + 1 for c in rng.permutation(7))
            assert len(A.fill_until_full(inst, order).routes) == _min_routes(inst, order), (seed, order)


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_split_with_a_fleet_limit_matches_the_enumeration(family, depot, routes):
    for seed in range(6):
        inst = make_instance(7, family, depot, routes, seed, 70 + 6 * seed)
        rng = np.random.default_rng(seed)
        order = tuple(int(c) + 1 for c in rng.permutation(7))
        fleet = A.split_by_fleet(inst, order, 7)
        for bound in range(1, 8):
            expected = _split_bound(inst, order, bound)
            got = fleet[bound]
            if math.isinf(expected):
                assert got is None, (seed, bound)
            else:
                assert got is not None and got.cost == pytest.approx(expected), (seed, bound)
                assert len(got.routes) <= bound and A.is_feasible_plan(inst, got.routes) and A.concatenate(got.routes) == order


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_exact_solver_with_a_fleet_limit_matches_the_enumeration(family, depot, routes):
    for seed in range(5):
        inst = make_instance(6, family, depot, routes, seed, 70 + 7 * seed)
        costs = A.exact_fleet_costs(inst, 4)
        for bound in range(1, 5):
            expected = _exact_bound(inst, bound)
            assert (math.isinf(costs[bound - 1]) and math.isinf(expected)) or costs[bound - 1] == pytest.approx(expected), (seed, bound)


@pytest.mark.parametrize("family,depot,routes", CELLS[::2])
def test_dominance_with_a_fleet_limit(family, depot, routes):
    """Das Minimum über alle Reihenfolgen von Split mit höchstens B Routen ist das exakte Optimum mit höchstens B Routen."""
    for seed in range(3):
        inst = make_instance(6, family, depot, routes, seed, 80 + 8 * seed)
        costs = A.exact_fleet_costs(inst, inst.min_routes + 2)
        for bound in range(inst.min_routes, inst.min_routes + 3):
            best = min((A.split_by_fleet(inst, p, bound)[bound] or A.SplitResult(math.inf, ())).cost for p in itertools.permutations(range(1, 7)))
            assert (math.isinf(best) and math.isinf(costs[bound - 1])) or best == pytest.approx(costs[bound - 1]), (seed, bound)


@pytest.mark.parametrize("family,depot,routes", CELLS)
def test_split_insertion_with_the_larger_place_is_the_mirror_image(family, depot, routes):
    """Der Split ist richtungsunabhängig: gespiegelte Kandidaten sind gleich teuer, die Regel „größere Stelle“ wählt jeweils das Spiegelbild der Wahl „kleinere Stelle“."""
    for seed in range(5):
        inst = make_instance(7, family, depot, routes, seed)
        assert K.insert_split_order(inst, True) == K.insert_split_order(inst)[::-1], seed


def test_unlimited_split_matches_the_enumeration_of_all_cuts():
    for family, depot, routes in CELLS:
        for seed in range(3):
            inst = make_instance(7, family, depot, routes, seed)
            order = tuple(int(c) + 1 for c in np.random.default_rng(seed).permutation(7))
            assert A.split(inst, order).cost == pytest.approx(_split_bound(inst, order, 7))
