import pandas as pd


def format_probability(val):
    return f"{val:.1%}"


def format_currency(val):
    if pd.isna(val):
        return "N/A"
    return f"${val:,.2f}"


def format_percentage(val):
    if pd.isna(val):
        return "N/A"
    return f"{val:.1%}"


def metric_delta(current, previous):
    if previous == 0 or pd.isna(previous):
        return None
    return f"{((current - previous) / previous):.1%}"
