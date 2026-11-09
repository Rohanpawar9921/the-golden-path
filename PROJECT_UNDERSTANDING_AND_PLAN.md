# BreakCheck AI: Understanding and Implementation Plan

## 1. Can this project be completed?

Yes. The project can be implemented from the supplied source structure, configuration, datasets, policy PDFs, and pytest contract.

The tests are detailed enough to define the expected behavior of the application. They cover the data pipeline, machine-learning models, document retrieval, scheduling compliance, persistence, agent workflow, authentication, API permissions, queue behavior, and chat.

Implementation must preserve the supplied raw data, PDFs, tests, configuration, and existing files. No file should be deleted.

## 2. Current repository understanding

### Main locations

- `Project/`: application source tree.
- `pytest/tests.py`: behavioral contract and integration tests.
- `Project/config/config.py`: central constants, mappings, paths, thresholds, roles, workflow states, and API/chat rules.
- `Project/data/`: raw datasets, live queue inputs, and sixteen policy/guide PDFs.
- `Project/requirements.txt`: runtime and test dependencies.
- `pytest/run.sh`: test runner that copies the tests into `Project/` and runs pytest.

### Current implementation state

Most application modules are empty scaffolds. The configuration and test suite are populated and should be treated as the authoritative specification.

The application is intended to be a complete advertising-clearance platform for Harbourlight Media:

1. Clean supplied datasets.
2. Train and save three models.
3. Index policy and guide documents.
4. Evaluate booked campaign spots against category rules and programme schedules.
5. Run a multi-agent clearance assessment.
6. Pause for an independent Clearance Controller decision.
7. Record the decision, documents, audit events, and model-call costs.
8. Serve the workflow through FastAPI.
9. Expose a Streamlit dashboard and document-grounded chat.

## 3. Test-driven functional contract

### A. Data loading and cleaning

Implement:

- Raw CSV loading as text without silently changing source data.
- Null-token handling using the configured null vocabulary.
- Duplicate removal while retaining one answered record.
- Removal of records whose target answer is never provided.
- Canonicalization of booleans, weekdays, categories, channels, genres, roles, sources, and issue labels.
- Strict numeric parsing for counts, percentages, audiences, and rates.
- Conversion of audience values to thousands.
- Conversion of copy lengths to seconds.
- Clock-number length validation, with the clock number taking precedence over a conflicting written length.
- Broadcast-clock conversion for scheduler-specific time formats.
- Broadcast-day rollover before 06:00.
- Contradiction repair by making impossible facts missing rather than discarding the answered record.
- Note text normalization: markup removal, entity decoding, whitespace cleanup, lowercase normalization for all-capital notes, timestamp normalization, and short-note removal.
- Quality profiling for every input and cleaned output.
- JSON quality report with row counts, duplicates, missing targets/cells, removals, and domain-specific defects.

Expected outputs:

- Five cleaned CSV files under `processed/`.
- One quality report under `output/data_quality_report.json`.

### B. Feature construction and machine learning

Implement:

- Feature-frame construction in the exact configured order.
- Numeric columns as floating-point values, preserving missing values.
- Categorical columns with missing values preserved for model imputers/encoders.
- Broadcast start-minute and duration features.
- Saved feature schemas that contain only declared predictive features.
- No target, identifier, or post-airing audience leakage.

Train and save:

1. Amendment classifier
   - Predicts whether a submission needs amendment.
   - Must expose probability classes `[0, 1]`.
   - Must meet configured ROC-AUC threshold.
   - Must respond directionally to health claims and missing offer terms.

2. Exposure regressor
   - Predicts under-18 audience exposure in thousands.
   - Must meet configured R² threshold.
   - Must respond directionally to school holidays, broadcast time, and forecast index.

3. Issue text classifier
   - Predicts one of the configured issue categories.
   - Must meet configured macro-F1 threshold.
   - Must cover every issue category in held-out predictions.

Also implement:

- Model serialization/deserialization.
- Feature schema serialization/deserialization.
- Classifier and regressor evaluation helpers.
- `output/model_metrics.json`.

### C. Knowledge extraction and retrieval

Implement:

- PDF extraction for every PDF in the configured documents directory.
- Refusal when any page produces no usable text.
- Ignoring non-PDF files.
- Section splitting using the configured section/header patterns.
- Removal of repeated document headers.
- Chunking with configured size and overlap.
- Stable unique chunk identifiers.
- Chroma vector-store creation and opening.
- Exact metadata association between each chunk and its source document.
- Search results containing chunk ID, text, document name, and distance.
- Document-restricted nearest-passage lookup.
- Whole-document retrieval.
- Exclusion of the casebook from chat retrieval.
- Refusal for unknown documents.

### D. Policy/code reading

Implement strict category-specific parsing for:

- Restricted hours or explicit all-day permission.
- Live-sport exception margins.
- Under-18 audience index threshold.
- Children’s-programme rule: `in` or `in or adjacent`.
- Daily campaign cap.
- Minimum separation between spots.
- Source document identity.
- Rule sentences for audit/explanation.

The reader must:

- Read rules only from the category’s configured code document.
- Reject contradictory codes.
- Reject missing/ambiguous rules.
- Never borrow values from another category or a decoy/superseded document.

### E. Scheduling and spot compliance

Implement:

- Campaign profile and campaign-note retrieval.
- Deterministic note ordering by numeric sequence.
- Duplicate, missing, and ambiguous record rejection.
- Spot length and clock-number validation.
- Schedule lookup by channel, scheduler, and broadcast day.
- Placement inside a programme or adjacent to two programmes at a boundary.
- Broadcast-clock placement across midnight.
- Rejection when placement is impossible.
- Breach checks in configured order:
  1. `WINDOW`
  2. `INDEX`
  3. `CHILDREN`
  4. `FREQUENCY`
  5. `SEPARATION`
- Daily caps per campaign, channel, and broadcast day.
- Separation from the previous spot in transmission order.
- Same-break ordering by spot reference.
- Correct handling of live-sport exceptions.
- Campaign summaries, open decisions, exposure, and first transmission.
- Clearance outcomes listing cleared and withdrawn spot references and counts.

### F. Prediction and campaign tools

Implement tools for:

- Amendment facts and score bands.
- Exposure forecasts.
- Issue facts with weighted votes and agreement.
- Campaign notes and profiles.
- Campaign spots and schedules.
- Schedule compliance.
- Retrieval-backed code and guide facts.
- Queue construction and ordering.

The queue must:

- Include each open campaign once.
- Support category filtering.
- Order by largest exposure first.
- Tie-break by earliest transmission and campaign reference.
- Assign sequential queue positions.
- Expose summary, risk, exposure, first transmission, and amendment fields.

### G. Persistence

Implement SQLAlchemy models and database helpers for:

- Users and password/session state.
- Assessment records.
- Agent runs and checkpoints.
- Model calls and latency/cost metadata.
- Spot results and clearance outcomes.
- Chat turns.
- Audit events.

Implement repository functions for:

- User lookup and session updates.
- Assessment lookup and status changes.
- Agent-run persistence.
- Call logging.
- Chat-turn insertion and retrieval.
- Campaign status records.
- Audit data needed by the API and tests.

Database setup must be repeatable and seed configured user accounts without storing plaintext passwords.

### H. Agent workflow

Implement the ten configured reachable nodes:

1. `load_campaign_context`
2. `plan_assessment`
3. `assess_copy_risk`
4. `identify_issues`
5. `check_spot_schedule`
6. `compose_clearance_assessment`
7. `request_controller_decision`
8. `draft_restriction_notice`
9. `draft_clearance_certificate`
10. `record_clearance_outcome`

Required behavior:

- Five assessing agents run exactly once and in the configured order.
- Each model call is recorded with agent, model, prompt size, response size, and positive latency.
- The run pauses at `AWAITING_DECISION`.
- No spots are cleared before a controller decision.
- The controller who opened the assessment cannot decide it.
- Another Clearance Controller can resume it.
- Checkpoint resume must not repeat completed agents.
- Decision routing:
  - `CLEAR` -> certificate -> record outcome.
  - `CLEAR WITH RESTRICTIONS` -> restriction notice -> certificate -> record outcome.
  - `REJECT` -> record outcome without either document.
- Stored assessment facts must match the deterministic tools that produced them.
- Model-generated text must be parsed without losing content caused by decoration characters.

### I. Authentication and FastAPI service

Implement:

- Password hashing with configured algorithm, salt size, and rounds.
- Sign-in with indistinguishable unknown-user and wrong-password failures.
- One active session per user.
- Sign-out invalidation.
- Authentication responses containing token, identity, role, pages, and areas.
- Authentication guards returning 401 when missing/invalid.
- Role-area guards returning 403 before resource lookup.
- Correct role permissions for Controller, Executive, and Agency Liaison.
- Queue endpoints.
- Assessment opening endpoint.
- Clearance listing/detail/call endpoints.
- Controller decision endpoint.
- Chat ask/history endpoints.
- Audit endpoints.
- Correct 404 responses for unknown campaigns/assessments when the role has access.
- Validation of minimum request and decision-reason lengths.
- Consistent response schemas and explicit errors.

### J. Chat and conversation memory

Implement:

- Question classification into configured chat types.
- Document-grounded code, scheduling, and agency advice answers.
- Campaign-status answers from persisted records.
- Campaign-reference extraction and validation.
- Access filtering for Agency Liaison campaign status.
- Refusal for out-of-scope or unsupported questions.
- Source-document reporting.
- Casebook exclusion.
- Short conversation-history recall.
- Chat-turn persistence.
- Status answers that avoid repeating the full answer in history.

### K. Dashboard and entry points

Implement the Streamlit modules and launch scripts after the service/tool contracts are stable:

- Queue page.
- Campaign detail page.
- Clearance chat.
- Decision queue.
- Audit trail.
- API client.
- Dashboard routing and authentication state.
- Data pipeline, database setup, indexing, model training, API, and dashboard entry points.

## 4. Recommended implementation order

### Phase 0: Safety and baseline

1. Preserve all supplied files.
2. Confirm Python/dependency availability.
3. Run the tests once to capture the initial failure baseline.
4. Do not copy, delete, or overwrite raw data except where the supplied test runner explicitly requires its normal test copy behavior.

### Phase 1: Foundations

1. Add package initialization files only where imports require them.
2. Implement configuration-safe path handling.
3. Implement dataset loading and common cleaning helpers.
4. Implement persistence models, database engine/session setup, and repeatable database initialization.
5. Implement password hashing and session helpers.

### Phase 2: Data pipeline

1. Implement submission cleaning.
2. Implement audience cleaning.
3. Implement note cleaning.
4. Implement feature construction.
5. Implement quality profiling and pipeline orchestration.
6. Run the data-cleaning and feature-focused tests.

### Phase 3: Models

1. Implement model registry and serialization.
2. Implement evaluation helpers.
3. Implement amendment model training.
4. Implement exposure model training.
5. Implement issue model training.
6. Write schemas, metrics, and model artifacts.
7. Run the model-focused tests and adjust only the implementation or model choices needed to satisfy the declared thresholds.

### Phase 4: Knowledge base

1. Implement PDF extraction.
2. Implement section splitting and chunking.
3. Implement vector indexing and opening.
4. Implement document search.
5. Implement code reading and retrieval helpers.
6. Run knowledge and code-reading tests.

### Phase 5: Scheduling and business tools

1. Implement campaign data readers.
2. Implement schedule placement.
3. Implement all compliance checks.
4. Implement outcome summarization.
5. Implement prediction and queue tools.
6. Run scheduling and tool tests.

### Phase 6: Agent workflow

1. Define typed workflow state.
2. Implement agent response parsing.
3. Implement deterministic context and tool-backed agent nodes.
4. Implement model-call logging.
5. Implement LangGraph checkpointing and pause/resume.
6. Implement decision routing and document drafting.
7. Run workflow and persistence integration tests.

### Phase 7: API, chat, and access control

1. Implement request/response schemas.
2. Implement authentication and session lifecycle.
3. Implement role-area guards.
4. Implement queue and campaign endpoints.
5. Implement assessment and decision endpoints.
6. Implement audit and model-call endpoints.
7. Implement chat classification, retrieval, status answers, and memory.
8. Run API, access, workflow, and chat tests.

### Phase 8: Dashboard and full validation

1. Implement API client and dashboard pages.
2. Wire launch scripts.
3. Run the complete pytest suite from the prescribed runner.
4. Fix failures in dependency order, starting with the earliest failing contract.
5. Re-run the complete suite after targeted fixes.
6. Verify generated outputs and runtime startup paths.

## 5. Validation strategy

Validation should be incremental:

1. Import and syntax checks.
2. Focused data-cleaning tests.
3. Focused model tests.
4. Focused knowledge and scheduling tests.
5. Focused workflow/API/chat tests.
6. Full pytest suite.

The final implementation is complete only when:

- All expected generated artifacts exist.
- Raw supplied inputs remain unchanged.
- The full test suite passes.
- The API and dashboard entry points start successfully.
- No secrets are added to source files.
- Errors are explicit and consistent with the project’s API conventions.

## 6. Important constraints and decisions

- The pytest suite is the acceptance contract.
- `config/config.py` is the canonical source for names, paths, mappings, thresholds, roles, and messages.
- Deterministic tools must produce the facts stored in assessments; language-model text must not replace deterministic calculations.
- Policy answers must be grounded in the supplied PDFs and must identify their source documents.
- Ambiguous, contradictory, malformed, or unplaceable inputs must be rejected or made explicitly missing according to the test contract; they must never be guessed.
- No existing file may be deleted.
- New Markdown documentation should be created only when it directly supports the project or is explicitly requested.
- The later project PDF can be incorporated as an additional requirement source without discarding the current test-driven contract.

## 7. Immediate next step when implementation is authorized

When implementation is requested, begin with the baseline test run and dependency/import assessment, then implement the foundation and data-pipeline phases first. Do not begin with the dashboard or language-model integration because all higher-level behavior depends on cleaned data, deterministic tools, persistence, and stable contracts.
