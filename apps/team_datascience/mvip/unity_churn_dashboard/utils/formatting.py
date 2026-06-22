import pandas as pd


def fmt_currency(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    if abs(val) >= 1_000_000:
        return f"${val / 1_000_000:.2f}M"
    if abs(val) >= 1_000:
        return f"${val / 1_000:.0f}K"
    return f"${val:,.0f}"


def fmt_probability(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    return f"{val:.1%}"


def fmt_percentage(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    return f"{val:.1%}"


def fmt_tenure(val) -> str:
    if val is None or (isinstance(val, float) and pd.isna(val)):
        return "—"
    return f"{val:.1f}y"


def metric_delta(current, previous) -> str | None:
    if previous == 0 or pd.isna(previous):
        return None
    return f"{((current - previous) / previous):.1%}"


# Aliases used by Streamlit .style.format() which calls with a single value
format_probability = fmt_probability
format_currency = fmt_currency
format_percentage = fmt_percentage
