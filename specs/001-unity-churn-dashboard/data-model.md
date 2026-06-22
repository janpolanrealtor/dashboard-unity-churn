# Data Model: Unity Churn Dashboard

**Date**: 2026-06-22  
**Source**: `TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY` + `TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS`

---

## Entity 1: Churn Prediction

**Source**: `TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY`

| Field | Type | Description | Constraints |
|---|---|---|---|
| `ASSET_ID` | VARCHAR | Unique asset identifier | PK, NOT NULL |
| `PREV_START_DATE` | TIMESTAMP | Current contract start date | NOT NULL |
| `EXPIRY_DATE` | TIMESTAMP | Current contract end date | NOT NULL |
| `MONTH_OF_EXPIRY` | TIMESTAMP | Normalized start-of-month of expiry | NOT NULL |
| `CHURN_PROB` | FLOAT | Estimated churn probability (0.0–1.0) | NOT NULL |
| `MOST_IMPORTANT_FEATURE` | VARCHAR | Primary driver feature behind prediction | NULLABLE |
| `CHURN_FLOW_ID` | VARCHAR | Metaflow run identifier | NOT NULL |
| `SNAPSHOT_DATE` | TIMESTAMP | Prediction generation timestamp | NOT NULL |

### Deduplication Rule
Only the latest prediction per asset should be used:
```sql
ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE DESC) = 1
```

---

## Entity 2: Asset Renewal

**Source**: `TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS`

| Field | Type | Description | Constraints |
|---|---|---|---|
| `ID` | VARCHAR | Unique asset identifier | PK, NOT NULL |
| `PRODUCT2ID` | VARCHAR | Product classification code | NOT NULL |
| `PRODUCT_NAME` | VARCHAR | Human-readable product name | NULLABLE |
| `ACCOUNTID` | VARCHAR | Account identifier | NULLABLE |
| `EXPIRING_VALUE_ACV` | FLOAT | Annual contract value at expiry | NULLABLE |
| `ROI_PER_LEAD` | FLOAT | ROI per lead metric | NULLABLE |

### Product Classification
- **Unity Package**: `PRODUCT2ID = '01t5f000006sGgOAAU'`
- **MVIP Legacy**: `PRODUCT2ID = '01t3a000004vIdIAAU'`

---

## Entity 3: Model Performance Record (Proposed)

**Target**: `TEAM_DATASCIENCE.PUBLIC.UNITY_CHURN_MODEL_PERFORMANCE`

| Field | Type | Description | Constraints |
|---|---|---|---|
| `CHURN_FLOW_ID` | VARCHAR | Metaflow run identifier | PK, NOT NULL |
| `SNAPSHOT_DATE` | TIMESTAMP_NTZ | When metrics were generated | NOT NULL |
| `AUC_SCORE` | FLOAT | Area under ROC curve | NULLABLE |
| `ACCURACY` | FLOAT | Model accuracy | NULLABLE |
| `PRECISION_SCORE` | FLOAT | Model precision | NULLABLE |
| `RECALL_SCORE` | FLOAT | Model recall | NULLABLE |
| `CREATED_AT` | TIMESTAMP_NTZ | Row insertion timestamp | DEFAULT CURRENT_TIMESTAMP() |

### Ownership
- **Creation & maintenance**: Pipeline team (`mvip_churn_baseline_flow`)
- **Consumption**: Dashboard (read-only)

---

## Entity Relationships

```
Churn Prediction (ASSET_ID) ---> Asset Renewal (ID)
         |                              |
         | INNER JOIN                    | PRODUCT2ID filters Unity
         | on ASSET_ID = ID             | '01t5f000006sGgOAAU'
         v                              v
    Joined View: Unity Churn Assets
              |
              | ROW_NUMBER() dedup
              | (latest SNAPSHOT_DATE per ASSET_ID)
              v
        Dashboard Data (max 1,000 rows)

Model Performance Record (CHURN_FLOW_ID)
    - Independent entity, no direct join to predictions
    - Displayed on Tab 2 independently
```

---

## Validation Rules

| Rule | Entity | Logic |
|---|---|---|
| Churn probability range | Churn Prediction | `0.0 <= CHURN_PROB <= 1.0` |
| Unity filter | Joined View | `PRODUCT2ID = '01t5f000006sGgOAAU'` |
| Deduplication | Joined View | `ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE DESC) = 1` |
| Row limit | Dashboard | Max 1,000 rows rendered in Streamlit |
| Asset ID match | Join condition | `ASSET_CHURN_HISTORY.ASSET_ID = MVIP_ASSET_RENEWALS_SNAPSHOTS.ID` |
