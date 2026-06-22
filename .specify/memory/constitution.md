<!--
  Sync Impact Report

  Version change: (template) → 1.0.0
  Bump rationale: First concrete fill of template placeholders — no prior version.
  Modified principles: N/A (initial fill)
  Added sections:
    - Core Principles (×5): Language Rule, Zero-Trust Security, Technology Stack
      Compliance, UI/UX Design Standards (Haven Foundations), Development & Git Workflow
    - Database Architecture & Data Standards
    - Quality Gates & Constraints
    - Governance
  Removed sections: N/A
  Templates requiring updates:
    - .specify/templates/plan-template.md   ✅ already aligned (has Constitution Check)
    - .specify/templates/spec-template.md   ✅ already aligned
    - .specify/templates/tasks-template.md   ✅ already aligned
    - .specify/templates/commands/*.md       ✅ no files (empty dir)
    - README.md                              ✅ already updated
  Follow-up TODOs:
    - RATIFICATION_DATE: needs manual entry
-->

# Unity Churn Dashboard Constitution

## Core Principles

### I. Language Rule

All code, SQL queries, schema definitions, inline comments, commit
messages, and user-facing text inside the dashboard MUST be written in
English. No Spanish words may exist in any configuration, repository, or
database files.

Rationale: Ensures team-wide readability and consistent documentation
across Realtor's multilingual organization.

### II. Zero-Trust Security

Never commit or hardcode credentials, private tokens, or passwords to
Git. Local credentials MUST reside exclusively inside
`.streamlit/secrets.toml`, which MUST be ignored by the version control
system. Production runs MUST rely on Snowflake's native environment
variables and Okta SSO integrations.

### III. Technology Stack Compliance

The project MUST adhere to the following stack:
- **Runtime**: Python 3.10+
- **UI Framework**: Streamlit
- **Database Connector**: snowflake-connector-python
- **Data Manipulation**: pandas
- **Visualization**: Plotly (explicitly formatted with Realtor brand
  styling)
- **Dependency Manager**: Conda via `environment.yml`

All dependencies MUST be declared in both `pyproject.toml` and
`environment.yml`. The Conda environment is required for Snowflake-native
deployments.

### IV. UI/UX Design Standards (Haven Foundations)

The Streamlit interface MUST match Realtor's design tokens:

| Token      | Hex       | Usage                                     |
| :--------- | :-------- | :---------------------------------------- |
| Accent Red | `#D92228` | Main headers, risk highlights, chart categories |
| Charcoal   | `#3F3B36` | Body text, table text, standard components |
| Warm Gray  | `#F4F3F0` | Background zones, sidebars, card backdrops |

Caching: Database queries MUST be cached using Streamlit's
`@st.cache_data` decorator with parameter-driven keys so filters do not
re-execute redundant warehouse sweeps.

Row Limits: Streamlit tables MUST NOT render more than 1,000 detail
rows at a time. Aggregations, pagination, or strict filters MUST be used
to ensure browser performance.

### V. Development & Git Workflow

Development MUST take place on dedicated feature branches following the
pattern `feature/CAML-###-descriptive-name`. Direct merges to `main` are
PROHIBITED — all code MUST be reviewed via Pull Request.

Local validation MUST use the `USER_SANDBOX` database and the
`SNOWFLAKE_LEARNING_WH` warehouse before pushing changes.

Production deployments MUST target Snowflake's native Streamlit
interface using the "Create from repository" workflow.

---

## Database Architecture & Data Standards

The active machine-learning schema is `TEAM_DATASCIENCE.MVIP` (the
initial assumption of a `TEAM_DATASCIENCE.UNITY` schema is incorrect).
The master prediction table is
`TEAM_DATASCIENCE.MVIP.ASSET_CHURN_HISTORY`.

### Unity vs. Legacy Asset Filtering

The raw prediction table contains predictions for both MVIP Legacy and
Unity Package assets but does not persist the `PRODUCT2ID` column.
Unity Package assets (`01t5f000006sGgOAAU`) MUST be isolated via an
`INNER JOIN` with
`TEAM_DATASCIENCE.PUBLIC.MVIP_ASSET_RENEWALS_SNAPSHOTS`.

### Deduplication

All queries MUST use `ROW_NUMBER() OVER (PARTITION BY asset_id ORDER BY
snapshot_date DESC) = 1` to isolate only the latest prediction per
asset.

### Performance

All aggregations MUST be pushed down to the Snowflake engine. Loading
large raw datasets into Streamlit memory is PROHIBITED.

---

## Quality Gates & Constraints

### Directory Structure

The project MUST adhere to Realtor's subdirectory monorepo layout.
Dumping files at the root of the repository is PROHIBITED.

```text
MoveRDC/omek-apps/
└── apps/
    └── team_datascience/
        └── mvip/
            └── unity_churn_dashboard/
                ├── app.py                  # Streamlit entry point
                ├── environment.yml         # Anaconda environment
                ├── snowflake.yml           # Snowflake CLI config
                ├── .streamlit/
                │   └── config.toml         # Theme settings
                ├── utils/                  # Helper functions
                └── README.md               # User guide
```

### PR Review Gate

Every PR MUST verify compliance with this constitution before merge.

### Complexity Tracking

When a constitution check produces violations, the plan's Complexity
Tracking table MUST document: (1) the violated principle, (2) why the
violation is necessary, and (3) why a simpler alternative was rejected.

---

## Governance

This constitution supersedes all other ad-hoc practices. Amendments:

- MUST be documented via a Pull Request with a clear rationale.
- MUST increment the version per semantic versioning rules:
  - **MAJOR**: Backward-incompatible governance or principle removals.
  - **MINOR**: New principle or materially expanded guidance.
  - **PATCH**: Clarifications, wording, typo fixes.
- MUST update all dependent templates if principles are added, removed,
  or renamed.

All PR reviews MUST verify compliance with this constitution.
Justification of complexity is required whenever a principle is
overridden.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): No original adoption date found — enter manually | **Last Amended**: 2026-06-22
