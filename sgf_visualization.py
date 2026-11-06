"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import sgf_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=380):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def build_map(inst, routes, title_prefix="Route"):
    """Karte: Depot als Quadrat, Kunden als Kreise (Größe = Nachfrage, Beschriftung = Nummer), jede Route eine Farbe. Gleicher Maßstab in x und y über scaleanchor mit
    autorange; der Rand kommt von zwei unsichtbaren Eckmarken (DEMO-PLAYBOOK §3)."""
    xs = [p[0] for p in inst.xy]
    ys = [p[1] for p in inst.xy]
    pad = 0.08 * max(max(xs) - min(xs), max(ys) - min(ys), 1.0)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=[min(xs) - pad, max(xs) + pad], y=[min(ys) - pad, max(ys) + pad], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    for r, route in enumerate(routes):
        pts = [inst.xy[0]] + [inst.xy[c] for c in route] + [inst.xy[0]]
        fig.add_trace(go.Scatter(x=[p[0] for p in pts], y=[p[1] for p in pts], mode="lines", line=dict(color=C.ROUTE_COLORS[r % len(C.ROUTE_COLORS)], width=3),
                                 name=f"{title_prefix} {r + 1} (Last {inst.load(route)} von {inst.capacity})", hoverinfo="skip"))
    customers = list(range(1, inst.n + 1))
    fig.add_trace(go.Scatter(
        x=[inst.xy[c][0] for c in customers], y=[inst.xy[c][1] for c in customers], mode="markers+text", text=[str(c) for c in customers], textposition="top center",
        marker=dict(size=[9 + 2.5 * inst.demand[c - 1] for c in customers], color="rgba(150,150,150,0.55)", line=dict(color="#555", width=1)),
        customdata=[[inst.demand[c - 1]] for c in customers], hovertemplate="Kunde %{text}: Nachfrage %{customdata[0]}<extra></extra>", name="Kunden (Größe = Nachfrage)"))
    fig.add_trace(go.Scatter(x=[inst.xy[0][0]], y=[inst.xy[0][1]], mode="markers", marker=dict(symbol="square", size=15, color="#222"), name="Depot", hoverinfo="skip"))
    fig.update_yaxes(scaleanchor="x", scaleratio=1, showgrid=False, zeroline=False, showticklabels=False)
    fig.update_xaxes(showgrid=False, zeroline=False, showticklabels=False)
    return _base(fig, 380)


def build_fleet_curve(split_by_bound, exact_costs, greedy):
    """Kosten über der Flottengrenze B: der Split der gewählten Reihenfolge (Stufenlinie ab dem Greedy-Wert; davor nicht zerlegbar) und das exakte Optimum mit höchstens B Routen."""
    bounds = [b for b, r in split_by_bound.items() if r is not None]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=bounds, y=[split_by_bound[b].cost for b in bounds], mode="lines+markers", line=dict(color=C.COLOR_SPLIT, width=3, shape="hv"), marker=dict(size=9),
                             name="Split mit höchstens B Routen", hovertemplate="B = %{x}: %{y:.2f}<extra></extra>"))
    exact = [(b + 1, c) for b, c in enumerate(exact_costs) if not math.isinf(c)]
    if exact:
        fig.add_trace(go.Scatter(x=[b for b, _ in exact], y=[c for _, c in exact], mode="lines+markers", line=dict(color=C.COLOR_OPT, width=2, dash="dash", shape="hv"),
                                 marker=dict(size=8, symbol="diamond"), name="Optimum mit höchstens B Routen", hovertemplate="B = %{x}: %{y:.2f}<extra></extra>"))
    fig.add_vline(x=greedy, line=dict(color="#999", width=1, dash="dot"), annotation_text=f"„Füllen“: {greedy}", annotation_position="top")
    fig.update_xaxes(title_text="Höchstzahl der Routen B", dtick=1)
    fig.update_yaxes(title_text="Gesamtlänge")
    fig = _base(fig, 380)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10))      # Platz für die Beschriftung der senkrechten Linie
    return fig


def build_bands(stats_by_key):
    """Median der Mehrkosten von „Füllen bis voll“ (vorwärts) über dem Split je Reihenfolge, mit Spanne (Minimum bis Maximum) als Fehlerbalken."""
    keys = [k for k in C.BAND_KEYS if k in stats_by_key]
    fig = go.Figure(go.Bar(
        x=[C.ORDER_NAMES[k] for k in keys], y=[stats_by_key[k]["fwd"]["median"] for k in keys], marker_color=[C.ORDER_COLORS[k] for k in keys],
        error_y=dict(type="data", symmetric=False, array=[stats_by_key[k]["fwd"]["max"] - stats_by_key[k]["fwd"]["median"] for k in keys],
                     arrayminus=[stats_by_key[k]["fwd"]["median"] - stats_by_key[k]["fwd"]["min"] for k in keys]),
        hovertemplate="%{x}: Median %{y:.1f} %<extra></extra>", name="Median (Balken: Minimum bis Maximum)"))
    fig.update_yaxes(title_text="Mehrkosten gegen den Split (%)", rangemode="tozero")
    return _base(fig, 340)
