"""Unit tests for the deterministic synchronization traces."""
from algorithms.synchronization import (
    race_condition_demo,
    semaphore_demo,
    producer_consumer_demo,
    readers_writers_demo,
)


# ----------------------------------------------------------------------
# Race condition
# ----------------------------------------------------------------------

def test_race_condition_lost_update():
    demo = race_condition_demo(initial=1000, deposit=500, withdraw=200)
    assert demo["expected"] == 1300
    assert demo["unsafe"][-1].state["balance"] == 800
    assert demo["safe"][-1].state["balance"] == 1300


def test_race_condition_step_counts_positive():
    demo = race_condition_demo()
    assert len(demo["unsafe"]) >= 6
    assert len(demo["safe"]) >= 6


# ----------------------------------------------------------------------
# Semaphore
# ----------------------------------------------------------------------

def test_semaphore_never_exceeds_permits():
    trace = semaphore_demo(permits=3, workers=5)
    for step in trace:
        assert step.state["permits_available"] >= 0
        assert len(step.state["holders"]) <= step.state["permits_total"]


def test_semaphore_all_workers_drained():
    trace = semaphore_demo(permits=2, workers=4)
    final = trace[-1].state
    assert final["permits_available"] == 2
    assert final["holders"] == []
    assert final["waiting"] == []


# ----------------------------------------------------------------------
# Producer-Consumer
# ----------------------------------------------------------------------

def test_pc_buffer_never_overflows():
    trace = producer_consumer_demo(buffer_size=3, items=6)
    for step in trace:
        assert len(step.state["buffer"]) <= step.state["buffer_size"]


def test_pc_semaphore_invariants():
    trace = producer_consumer_demo(buffer_size=3, items=6)

    # 1. Quiescent endpoints: buffer empty, all slots free
    first, last = trace[0].state, trace[-1].state
    assert first["empty"] == 3
    assert first["full"] == 0
    assert first["buffer"] == []
    assert last["empty"] == 3
    assert last["full"] == 0
    assert last["buffer"] == []

    # 2. At every step: semaphores and buffer stay inside valid bounds
    for step in trace:
        s = step.state
        assert 0 <= s["empty"] <= s["buffer_size"]
        assert 0 <= s["full"] <= s["buffer_size"]
        assert 0 <= len(s["buffer"]) <= s["buffer_size"]
        assert s["mutex"] in (0, 1)


def test_pc_ends_empty():
    trace = producer_consumer_demo(buffer_size=2, items=4)
    assert trace[-1].state["buffer"] == []
    assert trace[-1].state["empty"] == 2
    assert trace[-1].state["full"] == 0

def test_pc_quiescent_invariant():
    """empty + full == buffer_size holds whenever no thread is mid-operation."""
    trace = producer_consumer_demo(buffer_size=3, items=6)
    quiescent_keywords = ("Init", "Done", "signals")
    for step in trace:
        if any(k in step.label for k in quiescent_keywords):
            s = step.state
            assert s["empty"] + s["full"] == s["buffer_size"], (
                f"Quiescent invariant violated at step '{step.label}'"
            )
            
            
# ----------------------------------------------------------------------
# Readers-Writers
# ----------------------------------------------------------------------

def test_rw_no_reader_writer_overlap():
    trace = readers_writers_demo()
    for step in trace:
        s = step.state
        if s["active_writer"] is not None:
            assert s["active_readers"] == []


def test_rw_readers_can_overlap():
    trace = readers_writers_demo()
    assert any(len(s.state["active_readers"]) >= 2 for s in trace)