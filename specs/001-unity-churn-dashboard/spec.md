# Feature Specification: Unity Churn Dashboard

**Feature Branch**: `001-unity-churn-dashboard`  
**Created**: 2026-06-22  
**Status**: Draft  
**Input**: SDD Draft v1 provided by Wizeline Engineering Team

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Executive Summary with KPIs and Churn Trend (Priority: P1)

Product Managers open the dashboard and see an aggregated overview of churn risk across all Unity Package assets. KPI cards display total assets, average churn probability, and high-risk asset count. A trend chart shows how average churn risk evolves over upcoming expiry months.

**Why this priority**: PMs need a one-glance summary to assess portfolio health and identify macro trends before diving into details. This is the core value of the dashboard.

**Independent Test**: A PM opens the dashboard URL and immediately sees updated KPI cards and a trend chart without needing to apply any filters.

**Acceptance Scenarios**:

1. **Given** the dashboard is loaded, **When** the page renders, **Then** the Executive Summary tab shows KPI cards for total assets, average churn probability, and high-risk count.
2. **Given** the user is on the Executive Summary tab, **When** data is available, **Then** a trend chart displays average churn probability over upcoming expiry months.
3. **Given** the user is on the Executive Summary tab, **When** no data is available, **Then** an empty state message is shown instead of a broken chart.

---

### User Story 2 - Model Performance Metrics (Priority: P2)

Technical users navigate to a dedicated tab displaying historical model performance metrics (AUC, Precision, Recall) and a static global feature importance summary. This helps stakeholders assess model reliability.

**Why this priority**: Model performance transparency builds trust in the churn predictions and helps PMs understand prediction confidence.

**Independent Test**: A user clicks the Model Performance tab and sees a table or chart with AUC, Precision, and Recall values along with feature importance rankings, without needing to interact with any filters.

**Acceptance Scenarios**:

1. **Given** the dashboard is loaded, **When** the user clicks the Model Performance tab, **Then** historical AUC, Precision, and Recall metrics are displayed.
2. **Given** the Model Performance tab is active, **When** model metrics data exists, **Then** a static global feature importance summary is shown.
3. **Given** the Model Performance tab is active, **When** no model metrics have been logged yet, **Then** a clear message indicates performance data is not yet available.

---

### User Story 3 - Asset Explorer with Filters (Priority: P3)

Product Managers search and filter individual assets to inspect specific churn predictions. The sidebar provides a churn probability slider, product type multiselect, and expiry month picker. Results are limited to prevent UI lag.

**Why this priority**: While the summary views serve most needs, PMs occasionally need to drill into specific assets for manual review or stakeholder questions.

**Independent Test**: A user navigates to the Asset Explorer tab, applies a churn probability filter (>0.7), and sees a paginated table of matching assets with asset ID, account ID, and product name.

**Acceptance Scenarios**:

1. **Given** the user is on the Asset Explorer tab, **When** they adjust the churn probability slider, **Then** the asset table updates to show only assets matching the filter range.
2. **Given** the user is on the Asset Explorer tab, **When** they select one or more product types in the multiselect, **Then** the table filters to show only those product types.
3. **Given** the user is on the Asset Explorer tab, **When** they select an expiry month, **Then** the table shows only assets expiring in that month.
4. **Given** any filter is applied, **When** the result set exceeds 1,000 rows, **Then** only the first 1,000 rows are displayed and a message indicates results are capped.

---

### Edge Cases

- What happens when the Snowflake connection fails or times out? A clear error message should be displayed indicating the user to retry or contact support.
- What happens when the renewals snapshot table has no rows for the Unity Package product ID? The dashboard should show empty states rather than broken visualizations.
- What happens when the model performance table has no historical data yet? Tab 2 should display a "no data available" message rather than an error or blank screen.
- How does the system handle duplicate predictions for the same asset? Only the latest prediction per asset should be displayed.
- How does the system handle very high-churn months where all assets are at risk? Charts and KPIs should scale correctly without visual distortion.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST connect to Snowflake and authenticate using the configured credentials.
- **FR-002**: System MUST load churn predictions from the predictions table and isolate Unity Package assets by joining with the renewals snapshot table.
- **FR-003**: System MUST deduplicate predictions so only the latest snapshot per asset is displayed.
- **FR-004**: System MUST display KPI cards showing total assets, average churn probability, and count of high-risk assets.
- **FR-005**: System MUST render a trend chart of average churn probability over expiry months.
- **FR-006**: System MUST display historical model performance metrics (AUC, Precision, Recall) in a dedicated tab.
- **FR-007**: System MUST display a static global feature importance summary.
- **FR-008**: System MUST provide an interactive asset explorer table showing asset ID, account ID, and product name.
- **FR-009**: System MUST provide sidebar filters: churn probability slider, product type multiselect, and expiry month picker.
- **FR-010**: System MUST cap displayed results at 1,000 rows with a user-visible notification.
- **FR-011**: System MUST cache database query results to avoid redundant warehouse sweeps when filters change.
- **FR-012**: System MUST display clear empty states or error messages when data sources are unavailable.

### Key Entities *(include if feature involves data)*

- **Churn Prediction**: An asset-level prediction with churn probability, most important feature, snapshot date, and associated asset ID.
- **Asset Renewal**: An asset record with product classification (Unity Package vs. Legacy), ACV, and ROI metrics used to enrich predictions with product metadata.
- **Model Performance Record**: Historical model evaluation metrics (AUC, accuracy, precision, recall) per model training run, used to display performance trends.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: PMs can view the dashboard Executive Summary with KPI cards and trend chart within 3 seconds of page load.
- **SC-002**: Asset Explorer loads and applies any filter in under 2 seconds for result sets up to 1,000 rows.
- **SC-003**: All three dashboard tabs render without errors when valid Snowflake credentials are provided.
- **SC-004**: Filter changes update charts and tables without requiring a full page reload.
- **SC-005**: Dashboard gracefully degrades with clear messages when any dependent data source is unavailable.

## Assumptions

- Users have valid Snowflake credentials with access to `TEAM_DATASCIENCE.MVIP` schema and `PRODUCER_DATASCIENCE_ROLE`.
- The renewals snapshot table `MVIP_ASSET_RENEWALS_SNAPSHOTS` already contains the `product2id` field needed to distinguish Unity Package assets.
- The target user is a Product Manager or technical stakeholder familiar with churn probability concepts.
- The dashboard will be deployed via Snowflake's native Streamlit interface (SiS).
- The UI will follow Realtor's Haven Foundations design guidelines with the specified color palette.
- All text and labels in the dashboard will be in English.
- Model performance metrics will be logged to a dedicated table (creation and maintenance of that table is handled separately).
- A maximum of 3 concurrent users is expected for the initial version.
