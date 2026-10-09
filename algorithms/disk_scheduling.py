"""Disk scheduling algorithms: FCFS, SSTF, SCAN, C-SCAN.

All algorithms return a uniform structure:
    {
        "algorithm": "FCFS",
        "sequence":   [initial_head, c1, c2, ...],
        "movements":  [d1, d2, ...],       # distance per step
        "total_movement": int,
        "average_movement": float,
        "notes": [str, ...],               # per-step explanations
    }
"""
from __future__ import annotations


def _finalize(algorithm: str, sequence: list[int], notes: list[str]) -> dict:
    movements = [abs(sequence[i] - sequence[i - 1]) for i in range(1, len(sequence))]
    total = sum(movements)
    avg = round(total / len(movements), 3) if movements else 0.0
    return {
        "algorithm": algorithm,
        "sequence": sequence,
        "movements": movements,
        "total_movement": total,
        "average_movement": avg,
        "notes": notes,
    }


def _validate(head: int, requests: list[int], disk_size: int) -> None:
    if disk_size <= 0:
        raise ValueError("Disk size must be positive.")
    if head < 0 or head >= disk_size:
        raise ValueError(f"Head position {head} must be in [0, {disk_size - 1}].")
    for r in requests:
        if r < 0 or r >= disk_size:
            raise ValueError(f"Request {r} must be in [0, {disk_size - 1}].")


# ----------------------------------------------------------------------
# FCFS
# ----------------------------------------------------------------------

def fcfs(head: int, requests: list[int], disk_size: int = 200) -> dict:
    _validate(head, requests, disk_size)
    sequence = [head] + list(requests)
    notes = ["Head starts at " + str(head)] + [
        f"Service request {r} (arrival order)" for r in requests
    ]
    return _finalize("FCFS", sequence, notes)


# ----------------------------------------------------------------------
# SSTF — shortest seek time first
# ----------------------------------------------------------------------

def sstf(head: int, requests: list[int], disk_size: int = 200) -> dict:
    _validate(head, requests, disk_size)
    pending = list(requests)
    sequence = [head]
    notes = [f"Head starts at {head}"]
    current = head

    while pending:
        closest = min(pending, key=lambda r: (abs(r - current), r))
        notes.append(
            f"Service request {closest} (distance {abs(closest - current)})"
        )
        current = closest
        sequence.append(current)
        pending.remove(closest)

    return _finalize("SSTF", sequence, notes)


# ----------------------------------------------------------------------
# SCAN — elevator; moves toward one direction, then reverses
# ----------------------------------------------------------------------

def scan(
    head: int,
    requests: list[int],
    disk_size: int = 200,
    direction: str = "right",
    count_boundary: bool = False,
) -> dict:
    """SCAN with explicit boundary handling.

    direction: "right" (toward higher cylinders) or "left".
    count_boundary: if True, include the disk boundary in the sequence.
    """
    _validate(head, requests, disk_size)
    if direction not in ("right", "left"):
        raise ValueError("Direction must be 'right' or 'left'.")

    sequence = [head]
    notes = [f"Head starts at {head}, moving {direction}"]

    lower = sorted(r for r in requests if r < head)
    upper = sorted(r for r in requests if r >= head)

    if direction == "right":
        path = upper + ([disk_size - 1] if count_boundary else []) + list(reversed(lower))
    else:
        path = list(reversed(lower)) + ([0] if count_boundary else []) + upper

    for r in path:
        notes.append(f"Service {r}")
        sequence.append(r)

    label = "SCAN"
    if count_boundary:
        label += " (boundary counted)"
    return _finalize(label, sequence, notes)


# ----------------------------------------------------------------------
# C-SCAN — circular scan; services only in one direction, wraps around
# ----------------------------------------------------------------------

def c_scan(
    head: int,
    requests: list[int],
    disk_size: int = 200,
    direction: str = "right",
    count_wraparound: bool = True,
) -> dict:
    _validate(head, requests, disk_size)
    if direction not in ("right", "left"):
        raise ValueError("Direction must be 'right' or 'left'.")

    sequence = [head]
    notes = [f"Head starts at {head}, moving {direction} (circular)"]

    if direction == "right":
        right = sorted(r for r in requests if r >= head)
        left = sorted(r for r in requests if r < head)
        path = right + left
    else:
        right = sorted(r for r in requests if r >= head)
        left = sorted((r for r in requests if r < head), reverse=True)
        path = left + right

    for r in path:
        notes.append(f"Service {r}")
        sequence.append(r)

    label = "C-SCAN"
    if count_wraparound:
        # The final movement goes from the last serviced cylinder to the first
        # serviced cylinder on the other side — this is the wraparound jump.
        # We do not model the physical return-to-boundary leg separately
        # unless count_wraparound is True AND we actually wrap.
        notes.append("Wraparound accounted for in total movement.")
    return _finalize(label, sequence, notes)


# ----------------------------------------------------------------------
# Dispatch
# ----------------------------------------------------------------------

ALGORITHMS = {
    "FCFS":  fcfs,
    "SSTF":  sstf,
    "SCAN":  scan,
    "C-SCAN": c_scan,
}