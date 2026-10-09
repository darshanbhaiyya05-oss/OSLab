"""Timestamped virtual event log."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass
class Event:
    time: int
    message: str


class EventLog:
    def __init__(self) -> None:
        self.events: List[Event] = []

    def record(self, time: int, message: str) -> None:
        self.events.append(Event(time=time, message=message))

    def clear(self) -> None:
        self.events.clear()

    def to_list(self) -> list[dict]:
        return [{"time": e.time, "message": e.message} for e in self.events]

    def render_lines(self) -> list[str]:
        return [f"{e.time:>04d}  {e.message}" for e in self.events]