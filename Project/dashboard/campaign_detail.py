"""Campaign profile, spot checks, and assessment initiation."""

import streamlit as st

from dashboard.ui import dataframe, metric_card, page_header


def render(api) -> None:
    page_header("CAMPAIGN REVIEW", "Campaign detail", "Inspect the booked spots and supporting risk signals before assessment.")
    queue = api.get("/queue", params={"product_category": "All"}) or []
    if not queue:
        st.info("There are no campaigns to inspect.")
        return
    refs = [str(row["campaign_reference"]) for row in queue]
    previous = st.session_state.get("selected_campaign")
    index = refs.index(previous) if previous in refs else 0
    reference = st.selectbox("Campaign reference", refs, index=index, key="detail_campaign")
    st.session_state.selected_campaign = reference
    detail = api.get(f"/queue/{reference}")
    summary = detail.get("summary", {})
    stats = st.columns(4)
    items = [
        ("Booked spots", summary.get("spots_booked", 0), detail.get("product_category", "")),
        ("Flagged spots", summary.get("spots_breaching", 0), "Require controller review"),
        ("Exposure", f"{float(detail.get('exposure', 0)):,.0f}", "Estimated audience units"),
        ("Amendment signal", detail.get("amendment", {}).get("amendment_band", "—"),
         f"Score {float(detail.get('amendment', {}).get('amendment_score', 0)):.2f}"),
    ]
    for col, (label, value, note) in zip(stats, items):
        with col:
            metric_card(label, value, note)

    col_a, col_b = st.columns([1.2, 1])
    with col_a:
        st.subheader("Booked spot checks")
        dataframe(detail.get("spot_results", []), ["spot_reference", "breach_codes"])
    with col_b:
        st.subheader("Assessment snapshot")
        st.markdown(f"**First transmission**  \n{detail.get('first_transmission', {}).get('broadcast_day', '—')} · {detail.get('first_transmission', {}).get('break_time', '—')}")
        st.markdown(f"**Issue signal**  \n{detail.get('issue', {}).get('issue_category', '—')}")
        st.markdown(f"**Code document**  \n{detail.get('code_rules', {}).get('document_name', '—')}")
        st.markdown(f"**Open outcomes**  \n{', '.join(summary.get('decisions_open', [])) or '—'}")

    st.write("")
    with st.form("assessment_form"):
        st.subheader("Open an assessment")
        request = st.text_area(
            "Executive request",
            value="Check every booked spot against the category code and tell me whether the copy can be cleared.",
            help="Describe what you want the assessment to check.",
        )
        submitted = st.form_submit_button("Start assessment", type="primary")
    if submitted:
        if len(request.strip()) < 5:
            st.error("Add a little more detail to the request (at least five characters).")
        else:
            result = api.post("/assessments", {"campaign_reference": reference,
                                                "executive_request": request.strip()})
            st.session_state.selected_assessment = result.get("assessment_id")
            st.success(f"Assessment opened · {result.get('assessment_id')} · {result.get('status')}")
            st.caption("You can review the assessment and its recorded model calls on the Assessments page.")
