# Feature Specification: Call Worklist View

**Feature Branch**: `002-call-worklist`
**Created**: 2026-06-26
**Status**: Draft
**Input**: User description: "Build a refined, production-ready implementation of the 'Call Worklist' view (Direction A) for the Unity Churn Dashboard."

## User Scenarios & Testing

### User Story 1 — Product Manager reviews upcoming renewals at a glance (Priority: P1)

As a Product Manager, I want to see a ranked list of Unity Package accounts approaching renewal so that I can prioritize outreach to the highest-risk accounts first.

**Why this priority**: This is the core value of the worklist — replacing the current generic asset table with a purpose-built renewal triage view. Without it, PMs must cross-reference multiple data points manually.

**Independent Test**: A PM can open the Portfolio tab, see a table of Unity Package assets sorted by churn risk, and for each row immediately identify the account name, location, expiring contract value, churn probability, top churn driver, and days until expiry. Each row's risk level is visually distinguishable at a glance.

**Acceptance Scenarios**:

1. **Given** the dashboard is loaded, **When** the user navigates to the Portfolio tab, **Then** the worklist displays only Unity Package assets filtered by `PRODUCT2ID = '01t5f000006sGgOAAU'`.
2. **Given** the worklist is displayed, **When** there are multiple snapshots for the same asset, **Then** only the most recent snapshot (latest `SNAPSHOT_DATE`) appears for each asset.
3. **Given** an account's location resolves to "Unknown", **When** the worklist renders, **Then** the location displays as "National (VIP Package)" instead of "Unknown".

---

### User Story 2 — PM identifies accounts needing urgent intervention (Priority: P2)

As a Product Manager, I want to immediately see which accounts have high churn probability, negative profitability, or imminent expiry dates so that I can take targeted action.

**Why this priority**: Risk signals (churn >70%, negative ROI, <15 days to expiry) require immediate attention. Surfacing these visually reduces the chance of missed renewals.

**Independent Test**: A PM can scan the worklist and instantly identify:
- Accounts with churn probability >70% via a red progress bar
- Accounts with negative ROI via a "below viability" label
- Accounts expiring within 15 days via a red countdown

**Acceptance Scenarios**:

1. **Given** an asset has `CHURN_PROB > 0.70`, **When** the worklist renders, **Then** the churn risk indicator displays red (`#D92228`) across the full high-risk zone.
2. **Given** an asset has `ROI_PER_LEAD < 0.0`, **When** the worklist renders, **Then** the text "below viability" appears in red beneath the expiring ACV value.
3. **Given** an asset expires within 0 to 15 days, **When** the worklist renders, **Then** the countdown displays in bold red (`#D92228`).

---

### User Story 3 — PM reviews churn drivers and trends (Priority: P3)

As a Product Manager, I want to see the top churn driver for each account along with a visual trend signal so that I can understand what is driving churn risk without drilling into each account.

**Why this priority**: Trend awareness helps PMs identify worsening accounts proactively rather than reactively. This is valuable but not blocking for the initial worklist launch.

**Independent Test**: For each row, the user can see the `MOST_IMPORTANT_FEATURE` name and a small visual indicator showing whether churn probability has increased or decreased from the prior snapshot.

**Acceptance Scenarios**:

1. **Given** the worklist displays an account, **When** the user reads the row, **Then** the top churn driver text is accompanied by a trend direction indicator.
2. **Given** the user clicks on an account row, **When** the drill-down panel opens, **Then** the trend chart shows historical churn probability over time.

---

### Edge Cases

- What happens when `FINAL_RATECARD = 0.0` causes `DISCOUNT_PCT` to compute as `-Infinity`? All numeric computations must gracefully handle infinite and NaN values, displaying `"—"` instead of broken numbers.
- What happens when an asset has no prior snapshot? The trend indicator shows a neutral state (no direction) instead of failing.
- What happens when `MVIP_ZONE_ID` returns NULL or an unrecognized value? The location resolves to "National (VIP Package)" by default.
- What happens when `EXPIRY_DATE` is in the past? The renews countdown displays "Expired" in gray text instead of a negative number.

## Requirements

### Functional Requirements

- **FR-001**: The dashboard MUST display a sticky top navigation bar (56px height, white background, brand red logo) with navigation items that cleanly toggle between "Portfolio", "Pipeline History", and "Insights" views.
- **FR-002**: The Portfolio tab MUST display a worklist table showing only Unity Package assets (`PRODUCT2ID = '01t5f000006sGgOAAU'`).
- **FR-003**: The worklist query MUST deduplicate assets by returning only the latest snapshot per asset (`QUALIFY ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE DESC) = 1`).
- **FR-004**: Each row MUST display the account name in bold with the resolved market location below it in smaller gray text.
- **FR-005**: Unknown market locations MUST display as "National (VIP Package)" rather than "Unknown".
- **FR-006**: Each row MUST display the expiring contract value (`EXPIRING_VALUE_ACV`) formatted as currency.
- **FR-007**: When `ROI_PER_LEAD` is negative, the worklist MUST display "below viability" in red beneath the ACV value.
- **FR-008**: Each row MUST display a visual churn probability indicator as a color-shaded horizontal bar with a position marker, using red for high risk (>70%), yellow for medium risk (40-70%), and green for low risk (<40%).
- **FR-009**: Each row MUST display the top churn driver name accompanied by a trend direction indicator showing whether churn probability improved or worsened since the prior snapshot.
- **FR-010**: Each row MUST display the days remaining until contract expiry, computed from the current date.
- **FR-011**: Expired contracts MUST display "Expired" in gray text. Contracts expiring within 15 days MUST display the countdown in bold red. All others display in standard charcoal text.
- **FR-012**: All numeric data MUST be sanitized so that infinity values (positive or negative) are treated as missing, and missing values render as `"—"` in the UI.
- **FR-013**: Clicking a worklist row MUST open a drill-down panel showing the account's churn probability trend over time and portfolio position distribution.

### Key Entities

- **Unity Package Asset**: A Salesforce asset record for the Unity product (`PRODUCT2ID = '01t5f000006sGgOAAU'`). Represents a customer contract under management. Key attributes: asset ID, account name, location, expiring value, tenure, ROI, churn probability, top churn driver.
- **Churn Snapshot**: A point-in-time prediction record from the machine learning pipeline. Key attributes: asset ID, churn probability, top SHAP feature, snapshot date, pipeline run ID.
- **Renewals Snapshot**: A point-in-time record of the customer's renewal profile. Key attributes: account name, product ID, expiring value, ROI, fulfillment metrics, market zone, expiry date.
- **Market Zone**: A geographic classification resolved from `MVIP_ZONE_ID`. Determines the client location label displayed in the worklist.

## Success Criteria

### Measurable Outcomes

- **SC-001**: PMs can identify the 3 highest-risk accounts in the worklist within 5 seconds of page load, without scrolling or clicking.
- **SC-002**: The worklist renders no more than 200 accounts on initial load, ensuring the page remains responsive on standard corporate laptops.
- **SC-003**: All risk indicators (churn probability bar, ROI alert, countdown) are distinguishable at a glance without requiring hover or click interaction.
- **SC-004**: The sticky navigation bar reliably switches between the three dashboard views without page reload or data loss.
- **SC-005**: Zero instances of `-Infinity`, `NaN`, or raw numeric error messages appear in the rendered UI under normal data conditions.

## Assumptions

- The existing dual-mode session infrastructure (`_get_session()`, `@st.cache_resource`) is reused without modification.
- The column `MVIP_ZONE_ID` exists in `MVIP_ASSET_RENEWALS_SNAPSHOTS` and can be resolved to a human-readable market name.
- A prior-snapshot comparison for trend direction is derived from the same asset's historical records in `ASSET_CHURN_HISTORY`.
- The sticky navigation bar replaces the existing Streamlit tab-based view switching with a custom Haven-branded navigation component.
- The churn probability progress bar uses the same color thresholds already established in the design system (70% and 40% boundaries).
- Data sanitization (infinity → NaN → "—") is applied at the application layer after query execution, not in SQL.
