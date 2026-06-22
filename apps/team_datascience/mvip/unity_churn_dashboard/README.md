# Unity Churn Dashboard

Streamlit dashboard for Unity Package asset churn predictions, deployed on Snowflake-native Streamlit (SiS) and runnable locally.

**Production**: https://app.snowflake.com/FJLKZOB/nca06910/#/streamlit-apps/TEAM_DATASCIENCE.MVIP.UNITY_CHURN_DASHBOARD

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

```bash
cd apps/team_datascience/mvip/unity_churn_dashboard
snow streamlit deploy --replace --connection realtor
```

The `realtor` connection must be configured in `~/.config/snowflake/config.toml` with `authenticator = externalbrowser`.

---

## Architecture

- **Session**: Dual-mode — `snowflake.snowpark.context.get_active_session()` on SiS, falls back to `snowflake.connector` with `externalbrowser` auth locally
- **Queries**: 5 cached functions in `utils/queries.py` with `@st.cache_data(ttl=3600)`
- **Charts**: 5 Plotly functions in `utils/plotting.py` using Haven design tokens
- **Formatting**: `utils/formatting.py` — currency, probability, percentage, tenure formatters
- **Styling**: Custom CSS via `st.markdown` — Haven Foundations design tokens, Inter font, risk pills, sticky header

---

## Notes

- Column names from Snowflake are **UPPERCASE** in pandas DataFrames
- Unity assets are filtered via `PRODUCT2ID = '01t5f000006sGgOAAU'` in the renewals join
- The app uses `custom` HTML tables (not `st.dataframe`) for the Portfolio tab to render risk pills
- All Plotly charts have transparent backgrounds (SiS renders on white cards)
