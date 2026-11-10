"""Regression checks for campaign buttons that update the sidebar navigation."""

import pytest
from streamlit.testing.v1 import AppTest


@pytest.mark.parametrize("button_label", ["View campaign", "Open campaign detail"])
def test_campaign_button_callback_navigates_before_radio_rerun(button_label):
    app = AppTest.from_string(
        """
import streamlit as st
from dashboard.ui import open_campaign

st.session_state.setdefault("nav", "Overview")
st.radio("WORKSPACE", ["Overview", "Campaign detail"], key="nav")
st.button(button_label, on_click=open_campaign, args=("CLR-TEST-001",))
""".replace("button_label", repr(button_label))
    ).run()

    assert app.session_state["nav"] == "Overview"
    app.button[0].click().run()

    assert app.session_state["nav"] == "Campaign detail"
    assert app.session_state["selected_campaign"] == "CLR-TEST-001"
