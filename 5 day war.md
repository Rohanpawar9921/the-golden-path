# BreakCheck AI — Three-Day Push Plan

**Schedule:** Tuesday 10 November to Thursday 12 November 2026

**Timezone:** India Standard Time (IST)
**Deadline:** complete pushes, integration, full-suite run and SME walkthrough by **Thursday 4:00 PM IST**.

This replaces the older Monday–Friday plan. Rohan reported the push status below. I checked that the `clean-main` changes are already included in the fetched `origin/main`; the local `main` branch pointer was stale, so new work must be based on current remote `main`.

## Monday completion

Karthiga reported that she pushed these files on Monday. They are complete; do not ask her to paste or push them again:

- `Project/data_pipeline/audience_cleaning.py`
- `Project/data_pipeline/common_cleaning.py`
- `Project/data_pipeline/dataset_loader.py`
- `Project/data_pipeline/feature_builder.py`
- `Project/data_pipeline/note_cleaning.py`
- `Project/data_pipeline/quality_profiler.py`
- `Project/data_pipeline/submission_cleaning.py`
- `Project/run_data_pipeline.py`
- `Project/tests.py`

Rohan reports that no one else has pushed yet. The four other owners still need their first domain push. Karthiga still owns the model/training files; they were not included in her Monday push.

## File ownership

Each person pushes their own changes. The lists below define ownership; stage only files that actually changed.

| Owner | Files |
|---|---|
| Rohan — API, database, access and integration | `Project/api/`, `Project/persistence/`, `Project/access/`, `Project/run_database_setup.py`, `Project/run_api_service.py`, shared setup/API documentation and this plan |
| Karthiga — data and models | Monday files above are done; remaining `Project/modeling/` and `Project/run_model_training.py` |
| Raghu — knowledge, retrieval and chat grounding | `Project/knowledge/`, `Project/tools/retrieval_tools.py`, `Project/run_knowledge_indexing.py`, `Project/chat/` |
| Ronit — campaign checks and workflow | `Project/tools/campaign_data_tools.py`, `Project/tools/prediction_tools.py`, `Project/tools/schedule_tools.py`, `Project/agentic/` |
| Avinash — dashboard | `Project/dashboard/`, `Project/run_dashboard.py`, `Project/docs/FRONTEND_MANUAL_TESTS.md` |

**Shared-file locks:** Rohan alone edits `Project/api/schemas.py`, `Project/config/config.py`, `Project/requirements.txt` and shared API docs. Raghu owns `Project/tools/retrieval_tools.py`; Ronit may call it but does not edit it. Do not rewrite Karthiga’s pushed `Project/tests.py` or the acceptance contract `pytest/tests.py`. Add focused tests in the relevant owner’s `Project/tests/` files.

Never stage `.env`, databases, model binaries, generated CSVs, the Chroma index, caches, `__pycache__`, or temporary office lock files. Rebuild generated artifacts locally.

## Tuesday 10 November — first domain pushes

**By 11:00 PM IST:** each of the four owners without a push submits a branch/PR containing the ready changes in their domain. If a file is unchanged, leave it out rather than creating a no-op commit.

| Person | Files to push | Evidence in the PR |
|---|---|---|
| Rohan | Changed files in `Project/api/`, `Project/persistence/`, `Project/access/`; `Project/run_database_setup.py` and `Project/run_api_service.py` if changed. Include applicable current changes such as `Project/api/routes.py` and `Project/persistence/models.py`. | Database setup succeeds; service starts; Swagger sign-in and an authenticated queue request work. |
| Raghu | Changed files in `Project/knowledge/`, `Project/tools/retrieval_tools.py`, `Project/run_knowledge_indexing.py` and `Project/chat/`. Include applicable current changes such as `Project/knowledge/vector_index.py` and the three `Project/chat/` modules. | Index reads the supplied documents; a policy reply cites its source; an unrelated question is refused. |
| Ronit | Changed files in `Project/tools/campaign_data_tools.py`, `Project/tools/prediction_tools.py`, `Project/tools/schedule_tools.py` and `Project/agentic/`. | Worked example has deterministic spot results; assessment pauses for a Controller. |
| Avinash | Changed files in `Project/dashboard/` and `Project/run_dashboard.py`; include `Project/tests/test_dashboard_navigation.py`, `test_home_page.py`, `test_clearance_chat_ui.py` and `Project/docs/FRONTEND_MANUAL_TESTS.md` if changed. | Sign-in, queue, detail and clearance chat render from the service. |
| Karthiga | Do not repeat the Monday files. Report remaining model files and any blocker by 11:00 PM; prepare the model push for Wednesday. | Model work is clearly listed for Wednesday. |

At 11:00 PM, Rohan posts the branch/PR name, changed-file list and blocker (if any) for each owner. No one merges a failing change to meet the clock.

## Wednesday 11 November — models and integration

**By 4:00 PM IST:** all domain PRs are reviewable. **By 6:00 PM:** the first integrated build is green.

| Time | Owner | Push / result |
|---|---|---|
| 9:00 AM–12:00 PM | Karthiga | Push changed `Project/modeling/_common.py`, `amendment_model.py`, `exposure_model.py`, `issue_model.py`, `model_evaluation.py`, `model_registry.py`, and `Project/run_model_training.py`. Run data cleaning then training; attach the metrics summary. Do not push generated model files. |
| By 1:00 PM | Rohan | Push API/auth/persistence fixes and focused API tests if needed. Owns changes to schemas/config. |
| By 1:00 PM | Raghu | Push retrieval/chat fixes; own `Project/tests/test_clearance_assistant.py` if changed. |
| By 1:00 PM | Ronit | Push schedule/compliance/workflow fixes and focused workflow tests if needed. |
| By 2:00 PM | Avinash | Push the full dashboard journey: queue, campaign detail, clearance chat, decision queue, audit, sign-in/navigation and role-aware Home page. Keep `Project/docs/FRONTEND_MANUAL_TESTS.md` current. |
| By 2:00 PM | Rohan | Push `Project/HOW_TO_RUN.md`, `Project/API_DOCUMENTATION.md`, `Project/TEST_API_EXAMPLES.md`, `Project/docs/unit_testing.md`, `Project/docs/unit_testing.pdf`, `README.md` and this plan where changed. |
| 2:00–4:00 PM | All owners | Review PRs and fix failures only in owned files. Keep secrets and generated artifacts out. |
| 4:00–6:00 PM | Rohan integrates | Merge one PR at a time in dependency order: Karthiga → Raghu → Ronit → Rohan → Avinash. Run focused checks after each merge; stop and return a failing PR to its owner. |

## Thursday 12 November — final verification and handoff

No new features Thursday. Make only correctness, test or documentation fixes.

| Time | Owner | Must finish |
|---|---|---|
| 9:00–11:00 AM | Karthiga | Re-run cleaning/training after any change; verify report, schemas and model minimums; push fixes only to data/model files. |
| 9:00–11:00 AM | Raghu | Check five distinct code answers, source attribution, follow-up memory and out-of-scope refusal; push retrieval/chat fixes. |
| 9:00–11:00 AM | Ronit | Check broadcast clock, all five breach rules, exposure/queue order, decision gate and restart/resume; push compliance/workflow fixes. |
| 9:00–11:00 AM | Avinash | Smoke-check each role’s navigation and the queue → detail → chat/decision/audit flows; push UI fixes. |
| 9:00–11:00 AM | Rohan | Check sign-in, service-side role checks, API errors, saved assessment/decision and fresh startup; push integration fixes. |
| 11:00 AM–1:00 PM | All owners | Run the full acceptance and regression suite. Fix failures with the file owner and rerun the entire suite. |
| 1:00–2:30 PM | All owners | Follow the manual SME guide at `Project/docs/unit_testing.pdf` with a fresh, unassessed campaign for each decision demo. |
| 2:30–3:30 PM | Rohan | Final merge and clean-start check; confirm all intended pushes are on remote `main` and no secrets or generated files are staged. |
| 3:30–4:00 PM | Team | Demonstrate queue → detail → assessment pending → different Controller decision → documents/audit → role-scoped chat. Close all blockers by 4:00 PM. |

### Full-suite command

Run in PowerShell from `Project`:

```powershell
$env:BREAKCHECK_CHAT_OFFLINE = "1"
python -m pytest ..\pytest\tests.py tests -q
$pytestExitCode = $LASTEXITCODE
Remove-Item Env:BREAKCHECK_CHAT_OFFLINE
exit $pytestExitCode
```

Pass means exit code 0 and no failing tests. Also start the API and dashboard and run the live manual flow; the offline test suite does not replace the smoke test.

## Thursday definition of done

- Karthiga’s Monday data files remain in place, and her remaining model/training changes are pushed.
- Rohan, Raghu, Ronit and Avinash have their own reviewed pushes on `main`.
- The five cleaned datasets, three model metrics and 16-document knowledge index can be reproduced locally.
- The service authenticates users and enforces role access; dashboard facts come through the service.
- Chat answers are category-correct and sourced, and unsupported questions are refused.
- Every spot is checked deterministically; assessments wait for a different Controller; all three decisions and audit records work.
- The full suite passes and the end-to-end SME demo is complete by Thursday 4:00 PM IST.

If an owner misses a checkpoint, they post the exact unpushed files and blocker. Reassign a file only after the owner and Rohan agree, so two people do not push competing edits to it.
