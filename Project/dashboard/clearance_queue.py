"""BreakCheck multipage Streamlit application entry point."""

from __future__ import annotations

import streamlit as st

from dashboard.api_client import APIError, BreakCheckAPI, DEFAULT_API_URL
from dashboard.ui import api_error, apply_theme
from config import config


st.set_page_config(
    page_title="BreakCheck | Clearance desk",
    page_icon="B",
    layout="wide",
    initial_sidebar_state="expanded",
)
apply_theme()

PAGES = {
    "Home": None,
    "Clearance queue": config.PAGE_QUEUE,
    "Campaign detail": config.PAGE_CAMPAIGN,
    "Assessments": config.PAGE_AUDIT,
    "Decision desk": config.PAGE_DECISION,
    "Audit trail": config.PAGE_AUDIT,
    "Clearance chat": config.PAGE_CHAT,
}


def show_login() -> None:
    st.sidebar.markdown("<h2 style='color:#c7f36b'>BREAKCHECK</h2>", unsafe_allow_html=True)
    st.sidebar.caption("Clearance operations workspace")
    st.sidebar.divider()
    api_url = st.sidebar.text_input("API address", value=st.session_state.get("api_url", DEFAULT_API_URL))
    st.session_state.api_url = api_url.rstrip("/")

    left, center, right = st.columns([1, 1.05, 1])
    with center:
        st.write("")
        st.write("")
        st.markdown("<p class='eyebrow'>HARBOURLIGHT • ADVERTISING CLEARANCE</p>", unsafe_allow_html=True)
        st.markdown("<h1 class='hero-title' style='font-size:2.8rem'>Clearance,\nwith clarity.</h1>", unsafe_allow_html=True)
        st.markdown("<p class='hero-copy'>One calm workspace for campaign review, decisions, and audit.</p>", unsafe_allow_html=True)
        st.write("")
        with st.form("login_form", clear_on_submit=False):
            st.subheader("Sign in")
            username = st.text_input("Username", placeholder="Your desk username")
            password = st.text_input("Password", type="password", placeholder="Your password")
            submitted = st.form_submit_button("Enter workspace", type="primary", width="stretch")
        if submitted:
            try:
                user = BreakCheckAPI(st.session_state.api_url).sign_in(username.strip(), password)
                st.session_state.auth = user
                st.session_state.nav = "Home"
                st.rerun()
            except APIError as error:
                api_error(error)
        with st.expander("Local demo accounts"):
            st.caption("Controller: priya / owen / grace  •  password 11111111")
            st.caption("Executive: tom / aisha / daniel  •  password 22222222")
            st.caption("Agency liaison: lucy / ben / sofia  •  password 33333333")
    with left:
        st.write("")
    with right:
        st.write("")


def show_workspace() -> None:
    auth = st.session_state.auth
    api_url = st.session_state.get("api_url", DEFAULT_API_URL)
    api = BreakCheckAPI(api_url, auth.get("session_token"))

    with st.sidebar:
        st.markdown("<h2 style='color:#c7f36b; letter-spacing:.08em'>BREAKCHECK</h2>", unsafe_allow_html=True)
        st.caption("CLEARANCE OPERATIONS")
        st.divider()
        st.markdown(f"**{auth.get('display_name', auth.get('username', 'User'))}**")
        st.caption(auth.get("role", "Team member"))
        st.caption(f"API · {api_url}")
        allowed = set(auth.get("pages", []))
        available = [name for name, required_page in PAGES.items()
                     if required_page is None or required_page in allowed]
        if not available:
            available = ["Home"]
        if st.session_state.get("nav") not in available:
            st.session_state.nav = available[0]
        selected = st.radio("WORKSPACE", available, key="nav", label_visibility="collapsed")
        st.divider()
        if st.button("Sign out", width="stretch"):
            try:
                api.sign_out()
            except APIError:
                pass
            st.session_state.pop("auth", None)
            st.session_state.pop("selected_campaign", None)
            st.session_state.pop("selected_assessment", None)
            st.rerun()

    if selected == "Home":
        from dashboard.home import render
    elif selected == "Clearance queue":
        from dashboard.queue_page import render
    elif selected == "Campaign detail":
        from dashboard.campaign_detail import render
    elif selected == "Assessments":
        from dashboard.assessment_page import render
    elif selected == "Decision desk":
        from dashboard.decision_queue import render
    elif selected == "Audit trail":
        from dashboard.audit_trail import render
    else:
        from dashboard.clearance_chat import render

    try:
        render(api)
    except APIError as error:
        api_error(error)
    except Exception as error:
        st.error("This page could not be loaded.")
        st.caption(str(error))


if "api_url" not in st.session_state:
    st.session_state.api_url = DEFAULT_API_URL

if "auth" not in st.session_state:
    show_login()
else:
    show_workspace()
