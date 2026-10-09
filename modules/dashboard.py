"""Module 0 — Dashboard: virtual system overview."""
from __future__ import annotations
import streamlit as st
from core.system_state import get_state


MODULE_CARDS = [
    ("1", "Process & Thread Simulator",
     "PCB/TCB, state transitions, context switch, live table."),
    ("2", "CPU Scheduling Laboratory",
     "FCFS, SJF, SRTF, Priority, Round Robin with Gantt charts and metrics."),
    ("3", "Synchronization Playground",
     "Race conditions, mutex, semaphore, Producer-Consumer, Readers-Writers."),
    ("4", "Deadlock Analyzer",
     "Resource Allocation Graph, Banker's Algorithm, safe-sequence analysis."),
    ("5", "Memory Management",
     "First/Best/Worst Fit, paging, segmentation, fragmentation."),
    ("6", "Virtual Memory",
     "Page tables, FIFO / LRU / Optimal replacement, comparison."),
    ("7", "File & Disk Management",
     "Virtual directory tree and FCFS/SSTF/SCAN/C-SCAN disk scheduling."),
]


def render(session_state) -> None:
    state = get_state(session_state)
    st.markdown("## Mini Operating System Simulator")
    st.caption("An interactive, visual laboratory for learning OS concepts. "
               "Choose a module from the sidebar to begin.")

    # Simulated status panel
    procs = state.get("processes", [])
    running = sum(1 for p in procs if p.state.value == "RUNNING")
    ready = sum(1 for p in procs if p.state.value == "READY")
    terminated = sum(1 for p in procs if p.state.value == "TERMINATED")
    total_mem = sum(p.memory_required for p in procs)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Processes", len(procs))
    c2.metric("Running / Ready", f"{running} / {ready}")
    c3.metric("Terminated", terminated)
    c4.metric("Memory Requested", f"{total_mem} KB")

    st.markdown("### Modules")
    cols = st.columns(2)
    for idx, (num, title, desc) in enumerate(MODULE_CARDS):
        with cols[idx % 2]:
            with st.container(border=True):
                st.markdown(f"**{num}. {title}**")
                st.caption(desc)

    # Recent events
    log = state["event_log"]
    st.markdown("### Recent Events")
    events = log.render_lines()[-10:]
    if events:
        st.code("\n".join(events), language="text")
    else:
        st.info("No events recorded yet. Start a simulation from any module.")