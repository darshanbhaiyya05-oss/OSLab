"""Tests for disk scheduling algorithms."""
import pytest
from algorithms.disk_scheduling import fcfs, sstf, scan, c_scan


REQS = [98, 183, 37, 122, 14, 124, 65, 67]
HEAD = 53
SIZE = 200


# ----------------------------------------------------------------------
# FCFS
# ----------------------------------------------------------------------

def test_fcfs_sequence_matches_arrival_order():
    r = fcfs(HEAD, REQS, SIZE)
    assert r["sequence"] == [HEAD] + REQS


def test_fcfs_total_movement():
    r = fcfs(HEAD, REQS, SIZE)
    # 53->98: 45; 98->183: 85; 183->37: 146; 37->122: 85; 122->14: 108;
    # 14->124: 110; 124->65: 59; 65->67: 2
    assert r["total_movement"] == 45+85+146+85+108+110+59+2


# ----------------------------------------------------------------------
# SSTF
# ----------------------------------------------------------------------

def test_sstf_first_pick_is_closest():
    r = sstf(HEAD, REQS, SIZE)
    # From 53, closest is 65 (distance 12). Sequence [53, 65, ...]
    assert r["sequence"][1] == 65


def test_sstf_visits_all_requests_exactly_once():
    r = sstf(HEAD, REQS, SIZE)
    assert sorted(r["sequence"][1:]) == sorted(REQS)


# ----------------------------------------------------------------------
# SCAN
# ----------------------------------------------------------------------

def test_scan_right_services_upper_then_lower():
    r = scan(HEAD, REQS, SIZE, direction="right")
    # Upper half (>=53) ascending: 65, 67, 98, 122, 124, 183
    # Lower half (<53) descending: 37, 14
    assert r["sequence"] == [HEAD, 65, 67, 98, 122, 124, 183, 37, 14]


def test_scan_with_boundary_adds_boundary_stop():
    r = scan(HEAD, REQS, SIZE, direction="right", count_boundary=True)
    assert SIZE - 1 in r["sequence"]


def test_scan_invalid_direction():
    with pytest.raises(ValueError):
        scan(HEAD, REQS, SIZE, direction="up")


# ----------------------------------------------------------------------
# C-SCAN
# ----------------------------------------------------------------------

def test_cscan_right_services_upper_then_lower():
    r = c_scan(HEAD, REQS, SIZE, direction="right")
    # Upper half (>=53) ascending: 65, 67, 98, 122, 124, 183
    # Lower half (<53) ascending: 14, 37
    assert r["sequence"] == [HEAD, 65, 67, 98, 122, 124, 183, 14, 37]


def test_cscan_all_requests_visited():
    r = c_scan(HEAD, REQS, SIZE, direction="right")
    assert sorted(r["sequence"][1:]) == sorted(REQS)


# ----------------------------------------------------------------------
# Validation
# ----------------------------------------------------------------------

def test_out_of_range_request_rejected():
    with pytest.raises(ValueError):
        fcfs(HEAD, [500], SIZE)
    with pytest.raises(ValueError):
        fcfs(-1, REQS, SIZE)
    with pytest.raises(ValueError):
        fcfs(HEAD, REQS, 0)


# ----------------------------------------------------------------------
# Invariants
# ----------------------------------------------------------------------

@pytest.mark.parametrize("algo", [fcfs, sstf, scan, c_scan])
def test_total_equals_sum_of_movements(algo):
    r = algo(HEAD, REQS, SIZE)
    assert r["total_movement"] == sum(r["movements"])


@pytest.mark.parametrize("algo", [fcfs, sstf, scan, c_scan])
def test_average_is_total_over_steps(algo):
    r = algo(HEAD, REQS, SIZE)
    if r["movements"]:
        assert abs(r["average_movement"] - r["total_movement"] / len(r["movements"])) < 0.001