"""Figure 2: first-year enrollment by selectivity, fall 2020 and fall 2024 vs fall 2019.

Reads clean/dumbbell_covid.csv (made by clean_data.ipynb) and writes figures/fig2_covid_dumbbell.png.
Run from the repo root: python scripts/covid_dumbbell.py
"""
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

ORANGE, BLUE, LINK = "#e07b1f", "#08519c", "#d3d7db"
ORANGE_TEXT = "#b2480a"


def fmt(v):
    sign = "+" if v > 0.05 else "−" if v < -0.05 else ""
    return f"{sign}{abs(v):.1f}%"


def build_figure(df):
    ys = df["tier"].tolist()
    v20, v24 = df["2020"].tolist(), df["2024"].tolist()
    fig = go.Figure()
    for y, a, b in zip(ys, v20, v24):  # connector from 2020 to 2024
        fig.add_trace(go.Scatter(x=[a, b], y=[y, y], mode="lines", line=dict(color=LINK, width=4),
                                 hoverinfo="skip", showlegend=False))
    for vals, color, text_color, pos, name in ((v20, ORANGE, ORANGE_TEXT, "middle left", "2020"),
                                               (v24, BLUE, BLUE, "middle right", "2024")):
        fig.add_trace(go.Scatter(
            x=vals, y=ys, mode="markers+text", text=[fmt(v) for v in vals], textposition=pos,
            textfont=dict(size=13, color=text_color), marker=dict(size=15, color=color),
            customdata=df["n_schools"],
            hovertemplate=f"%{{y}}<br>{name}: %{{x:.1f}}% (%{{customdata}} schools)<extra></extra>",
            showlegend=False))

    fig.update_xaxes(range=[-8, 14], showgrid=True, gridcolor="#e8eaec", zeroline=True,
                     zerolinecolor="#8a9096", zerolinewidth=1.2, ticksuffix="%", showline=False,
                     title_text="Change vs fall 2019")
    fig.update_yaxes(tickvals=ys, ticktext=[f"{t}  (n={n})" for t, n in zip(ys, df["n_schools"])],
                     autorange="reversed", showgrid=False, zeroline=False, showline=False, ticks="",
                     title_text="Admit rate in 2019")
    fig.update_layout(
        title=dict(text="First-year enrollment by selectivity, 2020 and 2024",
                   x=0.5, xanchor="center", font=dict(size=20)),
        font=dict(family="Helvetica, Arial, sans-serif", size=13, color="#222"),
        paper_bgcolor="white", plot_bgcolor="white",
        width=900, height=540, margin=dict(l=150, r=30, t=100, b=130),
    )
    for vals, color, name in ((v20, ORANGE_TEXT, "2020"), (v24, BLUE, "2024")):
        fig.add_annotation(  # direct labels above the top row, instead of a legend
            xref="x", yref="y", x=vals[0], y=ys[0], yshift=30, showarrow=False,
            text=f"<b>{name}</b>", font=dict(size=13, color=color))
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=-0.26, xanchor="left", yanchor="top", showarrow=False,
        align="left",
        text="Schools reporting first-year enrollment in 2019, 2020 and 2024. Each tier is summed enrollment.<br>"
             "Open-admission schools are mostly missing. 2024 is provisional. Source: IPEDS.",
        font=dict(size=11, color="#555"))
    return fig


def main():
    df = pd.read_csv("clean/dumbbell_covid.csv")
    fig = build_figure(df)
    Path("figures").mkdir(exist_ok=True)
    try:
        fig.write_image("figures/fig2_covid_dumbbell.png", scale=2)
        print("wrote figures/fig2_covid_dumbbell.png")
    except Exception as e:  # kaleido needs Chrome; fall back to html
        print("png export failed:", e)
        fig.write_html("figures/fig2_covid_dumbbell.html")
        print("wrote figures/fig2_covid_dumbbell.html")


if __name__ == "__main__":
    main()
