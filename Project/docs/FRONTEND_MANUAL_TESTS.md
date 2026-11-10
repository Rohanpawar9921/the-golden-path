# Frontend manual test guide

Use this checklist after starting the API and dashboard as described in
[`HOW_TO_RUN.md`](../HOW_TO_RUN.md). Sign in through the dashboard with a demo account
listed on the login screen. The application obtains and retains the session token itself;
there is no token to copy into a field.

## Regression checks

| # | Area | Action | Expected result |
|---|---|---|---|
| 1 | Role-aware Home | Sign in as a controller, executive, and liaison in turn | Home explains BreakCheck, identifies the signed-in role, shows permitted pages, and gives a role-appropriate next action. The liaison sees assigned agencies. |
| 2 | Overview navigation | Choose a campaign and click **View campaign** | Campaign detail opens for the chosen reference; no session-state error appears. |
| 3 | Queue navigation | Open **Clearance queue**, choose a campaign, click **Open campaign detail** | Campaign detail opens for that reference; no session-state error appears. |
| 4 | Campaign selection | On Campaign detail, choose another reference | The summary, spot checks, and assessment snapshot refresh for that campaign. |
| 5 | Start assessment | Submit the prefilled request | An assessment ID and status appear; the assessment is available under Assessments. |
| 6 | Assessment record | Open Assessments and select the new record | Summary, model calls, and full record tabs load. |
| 7 | Decision desk | As a controller, open a pending assessment, enter a reason, confirm review, and record an allowed outcome | The outcome is recorded and the page reports cleared/withdrawn spot counts. |
| 8 | Audit trail | Open Audit trail after recording a decision | The event appears in Audit events; chat activity tab loads. |
| 9 | Chat retrieval | Ask “How many spots of one alcohol campaign may go out on one channel in one broadcast day?”, then “How far apart must Betting and gaming spots be?” | Answers differ, cite the relevant category codes, and use each figure only from its own code. Both questions appear in recent conversation. |
| 10 | Sign out and access | Sign out, then sign in as an executive and as an agency liaison | Each role returns to Home, sees only its allowed pages, and gets a next step for that role; restricted pages cannot be selected. |
| 11 | Out-of-scope chat | Ask “What is the capital of France?” | The assistant refuses instead of answering from general knowledge and cites no policy document. |
| 12 | Liaison ownership | As a liaison, ask about one campaign belonging to an assigned agency and one belonging to another agency | The assigned campaign gets its permitted status; the other gets the same not-found answer as an unknown reference. |

For the queue navigation check, also try a product category filter and a partial campaign
reference search before opening a result. An empty search should display an empty result
table without an error. If no assessment is pending, the decision desk should show that its
queue is clear.

## Automated acceptance suite

From the `Project` directory, run the 50 case acceptance suite, five Streamlit UI checks,
and three assistant retrieval/generation checks. Disable live model calls for a repeatable,
offline test run:

```powershell
$env:BREAKCHECK_CHAT_OFFLINE = "1"
python -m pytest ..\pytest\tests.py tests -q
Remove-Item Env:BREAKCHECK_CHAT_OFFLINE
```

The current acceptance file contains 50 automated checks for data cleaning, features and
models, policy retrieval, campaign assessment, decisions, permissions, queue ordering, and
chat access. The UI checks verify role-appropriate Home guidance for all three roles and
click each campaign button. Assistant checks verify one generated response uses the question
and all category codes, the offline retrieval answers different questions from their own
codes, and the Gemini transport makes one authenticated request. The manual checks above
cover broader interactive page rendering and live Gemini generation.
