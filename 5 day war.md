# The Five-Day War of House Atreides

## Mission

By **Friday afternoon**, House Atreides will demonstrate BreakCheck AI end to
end: clean data, predictive models, policy-grounded checks, deterministic spot
compliance, human approval, REST APIs, and a Streamlit dashboard.

The project brief is [`BreakCheck_AI.pdf`](BreakCheck_AI.pdf). The acceptance
contract is [`pytest/tests.py`](pytest/tests.py). The existing implementation
map is [`PROJECT_UNDERSTANDING_AND_PLAN.md`](PROJECT_UNDERSTANDING_AND_PLAN.md).

> **The crysknife rule:** no new feature is allowed to break the full pytest
> suite. Every PR must include a focused test or a reproducible demo command.

## Starting Point: The Sietch Already Exists

This is not a greenfield setup week. The repository already contains the
project structure, source modules, raw CSV files, supplied PDFs, tests,
configuration, entry points, and the current implementation baseline.

Before anyone writes code, they must inspect the existing files on their branch:

```powershell
cd "D:\Downloads\workspace-source-20261109-102912\workspace"
git checkout main
git pull origin main
git checkout <your-branch>
git rebase main
```

Then read only the files belonging to the assigned domain and run the current
baseline:

```powershell
cd Project
python -m pytest ..\pytest\tests.py -q
```

Do **not** recreate folders, copy the PDF into `Project\data\docs\`, duplicate
CSV files, rebuild already-working modules from scratch, or create parallel
versions of existing entry points. Add a new file only when the existing
architecture genuinely has no suitable home for the required feature.

## The Five Houses

| Person | Dune title | Ownership | Main directories |
|---|---|---|---|
| Rohan Atreides | Duke and integration lead | API, database, authentication, releases | `api/`, `persistence/`, `access/` |
| Kartiga | Data and ML developer | Cleaning, features, model training | `Project\data_pipeline\`, `Project\modeling\` |
| Raghu | Knowledge and policy developer | PDFs, retrieval, code reading | `Project\knowledge\`, retrieval tools |
| Ronit | Compliance and workflow developer | Scheduling, spot checks, workflow facts | `Project\tools\`, `Project\agentic\` |
| Avinash | Streamlit frontend developer | Streamlit UI and demo experience | `Project\dashboard\` |

## Git Rules That Prevent Bloodshed

Create one branch per person:

```text
feat/atreides-rohan-api
feat/atreides-chani-data-models
feat/atreides-duncan-knowledge
feat/atreides-gurney-compliance
feat/atreides-irulan-streamlit
```

Rules:

1. Never work directly on `main`.
2. Never commit `.env`, databases, `output/`, `processed/`, caches, or
   `__pycache__/`.
3. Do not edit another person's ownership directory.
4. Do not change `config/config.py`, shared schemas, or `requirements.txt`
   without first announcing it in the team channel.
5. One PR equals one domain and one demonstrable result.
6. Rebase before work:

   ```powershell
   git checkout main
   git pull origin main
   git checkout <your-branch>
   git rebase main
   ```

7. Rohan merges only after the focused test and full-suite result are attached.

### File ownership lock

Two people must never edit the same file on the same day.

| Owner | Directly owned files |
|---|---|
| Rohan | `api/`, `persistence/`, `access/`, `run_api_service.py`, `run_database_setup.py` |
| Kartiga | `Project\data_pipeline\`, `Project\modeling\`, `Project\run_data_pipeline.py`, `Project\run_model_training.py` |
| Raghu | `Project\knowledge\`, `Project\tools\retrieval_tools.py`, `Project\run_knowledge_indexing.py` |
| Ronit | `Project\tools\campaign_data_tools.py`, `Project\tools\schedule_tools.py`, `Project\tools\prediction_tools.py`, `Project\agentic\` |
| Avinash | `Project\dashboard\`, `Project\run_dashboard.py` |

These shared files are locked and may only be changed by Rohan after a proposed
interface is approved:

```text
Project/config/config.py
Project/requirements.txt
Project/api/schemas.py
Project/5 day war.md
Project/HOW_TO_RUN.md
Project/API_DOCUMENTATION.md
Project/TEST_API_EXAMPLES.md
```

If a shared change is needed, describe the exact requested lines in the PR;
Rohan applies the smallest patch on the integration branch. Do not copy an
entire incoming file during conflict resolution.

### Daily merge gate

Merge one PR at a time in this order:

```text
Kartiga -> Raghu -> Ronit -> Rohan -> Avinash
```

After every merge:

```powershell
python -m pytest ..\pytest\tests.py -q
```

If the suite fails, stop merging and return that PR to its owner. This prevents
one broken branch from contaminating the remaining branches.

## What Already Exists in This Repository

The supplied project is already populated. Treat these as existing assets to
understand, test, extend, or repair:

- `BreakCheck_AI.pdf`: authoritative problem statement and domain rules.
- `Project/data/`: supplied raw CSV files, live queue inputs, and policy PDFs.
- `pytest/tests.py`: acceptance contract.
- `Project/config/config.py`: canonical paths, names, thresholds, roles, and
  workflow constants.
- `Project/data_pipeline/`: cleaning, feature construction, and profiling.
- `Project/modeling/`: model training, evaluation, schemas, and registry.
- `Project/knowledge/`: PDF extraction, chunking, indexing, and code reading.
- `Project/tools/`: campaign, schedule, retrieval, and prediction tools.
- `Project/agentic/`: workflow state, nodes, agents, and checkpoint logic.
- `Project/persistence/`, `Project/access/`, and `Project/api/`: database,
  authentication, permissions, and REST service.
- `Project/dashboard/`: Streamlit page modules that need completion and polish.
- `Project/API_DOCUMENTATION.md` and `Project/TEST_API_EXAMPLES.md`: API demo
  contracts.

The team is starting from this baseline. Monday and Tuesday work means
understanding, validating, and improving these existing files—not pretending
that the repository is empty.

## Direct File Map: What to Open and Paste Each Day

The paths below are relative to the repository root:

```text
D:\Downloads\workspace-source-20261109-102912\workspace\
```

If you are working from inside `Project`, remove the `Project\` prefix. Do not
paste Kartiga's code into Raghu's files, and do not paste code into a Markdown
file unless the task specifically asks for documentation.

| Day | Person | Open these exact files today | Paste or implement here | Visible result |
|---|---|---|---|---|
| Monday | Rohan | `PROJECT_UNDERSTANDING_AND_PLAN.md`, `Project\config\config.py`, `pytest\tests.py` | Notes and ownership decisions belong in the PR description; do not alter the test or config just for planning | baseline and ownership map |
| Monday | Kartiga | `Project\data_pipeline\*.py`, `Project\modeling\*.py`, `Project\run_data_pipeline.py`, `Project\run_model_training.py` | Data/model observations go in the PR description; code fixes go only in `data_pipeline\` or `modeling\` | data/model gap list |
| Monday | Raghu | `BreakCheck_AI.pdf`, `Project\data\docs\`, `Project\knowledge\*.py`, `Project\tools\retrieval_tools.py` | Retrieval observations go in the PR description; code fixes go only in `knowledge\` or `retrieval_tools.py` | source-document map |
| Monday | Ronit | `Project\tools\campaign_data_tools.py`, `Project\tools\schedule_tools.py`, `Project\tools\prediction_tools.py`, `Project\agentic\*.py` | Compliance observations go in the PR description; code fixes go only in `tools\` or `agentic\` | compliance gap list |
| Monday | Avinash | `Project\dashboard\*.py`, `Project\API_DOCUMENTATION.md`, `Project\TEST_API_EXAMPLES.md` | UI observations go in the PR description; do not change backend files | dashboard gap list |
| Tuesday | Rohan | `Project\api\routes.py`, `Project\api\schemas.py`, `Project\persistence\*.py`, `Project\access\*.py` | Paste API/auth fixes only into these owned files | authenticated Swagger flow |
| Tuesday | Kartiga | `Project\data_pipeline\*.py`, `Project\modeling\*.py`, `Project\run_data_pipeline.py`, `Project\run_model_training.py` | Paste cleaning/model fixes only into these owned files | cleaned files, report, metrics |
| Tuesday | Raghu | `Project\knowledge\*.py`, `Project\tools\retrieval_tools.py`, `Project\run_knowledge_indexing.py` | Paste extraction/retrieval fixes only into these owned files | source-linked retrieval |
| Tuesday | Ronit | `Project\tools\*.py`, `Project\agentic\*.py` | Paste deterministic compliance/workflow fixes only into these owned files | breach result and workflow state |
| Tuesday | Avinash | `Project\dashboard\*.py` | Paste only UI planning scaffolding or safe UI changes; use API docs for endpoint order | UI gap board and API journey |
| Wednesday | Rohan | `Project\api\`, `Project\persistence\`, `Project\access\` | Integration fixes only in the API/backend ownership area | stable API contract |
| Wednesday | Kartiga | `Project\modeling\`, `Project\run_model_training.py` | Paste reproducibility and display-data fixes | risk cards have trusted values |
| Wednesday | Raghu | `Project\knowledge\`, `Project\tools\retrieval_tools.py`, chat retrieval modules | Paste source-attribution and retrieval fixes | chat answer with source |
| Wednesday | Ronit | `Project\agentic\`, `Project\tools\` | Paste workflow and outcome integration fixes | decision path demo |
| Wednesday | Avinash | `Project\dashboard\api_client.py`, `Project\dashboard\clearance_queue.py`, `Project\dashboard\campaign_detail.py` | Paste the first Streamlit pages here | live queue and campaign detail |
| Thursday | Rohan | `Project\api\`, `Project\persistence\`, `Project\access\` | Paste final auth, audit, and decision fixes | role-safe end-to-end API |
| Thursday | Kartiga | `Project\modeling\`, `Project\data_pipeline\` | Paste final edge-case or artifact fixes | model values agree with tests |
| Thursday | Raghu | `Project\chat\`, `Project\knowledge\`, retrieval tools | Paste chat memory, refusal, and source-display fixes | grounded chat demo |
| Thursday | Ronit | `Project\agentic\`, `Project\tools\` | Paste checkpoint and decision-route fixes | CLEAR/RESTRICT/REJECT demo |
| Thursday | Avinash | `Project\dashboard\*.py`, `Project\run_dashboard.py` | Paste decision queue, audit, chat, and role-page UI | complete Streamlit journey |

### Daily copy/paste rule

1. Open the exact file path in the table.
2. Copy only the relevant function or component into that file.
3. Do not replace the entire file unless the PR explicitly owns that file.
4. Run the focused test.
5. Commit only files listed for that day.
6. Put the command output and changed-file list in the PR.

# Monday — Day 1: Mapping the Existing Sietch

**Status: complete.**

Monday is not a file-creation day. It is the day for understanding the supplied
repository: read `BreakCheck_AI.pdf`, inspect the existing modules, read the
pytest contract, map the current behavior, and assign ownership without
duplicating anything.

## Monday ownership and visible result

| Person | Work completed | Demonstrable result |
|---|---|---|
| Rohan | read existing API, persistence, access, and entry points | baseline report and ownership map |
| Kartiga | read existing cleaning/model modules and their outputs | data/model gap list |
| Raghu | read supplied PDFs and existing knowledge modules | retrieval/code-reading gap list |
| Ronit | read existing tools and workflow modules | compliance/workflow gap list |
| Avinash | read existing dashboard modules and API docs | UI gap list and demo route |

### Monday show-and-tell checklist

| Person | Show this exact visible evidence |
|---|---|
| Rohan | current pytest result, API route map, and ownership map |
| Kartiga | an existing cleaned CSV/report and one raw-to-cleaned comparison |
| Raghu | one supplied PDF passage returned by the existing knowledge layer |
| Ronit | an existing `01:10 -> 25:10` conversion or breach-result example |
| Avinash | existing dashboard page inventory connected to API endpoints |

## Monday files to read, demonstrate, or extend

### Rohan — project map

**File:** repository root `PROJECT_UNDERSTANDING_AND_PLAN.md`

**Read/reference:** the project understanding, test contract, implementation
phases, and validation strategy. Do not create a duplicate plan.

**What it does:** gives the team one source of truth for scope, dependencies,
acceptance tests, and constraints.

```text
Acceptance contract: pytest/tests.py
Configuration source: Project/config/config.py
Raw inputs: Project/data/
Application code: Project/
Validation command: python -m pytest ..\pytest\tests.py -q
```

### Kartiga — existing data preparation

**Files:** `Project/data_pipeline/`,
`Project/run_data_pipeline.py`

**Read and run:**

```text
The data pipeline reads raw CSV files as text, repairs configured defects,
normalizes values, removes unusable records, builds features, and writes five
cleaned extracts plus output/data_quality_report.json.
```

**What it does:** protects raw inputs while producing deterministic data for
models and live campaign tools.

### Raghu — existing document map

**Files:** `Project/data/docs/`, `Project/knowledge/`

**Read and demonstrate:**

```text
The knowledge layer extracts the sixteen PDFs, splits them into sections and
chunks, stores source-document metadata, and retrieves passages without mixing
category codes or exposing the excluded casebook to chat.
```

**What it does:** makes every policy answer traceable to a supplied document.

### Ronit — existing compliance map

**Files:** `Project/tools/schedule_tools.py`,
`Project/tools/campaign_data_tools.py`

**Read and demonstrate:**

```text
Every spot is converted to the broadcast clock and checked in this order:
WINDOW, INDEX, CHILDREN, FREQUENCY, SEPARATION.
No language model decides whether a spot breaches a rule.
```

**What it does:** keeps safety-critical clearance facts deterministic.

### Avinash — existing dashboard map

**Files:** `Project/dashboard/`, `Project/API_DOCUMENTATION.md`

**Read and demonstrate:**

```text
The dashboard must call the REST API for campaign facts. It must not read raw
CSV files, PDFs, databases, or implement business rules directly.
```

**What it does:** preserves a clean frontend/backend boundary.

# Tuesday — Day 2: Testing the Foundations

**Status: complete.**

Tuesday is for validating the existing implementation and making only focused
repairs. The data, PDF, model, tools, API, workflow, and persistence foundations
already exist. The UI is intentionally not treated as complete; it moves to
Wednesday and Thursday.

## Tuesday ownership and demo

| Person | Completed work | Files | Tuesday demo |
|---|---|---|---|
| Rohan | test and repair existing API/database/auth behavior | `api/`, `persistence/`, `access/` | sign in, authorize Swagger, inspect queue |
| Kartiga | verify and repair existing cleaning/model behavior | `data_pipeline/`, `modeling/` | existing cleaned files, report, and metrics |
| Raghu | verify and repair existing extraction/retrieval behavior | `knowledge/`, `tools/retrieval_tools.py` | existing search returns source text |
| Ronit | verify and repair existing compliance/workflow behavior | `tools/`, `agentic/` | existing spot result and decision state |
| Avinash | inspect existing dashboard modules and map missing screens | `dashboard/`, API docs | existing page inventory and UI gap board |

### Tuesday show-and-tell checklist

| Person | Show this exact visible evidence |
|---|---|
| Rohan | current test result for the API area plus Swagger sign-in and queue |
| Kartiga | existing `processed\` files, quality report, and model metrics |
| Raghu | existing retrieval result containing passage text and source document |
| Ronit | existing campaign profile, schedule row, breach result, and workflow status |
| Avinash | existing dashboard files, missing-page list, and ordered API journey |

Tuesday's deliverable is a verified baseline and gap list. Nobody should create
duplicate data, PDF, model, API, or dashboard folders.

## Tuesday verification commands

These commands inspect and validate the files already in the repository. They
are not instructions to recreate the project structure. Run only the command
that belongs to the assigned owner and commit only source/test changes.

### Rohan — start the API

**Paste/run from:** `Project\`

```powershell
python run_database_setup.py
python -m uvicorn api.routes:service_application --host 127.0.0.1 --port 8000
```

**Files used:** `run_database_setup.py`, `persistence/database.py`,
`persistence/repository.py`, `api/routes.py`.

**What they do:** create the local schema, seed users and campaigns, then expose
authentication, queue, assessment, decision, audit, and chat endpoints.

**Proof:** open `http://127.0.0.1:8000/docs`, sign in, and use the Swagger
Authorize button with the returned `X-Session-Token`.

### Kartiga — verify existing cleaned data

**Paste/run from:** `Project\`

```powershell
python run_data_pipeline.py
Get-ChildItem processed
Get-Content output\data_quality_report.json
```

**Files used:** `run_data_pipeline.py`, `data_pipeline/dataset_loader.py`,
`data_pipeline/common_cleaning.py`, `data_pipeline/submission_cleaning.py`,
`data_pipeline/audience_cleaning.py`, `data_pipeline/note_cleaning.py`,
`data_pipeline/quality_profiler.py`.

**What they do:** confirm that the existing pipeline can reproduce the cleaned
outputs and quality evidence from the supplied raw files.

**Proof:** five cleaned CSVs appear under `processed\` and the quality report
appears under `output\`.

### Kartiga — verify existing model artifacts

**Paste/run from:** `Project\`

```powershell
python run_model_training.py
Get-ChildItem output\models
Get-Content output\model_metrics.json
```

**Files used:** `run_model_training.py`, `modeling/_common.py`,
`modeling/amendment_model.py`, `modeling/exposure_model.py`,
`modeling/issue_model.py`, `modeling/model_registry.py`,
`modeling/model_evaluation.py`.

**What they do:** confirm that the existing model code, schemas, artifacts, and
metrics agree. If a repair is needed, change the owner source module rather
than committing generated binaries.

**Proof:** amendment, exposure, and issue artifacts exist and metrics are
available for the SME.

### Raghu — verify the existing document index

**Paste/run from:** `Project\`

```powershell
python run_knowledge_indexing.py
Get-ChildItem database\chroma_store
```

**Files used:** `run_knowledge_indexing.py`, `knowledge/pdf_extraction.py`,
`knowledge/chunk_splitting.py`, `knowledge/vector_index.py`.

**What they do:** confirm the existing knowledge layer can read the supplied
PDFs and return stable source-linked chunks. Do not copy the PDFs elsewhere.

**Proof:** a retrieval query returns passage text, document name, chunk ID, and
distance.

### Ronit — run deterministic campaign tools

**Paste into:** a Python REPL from `Project\`, or a temporary local test file
that must not be committed.

```python
from config import config
from data_pipeline.dataset_loader import load_raw_dataset
from tools.campaign_data_tools import (
    fetch_campaign_profile,
    fetch_campaign_spots,
    fetch_campaign_schedules,
)

campaigns = load_raw_dataset(config.OPEN_CAMPAIGNS_FILE)
spots = load_raw_dataset(config.BOOKED_SPOTS_FILE)
reference = str(campaigns.iloc[0][config.CAMPAIGN_REFERENCE_COLUMN])
profile = fetch_campaign_profile(campaigns, reference)
campaign_spots = fetch_campaign_spots(spots, reference)
schedule = load_raw_dataset(config.PROGRAMME_SCHEDULE_FILE)
campaign_schedule = fetch_campaign_schedules(schedule, campaign_spots)
print("campaign:", profile[config.CAMPAIGN_REFERENCE_COLUMN])
print("booked spots:", len(campaign_spots))
print("schedule rows:", len(campaign_schedule))
```

**Files used:** `tools/campaign_data_tools.py`,
`tools/schedule_tools.py`, `tools/prediction_tools.py`.

**What they do:** exercise the existing campaign and compliance tools against
the supplied live queue. If a repair is needed, edit only the owned source
module.

**Proof:** the worked example campaign returns booked spots, breach codes,
exposure, first transmission, and open decisions.

### Avinash — prepare the UI contract, not the finished UI

**Paste/reference:** `Project\TEST_API_EXAMPLES.md`

```text
Swagger order:
sign in -> queue -> campaign detail -> create assessment ->
pending clearances -> assessment detail -> model calls ->
second controller sign in -> decision -> final detail -> audit -> chat.
```

**What it does:** gives the dashboard owner the exact API sequence without
duplicating backend rules.

**Proof:** demonstrate the sequence in Swagger. The real Streamlit pages are
Wednesday/Thursday work.

# Wednesday — Day 3: The First Shield

**Goal: build the real Streamlit shell and connect it to the API.**

| Person | Work | Files | Demo |
|---|---|---|---|
| Rohan | stabilize response shapes and API integration points | `api/`, shared schemas only if approved | API sequence works from a fresh database |
| Kartiga | reproducible artifacts and model display data | `modeling/`, training scripts | risk/exposure values shown to UI owner |
| Raghu | retrieval-backed chat responses and source display | `knowledge/`, chat retrieval tools | answer plus source document |
| Ronit | workflow integration and final spot summaries | `agentic/`, `tools/` | decision paths produce correct outcomes |
| Avinash | queue, campaign detail, login/navigation pages | `dashboard/` | Streamlit displays live API data |

### Avinash's Wednesday paste/run commands

```powershell
python -m streamlit run dashboard/clearance_queue.py
```

The dashboard must use `dashboard/api_client.py`; it must not import
`pandas`, `pypdf`, or database sessions for business data.

# Thursday — Day 4: The Human Gate

**Goal: finish UI pages, chat, audit, decision flow, and role visibility.**

| Person | Work | Demo |
|---|---|---|
| Rohan | final auth/role/audit/decision integration | controller can decide only through permitted path |
| Kartiga | score bands, edge cases, artifact regeneration | risk cards agree with model outputs |
| Raghu | chat memory, refusal, source attribution | unsupported questions are refused |
| Ronit | checkpoint resume and all three decision routes | CLEAR, RESTRICT, REJECT demos |
| Avinash | decision queue, audit trail, chat panel, role pages | full Streamlit clearance journey |

### Thursday acceptance journey

1. Executive signs in.
2. Executive reads queue and opens assessment.
3. Workflow pauses at `PENDING_DECISION`.
4. A different Controller signs in.
5. Controller decides `CLEAR WITH RESTRICTIONS`.
6. UI shows restriction notice before certificate.
7. Audit page shows the decision.
8. Chat explains status according to role.

# Friday — Day 5: The Gom Jabbar

**Everything must run by Friday afternoon. No new features after the freeze.**

## Friday morning freeze

```powershell
cd "D:\Downloads\workspace-source-20261109-102912\workspace\Project"
git checkout main
git pull origin main
python -m pytest ..\pytest\tests.py -q
```

If pytest fails, fix only release-blocking defects. Do not redesign interfaces.

## Friday startup proof

```powershell
.\run_project.ps1 -SkipKnowledgeIndex -SkipModelTraining
```

Open:

```text
http://127.0.0.1:8000/docs
```

Then start the dashboard in another terminal:

```powershell
python -m streamlit run dashboard/clearance_queue.py
```

The Friday run uses the repository's existing source tree and supplied
`BreakCheck_AI.pdf`/CSV assets. It does not depend on newly copied project
files. Generated local artifacts may be rebuilt on the machine but must remain
ignored by Git.

## Friday afternoon SME demonstration

1. Explain the business problem and queue priority.
2. Show the five cleaned datasets and quality report.
3. Show model metrics and risk values.
4. Ask a policy question and show its source document.
5. Open a campaign and show deterministic breach reasons.
6. Pause at the human decision gate.
7. Decide with a second Controller.
8. Show cleared and withdrawn spots.
9. Show audit events, model calls, and chat history.
10. Repeat the main journey from Streamlit.

## Definition of victory

The mission is complete when:

- every person has a domain-specific Monday and Tuesday commit;
- UI work is visibly completed on Wednesday and Thursday;
- no branch owns another branch's files;
- fresh startup works on Friday;
- the API requires authentication and enforces roles;
- the dashboard reads facts only through the API;
- policy answers identify source documents;
- the workflow pauses before clearance;
- the second Controller can resume and decide;
- all three decision routes work;
- `python -m pytest ..\pytest\tests.py -q` passes;
- the SME can operate the complete Streamlit journey Friday afternoon.

## Honest confidence statement

Yes: the revised plan gives every person a visible artifact every day.
Monday and Tuesday show data, documents, deterministic compliance, API
behavior, and the UI contract. Wednesday and Thursday show the actual
Streamlit pages and the integrated human-decision journey.

No Git plan can mathematically guarantee zero conflicts. This plan makes normal
work conflict-safe by separating ownership directories, locking shared files,
merging one PR at a time, and testing after every merge. The only serious
remaining conflict risk is an unplanned edit to a shared file; the protocol
above explicitly routes those edits through Rohan.
