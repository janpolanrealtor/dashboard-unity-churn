# Findings and Exploratory Analysis Report

**Project Name:** Unity Churn Dashboard  
**Status Date:** June 22, 2026  
**Compiled By:** Wizeline Engineering Team  

---

## 1. Summary of Exploration
This document consolidates all architectural and data-level findings gathered during the initial exploratory phase of the Unity Churn Dashboard ticket. These findings form the empirical basis for our technical design and implementation steps.

---

## 2. Key Technical Findings

### 2.1 Schema and Database Architecture
*   **The Unity Schema Discrepancy:** The initial target of querying `TEAM_DATASCIENCE.UNITY.CHURN_HISTORY` failed because the `UNITY` schema does not exist in the `TEAM_DATASCIENCE` database.
*   **Active Schemas Identified:** Direct metadata queries inside Snowflake confirmed that the active machine learning schema is **`TEAM_DATASCIENCE.MVIP`**.
*   **Concrete Churn Source:** The master table containing active model predictions is **`TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY`**.

### 2.2 The Product-Id Association (Unity vs. Legacy)
*   The raw prediction table `TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY` contains predictions for both MVIP Legacy and Unity Package assets. However, it does not persist the `PRODUCT2ID` column.
*   **Resolution:** The database context shows that we can successfully isolate Unity Package assets (`01t5f000006sGgOAAU`) from MVIP Legacy assets (`01t3a000004vIdIAAU`) by performing an `INNER JOIN` with the computed renewals snapshot table: `TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS`.
*   A query testing this join successfully matched the asset records and returned 1,848 unique assets.

### 2.3 Model Performance Metrics Gap
*   The model training flow (`mvip_renewals_v2`) generates performance evaluations (such as AUC, accuracy, and calibration curves) and displays them on Metaflow cards.
*   **The Gap:** These historical metrics are not written to Snowflake. Only raw asset-level predictions are stored in `ASSET_CHURN_HISTORY`.
*   **Resolution:** To render model performance history in the Streamlit UI, a dedicated performance telemetry table must be proposed in the engineering design.

### 2.4 User Privileges and Environment
*   Execution of `SHOW GRANTS TO ROLE PRODUCER_DATASCIENCE_ROLE` confirmed that the active developer role already possesses the required `USAGE` and object creation privileges.
*   There is no requirement to run manual database `GRANT` scripts. Administrative privileges over the `USER_SANDBOX` database are owned by `_DO_NOT_USE_ROLE`.
*   **Local Execution Verification:** Streamlit can be run locally via `streamlit run app.py` by configuring a local `.streamlit/secrets.toml` file. The local Python runtime uses the network to connect securely to the cloud Snowflake warehouse, execute the SQL, and retrieve results in memory.

---

## 3. Data Schema Specifications

### 3.1 Churn History Schema (`TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY`)
The table contains the following structure verified via direct inspection queries:
*   `ASSET_ID` (VARCHAR) - Unique identifier of the asset.
*   `PREV_START_DATE` (TIMESTAMP) - Start date of the current contract.
*   `EXPIRY_DATE` (TIMESTAMP) - End date of the current contract.
*   `MONTH_OF_EXPIRY` (TIMESTAMP) - Normalized start-of-month date for expiration.
*   `CHURN_PROB` (FLOAT) - Estimated probability of churn.
*   `MOST_IMPORTANT_FEATURE` (VARCHAR) - The primary feature driver contributing to the prediction.
*   `CHURN_FLOW_ID` (VARCHAR) - Metaflow run identifier.
*   `SNAPSHOT_DATE` (TIMESTAMP) - Timestamp of when the prediction was generated.

---

## 4. Risks and Mitigation Strategies

| Risk | Impact | Mitigation Strategy |
| :--- | :--- | :--- |
| **Incorrect Asset Classification** | High | Always filter and group assets by joining the renewals snapshot and mapping the specific `PRODUCT2ID` codes. |
| **Duplicate Rows in UI** | Medium | Implement `ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY snapshot_date DESC) = 1` inside the data acquisition queries to isolate only the latest predictions. |
| **Slow Streamlit UI Load Times** | High | Avoid loading large raw datasets. Push aggregations and sorting down to the Snowflake engine, and enforce strict row limits in Streamlit. |