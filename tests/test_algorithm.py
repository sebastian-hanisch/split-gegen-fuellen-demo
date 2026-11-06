"""„Füllen bis voll“, Split mit Flottengrenze und exakter Löser mit Flottengrenze an der Handinstanz (PLAN-03): jede Zahl ist hier aus Wurzeln von Hand zusammengesetzt."""

import math

import pytest

import sgf_algorithm as A
from conftest import OPTIMUM, S2, S18, S20, S29, S32, S37, S45, S53, S72, S74, S185, TOUR_LENGTH

R41 = S72 + S37 + 7                      # Route (4 1)
R2632 = S29 + S20 + S53 + S32            # Route (2 6 3) = Route (3 6 2)

# Reihenfolge -> (Füllen vorwärts: Kosten, Routen; Füllen rückwärts: Kosten, Routen)
TABLE = {
    (5, 1, 4, 3, 6, 2): ((S2 + S74 + S72) + (7 + 5 + S53 + S45) + 2 * S29, ((5, 1), (4, 3, 6), (2,)), R2632 + R41 + 2 * S2, ((2, 6, 3), (4, 1), (5,))),
    (2, 6, 3, 4, 1, 5): (R2632 + R41 + 2 * S2, ((2, 6, 3), (4, 1), (5,)), (S2 + S74 + S72) + (7 + 5 + S53 + S45) + 2 * S29, ((5, 1), (4, 3, 6), (2,))),
    (5, 3, 4, 1, 2, 6): ((S2 + S18 + S32) + R41 + (S29 + S20 + S45), ((5, 3), (4, 1), (2, 6)), (S45 + S20 + S185 + S72) + (7 + 5 + S32) + 2 * S2, ((6, 2, 1), (4, 3), (5,))),
    (5, 3, 6, 2, 4, 1): (OPTIMUM, ((5, 3, 6, 2), (4, 1)), OPTIMUM, ((1, 4), (2, 6, 3, 5))),
    (4, 1, 2, 6, 3, 5): (OPTIMUM, ((4, 1), (2, 6, 3, 5)), OPTIMUM, ((5, 3, 6, 2), (1, 4))),
}


@pytest.mark.parametrize("order", list(TABLE))
def test_fill_until_full_forward_and_backward_by_hand(hand, order):
    fwd_cost, fwd_routes, bwd_cost, bwd_routes = TABLE[order]
    f, b = A.fill_until_full(hand, order), A.fill_until_full(hand, order[::-1])
    assert f.routes == fwd_routes and f.cost == pytest.approx(fwd_cost)
    assert b.routes == bwd_routes and b.cost == pytest.approx(bwd_cost)


def test_greedy_route_counts_by_hand(hand):
    """Nachfragen 3, 2, 2, 4, 2, 1, Kapazität 7, Gesamtnachfrage 14: Rundreise (5 1 4 3 6 2) braucht drei Routen (2 + 3 | 4 + 2 + 1 | 2), die Optimum-Folge zwei."""
    assert [len(A.fill_until_full(hand, o).routes) for o in TABLE] == [3, 3, 3, 2, 2]
    assert hand.min_routes == 2


def test_split_with_a_fleet_limit_by_hand(hand):
    # Rundreise: unter 3 Routen nicht zerlegbar, ab 3 der Split 47,19
    fleet = A.split_by_fleet(hand, (5, 1, 4, 3, 6, 2), 4)
    assert [fleet[b] is None for b in (1, 2, 3, 4)] == [True, True, False, False]
    assert fleet[3].cost == pytest.approx(2 * S2 + R41 + R2632) and len(fleet[3].routes) == 3 and fleet[4].cost == pytest.approx(fleet[3].cost)
    # Optimum-Folge: ab 2 Routen
    fleet = A.split_by_fleet(hand, (4, 1, 2, 6, 3, 5), 4)
    assert fleet[1] is None and fleet[2].cost == pytest.approx(OPTIMUM) and fleet[2].routes == ((4, 1), (2, 6, 3, 5))
    assert A.split_fleet(hand, (4, 1, 2, 6, 3, 5), 3).cost == pytest.approx(OPTIMUM)
    assert A.split_fleet(hand, (5, 3, 4, 1, 2, 6), 2) is None


def test_exact_optimum_with_a_fleet_limit_by_hand(hand):
    costs = A.exact_fleet_costs(hand, 3)
    assert math.isinf(costs[0]) and costs[1] == pytest.approx(OPTIMUM) and costs[2] == pytest.approx(OPTIMUM)      # ein Fahrzeug fasst nur 7 von 14


def test_unlimited_split_and_the_tour_come_from_stueck_1(hand):
    assert A.exact_cvrp(hand).cost == pytest.approx(OPTIMUM)
    length, order = A.tsp_tour(hand)
    assert length == pytest.approx(TOUR_LENGTH) and order == (2, 6, 3, 4, 1, 5)
    assert A.split(hand, order[::-1]).cost == pytest.approx(2 * S2 + R41 + R2632)


def test_split_with_a_large_bound_equals_the_unlimited_split(hand):
    for order in TABLE:
        assert A.split_fleet(hand, order, 6).cost == pytest.approx(A.split(hand, order).cost)


def test_fill_cost_is_the_plan_length_of_its_routes(hand):
    r = A.fill_until_full(hand, (5, 1, 4, 3, 6, 2))
    assert A.is_feasible_plan(hand, r.routes) and r.cost == pytest.approx(A.plan_length(hand, r.routes))
