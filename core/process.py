"""Process record and valid state transitions (simulated PCB)."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ProcessState(str, Enum):
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"


VALID_TRANSITIONS: dict[ProcessState, set[ProcessState]] = {
    ProcessState.NEW:        {ProcessState.READY},
    ProcessState.READY:      {ProcessState.RUNNING},
    ProcessState.RUNNING:    {ProcessState.READY, ProcessState.WAITING, ProcessState.TERMINATED},
    ProcessState.WAITING:    {ProcessState.READY},
    ProcessState.TERMINATED: set(),
}


@dataclass
class Process:
    pid: int
    name: str
    arrival_time: int
    burst_time: int
    priority: int = 0
    memory_required: int = 0
    state: ProcessState = ProcessState.NEW
    remaining_time: int = field(default=-1)

    # Metric fields (filled by the scheduler)
    start_time: Optional[int] = None
    completion_time: Optional[int] = None
    waiting_time: int = 0
    turnaround_time: int = 0
    response_time: int = 0

    def __post_init__(self) -> None:
        if self.remaining_time < 0:
            self.remaining_time = self.burst_time

    def transition_to(self, new_state: ProcessState) -> None:
        """Enforce valid state transitions."""
        if new_state not in VALID_TRANSITIONS[self.state]:
            raise ValueError(
                f"Invalid state transition: {self.state.value} -> {new_state.value}"
            )
        self.state = new_state

    def to_dict(self) -> dict:
        return {
            "pid": self.pid,
            "name": self.name,
            "state": self.state.value,
            "arrival_time": self.arrival_time,
            "burst_time": self.burst_time,
            "priority": self.priority,
            "memory_required": self.memory_required,
            "remaining_time": self.remaining_time,
            "completion_time": self.completion_time,
            "waiting_time": self.waiting_time,
            "turnaround_time": self.turnaround_time,
            "response_time": self.response_time,
        }