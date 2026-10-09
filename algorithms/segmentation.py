"""Segmentation: (segment number, offset) -> physical address."""
from __future__ import annotations


def translate_segment(
    segment_number: int,
    offset: int,
    segment_table: dict[int, dict],
) -> dict:
    """segment_table: {seg_num: {"name": str, "base": int, "limit": int}}."""
    entry = segment_table.get(segment_number)

    if entry is None:
        return {
            "segment_number": segment_number,
            "offset": offset,
            "segment": None,
            "physical_address": None,
            "valid": False,
            "note": f"Segment {segment_number} does not exist.",
        }

    if offset < 0 or offset >= entry["limit"]:
        return {
            "segment_number": segment_number,
            "offset": offset,
            "segment": entry,
            "physical_address": None,
            "valid": False,
            "note": (
                f"Offset {offset} is outside segment {segment_number} "
                f"({entry['name']}, limit = {entry['limit']}). Segmentation fault."
            ),
        }

    physical = entry["base"] + offset
    return {
        "segment_number": segment_number,
        "offset": offset,
        "segment": entry,
        "physical_address": physical,
        "valid": True,
        "note": (
            f"Physical = base {entry['base']} + offset {offset} = {physical}."
        ),
    }