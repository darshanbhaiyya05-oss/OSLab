"""Tests for the Process state machine."""
import pytest
from core.process import Process, ProcessState, VALID_TRANSITIONS


def make(pid=1, state=ProcessState.NEW):
    p = Process(pid=pid, name=f"P{pid}", arrival_time=0, burst_time=5)
    p.state = state
    return p


# ----------------------------------------------------------------------
# Legal transitions
# ----------------------------------------------------------------------

def test_new_to_ready():
    p = make(state=ProcessState.NEW)
    p.transition_to(ProcessState.READY)
    assert p.state == ProcessState.READY


def test_ready_to_running():
    p = make(state=ProcessState.READY)
    p.transition_to(ProcessState.RUNNING)
    assert p.state == ProcessState.RUNNING


def test_running_to_ready():
    p = make(state=ProcessState.RUNNING)
    p.transition_to(ProcessState.READY)
    assert p.state == ProcessState.READY


def test_running_to_waiting():
    p = make(state=ProcessState.RUNNING)
    p.transition_to(ProcessState.WAITING)
    assert p.state == ProcessState.WAITING


def test_waiting_to_ready():
    p = make(state=ProcessState.WAITING)
    p.transition_to(ProcessState.READY)
    assert p.state == ProcessState.READY


def test_running_to_terminated():
    p = make(state=ProcessState.RUNNING)
    p.transition_to(ProcessState.TERMINATED)
    assert p.state == ProcessState.TERMINATED


def test_full_lifecycle():
    p = make()
    p.transition_to(ProcessState.READY)
    p.transition_to(ProcessState.RUNNING)
    p.transition_to(ProcessState.WAITING)
    p.transition_to(ProcessState.READY)
    p.transition_to(ProcessState.RUNNING)
    p.transition_to(ProcessState.TERMINATED)
    assert p.state == ProcessState.TERMINATED


# ----------------------------------------------------------------------
# Illegal transitions
# ----------------------------------------------------------------------

def test_new_cannot_jump_to_running():
    p = make(state=ProcessState.NEW)
    with pytest.raises(ValueError):
        p.transition_to(ProcessState.RUNNING)


def test_ready_cannot_go_to_terminated():
    p = make(state=ProcessState.READY)
    with pytest.raises(ValueError):
        p.transition_to(ProcessState.TERMINATED)


def test_terminated_is_final():
    p = make(state=ProcessState.TERMINATED)
    with pytest.raises(ValueError):
        p.transition_to(ProcessState.READY)


def test_waiting_cannot_go_to_running_directly():
    p = make(state=ProcessState.WAITING)
    with pytest.raises(ValueError):
        p.transition_to(ProcessState.RUNNING)


# ----------------------------------------------------------------------
# Remaining-time initialisation
# ----------------------------------------------------------------------

def test_remaining_time_defaults_to_burst():
    p = Process(pid=1, name="P1", arrival_time=0, burst_time=7)
    assert p.remaining_time == 7