"""Erzeugt sgf_bands.json: die Bänder über feste Instanzen (Zerlegung derselben Reihenfolge durch „Füllen bis voll“ und Split) und den Preis der Mindestflotte im Optimum.

Reihenfolgen und Zerlegungen rechnen schnell (n = 100: etwa 1 s je Instanz, Einfügen nach Split dort ausgelassen), der Preis der Mindestflotte braucht den exakten Löser (n = 12, etwa 5 s je Instanz).

Aufruf (Teile können parallel laufen):
    python generate_precomputed.py orders 12 90 --out part_12_90.json        # Reihenfolgen: n, Auslastungen in Prozent
    python generate_precomputed.py orders 25 60 75 90 98 --out part_25.json
    python generate_precomputed.py price 90 95 --out part_price_a.json       # Preis der Mindestflotte: Auslastungen in Prozent
    python generate_precomputed.py merge part_12_90.json part_25.json ...    # zu sgf_bands.json zusammenführen"""

import argparse
import json
import time
from pathlib import Path

import sgf_constants as C
from sgf_evaluation import instance_row, price_row

TARGET = Path(__file__).with_name(C.BAND_FILE)


def build_orders(n: int, fills) -> list[dict]:
    cells, start = [], time.time()
    for fill in fills:
        for family, depot in C.BAND_CELLS:
            rows = [instance_row(n, family, depot, seed, fill) for seed in C.BAND_SEEDS[n]]
            cells.append({"n": n, "fill": fill, "family": family, "depot": depot, "rows": rows})
            print("orders", n, fill, family, depot, f"{time.time() - start:.0f} s", flush=True)
    return cells


def build_price(fills) -> list[dict]:
    cells, start = [], time.time()
    for fill in fills:
        for family, depot in C.BAND_CELLS:
            rows = [price_row(family, depot, seed, fill) for seed in C.PRICE_SEEDS]
            cells.append({"fill": fill, "family": family, "depot": depot, "rows": rows})
            print("price", fill, family, depot, f"{time.time() - start:.0f} s", flush=True)
    return cells


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=["orders", "price", "merge"])
    ap.add_argument("args", nargs="+")
    ap.add_argument("--out")
    args = ap.parse_args()
    if args.kind == "merge":
        cells, price = [], []
        for f in args.args:
            data = json.loads(Path(f).read_text(encoding="utf-8"))
            cells += data.get("cells", [])
            price += data.get("price", [])
        key = {cell: i for i, cell in enumerate(C.BAND_CELLS)}
        cells.sort(key=lambda c: (c["n"], c["fill"], key[(c["family"], c["depot"])]))
        price.sort(key=lambda c: (c["fill"], key[(c["family"], c["depot"])]))
        meta = {"routes": C.BAND_ROUTES, "seeds": {str(n): [s[0], s[-1]] for n, s in C.BAND_SEEDS.items()}, "price_seeds": [C.PRICE_SEEDS[0], C.PRICE_SEEDS[-1]]}
        TARGET.write_text(json.dumps({"meta": meta, "cells": cells, "price": price}, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", TARGET.name, len(cells), "Zellen,", len(price), "Preiszellen")
    else:
        data = {"cells": build_orders(int(args.args[0]), [int(x) for x in args.args[1:]])} if args.kind == "orders" else {"price": build_price([int(x) for x in args.args])}
        Path(args.out).write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        print("geschrieben:", args.out)
