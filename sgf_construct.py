"""Erzeuger der Reihenfolgen (aus riesentouren-erzeugen-demo, Stück 2 der Linie, ohne Spuren kopiert und umbenannt; neu: `larger_place` beim Einfügen nach Split).

Gleichstände: bei Kunden die kleinere Nummer, bei Stellen standardmäßig die kleinere Stelle. Mit `larger_place=True` gewinnt bei Gleichstand die größere Stelle: die entstehende
Reihenfolge ist dann genau das Spiegelbild der Reihenfolge mit der kleineren Stelle (an Instanzen geprüft, tests/test_properties.py). Eine Stelle p heißt: vor den p-ten Kunden der Folge."""

import sgf_algorithm as A
import sgf_constants as C
from sgf_scenario import Instance, distance_matrix


def farthest_insertion_order(inst: Instance) -> tuple[int, ...]:
    """Fernstes Einfügen: Start mit dem Kunden am weitesten vom Depot, dann der Kunde am weitesten von der bisherigen Rundreise an der Stelle mit der kleinsten Längenzunahme."""
    D = distance_matrix(inst)
    far = max(range(1, inst.n + 1), key=lambda c: (D[0][c], -c))
    tour = [0, far]
    left = set(range(1, inst.n + 1)) - {far}
    while left:
        pick = max(sorted(left), key=lambda c: (min(D[c][t] for t in tour), -c))
        best = None
        for k in range(len(tour)):
            a, b = tour[k], tour[(k + 1) % len(tour)]
            added = D[a][pick] + D[pick][b] - D[a][b]
            if best is None or added < best[0] - C.TIE:
                best = (added, k + 1)
        tour.insert(best[1], pick)
        left.remove(pick)
    return tuple(tour[1:])


def insert_split_order(inst: Instance, larger_place: bool = False) -> tuple[int, ...]:
    """Einfügen nach Split: Kunden in absteigender Entfernung vom Depot, jeder an der Stelle mit den kleinsten Split-Kosten der Teilfolge."""
    D = distance_matrix(inst)
    sequence = sorted(range(1, inst.n + 1), key=lambda c: (-D[0][c], c))
    order: tuple[int, ...] = ()
    for c in sequence:
        best = None
        for p in range(len(order) + 1):
            trial = order[:p] + (c,) + order[p:]
            cost = A.split(inst, trial).cost
            if best is None or cost < best[0] - C.TIE or (larger_place and abs(cost - best[0]) <= C.TIE):
                best = (cost, trial)
        order = best[1]
    return order


def order_for(key: str, inst: Instance, seed: int, tour_order=None, optimum=None) -> tuple[int, ...]:
    """Die Reihenfolge zum Schlüssel; `tour_order` und `optimum` (ExactResult) werden nur für „tour“ und „optimum“ gebraucht."""
    if key == "tour":
        return tuple(tour_order if tour_order is not None else A.tsp_tour(inst)[1])
    if key == "nn":
        return A.nearest_neighbour_order(inst)
    if key == "farthest":
        return farthest_insertion_order(inst)
    if key == "insert_split":
        return insert_split_order(inst)
    if key == "random":
        return A.random_order(inst, seed)
    if key == "optimum":
        return A.concatenate((optimum if optimum is not None else A.exact_cvrp(inst)).routes)
    raise KeyError(key)
