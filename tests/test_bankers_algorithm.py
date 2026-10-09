"""Unit tests for Banker's Algorithm and resource requests."""
from copy import deepcopy
from algorithms.bankers_algorithm import (
    SystemState, sample_state, is_safe, request_resources,
)


# ----------------------------------------------------------------------
# Need computation
# ----------------------------------------------------------------------

def test_need_matrix():
    s = sample_state()
    need = s.need()
    assert need[0] == [7, 4, 3]
    assert need[1] == [1, 2, 2]
    assert need[2] == [6, 0, 0]
    assert need[3] == [0, 1, 1]
    assert need[4] == [4, 3, 1]


# ----------------------------------------------------------------------
# Safety
# ----------------------------------------------------------------------

def test_sample_state_is_safe():
    result = is_safe(sample_state())
    assert result["safe"] is True

    # Any valid safe sequence must contain each process exactly once.
    seq = result["safe_sequence"]
    assert sorted(seq) == ["P0", "P1", "P2", "P3", "P4"]
    assert len(seq) == 5

    # Optional: verify the reported sequence is itself valid by replaying it.
    from algorithms.bankers_algorithm import SystemState
    s = sample_state()
    work = list(s.available)
    need = s.need()
    for pid in seq:
        i = s.processes.index(pid)
        assert all(need[i][j] <= work[j] for j in range(len(s.resources))), (
            f"{pid} does not fit at Work={work}"
        )
        for j in range(len(s.resources)):
            work[j] += s.allocation[i][j]


def test_unsafe_state():
    s = SystemState(
        processes=["P0", "P1"],
        resources=["A", "B"],
        allocation=[[2, 0], [0, 2]],
        maximum=[[5, 0], [0, 5]],
        available=[0, 0],
    )
    result = is_safe(s)
    assert result["safe"] is False


def test_single_process_fits():
    s = SystemState(
        processes=["P0"],
        resources=["A"],
        allocation=[[0]],
        maximum=[[3]],
        available=[5],
    )
    result = is_safe(s)
    assert result["safe"] is True
    assert result["safe_sequence"] == ["P0"]


# ----------------------------------------------------------------------
# Resource requests
# ----------------------------------------------------------------------

def test_request_exceeds_need():
    s = sample_state()
    # P1's Need is [1, 2, 2], so [2, 0, 0] exceeds it on resource A
    out = request_resources(s, "P1", [2, 0, 0])
    assert out["granted"] is False
    assert "exceeds" in out["reason"].lower()


def test_request_exceeds_available():
    s = sample_state()
    # Available is [3, 3, 2]; P0 Need is [7, 4, 3]; request [5, 0, 0] fits Need
    # but exceeds Available on A.
    out = request_resources(s, "P0", [5, 0, 0])
    assert out["granted"] is False
    assert "available" in out["reason"].lower()


def test_request_safe_granted_and_committed():
    s = sample_state()
    # P1 Need is [1, 2, 2], Available is [3, 3, 2] -> [1, 0, 2] is safe
    before_alloc = deepcopy(s.allocation)
    before_avail = list(s.available)
    out = request_resources(s, "P1", [1, 0, 2])
    assert out["granted"] is True
    assert out["after"]["available"] != before_avail
    assert out["after"]["allocation"][1] != before_alloc[1]


def test_request_unsafe_rolled_back():
    # Construct a state where a request fits Need and Available
    # but leaves the system unsafe.
    s = SystemState(
        processes=["P0", "P1"],
        resources=["A"],
        allocation=[[1], [0]],
        maximum=[[2], [5]],
        available=[2],
    )
    # If P0 requests [1] of A, allocation becomes [[2],[0]], available [1].
    # Need P1 = 5 > available 1, and P0 need = 0 so P0 finishes -> work=2.
    # Still 2 < 5, unsafe.
    out = request_resources(s, "P0", [1])
    assert out["granted"] is False
    assert out["after"] == out["before"]
    assert out["safe_check"]["safe"] is False