# Quickstart: Call Worklist View

## Implementation Order

1. **`utils/formatting.py`** — Add `fmt_renews_in(days)` function
2. **`utils/queries.py`** — Add `load_call_worklist()` with market JOIN and trend LAG
3. **`app.py`** — Replace Tab 1 table section with call worklist rendering

## Key Patterns

### New query function
```python
@st.cache_data(ttl=3600)
def load_call_worklist() -> pd.DataFrame:
    query = """
    WITH latest_churn AS (
        SELECT a.ASSET_ID, a.CHURN_PROB, a.MOST_IMPORTANT_FEATURE,
               a.EXPIRY_DATE, a.SNAPSHOT_DATE AS PREDICTION_DATE
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
        c.ASSET_ID, c.CHURN_PROB, c.MOST_IMPORTANT_FEATURE, c.EXPIRY_DATE,
        c.PREDICTION_DATE,
        r.NAME AS ACCOUNT_NAME, r.ROI_PER_LEAD, r.EXPIRING_VALUE_ACV,
        DATEDIFF('day', CURRENT_DATE(), r.EXPIRY_DATE::DATE) AS DAYS_UNTIL_EXPIRY,
        COALESCE(m.NAME, 'National (VIP Package)') AS MARKET_NAME,
        p.PREV_CHURN_PROB
    FROM latest_churn c
    INNER JOIN ...  -- rest of JOIN chain
    """
    df = _run_query(query)
    return df.replace([np.inf, -np.inf], np.nan)
```

### Trend arrow helper
```python
def trend_arrow(current: float, previous: float | None) -> str:
    if previous is None or pd.isna(previous):
        return '<span style="color:#726A60">–</span>'
    if current < previous:
        return '<span class="trend-down">↓</span>'
    if current > previous:
        return '<span class="trend-up">↑</span>'
    return '<span style="color:#726A60">–</span>'
```

### Remember
- UPPERCASE column names in all pandas operations
- `@st.cache_data(ttl=3600)` on all query functions
- `df.replace([np.inf, -np.inf], np.nan)` after every query
- All formatters return `"—"` for NaN/None
- No `snowflake-connector-python` or version pins in `environment.yml`
