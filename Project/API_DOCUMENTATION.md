# BreakCheck API Documentation

Base URL:

```text
http://127.0.0.1:8000
```

Interactive documentation is also available at:

```text
http://127.0.0.1:8000/docs
```

## Authentication

Sign in first. The returned token must be sent in the `X-Session-Token` header.

### `POST /auth/sign-in`

The alias `POST /auth/signin` is also supported.

Request:

```json
{
  "username": "tom",
  "password": "22222222"
}
```

PowerShell:

```powershell
$login = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/auth/sign-in" `
  -ContentType "application/json" `
  -Body '{"username":"tom","password":"22222222"}'
$token = $login.session_token
$headers = @{ "X-Session-Token" = $token }
```

Seeded test accounts:

| Role | Usernames | Password |
|---|---|---|
| Clearance Controller | `priya`, `owen`, `grace` | `11111111` |
| Clearance Executive | `tom`, `aisha`, `daniel`, `hannah`, `marcus`, `zara` | `22222222` |
| Agency Liaison | `lucy`, `ben`, `sofia`, `jack`, `nadia` | `33333333` |

### `POST /auth/signout`

Headers: `X-Session-Token`

```powershell
Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/auth/signout" `
  -Headers $headers
```

The token is invalid after sign-out.

## Intake and queue

These endpoints require a signed-in Controller or Executive.

### `GET /queue`

Optional query parameter:

```text
product_category=All
```

Example:

```powershell
$queue = Invoke-RestMethod -Uri "http://127.0.0.1:8000/queue?product_category=All" `
  -Headers $headers
$queue | ConvertTo-Json -Depth 5
```

Each queue row includes `campaign_reference`, `product_category`, `spots_booked`,
`spots_breaching`, `exposure`, `amendment_score`, `amendment_band`,
`first_transmission`, and `queue_position`.

### `GET /queue/{campaign_reference}`

Example:

```powershell
$reference = $queue[0].campaign_reference
Invoke-RestMethod -Uri "http://127.0.0.1:8000/queue/$reference" `
  -Headers $headers | ConvertTo-Json -Depth 8
```

The detail response includes spot results, breach counts, amendment information,
issue information, exposure, code document, and available decisions.

## Assessments

Assessment creation requires a signed-in Controller or Executive.

### `POST /assessments`

Request:

```json
{
  "campaign_reference": "CLR-QSC-0042117",
  "executive_request": "Check every booked spot against the category code."
}
```

PowerShell:

```powershell
$body = @{
  campaign_reference = $reference
  executive_request = "Check every booked spot against the category code."
} | ConvertTo-Json

$assessment = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/assessments" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $body
$assessment | ConvertTo-Json -Depth 8
$assessmentId = $assessment.assessment_id
```

The initial status is `PENDING_DECISION`. The response contains the assessment
identifier, run identifier, recommendation, model facts, breach details, and
the five pre-decision model calls.

An assessment can only be opened once for a campaign. Use a fresh campaign from
`GET /queue` when testing creation repeatedly.

### `GET /clearances`

Requires the audit area: Controller or Executive.

Optional repeated query parameter:

```text
status_value=PENDING_DECISION
```

Example:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/clearances?status_value=PENDING_DECISION" `
  -Headers $headers | ConvertTo-Json -Depth 5
```

### `GET /clearances/{assessment_id}`

Returns the stored assessment status, decision, reason, and result.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/clearances/$assessmentId" `
  -Headers $headers | ConvertTo-Json -Depth 8
```

### `GET /clearances/{assessment_id}/calls`

Returns every recorded model call, call count, expected call count, and total
latency.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/clearances/$assessmentId/calls" `
  -Headers $headers | ConvertTo-Json -Depth 8
```

## Controller decisions

Only a Clearance Controller can decide. The Controller who opened an assessment
cannot decide their own assessment.

### `POST /clearances/{assessment_id}/decision`

Use one of these exact decisions:

- `CLEAR`
- `CLEAR WITH RESTRICTIONS`
- `REJECT`

Request:

```json
{
  "decision": "CLEAR WITH RESTRICTIONS",
  "decision_reason": "Compliant spots may air; breaching spots must be withdrawn."
}
```

The `reason` field is also accepted:

```json
{
  "decision": "REJECT",
  "reason": "The copy breaches the applicable requirements."
}
```

PowerShell:

```powershell
$controllerLogin = Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/auth/sign-in" `
  -ContentType "application/json" `
  -Body '{"username":"owen","password":"11111111"}'
$controllerHeaders = @{ "X-Session-Token" = $controllerLogin.session_token }

$decisionBody = @{
  decision = "CLEAR WITH RESTRICTIONS"
  decision_reason = "Compliant spots may air; breaching spots must be withdrawn."
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/clearances/$assessmentId/decision" `
  -Headers $controllerHeaders `
  -ContentType "application/json" `
  -Body $decisionBody | ConvertTo-Json -Depth 8
```

After a decision, the assessment status becomes one of:

- `CLEARED`
- `CLEARED_WITH_RESTRICTIONS`
- `REJECTED`

The response includes the decision, decision timestamp, cleared and withdrawn
spots, call count, and generated notice/certificate text.

## Audit

These endpoints require the audit area.

### `GET /audit`

Optional query parameter: `limit`.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/audit?limit=50" `
  -Headers $controllerHeaders | ConvertTo-Json -Depth 8
```

### `GET /audit/chat-turns`

Optional query parameter: `turn_limit`.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/audit/chat-turns?turn_limit=50" `
  -Headers $controllerHeaders | ConvertTo-Json -Depth 8
```

## Chat

Chat requires a signed-in user with chat access.

### `POST /chat/ask`

Request:

```json
{
  "question": "What does the alcohol code say about this category?"
}
```

PowerShell:

```powershell
$chatBody = @{
  question = "What does the alcohol code say about this category?"
} | ConvertTo-Json

Invoke-RestMethod -Method Post `
  -Uri "http://127.0.0.1:8000/chat/ask" `
  -Headers $headers `
  -ContentType "application/json" `
  -Body $chatBody | ConvertTo-Json -Depth 8
```

The response includes `question_type`, `campaign_reference`, `answer`,
`source_documents`, `was_refused`, and `closest_distance`.

### `GET /chat/turns`

Optional query parameter: `turn_limit`.

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat/turns?turn_limit=20" `
  -Headers $headers | ConvertTo-Json -Depth 8
```

## Expected error responses

| Status | Meaning |
|---:|---|
| `401` | Missing or invalid `X-Session-Token` |
| `403` | Signed-in role is not permitted to use the endpoint |
| `404` | Campaign or assessment was not found |
| `409` | Duplicate assessment, already-decided assessment, or invalid decision for the campaign |
| `422` | Request validation failed |

## Recommended end-to-end test

1. Start the project with `.\run_project.ps1 -SkipKnowledgeIndex -SkipModelTraining`.
2. Sign in as `tom` and save the token.
3. Call `GET /queue`.
4. Choose a campaign with both compliant and breaching spots.
5. Create an assessment with `POST /assessments`.
6. Inspect it using `/clearances/{assessment_id}`, `/calls`, and `/clearances`.
7. Sign in as a different Controller, such as `owen`.
8. Submit a decision.
9. Verify the final assessment, audit event, model calls, and chat response.

For browser-based testing, use the Swagger UI at
`http://127.0.0.1:8000/docs`.
