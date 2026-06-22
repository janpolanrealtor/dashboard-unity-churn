-- Contract: Asset Explorer (Tab 3)
-- Purpose: Granular asset lookup with filters
-- Parameters:
--   :churn_prob_min - minimum churn probability filter (default: 0.0)
--   :churn_prob_max - maximum churn probability filter (default: 1.0)
--   :product_ids - array of product2id values (default: ['01t5f000006sGgOAAU'])
--   :expiry_months - array of MONTH_OF_EXPIRY values (default: all)

WITH unity_assets AS (
    SELECT a.*
    FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY a
    INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
        ON a.ASSET_ID = r.ID
    WHERE r.PRODUCT2ID IN (:product_ids)
),
latest_predictions AS (
    SELECT *
    FROM unity_assets
    QUALIFY ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE DESC) = 1
)
SELECT
    lp.ASSET_ID,
    r.ACCOUNTID,
    r.PRODUCT_NAME,
    lp.CHURN_PROB,
    lp.MOST_IMPORTANT_FEATURE,
    lp.EXPIRY_DATE,
    lp.MONTH_OF_EXPIRY,
    r.EXPIRING_VALUE_ACV,
    r.ROI_PER_LEAD
FROM latest_predictions lp
INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
    ON lp.ASSET_ID = r.ID
WHERE lp.CHURN_PROB BETWEEN :churn_prob_min AND :churn_prob_max
  AND lp.MONTH_OF_EXPIRY IN (:expiry_months)
ORDER BY lp.CHURN_PROB DESC
LIMIT 1000;
