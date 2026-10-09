"""Module 3 — Deadlock Analyzer."""
from __future__ import annotations
import json
import pandas as pd
import streamlit as st
from algorithms.bankers_algorithm import (
    SystemState, sample_state, is_safe, request_resources,
)
from visualizations.resource_graph import build_rag


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _matrix_df(procs, cols, matrix, index_label="Process"):
    return pd.DataFrame(matrix, index=procs, columns=cols).rename_axis(index_label)


def _init_state(session_state):
    if "deadlock_state" not in session_state:
        session_state["deadlock_state"] = sample_state()


# ----------------------------------------------------------------------
# Panel 1 — Banker's Algorithm
# ----------------------------------------------------------------------

def _panel_bankers(session_state) -> None:
    state: SystemState = session_state["deadlock_state"]
    procs, res = state.processes, state.resources

    st.markdown("### System State")
    st.caption("Edit allocation, maximum, or available; then run the safety check.")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Allocation**")
        alloc_df = st.data_editor(
            _matrix_df(procs, res, state.allocation),
            use_container_width=True, key="alloc_editor",
        )
    with col2:
        st.markdown("**Maximum**")
        max_df = st.data_editor(
            _matrix_df(procs, res, state.maximum),
            use_container_width=True, key="max_editor",
        )

    st.markdown("**Available**")
    avail_cols = st.columns(len(res))
    avail = []
    for j, r in enumerate(res):
        with avail_cols[j]:
            avail.append(st.number_input(
                f"Available {r}", min_value=0,
                value=int(state.available[j]), step=1, key=f"avail_{r}",
            ))

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if st.button("▶ Run Safety Check", type="primary",
                     use_container_width=True):
            session_state["deadlock_state"] = SystemState(
                processes=procs, resources=res,
                allocation=alloc_df.values.tolist(),
                maximum=max_df.values.tolist(),
                available=avail,
            )
            session_state["bankers_result"] = is_safe(session_state["deadlock_state"])
    with c2:
        if st.button("Load Sample", use_container_width=True):
            session_state["deadlock_state"] = sample_state()
            session_state.pop("bankers_result", None)
            st.rerun()
    with c3:
        st.write("")

    # Live Need matrix preview
    st.markdown("**Need = Max − Allocation**")
    need = state.need()
    st.dataframe(_matrix_df(procs, res, need), use_container_width=True)

    result = session_state.get("bankers_result")
    if not result:
        return

    st.markdown("### Safety Analysis")

    if result["safe"]:
        st.success(f"Safe state. Safe sequence: **{' → '.join(result['safe_sequence'])}**")
    else:
        st.error("Unsafe state — no safe sequence exists for the current allocation.")

    rows = []
    for s in result["steps"]:
        rows.append({
            "Step": s["step"],
            "Work Before": str(s["work_before"]),
            "Selected": s["candidate"] or "—",
            "Need Row": str(s["need_row"]) if s["need_row"] else "—",
            "Work After": str(s["work_after"]),
            "Note": s["note"],
        })
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    # Export
    snapshot = {
        "state": state.to_dict(),
        "safe": result["safe"],
        "safe_sequence": result["safe_sequence"],
        "steps": result["steps"],
    }
    st.download_button(
        "⬇ Download Safety JSON",
        data=json.dumps(snapshot, indent=2),
        file_name="bankers_safety.json",
        mime="application/json",
    )


# ----------------------------------------------------------------------
# Panel 2 — Resource request
# ----------------------------------------------------------------------

def _panel_request(session_state) -> None:
    state: SystemState = session_state["deadlock_state"]
    procs, res = state.processes, state.resources

    st.markdown("### Resource Request Simulation")
    st.caption("Check whether a request can be safely granted. Rejected "
               "requests are rolled back.")

    c1, c2 = st.columns([1, 3])
    with c1:
        pid = st.selectbox("Requesting process", procs, key="req_pid")
    with c2:
        req_cols = st.columns(len(res))
        request: list[int] = []
        for j, r in enumerate(res):
            with req_cols[j]:
                request.append(st.number_input(
                    f"Request {r}", min_value=0, value=0, step=1,
                    key=f"req_{r}",
                ))

    need = state.need()
    i = procs.index(pid)
    st.caption(f"{pid}'s Need = {need[i]}   |   Available = {state.available}")

    if st.button("▶ Submit Request", type="primary", key="submit_req"):
        outcome = request_resources(state, pid, request)
        session_state["request_result"] = outcome

    outcome = session_state.get("request_result")
    if not outcome:
        return

    if outcome["granted"]:
        st.success(outcome["reason"])
        # Commit the allocation to the live state
        session_state["deadlock_state"] = SystemState(
            processes=outcome["after"]["processes"],
            resources=outcome["after"]["resources"],
            allocation=outcome["after"]["allocation"],
            maximum=outcome["after"]["maximum"],
            available=outcome["after"]["available"],
        )
    else:
        st.error(outcome["reason"])
        st.info("State unchanged (rolled back to the pre-request snapshot).")

    with st.expander("Show before / after state", expanded=outcome["granted"]):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Before**")
            st.json(outcome["before"])
        with c2:
            st.markdown("**After**")
            st.json(outcome["after"])

    if outcome.get("safe_check"):
        st.markdown("**Safety trace for the tentative allocation:**")
        rows = [{
            "Step": s["step"],
            "Work Before": str(s["work_before"]),
            "Selected": s["candidate"] or "—",
            "Work After": str(s["work_after"]),
        } for s in outcome["safe_check"]["steps"]]
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)


# ----------------------------------------------------------------------
# Panel 3 — Resource Allocation Graph
# ----------------------------------------------------------------------

def _panel_rag(session_state) -> None:
    state: SystemState = session_state["deadlock_state"]

    st.markdown("### Resource Allocation Graph")
    st.caption("Solid arrows (resource → process) are allocations. "
               "Dashed amber arrows (process → resource) are requests.")

    st.markdown("**Outstanding Requests** (process → resource)")
    requests_df = st.data_editor(
        _matrix_df(state.processes, state.resources,
                   [[0] * len(state.resources) for _ in state.processes]),
        use_container_width=True, key="rag_req_editor",
    )

    fig = build_rag(
        processes=state.processes,
        resources=state.resources,
        allocation=state.allocation,
        requests=requests_df.values.tolist(),
    )
    st.plotly_chart(fig, use_container_width=True)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def render(session_state) -> None:
    st.markdown("## Deadlock Analyzer")
    st.caption("Banker's Algorithm, safety checks, resource requests, and "
               "resource-allocation graph visualization.")

    _init_state(session_state)

    tab1, tab2, tab3 = st.tabs([
        "Banker's Algorithm",
        "Resource Request",
        "Resource Allocation Graph",
    ])
    with tab1:
        _panel_bankers(session_state)
    with tab2:
        _panel_request(session_state)
    with tab3:
        _panel_rag(session_state)