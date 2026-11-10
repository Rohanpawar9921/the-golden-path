"""Search, filter, and route campaigns from the open clearance queue."""

import streamlit as st

from dashboard.ui import dataframe, open_campaign, page_header


def render(api) -> None:
    page_header("INTAKE", "Clearance queue", "Review incoming campaigns, spot counts, and predicted exposure.")
    rows = api.get("/queue", params={"product_category": "All"}) or []
    if not rows:
        st.info("The queue is empty.")
        return

    categories = ["All"] + sorted({str(row.get("product_category", "Other")) for row in rows})
    col_filter, col_search = st.columns([1, 2])
    with col_filter:
        category = st.selectbox("Product category", categories)
    with col_search:
        search = st.text_input("Find a campaign", placeholder="Campaign reference")
    filtered = [row for row in rows if (category == "All" or row.get("product_category") == category)
                and search.strip().lower() in str(row.get("campaign_reference", "")).lower()]
    st.caption(f"Showing {len(filtered)} of {len(rows)} campaigns · sorted by exposure")
    dataframe(filtered, ["queue_position", "campaign_reference", "product_category", "spots_booked",
                         "spots_breaching", "exposure", "amendment_score", "amendment_band",
                         "first_transmission"])
    if filtered:
        refs = [str(row["campaign_reference"]) for row in filtered]
        previous = st.session_state.get("selected_campaign")
        index = refs.index(previous) if previous in refs else 0
        chosen = st.selectbox("Campaign to inspect", refs, index=index, key="queue_campaign")
        st.button("Open campaign detail", type="primary", on_click=open_campaign, args=(chosen,))

