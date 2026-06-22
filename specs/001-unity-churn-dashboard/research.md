# Research: Unity Churn Dashboard

**Date**: 2026-06-22  
**Feature**: [spec.md](spec.md)  
**Status**: Complete — all unknowns resolved

---

## 1. Testing Strategy

### Decision: Layered Testing (Unit + AppTest + Manual Smoke)

Adopt a three-layer approach tailored for SiS-deployed apps:

| Layer | Tool | Scope |
|---|---|---|
| **Unit** | `pytest` | Pure functions: data transformations, metric calculations, query logic extracted from `app.py` |
| **Integration** | Streamlit `AppTest` + `unittest.mock` | Widget interaction, session state, mocked Snowflake queries, chart presence |
| **Smoke** | Manual + `pytest` pre-deploy | App boots without exceptions, filters don't crash |

### Rationale
- Unit tests are fast (<10ms) and need no Snowflake connection.
- `AppTest.from_file()` runs headlessly — exercises real Streamlit rendering without a browser.
- Mocking at the `load_dashboard_data()` boundary is the cleanest approach; no need to mock Snowflake internals.
- Chart assertions: test existence (`len(at.get("plotly_chart")) > 0`) and extract figure specs via `.proto` for deeper validation if needed.

### Key Patterns
```python
from streamlit.testing.v1 import AppTest
@patch("app.load_dashboard_data", return_value=mock_df)
def test_kpi_card_values(mock_load):
    at = AppTest.from_file("app.py")
    at.run()
    assert at.metric[0].value == "1848"
    assert not at.exception
```

### Alternatives Considered
- **Playwright E2E**: Too heavy for CI now; revisit for visual regression later.
- **Live Snowflake in tests**: Requires credentials in CI, costly, non-deterministic.
- **No testing**: Current status quo — not acceptable for production.

### Next Steps
1. Create `tests/` directory.
2. Extract SQL + data transformations into `utils/` modules.
3. Add `pytest` and `pytest-mock` to `pyproject.toml`.
4. Write unit tests for extracted logic.

---

## 2. Snowflake SiS Deployment

### Decision: Snowflake CLI (Push-Based) for Production

The recommended deployment strategy uses Snowflake CLI (`snow streamlit deploy`) with CI/CD.

### Rationale
- Can deploy Streamlit + auxiliary objects (roles, tables, grants) in a single pipeline.
- Works with private Git forges (no public-internet requirement).
- Local development parity: `snow streamlit deploy` from dev machine.
- More control: `--replace`, `--prune`, environment variable overrides.

### Warehouse Runtime (Default)
- Dependency file: `environment.yml` (Conda, Anaconda channel only).
- No `pip` support — all deps must be in Snowflake's Anaconda channel.
- Available Python: 3.9, 3.10, 3.11.

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

### Alternatives Considered
- **"Create from Repository" (pull-based)**: Simpler but requires publicly reachable Git forge, no auxiliary object deployment.
- **Snowsight editor**: No version control, rejected for production.
- **Container runtime (SPCS)**: Full flexibility but higher cost and ops overhead. Use only if warehouse runtime limits are hit.

---

## 3. Proposed `UNITY_CHURN_MODEL_PERFORMANCE` Table

### Decision: Create as specified in SDD v1

The table will live in `TEAM_DATASCIENCE.PUBLIC` (same schema as `MVIP_ASSET_RENEWALS_SNAPSHOTS`).

```sql
CREATE TABLE IF NOT EXISTS TEAM_DATASCIENCE.PUBLIC.UNITY_CHURN_MODEL_PERFORMANCE (
    churn_flow_id VARCHAR,
    snapshot_date TIMESTAMP_NTZ,
    auc_score FLOAT,
    accuracy FLOAT,
    precision_score FLOAT,
    recall_score FLOAT,
    created_at TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

### Ownership
- Table creation and maintenance is a **pipeline-side responsibility** (data engineering).
- Dashboard reads from this table — it does not write.
- If the table doesn't exist yet, Tab 2 shows a "no data available" message.

### Rationale
- Historical model metrics (AUC, accuracy, precision, recall) are currently only on Metaflow cards.
- No existing Snowflake table persists these metrics.
- This lightweight logging table fills the gap for Tab 2 (Model Performance).

---

## 4. Streamlit Theme & Haven Foundations

### Decision: Existing `config.toml` is correct

The current `.streamlit/config.toml` already maps the brand tokens correctly:

| Theme Token | Brand Token | Hex | Usage |
|---|---|---|---|
| `primaryColor` | Accent Red | `#D92228` | Buttons, sliders, active states, metric highlights |
| `backgroundColor` | White | `#FFFFFF` | Main page background |
| `secondaryBackgroundColor` | Warm Gray | `#F4F3F0` | Sidebar, widget backgrounds, cards |
| `textColor` | Charcoal | `#3F3B36` | Body text, table text |
| `font` | sans serif | `"sans serif"` | System sans-serif stack |

### Plotly Chart Theming

Recommended approach — create a global template:

```python
import plotly.io as pio
import plotly.graph_objects as go

pio.templates["haven"] = go.layout.Template(
    layout=dict(
        font=dict(family="sans serif", color="#3F3B36"),
        title=dict(font=dict(color="#D92228", size=18)),
        colorway=["#D92228", "#3F3B36", "#F4F3F0", "#8B4513", "#A9A9A9"],
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#E0DDD8", zerolinecolor="#E0DDD8"),
        yaxis=dict(gridcolor="#E0DDD8", zerolinecolor="#E0DDD8"),
    )
)
pio.templates.default = "haven"
```

### Rationale
- Transparent backgrounds let Streamlit's theme show through.
- Accent Red for primary series, Charcoal for secondary/reference, Warm Gray variant `#E0DDD8` for grid lines.
- All colors pass WCAG AA contrast requirements.
