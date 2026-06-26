import pandas as pd
import streamlit as st
from utils.formatting import (
    fmt_currency,
    fmt_percentage,
    fmt_probability,
    fmt_renews_in,
    fmt_tenure,
)
from utils.plotting import (
    asset_distribution_chart,
    churn_trend_chart,
    feature_importance_chart,
    pipeline_history_chart,
    plot_quartile_indicator,
    survival_distribution_chart,
)
from utils.queries import (
    load_account_detail,
    load_call_worklist,
    load_feature_distributions,
    load_feature_importance,
    load_pipeline_runs,
    load_portfolio_accounts,
    load_portfolio_summary,
)

st.set_page_config(
    page_title="Unity Churn Dashboard · realtor.com",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Haven Design System tokens injected via CSS ──────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap');

:root {
  --brand:        #D92228;
  --gray-50:      #F8F7F7;
  --gray-100:     #F2F0EF;
  --gray-200:     #E9E7E4;
  --gray-300:     #D3CFCA;
  --gray-600:     #958A7F;
  --gray-700:     #726A60;
  --gray-1000:    #3F3B36;
  --gray-1200:    #1A1816;
  --green-100:    #E9F6E9;
  --green-700:    #46A758;
  --green-900:    #2A7E3B;
  --red-100:      #FEE2E3;
  --red-700:      #BA1B20;
  --yellow-200:   #FFF2D0;
  --yellow-900:   #685700;
  --blue-100:     #E9EFFB;
  --blue-800:     #15459A;
  --font-body: "Galano Grotesque Alt", "Inter", -apple-system, sans-serif;
}

/* Reset Streamlit chrome */
.block-container { padding: 0 !important; max-width: 100% !important; }
#MainMenu, footer, header { visibility: hidden; }
.stApp { background: var(--gray-50); font-family: var(--font-body); }
section[data-testid="stSidebar"] { display: none; }

/* ── App header ─────────────────────────────────────────────────────────── */
.haven-header {
  display: flex; align-items: center; gap: 32px;
  height: 56px; padding: 0 32px;
  background: #fff;
  border-bottom: 1px solid var(--gray-200);
  position: sticky; top: 0; z-index: 100;
}
.haven-logo { display: flex; align-items: center; gap: 10px; }
.haven-logo-text { font-size: 15px; font-weight: 600; color: var(--gray-1200); }
.haven-logo-sub  { font-size: 11px; font-weight: 600; color: var(--gray-600);
                   letter-spacing: 0.6px; text-transform: uppercase; }
.haven-nav { display: flex; gap: 4px; flex: 1; }
.haven-nav-btn {
  background: transparent; border: none;
  padding: 6px 12px; font-size: 14px; font-weight: 500;
  color: var(--gray-700); border-radius: 6px; cursor: pointer; font-family: inherit;
}
.haven-nav-btn.active {
  background: var(--gray-100); color: var(--gray-1200); font-weight: 600;
}

/* ── KPI strip ──────────────────────────────────────────────────────────── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px;
            padding: 24px 32px 0; }
.kpi-card {
  background: #fff; border: 1px solid var(--gray-200);
  border-radius: 12px; padding: 16px 20px;
}
.kpi-label { font-size: 11px; font-weight: 600; color: var(--gray-700);
             letter-spacing: 0.5px; text-transform: uppercase; margin-bottom: 6px; }
.kpi-value { font-size: 28px; font-weight: 600; color: var(--gray-1200);
             letter-spacing: -0.4px; font-variant-numeric: tabular-nums; }
.kpi-value.danger { color: var(--brand); }
.kpi-sub   { font-size: 12px; color: var(--gray-700); margin-top: 2px; }

/* ── Status pill ────────────────────────────────────────────────────────── */
.pill {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 3px 9px; border-radius: 6px;
  font-size: 12px; font-weight: 600; line-height: 1.2; white-space: nowrap;
}
.pill-dot { width: 6px; height: 6px; border-radius: 999px; }
.pill-high   { background: var(--red-100);    color: #9A1A1E; }
.pill-medium { background: var(--yellow-200); color: var(--yellow-900); }
.pill-low    { background: var(--green-100);  color: var(--green-900); }
.pill-na     { background: var(--gray-100);   color: var(--gray-1000); }

/* ── Portfolio table ────────────────────────────────────────────────────── */
.portfolio-wrap {
  padding: 24px 32px; overflow-x: auto;
}
.portfolio-table {
  background: #fff; border: 1px solid var(--gray-200);
  border-radius: 12px; overflow: hidden; width: 100%;
  border-collapse: collapse;
}
.portfolio-table th {
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-200);
  padding: 10px 14px; text-align: left;
  font-size: 11px; font-weight: 600; color: var(--gray-700);
  letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap;
}
.portfolio-table td {
  padding: 12px 14px; font-size: 13px; color: var(--gray-1200);
  border-bottom: 1px solid var(--gray-100); vertical-align: middle;
}
.portfolio-table tr:last-child td { border-bottom: none; }
.portfolio-table tr.selected-row td { background: #FEF2F2; }

/* ── Account detail panel ───────────────────────────────────────────────── */
.detail-header {
  padding: 20px 32px 0;
  display: flex; align-items: flex-start; justify-content: space-between;
}
.detail-breadcrumb { font-size: 12px; color: var(--gray-700); margin-bottom: 6px; }
.detail-title {
  font-size: 28px; font-weight: 600; color: var(--gray-1200);
  letter-spacing: -0.4px; margin: 0 0 8px;
}
.detail-meta { font-size: 13px; color: var(--gray-700); }
.detail-meta span { margin-right: 8px; }

/* ── Section header ─────────────────────────────────────────────────────── */
.section-eyebrow {
  font-size: 11px; font-weight: 600; color: var(--brand);
  letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 4px;
}
.section-title {
  font-size: 18px; font-weight: 600; color: var(--gray-1200); margin: 0 0 16px;
}

/* ── Trend arrow ────────────────────────────────────────────────────────── */
.trend-up   { color: var(--green-900); font-weight: 600; font-size: 13px; }
.trend-down { color: var(--brand);     font-weight: 600; font-size: 13px; }

/* ── Streamlit tab bar — Haven nav styling ──────────────────────────────── */
div[data-baseweb="tab-list"] {
  background: #fff !important;
  border-bottom: 1px solid var(--gray-200) !important;
  padding: 0 24px !important;
  gap: 0 !important;
}
button[data-baseweb="tab"] {
  background: transparent !important;
  border: none !important;
  border-radius: 0 !important;
  padding: 14px 16px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
  color: var(--gray-700) !important;
  font-family: var(--font-body) !important;
  border-bottom: 2px solid transparent !important;
  margin-bottom: -1px !important;
}
button[data-baseweb="tab"]:hover {
  color: var(--gray-1200) !important;
  background: var(--gray-50) !important;
}
button[data-baseweb="tab"][aria-selected="true"] {
  color: var(--gray-1200) !important;
  font-weight: 600 !important;
  border-bottom: 2px solid var(--brand) !important;
  background: transparent !important;
}
div[data-baseweb="tab-highlight"] { display: none !important; }
div[data-baseweb="tab-border"]    { display: none !important; }

/* ── Feature Metrics quartile strip ────────────────────────────────────── */
.feat-metrics-wrap {
  background: #fff; border: 1px solid var(--gray-200);
  border-radius: 12px; padding: 16px 20px; margin-top: 16px;
}
.feat-metrics-title {
  font-size: 11px; font-weight: 600; color: var(--brand);
  letter-spacing: 0.6px; text-transform: uppercase; margin-bottom: 12px;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Header (logo only — navigation is handled by the styled st.tabs below) ───
st.markdown(
    """
<div class="haven-header">
  <div class="haven-logo">
    <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
      <path d="M12 2 L22 11 V22 H14 V14 H10 V22 H2 V11 Z" fill="#D92228"/>
    </svg>
    <div>
      <div class="haven-logo-text">realtor.com</div>
    </div>
    <div class="haven-logo-sub">Unity Churn Dashboard</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

# ── Load data ────────────────────────────────────────────────────────────────
try:
    portfolio_summary = load_portfolio_summary()
    accounts_df = load_portfolio_accounts()
    worklist_df = load_call_worklist()
    pipeline_df = load_pipeline_runs()
    importance_df = load_feature_importance()
    feat_dist = load_feature_distributions()
except Exception as e:
    st.error(f"Error connecting to Snowflake: {e}")
    st.stop()

# ── KPI Strip ────────────────────────────────────────────────────────────────
total = portfolio_summary["total_assets"]
avg_churn = portfolio_summary["avg_churn_prob"]
high_risk = portfolio_summary["high_risk_count"]
high_pct = high_risk / total if total > 0 else 0
total_acv = portfolio_summary["total_acv"]

st.markdown(
    f"""
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-label">Total Unity Assets</div>
    <div class="kpi-value">{total:,}</div>
    <div class="kpi-sub">Active assets tracked</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Avg Churn Probability</div>
    <div class="kpi-value">{fmt_probability(avg_churn)}</div>
    <div class="kpi-sub">Latest snapshot</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">High-Risk Assets (&gt;70%)</div>
    <div class="kpi-value danger">{high_risk:,}</div>
    <div class="kpi-sub">{fmt_percentage(high_pct)} of portfolio</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Total Expiring ACV</div>
    <div class="kpi-value">{fmt_currency(total_acv)}</div>
    <div class="kpi-sub">Sum of expiring contract value</div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.markdown("<div style='height:24px'></div>", unsafe_allow_html=True)

# ── Main tabs ────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📋  Portfolio", "📈  Pipeline History", "🔍  Asset Explorer"])

# ════════════════════════════════════════════════════════════════════════════
# TAB 1 — PORTFOLIO
# ════════════════════════════════════════════════════════════════════════════
with tab1:
    # ── Insights box ────────────────────────────────────────────────────────────
    _insights = []
    if high_risk > 0:
        _at_risk_acv = float(
            accounts_df[accounts_df["CHURN_PROB"] > 0.7]["EXPIRING_VALUE_ACV"].sum()
        )
        _insights.append(
            f"**{high_risk:,} assets** ({fmt_percentage(high_pct)} of portfolio) are high-risk — "
            f"representing **{fmt_currency(_at_risk_acv)}** in expiring ACV."
        )
    _unfulfilled_high = int(
        ((accounts_df["CHURN_PROB"] > 0.7) & ~accounts_df["IS_FULFILLED"]).sum()
    )
    if _unfulfilled_high > 0:
        _insights.append(
            f"**{_unfulfilled_high:,} high-risk assets** are also unfulfilled — "
            f"fulfillment issues are compounding churn risk."
        )
    _top_driver = None
    if not accounts_df.empty and "MOST_IMPORTANT_FEATURE" in accounts_df.columns:
        _top_driver = accounts_df["MOST_IMPORTANT_FEATURE"].mode()
        if not _top_driver.empty:
            _top_driver = _top_driver.iloc[0]
            _driver_count = int((accounts_df["MOST_IMPORTANT_FEATURE"] == _top_driver).sum())
            _insights.append(
                f'**"{_top_driver}"** is the top churn driver for **{_driver_count:,} assets** — '
                f"the single biggest lever to address."
            )

    with st.container(border=True):
        if _insights:
            st.markdown("**Signals**")
            for _msg in _insights:
                st.markdown(f"- {_msg}")
        else:
            st.success("No unusual patterns detected in the current snapshot.")

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    col_filters, col_spacer = st.columns([3, 1])
    with col_filters:
        filter_status = st.selectbox(
            "Filter by risk",
            ["All assets", "High risk (>70%)", "Medium risk (40-70%)", "Low risk (<40%)"],
            label_visibility="collapsed",
        )
        sort_by = st.selectbox(
            "Sort by",
            ["Churn Prob ↓", "Churn Prob ↑", "ACV ↓", "Tenure ↓"],
            label_visibility="collapsed",
        )

    df = worklist_df.copy()

    # Apply filter
    if filter_status == "High risk (>70%)":
        df = df[df["CHURN_PROB"] > 0.7]
    elif filter_status == "Medium risk (40-70%)":
        df = df[df["CHURN_PROB"].between(0.4, 0.7)]
    elif filter_status == "Low risk (<40%)":
        df = df[df["CHURN_PROB"] < 0.4]

    # Apply sort
    if sort_by == "Churn Prob ↓":
        df = df.sort_values("CHURN_PROB", ascending=False)
    elif sort_by == "Churn Prob ↑":
        df = df.sort_values("CHURN_PROB", ascending=True)
    elif sort_by == "ACV ↓":
        df = df.sort_values("EXPIRING_VALUE_ACV", ascending=False)
    elif sort_by == "Tenure ↓":
        df = df.sort_values("TENURE", ascending=False)

    df = df.head(200)

    def churn_bar_html(p: float) -> str:
        if p > 0.7:
            bar_color = "#D92228"
        elif p > 0.4:
            bar_color = "#685700"
        else:
            bar_color = "#46A758"
        pct = p * 80
        circle_left = max(0, min(pct - 4, 72))
        return f"""
        <div style="width:80px;height:6px;background:#E9E7E4;border-radius:3px;position:relative;">
          <div style="position:absolute;left:0;top:0;height:6px;width:{pct:.0f}px;background:{bar_color};border-radius:3px;"></div>
          <div style="position:absolute;left:{circle_left:.0f}px;top:-3px;width:12px;height:12px;background:{bar_color};border:2px solid #fff;border-radius:999px;box-shadow:0 0 2px rgba(0,0,0,0.2);"></div>
        </div>"""

    def trend_arrow_html(current: float, previous) -> str:
        if previous is None or (isinstance(previous, float) and pd.isna(previous)):
            return '<span style="color:#726A60">–</span>'
        if current < previous:
            return '<span style="color:#46A758;font-weight:600">↑</span>'
        if current > previous:
            return '<span style="color:#D92228;font-weight:600">↓</span>'
        return '<span style="color:#726A60">–</span>'

    rows_html = ""
    for _, row in df.iterrows():
        acv = fmt_currency(row.get("EXPIRING_VALUE_ACV", 0))
        acct = row.get("ACCOUNT_NAME") or "—"
        market = row.get("MARKET_NAME") or "—"
        acv_row = f"<div style='font-size:13px;font-weight:600;color:var(--gray-1200)'>{acv}</div>"
        if row.get("ROI_PER_LEAD") is not None and row["ROI_PER_LEAD"] < 0.0:
            acv_row += '<div style="color:#D92228;font-size:11px">below viability</div>'
        feat = row.get("MOST_IMPORTANT_FEATURE") or "—"
        trend = trend_arrow_html(row["CHURN_PROB"], row.get("PREV_CHURN_PROB"))
        renews = fmt_renews_in(row.get("DAYS_UNTIL_EXPIRY"))
        if row.get("DAYS_UNTIL_EXPIRY") is not None and pd.isna(row["DAYS_UNTIL_EXPIRY"]):
            renews = "—"
        rows_html += f"""
        <tr>
          <td>
            <div style="font-size:13px;font-weight:600;color:var(--gray-1200)">{acct}</div>
            <div style="font-size:11px;color:#726A60">{market}</div>
          </td>
          <td>{acv_row}</td>
          <td>{churn_bar_html(row["CHURN_PROB"])}</td>
          <td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
            <span style="font-size:13px;color:var(--gray-1200)">{feat}</span> {trend}
          </td>
          <td>{renews}</td>
        </tr>"""

    st.markdown(
        f"""
    <div class="portfolio-wrap">
      <div class="section-eyebrow">Call Worklist · {len(df):,} accounts</div>
      <table class="portfolio-table">
        <thead>
          <tr>
            <th>Account</th>
            <th>Expiring ACV</th>
            <th>Churn Risk</th>
            <th>Top Driver</th>
            <th>Renews In</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ── Selected account drill-down ──────────────────────────────────────────
    st.markdown("---")
    st.markdown('<div class="section-eyebrow">Account deep-dive</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-title">Select an asset to explore its churn trend</div>',
        unsafe_allow_html=True,
    )

    asset_options = df["ASSET_ID"].tolist()
    if asset_options:
        selected_asset = st.selectbox("Choose asset", asset_options, label_visibility="collapsed")
        if selected_asset:
            try:
                detail_df = load_account_detail(selected_asset)
                if not detail_df.empty:

                    def _risk_pill(p):
                        if p > 0.7:
                            return f'<span class="pill pill-high"><span class="pill-dot" style="background:#9A1A1E"></span>{fmt_probability(p)}</span>'
                        if p > 0.4:
                            return f'<span class="pill pill-medium"><span class="pill-dot" style="background:#685700"></span>{fmt_probability(p)}</span>'
                        return f'<span class="pill pill-low"><span class="pill-dot" style="background:#2A7E3B"></span>{fmt_probability(p)}</span>'

                    row = detail_df.iloc[0]
                    churn_p = row["CHURN_PROB"]
                    pill_html = _risk_pill(churn_p)

                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown(
                            f"""
                        <div class="detail-header" style="padding:0">
                          <div>
                            <div class="detail-breadcrumb">Portfolio › Unity Assets › {selected_asset[:30]}</div>
                            <div class="detail-title">{selected_asset}</div>
                            <div class="detail-meta">
                              <span>Account: {row.get("ACCOUNTID", "—")}</span> ·
                              <span>Tenure: {fmt_tenure(row.get("TENURE", 0))}</span> ·
                              <span>ACV: {fmt_currency(row.get("EXPIRING_VALUE_ACV", 0))}</span> ·
                              <span>Fulfilled: {"Yes" if row.get("IS_FULFILLED") else "No"}</span>
                            </div>
                          </div>
                          <div style="margin-top:8px">{pill_html}</div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

                        # Trend chart + distribution side by side
                        ch1, ch2 = st.columns(2)
                        with ch1:
                            fig = churn_trend_chart(detail_df)
                            if fig:
                                st.plotly_chart(fig, width="stretch")
                            else:
                                st.info(
                                    "Only one snapshot available for this asset — trend requires multiple dates."
                                )
                        with ch2:
                            dist_fig = asset_distribution_chart(
                                population=accounts_df["CHURN_PROB"],
                                entity_value=churn_p,
                                entity_label=selected_asset[:20],
                            )
                            st.plotly_chart(dist_fig, width="stretch")

                        # ── Feature Metrics ──────────────────────────────────
                        st.markdown(
                            '<div class="feat-metrics-wrap">'
                            '<div class="feat-metrics-title">Feature Metrics</div>',
                            unsafe_allow_html=True,
                        )

                        # Each entry: (column_key, label, lower_is_better, fmt_fn, tick_format)
                        _feat_specs = [
                            (
                                "TENURE",
                                "Tenure (years)",
                                False,
                                lambda v: f"{v:.1f}y",
                                None,
                                "TENURE_Q1",
                                "TENURE_Q3",
                            ),
                            (
                                "FULFILLMENT_PCT",
                                "Fulfillment %",
                                False,
                                lambda v: f"{v:.1%}",
                                ".0%",
                                "FULFILLMENT_Q1",
                                "FULFILLMENT_Q3",
                            ),
                            (
                                "ROI_PER_LEAD",
                                "Agent ROI per Lead",
                                False,
                                lambda v: f"{v:.1%}",
                                ".0%",
                                "ROI_Q1",
                                "ROI_Q3",
                            ),
                            (
                                "EXPIRING_VALUE_ACV",
                                "Expiring ACV",
                                False,
                                fmt_currency,
                                "$,.0f",
                                "ACV_Q1",
                                "ACV_Q3",
                            ),
                            (
                                "SPILLOVER_PCT",
                                "Spillover %",
                                True,
                                lambda v: f"{v:.1%}",
                                ".0%",
                                "SPILLOVER_Q1",
                                "SPILLOVER_Q3",
                            ),
                        ]

                        for (
                            _col_key,
                            _label,
                            _lib,
                            _fmt_fn,
                            _tick_fmt,
                            _q1_key,
                            _q3_key,
                        ) in _feat_specs:
                            _val = row.get(_col_key)
                            _q1 = feat_dist.get(_q1_key)
                            _q3 = feat_dist.get(_q3_key)
                            if _val is None or _q1 is None or _q3 is None:
                                continue
                            _lc, _rc = st.columns([1, 3])
                            with _lc:
                                st.markdown(
                                    f"<div style='padding-top:36px;font-size:13px;"
                                    f"font-weight:600;color:var(--gray-1000)'>{_label}</div>",
                                    unsafe_allow_html=True,
                                )
                            with _rc:
                                st.plotly_chart(
                                    plot_quartile_indicator(
                                        current_val=float(_val),
                                        q1_val=_q1,
                                        q3_val=_q3,
                                        feature_name="",
                                        lower_is_better=_lib,
                                        fmt=_fmt_fn,
                                        tick_format=_tick_fmt,
                                    ),
                                    width="stretch",
                                )

                        st.markdown("</div>", unsafe_allow_html=True)

                    with col2:
                        st.markdown(
                            f"""
                        <div style="background:#fff;border:1px solid var(--gray-200);border-radius:12px;padding:20px;display:flex;flex-direction:column;gap:16px">
                          <div>
                            <div class="kpi-label">Churn Probability</div>
                            <div class="kpi-value {"danger" if churn_p > 0.7 else ""}">{fmt_probability(churn_p)}</div>
                          </div>
                          <div>
                            <div class="kpi-label">Top Driver</div>
                            <div style="font-size:14px;font-weight:600;color:var(--gray-1200)">{row.get("MOST_IMPORTANT_FEATURE", "—")}</div>
                          </div>
                          <div>
                            <div class="kpi-label">Fulfillment %</div>
                            <div style="font-size:20px;font-weight:600;color:var(--gray-1200)">{fmt_percentage(row.get("FULFILLMENT_PCT", 0))}</div>
                          </div>
                          <div>
                            <div class="kpi-label">Agent ROI</div>
                            <div style="font-size:20px;font-weight:600;color:var(--gray-1200)">{fmt_percentage(row.get("ROI_PER_LEAD", 0)) if row.get("ROI_PER_LEAD") else "—"}</div>
                          </div>
                          <div>
                            <div class="kpi-label">Competitive Market</div>
                            <div style="font-size:14px;font-weight:500;color:var(--gray-1200)">{"Yes" if row.get("IS_COMPETITIVE_MARKET") else "No"}</div>
                          </div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )
            except Exception as e:
                st.warning(f"Could not load detail for {selected_asset}: {e}")

# ════════════════════════════════════════════════════════════════════════════
# TAB 2 — PIPELINE HISTORY
# ════════════════════════════════════════════════════════════════════════════
with tab2:
    if not pipeline_df.empty:
        latest = pipeline_df.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.metric(
            "Latest Run Assets",
            f"{int(latest['TOTAL_ASSETS']):,}",
            help="Number of Unity assets scored in the most recent pipeline run.",
        )
        c2.metric(
            "Avg Churn Prob",
            fmt_probability(latest["AVG_CHURN_PROB"]),
            help="Mean churn probability across all scored assets in the latest run.",
        )
        c3.metric(
            "Median Churn Prob",
            fmt_probability(latest["MEDIAN_CHURN_PROB"]),
            help="Median churn probability — less sensitive to outliers than the mean.",
        )
        c4.metric(
            "High-Risk Rate",
            fmt_probability(latest["HIGH_RISK_RATE"]),
            help="Fraction of assets with churn probability above 70% in the latest run.",
        )

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        st.plotly_chart(pipeline_history_chart(pipeline_df), width="stretch")

        with st.expander("Raw pipeline run data"):
            st.dataframe(
                pipeline_df.style.format(
                    {
                        "AVG_CHURN_PROB": fmt_probability,
                        "MEDIAN_CHURN_PROB": fmt_probability,
                        "HIGH_RISK_RATE": fmt_probability,
                    }
                ),
                width="stretch",
            )
    else:
        st.info("No pipeline runs found for Unity assets.")

# ════════════════════════════════════════════════════════════════════════════
# TAB 3 — INSIGHTS
# ════════════════════════════════════════════════════════════════════════════
with tab3:
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown('<div class="section-eyebrow">Model signals</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Top Churn Drivers</div>', unsafe_allow_html=True)
        if not importance_df.empty:
            st.plotly_chart(feature_importance_chart(importance_df), width="stretch")
        else:
            st.info("No feature importance data available.")

    with col_b:
        st.markdown('<div class="section-eyebrow">Risk distribution</div>', unsafe_allow_html=True)
        st.markdown(
            '<div class="section-title">Churn Probability Spread</div>', unsafe_allow_html=True
        )
        if not accounts_df.empty:
            st.plotly_chart(survival_distribution_chart(accounts_df), width="stretch")
        else:
            st.info("No distribution data available.")

    # Driver breakdown table
    st.markdown("---")
    st.markdown('<div class="section-eyebrow">By driver</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Feature × Avg Churn Prob</div>', unsafe_allow_html=True)
    if not importance_df.empty:
        display_df = importance_df[
            ["MOST_IMPORTANT_FEATURE", "ASSET_COUNT", "AVG_CHURN_PROB"]
        ].copy()
        display_df.columns = ["Top Driver", "Assets Affected", "Avg Churn Prob"]
        st.dataframe(
            display_df.style.format(
                {
                    "Avg Churn Prob": fmt_probability,
                    "Assets Affected": "{:,}",
                }
            ),
            width="stretch",
            height=400,
        )
