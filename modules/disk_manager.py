"""Module 6b — Disk Scheduling."""
from __future__ import annotations
import json
import pandas as pd
import streamlit as st
from algorithms.disk_scheduling import fcfs, sstf, scan, c_scan
from visualizations.disk_chart import build_disk_chart


DEFAULT_REQUESTS = "98, 183, 37, 122, 14, 124, 65, 67"


def _parse_requests(text: str) -> list[int]:
    parts = [p.strip() for p in text.split(",") if p.strip()]
    try:
        return [int(p) for p in parts]
    except ValueError as exc:
        raise ValueError("Requests must be integers, comma-separated.") from exc


def render(session_state) -> None:
    st.markdown("## Disk Scheduling")
    st.caption("Compare head movement across FCFS, SSTF, SCAN, and C-SCAN.")

    c1, c2, c3 = st.columns([2, 1, 1])
    with c1:
        req_text = st.text_input("Cylinder requests", value=DEFAULT_REQUESTS)
    with c2:
        head = st.number_input("Initial head position", min_value=0, value=53, step=1)
    with c3:
        disk_size = st.number_input("Disk size (cylinders)", min_value=2, value=200, step=1)

    c1, c2 = st.columns(2)
    with c1:
        direction = st.selectbox("SCAN / C-SCAN direction",
                                 ["right", "left"], index=0)
    with c2:
        count_boundary = st.checkbox(
            "SCAN: count boundary travel",
            value=False,
            help="Include the disk boundary as an extra stop.",
        )

    if st.button("▶ Run All Four", type="primary"):
        try:
            requests = _parse_requests(req_text)
        except ValueError as exc:
            st.error(str(exc))
            return
        if not requests:
            st.error("Enter at least one request.")
            return

        try:
            session_state["disk_results"] = {
                "FCFS":  fcfs(int(head), requests, int(disk_size)),
                "SSTF":  sstf(int(head), requests, int(disk_size)),
                "SCAN":  scan(int(head), requests, int(disk_size),
                              direction=direction,
                              count_boundary=count_boundary),
                "C-SCAN": c_scan(int(head), requests, int(disk_size),
                                 direction=direction),
            }
        except ValueError as exc:
            st.error(str(exc))
            return

    results = session_state.get("disk_results")
    if not results:
        st.info("Click **Run All Four** to compute disk schedules.")
        return

    st.markdown("### Comparison")
    rows = []
    for name, r in results.items():
        rows.append({
            "Algorithm": name,
            "Service order": " → ".join(str(x) for x in r["sequence"]),
            "Total movement": r["total_movement"],
            "Average movement": r["average_movement"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    tabs = st.tabs(list(results.keys()))
    for tab, (name, r) in zip(tabs, results.items()):
        with tab:
            st.plotly_chart(
                build_disk_chart(r),
                use_container_width=True,
                key=f"disk_chart_{name}",
            )
            st.markdown("**Movement breakdown**")
            detail = pd.DataFrame({
                "From": r["sequence"][:-1],
                "To": r["sequence"][1:],
                "Distance": r["movements"],
            })
            st.dataframe(detail, use_container_width=True, hide_index=True)
            st.caption(f"Total: **{r['total_movement']}** cylinders · "
                       f"Average: **{r['average_movement']}**")

    st.download_button(
        "⬇ Download Disk Results JSON",
        data=json.dumps(
            {k: {"sequence": v["sequence"],
                 "total_movement": v["total_movement"],
                 "average_movement": v["average_movement"]}
             for k, v in results.items()},
            indent=2),
        file_name="disk_scheduling.json",
        mime="application/json",
    )