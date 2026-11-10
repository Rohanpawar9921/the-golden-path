"""Assessment status, recommendation, and model-call visibility."""

import streamlit as st

from dashboard.ui import dataframe, metric_card, page_header, status_label


def render(api) -> None:
    page_header("REVIEW RECORDS", "Assessments", "Follow each assessment from recommendation through controller decision.")
    records = api.get("/clearances") or []
    if not records:
        st.info("No assessments have been opened yet. Choose a campaign from the queue to start one.")
        return
    filters = ["All"] + sorted({str(row.get("status", "UNKNOWN")) for row in records})
    col_filter, col_ref = st.columns([1, 2])
    with col_filter:
        status = st.selectbox("Status", filters)
    filtered = [row for row in records if status == "All" or row.get("status") == status]
    dataframe(filtered, ["assessment_id", "campaign_reference", "status", "decision"])
    if not filtered:
        return
    ids = [str(row["assessment_id"]) for row in filtered]
    previous = st.session_state.get("selected_assessment")
    index = ids.index(previous) if previous in ids else 0
    with col_ref:
        selected = st.selectbox("Assessment record", ids, index=index, key="assessment_select")
    st.session_state.selected_assessment = selected
    detail = api.get(f"/clearances/{selected}")
    result = detail.get("result") or {}
    st.divider()
    st.subheader(f"{detail.get('campaign_reference', 'Campaign')} · {status_label(detail.get('status'))}")
    c1, c2, c3 = st.columns(3)
    for col, (label, value, note) in zip(
        [c1, c2, c3],
        [("Recommendation", result.get("recommended_decision", "—"), "Assessment recommendation"),
         ("Booked / flagged", f"{result.get('spots_booked', 0)} / {result.get('spots_breaching', 0)}", "Spots in the campaign"),
         ("Exposure", f"{float(result.get('exposure', 0)):,.0f}", "Estimated audience units")],
    ):
        with col:
            metric_card(label, value, note)
    tab_summary, tab_calls, tab_result = st.tabs(["Summary", "Model calls", "Full record"])
    with tab_summary:
        st.markdown("**Assessment request**")
        st.write(result.get("executive_request") or "No request text stored.")
        if detail.get("decision"):
            st.success(f"{detail['decision']} · decided by {result.get('decided_by', 'controller')}")
            if detail.get("decision_reason"):
                st.caption(detail["decision_reason"])
        st.markdown("**Spots that need attention**")
        dataframe(result.get("breaching_spots", []), ["spot_reference", "breach_codes"])
    with tab_calls:
        calls = api.get(f"/clearances/{selected}/calls")
        dataframe(calls.get("calls", []), ["agent_name", "model_name", "prompt_characters",
                                             "response_characters", "latency_milliseconds"])
        st.caption(f"{calls.get('call_count', 0)} calls · {calls.get('total_latency_milliseconds', 0)} ms total")
    with tab_result:
        st.json({"assessment": detail, "result": result}, expanded=False)

