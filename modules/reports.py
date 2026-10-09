"""Reports page — summarises the last simulation in the session."""
from __future__ import annotations
import json
import streamlit as st


def render(session_state) -> None:
    st.markdown("## Reports")
    st.caption("Summary of the most recent simulation, plus session exports.")

    last = session_state.get("oslab", {}).get("last_simulation")
    if not last:
        st.info("Run any module first — a summary will appear here.")
    else:
        st.markdown(f"### Last simulation: **{last['module']}**")
        st.json(last["result"], expanded=False)

    st.markdown("### Session Snapshot")
    oslab = session_state.get("oslab", {})
    procs = oslab.get("processes", [])
    if procs:
        st.markdown(f"**Processes tracked:** {len(procs)}")
        st.dataframe([p.to_dict() for p in procs], use_container_width=True)

    log = oslab.get("event_log")
    if log:
        events = log.render_lines()
        if events:
            st.markdown("**Recent events**")
            st.code("\n".join(events[-15:]), language="text")

    st.download_button(
        "⬇ Download Session Snapshot (JSON)",
        data=json.dumps({
            "processes": [p.to_dict() for p in procs],
            "last_simulation": last,
        }, default=str, indent=2) if last else "{}",
        file_name="oslab_session.json",
        mime="application/json",
    )