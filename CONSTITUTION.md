> **DEPRECATED**: This file is superseded by the SDD constitution at
> `.specify/memory/constitution.md`. All new changes must go there.

# Project Constitution

This document establishes the binding rules, standards, and guidelines for the development of the **Unity Churn Dashboard**. All contributors, including automated coding agents, must strictly adhere to this constitution.

---

## 1. Project Standards

### 1.1 Language Rule
*   **All code, SQL queries, schema definitions, inline comments, commit messages, and user-facing text inside the dashboard must be written in English.**
*   No Spanish words may exist in any configuration, repository, or database files.

### 1.2 Zero-Trust Security
*   **Never commit or hardcode credentials, private tokens, or passwords to Git.**
*   Local credentials must reside exclusively inside `.streamlit/secrets.toml`, which must be ignored by the version control system.
*   Production runs must rely on Snowflake's native environment variables and Okta SSO integrations.

---

## 2. Directory Structure Conventions

The project must strictly adhere to Realtor's subdirectory monorepo layout. Dumping files at the root of the repository is prohibited.

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
3. Technology Stack and Requirements
Runtime Environment: Python 3.10+
Core UI Framework: Streamlit
Database Connector: snowflake-connector-python
Data Manipulation: pandas
Visualization Engine: plotly (explicitly formatted with brand styling)
Dependency Manager: Conda (environment.yml configuration is required for Snowflake-native deployments)
4. UI/UX and Haven Foundations Design Guidelines
4.1 Color Palette
The Streamlit interface must match Realtor's design tokens:
Primary Accent Red: #D92228 (Must be used for main headers, risk highlights, and key chart categories).
Primary Charcoal: #3F3B36 (Must be used for body text, table text, and standard components).
Warm Gray Light: #F4F3F0 (Must be used for background zones, sidebars, and card backdrops).
4.2 Caching Strategy
To minimize compute cost and ensure rapid response times, database queries must be cached using Streamlit's @st.cache_data decorator.
Queries must be structured with parameter-driven caching so filters do not re-execute redundant warehouse sweeps.
4.3 UI Performance Constraints
Row Limits: Streamlit tables must never render more than 1,000 detail rows at a time. Aggregations, pagination, or strict filters must be used to ensure browser rendering does not crash or degrade performance.
5. Development and Git Workflow
5.1 Branching Strategy
Development must take place on dedicated feature branches (e.g., feature/CAML-1637-unity-churn-dashboard).
Direct merges to main are prohibited. All code must be reviewed via a Pull Request (PR) process.
5.2 Deployment Strategy
Deployments to production must target Snowflake's native Streamlit interface using the "Create from repository" workflow.
Developers must validate local execution using their sandbox database (USER_SANDBOX) and the diagnostic warehouse (SNOWFLAKE_LEARNING_WH) before pushing changes to production repositories.