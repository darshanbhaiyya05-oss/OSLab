"""Banker's Algorithm and resource-allocation utilities.

All matrices are lists of lists of ints. The Available vector is a list of ints.
Process IDs are strings (P0..Pn).
"""
from __future__ import annotations
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


# ----------------------------------------------------------------------
# Data containers
# ----------------------------------------------------------------------

@dataclass
class SystemState:
    processes: list[str]
    resources: list[str]
    allocation: list[list[int]]
    maximum: list[list[int]]
    available: list[int]

    def need(self) -> list[list[int]]:
        return [
            [self.maximum[i][j] - self.allocation[i][j]
             for j in range(len(self.resources))]
            for i in range(len(self.processes))
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "processes": list(self.processes),
            "resources": list(self.resources),
            "allocation": deepcopy(self.allocation),
            "maximum": deepcopy(self.maximum),
            "available": list(self.available),
            "need": self.need(),
        }


# ----------------------------------------------------------------------
# Safety algorithm
# ----------------------------------------------------------------------

def is_safe(state: SystemState) -> dict[str, Any]:
    """Run the Banker's safety algorithm and return a full step trace.

    Returns:
        {
            "safe": bool,
            "safe_sequence": [pid, ...],
            "need": [[...], ...],
            "steps": [
                {
                    "step": int,
                    "work_before": [...],
                    "candidate": pid or None,
                    "need_row": [...] or None,
                    "work_after": [...],
                    "note": str,
                },
                ...
            ],
        }
    """
    n = len(state.processes)
    m = len(state.resources)
    need = state.need()
    work = list(state.available)
    finish = [False] * n
    sequence: list[str] = []
    steps: list[dict[str, Any]] = []

    step_no = 0
    while len(sequence) < n:
        # Find an unfinished process whose Need <= Work
        chosen: int | None = None
        for i in range(n):
            if finish[i]:
                continue
            if all(need[i][j] <= work[j] for j in range(m)):
                chosen = i
                break

        step_no += 1
        if chosen is None:
            remaining = [state.processes[i] for i in range(n) if not finish[i]]
            steps.append({
                "step": step_no,
                "work_before": list(work),
                "candidate": None,
                "need_row": None,
                "work_after": list(work),
                "note": (
                    "No unfinished process has Need <= Work. "
                    f"Deadlocked: {remaining}"
                ),
            })
            break

        need_row = list(need[chosen])
        work_before = list(work)
        for j in range(m):
            work[j] += state.allocation[chosen][j]

        steps.append({
            "step": step_no,
            "work_before": work_before,
            "candidate": state.processes[chosen],
            "need_row": need_row,
            "work_after": list(work),
            "note": (
                f"{state.processes[chosen]} can finish. "
                f"Work = {work_before} + {state.allocation[chosen]} = {work}"
            ),
        })
        finish[chosen] = True
        sequence.append(state.processes[chosen])

    return {
        "safe": len(sequence) == n,
        "safe_sequence": sequence,
        "need": need,
        "steps": steps,
    }


# ----------------------------------------------------------------------
# Resource-request algorithm
# ----------------------------------------------------------------------

def request_resources(
    state: SystemState,
    pid: str,
    request: list[int],
) -> dict[str, Any]:
    """Simulate a resource request from `pid`.

    Returns:
        {
            "granted": bool,
            "reason": str,
            "before": state.to_dict(),
            "after": state.to_dict(),
            "safe_check": {...},
        }
    """
    if pid not in state.processes:
        return {"granted": False, "reason": f"Unknown process {pid}",
                "before": state.to_dict(), "after": state.to_dict(),
                "safe_check": None}
    i = state.processes.index(pid)
    need = state.need()

    # 1. Request <= Need?
    for j in range(len(state.resources)):
        if request[j] > need[i][j]:
            return {
                "granted": False,
                "reason": (
                    f"Request exceeds {pid}'s remaining Need for "
                    f"{state.resources[j]} ({request[j]} > {need[i][j]})."
                ),
                "before": state.to_dict(),
                "after": state.to_dict(),
                "safe_check": None,
            }

    # 2. Request <= Available?
    for j in range(len(state.resources)):
        if request[j] > state.available[j]:
            return {
                "granted": False,
                "reason": (
                    f"Request exceeds Available {state.resources[j]} "
                    f"({request[j]} > {state.available[j]})."
                ),
                "before": state.to_dict(),
                "after": state.to_dict(),
                "safe_check": None,
            }

    # 3. Tentatively grant and run safety check
    before = state.to_dict()
    trial = SystemState(
        processes=list(state.processes),
        resources=list(state.resources),
        allocation=deepcopy(state.allocation),
        maximum=deepcopy(state.maximum),
        available=list(state.available),
    )
    for j in range(len(state.resources)):
        trial.available[j] -= request[j]
        trial.allocation[i][j] += request[j]

    check = is_safe(trial)
    if check["safe"]:
        return {
            "granted": True,
            "reason": (
                f"Request is safe. New safe sequence: {check['safe_sequence']}"
            ),
            "before": before,
            "after": trial.to_dict(),
            "safe_check": check,
        }
    return {
        "granted": False,
        "reason": (
            "Granting this request would leave the system in an unsafe state. "
            "Request rolled back."
        ),
        "before": before,
        "after": before,          # rollback
        "safe_check": check,
    }


# ----------------------------------------------------------------------
# Reference example — the classic Silberschatz 5x3 case
# ----------------------------------------------------------------------

def sample_state() -> SystemState:
    return SystemState(
        processes=["P0", "P1", "P2", "P3", "P4"],
        resources=["A", "B", "C"],
        allocation=[
            [0, 1, 0],
            [2, 0, 0],
            [3, 0, 2],
            [2, 1, 1],
            [0, 0, 2],
        ],
        maximum=[
            [7, 5, 3],
            [3, 2, 2],
            [9, 0, 2],
            [2, 2, 2],
            [4, 3, 3],
        ],
        available=[3, 3, 2],
    )