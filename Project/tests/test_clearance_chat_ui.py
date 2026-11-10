"""Rendering checks for the conversation-style clearance assistant."""

from streamlit.testing.v1 import AppTest


def test_clearance_chat_shows_welcome_and_chat_input_when_conversation_is_empty():
    app = AppTest.from_string(
        """
import streamlit as st
from dashboard.clearance_chat import render

class FakeAPI:
    def get(self, path, **kwargs):
        assert path == "/chat/turns"
        assert kwargs["params"]["turn_limit"] == 20
        return []

render(FakeAPI())
"""
    ).run()

    assert not app.exception
    assert any("Clearance chat" in item.value for item in app.markdown)
    assert any("How can I help?" in item.value for item in app.markdown)
    assert any("Policy guidance" in item.value for item in app.markdown)


def test_clearance_chat_renders_saved_messages_and_source_documents():
    app = AppTest.from_string(
        """
import streamlit as st
from dashboard.clearance_chat import render

class FakeAPI:
    def get(self, path, **kwargs):
        return [{
            "question_text": "What does the alcohol code require?",
            "answer_text": "The guidance requires a responsible presentation.",
            "source_documents": ["Alcohol Code.pdf"],
            "was_refused": False,
        }]

render(FakeAPI())
"""
    ).run()

    assert not app.exception
    rendered_markdown = "\n".join(item.value for item in app.markdown)
    rendered_captions = "\n".join(item.value for item in app.caption)
    assert "What does the alcohol code require?" in rendered_markdown
    assert "responsible presentation" in rendered_markdown
    assert "Alcohol Code.pdf" in rendered_captions


def test_clearance_chat_submits_to_existing_api_and_renders_the_returned_turn():
    app = AppTest.from_string(
        """
import streamlit as st
from dashboard.clearance_chat import render

class FakeAPI:
    def get(self, path, **kwargs):
        return st.session_state.get("_fake_turns", [])

    def post(self, path, body):
        assert path == "/chat/ask"
        st.session_state["_fake_posted_question"] = body["question"]
        st.session_state["_fake_turns"] = [{
            "question_text": body["question"],
            "answer_text": "The guidance calls for a clear campaign review.",
            "source_documents": ["Campaign Guidance.pdf"],
            "was_refused": False,
        }]
        return {"generation_mode": "gemini"}

render(FakeAPI())
"""
    ).run()

    app.chat_input[0].set_value("How should I review this campaign?").run()

    assert not app.exception
    assert app.session_state["_fake_posted_question"] == "How should I review this campaign?"
    rendered_markdown = "\n".join(item.value for item in app.markdown)
    assert "How should I review this campaign?" in rendered_markdown
    assert "clear campaign review" in rendered_markdown
