# Data Model: Call Worklist View

## WorklistRow

The core entity displayed in the Portfolio tab worklist table. One row per Unity Package asset (latest snapshot only).

| Field | Source | Type | Notes |
|---|---|---|---|
| `ASSET_ID` | `ASSET_CHURN_HISTORY.ASSET_ID` | VARCHAR | Primary key; Salesforce asset ID |
| `ACCOUNT_NAME` | `MVIP_ASSET_RENEWALS_SNAPSHOTS.NAME` | VARCHAR | Displayed in bold in the worklist |
| `MARKET_NAME` | `MARKET.NAME` (via FIVETRAN_REFERRAL JOIN chain) | VARCHAR | Displayed below account name in gray; "Unknown" → "National (VIP Package)" |
| `EXPIRING_VALUE_ACV` | `MVIP_ASSET_RENEWALS_SNAPSHOTS.EXPIRING_VALUE_ACV` | FLOAT | Currency-formatted; drives "below viability" alert |
| `ROI_PER_LEAD` | `MVIP_ASSET_RENEWALS_SNAPSHOTS.ROI_PER_LEAD` | FLOAT | If <0, show red "below viability" text |
| `CHURN_PROB` | `ASSET_CHURN_HISTORY.CHURN_PROB` | FLOAT (0–1) | Drives the custom progress bar color and position |
| `PREV_CHURN_PROB` | `ASSET_CHURN_HISTORY` via `LAG()` | FLOAT (0–1) | Prior snapshot value for trend direction; NULL if no prior snapshot |
| `MOST_IMPORTANT_FEATURE` | `ASSET_CHURN_HISTORY.MOST_IMPORTANT_FEATURE` | VARCHAR | Top SHAP feature name; displayed with trend arrow |
| `DAYS_UNTIL_EXPIRY` | Computed: `DATEDIFF('day', CURRENT_DATE(), r.EXPIRY_DATE::DATE)` | INTEGER | Drives countdown display (3 states) |
| `EXPIRY_DATE` | `ASSET_CHURN_HISTORY.EXPIRY_DATE` | DATE | Raw date for countdown computation |
| `PREDICTION_DATE` | `ASSET_CHURN_HISTORY.SNAPSHOT_DATE` (aliased) | DATE | Snapshot timestamp for trend anchor |

## MarketZone

A geographic zone resolved from `MVIP_ZONE_ID` via the FIVETRAN_REFERRAL schema. Used solely for display.

| Field | Source | Type | Notes |
|---|---|---|---|
| `ZONE_ID` | `LEAD_ZONE.ID` | VARCHAR | Joins to `MVIP_ASSET_RENEWALS_SNAPSHOTS.MVIP_ZONE_ID` |
| `MARKET_ID` | `LEAD_ZONE.MARKET_ID` | VARCHAR | Joins to `MARKET.ID` |
| `MARKET_NAME` | `MARKET.NAME` | VARCHAR | Displayed in worklist; "Unknown" → "National (VIP Package)" |

## Validation Rules

- `CHURN_PROB`: MUST be 0.0–1.0. Values outside this range treated as NaN.
- `EXPIRING_VALUE_ACV`: MUST be ≥ 0. Negative values treated as NaN.
- `DAYS_UNTIL_EXPIRY`: Can be negative (expired). Displayed as "Expired" when <0.
- Infinity (`±Inf`): All numeric columns MUST be sanitized to NaN after query execution.

## State Transitions

The worklist is a read-only view — no state transitions. The drill-down panel (existing `load_account_detail()`) is unchanged and triggered via `st.selectbox`.
