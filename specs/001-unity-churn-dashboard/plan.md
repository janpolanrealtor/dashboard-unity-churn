# Implementation Plan: Unity Churn Dashboard

**Branch**: `001-unity-churn-dashboard` | **Date**: 2026-06-22 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-unity-churn-dashboard/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a 3-tab Streamlit dashboard that surfaces Unity Package asset churn predictions from Snowflake (`TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY`), enriched via a federated join with `MVIP_ASSET_RENEWALS_SNAPSHOTS` to isolate Unity assets by `PRODUCT2ID`. The dashboard delivers an executive KPI summary (P1), model performance metrics (P2), and an interactive asset explorer (P3), all styled with Realtor's Haven Foundations design tokens.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: Streamlit 1.58+, snowflake-connector-python 4.6+, pandas 2.3+, plotly 6.8+  
**Storage**: Snowflake — `TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY` (predictions), `TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS` (renewals), proposed `TEAM_DATASCIENCE.PUBLIC.UNITY_CHURN_MODEL_PERFORMANCE` (metrics)  
**Testing**: NEEDS CLARIFICATION — Streamlit UI validation approach (manual testing, no established Streamlit testing framework in project)  
**Target Platform**: Snowflake-native Streamlit (SiS) + local development via `streamlit run app.py`  
**Project Type**: Streamlit dashboard application  
**Performance Goals**: Page load < 3s, filter response < 2s, table cap at 1,000 rows  
**Constraints**: Snowflake warehouse costs, 3 concurrent users expected, no hardcoding of credentials  
**Scale/Scope**: ~1,848 unique Unity assets, 3 dashboard tabs, 3 user stories (P1→P2→P3)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Rule | Status |
|---|---|---|
| Language Rule | All code, SQL, docs, UI text in English. No Spanish. | ✅ Pass — spec written in English |
| Zero-Trust Security | No credentials in git. Secrets in `.streamlit/secrets.toml`. | ✅ Pass — documented in assumptions |
| Tech Stack Compliance | Python 3.10+, Streamlit, snowflake-connector-python, pandas, plotly, Conda | ✅ Pass — all declared in `pyproject.toml` |
| UI/UX Standards | Haven Foundations colors (#D92228, #3F3B36, #F4F3F0), `@st.cache_data`, 1,000 row limit | ✅ Pass — specified in requirements |
| Dev Workflow | Feature branch, PR required, local validation with USER_SANDBOX | ✅ Pass — on `001-unity-churn-dashboard` branch |
| Database Standards | Schema MVIP, filter by PRODUCT2ID join, deduplicate with ROW_NUMBER() | ✅ Pass — specified in entity contracts |
| Quality Gates | Monorepo directory layout, PR review, complexity tracking | ✅ Pass — follows constitution layout |

**No violations found.** Complexity Tracking not required.

## Project Structure

### Documentation (this feature)

```text
specs/001-unity-churn-dashboard/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
├── checklists/
│   └── requirements.md  # Spec quality checklist
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

Per constitution §Quality Gates, the project adheres to Realtor's monorepo layout. The structure mirrors `MoveRDC/omek-apps/apps/team_datascience/mvip/unity_churn_dashboard/`:

```text
apps/team_datascience/mvip/unity_churn_dashboard/
├── app.py                  # Streamlit entry point
├── environment.yml         # Conda env for Snowflake deployment
├── snowflake.yml           # Snowflake CLI deployment config
├── .streamlit/
│   ├── config.toml         # Theme settings (Haven Foundations)
│   └── secrets.toml        # Local credentials (git-ignored)
├── utils/
│   ├── __init__.py
│   ├── queries.py          # SQL query functions
│   ├── plotting.py         # Plotly chart builders
│   └── formatting.py       # Data formatting helpers
└── README.md               # User guide
```

**Structure Decision**: Monorepo subdirectory per Realtor conventions. Single Streamlit app with a `utils/` module for separation of concerns (queries, plotting, formatting). No separate test directory since Streamlit UI testing is not established — manual validation is the current approach.

## Complexity Tracking

> *Not required — all constitution checks pass with zero violations.*

## Research Items (Phase 0)

The following unknowns require research before Phase 1 design:

1. **Testing approach**: No established Streamlit testing framework in the project. Research options: Streamlit AppTest, manual testing, or custom validation scripts.
2. **Snowflake SiS deployment**: Confirm Streamlit-in-Snowflake deployment workflow and environment.yml compatibility with Snowflake's native runtime.
3. **UNITY_CHURN_MODEL_PERFORMANCE table**: Finalize schema design and ownership (dashboard vs. pipeline responsibility for table creation).
4. **Haven Foundations Streamlit theme**: Confirm `config.toml` theme settings for Realtor's design tokens (primaryColor, backgroundColor, etc.).
