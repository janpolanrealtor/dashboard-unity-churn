# Research: Call Worklist View

## R1 — FIVETRAN_REFERRAL Schema Tables

**Unknown**: Whether `FIVETRAN_REFERRAL.PG_PUBLIC.LEAD_ZONE` and `FIVETRAN_REFERRAL.PG_PUBLIC.MARKET` exist in Snowflake.

**Decision**: Trust the user's specification. These tables were explicitly provided by the Product Manager who verified the schema. The `MVIP_ZONE_ID` column is confirmed to exist in `MVIP_ASSET_RENEWALS_SNAPSHOTS` (not in the documented columns of §6.2, but among the ~106 undocumented columns). The LEFT JOIN chain is:

```sql
LEFT JOIN FIVETRAN_REFERRAL.PG_PUBLIC.LEAD_ZONE lz ON r.MVIP_ZONE_ID = lz.ID
LEFT JOIN FIVETRAN_REFERRAL.PG_PUBLIC.MARKET m ON lz.MARKET_ID = m.ID
```

**Alternatives considered**:
- Skip market resolution entirely (would show raw `MVIP_ZONE_ID` — poor UX)
- Maintain a local Python mapping dict (brittle, requires manual updates)
- Use a CASE statement with known zone IDs (maintenance burden)

**Rationale**: The FIVETRAN schema is the authoritative source for market/zone data in Snowflake. This approach keeps resolution in SQL where it can be maintained by data engineering.

---

## R2 — NAME Column in MVIP_ASSET_RENEWALS_SNAPSHOTS

**Unknown**: Whether `NAME` exists in `MVIP_ASSET_RENEWALS_SNAPSHOTS` (the `ACCOUNT_NAME` from Salesforce).

**Decision**: The column is referenced as both `NAME` and `ACCOUNT_NAME` in the user's specification. The existing code uses `ACCOUNTID` for display. We assume `NAME` exists (likely among the ~106 undocumented columns). Query pattern:

```sql
SELECT r.NAME AS ACCOUNT_NAME, ...
```

**Fallback**: If `NAME` is not available at query time, fall back to `ACCOUNTID` display and log a warning.

**Alternatives considered**:
- Join to Salesforce account table directly (schema unknown, may not be available)
- Hardcode account IDs to names in Python (not scalable)

---

## R3 — Trend Direction Indicator

**Unknown**: How to determine whether churn probability is trending up or down.

**Decision**: Use `LAG(CHURN_PROB)` over the asset's historical snapshots partitioned by `ASSET_ID` and ordered by `SNAPSHOT_DATE ASC`. Compare the current `CHURN_PROB` to the previous snapshot's value:

- Current > Previous → `↑` (worsening, red)
- Current < Previous → `↓` (improving, green)
- Current = Previous or no prior snapshot → `–` (neutral, gray)

This requires a second query or subquery in `load_call_worklist()` that fetches the previous snapshot's `CHURN_PROB` for each asset. Pattern:

```sql
WITH ranked AS (
    SELECT ASSET_ID, CHURN_PROB,
           ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE DESC) AS rn,
           LAG(CHURN_PROB) OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE ASC) AS PREV_CHURN_PROB
    FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY
)
```

**Alternatives considered**:
- Use `PREV_START_DATE` column (not well understood; may not represent prior run)
- Compare against portfolio average (would not show account-specific trend)
- Omit trend entirely (P3 requirement — acceptable to stub initially)

**Rationale**: `LAG()` is the canonical SQL window function for this use case. It's efficient and requires no external state.
