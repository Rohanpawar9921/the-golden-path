# Swagger API Test Examples

Open:

```text
http://127.0.0.1:8000/docs
```

Run the endpoints in this order. In Swagger, click **Try it out**, paste the
values below, then click **Execute**.

## 1. Sign in as a Clearance Executive

Endpoint:

```text
POST /auth/sign-in
```

Request body:

```json
{
  "username": "tom",
  "password": "22222222"
}
```

Copy the returned `session_token`.

Click **Authorize** at the top of Swagger and paste only the token value into
the `X-Session-Token` field. Click **Authorize**, then **Close**.

## 2. Read the queue

Endpoint:

```text
GET /queue
```

Query parameter:

```text
product_category=All
```

From the response, choose a row where:

```text
spots_breaching > 0
spots_breaching < spots_booked
```

Copy that row's `campaign_reference`. It is called
`YOUR_CAMPAIGN_REFERENCE` below.

## 3. Read campaign details

Endpoint:

```text
GET /queue/YOUR_CAMPAIGN_REFERENCE
```

Replace `YOUR_CAMPAIGN_REFERENCE` with the value copied from step 2.

Example:

```text
GET /queue/CLR-QSC-0042117
```

## 4. Create an assessment

Endpoint:

```text
POST /assessments
```

Request body:

```json
{
  "campaign_reference": "YOUR_CAMPAIGN_REFERENCE",
  "executive_request": "Check every booked spot against the category code and tell me whether the copy can be cleared."
}
```

Copy the returned `assessment_id`. It is called
`YOUR_ASSESSMENT_ID` below.

The assessment should initially have status:

```text
PENDING_DECISION
```

## 5. List pending clearances

Endpoint:

```text
GET /clearances
```

Query parameter:

```text
status_value=PENDING_DECISION
```

Confirm that the assessment created in step 4 appears in the response.

## 6. Read the assessment

Endpoint:

```text
GET /clearances/YOUR_ASSESSMENT_ID
```

Replace `YOUR_ASSESSMENT_ID` with the value returned by step 4.

## 7. Read model calls

Endpoint:

```text
GET /clearances/YOUR_ASSESSMENT_ID/calls
```

Replace `YOUR_ASSESSMENT_ID` with the value returned by step 4.

## 8. Sign in as a different Clearance Controller

Use the second sign-in response for the decision. Do not use the same user who
created the assessment.

Endpoint:

```text
POST /auth/sign-in
```

Request body:

```json
{
  "username": "owen",
  "password": "11111111"
}
```

Click **Authorize** again and replace the old token with the new
`session_token`.

## 9. Record the controller decision

Endpoint:

```text
POST /clearances/YOUR_ASSESSMENT_ID/decision
```

Replace `YOUR_ASSESSMENT_ID` in the path.

Request body for a campaign with breaches:

```json
{
  "decision": "CLEAR WITH RESTRICTIONS",
  "decision_reason": "Compliant spots may air; breaching spots must be withdrawn."
}
```

Other valid decision bodies:

```json
{
  "decision": "REJECT",
  "decision_reason": "The copy breaches the applicable requirements."
}
```

```json
{
  "decision": "CLEAR",
  "decision_reason": "All checked spots comply with the applicable requirements."
}
```

Use `CLEAR WITH RESTRICTIONS` or `REJECT` when the selected campaign has
breaching spots. `CLEAR` is rejected for a campaign with breaches.

## 10. Read the final assessment

Endpoint:

```text
GET /clearances/YOUR_ASSESSMENT_ID
```

The final status should be one of:

```text
CLEARED
CLEARED_WITH_RESTRICTIONS
REJECTED
```

## 11. Read the final model calls

Endpoint:

```text
GET /clearances/YOUR_ASSESSMENT_ID/calls
```

Confirm that the final drafting calls appear after the five initial calls.

## 12. Read the audit events

Endpoint:

```text
GET /audit
```

Optional query parameter:

```text
limit=50
```

## 13. Ask a chat question

Endpoint:

```text
POST /chat/ask
```

Request body:

```json
{
  "question": "What does the alcohol code say about this category?"
}
```

## 14. Read your chat history

Endpoint:

```text
GET /chat/turns
```

Optional query parameter:

```text
turn_limit=20
```

## 15. Read the audit chat history

This endpoint requires a user with audit access, such as a Clearance Controller.

Endpoint:

```text
GET /audit/chat-turns
```

Optional query parameter:

```text
turn_limit=50
```

## Important testing notes

- Always use `All`, not `ALL`, for the queue category.
- Replace `YOUR_CAMPAIGN_REFERENCE` and `YOUR_ASSESSMENT_ID` before executing.
- After signing in as another user, click **Authorize** and replace the old token.
- Do not repeat assessment creation for the same campaign; the API rejects duplicates.
- If the API was restarted, run the sequence again from step 1 because the test
  database is reinitialized on service startup.
