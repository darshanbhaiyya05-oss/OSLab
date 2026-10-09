"""Deterministic synchronization demonstrations.

Instead of relying on real Python threads (which are nondeterministic),
each function precomputes a reproducible list of steps. The UI walks
through these steps so the same input always produces the same output.

Each step contains:
    label   — short caption (e.g. "T1 reads balance")
    actor   — which thread or "system"
    action  — human-readable description
    state   — full snapshot of the visible shared state at that moment
    note    — optional warning / annotation
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class Step:
    label: str
    actor: str
    action: str
    state: dict[str, Any] = field(default_factory=dict)
    note: str = ""


# ----------------------------------------------------------------------
# 1. Race condition — read-modify-write with a lost update
# ----------------------------------------------------------------------

def race_condition_demo(
    initial: int = 1000,
    deposit: int = 500,
    withdraw: int = 200,
) -> dict[str, Any]:
    """Return {'expected': int, 'unsafe': [Step, ...], 'safe': [Step, ...]}."""
    expected = initial + deposit - withdraw

    def snap(balance, t1_local=None, t2_local=None, lock=None):
        return {
            "balance": balance,
            "T1_local": t1_local,
            "T2_local": t2_local,
            "lock": lock,
        }

    # ---- UNSAFE (interleaved, no lock) ----
    unsafe: list[Step] = []
    unsafe.append(Step("Start", "system",
        f"Initial balance = Rs.{initial}", snap(initial)))
    unsafe.append(Step("T1 reads", "Thread A",
        f"T1 reads balance = Rs.{initial}",
        snap(initial, t1_local=initial)))
    unsafe.append(Step("T2 reads", "Thread B",
        f"T2 reads balance = Rs.{initial}  (T1 hasn't written yet!)",
        snap(initial, t1_local=initial, t2_local=initial),
        note="Both threads hold the stale value — a race is developing."))
    unsafe.append(Step("T1 computes", "Thread A",
        f"T1 computes {initial} + {deposit} = Rs.{initial + deposit}",
        snap(initial, t1_local=initial + deposit, t2_local=initial)))
    unsafe.append(Step("T2 computes", "Thread B",
        f"T2 computes {initial} - {withdraw} = Rs.{initial - withdraw}",
        snap(initial, t1_local=initial + deposit, t2_local=initial - withdraw)))
    unsafe.append(Step("T1 writes", "Thread A",
        f"T1 writes balance = Rs.{initial + deposit}",
        snap(initial + deposit, t1_local=initial + deposit,
             t2_local=initial - withdraw)))
    unsafe.append(Step("T2 writes", "Thread B",
        f"T2 writes balance = Rs.{initial - withdraw}  (overwrites T1!)",
        snap(initial - withdraw, t1_local=initial + deposit,
             t2_local=initial - withdraw),
        note=f"Lost update: deposit of Rs.{deposit} was overwritten."))
    unsafe.append(Step("Final", "system",
        f"Final balance = Rs.{initial - withdraw}, expected Rs.{expected}",
        snap(initial - withdraw),
        note="Incorrect — the race condition lost the deposit."))

    # ---- SAFE (mutex-protected) ----
    safe: list[Step] = []
    safe.append(Step("Start", "system",
        f"Initial balance = Rs.{initial}   (mutex available)",
        snap(initial, lock="free")))
    safe.append(Step("T1 acquires", "Thread A",
        "T1 acquires the mutex lock",
        snap(initial, lock="held by T1")))
    safe.append(Step("T1 reads", "Thread A",
        f"T1 reads balance = Rs.{initial}",
        snap(initial, t1_local=initial, lock="held by T1")))
    safe.append(Step("T1 writes", "Thread A",
        f"T1 computes Rs.{initial + deposit} and writes it",
        snap(initial + deposit, t1_local=initial + deposit,
             lock="held by T1")))
    safe.append(Step("T1 releases", "Thread A",
        "T1 releases the mutex lock",
        snap(initial + deposit, lock="free")))
    safe.append(Step("T2 acquires", "Thread B",
        "T2 acquires the mutex lock",
        snap(initial + deposit, lock="held by T2")))
    safe.append(Step("T2 reads", "Thread B",
        f"T2 reads balance = Rs.{initial + deposit}",
        snap(initial + deposit, t2_local=initial + deposit,
             lock="held by T2")))
    safe.append(Step("T2 writes", "Thread B",
        f"T2 computes Rs.{expected} and writes it",
        snap(expected, t2_local=expected, lock="held by T2")))
    safe.append(Step("T2 releases", "Thread B",
        "T2 releases the mutex lock",
        snap(expected, lock="free")))
    safe.append(Step("Final", "system",
        f"Final balance = Rs.{expected}",
        snap(expected),
        note="Correct — mutual exclusion serialized the critical sections."))

    return {"expected": expected, "unsafe": unsafe, "safe": safe}


# ----------------------------------------------------------------------
# 2. Semaphore — limited permits
# ----------------------------------------------------------------------

def semaphore_demo(permits: int = 3, workers: int = 5) -> list[Step]:
    steps: list[Step] = []
    available = permits
    holders: list[str] = []
    waiting: list[str] = []

    def snap():
        return {
            "permits_total": permits,
            "permits_available": available,
            "holders": list(holders),
            "waiting": list(waiting),
        }

    steps.append(Step("Init", "system",
        f"Semaphore initialized with {permits} permits.", snap()))

    for i in range(1, workers + 1):
        name = f"W{i}"
        if available > 0:
            available -= 1
            holders.append(name)
            steps.append(Step(f"{name} acquires", name,
                f"{name} acquires a permit. Available = {available}", snap()))
        else:
            waiting.append(name)
            steps.append(Step(f"{name} waits", name,
                f"{name} must wait — no permits available.", snap(),
                note=f"{name} is blocked on the semaphore."))

    release_order = [f"W{i}" for i in range(1, permits + 1)]
    for name in release_order:
        if name in holders:
            holders.remove(name)
            if waiting:
                nxt = waiting.pop(0)
                holders.append(nxt)
                steps.append(Step(f"{name} releases", name,
                    f"{name} releases. {nxt} wakes and acquires.", snap()))
            else:
                available += 1
                steps.append(Step(f"{name} releases", name,
                    f"{name} releases. Available = {available}", snap()))

    for name in list(holders):
        holders.remove(name)
        available += 1
        steps.append(Step(f"{name} releases", name,
            f"{name} releases. Available = {available}", snap()))

    steps.append(Step("Done", "system",
        f"All {workers} workers served. Available permits = {available}",
        snap()))
    return steps


# ----------------------------------------------------------------------
# 3. Producer-Consumer — bounded buffer
# ----------------------------------------------------------------------

def producer_consumer_demo(buffer_size: int = 3, items: int = 6) -> list[Step]:
    steps: list[Step] = []
    buffer: list[str] = []
    empty = buffer_size
    full = 0
    mutex = 1

    def snap():
        return {
            "buffer_size": buffer_size,
            "buffer": list(buffer),
            "empty": empty,
            "full": full,
            "mutex": mutex,
        }

    steps.append(Step("Init", "system",
        f"Buffer size = {buffer_size}. empty = {buffer_size}, full = 0, mutex = 1",
        snap()))

    for i in range(1, items + 1):
        item = f"Item{i}"

        steps.append(Step(f"Producer wants to produce {item}", "Producer",
            f"wait(empty)  — empty = {empty}", snap()))
        empty -= 1
        steps.append(Step("Producer passed empty", "Producer",
            f"empty = {empty}", snap()))
        steps.append(Step("Producer locks buffer", "Producer",
            f"wait(mutex) — mutex = {mutex} -> 0", snap()))
        mutex = 0
        buffer.append(item)
        steps.append(Step(f"Produce {item}", "Producer",
            f"buffer.append({item}) -> {buffer}", snap()))
        mutex = 1
        steps.append(Step("Producer unlocks", "Producer",
            "signal(mutex) -> mutex = 1", snap()))
        full += 1
        steps.append(Step("Producer signals full", "Producer",
            f"signal(full) -> full = {full}", snap()))

        steps.append(Step("Consumer wants an item", "Consumer",
            f"wait(full) — full = {full}", snap()))
        full -= 1
        steps.append(Step("Consumer passed full", "Consumer",
            f"full = {full}", snap()))
        mutex = 0
        steps.append(Step("Consumer locks buffer", "Consumer",
            "wait(mutex) -> mutex = 0", snap()))
        consumed = buffer.pop(0)
        steps.append(Step(f"Consume {consumed}", "Consumer",
            f"buffer.pop(0) -> {buffer}", snap()))
        mutex = 1
        steps.append(Step("Consumer unlocks", "Consumer",
            "signal(mutex) -> mutex = 1", snap()))
        empty += 1
        steps.append(Step("Consumer signals empty", "Consumer",
            f"signal(empty) -> empty = {empty}", snap()))

    steps.append(Step("Done", "system",
        f"Produced and consumed {items} items. Buffer empty again.", snap()))
    return steps


# ----------------------------------------------------------------------
# 4. Readers-Writers
# ----------------------------------------------------------------------

def readers_writers_demo() -> list[Step]:
    steps: list[Step] = []
    active_readers: list[str] = []
    active_writer: list[str | None] = [None]
    reads_done = [0]
    writes_done = [0]

    def snap():
        return {
            "active_readers": list(active_readers),
            "active_writer": active_writer[0],
            "reads_completed": reads_done[0],
            "writes_completed": writes_done[0],
        }

    steps.append(Step("Init", "system", "No readers, no writers.", snap()))

    def reader_acquire(name: str):
        active_readers.append(name)
        steps.append(Step(f"{name} starts reading", name,
            f"{name} enters. Active readers = {len(active_readers)}", snap()))

    def reader_release(name: str):
        if name in active_readers:
            active_readers.remove(name)
        reads_done[0] += 1
        steps.append(Step(f"{name} stops reading", name,
            f"{name} leaves. Active readers = {len(active_readers)}", snap()))

    def writer_acquire(name: str) -> bool:
        if active_readers:
            steps.append(Step(f"{name} waits", name,
                f"{name} must wait — {len(active_readers)} reader(s) active.",
                snap(), note="Writer blocked until all readers leave."))
            return False
        active_writer[0] = name
        steps.append(Step(f"{name} starts writing", name,
            f"{name} enters. Exclusive access.", snap()))
        return True

    def writer_release(name: str):
        if active_writer[0] == name:
            active_writer[0] = None
            writes_done[0] += 1
        steps.append(Step(f"{name} stops writing", name,
            f"{name} leaves.", snap()))

    reader_acquire("R1")
    reader_acquire("R2")
    writer_acquire("W1")            # blocks
    reader_release("R1")
    reader_release("R2")
    writer_acquire("W1")            # now enters
    writer_release("W1")
    reader_acquire("R3")
    reader_release("R3")

    steps.append(Step("Done", "system",
        f"All done. Reads completed: {reads_done[0]}, writes completed: {writes_done[0]}.",
        snap()))
    return steps