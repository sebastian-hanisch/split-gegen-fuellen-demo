"""Randfälle, an denen „Füllen bis voll“, Split mit Flottengrenze und exakter Löser mit Flottengrenze erfahrungsgemäß brechen (DEMO-PLAYBOOK §12): n = 1 und n = 2, Kapazität gleich
Gesamtnachfrage, Nachfrage gleich Kapazität, Kunden am selben Ort, Flottengrenze 1, Gleichstände, Reglergrenzen, Abstände an der Null."""

import dataclasses
import math

import pytest

import sgf_algorithm as A
import sgf_constants as C
import sgf_construct as K
import sgf_evaluation as ev
from sgf_scenario import Instance, make_instance


def test_one_customer():
    inst = Instance(((0.0, 0.0), (3.0, 4.0)), (2,), 2)
    assert A.fill_until_full(inst, (1,)).routes == ((1,),) and A.fill_until_full(inst, (1,)).cost == pytest.approx(10.0)
    assert A.split_by_fleet(inst, (1,), 1)[1].cost == pytest.approx(10.0)
    assert A.exact_fleet_costs(inst, 2) == [pytest.approx(10.0), pytest.approx(10.0)]
    assert K.insert_split_order(inst) == (1,) == K.insert_split_order(inst, True) and K.farthest_insertion_order(inst) == (1,)


def test_exactly_two_customers_with_one_or_two_routes():
    together = Instance(((0.0, 0.0), (3.0, 4.0), (6.0, 8.0)), (1, 1), 2)       # Last 2 passt: eine Route 5 + 5 + 10
    assert A.fill_until_full(together, (1, 2)).routes == ((1, 2),) and A.fill_until_full(together, (2, 1)).cost == pytest.approx(20.0)
    assert A.split_by_fleet(together, (1, 2), 2)[1].cost == pytest.approx(20.0)
    apart = dataclasses.replace(together, capacity=1)                          # Last 2 passt nicht: zwei Fahrten 10 + 20
    assert A.fill_until_full(apart, (1, 2)).routes == ((1,), (2,))
    fleet = A.split_by_fleet(apart, (1, 2), 3)
    assert fleet[1] is None and fleet[2].cost == pytest.approx(30.0) and fleet[3].cost == pytest.approx(30.0)
    costs = A.exact_fleet_costs(apart, 2)
    assert math.isinf(costs[0]) and costs[1] == pytest.approx(30.0)


def test_capacity_for_everyone_is_one_route_and_one_bound_suffices():
    inst = make_instance(6, 1, 0, 2, 3)
    roomy = dataclasses.replace(inst, capacity=sum(inst.demand))
    order = (3, 1, 6, 2, 5, 4)
    assert len(A.fill_until_full(roomy, order).routes) == 1 and A.fill_until_full(roomy, order).cost == pytest.approx(A.route_length(roomy, order))
    assert A.split_by_fleet(roomy, order, 1)[1].cost == pytest.approx(A.route_length(roomy, order))
    assert A.exact_fleet_costs(roomy, 1)[0] == pytest.approx(A.tsp_tour(roomy)[0])


def test_demand_equal_to_capacity_forces_one_customer_per_route():
    inst = Instance(((0.0, 0.0), (3.0, 4.0), (6.0, 8.0), (-3.0, 4.0)), (4, 4, 4), 4)
    assert A.fill_until_full(inst, (2, 1, 3)).routes == ((2,), (1,), (3,))
    fleet = A.split_by_fleet(inst, (2, 1, 3), 4)
    assert fleet[1] is None and fleet[2] is None and fleet[3].cost == pytest.approx(2 * (10 + 5 + 5)) and fleet[4].cost == pytest.approx(fleet[3].cost)


def test_all_customers_on_one_point_and_a_customer_on_the_depot():
    same = Instance(((0.0, 0.0),) + ((3.0, 4.0),) * 4, (1, 1, 1, 1), 2)
    assert A.fill_until_full(same, (1, 2, 3, 4)).cost == pytest.approx(20.0) == A.fill_until_full(same, (4, 3, 2, 1)).cost
    assert A.split_fleet(same, (1, 2, 3, 4), 2).cost == pytest.approx(20.0) and A.split_fleet(same, (1, 2, 3, 4), 1) is None
    on_depot = Instance(((0.0, 0.0), (0.0, 0.0), (3.0, 4.0), (-3.0, 4.0)), (1, 1, 1), 2)
    assert A.exact_fleet_costs(on_depot, 2)[1] == pytest.approx(16.0)             # (1) kostet 0, (2 3) kostet 5 + 6 + 5


def test_fleet_bound_of_exactly_one_with_a_fitting_order():
    inst = dataclasses.replace(make_instance(6, 1, 0, 2, 1), capacity=10 ** 6)
    order = (1, 2, 3, 4, 5, 6)
    assert A.split_by_fleet(inst, order, 1)[1].routes == (order,)


def test_the_unreachable_minimum_fleet_is_reported_as_infinite():
    inst = make_instance(12, 1, 0, 3, 300002, 100)                              # Mindestroutenzahl 3, aber mit 3 Routen gibt es keinen Plan (Bin Packing)
    assert inst.min_routes == 3 and math.isinf(A.exact_fleet_costs(inst, 3)[2]) and not math.isinf(A.exact_fleet_costs(inst, 4)[3])


def test_every_control_limit_gives_a_valid_analysis():
    for n in (C.N_MIN, C.N_MAX):
        for fill in (C.FILL_MIN, C.FILL_MAX):
            for order in range(len(C.ORDER_KEYS)):
                a = ev.analyse(ev.Settings(n, 2, 1, C.ROUTES_MAX, fill, C.SEED_MAX, order))
                assert a.split.cost >= a.exact.cost - 1e-9 and a.greedy >= a.min_routes and a.fleet[a.greedy] is not None
                assert a.greedy == 1 or a.fleet[a.greedy - 1] is None


def test_gap_helpers_at_their_edges():
    assert ev.gap_percent(10.0, 0.0) == 0.0 and ev.gap_percent(5.0 + 1e-12, 5.0) == 0.0 and ev.gap_percent(4.0, 5.0) == 0.0
    assert ev.gap_percent(11.0, 10.0) == pytest.approx(10.0)
    assert ev.num(40320) == "40 320" and ev.de(3.14159) == "3,14" and ev.routes_word(1) == "1 Route" and ev.routes_word(3) == "3 Routen"
    assert ev.pct(4.26) == "4,3 %" and ev.pct(4.24) == "4,2 %"


def test_mirror_rows_of_an_instance_without_ties_report_equal_orders():
    inst_settings = ev.Settings(6, 1, 0, 3, 90, 5, 0)
    rows = ev.mirror_rows(inst_settings)
    assert len(rows) == 4 and rows[1]["order"] == rows[0]["order"][::-1] and rows[0]["split"] == pytest.approx(rows[1]["split"])
    assert rows[0]["fwd"] == pytest.approx(rows[1]["bwd"]) and rows[0]["bwd"] == pytest.approx(rows[1]["fwd"])
