"""CPU scheduling algorithms: FCFS, SJF, SRTF, Priority, Round Robin.

Every algorithm in this module returns the same result structure:

    {
        "algorithm": "FCFS",
        "segments": [
            {"process": "P1", "start": 0, "end": 5},
            ...
        ],
        "metrics": {
            <pid>: {
                "completion": int,
                "turnaround": int,
                "waiting": int,
                "response": int,
            },
            ...
        },
        "averages": {
            "turnaround": float,
            "waiting": float,
            "response": float,
        },
        "cpu_utilization": float,   # percentage, 0–100
        "total_time": int,
        "idle_time": int,
    }
"""


from __future__ import annotations
from typing import List
from core.process import Process
from core.validation import validate_time_quantum


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _finalize(
    segments: list[dict],
    metrics: dict[int, dict],
    procs: List[Process],
    algorithm_name: str,
) -> dict:
    total_time = max((s["end"] for s in segments), default=0)
    busy_time = sum(s["end"] - s["start"] for s in segments if s["process"] != "IDLE")
    idle_time = total_time - busy_time

    n = len(procs)
    avg_tat = sum(m["turnaround"] for m in metrics.values()) / n
    avg_wt = sum(m["waiting"] for m in metrics.values()) / n
    avg_rt = sum(m["response"] for m in metrics.values()) / n
    cpu_util = (busy_time / total_time * 100.0) if total_time > 0 else 0.0

    return {
        "algorithm": algorithm_name,
        "segments": segments,
        "metrics": metrics,
        "averages": {
            "turnaround": round(avg_tat, 3),
            "waiting": round(avg_wt, 3),
            "response": round(avg_rt, 3),
        },
        "cpu_utilization": round(cpu_util, 2),
        "total_time": total_time,
        "idle_time": idle_time,
    }


def _metrics_for(p: Process, start: int, end: int) -> dict:
    return {
        "completion": end,
        "turnaround": end - p.arrival_time,
        "waiting": end - p.arrival_time - p.burst_time,
        "response": start - p.arrival_time,
    }


# ----------------------------------------------------------------------
# FCFS — non-preemptive, arrival order
# ----------------------------------------------------------------------

def fcfs(processes: List[Process]) -> dict:
    procs = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    segments, metrics = [], {}
    time = 0
    for p in procs:
        if time < p.arrival_time:
            segments.append({"process": "IDLE", "start": time, "end": p.arrival_time})
            time = p.arrival_time
        start, end = time, time + p.burst_time
        segments.append({"process": p.name, "start": start, "end": end})
        metrics[p.pid] = _metrics_for(p, start, end)
        time = end
    return _finalize(segments, metrics, procs, "FCFS")


# ----------------------------------------------------------------------
# SJF — non-preemptive, shortest burst first
# ----------------------------------------------------------------------

def sjf(processes: List[Process]) -> dict:
    procs = list(processes)
    remaining = {p.pid: p for p in procs}
    segments, metrics = [], {}
    time = 0
    completed: set[int] = set()

    while len(completed) < len(procs):
        ready = [p for p in procs if p.arrival_time <= time and p.pid not in completed]
        if not ready:
            next_arrival = min(p.arrival_time for p in procs if p.pid not in completed)
            segments.append({"process": "IDLE", "start": time, "end": next_arrival})
            time = next_arrival
            continue
        p = min(ready, key=lambda x: (x.burst_time, x.arrival_time, x.pid))
        start, end = time, time + p.burst_time
        segments.append({"process": p.name, "start": start, "end": end})
        metrics[p.pid] = _metrics_for(p, start, end)
        completed.add(p.pid)
        time = end

    return _finalize(segments, metrics, procs, "SJF")


# ----------------------------------------------------------------------
# SRTF — preemptive SJF, shortest remaining time
# ----------------------------------------------------------------------

def srtf(processes: List[Process]) -> dict:
    procs = list(processes)
    remaining = {p.pid: p.burst_time for p in procs}
    first_start: dict[int, int] = {}
    completion: dict[int, int] = {}
    segments: list[dict] = []
    time = 0
    completed: set[int] = set()

    while len(completed) < len(procs):
        ready = [
            p for p in procs
            if p.arrival_time <= time and p.pid not in completed and remaining[p.pid] > 0
        ]
        if not ready:
            next_arrival = min(p.arrival_time for p in procs if p.pid not in completed)
            segments.append({"process": "IDLE", "start": time, "end": next_arrival})
            time = next_arrival
            continue

        p = min(ready, key=lambda x: (remaining[x.pid], x.arrival_time, x.pid))
        if p.pid not in first_start:
            first_start[p.pid] = time

        # Run until either the process finishes or a shorter job arrives
        finish_at = time + remaining[p.pid]
        next_arrival = min(
            (q.arrival_time for q in procs
             if q.pid not in completed and q.arrival_time > time),
            default=finish_at,
        )
        run_until = min(finish_at, next_arrival)

        # Append/merge segment
        if segments and segments[-1]["process"] == p.name and segments[-1]["end"] == time:
            segments[-1]["end"] = run_until
        else:
            segments.append({"process": p.name, "start": time, "end": run_until})

        remaining[p.pid] -= (run_until - time)
        time = run_until
        if remaining[p.pid] == 0:
            completion[p.pid] = time
            completed.add(p.pid)

    metrics = {}
    for p in procs:
        ct = completion[p.pid]
        metrics[p.pid] = {
            "completion": ct,
            "turnaround": ct - p.arrival_time,
            "waiting": ct - p.arrival_time - p.burst_time,
            "response": first_start[p.pid] - p.arrival_time,
        }
    return _finalize(segments, metrics, procs, "SRTF")


# ----------------------------------------------------------------------
# Priority — non-preemptive by default; smaller number = higher priority
# ----------------------------------------------------------------------

def priority_scheduling(processes: List[Process], preemptive: bool = False) -> dict:
    if preemptive:
        return _priority_preemptive(processes)
    return _priority_non_preemptive(processes)


def _priority_non_preemptive(processes: List[Process]) -> dict:
    procs = list(processes)
    segments, metrics = [], {}
    completed: set[int] = set()
    time = 0

    while len(completed) < len(procs):
        ready = [
            p for p in procs
            if p.arrival_time <= time and p.pid not in completed
        ]
        if not ready:
            next_arrival = min(p.arrival_time for p in procs if p.pid not in completed)
            segments.append({"process": "IDLE", "start": time, "end": next_arrival})
            time = next_arrival
            continue
        p = min(ready, key=lambda x: (x.priority, x.arrival_time, x.pid))
        start, end = time, time + p.burst_time
        segments.append({"process": p.name, "start": start, "end": end})
        metrics[p.pid] = _metrics_for(p, start, end)
        completed.add(p.pid)
        time = end

    return _finalize(segments, metrics, procs, "Priority (non-preemptive)")


def _priority_preemptive(processes: List[Process]) -> dict:
    procs = list(processes)
    remaining = {p.pid: p.burst_time for p in procs}
    first_start: dict[int, int] = {}
    completion: dict[int, int] = {}
    segments: list[dict] = []
    completed: set[int] = set()
    time = 0

    while len(completed) < len(procs):
        ready = [
            p for p in procs
            if p.arrival_time <= time and p.pid not in completed and remaining[p.pid] > 0
        ]
        if not ready:
            next_arrival = min(p.arrival_time for p in procs if p.pid not in completed)
            segments.append({"process": "IDLE", "start": time, "end": next_arrival})
            time = next_arrival
            continue

        p = min(ready, key=lambda x: (x.priority, x.arrival_time, x.pid))
        if p.pid not in first_start:
            first_start[p.pid] = time

        finish_at = time + remaining[p.pid]
        # Preempt if a higher-priority process arrives before this finishes
        higher_arrivals = [
            q.arrival_time for q in procs
            if q.pid not in completed
            and q.arrival_time > time
            and q.priority < p.priority
        ]
        next_arrival = min(higher_arrivals, default=finish_at)
        run_until = min(finish_at, next_arrival)

        if segments and segments[-1]["process"] == p.name and segments[-1]["end"] == time:
            segments[-1]["end"] = run_until
        else:
            segments.append({"process": p.name, "start": time, "end": run_until})

        remaining[p.pid] -= (run_until - time)
        time = run_until
        if remaining[p.pid] == 0:
            completion[p.pid] = time
            completed.add(p.pid)

    metrics = {}
    for p in procs:
        ct = completion[p.pid]
        metrics[p.pid] = {
            "completion": ct,
            "turnaround": ct - p.arrival_time,
            "waiting": ct - p.arrival_time - p.burst_time,
            "response": first_start[p.pid] - p.arrival_time,
        }
    return _finalize(segments, metrics, procs, "Priority (preemptive)")


# ----------------------------------------------------------------------
# Round Robin — preemptive, fixed time quantum
# ----------------------------------------------------------------------

def round_robin(processes: List[Process], quantum: int) -> dict:
    validate_time_quantum(quantum)
    procs = sorted(processes, key=lambda p: (p.arrival_time, p.pid))
    n = len(procs)
    remaining = {p.pid: p.burst_time for p in procs}
    first_start: dict[int, int] = {}
    completion: dict[int, int] = {}
    segments: list[dict] = []
    ready: list[int] = []
    time = 0
    i = 0

    # Seed with processes that arrive at or before t=0
    while i < n and procs[i].arrival_time <= time:
        ready.append(procs[i].pid)
        i += 1

    while ready or i < n:
        if not ready:
            next_arrival = procs[i].arrival_time
            segments.append({"process": "IDLE", "start": time, "end": next_arrival})
            time = next_arrival
            while i < n and procs[i].arrival_time <= time:
                ready.append(procs[i].pid)
                i += 1
            continue

        pid = ready.pop(0)
        if pid not in first_start:
            first_start[pid] = time

        run = min(quantum, remaining[pid])
        start, end = time, time + run
        segments.append({
            "process": next(p.name for p in procs if p.pid == pid),
            "start": start,
            "end": end,
        })
        remaining[pid] -= run
        time = end

        # New arrivals during this slice enter the queue first
        while i < n and procs[i].arrival_time <= time:
            ready.append(procs[i].pid)
            i += 1

        if remaining[pid] == 0:
            completion[pid] = time
        else:
            ready.append(pid)

    metrics = {}
    for p in procs:
        ct = completion[p.pid]
        metrics[p.pid] = {
            "completion": ct,
            "turnaround": ct - p.arrival_time,
            "waiting": ct - p.arrival_time - p.burst_time,
            "response": first_start[p.pid] - p.arrival_time,
        }
    return _finalize(segments, metrics, procs, f"Round Robin (q={quantum})")


# ----------------------------------------------------------------------
# Dispatch helper used by the UI
# ----------------------------------------------------------------------

ALGORITHMS = {
    "FCFS":                  lambda procs, **kw: fcfs(procs),
    "SJF (non-preemptive)":  lambda procs, **kw: sjf(procs),
    "SRTF (preemptive)":     lambda procs, **kw: srtf(procs),
    "Priority (non-preemptive)": lambda procs, **kw: priority_scheduling(procs, preemptive=False),
    "Priority (preemptive)": lambda procs, **kw: priority_scheduling(procs, preemptive=True),
    "Round Robin":           lambda procs, quantum=2, **kw: round_robin(procs, quantum),
}


def run_algorithm(name: str, processes: List[Process], **kwargs) -> dict:
    if name not in ALGORITHMS:
        raise ValueError(f"Unknown algorithm: {name}")
    return ALGORITHMS[name](processes, **kwargs)