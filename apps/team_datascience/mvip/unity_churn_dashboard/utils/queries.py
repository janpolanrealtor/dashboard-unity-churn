import numpy as np
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
    # FINAL_RATECARD = 0.0 causes DISCOUNT_PCT to be -Infinity in the pipeline.
    # Sanitize here so all downstream formatters receive NaN, not ±Inf.
    df = df.replace([np.inf, -np.inf], np.nan)
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


_CALL_WORKLIST_SQL = """
WITH latest_churn AS (
    SELECT
        a.ASSET_ID,
        a.CHURN_PROB,
        a.MOST_IMPORTANT_FEATURE,
        a.EXPIRY_DATE,
        a.SNAPSHOT_DATE AS PREDICTION_DATE
    FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY a
    INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
        ON a.ASSET_ID = r.ID
    WHERE r.PRODUCT2ID = '01t5f000006sGgOAAU'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY a.ASSET_ID ORDER BY a.SNAPSHOT_DATE DESC) = 1
),
prev_churn AS (
    SELECT ASSET_ID, CHURN_PROB AS PREV_CHURN_PROB
    FROM (
        SELECT ASSET_ID, CHURN_PROB,
               ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE DESC) AS rn
        FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY
    ) WHERE rn = 2
)
SELECT
    c.ASSET_ID,
    c.CHURN_PROB,
    c.MOST_IMPORTANT_FEATURE,
    c.EXPIRY_DATE,
    c.PREDICTION_DATE,
    r.NAME                               AS ACCOUNT_NAME,
    r.ROI_PER_LEAD,
    r.EXPIRING_VALUE_ACV,
    DATEDIFF('day', CURRENT_DATE(), r.EXPIRY_DATE::DATE) AS DAYS_UNTIL_EXPIRY,
    COALESCE(m.NAME, 'National (VIP Package)')            AS MARKET_NAME,
    p.PREV_CHURN_PROB
FROM latest_churn c
INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
    ON c.ASSET_ID = r.ID
LEFT JOIN FIVETRAN_REFERRAL.PG_PUBLIC.LEAD_ZONE lz
    ON r.MVIP_ZONE_ID = lz.ID
LEFT JOIN FIVETRAN_REFERRAL.PG_PUBLIC.MARKET m
    ON lz.MARKET_ID = m.ID
LEFT JOIN prev_churn p
    ON c.ASSET_ID = p.ASSET_ID
ORDER BY c.CHURN_PROB DESC
"""


@st.cache_data(ttl=3600)
def load_call_worklist() -> pd.DataFrame:
    df = _run_query(_CALL_WORKLIST_SQL)
    df = df.replace([np.inf, -np.inf], np.nan)
    return df


@st.cache_data(ttl=3600)
def load_portfolio_accounts() -> pd.DataFrame:
    return _load_base()


@st.cache_data(ttl=3600)
def load_account_detail(asset_id: str) -> pd.DataFrame:
    """All snapshots for a single asset, ordered by date for trend chart."""
    df = _run_query(f"""
        SELECT
            a.ASSET_ID, a.CHURN_PROB, a.MOST_IMPORTANT_FEATURE,
            a.SNAPSHOT_DATE, a.EXPIRY_DATE, a.MONTH_OF_EXPIRY,
            r.ACCOUNTID, r.EXPIRING_VALUE_ACV, r.ROI_PER_LEAD,
            r.FULFILLMENT_PCT, r.TENURE, r.IS_FULFILLED,
            r.IS_COMPETITIVE_MARKET, r.SPILLOVER_PCT
        FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY a
        INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
            ON a.ASSET_ID = r.ID
        WHERE a.ASSET_ID = '{asset_id}'
          AND r.PRODUCT2ID = '01t5f000006sGgOAAU'
        QUALIFY ROW_NUMBER() OVER (PARTITION BY r.ID ORDER BY r.SNAPSHOT_DATE DESC) = 1
        ORDER BY a.SNAPSHOT_DATE ASC
    """)
    return df.replace([np.inf, -np.inf], np.nan)


@st.cache_data(ttl=3600)
def load_feature_distributions() -> dict:
    """Q1 and Q3 for all numeric feature columns across the latest Unity snapshot per asset.

    Verified production thresholds (CONSTITUTION.md §6.11):
      TENURE        Q1=3.0,     Q3=9.0      (higher is better)
      FULFILLMENT   Q1=1.105,   Q3=1.517    (higher is better)
      ROI_PER_LEAD  Q1=-0.357,  Q3=0.243    (higher is better)
      EXPIRING_ACV  Q1=41962.80 Q3=144441.72(higher is better)
      SPILLOVER_PCT Q1=0.045,   Q3=0.154    (lower is better)
    """
    query = """
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

    def _safe_float(val):
        return float(val) if val is not None and str(val) not in ("nan", "inf", "-inf") else None

    _empty = {
        k: None
        for k in (
            "TENURE_Q1",
            "TENURE_Q3",
            "FULFILLMENT_Q1",
            "FULFILLMENT_Q3",
            "ROI_Q1",
            "ROI_Q3",
            "ACV_Q1",
            "ACV_Q3",
            "SPILLOVER_Q1",
            "SPILLOVER_Q3",
        )
    }

    try:
        r = _run_query(query).iloc[0]
        return {k: _safe_float(r.get(k)) for k in _empty}
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
