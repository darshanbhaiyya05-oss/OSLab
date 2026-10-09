"""Module 4 — Memory Management (allocation, paging, segmentation)."""
from __future__ import annotations
import json
import pandas as pd
import streamlit as st
from algorithms.memory_allocation import first_fit, best_fit, worst_fit, STRATEGIES
from algorithms.paging import translate_address
from algorithms.segmentation import translate_segment
from visualizations.memory_map import build_memory_map


# ----------------------------------------------------------------------
# Defaults
# ----------------------------------------------------------------------

DEFAULT_FREE_SIZES = [100, 500, 200, 300]
DEFAULT_REQUESTS = [
    {"pid": 1, "name": "P1", "size": 180},
    {"pid": 2, "name": "P2", "size": 120},
    {"pid": 3, "name": "P3", "size": 90},
]
DEFAULT_PAGE_SIZE = 1024
DEFAULT_PAGE_TABLE = {0: 3, 1: 4, 2: 5, 3: 6}
DEFAULT_SEGMENT_TABLE = {
    0: {"name": "code",  "base": 1000, "limit": 500},
    1: {"name": "data",  "base": 2000, "limit": 800},
    2: {"name": "stack", "base": 5000, "limit": 300},
}


# ----------------------------------------------------------------------
# Panel 1 — Contiguous allocation
# ----------------------------------------------------------------------

def _panel_contiguous(session_state) -> None:
    st.markdown("### Contiguous Allocation")
    st.caption("Compare First Fit, Best Fit, and Worst Fit on the same workload.")

    c1, c2 = st.columns([1, 2])
    with c1:
        sizes_text = st.text_input(
            "Free block sizes (KB, comma-separated)",
            value=", ".join(str(s) for s in DEFAULT_FREE_SIZES),
            key="free_sizes_input",
        )
    with c2:
        st.write("")
        st.caption("Requests (pid, name, size in KB):")

    req_df = st.data_editor(
        pd.DataFrame(session_state.get("mem_requests", DEFAULT_REQUESTS)),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "pid":  st.column_config.NumberColumn("PID", min_value=1, step=1),
            "name": st.column_config.TextColumn("Name"),
            "size": st.column_config.NumberColumn("Size (KB)", min_value=1, step=10),
        },
        key="mem_req_editor",
    )
    session_state["mem_requests"] = req_df.to_dict("records")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("▶ Run All Three", type="primary", use_container_width=True):
            try:
                free_sizes = [int(x.strip()) for x in sizes_text.split(",") if x.strip()]
            except ValueError:
                st.error("Free block sizes must be integers separated by commas.")
                return
            if not free_sizes:
                st.error("Enter at least one free block size.")
                return

            requests = session_state["mem_requests"]
            session_state["mem_results"] = {
                "First Fit": first_fit(free_sizes, requests),
                "Best Fit":  best_fit(free_sizes, requests),
                "Worst Fit": worst_fit(free_sizes, requests),
            }
    with c2:
        if st.button("Reset", use_container_width=True):
            session_state["mem_requests"] = list(DEFAULT_REQUESTS)
            session_state.pop("mem_results", None)
            st.rerun()
    with c3:
        st.write("")

    results = session_state.get("mem_results")
    if not results:
        st.info("Click **Run All Three** to compare the strategies.")
        return

    # Summary
    st.markdown("#### Strategy Comparison")
    rows = []
    for name, r in results.items():
        rows.append({
            "Strategy": name,
            "Allocations OK": sum(1 for a in r["allocations"] if a["success"]),
            "Rejected": sum(1 for a in r["allocations"] if not a["success"]),
            "Total free (KB)": r["total_free"],
            "Largest free (KB)": r["largest_free"],
            "External frag (KB)": r["external_fragmentation"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Per-strategy detail
    tabs = st.tabs(list(results.keys()))
    for tab, (name, r) in zip(tabs, results.items()):
        with tab:
            st.markdown(f"**{name} — Initial Memory**")
            st.plotly_chart(
                build_memory_map(r["initial_blocks"]),
                use_container_width=True,
                key=f"mem_initial_{name}",
            )

            step_idx = st.slider(
                "Step", 0, len(r["steps"]),
                value=len(r["steps"]),
                key=f"mem_step_{name}",
                help="0 = initial; N = after the Nth allocation.",
            )
            if step_idx == 0:
                blocks = r["initial_blocks"]
            else:
                blocks = r["steps"][step_idx - 1]["blocks_after"]

            st.markdown(f"**Memory after step {step_idx}**")
            st.plotly_chart(
                build_memory_map(blocks),
                use_container_width=True,
                key=f"mem_after_{name}_{step_idx}",
            )

            st.markdown("**Allocation records**")
            st.dataframe(pd.DataFrame(r["allocations"]),
                         use_container_width=True, hide_index=True)

    st.download_button(
        "⬇ Download Results JSON",
        data=json.dumps(
            {k: {"allocations": v["allocations"],
                 "total_free": v["total_free"],
                 "largest_free": v["largest_free"]}
             for k, v in results.items()},
            indent=2),
        file_name="memory_allocation.json",
        mime="application/json",
    )


# ----------------------------------------------------------------------
# Panel 2 — Paging
# ----------------------------------------------------------------------

def _panel_paging(session_state) -> None:
    st.markdown("### Paging — Address Translation")
    st.caption("Virtual → Physical translation using a page table.")

    c1, c2 = st.columns([1, 1])
    with c1:
        page_size = st.number_input(
            "Page size (bytes)", min_value=1, value=DEFAULT_PAGE_SIZE, step=1,
        )
    with c2:
        virtual = st.number_input(
            "Virtual address (bytes)", min_value=0, value=2500, step=1,
        )

    st.markdown("**Page Table** (page → frame; use blank / -1 to mark missing)")
    pt_rows = [{"page": p, "frame": f} for p, f in DEFAULT_PAGE_TABLE.items()]
    pt_df = st.data_editor(
        pd.DataFrame(pt_rows),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "page":  st.column_config.NumberColumn("Page", min_value=0, step=1),
            "frame": st.column_config.NumberColumn("Frame", min_value=0, step=1),
        },
        key="page_table_editor",
    )

    try:
        page_table = {int(r["page"]): int(r["frame"])
                      for r in pt_df.to_dict("records")
                      if r.get("page") is not None and r.get("frame") is not None}
    except (TypeError, ValueError):
        st.error("Page table contains invalid entries.")
        return

    if st.button("▶ Translate", type="primary", key="translate_page"):
        try:
            out = translate_address(int(virtual), int(page_size), page_table)
            session_state["paging_result"] = out
        except ValueError as exc:
            st.error(str(exc))

    out = session_state.get("paging_result")
    if not out:
        return

    if out["valid"]:
        st.success(out["note"])
    else:
        st.error(out["note"])

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Page number", out["page_number"])
    c2.metric("Offset", out["offset"])
    c3.metric("Frame", out["frame_number"] if out["frame_number"] is not None else "—")
    c4.metric("Physical address",
              out["physical_address"] if out["physical_address"] is not None else "—")


# ----------------------------------------------------------------------
# Panel 3 — Segmentation
# ----------------------------------------------------------------------

def _panel_segmentation(session_state) -> None:
    st.markdown("### Segmentation — Address Translation")
    st.caption("Segment + offset → physical address.")

    st.markdown("**Segment Table**")
    seg_rows = [{"segment": s, **v} for s, v in DEFAULT_SEGMENT_TABLE.items()]
    seg_df = st.data_editor(
        pd.DataFrame(seg_rows),
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "segment": st.column_config.NumberColumn("Segment", min_value=0, step=1),
            "name":    st.column_config.TextColumn("Name"),
            "base":    st.column_config.NumberColumn("Base", min_value=0, step=100),
            "limit":   st.column_config.NumberColumn("Limit", min_value=1, step=100),
        },
        key="segment_editor",
    )
    try:
        segment_table = {
            int(r["segment"]): {"name": str(r["name"]),
                                "base": int(r["base"]),
                                "limit": int(r["limit"])}
            for r in seg_df.to_dict("records")
            if r.get("segment") is not None
        }
    except (TypeError, ValueError):
        st.error("Segment table contains invalid entries.")
        return

    c1, c2 = st.columns(2)
    with c1:
        seg_num = st.number_input("Segment number", min_value=0, value=1, step=1)
    with c2:
        offset = st.number_input("Offset (bytes)", min_value=0, value=100, step=1)

    if st.button("▶ Translate", type="primary", key="translate_seg"):
        session_state["segmentation_result"] = translate_segment(
            int(seg_num), int(offset), segment_table)

    out = session_state.get("segmentation_result")
    if not out:
        return

    if out["valid"]:
        st.success(out["note"])
        st.metric("Physical address", out["physical_address"])
    else:
        st.error(out["note"])


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def render(session_state) -> None:
    st.markdown("## Memory Management")
    st.caption("Contiguous allocation, paging, and segmentation.")
    tab1, tab2, tab3 = st.tabs(["Contiguous Allocation", "Paging", "Segmentation"])
    with tab1:
        _panel_contiguous(session_state)
    with tab2:
        _panel_paging(session_state)
    with tab3:
        _panel_segmentation(session_state)