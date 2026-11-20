"""Figure 2: first-year enrollment by selectivity, 2020 and 2024 vs fall 2019.

Reads clean/dumbbell_covid.csv (made by clean_data.ipynb) and writes figures/fig2_covid_dumbbell.png.
Run from the repo root: python scripts/covid_dumbbell.py
"""
import pandas as pd
import plotly.graph_objects as go

from utils import BLUE, ORANGE, footnote, save, style

ORANGE_TEXT = "#b2480a"  # darker orange so the labels are readable


def pct(v):
    return f"{'+' if v > 0 else '−'}{abs(v):.1f}%"


def build_figure(df):
    tiers, n = df["tier"], df["n_schools"]
    fig = go.Figure()
    for tier, a, b in zip(tiers, df["2020"], df["2024"]):  # connector between the two years
        fig.add_trace(go.Scatter(x=[a, b], y=[tier, tier], mode="lines",
                                 line=dict(color="#d3d7db", width=4), hoverinfo="skip"))
    for year, color, text_color, side in (("2020", ORANGE, ORANGE_TEXT, "left"), ("2024", BLUE, BLUE, "right")):
        fig.add_trace(go.Scatter(
            x=df[year], y=tiers, mode="markers+text", text=df[year].map(pct),
            textposition=f"middle {side}", textfont=dict(size=13, color=text_color),
            marker=dict(size=15, color=color), customdata=n,
            hovertemplate=f"%{{y}}<br>{year}: %{{x:.1f}}% (%{{customdata}} schools)<extra></extra>"))
        fig.add_annotation(  # label each year above the top row, instead of a legend
            x=df[year][0], y=tiers[0], yshift=30, showarrow=False,
            text=f"<b>{year}</b>", font=dict(size=13, color=text_color))

    fig.update_xaxes(range=[-8, 14], ticksuffix="%", title_text="Change vs fall 2019",
                     gridcolor="#e8eaec", zerolinecolor="#8a9096", zerolinewidth=1.2)
    fig.update_yaxes(tickvals=tiers, ticktext=[f"{t}  (n={k})" for t, k in zip(tiers, n)],
                     autorange="reversed", showgrid=False, title_text="Admit rate in 2019", ticks="")
    fig.update_layout(showlegend=False)
    style(fig, "First-year enrollment by selectivity, 2020 and 2024", 900, 540, dict(l=150, r=30, t=100, b=130))
    footnote(fig, "Schools reporting first-year enrollment in 2019, 2020 and 2024. Each tier is summed enrollment.<br>"
                  "Open-admission schools are mostly missing. 2024 is provisional. Source: IPEDS.", y=-0.26)
    return fig


if __name__ == "__main__":
    save(build_figure(pd.read_csv("clean/dumbbell_covid.csv")), "fig2_covid_dumbbell")
