"""Controller decision desk for pending clearance assessments."""

import streamlit as st

from dashboard.ui import dataframe, metric_card, page_header, status_label


def render(api) -> None:
    page_header("CONTROLLER WORKSPACE", "Decision desk", "Review pending assessments and record a reasoned controller outcome.")
    pending = api.get("/clearances", params={"status_value": "PENDING_DECISION"}) or []
    if not pending:
        st.success("The decision queue is clear.")
        return
    dataframe(pending, ["assessment_id", "campaign_reference", "status"])
    ids = [str(row["assessment_id"]) for row in pending]
    previous = st.session_state.get("selected_assessment")
    index = ids.index(previous) if previous in ids else 0
    selected = st.selectbox("Assessment to decide", ids, index=index, key="decision_assessment")
    st.session_state.selected_assessment = selected
    detail = api.get(f"/clearances/{selected}")
    result = detail.get("result") or {}
    st.divider()
    st.subheader(f"{detail.get('campaign_reference', 'Campaign')} · {status_label(detail.get('status'))}")
    a, b, c = st.columns(3)
    for col, (label, value, note) in zip(
        [a, b, c],
        [("Recommendation", result.get("recommended_decision", "—"), "Assessment suggestion"),
         ("Spots flagged", result.get("spots_breaching", 0), "Review restrictions carefully"),
         ("Compliant spots", result.get("spots_compliant", 0), "Recorded in assessment")],
    ):
        with col:
            metric_card(label, value, note)
    st.markdown("**Breaching spots**")
    dataframe(result.get("breaching_spots", []), ["spot_reference", "breach_codes"])
    st.info("The assessment opener cannot decide their own record. The API enforces this rule.")

    choices = result.get("decisions_open") or ["CLEAR WITH RESTRICTIONS", "REJECT"]
    with st.form("controller_decision"):
        decision = st.selectbox("Controller outcome", choices)
        reason = st.text_area("Decision reason", placeholder="Explain the decision for the audit record.")
        confirmed = st.checkbox("I have reviewed the campaign facts and assessment.")
        submit = st.form_submit_button("Record decision", type="primary")
    if submit:
        if not confirmed:
            st.error("Confirm that you reviewed the assessment before recording a decision.")
        elif len(reason.strip()) < 10:
            st.error("Enter a reason of at least 10 characters.")
        else:
            outcome = api.post(
                f"/clearances/{selected}/decision",
                {"decision": decision, "decision_reason": reason.strip(), "reason": reason.strip()},
            )
            status = outcome.get("status", decision).replace("_", " ").title()
            st.success(f"Decision recorded · {status}")
            st.json({"decision": outcome.get("decision"),
                     "spots_cleared": outcome.get("spots_cleared_count"),
                     "spots_withdrawn": outcome.get("spots_withdrawn_count")}, expanded=False)
