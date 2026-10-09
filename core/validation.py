"""Reusable validation helpers."""
from __future__ import annotations
from typing import Iterable


class ValidationError(ValueError):
    pass


def validate_process_fields(
    pid: int,
    arrival_time: int,
    burst_time: int,
    priority: int = 0,
    memory_required: int = 0,
) -> None:
    errors = []
    if burst_time <= 0:
        errors.append("Burst time must be a positive integer.")
    if arrival_time < 0:
        errors.append("Arrival time cannot be negative.")
    if memory_required < 0:
        errors.append("Memory requirement cannot be negative.")
    if priority < 0:
        errors.append("Priority cannot be negative.")
    if errors:
        raise ValidationError(" ".join(errors))


def validate_time_quantum(quantum: int) -> None:
    if quantum <= 0:
        raise ValidationError("Time quantum must be a positive integer.")


def validate_unique_pids(pids: Iterable[int]) -> None:
    pids = list(pids)
    if len(pids) != len(set(pids)):
        raise ValidationError("Duplicate process IDs are not allowed.")