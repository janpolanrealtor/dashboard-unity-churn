# Quickstart: Unity Churn Dashboard

**Prerequisites**: Snowflake access with `PRODUCER_DATASCIENCE_ROLE`

---

## 1. Local Setup

### 1.1 Create Conda environment

```bash
conda env create -f apps/team_datascience/mvip/unity_churn_dashboard/environment.yml
conda activate unity_churn_dashboard
```

### 1.2 Configure Snowflake credentials

Create `.streamlit/secrets.toml`:

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

> **Security**: This file is git-ignored. Never commit it.

### 1.3 Run the dashboard

```bash
streamlit run apps/team_datascience/mvip/unity_churn_dashboard/app.py
```

---

## 2. Running Tests

```bash
pytest tests/ -v
```

Unit tests do not require a Snowflake connection. Integration tests use mocked data.

---

## 3. Deployment (Snowflake CLI)

```bash
# Deploy to SiS
snow streamlit deploy \
  --project-dir apps/team_datascience/mvip/unity_churn_dashboard/ \
  --replace
```

### Required `snowflake.yml`

```yaml
definition_version: 2
entities:
  unity_churn_dashboard:
    type: streamlit
    identifier: unity_churn_dashboard
    query_warehouse: SNOWFLAKE_LEARNING_WH
    main_file: app.py
    artifacts:
      - environment.yml
      - app.py
      - utils/
      - .streamlit/config.toml
```

---

## 4. Architecture Overview

```text
Snowflake Layer
  ├── TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY  (raw predictions)
  └── TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS  (product metadata)
       └── INNER JOIN on ASSET_ID → Unity-filtered view (PRODUCT2ID = '01t5f000006sGgOAAU')

Dashboard Layer (Streamlit)
  ├── Tab 1: Executive Summary (KPI cards + trend chart)
  ├── Tab 2: Model Performance (AUC/Precision/Recall + feature importance)
  └── Tab 3: Asset Explorer (interactive table with sidebar filters)

Design Tokens (Haven Foundations)
  ├── Accent Red   #D92228  → headers, highlights, chart categories
  ├── Charcoal     #3F3B36  → body text, tables
  └── Warm Gray    #F4F3F0  → backgrounds, sidebar, cards
```
