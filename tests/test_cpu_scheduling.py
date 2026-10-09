"""Unit tests for CPU scheduling algorithms."""
import pytest
from core.process import Process
from core.validation import ValidationError, validate_time_quantum
from algorithms.cpu_scheduling import (
    fcfs, sjf, srtf, priority_scheduling, round_robin,
)


def make(pid, name, arr, burst, prio=0):
    return Process(pid=pid, name=name, arrival_time=arr, burst_time=burst, priority=prio)


# ----------------------------------------------------------------------
# FCFS
# ----------------------------------------------------------------------

def test_fcfs_basic():
    procs = [make(1, "P1", 0, 5), make(2, "P2", 1, 3), make(3, "P3", 2, 1)]
    r = fcfs(procs)
    assert [(s["process"], s["start"], s["end"]) for s in r["segments"]] == [
        ("P1", 0, 5), ("P2", 5, 8), ("P3", 8, 9),
    ]
    assert r["metrics"][1]["completion"] == 5
    assert r["metrics"][1]["waiting"] == 0
    assert r["metrics"][2]["waiting"] == 4
    assert r["metrics"][3]["waiting"] == 6
    assert r["cpu_utilization"] == 100.0


def test_fcfs_idle_gap():
    procs = [make(1, "P1", 3, 2)]
    r = fcfs(procs)
    assert r["segments"][0] == {"process": "IDLE", "start": 0, "end": 3}
    assert r["idle_time"] == 3


# ----------------------------------------------------------------------
# SJF (non-preemptive)
# ----------------------------------------------------------------------

def test_sjf_picks_shortest_ready():
    procs = [make(1, "P1", 0, 5), make(2, "P2", 1, 3), make(3, "P3", 2, 1)]
    r = sjf(procs)
    order = [s["process"] for s in r["segments"]]
    assert order == ["P1", "P3", "P2"]
    assert r["metrics"][3]["waiting"] == 3   # P3 waited 3
    assert r["metrics"][2]["waiting"] == 5   # P2 waited 5


# ----------------------------------------------------------------------
# SRTF
# ----------------------------------------------------------------------

def test_srtf_preempts():
    procs = [make(1, "P1", 0, 5), make(2, "P2", 1, 3), make(3, "P3", 2, 1)]
    r = srtf(procs)
    # P3 arrives at t=2 with 1 unit; should run before P2 finishes
    assert r["metrics"][3]["completion"] == 3
    assert r["metrics"][2]["completion"] == 5
    assert r["metrics"][1]["completion"] == 9
    assert r["metrics"][3]["waiting"] == 0


# ----------------------------------------------------------------------
# Priority
# ----------------------------------------------------------------------

def test_priority_non_preemptive_smaller_is_higher():
    procs = [make(1, "P1", 0, 5, prio=2),
             make(2, "P2", 1, 3, prio=1),
             make(3, "P3", 2, 1, prio=3)]
    r = priority_scheduling(procs, preemptive=False)
    order = [s["process"] for s in r["segments"]]
    # P1 starts because it is the only arrival at t=0; then P2 (higher priority than P3)
    assert order == ["P1", "P2", "P3"]


def test_priority_preemptive_preempts_for_higher_priority():
    procs = [make(1, "P1", 0, 5, prio=2),
             make(2, "P2", 1, 3, prio=1),
             make(3, "P3", 2, 1, prio=3)]
    r = priority_scheduling(procs, preemptive=True)
    # At t=1 P2 arrives with higher priority -> preempts P1
    assert r["segments"][0]["process"] == "P1"
    assert r["segments"][0]["end"] == 1
    assert r["segments"][1]["process"] == "P2"


# ----------------------------------------------------------------------
# Round Robin
# ----------------------------------------------------------------------

def test_round_robin_sequence():
    procs = [make(1, "P1", 0, 8), make(2, "P2", 1, 6),
             make(3, "P3", 3, 3), make(4, "P4", 5, 2), make(5, "P5", 6, 4)]
    r = round_robin(procs, quantum=4)
    order = [s["process"] for s in r["segments"]]
    # Expected from the reference image
    assert order == ["P1", "P2", "P3", "P1", "P4", "P5", "P2"]
    assert r["total_time"] == 23


def test_round_robin_quantum_gt_burst():
    procs = [make(1, "P1", 0, 2), make(2, "P2", 1, 3)]
    r = round_robin(procs, quantum=10)
    order = [s["process"] for s in r["segments"]]
    assert order == ["P1", "P2"]


def test_round_robin_invalid_quantum():
    with pytest.raises(ValidationError):
        validate_time_quantum(0)
    with pytest.raises(ValidationError):
        validate_time_quantum(-1)


# ----------------------------------------------------------------------
# General correctness invariants
# ----------------------------------------------------------------------

@pytest.mark.parametrize("algo_fn", [fcfs, sjf, srtf])
def test_metric_invariants(algo_fn):
    procs = [make(1, "P1", 0, 5), make(2, "P2", 1, 3), make(3, "P3", 2, 1)]
    r = algo_fn(procs)
    for pid, m in r["metrics"].items():
        p = next(x for x in procs if x.pid == pid)
        assert m["completion"] >= p.arrival_time
        assert m["turnaround"] == m["completion"] - p.arrival_time
        assert m["waiting"] == m["turnaround"] - p.burst_time
        assert m["response"] >= 0
        assert m["waiting"] >= 0