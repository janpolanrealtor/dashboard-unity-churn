import pandas as pd
import plotly.graph_objects as go

# Haven design tokens
BRAND = "#D92228"
CHARCOAL = "#3F3B36"
GRAY_1200 = "#1A1816"
GRAY_700 = "#726A60"
GRAY_200 = "#E9E7E4"
GRAY_100 = "#F2F0EF"
GRAY_50 = "#F8F7F7"
GREEN_700 = "#46A758"
GREEN_900 = "#2A7E3B"
RED_100 = "#FEE2E3"
BLUE_800 = "#15459A"
TEAL_700 = "#008583"

# Only keys that are truly identical on every chart.
# xaxis, yaxis, margin must NOT be here — they differ per chart and would
# cause "multiple values for keyword argument" if also passed to update_layout.
_BASE = dict(
    font=dict(family="'Galano Grotesque Alt', 'Inter', sans-serif", color=GRAY_700, size=12),
    plot_bgcolor="rgba(0,0,0,0)",
    paper_bgcolor="rgba(0,0,0,0)",
)

# Reusable axis grid style — spread into each axis dict per chart.
_AXIS = dict(gridcolor=GRAY_200, zerolinecolor=GRAY_200, linecolor=GRAY_200)


def churn_trend_chart(df: pd.DataFrame):
    """Line chart of churn probability over snapshot dates for a single asset."""
    if df.empty or len(df) < 2:
        return None

    df = df.copy().sort_values("SNAPSHOT_DATE")

    fig = go.Figure()

    # Danger zone band at 70%
    fig.add_hrect(
        y0=0.7,
        y1=1.0,
        fillcolor=RED_100,
        opacity=0.4,
        layer="below",
        line_width=0,
    )
    fig.add_hline(
        y=0.7,
        line_dash="dot",
        line_color=BRAND,
        line_width=1,
        annotation_text="High-risk threshold",
        annotation_position="top right",
        annotation_font_size=11,
        annotation_font_color=BRAND,
    )

    fig.add_trace(
        go.Scatter(
            x=df["SNAPSHOT_DATE"],
            y=df["CHURN_PROB"],
            mode="lines+markers",
            name="Churn Probability",
            line=dict(color=BRAND, width=2.5),
            marker=dict(size=7, color=BRAND, line=dict(color="#fff", width=2)),
            hovertemplate="%{x}<br>Churn: %{y:.1%}<extra></extra>",
        )
    )

    fig.update_layout(
        **_BASE,
        title=dict(text="Churn Probability Over Time", font=dict(size=14, color=GRAY_1200), x=0),
        xaxis=dict(**_AXIS, title="Snapshot Date"),
        yaxis=dict(**_AXIS, tickformat=".0%", range=[0, 1]),
        margin=dict(l=8, r=8, t=32, b=8),
        showlegend=False,
    )
    return fig


def pipeline_history_chart(df: pd.DataFrame):
    """Dual-axis bar + line chart for pipeline run history."""
    fig = go.Figure()

    fig.add_trace(
        go.Bar(
            x=df["SNAPSHOT_DATE"],
            y=df["TOTAL_ASSETS"],
            name="Total Assets",
            marker_color=GRAY_200,
            yaxis="y1",
            hovertemplate="%{x}<br>Assets: %{y:,}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["SNAPSHOT_DATE"],
            y=df["AVG_CHURN_PROB"],
            name="Avg Churn Prob",
            mode="lines+markers",
            line=dict(color=BRAND, width=2.5),
            marker=dict(size=7, color=BRAND, line=dict(color="#fff", width=2)),
            yaxis="y2",
            hovertemplate="%{x}<br>Avg churn: %{y:.1%}<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df["SNAPSHOT_DATE"],
            y=df["HIGH_RISK_RATE"],
            name="High-Risk Rate (>70%)",
            mode="lines+markers",
            line=dict(color=BRAND, width=2, dash="dot"),
            marker=dict(size=6, color=BRAND),
            yaxis="y2",
            hovertemplate="%{x}<br>High-risk rate: %{y:.1%}<extra></extra>",
        )
    )

    fig.update_layout(
        **_BASE,
        title=dict(
            text="Pipeline Run History — Volume & Churn Risk",
            font=dict(size=14, color=GRAY_1200),
            x=0,
        ),
        xaxis=dict(**_AXIS, title="Snapshot Date"),
        yaxis=dict(**_AXIS, title="Total Assets"),
        yaxis2=dict(
            title="Churn Rate",
            side="right",
            overlaying="y",
            tickformat=".0%",
            gridcolor="rgba(0,0,0,0)",
        ),
        legend=dict(orientation="h", yanchor="bottom", y=-0.45, xanchor="center", x=0.5),
        margin=dict(l=8, r=8, t=32, b=100),
        barmode="group",
    )
    return fig


def feature_importance_chart(df: pd.DataFrame):
    """Horizontal bar chart of top churn drivers."""
    df = df.rename(columns={"asset_count": "ASSET_COUNT", "avg_churn_prob": "AVG_CHURN_PROB"})
    top = df.head(10).sort_values("ASSET_COUNT")

    colors = [
        BRAND if p > 0.7 else (CHARCOAL if p > 0.4 else GREEN_700) for p in top["AVG_CHURN_PROB"]
    ]

    fig = go.Figure(
        go.Bar(
            x=top["ASSET_COUNT"],
            y=top["MOST_IMPORTANT_FEATURE"],
            orientation="h",
            marker=dict(color=colors),
            customdata=top["AVG_CHURN_PROB"],
            hovertemplate="%{y}<br>Assets: %{x:,}<br>Avg churn: %{customdata:.1%}<extra></extra>",
        )
    )

    fig.update_layout(
        **_BASE,
        title=dict(
            text="Top 10 Churn Drivers by Asset Count", font=dict(size=14, color=GRAY_1200), x=0
        ),
        xaxis=dict(**_AXIS, title="Number of Assets"),
        yaxis=dict(**_AXIS, autorange="reversed"),
        margin=dict(l=8, r=8, t=32, b=8),
        showlegend=False,
    )
    return fig


def survival_distribution_chart(df: pd.DataFrame):
    """Histogram of churn probability distribution with risk zone shading."""
    fig = go.Figure()

    # Risk zone bands
    fig.add_vrect(
        x0=0.7,
        x1=1.0,
        fillcolor=RED_100,
        opacity=0.5,
        layer="below",
        line_width=0,
        annotation_text="High risk",
        annotation_position="top right",
        annotation_font=dict(size=11, color=BRAND),
    )
    fig.add_vrect(
        x0=0.4,
        x1=0.7,
        fillcolor="#FFF9E9",
        opacity=0.5,
        layer="below",
        line_width=0,
        annotation_text="Medium",
        annotation_position="top right",
        annotation_font=dict(size=11, color="#685700"),
    )

    fig.add_trace(
        go.Histogram(
            x=df["CHURN_PROB"],
            nbinsx=20,
            marker_color=CHARCOAL,
            marker_line=dict(color="#fff", width=1),
            hovertemplate="Range: %{x}<br>Count: %{y:,}<extra></extra>",
        )
    )

    fig.update_layout(
        **_BASE,
        title=dict(text="Churn Probability Distribution", font=dict(size=14, color=GRAY_1200), x=0),
        xaxis=dict(**_AXIS, title="Churn Probability", tickformat=".0%"),
        yaxis=dict(**_AXIS, title="Number of Assets"),
        margin=dict(l=8, r=8, t=32, b=8),
        showlegend=False,
    )
    return fig


def plot_quartile_indicator(
    current_val: float,
    q1_val: float,
    q3_val: float,
    feature_name: str,
    lower_is_better: bool = True,
    fmt=None,
    tick_format: str = None,
):
    """Compact horizontal quartile range plot (height ~110px).
    Line = IQR axis; triangle markers at Q1/Q3; larger circle for current value.
    Color coding: green end = favorable, red end = risk.
    fmt: callable for value labels (defaults to {v:,.1f}).
    tick_format: Plotly d3 format string for the x-axis ticks (e.g. ".0%", "$,.0f").
    """
    if fmt is None:

        def fmt(v):
            return f"{v:,.1f}"

    if lower_is_better:
        q1_color, q3_color = GREEN_700, BRAND
    else:
        q1_color, q3_color = BRAND, GREEN_700

    # Axis span with 20% padding on each side
    span = max(q3_val - q1_val, 1e-9)
    x_min = q1_val - 0.2 * span
    x_max = q3_val + 0.2 * span
    if current_val < x_min:
        x_min = current_val - 0.1 * span
    if current_val > x_max:
        x_max = current_val + 0.1 * span

    fig = go.Figure()

    # IQR range bar (thick line between Q1 and Q3)
    fig.add_shape(
        type="line",
        x0=q1_val,
        x1=q3_val,
        y0=0.5,
        y1=0.5,
        yref="paper",
        line=dict(color=GRAY_200, width=8),
    )

    # Q1 triangle marker
    fig.add_trace(
        go.Scatter(
            x=[q1_val],
            y=[0.5],
            mode="markers",
            marker=dict(
                symbol="triangle-up",
                size=14,
                color=q1_color,
                line=dict(color="#fff", width=1),
            ),
            name=f"Q1: {fmt(q1_val)}",
            hovertemplate=f"Q1 (25th pct): {fmt(q1_val)}<extra></extra>",
            showlegend=True,
        )
    )

    # Q3 triangle marker
    fig.add_trace(
        go.Scatter(
            x=[q3_val],
            y=[0.5],
            mode="markers",
            marker=dict(
                symbol="triangle-up",
                size=14,
                color=q3_color,
                line=dict(color="#fff", width=1),
            ),
            name=f"Q3: {fmt(q3_val)}",
            hovertemplate=f"Q3 (75th pct): {fmt(q3_val)}<extra></extra>",
            showlegend=True,
        )
    )

    # Current value — larger circle with border
    _good = (lower_is_better and current_val <= q1_val) or (
        not lower_is_better and current_val >= q3_val
    )
    _bad = (lower_is_better and current_val >= q3_val) or (
        not lower_is_better and current_val <= q1_val
    )
    cur_color = GREEN_700 if _good else (BRAND if _bad else CHARCOAL)
    fig.add_trace(
        go.Scatter(
            x=[current_val],
            y=[0.5],
            mode="markers",
            marker=dict(
                symbol="circle",
                size=18,
                color=cur_color,
                line=dict(color="#fff", width=2),
            ),
            name=f"This asset: {fmt(current_val)}",
            hovertemplate=f"This asset: {fmt(current_val)}<extra></extra>",
            showlegend=True,
        )
    )

    _xaxis = dict(
        range=[x_min, x_max],
        showgrid=False,
        zeroline=False,
        showline=False,
        tickfont=dict(size=11, color=GRAY_700),
    )
    if tick_format:
        _xaxis["tickformat"] = tick_format

    fig.update_layout(
        **_BASE,
        title=dict(text=feature_name, font=dict(size=13, color=GRAY_1200), x=0),
        xaxis=_xaxis,
        yaxis=dict(
            showgrid=False,
            zeroline=False,
            showline=False,
            showticklabels=False,
            range=[0, 1],
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.6,
            xanchor="center",
            x=0.5,
            font=dict(size=11),
            bgcolor="rgba(0,0,0,0)",
        ),
        margin=dict(l=0, r=0, t=28, b=48),
        height=110,
        showlegend=True,
    )
    return fig


def asset_distribution_chart(
    population: pd.Series, entity_value: float, entity_label: str = "Selected Asset"
):
    """
    Population histogram with entity position marked.
    Uses add_shape + add_annotation pairs (never add_vline with annotation_text)
    so reference labels can be staggered vertically without overlap.
    """
    fig = go.Figure()

    # Risk zone bands
    fig.add_vrect(x0=0.7, x1=1.0, fillcolor=RED_100, opacity=0.4, layer="below", line_width=0)
    fig.add_vrect(x0=0.4, x1=0.7, fillcolor="#FFF9E9", opacity=0.4, layer="below", line_width=0)

    # Population histogram base trace
    fig.add_trace(
        go.Histogram(
            x=population,
            nbinsx=30,
            marker_color=GRAY_200,
            marker_line=dict(color=GRAY_100, width=0.5),
            name="All assets",
            hovertemplate="Range: %{x}<br>Count: %{y:,}<extra></extra>",
        )
    )

    # Reference lines — staggered add_shape + add_annotation to prevent overlap
    refs = [
        (float(population.quantile(0.25)), "Q1", GRAY_700, "dot", 0.97),
        (float(population.median()), "Median", TEAL_700, "dash", 0.87),
        (float(population.mean()), "Mean", BLUE_800, "dot", 0.77),
        (float(population.quantile(0.75)), "Q3", GRAY_700, "dot", 0.67),
        (float(entity_value), entity_label[:20], BRAND, "solid", 0.57),
    ]

    for x_val, ref_label, color, dash, y_paper in refs:
        fig.add_shape(
            type="line",
            x0=x_val,
            x1=x_val,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color=color, width=1.5, dash=dash),
        )
        fig.add_annotation(
            x=x_val,
            y=y_paper,
            yref="paper",
            text=f"{ref_label}: {x_val:.1%}",
            showarrow=False,
            xanchor="left",
            xshift=4,
            font=dict(size=11, color=color),
            bgcolor="rgba(255,255,255,0.7)",
        )

    fig.update_layout(
        **_BASE,
        title=dict(
            text="Churn Probability — Portfolio Position", font=dict(size=14, color=GRAY_1200), x=0
        ),
        xaxis=dict(**_AXIS, title="Churn Probability", tickformat=".0%"),
        yaxis=dict(**_AXIS, title="Number of Assets"),
        margin=dict(l=8, r=8, t=32, b=8),
        height=450,
        showlegend=False,
    )
    return fig
