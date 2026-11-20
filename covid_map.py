"""Figure 1: change in first-year enrollment by state, fall 2019 to fall 2020.

Reads clean/map_covid.csv (made by clean_data.ipynb) and writes figures/fig1_covid_map.png.
Run from the repo root: python covid_map.py
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go

CAP = 14  # color scale is capped at +/- this many percent
EDGES = [-14, -10, -6, -2, 0, 2, 6, 10, 14]
COLORS = ["#b2480a", "#e07b1f", "#f9bb7d", "#fde3c3", "#d4e6f4", "#9ecae1", "#4292c6", "#08519c"]
COL = "2019-2020"
# states too small for an in-map label: (x, y, ax, ay) in plot coords and pixel offset of the text
CALLOUTS = {"HI": (0.357, 0.115, 0, 28), "DE": (0.814, 0.553, 55, 8)}


def color_scale():
    """Stepped colorscale, one flat color per bin (bins have unequal widths)."""
    pos = [(e + CAP) / (2 * CAP) for e in EDGES]
    scale = []
    for i, c in enumerate(COLORS):
        scale += [[pos[i], c], [pos[i + 1], c]]
    return scale


def build_figure(map_covid):
    fig = go.Figure()
    n = map_covid["n_schools"]
    v = map_covid[COL]
    fig.add_trace(go.Choropleth(
        locations=v.index, z=v.clip(-CAP, CAP), locationmode="USA-states",
        colorscale=color_scale(), zmin=-CAP, zmax=CAP,
        marker_line_color="white", marker_line_width=0.6,
        customdata=np.c_[v.values, n.values],
        hovertemplate="%{location}: %{customdata[0]:.1f}% (%{customdata[1]} schools)<extra></extra>",
        colorbar=dict(title="Change in first-year<br>enrollment", tickvals=EDGES,
                      ticktext=[f"{e:+d}%" if e else "" for e in EDGES], len=0.9, thickness=14),
    ))

    # label the three biggest losses and gains (DC is too small to hold a label)
    vv = v.drop("DC")
    lab = pd.concat([vv.nsmallest(3), vv.nlargest(3)])
    called = lab[lab.index.isin(CALLOUTS)]
    lab = lab.drop(called.index)
    text = [f"{s}{'*' if n[s] < 5 else ''}<br>{x:+.0f}%" for s, x in lab.items()]
    colors = ["white" if abs(x) >= 10 else "black" for s, x in lab.items()]
    fig.add_trace(go.Scattergeo(
        locations=lab.index, locationmode="USA-states", mode="text", text=text,
        textfont=dict(size=11, color=colors), hoverinfo="skip", showlegend=False,
    ))

    for st, x in called.items():
        cx, cy, ax, ay = CALLOUTS[st]
        fig.add_annotation(
            xref="paper", yref="paper", x=cx, y=cy, ax=ax, ay=ay, axref="pixel", ayref="pixel",
            text=f"{st}{'*' if n[st] < 5 else ''} {x:+.0f}%", showarrow=True,
            arrowhead=0, arrowwidth=1, arrowcolor="#555", font=dict(size=14, color="black"),
        )

    fig.update_geos(scope="usa", projection_type="albers usa", showlakes=False,
                    showocean=False, showland=False, showcountries=False,
                    showcoastlines=False, showframe=False, bgcolor="white")
    fig.update_layout(
        title=dict(text="Change in first-year enrollment, fall 2019 to fall 2020",
                   x=0.5, xanchor="center", font=dict(size=20)),
        font=dict(family="Helvetica, Arial, sans-serif", size=13, color="#222"),
        paper_bgcolor="white", plot_bgcolor="white",
        width=1000, height=640, margin=dict(l=20, r=20, t=80, b=60),
    )
    fig.add_annotation(
        xref="paper", yref="paper", x=0.01, y=-0.02, xanchor="left", showarrow=False,
        align="left",
        text="Schools reporting first-year enrollment in both 2019 and 2020. "
             f"Scale capped at {CAP}%. * fewer than 5 schools in the state. Alaska and Hawaii are not to scale. Source: IPEDS.",
        font=dict(size=11, color="#555"),
    )
    return fig


def main():
    map_covid = pd.read_csv("clean/map_covid.csv", index_col="state")
    fig = build_figure(map_covid)
    Path("figures").mkdir(exist_ok=True)
    try:
        fig.write_image("figures/fig1_covid_map.png", scale=2)
        print("wrote figures/fig1_covid_map.png")
    except Exception as e:  # kaleido needs Chrome; fall back to html
        print("png export failed:", e)
        fig.write_html("figures/fig1_covid_map.html")
        print("wrote figures/fig1_covid_map.html")


if __name__ == "__main__":
    main()
