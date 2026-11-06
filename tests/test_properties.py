"""Eigenschaftstests (ORACLE-PLAYBOOK §5): Aussagen, die für JEDE Instanz und Reihenfolge gelten müssen, auf festen Zufallsinstanzen."""

import dataclasses
import math

import numpy as np
import pytest

import sgf_algorithm as A
from sgf_scenario import Instance, make_instance

CASES = [(f, d, r, s, fill) for f in (0, 1, 2) for d in (0, 1) for r in (2, 3) for s in range(2) for fill in (60, 90, 100)]


def _case(f, d, r, s, fill, n=8):
    inst = make_instance(n, f, d, r, s, fill)
    order = tuple(int(c) + 1 for c in np.random.default_rng(s + 3).permutation(inst.n))
    return inst, order


@pytest.mark.parametrize("f,d,r,s,fill", CASES)
def test_split_is_never_worse_than_filling_in_either_direction(f, d, r, s, fill):
    inst, order = _case(f, d, r, s, fill)
    split = A.split(inst, order).cost
    assert split <= A.fill_until_full(inst, order).cost + 1e-9 and split <= A.fill_until_full(inst, order[::-1]).cost + 1e-9


@pytest.mark.parametrize("f,d,r,s,fill", CASES)
def test_greedy_count_is_direction_independent_and_at_least_the_minimum_route_count(f, d, r, s, fill):
    inst, order = _case(f, d, r, s, fill)
    g = len(A.fill_until_full(inst, order).routes)
    assert g == len(A.fill_until_full(inst, order[::-1]).routes) and g >= inst.min_routes
    assert g <= len(A.split(inst, order).routes)                                         # der Split fährt nie weniger Routen als Greedy: g ist die kleinste mögliche Zahl


@pytest.mark.parametrize("f,d,r,s,fill", CASES)
def test_the_split_ignores_the_reading_direction(f, d, r, s, fill):
    inst, order = _case(f, d, r, s, fill)
    assert A.split(inst, order[::-1]).cost == pytest.approx(A.split(inst, order).cost)


def test_filling_does_depend_on_the_reading_direction_in_many_cases():
    changed = 0
    for f, d, r, s, fill in CASES:
        inst, order = _case(f, d, r, s, fill)
        changed += abs(A.fill_until_full(inst, order).cost - A.fill_until_full(inst, order[::-1]).cost) > 1e-9
    assert changed >= len(CASES) // 3


@pytest.mark.parametrize("f,d,r,s,fill", CASES)
def test_split_with_a_fleet_limit_is_nonincreasing_in_the_bound_feasible_exactly_from_the_greedy_count_and_equal_to_the_unlimited_split_for_large_bounds(f, d, r, s, fill):
    inst, order = _case(f, d, r, s, fill)
    g = len(A.fill_until_full(inst, order).routes)
    fleet = A.split_by_fleet(inst, order, inst.n)
    assert all((fleet[b] is None) == (b < g) for b in fleet)
    costs = [fleet[b].cost for b in range(g, inst.n + 1)]
    assert all(x >= y - 1e-9 for x, y in zip(costs, costs[1:]))
    assert costs[-1] == pytest.approx(A.split(inst, order).cost)
    assert all(fleet[b].cost >= A.split(inst, order).cost - 1e-9 and len(fleet[b].routes) <= b for b in range(g, inst.n + 1))


@pytest.mark.parametrize("f,d,r,s,fill", CASES[::3])
def test_the_split_with_a_fleet_limit_ignores_the_direction(f, d, r, s, fill):
    inst, order = _case(f, d, r, s, fill)
    a, b = A.split_by_fleet(inst, order, 6), A.split_by_fleet(inst, order[::-1], 6)
    for bound in a:
        assert (a[bound] is None) == (b[bound] is None) and (a[bound] is None or a[bound].cost == pytest.approx(b[bound].cost))


@pytest.mark.parametrize("f,d,r,s,fill", CASES[::2])
def test_more_capacity_never_raises_greedy_split_or_fill_costs_of_the_split(f, d, r, s, fill):
    inst, order = _case(f, d, r, s, fill)
    roomy = dataclasses.replace(inst, capacity=inst.capacity + 3)
    assert len(A.fill_until_full(roomy, order).routes) <= len(A.fill_until_full(inst, order).routes)
    assert A.split(roomy, order).cost <= A.split(inst, order).cost + 1e-9


@pytest.mark.parametrize("f,d,r,s,fill", CASES[::3])
def test_the_exact_optimum_with_a_fleet_limit_is_nonincreasing_and_bounded_by_every_split(f, d, r, s, fill):
    inst, order = _case(f, d, r, s, fill, n=6)
    costs = A.exact_fleet_costs(inst, 5)
    assert all(x >= y - 1e-9 for x, y in zip(costs, costs[1:]))
    assert costs[-1] == pytest.approx(A.exact_cvrp(inst).cost) or costs[-1] >= A.exact_cvrp(inst).cost - 1e-9
    fleet = A.split_by_fleet(inst, order, 5)
    for bound in range(1, 6):
        if fleet[bound] is not None:
            assert fleet[bound].cost >= costs[bound - 1] - 1e-9


@pytest.mark.parametrize("f,d,r,s,fill", CASES[::4])
def test_shifting_and_scaling_the_map_scales_all_costs_and_changes_no_routes(f, d, r, s, fill):
    inst, order = _case(f, d, r, s, fill)
    big = dataclasses.replace(inst, xy=tuple((3.0 * x + 7.0, 3.0 * y - 2.0) for x, y in inst.xy))
    assert A.fill_until_full(big, order).routes == A.fill_until_full(inst, order).routes
    assert A.fill_until_full(big, order).cost == pytest.approx(3.0 * A.fill_until_full(inst, order).cost)
    assert A.split(big, order).cost == pytest.approx(3.0 * A.split(inst, order).cost)


@pytest.mark.parametrize("f,d,r,s", [(f, d, r, s) for f in (0, 1, 2) for d in (0, 1) for r in (2, 3) for s in range(2)])
def test_the_capacity_falls_with_the_utilization_and_covers_the_largest_demand(f, d, r, s):
    caps = [make_instance(8, f, d, r, s, fill).capacity for fill in range(60, 101, 10)]
    assert all(x >= y for x, y in zip(caps, caps[1:]))
    assert all(c >= max(make_instance(8, f, d, r, s).demand) for c in caps)


def test_utilization_one_hundred_percent_gives_exact_total_over_target_routes():
    inst = make_instance(8, 1, 0, 3, 4, 100)
    assert inst.capacity == max(math.ceil(sum(inst.demand) / 3), max(inst.demand))


def test_fleet_costs_of_the_mirror_image_instance_are_unchanged_by_renumbering():
    inst, order = _case(1, 0, 3, 1, 90)
    perm = list(np.random.default_rng(5).permutation(inst.n))
    renamed = Instance((inst.xy[0],) + tuple(inst.xy[p + 1] for p in perm), tuple(inst.demand[p] for p in perm), inst.capacity)
    assert A.exact_fleet_costs(renamed, 4) == pytest.approx(A.exact_fleet_costs(inst, 4))
