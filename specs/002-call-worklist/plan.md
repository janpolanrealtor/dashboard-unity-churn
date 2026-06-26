# Implementation Plan: Call Worklist View

**Branch**: `002-call-worklist` | **Date**: 2026-06-26 | **Spec**: specs/002-call-worklist/spec.md
**Input**: Feature specification from `specs/002-call-worklist/spec.md`

## Summary

Replace the current Portfolio tab table with a refined "Call Worklist" table purpose-built for Product Manager renewal triage. The worklist adds account location resolution (via `FIVETRAN_REFERRAL` schema), a churn risk progress bar, ACV profitability alerts, trend indicators, and a color-coded renews-in countdown. Navigation remains `st.tabs` with existing Haven CSS styling.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: streamlit, pandas, plotly, snowflake-connector-python, numpy
**Storage**: Snowflake (`TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY` + `TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS` + `FIVETRAN_REFERRAL.PG_PUBLIC.LEAD_ZONE` + `FIVETRAN_REFERRAL.PG_PUBLIC.MARKET`)
**Testing**: pytest (suite at `apps/team_datascience/mvip/unity_churn_dashboard/tests/`)
**Target Platform**: Snowflake Streamlit in Snowflake (SiS) + local dev via Okta SSO
**Project Type**: Streamlit dashboard (single-page app with multi-tab layout)
**Performance Goals**: Worklist renders ≤200 rows; page load <5s for KPI + table
**Constraints**: Dual-mode (SiS snowpark + local connector); no `snowflake-connector-python` in `environment.yml`; UPPERCASE column names; `@st.cache_data(ttl=3600)` on all queries
**Scale/Scope**: ~1,000–5,000 Unity Package assets; single user (PM) per session

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Rule | Status | Notes |
|---|---|---|
| §2.1 Language (English) | ✅ | All code/comments/commits in English |
| §2.2 Zero-Trust Security | ✅ | No credentials in code; uses `_get_session()` |
| §2.3 UPPERCASE columns | ✅ | All pandas refs use uppercase strings |
| §4 Dual-Mode Architecture | ✅ | Reuses `_get_session()` / `@st.cache_resource` |
| §6.4 Unity filter | ✅ | `PRODUCT2ID = '01t5f000006sGgOAAU'` in every query |
| §6.5 Dedup pattern | ✅ | `QUALIFY ROW_NUMBER() OVER (PARTITION BY ASSET_ID ORDER BY SNAPSHOT_DATE DESC) = 1` |
| §6.6 JOIN alias rules | ✅ | Ambiguous columns aliased (`a.SNAPSHOT_DATE AS PREDICTION_DATE`) |
| §6.9 Data sanitization | ✅ | `df.replace([np.inf, -np.inf], np.nan)` after every query |
| §10 Caching | ✅ | `@st.cache_data(ttl=3600)` on all query functions |
| §7 Haven design tokens | ✅ | Colors match token spec: `#D92228`, `#685700`, `#46A758`, etc. |

**No violations.** All constitutional requirements are met by this feature.

## Project Structure

### Documentation (this feature)

```text
specs/002-call-worklist/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
dashboard_unity_churn/
├── apps/
│   └── team_datascience/
│       └── mvip/
│           └── unity_churn_dashboard/
│               ├── app.py                     # Updated: Tab 1 worklist table
│               ├── utils/
│               │   ├── queries.py             # +load_call_worklist()
│               │   ├── formatting.py          # +fmt_renews_in()
│               │   └── plotting.py            # Unchanged
│               └── tests/
│                   └── test_worklist.py       # New (if tests requested)
```

**Structure Decision**: The existing app structure is preserved. Changes are additive (new function in `queries.py`, new formatter in `formatting.py`, modified Portfolio tab block in `app.py`). No new files at repo root.

## Complexity Tracking

> **No violations found in Constitution Check** — table left empty intentionally.
