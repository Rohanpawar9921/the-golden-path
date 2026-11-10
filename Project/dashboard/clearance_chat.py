"""Grounded policy and campaign-status assistant interface."""

from __future__ import annotations

import streamlit as st

from dashboard.api_client import APIError
from dashboard.ui import api_error, page_header


def _show_sources(turn: dict) -> None:
    sources = turn.get("source_documents") or []
    if sources:
        st.caption("Sources · " + " · ".join(sources))
    if turn.get("was_refused"):
        st.caption("I could not ground this answer in the available policy or campaign information.")


def _render_turns(turns: list[dict]) -> None:
    pending_notice = st.session_state.get("_clearance_chat_notice")
    for turn in reversed(turns):
        with st.chat_message("user"):
            st.markdown(turn.get("question_text") or "")

        with st.chat_message("assistant"):
            st.markdown(turn.get("answer_text") or "No answer was returned.")
            if (pending_notice and
                    pending_notice.get("question") == turn.get("question_text") and
                    pending_notice.get("generation_mode") == "retrieval fallback"):
                st.caption(
                    "This is an excerpt selected from the matching policy documents "
                    "because the language model was unavailable."
                )
                pending_notice = None
                st.session_state.pop("_clearance_chat_notice", None)
            _show_sources(turn)


def render(api) -> None:
    st.markdown(
        """
        <style>
        section.main > div.block-container { max-width: 54rem; padding-bottom: 7rem; }
        [data-testid="stChatMessage"] { border-radius: 16px; }
        [data-testid="stChatInput"] { max-width: 54rem; margin-left: auto; margin-right: auto; }
        </style>
        """,
        unsafe_allow_html=True,
    )
    page_header(
        "CLEARANCE ASSISTANT",
        "Clearance chat",
        "Ask a policy question or check a campaign’s clearance status.",
    )
    st.caption("The assistant uses the available clearance guidance and your role’s campaign access.")

    try:
        turns = api.get("/chat/turns", params={"turn_limit": 20}) or []
    except APIError as error:
        turns = []
        api_error(error)

    if turns:
        _render_turns(turns)
    else:
        st.markdown("### How can I help?")
        st.write("Ask in your own words. I can help you understand the clearance rules or explain a campaign’s current status.")
        with st.container(border=True):
            st.markdown("**Policy guidance**")
            st.caption("For example: “What does the alcohol code say about advertising this product?”")
        with st.container(border=True):
            st.markdown("**Campaign status**")
            st.caption("For example: “Where is campaign CLR-ABC-001 in the clearance process?”")
        st.caption("Replies show the source documents when policy guidance is used. Ask a follow-up to continue the conversation.")

    prompt = st.chat_input(
        "Message the Clearance assistant…",
        key="clearance_chat_input",
        max_chars=2000,
    )
    if prompt and prompt.strip():
        try:
            answer = api.post("/chat/ask", {"question": prompt.strip()}) or {}
        except APIError as error:
            with st.chat_message("assistant"):
                api_error(error)
        else:
            if answer.get("generation_mode"):
                st.session_state["_clearance_chat_notice"] = {
                    "question": prompt.strip(),
                    "generation_mode": answer["generation_mode"],
                }
            st.rerun()
