import pandas as pd
import streamlit as st

PRODUCT_MAPPING = {
    "01t3a000004vIdIAAU": "MVIP Legacy",
    "01t5f000006sGgOAAU": "Unity Package",
}

UNITY_PRODUCT_ID = "01t5f000006sGgOAAU"


@st.cache_resource
def _get_session():
    """Return (session, mode). Cached for the lifetime of the Streamlit process
    so externalbrowser auth fires exactly once per local dev session."""
    try:
        from snowflake.snowpark.context import get_active_session

        return get_active_session(), "snowpark"
    except Exception:
        import snowflake.connector

        cfg = st.secrets["snowflake"]
        params = {
            "user": cfg["user"],
            "account": cfg["account"],
            "warehouse": cfg["warehouse"],
            "database": "TEAM_DATASCIENCE",
            "schema": "PUBLIC",
        }
        if "authenticator" in cfg:
            params["authenticator"] = cfg["authenticator"]
        else:
            params["password"] = cfg["password"]
        return snowflake.connector.connect(**params), "connector"


def _run_query(query: str) -> pd.DataFrame:
    session, mode = _get_session()
    if mode == "snowpark":
        return session.sql(query).to_pandas()
    # Use cursor directly to avoid the pandas SQLAlchemy deprecation warning
    cur = session.cursor()
    cur.execute(query)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    cur.close()
    return pd.DataFrame(rows, columns=cols)


# ── Core Unity churn dataset (latest snapshot per asset) ────────────────────
_UNITY_CHURN_SQL = """
WITH latest_churn AS (
    SELECT
        a.ASSET_ID,
        a.CHURN_PROB,
        a.MOST_IMPORTANT_FEATURE,
        a.EXPIRY_DATE,
        a.MONTH_OF_EXPIRY,
        a.SNAPSHOT_DATE AS PREDICTION_DATE,
        a.CHURN_FLOW_ID
    FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY a
    INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
        ON a.ASSET_ID = r.ID
    WHERE r.PRODUCT2ID = '01t5f000006sGgOAAU'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY a.ASSET_ID ORDER BY a.SNAPSHOT_DATE DESC) = 1
),
latest_renewals AS (
    SELECT
        ID,
        ACCOUNTID,
        PRODUCT2ID,
        EXPIRING_VALUE_ACV,
        ROI_PER_LEAD,
        FULFILLMENT_PCT,
        TENURE,
        IS_FULFILLED,
        IS_COMPETITIVE_MARKET
    FROM TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS
    WHERE PRODUCT2ID = '01t5f000006sGgOAAU'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY ID ORDER BY SNAPSHOT_DATE DESC) = 1
)
SELECT
    c.ASSET_ID,
    c.CHURN_PROB,
    c.MOST_IMPORTANT_FEATURE,
    c.EXPIRY_DATE,
    c.MONTH_OF_EXPIRY,
    c.PREDICTION_DATE,
    c.CHURN_FLOW_ID,
    r.ACCOUNTID,
    r.PRODUCT2ID,
    r.EXPIRING_VALUE_ACV,
    r.ROI_PER_LEAD,
    r.FULFILLMENT_PCT,
    r.TENURE,
    r.IS_FULFILLED,
    r.IS_COMPETITIVE_MARKET
FROM latest_churn c
INNER JOIN latest_renewals r ON c.ASSET_ID = r.ID
ORDER BY c.CHURN_PROB DESC
"""


@st.cache_data(ttl=3600)
def _load_base() -> pd.DataFrame:
    df = _run_query(_UNITY_CHURN_SQL)
    df["PRODUCT_NAME"] = df["PRODUCT2ID"].map(PRODUCT_MAPPING).fillna("Other Asset")
    return df


@st.cache_data(ttl=3600)
def load_portfolio_summary() -> dict:
    df = _load_base()
    return {
        "total_assets": len(df),
        "avg_churn_prob": round(float(df["CHURN_PROB"].mean()), 4),
        "high_risk_count": int((df["CHURN_PROB"] > 0.7).sum()),
        "total_acv": float(df["EXPIRING_VALUE_ACV"].sum()),
    }


@st.cache_data(ttl=3600)
def load_portfolio_accounts() -> pd.DataFrame:
    return _load_base()


@st.cache_data(ttl=3600)
def load_account_detail(asset_id: str) -> pd.DataFrame:
    """All snapshots for a single asset, ordered by date for trend chart.
    Attempts to include SPILLOVER_PCT; silently omits it if the column doesn't exist."""
    _join = f"""
    FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY a
    INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
        ON a.ASSET_ID = r.ID
    WHERE a.ASSET_ID = '{asset_id}'
      AND r.PRODUCT2ID = '01t5f000006sGgOAAU'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY r.ID ORDER BY r.SNAPSHOT_DATE DESC) = 1
    ORDER BY a.SNAPSHOT_DATE ASC
    """
    try:
        return _run_query(f"""
            SELECT
                a.ASSET_ID, a.CHURN_PROB, a.MOST_IMPORTANT_FEATURE,
                a.SNAPSHOT_DATE, a.EXPIRY_DATE, a.MONTH_OF_EXPIRY,
                r.ACCOUNTID, r.EXPIRING_VALUE_ACV, r.ROI_PER_LEAD,
                r.FULFILLMENT_PCT, r.TENURE, r.IS_FULFILLED,
                r.IS_COMPETITIVE_MARKET, r.SPILLOVER_PCT
            {_join}
        """)
    except Exception:
        return _run_query(f"""
            SELECT
                a.ASSET_ID, a.CHURN_PROB, a.MOST_IMPORTANT_FEATURE,
                a.SNAPSHOT_DATE, a.EXPIRY_DATE, a.MONTH_OF_EXPIRY,
                r.ACCOUNTID, r.EXPIRING_VALUE_ACV, r.ROI_PER_LEAD,
                r.FULFILLMENT_PCT, r.TENURE, r.IS_FULFILLED,
                r.IS_COMPETITIVE_MARKET
            {_join}
        """)


@st.cache_data(ttl=3600)
def load_feature_distributions() -> dict:
    """Q1 and Q3 for all numeric feature columns across the latest Unity snapshot per asset.
    SPILLOVER_PCT is optional — silently excluded if the column doesn't exist."""
    _with_spillover = """
    WITH deduped AS (
        SELECT TENURE, FULFILLMENT_PCT, ROI_PER_LEAD, EXPIRING_VALUE_ACV, SPILLOVER_PCT
        FROM TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS
        WHERE PRODUCT2ID = '01t5f000006sGgOAAU'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY ID ORDER BY SNAPSHOT_DATE DESC) = 1
    )
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY TENURE)             AS TENURE_Q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY TENURE)             AS TENURE_Q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY FULFILLMENT_PCT)    AS FULFILLMENT_Q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY FULFILLMENT_PCT)    AS FULFILLMENT_Q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ROI_PER_LEAD)       AS ROI_Q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ROI_PER_LEAD)       AS ROI_Q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXPIRING_VALUE_ACV) AS ACV_Q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXPIRING_VALUE_ACV) AS ACV_Q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY SPILLOVER_PCT)      AS SPILLOVER_Q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY SPILLOVER_PCT)      AS SPILLOVER_Q3
    FROM deduped
    """
    _without_spillover = """
    WITH deduped AS (
        SELECT TENURE, FULFILLMENT_PCT, ROI_PER_LEAD, EXPIRING_VALUE_ACV
        FROM TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS
        WHERE PRODUCT2ID = '01t5f000006sGgOAAU'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY ID ORDER BY SNAPSHOT_DATE DESC) = 1
    )
    SELECT
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY TENURE)             AS TENURE_Q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY TENURE)             AS TENURE_Q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY FULFILLMENT_PCT)    AS FULFILLMENT_Q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY FULFILLMENT_PCT)    AS FULFILLMENT_Q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY ROI_PER_LEAD)       AS ROI_Q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY ROI_PER_LEAD)       AS ROI_Q3,
        PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY EXPIRING_VALUE_ACV) AS ACV_Q1,
        PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY EXPIRING_VALUE_ACV) AS ACV_Q3
    FROM deduped
    """

    def _safe_float(val):
        return float(val) if val is not None and str(val) != "nan" else None

    def _extract(r, with_spillover: bool) -> dict:
        out = {
            "TENURE_Q1":      _safe_float(r.get("TENURE_Q1")),
            "TENURE_Q3":      _safe_float(r.get("TENURE_Q3")),
            "FULFILLMENT_Q1": _safe_float(r.get("FULFILLMENT_Q1")),
            "FULFILLMENT_Q3": _safe_float(r.get("FULFILLMENT_Q3")),
            "ROI_Q1":         _safe_float(r.get("ROI_Q1")),
            "ROI_Q3":         _safe_float(r.get("ROI_Q3")),
            "ACV_Q1":         _safe_float(r.get("ACV_Q1")),
            "ACV_Q3":         _safe_float(r.get("ACV_Q3")),
            "SPILLOVER_Q1":   None,
            "SPILLOVER_Q3":   None,
        }
        if with_spillover:
            out["SPILLOVER_Q1"] = _safe_float(r.get("SPILLOVER_Q1"))
            out["SPILLOVER_Q3"] = _safe_float(r.get("SPILLOVER_Q3"))
        return out

    _empty = {k: None for k in (
        "TENURE_Q1", "TENURE_Q3", "FULFILLMENT_Q1", "FULFILLMENT_Q3",
        "ROI_Q1", "ROI_Q3", "ACV_Q1", "ACV_Q3", "SPILLOVER_Q1", "SPILLOVER_Q3",
    )}

    try:
        df = _run_query(_with_spillover)
        return _extract(df.iloc[0], with_spillover=True)
    except Exception:
        try:
            df = _run_query(_without_spillover)
            return _extract(df.iloc[0], with_spillover=False)
        except Exception:
            return _empty


@st.cache_data(ttl=3600)
def load_pipeline_runs() -> pd.DataFrame:
    query = """
    WITH unity_runs AS (
        SELECT
            a.CHURN_FLOW_ID,
            a.SNAPSHOT_DATE,
            a.CHURN_PROB
        FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY a
        INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
            ON a.ASSET_ID = r.ID
        WHERE r.PRODUCT2ID = '01t5f000006sGgOAAU'
    )
    SELECT
        CHURN_FLOW_ID,
        SNAPSHOT_DATE,
        COUNT(*)                                              AS TOTAL_ASSETS,
        ROUND(AVG(CHURN_PROB), 4)                            AS AVG_CHURN_PROB,
        ROUND(MEDIAN(CHURN_PROB), 4)                         AS MEDIAN_CHURN_PROB,
        COUNT(CASE WHEN CHURN_PROB > 0.7 THEN 1 END)         AS HIGH_RISK_COUNT,
        ROUND(COUNT(CASE WHEN CHURN_PROB > 0.7 THEN 1 END)
              / NULLIF(COUNT(*), 0), 4)                      AS HIGH_RISK_RATE
    FROM unity_runs
    GROUP BY CHURN_FLOW_ID, SNAPSHOT_DATE
    ORDER BY SNAPSHOT_DATE DESC
    """
    try:
        return _run_query(query)
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_feature_importance() -> pd.DataFrame:
    query = """
    WITH latest_churn AS (
        SELECT
            a.ASSET_ID,
            a.CHURN_PROB,
            a.MOST_IMPORTANT_FEATURE
        FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY a
        INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
            ON a.ASSET_ID = r.ID
        WHERE r.PRODUCT2ID = '01t5f000006sGgOAAU'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY a.ASSET_ID ORDER BY a.SNAPSHOT_DATE DESC) = 1
    )
    SELECT
        MOST_IMPORTANT_FEATURE,
        COUNT(*)                   AS ASSET_COUNT,
        ROUND(AVG(CHURN_PROB), 4)  AS AVG_CHURN_PROB
    FROM latest_churn
    WHERE MOST_IMPORTANT_FEATURE IS NOT NULL
    GROUP BY MOST_IMPORTANT_FEATURE
    ORDER BY ASSET_COUNT DESC
    """
    return _run_query(query)
