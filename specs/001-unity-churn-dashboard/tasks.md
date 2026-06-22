---

description: "Task list for Unity Churn Dashboard feature implementation"

---

# Tasks: Unity Churn Dashboard

**Input**: Design documents from `specs/001-unity-churn-dashboard/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included based on research.md recommendations (unit tests with pytest + AppTest integration tests).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Streamlit app**: `apps/team_datascience/mvip/unity_churn_dashboard/` (per monorepo layout in constitution)
- **Utils**: `apps/team_datascience/mvip/unity_churn_dashboard/utils/`
- **Tests**: `apps/team_datascience/mvip/unity_churn_dashboard/tests/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, directory structure, and dependency files

- [ ] T001 Create the monorepo directory structure at `apps/team_datascience/mvip/unity_churn_dashboard/` with subdirectories `utils/` and `.streamlit/`
- [ ] T002 [P] Create `apps/team_datascience/mvip/unity_churn_dashboard/environment.yml` with Conda dependencies (Python 3.10, streamlit, snowflake-connector-python, pandas, plotly)
- [ ] T003 [P] Create `apps/team_datascience/mvip/unity_churn_dashboard/snowflake.yml` with Streamlit-in-Snowflake deployment configuration per research.md
- [ ] T004 [P] Create `apps/team_datascience/mvip/unity_churn_dashboard/.streamlit/config.toml` with Haven Foundations theme tokens per research.md
- [ ] T005 Create `apps/team_datascience/mvip/unity_churn_dashboard/utils/__init__.py` to enable Python package imports

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T006 Create `apps/team_datascience/mvip/unity_churn_dashboard/utils/queries.py` with the base Snowflake connection function using `st.cache_data` and secrets
- [ ] T007 [P] Create `apps/team_datascience/mvip/unity_churn_dashboard/utils/plotting.py` with shared Plotly chart helpers (brand-styled template per research.md, chart layout defaults)
- [ ] T008 [P] Create `apps/team_datascience/mvip/unity_churn_dashboard/utils/formatting.py` with shared formatting utilities (metric display, number formatting, date formatting)
- [ ] T009 Create `apps/team_datascience/mvip/unity_churn_dashboard/app.py` with the Streamlit entry point, page config, sidebar layout, and 3-tab structure
- [ ] T010 [P] Create `apps/team_datascience/mvip/unity_churn_dashboard/.streamlit/secrets.toml.example` as a template for local credentials (without real values)

**Checkpoint**: Foundation ready — user story implementation can now begin in parallel

---

## Phase 3: User Story 1 — Executive Summary (Priority: P1) 🎯 MVP

**Goal**: PMs see an aggregated overview with KPI cards (total assets, avg churn prob, high-risk count) and a trend chart of churn risk over expiry months.

**Independent Test**: Load the dashboard URL and verify KPI cards display correct values and a trend chart renders on the Executive Summary tab, without applying any filters.

### Tests for User Story 1

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T011 [P] [US1] Create unit test for KPI calculation functions in `apps/team_datascience/mvip/unity_churn_dashboard/tests/test_metrics.py`
- [ ] T012 [P] [US1] Create integration test for Executive Summary tab rendering in `apps/team_datascience/mvip/unity_churn_dashboard/tests/test_app.py`

### Implementation for User Story 1

- [ ] T013 [US1] Implement the Unity-filtered + deduplicated churn query in `apps/team_datascience/mvip/unity_churn_dashboard/utils/queries.py` using `executive-summary.sql` contract
- [ ] T014 [US1] Implement KPI card rendering (total assets, avg churn prob, high-risk count) in `apps/team_datascience/mvip/unity_churn_dashboard/app.py`
- [ ] T015 [US1] Implement trend chart of average churn probability over expiry months in `apps/team_datascience/mvip/unity_churn_dashboard/app.py`

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

---

## Phase 4: User Story 2 — Model Performance (Priority: P2)

**Goal**: Technical users view historical model metrics (AUC, Precision, Recall) and a static global feature importance summary.

**Independent Test**: Click the Model Performance tab and verify AUC/Precision/Recall values and feature importance rankings are displayed, without needing to apply any filters.

### Tests for User Story 2

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T016 [P] [US2] Create integration test for Model Performance tab rendering in `apps/team_datascience/mvip/unity_churn_dashboard/tests/test_app.py`

### Implementation for User Story 2

- [ ] T017 [US2] Implement the model performance query in `apps/team_datascience/mvip/unity_churn_dashboard/utils/queries.py` using `model-performance.sql` contract (handle empty table gracefully)
- [ ] T018 [P] [US2] Implement the feature importance query (aggregated from predictions) in `apps/team_datascience/mvip/unity_churn_dashboard/utils/queries.py`
- [ ] T019 [US2] Implement Model Performance tab with metrics display and feature importance chart in `apps/team_datascience/mvip/unity_churn_dashboard/app.py`

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

## Phase 5: User Story 3 — Asset Explorer (Priority: P3)

**Goal**: PMs search and filter individual assets using a churn probability slider, product type multiselect, and expiry month picker. Results capped at 1,000 rows.

**Independent Test**: Navigate to the Asset Explorer tab, set a churn probability filter (>0.7), and confirm the table updates to show only matching assets.

### Tests for User Story 3

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

- [ ] T020 [P] [US3] Create integration test for Asset Explorer tab with filter interactions in `apps/team_datascience/mvip/unity_churn_dashboard/tests/test_app.py`

### Implementation for User Story 3

- [ ] T021 [US3] Implement the parameterized asset explorer query in `apps/team_datascience/mvip/unity_churn_dashboard/utils/queries.py` using `asset-explorer.sql` contract with filter parameters
- [ ] T022 [P] [US3] Implement sidebar filter widgets (churn prob slider, product type multiselect, expiry month picker) in `apps/team_datascience/mvip/unity_churn_dashboard/app.py`
- [ ] T023 [US3] Implement the interactive asset table with 1,000-row cap in `apps/team_datascience/mvip/unity_churn_dashboard/app.py`
- [ ] T024 [US3] Wire sidebar filter state to query parameters and table updates in `apps/team_datascience/mvip/unity_churn_dashboard/app.py`

**Checkpoint**: All user stories should now be independently functional

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T025 [P] Document usage instructions in `apps/team_datascience/mvip/unity_churn_dashboard/README.md`
- [ ] T026 Create `apps/team_datascience/mvip/unity_churn_dashboard/tests/__init__.py` and `conftest.py` with shared test fixtures and mock data
- [ ] T027 Code cleanup: verify `@st.cache_data` decorator on all query functions, verify 1,000-row limit enforcement, verify empty state handling for all three tabs
- [ ] T028 Run quickstart.md validation: verify `streamlit run` starts without errors, verify all three tabs render, verify filters work

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Phase 6)**: Depends on all desired user stories being complete

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational — no dependencies on other stories
- **US2 (P2)**: Can start after Foundational — no code dependencies on US1 (reads from different source table)
- **US3 (P3)**: Can start after Foundational — no code dependencies on US1 or US2 (shares base queries but independently testable)

### Within Each User Story

- Tests MUST be written and FAIL before implementation
- Query functions before UI components
- Core implementation before integration
- Story complete before moving to next priority

### Parallel Opportunities

- All Phase 1 tasks marked [P] can run in parallel
- All Phase 2 tasks marked [P] can run in parallel
- All three user stories can start in parallel once Foundational phase completes
- Tests within a story marked [P] can run in parallel
- Query and UI tasks within a story marked [P] can run in parallel

---

## Parallel Example: User Story 1

```bash
# Launch all tests for US1 together:
Task: "Create unit test for KPI calculation functions"
Task: "Create integration test for Executive Summary tab"

# Launch all implementation for US1 together:
Task: "Implement Unity-filtered churn query in queries.py"
Task: "Implement KPI card rendering in app.py"
Task: "Implement trend chart in app.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (KPI cards + trend chart)
4. **STOP and VALIDATE**: Test Executive Summary independently
5. Deploy/demo if ready

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Add User Story 3 → Test independently → Deploy/Demo

### Parallel Team Strategy

With multiple developers:
1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
   - Developer C: User Story 3
3. Stories complete and integrate independently

---

## Notes

- [P] tasks = different files, no dependencies
- Tests use pytest + Streamlit AppTest framework (per research.md)
- Mock Snowflake data for tests using `unittest.mock.patch`
- Each user story independently testable with mocked data
- All queries use `@st.cache_data` for performance
- Database schema: TEAM_DATASCIENCE.MVIP (predictions) + TEAM_DATASCIENCE.PUBLIC (renewals)
