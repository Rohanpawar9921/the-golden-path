# BreakCheck AI — One-Day Push Plan

**Push day:** Tuesday, 10 November 2026 (IST)

**Goal:** every remaining owner pushes their assigned, ready work today; Rohan integrates it to `main` and the team records any remaining blocker before the day ends.

This replaces the previous Tuesday–Thursday schedule. The project is already on `main`; today's work is to push remaining owner changes and integrate them. Put each change in its matching repository path. Do not paste source code into this plan or overwrite another owner's files.

## Already pushed on Monday

Karthiga reported these files as pushed. They are complete; do not copy or push them again unless an actual fix is needed:

- `Project/data_pipeline/audience_cleaning.py`
- `Project/data_pipeline/common_cleaning.py`
- `Project/data_pipeline/dataset_loader.py`
- `Project/data_pipeline/feature_builder.py`
- `Project/data_pipeline/note_cleaning.py`
- `Project/data_pipeline/quality_profiler.py`
- `Project/data_pipeline/submission_cleaning.py`
- `Project/run_data_pipeline.py`
- `Project/tests.py`

## Today's file assignments

Use the paths exactly as written. If a listed file has no change, leave it alone; do not make a duplicate or empty commit. For a new focused test, create it at the path shown and keep the acceptance suite at `pytest/tests.py` unchanged.

### Karthiga — data pipeline and models

**Paste/update and push today:**

- `Project/modeling/_common.py`
- `Project/modeling/amendment_model.py`
- `Project/modeling/exposure_model.py`
- `Project/modeling/issue_model.py`
- `Project/modeling/model_evaluation.py`
- `Project/modeling/model_registry.py`
- `Project/run_model_training.py`
- `Project/docs/Know_Your_Data.md` if the current schema or cleaning behavior needs documenting
- `Project/tests/test_modeling.py` if adding focused model tests; create this file if needed

**Data files Karthiga owns:**

- `Project/data/campaign_submissions_train.csv`
- `Project/data/campaign_submissions_eval.csv`
- `Project/data/clearance_notes.csv`
- `Project/data/programme_audiences_train.csv`
- `Project/data/programme_audiences_eval.csv`

Only include a CSV if its source data actually changed. Do not regenerate or commit cleaned output, quality-report output, caches, or trained model binaries. The nine Monday files above are already done.

**Before handing off:** verify the pipeline can read the five source datasets and training reports the three model metrics and schemas.

### Raghu — policy knowledge, retrieval, and assistant

**Paste/update and push today:**

- `Project/knowledge/chunk_splitting.py`
- `Project/knowledge/code_reading.py`
- `Project/knowledge/pdf_extraction.py`
- `Project/knowledge/vector_index.py`
- `Project/tools/retrieval_tools.py`
- `Project/run_knowledge_indexing.py`
- `Project/chat/campaign_status_answer.py`
- `Project/chat/clearance_assistant.py`
- `Project/chat/conversation_memory.py`
- `Project/tests/test_clearance_assistant.py`

**Policy source files Raghu maintains:**

- `Project/data/docs/Advertising-Clearance-Policy.pdf`
- `Project/data/docs/Code-Alcohol.pdf`
- `Project/data/docs/Code-Betting-And-Gaming.pdf`
- `Project/data/docs/Code-Consumer-Credit.pdf`
- `Project/data/docs/Code-Less-Healthy-Food.pdf`
- `Project/data/docs/Code-Medicines-And-Health.pdf`
- `Project/data/docs/Guide-Alcohol-And-Social-Success.pdf`
- `Project/data/docs/Guide-Appeal-To-Under-18s.pdf`
- `Project/data/docs/Guide-Comparative-Claims.pdf`
- `Project/data/docs/Guide-Environmental-Claims.pdf`
- `Project/data/docs/Guide-Financial-Promotions.pdf`
- `Project/data/docs/Guide-Gambling-Inducements.pdf`
- `Project/data/docs/Guide-Health-Claims.pdf`
- `Project/data/docs/Guide-Price-And-Offer-Claims.pdf`
- `Project/data/docs/Past-Clearances-Casebook.pdf`
- `Project/data/docs/Scheduling-And-Audience-Rules.pdf`

The PDFs are already in the repository. Include them only if the source documents themselves changed; never push a generated vector index. Check that different policy questions retrieve relevant sources, answers cite those sources, and unrelated questions are declined.

### Ronit — campaign checks, scheduling, and workflow

**Paste/update and push today:**

- `Project/tools/campaign_data_tools.py`
- `Project/tools/prediction_tools.py`
- `Project/tools/schedule_tools.py`
- `Project/agentic/agents.py`
- `Project/agentic/graph.py`
- `Project/agentic/nodes.py`
- `Project/agentic/state.py`
- `Project/tests/test_campaign_workflow.py` if adding focused workflow tests; create this file if needed

**Campaign and schedule input files Ronit owns:**

- `Project/data/input/booked_spots.csv`
- `Project/data/input/open_campaign_notes.csv`
- `Project/data/input/open_campaigns.csv`
- `Project/data/input/programme_schedule.csv`

Only include a CSV if its source data actually changed. Check that schedule and breach-rule results are repeatable, a clearance assessment pauses for a different Controller, and the allowed decisions are recorded correctly.

### Rohan — API, persistence, access, setup, and integration

**Paste/update and push today:**

- `Project/api/routes.py`
- `Project/api/schemas.py`
- `Project/persistence/database.py`
- `Project/persistence/models.py`
- `Project/persistence/repository.py`
- `Project/access/password_security.py`
- `Project/access/permissions.py`
- `Project/config/config.py`
- `Project/.env.example` (names and safe sample values only; never real credentials)
- `Project/requirements.txt`
- `Project/run_database_setup.py`
- `Project/run_api_service.py`
- `Project/tests/test_api_integration.py` if adding focused API tests; create this file if needed
- `Project/API_DOCUMENTATION.md`
- `Project/TEST_API_EXAMPLES.md`
- `Project/HOW_TO_RUN.md`
- `Project/docs/unit_testing.md`
- `Project/docs/unit_testing.pdf`
- `README.md`
- `PROJECT_UNDERSTANDING_AND_PLAN.md` if it needs to reflect the completed implementation
- `5 day war.md` (this plan)
- `.github/workflows/build.yml` and `sonar-project.properties` only if today's integration requires changes

Rohan integrates owner pushes in dependency order, resolves cross-module issues with the file owner, and confirms each commit reaches `main`. Do not edit or replace the acceptance contract `pytest/tests.py`. `a.py` is a workspace source-download utility, not part of the clearance application; leave it unchanged unless the team has a specific requirement for it.

### Avinash — dashboard and manual UI guide

**Paste/update and push today:**

- `Project/dashboard/__init__.py`
- `Project/dashboard/api_client.py`
- `Project/dashboard/assessment_page.py`
- `Project/dashboard/audit_trail.py`
- `Project/dashboard/campaign_detail.py`
- `Project/dashboard/clearance_chat.py`
- `Project/dashboard/clearance_queue.py`
- `Project/dashboard/decision_queue.py`
- `Project/dashboard/home.py`
- `Project/dashboard/queue_page.py`
- `Project/dashboard/ui.py`
- `Project/run_dashboard.py`
- `Project/tests/test_clearance_chat_ui.py`
- `Project/tests/test_dashboard_navigation.py`
- `Project/tests/test_home_page.py`
- `Project/docs/FRONTEND_MANUAL_TESTS.md`
- `Project/.streamlit/config.toml` only if a dashboard configuration change is needed

Check role-aware Home, sign-in, queue, campaign detail, clearance chat, decision queue, and audit navigation against the running API. Report the page and action for any failure.

## Files the team must not copy or stage

- `.env` files containing real credentials, passwords, or tokens
- Generated model binaries, cleaned CSV outputs, quality reports, vector indexes, caches, `__pycache__`, and `.pyc` files
- Temporary office lock files such as `~$Monday_SME_Baseline_Review.pptx`
- `pytest/tests.py` acceptance tests: read and run them, but do not edit the contract
- The Monday data-pipeline files listed above, unless fixing a real defect

The reference brief `BreakCheck_AI.pdf`, existing handoff PDFs and review slides remain reference material; do not re-create them as code files.

## Push and integration sequence for today

1. Each owner works only in their assigned files and pushes their branch as soon as it is ready. Include a changed-file list and a one-line result/blocker.
2. Rohan integrates one owner at a time in this order: **Karthiga → Raghu → Ronit → Rohan/API → Avinash/UI**. Resolve conflicts with the owner of the conflicting file.
3. After integration, run the project acceptance and focused test suites, then start the API and dashboard for a short live smoke check. If something fails, report the exact failing test or UI step and the file owner; do not claim it passed.
4. Before the day ends, Rohan confirms the intended commits are on remote `main`, and the team posts any remaining blocker with exact filenames.

Run from the `Project` directory in PowerShell:

```powershell
$env:BREAKCHECK_CHAT_OFFLINE = "1"
python -m pytest ..\pytest\tests.py tests -q
$pytestExitCode = $LASTEXITCODE
Remove-Item Env:BREAKCHECK_CHAT_OFFLINE
exit $pytestExitCode
```

An exit code of `0` with no failing tests is a pass. The live check must also confirm API sign-in, a role-scoped queue request, opening a campaign detail, a grounded assistant answer, and the clearance decision flow.
