"""Page replacement: FIFO, LRU, Optimal."""
from __future__ import annotations


# ----------------------------------------------------------------------
# Shared helpers
# ----------------------------------------------------------------------

def _frame_table(frames: list[int | None]) -> list[int | None]:
    return list(frames)


def _build_result(
    algorithm: str,
    reference: list[int],
    num_frames: int,
    steps: list[dict],
    faults: int,
) -> dict:
    hits = len(reference) - faults
    return {
        "algorithm": algorithm,
        "reference_string": list(reference),
        "num_frames": num_frames,
        "steps": steps,
        "total_faults": faults,
        "total_hits": hits,
        "fault_rate": round(faults / len(reference) * 100, 2),
    }


# ----------------------------------------------------------------------
# FIFO
# ----------------------------------------------------------------------

def fifo(reference: list[int], num_frames: int) -> dict:
    if num_frames <= 0:
        raise ValueError("Number of frames must be positive.")

    frames: list[int | None] = [None] * num_frames
    next_slot = 0
    steps: list[dict] = []
    faults = 0

    for i, page in enumerate(reference, start=1):
        if page in frames:
            result = "HIT"
            evicted = None
            note = f"Page {page} already present in frame {frames.index(page)}."
        else:
            result = "FAULT"
            faults += 1
            evicted = frames[next_slot]
            frames[next_slot] = page
            next_slot = (next_slot + 1) % num_frames
            note = (f"Page {page} loaded into empty frame {frames.index(page)}."
                    if evicted is None
                    else f"Page {page} replaces page {evicted} (FIFO order).")

        steps.append({
            "step": i,
            "referenced_page": page,
            "frames": _frame_table(frames),
            "result": result,
            "evicted": evicted,
            "note": note,
        })

    return _build_result("FIFO", reference, num_frames, steps, faults)


# ----------------------------------------------------------------------
# LRU
# ----------------------------------------------------------------------

def lru(reference: list[int], num_frames: int) -> dict:
    if num_frames <= 0:
        raise ValueError("Number of frames must be positive.")

    frames: list[int | None] = [None] * num_frames
    last_used: dict[int, int] = {}
    steps: list[dict] = []
    faults = 0

    for i, page in enumerate(reference, start=1):
        if page in frames:
            result = "HIT"
            evicted = None
            last_used[page] = i
            note = f"Page {page} already present in frame {frames.index(page)}."
        else:
            result = "FAULT"
            faults += 1
            if None in frames:
                idx = frames.index(None)
                frames[idx] = page
                evicted = None
                note = f"Page {page} loaded into empty frame {idx}."
            else:
                victim = min(frames, key=lambda p: last_used.get(p, -1))
                idx = frames.index(victim)
                evicted = victim
                frames[idx] = page
                note = f"Page {page} replaces page {victim} (least recently used)."
            last_used[page] = i

        steps.append({
            "step": i,
            "referenced_page": page,
            "frames": _frame_table(frames),
            "result": result,
            "evicted": evicted,
            "note": note,
        })

    return _build_result("LRU", reference, num_frames, steps, faults)


# ----------------------------------------------------------------------
# Optimal (Belady's)
# ----------------------------------------------------------------------

def optimal(reference: list[int], num_frames: int) -> dict:
    if num_frames <= 0:
        raise ValueError("Number of frames must be positive.")

    frames: list[int | None] = [None] * num_frames
    steps: list[dict] = []
    faults = 0

    for i, page in enumerate(reference, start=1):
        if page in frames:
            result = "HIT"
            evicted = None
            note = f"Page {page} already present in frame {frames.index(page)}."
        else:
            result = "FAULT"
            faults += 1
            if None in frames:
                idx = frames.index(None)
                frames[idx] = page
                evicted = None
                note = f"Page {page} loaded into empty frame {idx}."
            else:
                future = reference[i:]
                victim = None
                farthest = -1
                for p in frames:
                    if p not in future:
                        victim = p
                        break
                    dist = future.index(p)
                    if dist > farthest:
                        farthest = dist
                        victim = p
                idx = frames.index(victim)
                evicted = victim
                frames[idx] = page
                note = (f"Page {page} replaces page {victim} "
                        f"(next use farthest / never).")

        steps.append({
            "step": i,
            "referenced_page": page,
            "frames": _frame_table(frames),
            "result": result,
            "evicted": evicted,
            "note": note,
        })

    return _build_result("Optimal", reference, num_frames, steps, faults)


ALGORITHMS = {
    "FIFO": fifo,
    "LRU": lru,
    "Optimal": optimal,
}