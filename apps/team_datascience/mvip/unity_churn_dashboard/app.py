import streamlit as st
from utils.queries import (
    load_executive_summary,
    load_model_performance,
    load_feature_importance,
    load_filtered_assets,
)
from utils.plotting import trend_chart, performance_metrics_chart, feature_importance_chart
from utils.formatting import format_probability, format_currency, format_percentage

st.set_page_config(page_title="Unity Churn Dashboard", layout="wide")

st.markdown(
    """
    <style>
    .main-title {
        color: #D92228;
        font-family: 'Galano Grotesque Alt', sans-serif;
        font-weight: bold;
        font-size: 2.5rem;
    }
    .section-header {
        color: #3F3B36;
        font-family: 'Galano Grotesque Alt', sans-serif;
        border-bottom: 2px solid #F4F3F0;
        padding-bottom: 10px;
    }
    div[data-testid="stMetricValue"] {
        color: #3F3B36;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<h1 class="main-title">Unity Asset Churn Dashboard</h1>', unsafe_allow_html=True)
st.markdown("---")

tab1, tab2, tab3 = st.tabs(
    ["Executive Summary", "Model Performance", "Asset Explorer"]
)

try:
    summary, trend = load_executive_summary()
    perf_df = load_model_performance()
    importance_df = load_feature_importance()
    full_df = load_filtered_assets()
except Exception as e:
    st.error(f"Error connecting to Snowflake: {e}")
    st.stop()

with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Assets", summary["total_assets"])
    with col2:
        st.metric("Avg Churn Probability", format_probability(summary["avg_churn_prob"]))
    with col3:
        st.metric("High-Risk Assets (>.70)", summary["high_risk_count"])

    st.markdown(" ")
    st.markdown('<h3 class="section-header">Churn Risk Trend</h3>', unsafe_allow_html=True)
    if not trend.empty:
        st.plotly_chart(trend_chart(trend), use_container_width=True)
    else:
        st.info("No trend data available.")

with tab2:
    st.markdown('<h3 class="section-header">Historical Model Performance</h3>', unsafe_allow_html=True)
    if not perf_df.empty:
        st.plotly_chart(performance_metrics_chart(perf_df), use_container_width=True)
        with st.expander("Raw Performance Data"):
            st.dataframe(
                perf_df.style.format(
                    {
                        "AUC_SCORE": format_probability,
                        "ACCURACY": format_probability,
                        "PRECISION_SCORE": format_probability,
                        "RECALL_SCORE": format_probability,
                    }
                ),
                use_container_width=True,
            )
    else:
        st.info("Model performance data is not yet available. This tab will display AUC, accuracy, precision, and recall metrics once the pipeline logs them to TEAM_DATASCIENCE.PUBLIC.UNITY_CHURN_MODEL_PERFORMANCE.")

    st.markdown(" ")
    st.markdown('<h3 class="section-header">Global Feature Importance</h3>', unsafe_allow_html=True)
    if not importance_df.empty:
        st.plotly_chart(feature_importance_chart(importance_df), use_container_width=True)
    else:
        st.info("No feature importance data available.")

with tab3:
    st.sidebar.markdown('<h3 class="section-header">Filter Options</h3>', unsafe_allow_html=True)

    churn_min, churn_max = st.sidebar.slider(
        "Churn Probability Range",
        min_value=0.0,
        max_value=1.0,
        value=(0.0, 1.0),
    )

    product_options = ["Unity Package"]
    product_filter = st.sidebar.multiselect(
        "Product Type",
        options=product_options,
        default=product_options,
    )

    available_months = sorted(full_df["MONTH_OF_EXPIRY"].dropna().unique())
    expiry_months = st.sidebar.multiselect(
        "Expiry Month",
        options=available_months,
        default=[],
    )

    result_df = load_filtered_assets(
        churn_min=churn_min, churn_max=churn_max, expiry_months=expiry_months if expiry_months else None
    )

    st.markdown(f'<h3 class="section-header">Assets ({len(result_df)} results)</h3>', unsafe_allow_html=True)

    if len(result_df) == 1000:
        st.caption("Results capped at 1,000 rows. Refine your filters for more specific data.")

    st.dataframe(
        result_df[
            [
                "ASSET_ID",
                "ACCOUNTID",
                "PRODUCT_NAME",
                "CHURN_PROB",
                "MOST_IMPORTANT_FEATURE",
                "EXPIRY_DATE",
                "EXPIRING_VALUE_ACV",
                "ROI_PER_LEAD",
            ]
        ].style.format(
            {
                "CHURN_PROB": format_probability,
                "ROI_PER_LEAD": format_percentage,
                "EXPIRING_VALUE_ACV": format_currency,
            }
        ),
        use_container_width=True,
        height=600,
    )
