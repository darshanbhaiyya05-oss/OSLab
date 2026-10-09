"""Paging: virtual-to-physical address translation."""
from __future__ import annotations


def translate_address(
    virtual_address: int,
    page_size: int,
    page_table: dict[int, int | None],
) -> dict:
    """Return a step-by-step translation result.

    page_table maps page number -> frame number (or None if not present).
    """
    if page_size <= 0:
        raise ValueError("Page size must be positive.")
    if virtual_address < 0:
        raise ValueError("Virtual address cannot be negative.")

    page_number = virtual_address // page_size
    offset = virtual_address % page_size
    frame_number = page_table.get(page_number)

    if frame_number is None:
        return {
            "virtual_address": virtual_address,
            "page_size": page_size,
            "page_number": page_number,
            "offset": offset,
            "frame_number": None,
            "physical_address": None,
            "valid": False,
            "note": (f"Page {page_number} is not resident in any frame. "
                     f"Page fault — the OS would load it from disk."),
        }

    physical_address = frame_number * page_size + offset
    return {
        "virtual_address": virtual_address,
        "page_size": page_size,
        "page_number": page_number,
        "offset": offset,
        "frame_number": frame_number,
        "physical_address": physical_address,
        "valid": True,
        "note": (
            f"Page = floor({virtual_address} / {page_size}) = {page_number}; "
            f"Offset = {virtual_address} mod {page_size} = {offset}; "
            f"Frame = {frame_number}; "
            f"Physical = {frame_number} * {page_size} + {offset} = {physical_address}."
        ),
    }