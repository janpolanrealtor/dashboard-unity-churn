---

description: "Implementation task list for Call Worklist View"
---

# Tasks: Call Worklist View

**Input**: Design documents from `specs/002-call-worklist/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are OPTIONAL — only include if explicitly requested.

**Organization**: Tasks are grouped by user story for independent implementation and testing.

## Path Conventions

- App root: `apps/team_datascience/mvip/unity_churn_dashboard/`
- Query functions: `apps/team_datascience/mvip/unity_churn_dashboard/utils/queries.py`
- Formatting functions: `apps/team_datascience/mvip/unity_churn_dashboard/utils/formatting.py`
- Main app: `apps/team_datascience/mvip/unity_churn_dashboard/app.py`

## Phase 1: Foundation — Data & Formatting (Blocks All Stories)

**Purpose**: Core query and formatting functions that MUST be complete before any UI work

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T001 Implement `load_call_worklist()` in `utils/queries.py`
      - SQL with `QUALIFY ROW_NUMBER()`, `DATEDIFF`, `LAG()` for trend
      - `LEFT JOIN` to `FIVETRAN_REFERRAL.PG_PUBLIC.LEAD_ZONE` + `MARKET` for location
      - `COALESCE(m.NAME, 'National (VIP Package)') AS MARKET_NAME`
      - `df.replace([np.inf, -np.inf], np.nan)` after query execution
      - `@st.cache_data(ttl=3600)` decorator
- [x] T002 [P] Add `fmt_renews_in(days)` to `utils/formatting.py`
      - `days < 0` → `"Expired"` span with `color:#726A60`
      - `0 <= days <= 15` → bold red span with `color:#D92228; font-weight:bold`
      - Else → span with `color:#3F3B36`
- [x] T003 [P] Update `app.py` imports to include `load_call_worklist` and `fmt_renews_in`
      - Replace `load_portfolio_accounts()` import with `load_call_worklist()`
      - Add `fmt_renews_in` to formatting import

**Checkpoint**: Foundation ready — user story implementation can begin.

---

## Phase 2: User Story 1 — PM reviews upcoming renewals (Priority: P1) 🎯 MVP

**Goal**: Replace the Portfolio tab table with the call worklist showing account name, location, ACV, churn risk bar, top driver, and renews countdown.

**Independent Test**: Open the dashboard, navigate to Portfolio tab. Verify only Unity Package assets appear, deduplicated, with all 6 worklist columns rendered.

- [x] T004 [US1] Build account column with bold name + gray location text
      - Render `ACCOUNT_NAME` in bold, `MARKET_NAME` below in `<span style="color:#726A60;font-size:11px">`
- [x] T005 [US1] Build ACV column with viability alert
      - `fmt_currency()` on `EXPIRING_VALUE_ACV`
      - If `ROI_PER_LEAD < 0`, append `"below viability"` in red `#D92228`
- [x] T006 [US1] Build churn risk progress bar (custom HTML)
      - 80px gray track `#E9E7E4`, filled bar + circle indicator
      - Color logic: `CHURN_PROB > 0.7` → red `#D92228`; `0.4–0.7` → yellow `#685700` with `#FFF2D0` bg; `< 0.4` → green `#46A758`
- [x] T007 [US1] Build top driver column with trend arrow
      - `MOST_IMPORTANT_FEATURE` text + trend arrow
      - Arrow: `↑` green if improving, `↓` red if worsening, `–` gray if no prior
- [x] T008 [US1] Build renews-in countdown column with `fmt_renews_in()`

**Checkpoint**: At this point, User Story 1 should be fully functional — worklist renders all columns correctly.

---

## Phase 3: User Story 2 — PM identifies urgent accounts (Priority: P2)

**Goal**: Risk signals are visually distinguishable at a glance — red for churn >70%, "below viability" for negative ROI, red countdown for <15 days.

**Independent Test**: Scan the worklist. Verify red progress bars for high-risk, "below viability" labels for negative-ROI accounts, red countdowns for imminent expiry.

**Note**: This story is entirely implemented in Phase 2 tasks (T004–T008) since the risk signals are embedded in the same columns. Validation-only phase.

- [x] T009 [US2] Verify churn risk bar color thresholds match spec
      - Red `#D92228` for CHURN_PROB > 0.70
      - Yellow `#685700` with `#FFF2D0` background for 0.40–0.70
      - Green `#46A758` for < 0.40
- [x] T010 [US2] Verify ACV viability alert triggers on `ROI_PER_LEAD < 0.0`
- [x] T011 [US2] Verify renews countdown color rules
      - `< 0` → `"Expired"` in gray `#726A60`
      - `0–15` → bold red `#D92228`
      - Else → charcoal `#3F3B36`

**Checkpoint**: All risk signals visually correct at a glance.

---

## Phase 4: User Story 3 — PM reviews trends (Priority: P3)

**Goal**: Each row shows a trend direction arrow next to the top churn driver.

**Independent Test**: Assets with improving churn show green `↑`, worsening show red `↓`, first snapshot shows `–`.

- [x] T012 [US3] Implement trend arrow logic in `app.py` table rendering
      - Compare `CHURN_PROB` vs `PREV_CHURN_PROB`
      - Output HTML span with appropriate color class
- [x] T013 [US3] Verify edge cases for trend
      - NULL `PREV_CHURN_PROB` → neutral `–` gray
      - Equal values → neutral `–` gray

**Checkpoint**: All user stories independently functional.

---

## Phase 5: Data Sanitization & Polish

**Purpose**: Cross-cutting concerns affecting all stories

- [x] T014 [P] Verify all numeric columns sanitized: `df.replace([np.inf, -np.inf], np.nan)` in `load_call_worklist()`
- [x] T015 [P] Verify all formatters return `"—"` for NaN/None
- [x] T016 [P] Verify worklist capped at 200 rows
- [x] T017 [P] Run `make lint` and `make format` — fix any issues
- [ ] T018 [P] Run `make dev` — verify app loads without errors
- [x] T019 [P] Commit all changes

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Foundation)**: No dependencies — can start immediately. BLOCKS all stories.
- **Phase 2 (US1 P1)**: Depends on Phase 1 completion
- **Phase 3 (US2 P2)**: Depends on Phase 1 completion (validates Phase 2 output)
- **Phase 4 (US3 P3)**: Depends on Phase 1 + Phase 2 completion
- **Phase 5 (Polish)**: Depends on all stories being complete

### Within Each Phase

- Tasks marked [P] can run in parallel
- Execute in numbered order within each phase

### Parallel Opportunities

- T002 (`fmt_renews_in`) and T003 (imports) can run in parallel with T001 (query)

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Foundation (T001–T003) → **Foundation ready**
2. Complete Phase 2: US1 (T004–T008) → **MVP ready**
3. **STOP and VALIDATE**: Open the dashboard, verify worklist renders correctly
4. Phase 3–5: Add P2/P3 signals and polish

### Incremental Delivery

1. T001 → T002/T003 (parallel) → Foundation ready
2. T004–T008 → Worklist renders (MVP!)
3. T009–T011 → Risk signals validated
4. T012–T013 → Trend arrows added
5. T014–T019 → Polish and final validation
