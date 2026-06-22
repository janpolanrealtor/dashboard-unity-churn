# apps/unity-churn-dashboard/app.py
import streamlit as st
import pandas as pd
import plotly.express as px
import snowflake.connector

# Page Configuration
st.set_page_config(
    page_title="Unity Churn Dashboard",
    page_icon="🎯",
    layout="wide"
)

# Custom CSS injection for Realtor.com Haven foundations theme
st.markdown("""
    <style>
    .main-title {
        color: #D92228; /* Realtor.com Primary Red */
        font-family: 'Galano Grotesque Alt', sans-serif;
        font-weight: bold;
        font-size: 2.5rem;
    }
    .section-header {
        color: #3F3B36; /* Haven Charcoal */
        font-family: 'Galano Grotesque Alt', sans-serif;
        border-bottom: 2px solid #F4F3F0;
        padding-bottom: 10px;
    }
    div[data-testid="stMetricValue"] {
        color: #3F3B36;
    }
    </style>
""", unsafe_allow_html=True)

# 1. Establish Secure Snowflake Connection
@st.cache_resource
def init_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database="TEAM_DATASCIENCE",
        schema="PUBLIC"
    )

# 2. Optimized Data Loading with De-duplicated SQL Query
@st.cache_data
def load_dashboard_data():
    conn = init_connection()
    query = """
    WITH latest_churn AS (
        SELECT *
        FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY
        QUALIFY ROW_NUMBER() OVER (PARTITION BY asset_id, month_of_expiry ORDER BY snapshot_date DESC) = 1
    ),
    latest_renewals AS (
        SELECT *
        FROM TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS
        QUALIFY ROW_NUMBER() OVER (PARTITION BY id, month_of_expiry ORDER BY snapshot_date DESC) = 1
    )
    SELECT 
        churn.asset_id,
        churn.snapshot_date AS prediction_date,
        churn.churn_prob,
        churn.most_important_feature,
        renewals.accountid,
        renewals.product2id,
        renewals.expiring_value_acv,
        renewals.expiring_value_sov,
        renewals.roi_per_lead,
        renewals.fulfillment_pct,
        renewals.tenure,
        renewals.is_fulfilled,
        renewals.is_competitive_market
    FROM latest_churn churn
    INNER JOIN latest_renewals renewals
        ON churn.asset_id = renewals.id
        AND DATE_TRUNC('month', churn.snapshot_date::DATE) = DATE_TRUNC('month', renewals.month_of_expiry::DATE)
    ORDER BY churn.churn_prob DESC;
    """
    df = pd.read_sql(query, conn)
    conn.close()
    
    # Map Salesforce Product IDs to readable product names
    product_mapping = {
        "01t3a000004vIdIAAU": "MVIP Legacy",
        "01t5f000006sGgOAAU": "Unity Package"
    }
    df["PRODUCT_NAME"] = df["PRODUCT2ID"].map(product_mapping).fillna("Other Asset")
    return df

# Load the production dataset
try:
    df = load_dashboard_data()
except Exception as e:
    st.error(f"Error connecting to Snowflake: {e}")
    st.stop()

# --- MAIN HEADER ---
st.markdown('<h1 class="main-title">Unity Asset Churn Dashboard</h1>', unsafe_allow_html=True)
st.markdown("---")

# --- SIDEBAR FILTERS ---
st.sidebar.markdown('<h3 class="section-header">Filter Options</h3>', unsafe_allow_html=True)
product_filter = st.sidebar.multiselect(
    "Product Type",
    options=df["PRODUCT_NAME"].unique(),
    default=df["PRODUCT_NAME"].unique()
)
churn_range = st.sidebar.slider(
    "Churn Probability Range",
    min_value=0.0, max_value=1.0, value=(0.0, 1.0)
)

# Apply filter selections
filtered_df = df[
    (df["PRODUCT_NAME"].isin(product_filter)) &
    (df["CHURN_PROB"].between(churn_range[0], churn_range[1]))
]

# --- METRIC CARDS ---
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Active Assets", len(filtered_df))
with col2:
    avg_churn = filtered_df["CHURN_PROB"].mean()
    st.metric("Avg. Churn Probability", f"{avg_churn:.2%}")
with col3:
    avg_roi = filtered_df["ROI_PER_LEAD"].mean()
    st.metric("Avg. Agent ROI", f"{avg_roi:.2%}" if not pd.isna(avg_roi) else "N/A")
with col4:
    at_risk = len(filtered_df[filtered_df["CHURN_PROB"] > 0.6])
    st.metric("High-Risk Assets (>60%)", at_risk)

st.markdown(" ")

# --- INSIGHT CHARTS ---
st.markdown('<h3 class="section-header">Performance & Churn Insights</h3>', unsafe_allow_html=True)
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    # Scatter Plot: Agent ROI vs Churn Probability
    fig_scatter = px.scatter(
        filtered_df,
        x="ROI_PER_LEAD",
        y="CHURN_PROB",
        size="FULFILLMENT_PCT",
        color="PRODUCT_NAME",
        title="Agent ROI vs. Churn Probability",
        color_discrete_map={"Unity Package": "#D92228", "MVIP Legacy": "#3F3B36", "Other Asset": "#F4F3F0"},
        labels={"ROI_PER_LEAD": "Agent ROI", "CHURN_PROB": "Churn Probability"}
    )
    fig_scatter.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_scatter, use_container_width=True)

with chart_col2:
    # Histogram: Churn Probability Distribution
    fig_hist = px.histogram(
        filtered_df,
        x="CHURN_PROB",
        nbins=10,
        title="Churn Probability Distribution",
        color_discrete_sequence=["#D92228"],
        labels={"CHURN_PROB": "Churn Probability"}
    )
    fig_hist.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)")
    st.plotly_chart(fig_hist, use_container_width=True)

# --- DATA TABLE ---
st.markdown('<h3 class="section-header">Detailed Asset Performance Metrics</h3>', unsafe_allow_html=True)
st.dataframe(
    filtered_df[[
        "ASSET_ID", "ACCOUNTID", "PRODUCT_NAME", "CHURN_PROB", 
        "MOST_IMPORTANT_FEATURE", "EXPIRING_VALUE_ACV", 
        "ROI_PER_LEAD", "FULFILLMENT_PCT", "TENURE"
    ]].style.format({
        "CHURN_PROB": "{:.1%}",
        "ROI_PER_LEAD": "{:.1%}",
        "FULFILLMENT_PCT": "{:.1%}",
        "EXPIRING_VALUE_ACV": "${:,.2f}"
    }),
    use_container_width=True
)