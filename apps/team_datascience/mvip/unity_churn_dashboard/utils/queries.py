import streamlit as st
import pandas as pd
import snowflake.connector

PRODUCT_MAPPING = {
    "01t3a000004vIdIAAU": "MVIP Legacy",
    "01t5f000006sGgOAAU": "Unity Package",
}

UNITY_PRODUCT_ID = "01t5f000006sGgOAAU"


@st.cache_resource
def init_connection():
    return snowflake.connector.connect(
        user=st.secrets["snowflake"]["user"],
        password=st.secrets["snowflake"]["password"],
        account=st.secrets["snowflake"]["account"],
        warehouse=st.secrets["snowflake"]["warehouse"],
        database="TEAM_DATASCIENCE",
        schema="PUBLIC",
    )


@st.cache_data
def load_unity_churn_data():
    conn = init_connection()
    query = """
    WITH unity_assets AS (
        SELECT a.*
        FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY a
        INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
            ON a.ASSET_ID = r.ID
        WHERE r.PRODUCT2ID = '01t5f000006sGgOAAU'
    ),
    latest_predictions AS (
        SELECT *
        FROM unity_assets
        QUALIFY ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE DESC) = 1
    )
    SELECT
        lp.ASSET_ID,
        lp.CHURN_PROB,
        lp.MOST_IMPORTANT_FEATURE,
        lp.EXPIRY_DATE,
        lp.MONTH_OF_EXPIRY,
        r.ACCOUNTID,
        r.PRODUCT_NAME,
        r.PRODUCT2ID,
        r.EXPIRING_VALUE_ACV,
        r.ROI_PER_LEAD
    FROM latest_predictions lp
    INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
        ON lp.ASSET_ID = r.ID
    ORDER BY lp.CHURN_PROB DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    df["PRODUCT_NAME"] = df["PRODUCT2ID"].map(
        PRODUCT_MAPPING
    ).fillna("Other Asset")
    return df


@st.cache_data
def load_executive_summary():
    df = load_unity_churn_data()
    summary = {
        "total_assets": len(df),
        "avg_churn_prob": round(df["CHURN_PROB"].mean(), 4),
        "high_risk_count": len(df[df["CHURN_PROB"] > 0.7]),
    }
    trend = (
        df.groupby("MONTH_OF_EXPIRY")
        .agg(avg_churn_prob=("CHURN_PROB", "mean"), asset_count=("ASSET_ID", "count"))
        .reset_index()
        .sort_values("MONTH_OF_EXPIRY")
    )
    return summary, trend


@st.cache_data
def load_model_performance():
    conn = init_connection()
    query = """
    SELECT
        CHURN_FLOW_ID,
        SNAPSHOT_DATE,
        AUC_SCORE,
        ACCURACY,
        PRECISION_SCORE,
        RECALL_SCORE
    FROM TEAM_DATASCIENCE.PUBLIC.UNITY_CHURN_MODEL_PERFORMANCE
    ORDER BY SNAPSHOT_DATE DESC
    """
    try:
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception:
        conn.close()
        return pd.DataFrame()


@st.cache_data
def load_feature_importance():
    conn = init_connection()
    query = """
    WITH unity_assets AS (
        SELECT a.*
        FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY a
        INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
            ON a.ASSET_ID = r.ID
        WHERE r.PRODUCT2ID = '01t5f000006sGgOAAU'
    ),
    latest_predictions AS (
        SELECT *
        FROM unity_assets
        QUALIFY ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE DESC) = 1
    )
    SELECT
        MOST_IMPORTANT_FEATURE,
        COUNT(*) AS asset_count,
        ROUND(AVG(CHURN_PROB), 4) AS avg_churn_prob
    FROM latest_predictions
    WHERE MOST_IMPORTANT_FEATURE IS NOT NULL
    GROUP BY MOST_IMPORTANT_FEATURE
    ORDER BY asset_count DESC
    """
    df = pd.read_sql(query, conn)
    conn.close()
    return df


@st.cache_data
def load_filtered_assets(churn_min=0.0, churn_max=1.0, expiry_months=None):
    df = load_unity_churn_data()
    mask = df["CHURN_PROB"].between(churn_min, churn_max)
    if expiry_months and len(expiry_months) > 0:
        mask &= df["MONTH_OF_EXPIRY"].isin(expiry_months)
    result = df[mask].head(1000)
    return result
