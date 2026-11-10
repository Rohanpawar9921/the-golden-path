"""Audit events and organization-wide chat history."""

import json

import streamlit as st

from dashboard.ui import dataframe, page_header


def render(api) -> None:
    page_header("GOVERNANCE", "Audit trail", "A searchable view of recorded decisions and desk activity.")
    tab_events, tab_chat = st.tabs(["Audit events", "Chat activity"])
    with tab_events:
        limit = st.select_slider("Recent events", options=[25, 50, 100, 200], value=50)
        rows = api.get("/audit", params={"limit": limit}) or []
        visible = [{**row, "details": json.dumps(row.get("details") or {}, ensure_ascii=False)} for row in rows]
        dataframe(visible, ["created_at", "actor", "action", "campaign_reference", "details"])
        st.caption(f"{len(rows)} event(s) returned")
    with tab_chat:
        turns = api.get("/audit/chat-turns", params={"turn_limit": 100}) or []
        dataframe(turns, ["turn_id", "username", "question_text", "question_type",
                          "was_refused", "source_documents"])
        st.caption("Chat history is visible here to authorized clearance staff.")
