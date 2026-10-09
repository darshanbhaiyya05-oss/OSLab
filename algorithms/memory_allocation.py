"""Contiguous memory allocation: First Fit, Best Fit, Worst Fit.

Free memory is modeled as an ordered list of segments. Each segment has
[start, size, free, pid, name]. Allocation splits a segment; the request
is placed at the start of the chosen segment, and any leftover becomes a
new free segment immediately after it.
"""
from __future__ import annotations
from copy import deepcopy
from typing import Any


# ----------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------

def _blocks_from_sizes(sizes: list[int]) -> list[dict[str, Any]]:
    blocks = []
    offset = 0
    for size in sizes:
        blocks.append({
            "start": offset, "size": size, "free": True, "pid": None, "name": "",
        })
        offset += size
    return blocks


def _pick_first_fit(blocks: list[dict], size: int) -> int | None:
    for i, b in enumerate(blocks):
        if b["free"] and b["size"] >= size:
            return i
    return None


def _pick_best_fit(blocks: list[dict], size: int) -> int | None:
    best_i, best_size = None, None
    for i, b in enumerate(blocks):
        if b["free"] and b["size"] >= size:
            if best_size is None or b["size"] < best_size:
                best_i, best_size = i, b["size"]
    return best_i


def _pick_worst_fit(blocks: list[dict], size: int) -> int | None:
    worst_i, worst_size = None, None
    for i, b in enumerate(blocks):
        if b["free"] and b["size"] >= size:
            if worst_size is None or b["size"] > worst_size:
                worst_i, worst_size = i, b["size"]
    return worst_i


# ----------------------------------------------------------------------
# Core driver
# ----------------------------------------------------------------------

def _contiguous(
    free_sizes: list[int],
    requests: list[dict],
    picker,
    strategy_name: str,
) -> dict[str, Any]:
    blocks = _blocks_from_sizes(free_sizes)
    initial = deepcopy(blocks)
    allocations: list[dict] = []
    steps: list[dict] = []

    for req in requests:
        size = int(req["size"])
        idx = picker(blocks, size)

        if idx is None:
            allocations.append({**req, "success": False,
                                "block_start": None, "block_size": None,
                                "leftover": None})
            steps.append({
                "request": dict(req),
                "chosen_index": None,
                "chosen_start": None,
                "chosen_size": None,
                "leftover": None,
                "success": False,
                "blocks_before": deepcopy(blocks),
                "blocks_after": deepcopy(blocks),
                "note": (f"No free block can hold {req['name']} "
                         f"({size} KB). Request queued / rejected."),
            })
            continue

        chosen = blocks[idx]
        leftover = chosen["size"] - size
        allocated = {
            "start": chosen["start"], "size": size, "free": False,
            "pid": req["pid"], "name": req["name"],
        }

        new_blocks = blocks[:idx] + [allocated]
        if leftover > 0:
            new_blocks.append({
                "start": chosen["start"] + size, "size": leftover,
                "free": True, "pid": None, "name": "",
            })
        new_blocks.extend(blocks[idx + 1:])

        steps.append({
            "request": dict(req),
            "chosen_index": idx,
            "chosen_start": chosen["start"],
            "chosen_size": chosen["size"],
            "leftover": leftover,
            "success": True,
            "blocks_before": deepcopy(blocks),
            "blocks_after": deepcopy(new_blocks),
            "note": (f"{strategy_name} picked free block "
                     f"[{chosen['start']}, {chosen['start']+chosen['size']}] "
                     f"({chosen['size']} KB) for {req['name']} ({size} KB). "
                     f"Leftover: {leftover} KB."),
        })

        allocations.append({
            **req, "success": True,
            "block_start": chosen["start"],
            "block_size": chosen["size"],
            "leftover": leftover,
        })
        blocks = new_blocks

    total_free = sum(b["size"] for b in blocks if b["free"])
    largest_free = max((b["size"] for b in blocks if b["free"]), default=0)

    return {
        "strategy": strategy_name,
        "initial_blocks": initial,
        "final_blocks": blocks,
        "allocations": allocations,
        "steps": steps,
        "total_free": total_free,
        "largest_free": largest_free,
        "external_fragmentation": total_free - largest_free,
    }


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------

def first_fit(free_sizes: list[int], requests: list[dict]) -> dict:
    return _contiguous(free_sizes, requests, _pick_first_fit, "First Fit")


def best_fit(free_sizes: list[int], requests: list[dict]) -> dict:
    return _contiguous(free_sizes, requests, _pick_best_fit, "Best Fit")


def worst_fit(free_sizes: list[int], requests: list[dict]) -> dict:
    return _contiguous(free_sizes, requests, _pick_worst_fit, "Worst Fit")


STRATEGIES = {
    "First Fit": first_fit,
    "Best Fit": best_fit,
    "Worst Fit": worst_fit,
}