"""Role-aware welcome page and next-step guide for clearance staff."""

from __future__ import annotations

import streamlit as st

from config import config
from dashboard.ui import metric_card, navigate_to, open_campaign, page_header


ROLE_GUIDES = {
    config.ROLE_CONTROLLER: {
        "summary": "You review assessment recommendations and record the final controller outcome.",
        "work": [
            "Review campaigns and spot details in the Clearance queue and Campaign detail pages.",
            "Open the Decision desk to review a pending assessment and record an outcome with a reason.",
            "Use Assessments and Audit trail to follow decisions; use Clearance chat for policy or campaign questions.",
        ],
        "focus_step": 3,
    },
    config.ROLE_EXECUTIVE: {
        "summary": "You review incoming campaigns, open assessments, and follow their progress.",
        "work": [
            "Find a campaign in the Clearance queue and inspect its booked spots and risk signals.",
            "Start an assessment from Campaign detail. The assessment records checks and a recommendation.",
            "Follow the record in Assessments. A controller records the final decision; Audit trail keeps the history.",
        ],
        "focus_step": 2,
    },
    config.ROLE_LIAISON: {
        "summary": "You help your assigned agencies understand policy and check their campaign status.",
        "work": [
            "Open Clearance chat and ask a policy question or ask for the status of a campaign from your agencies.",
            "Read the answer and any listed source documents; your recent conversation stays available on the chat page.",
            "If a campaign needs review or a decision, the clearance team handles those steps in its workspace.",
        ],
        "focus_step": 1,
    },
}


WORKFLOW = [
    ("1", "Review the campaign", "The queue groups open campaigns by exposure. Campaign detail shows booked spots and the signals behind review."),
    ("2", "Run an assessment", "An executive or controller opens an assessment from Campaign detail. The assessment checks the campaign and stores its recommendation."),
    ("3", "Record the controller outcome", "A controller reviews a pending assessment, chooses an available outcome, and records the reason. The person who opened that assessment cannot decide it."),
    ("4", "Follow the record", "Assessments shows progress and model calls. Audit trail records decisions and desk activity. Clearance chat answers policy and permitted campaign status questions."),
]


def render(api) -> None:
    auth = st.session_state.get("auth", {})
    role = auth.get("role", "Team member")
    guide = ROLE_GUIDES.get(role, {
        "summary": "Use the pages available in your workspace to continue your clearance work.",
        "work": [],
        "focus_step": 1,
    })
    display_name = auth.get("display_name", auth.get("username", "there"))
    page_access = set(auth.get("pages", []))

    page_header("YOUR CLEARANCE WORKSPACE", f"Welcome, {display_name}",
                "BreakCheck helps the clearance team review advertising campaigns, assess risks, and record decisions.")

    with st.container(border=True):
        st.subheader("Your role")
        st.markdown(f"**{role}**")
        st.write(guide["summary"])
        if role == config.ROLE_LIAISON:
            agencies = auth.get("assigned_agencies", [])
            if agencies:
                st.caption("Assigned agencies: " + ", ".join(agencies))
        readable_pages = [
            (config.PAGE_QUEUE, "Clearance queue"),
            (config.PAGE_CAMPAIGN, "Campaign detail"),
            (config.PAGE_AUDIT, "Assessments and Audit trail"),
            (config.PAGE_DECISION, "Decision desk"),
            (config.PAGE_CHAT, "Clearance chat"),
        ]
        tools = [label for required, label in readable_pages if required in page_access]
        st.caption("Available to you: " + (" · ".join(tools) if tools else "Home"))

    st.subheader("How the work moves")
    steps = st.columns(4)
    for index, (number, title, description) in enumerate(WORKFLOW):
        with steps[index]:
            with st.container(border=True):
                st.markdown(f"**{number} · {title}**")
                st.caption(description)
                if index + 1 == guide["focus_step"]:
                    st.markdown("**Your role focuses here**")

    st.subheader("Your next step")
    if role == config.ROLE_LIAISON:
        st.subheader("What you can do in this role")
        for item in guide["work"]:
            st.markdown(f"- {item}")
        st.info("Ask about a policy rule, or ask for the status of a campaign handled by one of your assigned agencies.")
        st.button("Go to Clearance chat", type="primary", on_click=navigate_to,
                  args=("Clearance chat",))
        return

    queue = api.get("/queue", params={"product_category": "All"}) or []
    assessments = api.get("/clearances") or [] if config.PAGE_AUDIT in page_access else []
    pending = [row for row in assessments if row.get("status") == config.CAMPAIGN_STATUS_PENDING]
    assessed_refs = {str(row.get("campaign_reference")) for row in assessments}
    unassessed = [row for row in queue
                  if str(row.get("campaign_reference")) not in assessed_refs]

    metric_columns = st.columns(3)
    metrics = [
        ("Open campaigns", len(queue), "Available for review"),
        ("Assessments", len(assessments), "Records in your workspace"),
        ("Pending decisions", len(pending), "Waiting for a controller"),
    ]
    for column, (label, value, note) in zip(metric_columns, metrics):
        with column:
            metric_card(label, value, note)

    if role == config.ROLE_CONTROLLER:
        if pending:
            st.info(f"There {'is' if len(pending) == 1 else 'are'} {len(pending)} pending assessment{'s' if len(pending) != 1 else ''}. Review a pending record in the Decision desk; you cannot decide an assessment you opened yourself.")
            st.button("Review pending decisions", type="primary", on_click=navigate_to,
                      args=("Decision desk",))
        elif queue:
            st.success("No assessments are waiting for a controller decision right now.")
            st.write("You can inspect the open campaign queue or follow completed records.")
            col_queue, col_records = st.columns(2)
            with col_queue:
                st.button("Review the campaign queue", type="primary", on_click=navigate_to,
                          args=("Clearance queue",))
            with col_records:
                st.button("Open assessments", on_click=navigate_to, args=("Assessments",))
        else:
            st.success("Your decision queue and campaign queue are clear.")
            st.button("Review recent records", type="primary", on_click=navigate_to,
                      args=("Assessments",))
    elif unassessed:
        st.info("Choose an open campaign to inspect. From its detail page, you can start an assessment and follow the result under Assessments.")
        references = [str(row["campaign_reference"]) for row in unassessed]
        chosen = st.selectbox("Campaign to work on", references, key="home_campaign")
        st.button("Review this campaign", type="primary", on_click=open_campaign,
                  args=(chosen,))
    elif queue and assessments:
        st.success("Every open campaign already has an assessment record.")
        st.write("Review the existing assessments to follow their status and recommendations.")
        st.button("Open assessments", type="primary", on_click=navigate_to,
                  args=("Assessments",))
    else:
        st.success("There are no open campaigns to assess right now.")
        st.button("Open the campaign queue", type="primary", on_click=navigate_to,
                  args=("Clearance queue",))

    st.divider()
    st.subheader("What you can do in this role")
    for item in guide["work"]:
        st.markdown(f"- {item}")
