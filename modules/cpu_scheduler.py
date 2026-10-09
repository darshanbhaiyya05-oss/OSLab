"""Module 1 — CPU Scheduling Laboratory."""
from __future__ import annotations
import json
import pandas as pd
import streamlit as st
from core.process import Process, ProcessState
from core.validation import ValidationError, validate_process_fields
from core.system_state import get_state
from algorithms.cpu_scheduling import run_algorithm
from visualizations.gantt_chart import build_gantt
from core.process import Process, ProcessState


SAMPLE_ROWS = [
    # pid, name, arrival, burst, priority
    (1, "P1", 0, 8, 2),
    (2, "P2", 1, 6, 1),
    (3, "P3", 3, 3, 3),
    (4, "P4", 5, 2, 4),
    (5, "P5", 6, 4, 5),
]

ALGO_CHOICES = [
    "FCFS",
    "SJF (non-preemptive)",
    "SRTF (preemptive)",
    "Priority (non-preemptive)",
    "Priority (preemptive)",
    "Round Robin",
]


def _rows_to_processes(rows) -> list[Process]:
    procs: list[Process] = []
    for r in rows:
        validate_process_fields(
            pid=int(r["pid"]),
            arrival_time=int(r["arrival"]),
            burst_time=int(r["burst"]),
            priority=int(r.get("priority", 0)),
        )
        procs.append(Process(
            pid=int(r["pid"]),
            name=r["name"],
            arrival_time=int(r["arrival"]),
            burst_time=int(r["burst"]),
            priority=int(r.get("priority", 0)),
        ))
    return procs


def _default_rows() -> list[dict]:
    return [
        {"pid": p, "name": n, "arrival": a, "burst": b, "priority": pr}
        for (p, n, a, b, pr) in SAMPLE_ROWS
    ]


def _build_metrics_table(result: dict, procs: list[Process]) -> pd.DataFrame:
    name_by_pid = {p.pid: p.name for p in procs}
    burst_by_pid = {p.pid: p.burst_time for p in procs}
    arr_by_pid = {p.pid: p.arrival_time for p in procs}
    rows = []
    for pid, m in result["metrics"].items():
        rows.append({
            "PID": pid,
            "Process": name_by_pid[pid],
            "Arrival": arr_by_pid[pid],
            "Burst": burst_by_pid[pid],
            "Completion": m["completion"],
            "Turnaround": m["turnaround"],
            "Waiting": m["waiting"],
            "Response": m["response"],
        })
    return pd.DataFrame(rows).sort_values("PID")


def render(session_state) -> None:
    st.markdown("## CPU Scheduling Laboratory")
    st.caption("Configure processes, choose an algorithm, and observe the "
               "execution timeline and performance metrics.")

    state = get_state(session_state)
    if "cpu_rows" not in session_state:
        session_state["cpu_rows"] = _default_rows()
    if "cpu_compare" not in session_state:
        session_state["cpu_compare"] = []

    # -------- Process configuration --------
    with st.expander("Process Configuration", expanded=True):
        c1, c2, c3 = st.columns([1, 1, 1])
        with c1:
            if st.button("Load Sample Data", use_container_width=True):
                session_state["cpu_rows"] = _default_rows()
                session_state["cpu_compare"] = []
                st.rerun()
        with c2:
            if st.button("Reset", use_container_width=True):
                session_state["cpu_rows"] = []
                session_state["cpu_compare"] = []
                st.rerun()
        with c3:
            st.write("")

        edited = st.data_editor(
            pd.DataFrame(session_state["cpu_rows"]),
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                "pid": st.column_config.NumberColumn("PID", min_value=1, step=1),
                "name": st.column_config.TextColumn("Name"),
                "arrival": st.column_config.NumberColumn("Arrival", min_value=0, step=1),
                "burst": st.column_config.NumberColumn("Burst", min_value=1, step=1),
                "priority": st.column_config.NumberColumn("Priority (smaller=higher)",
                                                          min_value=0, step=1),
            },
            key="cpu_editor",
        )
        session_state["cpu_rows"] = edited.to_dict("records")

    if not session_state["cpu_rows"]:
        st.info("Add at least one process row to run the scheduler.")
        return

    # -------- Algorithm configuration --------
    colA, colB, colC = st.columns([2, 1, 1])
    with colA:
        algo = st.selectbox("Algorithm", ALGO_CHOICES, index=5)
    with colB:
        quantum = st.number_input("Time Quantum (RR)", min_value=1, value=4, step=1)
    with colC:
        st.write("")
        run = st.button("▶ Run Scheduler", type="primary", use_container_width=True)

    if run:
        try:
            procs = _rows_to_processes(session_state["cpu_rows"])
        except ValidationError as exc:
            st.error(f"Invalid input: {exc}")
            return

        kwargs = {}
        if algo == "Round Robin":
            kwargs["quantum"] = int(quantum)

        result = run_algorithm(algo, procs, **kwargs)
        session_state["cpu_result"] = result
        session_state["cpu_processes"] = procs
        state["processes"] = procs
        state["last_simulation"] = {"module": "CPU Scheduling", "result": result}

        # Log events
        log = state["event_log"]
        log.record(0, f"Scheduled {len(procs)} processes with {algo}")
        for seg in result["segments"]:
            if seg["process"] == "IDLE":
                log.record(seg["start"], f"CPU idle until t={seg['end']}")
            else:
                log.record(seg["start"],
                           f"Dispatch {seg['process']} for {seg['end']-seg['start']} units")

        # Drive process state transitions to reflect the scheduler run.
        for p in procs:
            try:
                while p.state != ProcessState.TERMINATED:
                    if p.state == ProcessState.NEW:
                        p.transition_to(ProcessState.READY)
                    elif p.state == ProcessState.READY:
                        p.transition_to(ProcessState.RUNNING)
                    elif p.state == ProcessState.RUNNING:
                        p.transition_to(ProcessState.TERMINATED)
                    else:
                        break
            except ValueError:
                pass
            metrics = result["metrics"].get(p.pid, {})
            p.completion_time = metrics.get("completion")
            p.turnaround_time = metrics.get("turnaround", 0)
            p.waiting_time = metrics.get("waiting", 0)
            p.response_time = metrics.get("response", 0)
            p.remaining_time = 0
            
    # -------- Results --------
    result = session_state.get("cpu_result")
    procs = session_state.get("cpu_processes")
    if not result or not procs:
        st.info("Press **Run Scheduler** to execute the selected algorithm.")
        return

    st.markdown("### Execution Timeline")
    st.plotly_chart(
        build_gantt(result["segments"], procs),
        use_container_width=True,
        key="cpu_gantt_main",
    )

    # Quick stats
    s1, s2, s3, s4 = st.columns(4)
    s1.metric("Avg Waiting", f"{result['averages']['waiting']:.2f}")
    s2.metric("Avg Turnaround", f"{result['averages']['turnaround']:.2f}")
    s3.metric("Avg Response", f"{result['averages']['response']:.2f}")
    s4.metric("CPU Utilization", f"{result['cpu_utilization']:.2f}%")

    st.markdown("### Per-Process Metrics")
    metrics_df = _build_metrics_table(result, procs)
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)

    # -------- Comparison --------
    st.markdown("### Compare Algorithms")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("Add current result to comparison"):
            session_state["cpu_compare"].append(result)
    with c2:
        if st.button("Clear comparison"):
            session_state["cpu_compare"] = []

    if session_state["cpu_compare"]:
        cmp_rows = []
        for r in session_state["cpu_compare"]:
            cmp_rows.append({
                "Algorithm": r["algorithm"],
                "Avg Waiting": r["averages"]["waiting"],
                "Avg Turnaround": r["averages"]["turnaround"],
                "Avg Response": r["averages"]["response"],
                "CPU Util %": r["cpu_utilization"],
                "Total Time": r["total_time"],
            })
        st.dataframe(pd.DataFrame(cmp_rows), use_container_width=True, hide_index=True)

    # -------- Exports --------
    st.markdown("### Export")
    snapshot = {
        "algorithm": result["algorithm"],
        "processes": [p.to_dict() for p in procs],
        "metrics": {str(k): v for k, v in result["metrics"].items()},
        "averages": result["averages"],
        "cpu_utilization": result["cpu_utilization"],
        "segments": result["segments"],
    }
    e1, e2 = st.columns(2)
    with e1:
        st.download_button(
            "⬇ Download JSON Snapshot",
            data=json.dumps(snapshot, indent=2),
            file_name="cpu_scheduling_result.json",
            mime="application/json",
        )
    with e2:
        st.download_button(
            "⬇ Download Metrics CSV",
            data=metrics_df.to_csv(index=False),
            file_name="cpu_metrics.csv",
            mime="text/csv",
        )