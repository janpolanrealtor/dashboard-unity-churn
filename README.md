# Unity Churn Dashboard

Streamlit dashboard for visualizing Unity Package asset churn predictions sourced from `TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY` on Snowflake.

---

## Overview

This dashboard surfaces machine-learning churn probabilities for Unity Package assets, enabling data-driven renewal interventions. It connects directly to Snowflake, caches query results, and renders interactive Plotly charts styled with Realtor's Haven Foundations design tokens.

---

## Tech Stack

| Component              | Choice                    |
| :--------------------- | :------------------------ |
| Runtime                | Python 3.10+              |
| UI Framework           | Streamlit                 |
| Database Connector     | snowflake-connector-python |
| Data Manipulation      | pandas                    |
| Visualization          | Plotly (brand-styled)     |
| Dependency Manager     | Conda (environment.yml)   |

---

## Directory Structure

```text
MoveRDC/omek-apps/
└── apps/
    └── team_datascience/
        └── mvip/
            └── unity_churn_dashboard/
                ├── app.py                  # Streamlit entry point
                ├── environment.yml         # Anaconda environment requirements
                ├── snowflake.yml           # Snowflake CLI deployment configuration
                ├── .streamlit/
                │   └── config.toml         # Theme settings (Haven Foundations)
                ├── utils/                  # Helper functions (plotting, formatting)
                └── README.md               # App-level user guide
```

---

## Getting Started

### 1. Clone the repository

```bash
git clone <repo-url>
cd unity_churn_dashboard
```

### 2. Configure credentials

Create `.streamlit/secrets.toml` with your Snowflake connection details:

```toml
[connections.snowflake]
account = "..."
user = "..."
password = "..."
role = "PRODUCER_DATASCIENCE_ROLE"
warehouse = "SNOWFLAKE_LEARNING_WH"
database = "TEAM_DATASCIENCE"
schema = "MVIP"
```

> **Security:** This file is git-ignored. Never commit credentials. Production runs rely on Snowflake environment variables and Okta SSO.

### 3. Create the Conda environment

```bash
conda env create -f environment.yml
conda activate unity_churn_dashboard
```

### 4. Run the dashboard

```bash
streamlit run app.py
```

---

## Database Architecture

### Schema

The initial assumption of a `TEAM_DATASCIENCE.UNITY` schema was incorrect. The active machine-learning schema is:

```
TEAM_DATASCIENCE.MVIP
```

### Source Table

Raw model predictions live in:

```
TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY
```

| Column                   | Type      | Description                                |
| :----------------------- | :-------- | :----------------------------------------- |
| `ASSET_ID`               | VARCHAR   | Unique asset identifier                    |
| `PREV_START_DATE`        | TIMESTAMP | Current contract start date                |
| `EXPIRY_DATE`            | TIMESTAMP | Current contract end date                  |
| `MONTH_OF_EXPIRY`        | TIMESTAMP | Normalised start-of-month of expiry        |
| `CHURN_PROB`             | FLOAT     | Estimated churn probability                |
| `MOST_IMPORTANT_FEATURE` | VARCHAR   | Primary driver feature behind prediction   |
| `CHURN_FLOW_ID`          | VARCHAR   | Metaflow run identifier                    |
| `SNAPSHOT_DATE`          | TIMESTAMP | Prediction generation timestamp            |

### Unity vs. Legacy Filtering

The table holds predictions for both **MVIP Legacy** and **Unity Package** assets. To isolate Unity assets, join with the renewals snapshot table:

```sql
SELECT a.*
FROM TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY a
INNER JOIN TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS r
    ON a.ASSET_ID = r.ASSET_ID
WHERE r.PRODUCT2ID = '01t5f000006sGgOAAU'  -- Unity Package
```

### Deduplication

Always retrieve the latest prediction per asset:

```sql
ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY snapshot_date DESC) = 1
```

---

## UI/UX Guidelines

### Color Palette (Haven Foundations)

| Token      | Hex       | Usage                                      |
| :--------- | :-------- | :----------------------------------------- |
| Accent Red | `#D92228` | Main headers, risk highlights, chart categories |
| Charcoal   | `#3F3B36` | Body text, table text, standard components |
| Warm Gray  | `#F4F3F0` | Background zones, sidebars, card backdrops |

### Caching

- Decorate database queries with `@st.cache_data` to minimise compute cost.
- Use parameter-driven caching so filter changes do not re-execute redundant warehouse sweeps.

### Row Limits

Streamlit tables must never render more than **1,000 detail rows** at a time. Always push aggregations and sorting down to Snowflake.

---

## Development Workflow

1. Create a feature branch from `main`:
   ```
   feature/CAML-1637-unity-churn-dashboard
   ```
2. Develop and validate locally using `USER_SANDBOX` and `SNOWFLAKE_LEARNING_WH`.
3. Open a Pull Request — direct merges to `main` are prohibited.
4. Deploy to Snowflake's native Streamlit using the **"Create from repository"** workflow.

---

## Risks and Mitigations

| Risk                                  | Impact | Mitigation                                                            |
| :------------------------------------ | :----- | :-------------------------------------------------------------------- |
| Incorrect asset classification        | High   | Always filter by `PRODUCT2ID` via the renewals snapshot join.         |
| Duplicate rows in UI                  | Medium | Use `ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY snapshot_date DESC) = 1`. |
| Slow Streamlit UI load times          | High   | Push aggregations to Snowflake; enforce 1,000-row limit.              |

---

## Security

- **Zero-trust principle:** Never commit or hardcode credentials, tokens, or passwords.
- Local secrets reside exclusively in `.streamlit/secrets.toml` (git-ignored).
- Production authentication uses Snowflake native environment variables and Okta SSO.
