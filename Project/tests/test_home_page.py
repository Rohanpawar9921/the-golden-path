"""Role-aware home page rendering checks using representative live-work data."""

import pytest
from streamlit.testing.v1 import AppTest

from config import config


@pytest.mark.parametrize(
    ("role", "pages", "expected_button"),
    [
        (config.ROLE_CONTROLLER, config.ROLE_PAGE_ACCESS[config.ROLE_CONTROLLER],
         "Review pending decisions"),
        (config.ROLE_EXECUTIVE, config.ROLE_PAGE_ACCESS[config.ROLE_EXECUTIVE],
         "Review this campaign"),
        (config.ROLE_LIAISON, config.ROLE_PAGE_ACCESS[config.ROLE_LIAISON],
         "Go to Clearance chat"),
    ],
)
def test_home_explains_role_and_shows_a_role_appropriate_next_action(
        role, pages, expected_button):
    app = AppTest.from_string(
        f"""
import streamlit as st
from dashboard.home import render

st.session_state.auth = {{
    "username": "demo-user",
    "display_name": "Demo User",
    "role": {role!r},
    "pages": {pages!r},
    "assigned_agencies": ["QSC", "HWK"],
}}

class FakeAPI:
    def get(self, path, **kwargs):
        if path == "/queue":
            return [{{"campaign_reference": "CLR-QSC-001", "spots_booked": 4}}]
        if path == "/clearances":
            return [{{"assessment_id": "ASM-1", "campaign_reference": "CLR-QSC-002",
                     "status": "PENDING_DECISION"}}]
        return []

render(FakeAPI())
"""
    ).run()

    assert not app.exception
    assert any(button.label == expected_button for button in app.button)
