"""Shared visual components and page helpers for the Streamlit dashboard."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from dashboard.api_client import APIError


def open_campaign(reference: str) -> None:
    """Select a campaign and navigate before Streamlit rebuilds the sidebar radio."""
    st.session_state.selected_campaign = reference
    st.session_state.nav = "Campaign detail"


def navigate_to(page: str) -> None:
    """Change the sidebar destination from a button callback."""
    st.session_state.nav = page


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
        :root { --ink:#17221f; --muted:#68736d; --paper:#f4f5f0; --line:#dfe4dc;
                --green:#c7f36b; --forest:#123e32; --orange:#f0a169; }
        html, body, [class*="css"] { font-family:'Manrope', sans-serif; }
        .stApp { background:var(--paper); color:var(--ink); }
        [data-testid="stSidebar"] { background:#142d28; }
        [data-testid="stSidebar"] * { color:#eef3e9; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label { padding:7px 10px; border-radius:9px; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:#23483e; }
        [data-testid="stSidebar"] hr { border-color:#34554b; }
        .eyebrow { color:#5b7067; text-transform:uppercase; letter-spacing:.16em;
                   font-size:.72rem; font-weight:800; margin:0 0 .35rem 0; }
        .hero-title { font-size:2.35rem; line-height:1.08; letter-spacing:-.055em;
                      font-weight:800; color:var(--ink); margin:0; }
        .hero-copy { color:var(--muted); font-size:.98rem; margin-top:.55rem; }
        .metric-card { background:#fff; border:1px solid var(--line); border-radius:16px;
                       padding:18px 20px; min-height:112px; }
        .metric-label { color:#68736d; font-size:.78rem; font-weight:700; text-transform:uppercase;
                        letter-spacing:.08em; }
        .metric-value { color:var(--ink); font-size:1.8rem; font-weight:800; letter-spacing:-.04em;
                        margin-top:7px; }
        .metric-note { color:#78827d; font-size:.78rem; margin-top:2px; }
        .panel { background:#fff; border:1px solid var(--line); border-radius:16px;
                 padding:20px 22px; }
        .status-chip { display:inline-block; background:#e6f4d2; color:#315b26; border-radius:999px;
                       padding:5px 10px; font-size:.75rem; font-weight:800; }
        div[data-testid="stDataFrame"] { border:1px solid var(--line); border-radius:13px; overflow:hidden; }
        div.stButton > button { border-radius:10px; font-weight:700; min-height:42px; }
        div.stButton > button[kind="primary"] { background:#193f34; border:1px solid #193f34; }
        div.stButton > button[kind="primary"]:hover { background:#285c4b; border-color:#285c4b; }
        div[data-testid="stForm"] { background:#fff; border:1px solid var(--line); border-radius:14px; padding:20px; }
        .stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] { border-radius:9px; }
        .small-note { color:var(--muted); font-size:.82rem; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def page_header(kicker: str, title: str, description: str) -> None:
    st.markdown(
        f'<p class="eyebrow">{kicker}</p><h1 class="hero-title">{title}</h1>'
        f'<p class="hero-copy">{description}</p>',
        unsafe_allow_html=True,
    )
    st.write("")


def metric_card(label: str, value: Any, note: str = "") -> None:
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{label}</div>'
        f'<div class="metric-value">{value}</div><div class="metric-note">{note}</div></div>',
        unsafe_allow_html=True,
    )


def api_error(error: APIError) -> None:
    if error.status_code == 401:
        st.error("Your session expired. Sign out and sign in again.")
    elif error.status_code == 403:
        st.error("Your account does not have permission for this action.")
    else:
        st.error(str(error))


def dataframe(rows: list[dict[str, Any]], columns: list[str] | None = None) -> None:
    if not rows:
        st.info("Nothing to show yet.")
        return
    frame = pd.DataFrame(rows)
    if columns:
        columns = [column for column in columns if column in frame.columns]
        frame = frame[columns]
    st.dataframe(frame, width="stretch", hide_index=True)


def status_label(status: str | None) -> str:
    return (status or "UNKNOWN").replace("_", " ").title()
