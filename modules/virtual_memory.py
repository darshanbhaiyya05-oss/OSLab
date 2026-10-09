"""Module 5 — Virtual Memory (page replacement)."""
from __future__ import annotations
import json
import pandas as pd
import streamlit as st
from algorithms.page_replacement import fifo, lru, optimal, ALGORITHMS


DEFAULT_REFERENCE = "1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5"
DEFAULT_FRAMES = 3


def _parse_reference(text: str) -> list[int]:
    parts = [p.strip() for p in text.split(",") if p.strip()]
    try:
        return [int(p) for p in parts]
    except ValueError as exc:
        raise ValueError("Reference string must be integers separated by commas.") from exc


def _frame_table_df(result: dict) -> pd.DataFrame:
    """Build a step-by-step frame table."""
    num_frames = result["num_frames"]
    rows = []
    for s in result["steps"]:
        row = {
            "Step": s["step"],
            "Reference": s["referenced_page"],
        }
        for i in range(num_frames):
            row[f"Frame {i+1}"] = s["frames"][i] if s["frames"][i] is not None else "—"
        row["Result"] = s["result"]
        row["Evicted"] = s["evicted"] if s["evicted"] is not None else "—"
        rows.append(row)
    return pd.DataFrame(rows)


def render(session_state) -> None:
    st.markdown("## Virtual Memory — Page Replacement")
    st.caption("Compare FIFO, LRU, and Optimal on the same reference string.")

    c1, c2 = st.columns([3, 1])
    with c1:
        ref_text = st.text_input("Reference string (integers, comma-separated)",
                                 value=DEFAULT_REFERENCE)
    with c2:
        frames = st.number_input("Number of frames", min_value=1, value=DEFAULT_FRAMES, step=1)

    c1, c2 = st.columns([1, 3])
    with c1:
        run = st.button("▶ Run All Three", type="primary", use_container_width=True)
    with c2:
        st.write("")

    if run:
        try:
            reference = _parse_reference(ref_text)
        except ValueError as exc:
            st.error(str(exc))
            return
        if not reference:
            st.error("Reference string cannot be empty.")
            return

        session_state["vm_results"] = {
            "FIFO":    fifo(reference, int(frames)),
            "LRU":     lru(reference, int(frames)),
            "Optimal": optimal(reference, int(frames)),
        }

    results = session_state.get("vm_results")
    if not results:
        st.info("Click **Run All Three** to compare page replacement algorithms.")
        return

    # Summary
    st.markdown("### Comparison")
    rows = []
    for name, r in results.items():
        rows.append({
            "Algorithm": name,
            "Frames": r["num_frames"],
            "References": len(r["reference_string"]),
            "Faults": r["total_faults"],
            "Hits": r["total_hits"],
            "Fault rate %": r["fault_rate"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Per-algorithm tables
    tabs = st.tabs(list(results.keys()))
    for tab, (name, r) in zip(tabs, results.items()):
        with tab:
            st.markdown(f"**{name}** — total faults: **{r['total_faults']}**, "
                        f"hits: **{r['total_hits']}**")
            df = _frame_table_df(r)
            st.dataframe(df, use_container_width=True, hide_index=True)

    st.download_button(
        "⬇ Download Comparison JSON",
        data=json.dumps(
            {k: {"algorithm": v["algorithm"],
                 "total_faults": v["total_faults"],
                 "total_hits": v["total_hits"],
                 "fault_rate": v["fault_rate"]}
             for k, v in results.items()},
            indent=2),
        file_name="page_replacement.json",
        mime="application/json",
    )