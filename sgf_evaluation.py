"""Kennzahlen, Verdikt-Logik und Bänder. Verdikte sind reine Funktionen (Art, Text): die App ruft st.<Art>(Text), die Tests prüfen jede Zahl im Text."""

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from statistics import mean, median

import sgf_algorithm as A
import sgf_constants as C
import sgf_construct as K
from sgf_scenario import Instance, make_instance


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    family: int = C.DEFAULT_FAMILY
    depot: int = C.DEFAULT_DEPOT
    routes: int = C.DEFAULT_ROUTES
    fill: int = C.DEFAULT_FILL
    seed: int = C.DEFAULT_SEED
    order: int = C.DEFAULT_ORDER


@dataclass(frozen=True, eq=False)
class Analysis:
    settings: Settings
    inst: Instance
    exact: A.ExactResult                 # Optimum über alle Tourenpläne (ohne Flottengrenze)
    tour_length: float
    tour_order: tuple[int, ...]
    order_key: str
    order: tuple[int, ...]               # die gewählte Reihenfolge
    split: A.SplitResult                 # Split ohne Flottengrenze
    fill_fwd: A.SplitResult              # „Füllen bis voll“, vorwärts gelesen
    fill_bwd: A.SplitResult              # … rückwärts gelesen
    greedy: int                          # kleinste Zahl aufeinanderfolgender Routen, in die die Reihenfolge passt (= Routenzahl von „Füllen bis voll“)
    min_routes: int                      # Mindestroutenzahl der Instanz: aufgerundet Gesamtnachfrage / Kapazität
    fleet: dict                          # B -> SplitResult | None für B = 1 bis n: Split mit höchstens B Routen
    exact_costs: tuple                   # B - 1 -> Optimum mit höchstens B Routen (inf: kein Plan), B = 1 bis exact_max
    exact_max: int


# ----------------------------------------------------------------------------------------------------------------------------------- Formate

def de(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pct(x: float, digits: int = 1) -> str:
    return f"{de(x, digits)} %"


def num(n: int) -> str:
    return f"{int(n):,}".replace(",", " ")


def routes_word(k: int) -> str:
    return f"{k} Route" if k == 1 else f"{k} Routen"


def gap_percent(cost: float, reference: float) -> float:
    """Mehrkosten gegenüber der Referenz in Prozent der Referenz; unter der Toleranz oder ohne Referenzkosten gibt es keinen Abstand, nie negativ."""
    if reference <= 0 or cost - reference <= C.TOL:
        return 0.0
    return 100.0 * (cost - reference) / reference


def order_text(order) -> str:
    return " ".join(str(c) for c in order)


# ----------------------------------------------------------------------------------------------------------------------------------- Analyse

def analyse(settings: Settings) -> Analysis:
    inst = make_instance(settings.n, settings.family, settings.depot, settings.routes, settings.seed, settings.fill)
    exact = A.exact_cvrp(inst)
    tour_length, tour_order = A.tsp_tour(inst)
    key = C.ORDER_KEYS[settings.order]
    order = K.order_for(key, inst, settings.seed, tour_order, exact)
    split = A.split(inst, order)
    fwd, bwd = A.fill_until_full(inst, order), A.fill_until_full(inst, order[::-1])
    exact_max = min(inst.n, max(inst.min_routes, len(exact.routes), len(fwd.routes)) + 1)
    return Analysis(settings, inst, exact, tour_length, tuple(tour_order), key, order, split, fwd, bwd, len(fwd.routes), inst.min_routes,
                    A.split_by_fleet(inst, order, inst.n), tuple(A.exact_fleet_costs(inst, exact_max)), exact_max)


def mirror_rows(settings: Settings) -> list[dict]:
    """Experiment 3: die gewählte Reihenfolge und ihr Spiegelbild sowie Einfügen nach Split mit beiden Gleichstandsregeln, je mit „Füllen bis voll“ in beiden Richtungen und dem Split."""
    inst = make_instance(settings.n, settings.family, settings.depot, settings.routes, settings.seed, settings.fill)
    a = analyse(settings)
    es_small, es_large = K.insert_split_order(inst), K.insert_split_order(inst, True)
    rows = []
    for name, order in ((f"{C.ORDER_NAMES[a.order_key]} (gewählt)", a.order), ("dieselbe Reihenfolge rückwärts", a.order[::-1]),
                        ("Einfügen nach Split, Gleichstand: kleinere Stelle", es_small), ("Einfügen nach Split, Gleichstand: größere Stelle", es_large)):
        rows.append({"name": name, "order": tuple(order), "fwd": A.fill_until_full(inst, order).cost, "bwd": A.fill_until_full(inst, order[::-1]).cost, "split": A.split(inst, order).cost})
    return rows


# ----------------------------------------------------------------------------------------------------------------------------------- Bänder

def instance_row(n: int, family: int, depot: int, seed: int, fill: int) -> dict:
    """Eine feste Instanz der Bänder: je Reihenfolge Split, Füllen vorwärts und rückwärts, Routenzahlen und Split mit höchstens g und g + 1 Routen."""
    inst = make_instance(n, family, depot, C.BAND_ROUTES, seed, fill)
    row = {"seed": seed, "m": inst.min_routes, "orders": {}}
    for key in C.BAND_KEYS:
        if key == "insert_split" and n > C.BAND_ES_MAX_N:
            continue
        order = K.order_for(key, inst, seed)
        split = A.split(inst, order)
        fwd, bwd = A.fill_until_full(inst, order), A.fill_until_full(inst, order[::-1])
        g = len(fwd.routes)
        fleet = A.split_by_fleet(inst, order, g + 1)
        row["orders"][key] = {"split": split.cost, "fwd": fwd.cost, "bwd": bwd.cost, "g": g, "k": len(split.routes), "cost_g": fleet[g].cost, "cost_g1": fleet[g + 1].cost}
    return row


def price_row(family: int, depot: int, seed: int, fill: int) -> dict:
    """Preis der Mindestflotte im Optimum (n = 12): Optimum, Zahl seiner Routen und Optimum mit höchstens m Routen (inf: unzulässig, als None gespeichert)."""
    inst = make_instance(12, family, depot, C.BAND_ROUTES, seed, fill)
    exact = A.exact_cvrp(inst)
    m = inst.min_routes
    opt_m = A.exact_fleet_costs(inst, m)[m - 1]
    return {"seed": seed, "m": m, "opt": exact.cost, "k_opt": len(exact.routes), "opt_m": None if math.isinf(opt_m) else opt_m}


def order_stats(rows: list[dict], key: str) -> dict:
    """Aus gespeicherten Zeilen (alle Zellen einer Größe und Auslastung): Mehrkosten von „Füllen bis voll“ über dem Split vorwärts, rückwärts und in der besseren Richtung,
    Zählungen und Kosten der Flottengrenze."""
    items = [r["orders"][key] for r in rows if key in r["orders"]]
    if not items:
        return {}
    fwd = [gap_percent(x["fwd"], x["split"]) for x in items]
    bwd = [gap_percent(x["bwd"], x["split"]) for x in items]
    best = [min(a, b) for a, b in zip(fwd, bwd)]

    def spread(v):
        return {"min": min(v), "median": median(v), "mean": mean(v), "max": max(v), "equal": sum(g == 0.0 for g in v)}

    g_cost = [gap_percent(x["cost_g"], x["split"]) for x in items]
    g1_cost = [gap_percent(x["cost_g1"], x["split"]) for x in items]
    return {
        "count": len(items), "fwd": spread(fwd), "bwd": spread(bwd), "best": spread(best),
        "direction_changes": sum(abs(x["fwd"] - x["bwd"]) > C.TOL for x in items),
        "greedy_over_min": sum(x["g"] > r["m"] for r, x in zip((r for r in rows if key in r["orders"]), items)),
        "split_over_greedy": sum(x["k"] > x["g"] for x in items),
        "g_bound": {"max": max(g_cost), "mean": mean(g_cost), "binds": sum(v > 0 for v in g_cost)},
        "g1_bound": {"max": max(g1_cost), "binds": sum(v > 0 for v in g1_cost)},
    }


def price_stats(rows: list[dict]) -> dict:
    """Preis der Mindestflotte über die gespeicherten Zeilen einer Auslastung."""
    price = [gap_percent(r["opt_m"], r["opt"]) for r in rows if r["opt_m"] is not None]
    return {"count": len(rows), "more_than_min": sum(r["k_opt"] > r["m"] for r in rows), "infeasible": sum(r["opt_m"] is None for r in rows),
            "mean": mean(price), "max": max(price), "median": median(price)}


@lru_cache(maxsize=1)
def load_bands() -> dict:
    """Vorberechnete Bänder (generate_precomputed.py); {} wenn die Datei fehlt."""
    path = Path(__file__).with_name(C.BAND_FILE)
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def band_rows(n: int, fill: int) -> list[dict]:
    """Alle gespeicherten Instanzzeilen einer Größe und Auslastung, Zellen in der Reihenfolge von BAND_CELLS."""
    order = {cell: i for i, cell in enumerate(C.BAND_CELLS)}
    cells = sorted((c for c in load_bands().get("cells", []) if c["n"] == n and c["fill"] == fill), key=lambda c: order[(c["family"], c["depot"])])
    return [r for c in cells for r in c["rows"]]


def price_rows(fill: int) -> list[dict]:
    order = {cell: i for i, cell in enumerate(C.BAND_CELLS)}
    cells = sorted((c for c in load_bands().get("price", []) if c["fill"] == fill), key=lambda c: order[(c["family"], c["depot"])])
    return [r for c in cells for r in c["rows"]]


# ----------------------------------------------------------------------------------------------------------------------------------- Verdikte

def verdict_fill(a: Analysis) -> tuple[str, str]:
    """Experiment 1 und Kernfrage: „Füllen bis voll“ in beiden Leserichtungen gegen den Split."""
    f, b = gap_percent(a.fill_fwd.cost, a.split.cost), gap_percent(a.fill_bwd.cost, a.split.cost)
    routes = f"„Füllen bis voll“ braucht {routes_word(a.greedy)}, der Split {routes_word(len(a.split.routes))}."
    if f == 0.0 and b == 0.0:
        return "success", (f"„Füllen bis voll“ trifft den Split in beiden Leserichtungen ({de(a.split.cost)}): Die Schnitte, die die Kapazität erzwingt, sind hier auch die billigsten. " + routes)
    head = (f"„Füllen bis voll“ kostet vorwärts {de(a.fill_fwd.cost)} ({pct(f)} über dem Split {de(a.split.cost)}), rückwärts {de(a.fill_bwd.cost)} ({pct(b)}). ")
    if f == 0.0 or b == 0.0:
        head += "Nur in einer Leserichtung trifft es den Split. "
    return ("info" if min(f, b) < C.GAP_WARN else "warning"), head + "Der Split hängt nicht von der Leserichtung ab. " + routes


def verdict_fleet(a: Analysis, bound: int) -> tuple[str, str]:
    """Experiment 2: der Split mit höchstens `bound` Routen."""
    r = a.fleet[bound]
    if r is None:
        return "warning", (f"Mit höchstens {routes_word(bound)} ist diese Reihenfolge nicht zerlegbar: Schon „Füllen bis voll“ braucht {routes_word(a.greedy)}, und das ist die kleinste Zahl, "
                           "in die die Reihenfolge überhaupt passt.")
    extra = gap_percent(r.cost, a.split.cost)
    optimum = a.exact_costs[bound - 1] if bound <= a.exact_max else None
    tail = "" if optimum is None else (" Das exakte Optimum mit höchstens so vielen Routen: " + ("kein Plan." if math.isinf(optimum) else f"{de(optimum)}."))
    if extra == 0.0:
        return "success", f"Mit höchstens {routes_word(bound)} kostet der Split {de(r.cost)} in {routes_word(len(r.routes))}: dasselbe wie ohne Grenze ({de(a.split.cost)})." + tail
    return ("info" if extra < C.GAP_WARN else "warning"), (f"Mit höchstens {routes_word(bound)} kostet der Split {de(r.cost)}: {pct(extra)} mehr als ohne Grenze "
                                                          f"({de(a.split.cost)} in {routes_word(len(a.split.routes))})." + tail)


def verdict_fleet_summary(a: Analysis) -> tuple[str, str]:
    """Experiment 2: Greedy-Wert, Kosten der Flottengrenze bei g und g + 1 Routen und Mindestflotte im Optimum."""
    g = a.greedy
    at_g = a.fleet[g]
    extra_g = gap_percent(at_g.cost, a.split.cost)
    extra_g1 = gap_percent(a.fleet[g + 1].cost, a.split.cost) if g + 1 <= a.inst.n else 0.0
    text = (f"Diese Reihenfolge passt in mindestens {routes_word(g)} (der Wert von „Füllen bis voll“); der Split fährt {routes_word(len(a.split.routes))}. "
            f"Mit höchstens {routes_word(g)} kostet der Split {pct(extra_g)} mehr, mit {routes_word(g + 1)} {pct(extra_g1)} mehr. ")
    optimum_k, m = len(a.exact.routes), a.min_routes
    cost_m = a.exact_costs[m - 1] if m <= a.exact_max else None
    if cost_m is None:
        text += f"Die Mindestroutenzahl der Instanz ist {m}; das Optimum fährt {routes_word(optimum_k)}."
    elif math.isinf(cost_m):
        text += f"Die Mindestroutenzahl der Instanz ist {m}, aber mit höchstens {routes_word(m)} gibt es keinen zulässigen Plan; das Optimum fährt {routes_word(optimum_k)}."
    else:
        text += (f"Die Mindestroutenzahl der Instanz ist {m}; das Optimum fährt {routes_word(optimum_k)}, auf höchstens {routes_word(m)} beschränkt kostet es "
                 f"{pct(gap_percent(cost_m, a.exact.cost))} mehr.")
    return ("info" if extra_g < C.GAP_WARN else "warning"), text


def verdict_mirror(rows: list[dict]) -> tuple[str, str]:
    """Experiment 3: Spiegelpaar der Gleichstandsregel und Richtungsunterschied."""
    small, large = rows[2], rows[3]
    mirrored = small["order"] == large["order"][::-1]
    chosen_diff = gap_percent(max(rows[0]["fwd"], rows[0]["bwd"]), min(rows[0]["fwd"], rows[0]["bwd"]))
    head = (f"Die gewählte Reihenfolge ändert „Füllen bis voll“ beim Umdrehen um {pct(chosen_diff)} ({de(rows[0]['fwd'])} gegen {de(rows[0]['bwd'])}); der Split bleibt {de(rows[0]['split'])}. ")
    if not mirrored:
        return "info", head + "Einfügen nach Split findet hier keine Gleichstände, die beiden Regeln liefern dieselbe Reihenfolge."
    if abs(small["fwd"] - small["bwd"]) <= C.TOL:
        return "info", head + (f"Einfügen nach Split mit größerer statt kleinerer Stelle liefert genau das Spiegelbild, aber „Füllen bis voll“ ist hier in beiden Richtungen gleich "
                               f"({de(small['fwd'])}); der Split bleibt {de(small['split'])}.")
    tail = (f"Einfügen nach Split mit größerer statt kleinerer Stelle liefert genau das Spiegelbild; „Füllen bis voll“ vertauscht dabei Vorwärts- und Rückwärtswert "
            f"({de(small['fwd'])} / {de(small['bwd'])} gegen {de(large['fwd'])} / {de(large['bwd'])}), der Split bleibt {de(small['split'])}. Der Richtungsunterschied ist also ein Leserichtungseffekt von „Füllen bis voll“, den die Gleichstandsregel nur auswählt.")
    return "info", head + tail


def verdict_bands(n: int, fill: int, stats_by_key: dict) -> tuple[str, str]:
    """Experiment 4: Bänder einer Größe und Auslastung (alle vier Zellen zusammen)."""
    if not stats_by_key:
        return "warning", f"Die vorberechneten Bänder fehlen ({C.BAND_FILE})."
    count = next(iter(stats_by_key.values()))["count"]
    parts = []
    for key in C.BAND_KEYS:
        if key in stats_by_key:
            s = stats_by_key[key]["fwd"]
            parts.append(f"{C.ORDER_NAMES[key]} {pct(s['median'])} (Maximum {pct(s['max'])}, gleich in {s['equal']})")
    return "info", (f"Bei n = {n}, Auslastung {fill} % ({count} Instanzen): „Füllen bis voll“ vorwärts liegt über dem Split, Median je Reihenfolge: " + "; ".join(parts) + ".")


def verdict_price(fill: int, stats: dict) -> tuple[str, str]:
    """Preis der Mindestflotte im Optimum (n = 12, exakt)."""
    if not stats:
        return "warning", f"Die vorberechneten Bänder fehlen ({C.BAND_FILE})."
    mean_word = "im Mittel (über die zulässigen Instanzen)" if stats["infeasible"] else "im Mittel"
    text = (f"Bei Auslastung {fill} % ({stats['count']} Instanzen, n = 12) fährt das Optimum in {stats['more_than_min']} Instanzen mehr Routen als die Mindestroutenzahl; auf diese Zahl beschränkt "
            f"kostet es {mean_word} {pct(stats['mean'])} mehr (Maximum {pct(stats['max'])})")
    if stats["infeasible"]:
        text += f"; in {stats['infeasible']} Instanzen gibt es mit der Mindestroutenzahl gar keinen zulässigen Plan"
    return ("warning" if stats["max"] >= C.GAP_WARN else "info"), text + "."
