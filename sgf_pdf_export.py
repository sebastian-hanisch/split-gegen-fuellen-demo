"""PDF-Export des aktuellen Ergebnisses (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import sgf_constants as C
from sgf_evaluation import Analysis, Settings, de, gap_percent, order_text, pct

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "×": "x", "„": '"', "“": '"', "²": "2"}


def _s(text) -> str:
    out = str(text).replace("**", "").replace("`", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(s: Settings, a: Analysis) -> bytes:
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Split gegen Füllen bis voll"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, _s(f"{s.n} Kunden, Karte: {C.FAMILIES[s.family]}, Depot: {C.DEPOTS[s.depot].lower()}, Zielroutenzahl {s.routes}, Auslastung {s.fill} %, Seed {s.seed}. "
                            f"Kapazität {a.inst.capacity}, Gesamtnachfrage {sum(a.inst.demand)}, Mindestroutenzahl {a.min_routes}. Reihenfolge ({C.ORDER_NAMES[a.order_key]}): {order_text(a.order)}. Alles simuliert."),
                   new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    widths = (70, 28, 22, 30, 36)
    pdf.set_font("Helvetica", "B", 9)
    for w, h in zip(widths, ("Zerlegung", "Kosten", "Routen", "Über Split", "Über Optimum")):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 9)
    rows = (("Optimum (alle Tourenpläne)", a.exact.cost, len(a.exact.routes)), ("Split der Reihenfolge", a.split.cost, len(a.split.routes)),
            ("Füllen bis voll, vorwärts", a.fill_fwd.cost, len(a.fill_fwd.routes)), ("Füllen bis voll, rückwärts", a.fill_bwd.cost, len(a.fill_bwd.routes)))
    for name, cost, k in rows:
        for w, v in zip(widths, (name, de(cost), str(k), pct(gap_percent(cost, a.split.cost)), pct(gap_percent(cost, a.exact.cost)))):
            pdf.cell(w, 5.5, _s(v), border=1)
        pdf.ln()
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 9)
    pdf.cell(0, 6, _s("Split mit höchstens B Routen"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 9)
    for bound in range(1, min(a.inst.n, a.greedy + 3) + 1):
        r = a.fleet[bound]
        pdf.cell(0, 5, _s(f"B = {bound}: " + ("nicht zerlegbar" if r is None else f"{de(r.cost)} in {len(r.routes)} Routen")), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Der Split zerlegt eine Reihenfolge per kürzestem Weg im Hilfsgraphen optimal in Routen; Füllen bis voll beginnt eine neue Route, sobald der nächste Kunde nicht mehr passt. "
                            "Quelle: split-gegen-fuellen-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
