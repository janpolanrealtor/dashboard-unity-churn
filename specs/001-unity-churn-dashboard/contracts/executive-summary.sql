-- Contract: Executive Summary (Tab 1)
-- Purpose: Aggregate KPI data + trend chart for high-level churn overview
-- Dependency: Relies on the Unity-filtered, deduplicated churn view

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
-- KPI: Total assets
SELECT COUNT(*) AS total_assets FROM latest_predictions;

-- KPI: Average churn probability
SELECT ROUND(AVG(CHURN_PROB), 4) AS avg_churn_prob FROM latest_predictions;

-- KPI: High-risk count (threshold > 0.7)
SELECT COUNT(*) AS high_risk_count
FROM latest_predictions
WHERE CHURN_PROB > 0.7;

-- Trend: Average churn probability by expiry month
SELECT
    MONTH_OF_EXPIRY,
    ROUND(AVG(CHURN_PROB), 4) AS avg_churn_prob,
    COUNT(*) AS asset_count
FROM latest_predictions
GROUP BY MONTH_OF_EXPIRY
ORDER BY MONTH_OF_EXPIRY;
