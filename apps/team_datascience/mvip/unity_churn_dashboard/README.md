# Unity Churn Dashboard

Streamlit dashboard for Unity Package asset churn predictions, deployed on Snowflake-native Streamlit (SiS) and runnable locally.

**Production**: https://app.snowflake.com/FJLKZOB/nca06910/#/streamlit-apps/TEAM_DATASCIENCE.MVIP.UNITY_CHURN_DASHBOARD

---

## Jira Ticket

| Field | Value |
|-------|-------|
| **Ticket** | [CAML-1637](https://moveinc.atlassian.net/browse/CAML-1637) |
| **Title** | Unity Churn Dashboard: Design and Development |
| **Project** | TL-Client Analytics and ML (CAML) |
| **Sprint** | Client ML — FY26.Q4.S25 (ends 2026-07-01) |
| **Status** | In Progress |
| **Assignee** | Jan Polanco |
| **Reporter** | Maanit Mehra |
| **Story Points** | 5 |

### User Story

> As a product manager, when I analyze asset performance, I want to see a Unity Asset Dashboard so that I can understand churn probabilities.

### Acceptance Criteria

- A Unity Asset Dashboard is created in Streamlit.
- The dashboard highlights asset model performance.
- The dashboard displays churn probabilities (aggregate and individual).

### Related CAML Work (Jan Polanco)

| Ticket | Summary | Status |
|--------|---------|--------|
| [CAML-1272](https://moveinc.atlassian.net/browse/CAML-1272) | Review existing MVIP Asset Churn Documentation | In Progress |
| [CAML-46](https://moveinc.atlassian.net/browse/CAML-46) | Additional Features for Unity Churn Model | In Progress |
| [CAML-1216](https://moveinc.atlassian.net/browse/CAML-1216) | Retrain the Unity Churn Model | Pending Approval |
| [CAML-1400](https://moveinc.atlassian.net/browse/CAML-1400) | Review existing C+ Asset Churn Documentation | Pending Approval |
| [CAML-1271](https://moveinc.atlassian.net/browse/CAML-1271) | Bug Fix: ChurnBaselineMVIP Flow | Accepted ✓ |
| [CAML-43](https://moveinc.atlassian.net/browse/CAML-43) | Unity Churn Dashboard: Investigate Data Issues | Accepted ✓ |

---

## Tabs

| Tab | What it shows |
|-----|---------------|
| **Portfolio** | KPI strip (total assets, avg churn prob, high-risk count, expiring ACV), signals/alerts box, filterable/sortable asset table with risk pills, drill-down panel for individual asset churn trend + distribution |
| **Pipeline History** | Pipeline run metrics, churn trend over time, raw data expander |
| **Insights** | Feature importance bar chart, churn probability distribution, driver breakdown table |

---

## Local Development

### Prerequisites

- Python 3.10+, `uv`
- Snowflake Okta SSO credentials

### Setup

```bash
cd apps/team_datascience/mvip/unity_churn_dashboard
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edit secrets with your Snowflake account / user / warehouse
```

### Run

```bash
uv run streamlit run app.py
```

Or from repo root: `make run`

---

## Deployment

**Every code change must do both steps — neither alone is enough.**

### 1. Deploy to Snowflake

```bash
cd apps/team_datascience/mvip/unity_churn_dashboard
snow streamlit deploy --replace --connection realtor
```

The `realtor` connection must be configured in `~/.config/snowflake/config.toml` with `authenticator = externalbrowser`.

### 2. Commit and push to the repository

```bash
git add apps/team_datascience/mvip/unity_churn_dashboard/
git commit -m "your message"
git push
```

The git repository (`janpolanrealtor/dashboard-unity-churn`) is the source of truth. Snowflake holds the running copy. If you deploy without committing, the production app and the repo diverge — the next deploy from a fresh clone will overwrite your changes.

---

## Architecture

- **Session**: Dual-mode — `snowflake.snowpark.context.get_active_session()` on SiS, falls back to `snowflake.connector` with `externalbrowser` auth locally
- **Queries**: 5 cached functions in `utils/queries.py` with `@st.cache_data(ttl=3600)`
- **Charts**: 5 Plotly functions in `utils/plotting.py` using Haven design tokens
- **Formatting**: `utils/formatting.py` — currency, probability, percentage, tenure formatters
- **Styling**: Custom CSS via `st.markdown` — Haven Foundations design tokens, Inter font, risk pills, sticky header

---

## RDC Data Science Conventions

Patterns from the RDC data science skill that apply to this project:

### Snowflake Query Guidelines

- **Always use LIMIT** when exploring large tables — queries cost ~$0.37/credit.
- **Filter early**: push `WHERE PRODUCT2ID = '01t5f000006sGgOAAU'` and `QUALIFY ROW_NUMBER()` into CTEs, not outer queries.
- **Warehouse**: use `SNOWFLAKE_LEARNING_WH` locally; SiS manages its own compute.
- **Pre-aggregated first**: for KPIs and trend metrics, aggregate in SQL rather than pulling raw rows into pandas.
- **Column names are UPPERCASE**: Snowflake returns all column names in UPPERCASE via both Snowpark and `snowflake.connector` — always use `df["CHURN_PROB"]`, never `df["churn_prob"]`.

### ML Pipeline Context (Metaflow / OMEK)

The churn probabilities shown in this dashboard are produced by the `ChurnBaselineMVIP` Metaflow flow, run on OMEK. Key facts:

- Flow run history is available at `https://omek.move.com/console/runs/ChurnBaselineMVIP/`
- Model artifacts are stored at `s3://opcity-ds-models/{ModelName}/{version}/`
- Pipeline run stats are approximated from `ASSET_CHURN_HISTORY` grouped by `CHURN_FLOW_ID + SNAPSHOT_DATE` (no separate performance table exists).
- The `CHURN_FLOW_ID` column is the Metaflow run identifier — use it to correlate dashboard snapshots with specific pipeline runs.

### Table Selection Tiers

| Tier | Table / Source | Use for |
|------|---------------|---------|
| 1 | `TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY` | Raw model predictions, per-asset churn scores |
| 2 | `TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS` | Asset metadata, ACV, tenure, fulfillment |
| 3 | Derived in Python | `PRODUCT_NAME` mapping, risk tier classification |

### Deduplication Pattern (always apply)

```sql
QUALIFY ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE DESC) = 1
```

Apply this in every CTE that reads from either source table — both tables have multiple snapshots per asset.

---

## Notes

- Column names from Snowflake are **UPPERCASE** in pandas DataFrames
- Unity assets are filtered via `PRODUCT2ID = '01t5f000006sGgOAAU'` in the renewals join
- The app uses custom HTML tables (not `st.dataframe`) for the Portfolio tab to render risk pills
- All Plotly charts have transparent backgrounds (SiS renders on white cards)
- `PRODUCT_NAME` does not exist in Snowflake — derived from `PRODUCT2ID` via a Python dict in `queries.py`
- `UNITY_CHURN_MODEL_PERFORMANCE` table does not exist — pipeline stats are derived from `ASSET_CHURN_HISTORY`
- `_get_session()` is decorated with `@st.cache_resource` — Okta SSO auth fires once per local dev session, not once per query
- Queries use cursor-based fetching (`cursor.execute` → `fetchall`), not `pd.read_sql` — the latter triggers a pandas deprecation warning with raw connectors
- `st.plotly_chart` uses `width="stretch"` (not the deprecated `use_container_width=True`)
