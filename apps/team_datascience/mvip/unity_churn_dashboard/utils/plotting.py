import plotly.io as pio
import plotly.graph_objects as go
import plotly.express as px

ACCENT_RED = "#D92228"
CHARCOAL = "#3F3B36"
WARM_GRAY = "#F4F3F0"
GRID_COLOR = "#E0DDD8"

pio.templates["haven"] = go.layout.Template(
    layout=dict(
        font=dict(family="sans serif", color=CHARCOAL),
        title=dict(font=dict(color=ACCENT_RED, size=18)),
        colorway=[ACCENT_RED, CHARCOAL, WARM_GRAY],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    )
)
pio.templates.default = "haven"


def trend_chart(df):
    fig = px.line(
        df,
        x="MONTH_OF_EXPIRY",
        y="avg_churn_prob",
        title="Average Churn Risk Over Expiry Months",
        labels={
            "MONTH_OF_EXPIRY": "Expiry Month",
            "avg_churn_prob": "Avg Churn Probability",
        },
        markers=True,
    )
    fig.update_traces(
        line=dict(color=ACCENT_RED, width=3),
        marker=dict(color=ACCENT_RED, size=8),
    )
    fig.update_layout(
        xaxis_title="Expiry Month",
        yaxis_title="Avg Churn Probability",
        yaxis_tickformat=".0%",
    )
    return fig


def feature_importance_chart(df):
    fig = px.bar(
        df.head(10),
        x="asset_count",
        y="MOST_IMPORTANT_FEATURE",
        orientation="h",
        title="Top 10 Feature Importance",
        labels={
            "asset_count": "Asset Count",
            "MOST_IMPORTANT_FEATURE": "Feature",
        },
        color="avg_churn_prob",
        color_continuous_scale=["#F4F3F0", "#D92228"],
    )
    fig.update_layout(yaxis=dict(autorange="reversed"))
    return fig


def performance_metrics_chart(df):
    fig = go.Figure()
    metrics = ["AUC_SCORE", "ACCURACY", "PRECISION_SCORE", "RECALL_SCORE"]
    colors = [ACCENT_RED, CHARCOAL, "#8B4513", "#2E7D32"]
    for metric, color in zip(metrics, colors):
        fig.add_trace(
            go.Scatter(
                x=df["SNAPSHOT_DATE"],
                y=df[metric],
                mode="lines+markers",
                name=metric.replace("_", " ").title(),
                line=dict(color=color, width=2),
            )
        )
    fig.update_layout(
        title="Model Performance Over Time",
        xaxis_title="Snapshot Date",
        yaxis_title="Score",
        yaxis_tickformat=".0%",
    )
    return fig
