-- Contract: Model Performance (Tab 2)
-- Purpose: Historical model metrics and global feature importance
-- Dependency: TEAM_DATASCIENCE.PUBLIC.UNITY_CHURN_MODEL_PERFORMANCE (proposed table)

-- Historical model metrics ordered by snapshot date
SELECT
    CHURN_FLOW_ID,
    SNAPSHOT_DATE,
    AUC_SCORE,
    ACCURACY,
    PRECISION_SCORE,
    RECALL_SCORE
FROM TEAM_DATASCIENCE.PUBLIC.UNITY_CHURN_MODEL_PERFORMANCE
ORDER BY SNAPSHOT_DATE DESC;

-- Global feature importance (from model prediction table)
-- Uses the most frequent MOST_IMPORTANT_FEATURE across latest predictions
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
ORDER BY asset_count DESC;
