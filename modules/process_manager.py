"""Module 1 — Process Management: PCB, state transitions, live table."""
from __future__ import annotations
import json
import pandas as pd
import streamlit as st
from core.process import Process, ProcessState, VALID_TRANSITIONS
from core.validation import ValidationError, validate_process_fields
from core.system_state import get_state


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

STATE_BADGE = {
    ProcessState.NEW.value:        "🆕 NEW",
    ProcessState.READY.value:      "🔵 READY",
    ProcessState.RUNNING.value:    "🟢 RUNNING",
    ProcessState.WAITING.value:    "🟡 WAITING",
    ProcessState.TERMINATED.value: "🟣 TERMINATED",
}


def _processes_df(procs: list[Process]) -> pd.DataFrame:
    rows = []
    for p in procs:
        rows.append({
            "PID": p.pid,
            "Name": p.name,
            "State": STATE_BADGE.get(p.state.value, p.state.value),
            "Arrival": p.arrival_time,
            "Burst": p.burst_time,
            "Remaining": p.remaining_time,
            "Priority": p.priority,
            "Memory (KB)": p.memory_required,
        })
    return pd.DataFrame(rows)


def _next_pid(procs: list[Process]) -> int:
    if not procs:
        return 1
    return max(p.pid for p in procs) + 1


def _log(state, t: int, msg: str) -> None:
    state["event_log"].record(t, msg)


# ----------------------------------------------------------------------
# Tab 1 — Live process table
# ----------------------------------------------------------------------

def _tab_live(state, session_state) -> None:
    procs: list[Process] = state["processes"]

    st.markdown("### Live Process Table")
    if not procs:
        st.info("No processes yet. Create one in the **Create Process** tab, "
                "or run the CPU Scheduler to populate this table.")
        return

    st.dataframe(_processes_df(procs), use_container_width=True, hide_index=True)

    # Summary metrics
    counts = {s.value: 0 for s in ProcessState}
    for p in procs:
        counts[p.state.value] += 1

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("NEW", counts["NEW"])
    c2.metric("READY", counts["READY"])
    c3.metric("RUNNING", counts["RUNNING"])
    c4.metric("WAITING", counts["WAITING"])
    c5.metric("TERMINATED", counts["TERMINATED"])

    st.download_button(
        "⬇ Download Process Table (CSV)",
        data=_processes_df(procs).to_csv(index=False),
        file_name="processes.csv",
        mime="text/csv",
    )


# ----------------------------------------------------------------------
# Tab 2 — Create process
# ----------------------------------------------------------------------

def _tab_create(state, session_state) -> None:
    st.markdown("### Create a Process")
    st.caption("Adds a simulated PCB record. The process starts in the NEW state.")

    procs: list[Process] = state["processes"]
    default_pid = _next_pid(procs)

    with st.form("create_proc_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        with c1:
            pid = st.number_input("PID", min_value=1, value=default_pid, step=1)
            name = st.text_input("Name", value=f"P{default_pid}")
            priority = st.number_input("Priority (smaller = higher)",
                                       min_value=0, value=0, step=1)
        with c2:
            arrival = st.number_input("Arrival time", min_value=0, value=0, step=1)
            burst = st.number_input("Burst time", min_value=1, value=5, step=1)
            memory = st.number_input("Memory required (KB)",
                                     min_value=0, value=128, step=16)

        submitted = st.form_submit_button("➕ Create Process")

    if submitted:
        try:
            validate_process_fields(
                pid=int(pid), arrival_time=int(arrival),
                burst_time=int(burst), priority=int(priority),
                memory_required=int(memory),
            )
            if any(p.pid == int(pid) for p in procs):
                raise ValidationError(f"PID {pid} already exists.")

            proc = Process(
                pid=int(pid), name=name or f"P{pid}",
                arrival_time=int(arrival), burst_time=int(burst),
                priority=int(priority), memory_required=int(memory),
            )
            procs.append(proc)
            _log(state, 0, f"Process {proc.name} created (PID {proc.pid})")
            st.success(f"Created {proc.name} (PID {proc.pid}).")
            st.rerun()
        except ValidationError as exc:
            st.error(str(exc))

    if procs and st.button("🗑 Clear all processes"):
        state["processes"] = []
        _log(state, 0, "All processes cleared")
        st.rerun()


# ----------------------------------------------------------------------
# Tab 3 — PCB detail
# ----------------------------------------------------------------------

def _tab_pcb(state, session_state) -> None:
    procs: list[Process] = state["processes"]
    if not procs:
        st.info("Create a process first.")
        return

    st.markdown("### Process Control Block (PCB)")
    labels = [f"{p.pid} — {p.name}" for p in procs]
    choice = st.selectbox("Select a process", labels, key="pcb_select")
    pid = int(choice.split(" — ")[0])
    p = next(x for x in procs if x.pid == pid)

    # Three-column PCB view
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Identification**")
        st.write(f"**PID:** {p.pid}")
        st.write(f"**Name:** {p.name}")
        st.write(f"**State:** {STATE_BADGE[p.state.value]}")

    with col2:
        st.markdown("**Scheduling**")
        st.write(f"**Arrival time:** {p.arrival_time}")
        st.write(f"**Burst time:** {p.burst_time}")
        st.write(f"**Remaining time:** {p.remaining_time}")
        st.write(f"**Priority:** {p.priority}")

    with col3:
        st.markdown("**Memory & Metrics**")
        st.write(f"**Memory required:** {p.memory_required} KB")
        st.write(f"**Completion:** {p.completion_time if p.completion_time is not None else '—'}")
        st.write(f"**Waiting time:** {p.waiting_time}")
        st.write(f"**Turnaround:** {p.turnaround_time}")

    st.markdown("**Raw PCB record (JSON)**")
    st.json(p.to_dict())


# ----------------------------------------------------------------------
# Tab 4 — State transitions
# ----------------------------------------------------------------------

def _tab_transitions(state, session_state) -> None:
    st.markdown("### Process State Transitions")
    st.caption("Valid transitions only — enforced by the Process class.")

    # Lifecycle diagram as text
    st.markdown("#### Lifecycle")
    st.code(
        "   NEW ──► READY ──► RUNNING ──► TERMINATED\n"
        "             ▲          │\n"
        "             │          ▼\n"
        "             └────── WAITING",
        language="text",
    )

    procs: list[Process] = state["processes"]
    if not procs:
        st.info("Create a process first (see the **Create Process** tab).")
        return

    labels = [f"{p.pid} — {p.name} (current: {p.state.value})" for p in procs]
    choice = st.selectbox("Select a process", labels, key="trans_select")
    pid = int(choice.split(" — ")[0])
    p = next(x for x in procs if x.pid == pid)

    st.markdown(f"**{p.name}** is currently in **{STATE_BADGE[p.state.value]}**.")

    allowed = list(VALID_TRANSITIONS[p.state])
    if not allowed:
        st.info("This process has reached TERMINATED. No further transitions.")
        return

    st.markdown("**Allowed next states:**")
    cols = st.columns(len(allowed))
    for i, target in enumerate(allowed):
        with cols[i]:
            if st.button(f"→ {target.value}", key=f"trans_{p.pid}_{target.value}",
                         use_container_width=True):
                try:
                    p.transition_to(target)
                    _log(state, 0,
                         f"{p.name}: transitioned to {target.value}")
                    st.rerun()
                except ValueError as exc:
                    st.error(str(exc))

    # Show recent state-related events
    log = state["event_log"]
    events = [e for e in log.render_lines() if "transition" in e.lower()
              or "created" in e.lower()]
    if events:
        st.markdown("**Recent state events**")
        st.code("\n".join(events[-10:]), language="text")


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def render(session_state) -> None:
    st.markdown("## Process Management")
    st.caption("Process Control Blocks, state transitions, and the process "
               "lifecycle that the CPU scheduler drives.")

    state = get_state(session_state)

    tab1, tab2, tab3, tab4 = st.tabs([
        "Live Table", "Create Process", "PCB Detail", "State Transitions",
    ])
    with tab1:
        _tab_live(state, session_state)
    with tab2:
        _tab_create(state, session_state)
    with tab3:
        _tab_pcb(state, session_state)
    with tab4:
        _tab_transitions(state, session_state)