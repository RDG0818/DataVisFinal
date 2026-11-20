"""Shared styling and export code for the figure scripts."""
from pathlib import Path

ORANGE, BLUE = "#e07b1f", "#08519c"
FONT = "Helvetica, Arial, sans-serif"


def style(fig, title, width, height, margin):
    """Centered title, one sans serif font, white background."""
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor="center", font=dict(size=20)),
        font=dict(family=FONT, size=13, color="#222"),
        paper_bgcolor="white", plot_bgcolor="white",
        width=width, height=height, margin=margin,
    )


def footnote(fig, text, y):
    """Small gray left-aligned note under the plot (y is in paper coordinates)."""
    fig.add_annotation(
        xref="paper", yref="paper", x=0, y=y, xanchor="left", yanchor="top",
        showarrow=False, align="left", text=text, font=dict(size=11, color="#555"),
    )


def save(fig, name):
    """Write figures/<name>.png, or an html file if the PNG export fails (kaleido needs Chrome)."""
    Path("figures").mkdir(exist_ok=True)
    try:
        fig.write_image(f"figures/{name}.png", scale=2)
        print(f"wrote figures/{name}.png")
    except Exception as e:
        print("png export failed:", e)
        fig.write_html(f"figures/{name}.html")
        print(f"wrote figures/{name}.html")
