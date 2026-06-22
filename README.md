# Unity Churn Dashboard

Streamlit dashboard for visualizing Unity Package asset churn predictions sourced from `TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY` on Snowflake.

**Production URL**: https://app.snowflake.com/FJLKZOB/nca06910/#/streamlit-apps/TEAM_DATASCIENCE.MVIP.UNITY_CHURN_DASHBOARD

---

## Overview

This dashboard surfaces machine-learning churn probabilities for Unity Package assets, enabling data-driven renewal interventions. It connects to Snowflake via a dual-mode session (Snowpark on SiS, `snowflake.connector` locally), caches query results with `st.cache_data`, and renders interactive Plotly charts styled with Realtor's Haven Foundations design system.

---

## Tech Stack

| Component              | Choice                          |
| :--------------------- | :------------------------------ |
| Runtime                | Python 3.10+                    |
| UI Framework           | Streamlit                       |
| Session Mode (SiS)     | Snowpark (`get_active_session`) |
| Session Mode (Local)   | `snowflake.connector` + Okta SSO|
| Data Manipulation      | pandas                          |
| Visualization          | Plotly (Haven-branded)          |
| Package Manager        | `uv`                            |
| Linter/Formatter       | Ruff                            |
| Pre-commit             | pre-commit                      |

---

## Dashboard Layout

| Tab                | Content                                                                 |
| :----------------- | :---------------------------------------------------------------------- |
| **Portfolio**      | KPI strip (total assets, avg churn, high-risk count, expiring ACV), signals box, filterable/sortable asset table with risk pills, drill-down panel for individual asset trend + distribution |
| **Pipeline History** | Pipeline run metrics, trend chart of avg/median churn over time, raw data expander |
| **Insights**       | Feature importance bar chart, churn probability distribution, driver breakdown table |

---

## Directory Structure

```text
apps/team_datascience/mvip/unity_churn_dashboard/
├── app.py                  # Streamlit entry point (493 lines, Haven CSS)
├── environment.yml         # Conda env for Snowflake deployment
├── snowflake.yml           # Snowflake CLI deployment config
├── CONSTITUTION.md         # Project constitution (authoritative)
├── .streamlit/
│   ├── config.toml         # Theme settings (Haven Foundations)
│   └── secrets.toml        # Local credentials (git-ignored)
├── utils/
│   ├── __init__.py
│   ├── queries.py          # Dual-mode session + 5 cached SQL queries
│   ├── plotting.py         # 5 Plotly chart builders (Haven tokens)
│   └── formatting.py       # fmt_currency, fmt_probability, etc.
└── tests/                  # Test directory (pytest, optional)
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- Snowflake credentials with access to `TEAM_DATASCIENCE.MVIP` and `TEAM_DATASCIENCE.PUBLIC`

### 2. Clone and install

```bash
git clone <repo-url>
cd dashboard_unity_churn
make install    # or: uv sync
```

### 3. Configure local credentials

Create `.streamlit/secrets.toml` inside the app directory:

```toml
[snowflake]
account = "FJLKZOB.nca06910"
user = "your.email@realtor.com"
warehouse = "SNOWFLAKE_LEARNING_WH"
authenticator = "externalbrowser"
```

> **Security:** This file is git-ignored. Never commit credentials. Production uses Snowflake's native auth via `get_active_session()`.

### 4. Run the dashboard

```bash
make run       # or: uv run streamlit run apps/team_datascience/mvip/unity_churn_dashboard/app.py
```

For auto-reload on save:

```bash
make dev       # --server.runOnSave true
```

---

## Database Architecture

### Schema

```
TEAM_DATASCIENCE.MVIP       — ML prediction tables
TEAM_DATASCIENCE.PUBLIC     — Renewal snapshot tables
```

### Source Tables

**`TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY`** — Raw model predictions

| Column                   | Description                                |
| :----------------------- | :----------------------------------------- |
| `ASSET_ID`               | Unique asset identifier                    |
| `CHURN_PROB`             | Estimated churn probability                |
| `MOST_IMPORTANT_FEATURE` | Primary driver feature                     |
| `EXPIRY_DATE`            | Contract end date                          |
| `MONTH_OF_EXPIRY`        | Normalised start-of-month of expiry        |
| `SNAPSHOT_DATE`          | Prediction generation timestamp            |
| `CHURN_FLOW_ID`          | Metaflow run identifier                    |

**`TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS`** — Asset metadata

| Column                  | Description                               |
| :---------------------- | :---------------------------------------- |
| `ID`                    | Asset ID (joins to ASSET_CHURN_HISTORY)   |
| `PRODUCT2ID`            | Product identifier (Unity = `01t5f000006sGgOAAU`) |
| `ACCOUNTID`             | Owning account                            |
| `EXPIRING_VALUE_ACV`    | Contract value in USD                     |
| `TENURE`                | Customer tenure in months                 |
| `IS_FULFILLED`          | Fulfillment status                        |

### Unity Asset Filtering

Join with renewals and filter by `PRODUCT2ID`:

```sql
WHERE r.PRODUCT2ID = '01t5f000006sGgOAAU'  -- Unity Package
```

### Deduplication

Always retrieve the latest prediction per asset:

```sql
QUALIFY ROW_NUMBER() OVER (PARTITION BY a.ASSET_ID ORDER BY a.SNAPSHOT_DATE DESC) = 1
```

---

## UI/UX Guidelines

### Color Palette (Haven Foundations)

| Token      | Hex       | Usage                                      |
| :--------- | :-------- | :----------------------------------------- |
| Accent Red | `#D92228` | Main headers, risk highlights, chart categories |
| Charcoal   | `#3F3B36` | Body text, table text, standard components |
| Warm Gray  | `#F4F3F0` | Background zones, sidebars, card backdrops |

### Risk Pills

Churn probability is displayed as color-coded pills:

- **High** (>70%): Red background — `pill-high`
- **Medium** (40-70%): Yellow background — `pill-medium`
- **Low** (<40%): Green background — `pill-low`

### Caching

- All query functions decorated with `@st.cache_data(ttl=3600)`.
- Cache invalidated hourly — sufficient for a daily-batch ML pipeline.

### Row Limits

- Portfolio table capped at **200 rows** in UI (topped from query).
- Asset Explorer capped at **1,000 rows** at query level.

---

## Development Workflow

```bash
make lint       # Ruff linting
make format     # Ruff formatting
make pre-commit # Run pre-commit hooks
make test       # Pytest (if tests exist)
```

## Deployment

```bash
cd apps/team_datascience/mvip/unity_churn_dashboard
snow streamlit deploy --replace --connection realtor
```

Uses the Okta SSO connection `realtor` configured in `~/.config/snowflake/config.toml`.

---

## Security

- **Zero-trust principle:** Never commit or hardcode credentials.
- Local secrets in `.streamlit/secrets.toml` (git-ignored).
- Production auth via Snowflake Snowpark `get_active_session()` — no secrets file needed.
- Local auth via Okta `externalbrowser` — no password stored in config.

---

## References

- [Specification](specs/001-unity-churn-dashboard/spec.md)
- [Plan & Research](specs/001-unity-churn-dashboard/plan.md)
- [Data Model](specs/001-unity-churn-dashboard/data-model.md)
- [Constitution](apps/team_datascience/mvip/unity_churn_dashboard/CONSTITUTION.md) (authoritative)
