"""Module 2 — Synchronization Playground (deterministic step-through)."""
from __future__ import annotations
import time
import streamlit as st
from algorithms.synchronization import (
    race_condition_demo,
    semaphore_demo,
    producer_consumer_demo,
    readers_writers_demo,
    Step,
)


SUB_MODES = [
    "Race Condition & Mutex",
    "Semaphore",
    "Producer–Consumer",
    "Readers–Writers",
]


def _reset_if_mode_changed(session_state, mode: str) -> None:
    if session_state.get("sync_mode") != mode:
        session_state["sync_mode"] = mode
        session_state["sync_step"] = 0
        session_state["sync_autoplay"] = False


def _render_step(trace: list[Step], index: int) -> None:
    step = trace[index]
    st.markdown(f"#### Step {index + 1} / {len(trace)} — {step.label}")
    st.markdown(f"**{step.actor}:** {step.action}")
    if step.note:
        low = step.note.lower()
        if "incorrect" in low or "lost update" in low or "blocked" in low:
            st.warning(step.note)
        else:
            st.success(step.note)
    st.markdown("**Shared state:**")
    st.json(step.state, expanded=True)


def _render_controls(session_state, trace: list[Step]) -> None:
    n = len(trace)
    step = session_state.get("sync_step", 0)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        if st.button("⏮ Reset", use_container_width=True):
            session_state["sync_step"] = 0
            session_state["sync_autoplay"] = False
            st.rerun()
    with c2:
        if st.button("◀ Prev", use_container_width=True, disabled=(step == 0)):
            session_state["sync_step"] = max(0, step - 1)
            st.rerun()
    with c3:
        if st.button("Next ▶", use_container_width=True,
                     disabled=(step >= n - 1)):
            session_state["sync_step"] = min(n - 1, step + 1)
            st.rerun()
    with c4:
        if st.button("⏭ End", use_container_width=True):
            session_state["sync_step"] = n - 1
            st.rerun()
    with c5:
        playing = session_state.get("sync_autoplay", False)
        label = "⏸ Pause" if playing else "▶ Auto"
        if st.button(label, use_container_width=True):
            session_state["sync_autoplay"] = not playing
            st.rerun()


def _autoplay(session_state, trace: list[Step]) -> None:
    if not session_state.get("sync_autoplay"):
        return
    step = session_state.get("sync_step", 0)
    if step >= len(trace) - 1:
        session_state["sync_autoplay"] = False
        return
    session_state["sync_step"] = step + 1
    time.sleep(0.8)
    st.rerun()


# ----------------------------------------------------------------------
# Panels
# ----------------------------------------------------------------------

def _panel_race(session_state) -> None:
    st.markdown("### Race Condition vs Mutex")
    st.caption("Two threads update the same balance. Compare what happens "
               "with and without a lock.")

    c1, c2, c3 = st.columns(3)
    with c1:
        initial = st.number_input("Initial balance (Rs.)",
                                  min_value=0, value=1000, step=100)
    with c2:
        deposit = st.number_input("Deposit by Thread A (Rs.)",
                                  min_value=0, value=500, step=50)
    with c3:
        withdraw = st.number_input("Withdraw by Thread B (Rs.)",
                                   min_value=0, value=200, step=50)

    if st.button("Generate Trace", type="primary", key="gen_race"):
        session_state["race_demo"] = race_condition_demo(
            initial=initial, deposit=deposit, withdraw=withdraw)
        session_state["race_unsafe_idx"] = 0
        session_state["race_safe_idx"] = 0

    demo = session_state.get("race_demo")
    if not demo:
        st.info("Click **Generate Trace** to build the demonstration.")
        return

    st.caption(f"Expected correct balance: **Rs.{demo['expected']}**")
    tab1, tab2 = st.tabs(["Unsafe (no lock)", "Safe (mutex)"])

    with tab1:
        trace = demo["unsafe"]
        idx = session_state.get("race_unsafe_idx", 0)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Reset", key="reset_unsafe"):
                session_state["race_unsafe_idx"] = 0
                st.rerun()
        with c2:
            if st.button("◀ Prev", key="prev_unsafe", disabled=(idx == 0)):
                session_state["race_unsafe_idx"] = idx - 1
                st.rerun()
        with c3:
            if st.button("Next ▶", key="next_unsafe",
                         disabled=(idx >= len(trace) - 1)):
                session_state["race_unsafe_idx"] = idx + 1
                st.rerun()
        _render_step(trace, session_state["race_unsafe_idx"])

    with tab2:
        trace = demo["safe"]
        idx = session_state.get("race_safe_idx", 0)
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Reset", key="reset_safe"):
                session_state["race_safe_idx"] = 0
                st.rerun()
        with c2:
            if st.button("◀ Prev", key="prev_safe", disabled=(idx == 0)):
                session_state["race_safe_idx"] = idx - 1
                st.rerun()
        with c3:
            if st.button("Next ▶", key="next_safe",
                         disabled=(idx >= len(trace) - 1)):
                session_state["race_safe_idx"] = idx + 1
                st.rerun()
        _render_step(trace, session_state["race_safe_idx"])


def _panel_semaphore(session_state) -> None:
    st.markdown("### Semaphore — Limited Permits")
    st.caption("Workers must acquire a permit from a pool. Extra workers wait.")

    c1, c2 = st.columns(2)
    with c1:
        permits = st.slider("Permits", 1, 5, 3)
    with c2:
        workers = st.slider("Workers", 1, 8, 5)

    if st.button("Generate Trace", type="primary", key="gen_sem"):
        session_state["sem_trace"] = semaphore_demo(permits=permits,
                                                    workers=workers)
        session_state["sync_step"] = 0
        session_state["sync_autoplay"] = False

    trace = session_state.get("sem_trace")
    if not trace:
        return
    _render_controls(session_state, trace)
    _render_step(trace, session_state.get("sync_step", 0))
    _autoplay(session_state, trace)


def _panel_pc(session_state) -> None:
    st.markdown("### Producer–Consumer (Bounded Buffer)")
    st.caption("Producer inserts items; consumer removes them. "
               "Semaphores prevent overflow and underflow.")

    c1, c2 = st.columns(2)
    with c1:
        buf = st.slider("Buffer size", 1, 5, 3)
    with c2:
        items = st.slider("Items to produce / consume", 1, 10, 6)

    if st.button("Generate Trace", type="primary", key="gen_pc"):
        session_state["pc_trace"] = producer_consumer_demo(
            buffer_size=buf, items=items)
        session_state["sync_step"] = 0
        session_state["sync_autoplay"] = False

    trace = session_state.get("pc_trace")
    if not trace:
        return
    _render_controls(session_state, trace)
    _render_step(trace, session_state.get("sync_step", 0))
    _autoplay(session_state, trace)


def _panel_rw(session_state) -> None:
    st.markdown("### Readers–Writers")
    st.caption("Multiple readers may read simultaneously; a writer needs "
               "exclusive access.")

    if st.button("Generate Trace", type="primary", key="gen_rw"):
        session_state["rw_trace"] = readers_writers_demo()
        session_state["sync_step"] = 0
        session_state["sync_autoplay"] = False

    trace = session_state.get("rw_trace")
    if not trace:
        return
    _render_controls(session_state, trace)
    _render_step(trace, session_state.get("sync_step", 0))
    _autoplay(session_state, trace)


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------

def render(session_state) -> None:
    st.markdown("## Synchronization Playground")
    st.caption("Deterministic simulations of classic synchronization "
               "problems. Step through each scenario to observe every event.")

    mode = st.radio("Choose a demonstration", SUB_MODES, horizontal=True)
    _reset_if_mode_changed(session_state, mode)
    st.markdown("---")

    if mode == "Race Condition & Mutex":
        _panel_race(session_state)
    elif mode == "Semaphore":
        _panel_semaphore(session_state)
    elif mode == "Producer–Consumer":
        _panel_pc(session_state)
    elif mode == "Readers–Writers":
        _panel_rw(session_state)