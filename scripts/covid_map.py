"""Figure 1: change in first-year enrollment by state, fall 2019 to fall 2020.

Reads clean/map_covid.csv (made by clean_data.ipynb) and writes figures/fig1_covid_map.png.
Run from the repo root: python scripts/covid_map.py
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go

from utils import footnote, save, style

CAP = 14  # color scale is capped at +/- this many percent
EDGES = [-14, -10, -6, -2, 0, 2, 6, 10, 14]
COLORS = ["#b2480a", "#e07b1f", "#f9bb7d", "#fde3c3", "#d4e6f4", "#9ecae1", "#4292c6", "#08519c"]
# states too small for an in-map label: (x, y, ax, ay) in plot coords and pixel offset of the text
CALLOUTS = {"HI": (0.357, 0.115, 0, 28), "DE": (0.814, 0.553, 55, 8)}


def color_scale():
    """Stepped colorscale, one flat color per bin (bins have unequal widths)."""
    pos = [(e + CAP) / (2 * CAP) for e in EDGES]
    return [[pos[i + j], c] for i, c in enumerate(COLORS) for j in (0, 1)]


def build_figure(map_covid):
    v, n = map_covid["2019-2020"], map_covid["n_schools"]
    star = lambda s: "*" if n[s] < 5 else ""  # marks states with very few schools
    fig = go.Figure(go.Choropleth(
        locations=v.index, z=v.clip(-CAP, CAP), locationmode="USA-states",
        colorscale=color_scale(), zmin=-CAP, zmax=CAP,
        marker_line_color="white", marker_line_width=0.6,
        customdata=np.c_[v, n],
        hovertemplate="%{location}: %{customdata[0]:.1f}% (%{customdata[1]} schools)<extra></extra>",
        colorbar=dict(title="Change in first-year<br>enrollment", tickvals=EDGES,
                      ticktext=[f"{e:+d}%" if e else "" for e in EDGES], len=0.9, thickness=14),
    ))

    # label the three biggest losses and gains (DC is too small to hold a label)
    top = v.drop("DC")
    top = pd.concat([top.nsmallest(3), top.nlargest(3)])
    inset = top[top.index.isin(CALLOUTS)]  # tiny states get a callout line instead
    top = top.drop(inset.index)
    fig.add_trace(go.Scattergeo(
        locations=top.index, locationmode="USA-states", mode="text", hoverinfo="skip",
        text=[f"{s}{star(s)}<br>{x:+.0f}%" for s, x in top.items()],
        textfont=dict(size=11, color=["white" if abs(x) >= 10 else "black" for x in top]),
    ))
    for s, x in inset.items():
        cx, cy, ax, ay = CALLOUTS[s]
        fig.add_annotation(x=cx, y=cy, ax=ax, ay=ay, axref="pixel", ayref="pixel",
                           xref="paper", yref="paper", text=f"{s}{star(s)} {x:+.0f}%",
                           arrowhead=0, arrowwidth=1, arrowcolor="#555", font=dict(size=14))

    fig.update_geos(scope="usa", projection_type="albers usa", showframe=False,  # no fills that carry no data
                    showlakes=False, showocean=False, showland=False, showcountries=False, showcoastlines=False)
    fig.update_layout(showlegend=False)
    style(fig, "Change in first-year enrollment, fall 2019 to fall 2020", 1000, 640, dict(l=20, r=20, t=80, b=60))
    footnote(fig, "Schools reporting first-year enrollment in both 2019 and 2020. Scale capped at "
                  f"{CAP}%. * fewer than 5 schools in the state. Alaska and Hawaii are not to scale. Source: IPEDS.", y=-0.01)
    return fig


if __name__ == "__main__":
    save(build_figure(pd.read_csv("clean/map_covid.csv", index_col="state")), "fig1_covid_map")
