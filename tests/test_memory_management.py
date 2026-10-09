"""Tests for memory allocation, paging, segmentation, and page replacement."""
import pytest
from algorithms.memory_allocation import first_fit, best_fit, worst_fit
from algorithms.paging import translate_address
from algorithms.segmentation import translate_segment
from algorithms.page_replacement import fifo, lru, optimal


REQS = [
    {"pid": 1, "name": "P1", "size": 180},
    {"pid": 2, "name": "P2", "size": 120},
    {"pid": 3, "name": "P3", "size": 90},
]


# ----------------------------------------------------------------------
# Contiguous allocation
# ----------------------------------------------------------------------

def test_first_fit_picks_first_matching_block():
    r = first_fit([100, 500, 200, 300], REQS[:1])
    # P1 (180) should land in the 500 block at offset 100
    assert r["allocations"][0]["block_start"] == 100
    assert r["allocations"][0]["block_size"] == 500
    # Final layout: [100 free, 180 P1, 320 free, 200 free, 300 free]
    sizes = [b["size"] for b in r["final_blocks"]]
    assert sizes == [100, 180, 320, 200, 300]


def test_best_fit_picks_smallest_fitting_block():
    r = best_fit([100, 500, 200, 300], REQS[:1])
    # 200 KB block is the smallest that fits 180
    assert r["allocations"][0]["block_start"] == 600
    assert r["allocations"][0]["block_size"] == 200


def test_worst_fit_picks_largest_fitting_block():
    r = worst_fit([100, 500, 200, 300], REQS[:1])
    # 500 KB block is the largest
    assert r["allocations"][0]["block_size"] == 500


def test_rejected_when_no_block_fits():
    r = first_fit([100, 200], [{"pid": 1, "name": "P1", "size": 500}])
    assert r["allocations"][0]["success"] is False
    assert r["total_free"] == 300


def test_external_fragmentation_calculation():
    r = first_fit([100, 500, 200, 300], REQS)

    # After all three allocations, the free blocks are: 10, 200, 200, 300
    # (P3 fit into the leftover 100 from the initial layout, leaving 10.)
    assert r["total_free"] == 710
    assert r["largest_free"] == 300
    assert r["external_fragmentation"] == 710 - 300   # 410

    # Sanity check: sum of all block sizes is conserved
    total_memory = sum(b["size"] for b in r["final_blocks"])
    assert total_memory == 100 + 500 + 200 + 300      # 1100


# ----------------------------------------------------------------------
# Paging
# ----------------------------------------------------------------------

def test_paging_translation():
    page_table = {0: 3, 1: 4, 2: 5, 3: 6}
    out = translate_address(2500, 1024, page_table)
    assert out["page_number"] == 2
    assert out["offset"] == 452
    assert out["frame_number"] == 5
    assert out["physical_address"] == 5 * 1024 + 452   # 5572
    assert out["valid"] is True


def test_paging_fault():
    page_table = {0: 3}
    out = translate_address(2500, 1024, page_table)
    assert out["page_number"] == 2
    assert out["valid"] is False
    assert out["physical_address"] is None


def test_paging_rejects_negative():
    with pytest.raises(ValueError):
        translate_address(-1, 1024, {})
    with pytest.raises(ValueError):
        translate_address(0, 0, {})


# ----------------------------------------------------------------------
# Segmentation
# ----------------------------------------------------------------------

def test_segmentation_valid():
    table = {1: {"name": "data", "base": 2000, "limit": 800}}
    out = translate_segment(1, 100, table)
    assert out["valid"] is True
    assert out["physical_address"] == 2100


def test_segmentation_offset_out_of_range():
    table = {1: {"name": "data", "base": 2000, "limit": 800}}
    out = translate_segment(1, 900, table)
    assert out["valid"] is False
    assert out["physical_address"] is None


def test_segmentation_missing_segment():
    out = translate_segment(9, 0, {})
    assert out["valid"] is False


# ----------------------------------------------------------------------
# Page replacement
# ----------------------------------------------------------------------

REF = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]


def test_fifo_known_result():
    r = fifo(REF, 3)
    assert r["total_faults"] == 9
    assert r["total_hits"] == 3


def test_lru_known_result():
    r = lru(REF, 3)
    assert r["total_faults"] == 10
    assert r["total_hits"] == 2


def test_optimal_known_result():
    r = optimal(REF, 3)
    assert r["total_faults"] == 7
    assert r["total_hits"] == 5


def test_optimal_never_worse_than_others():
    o = optimal(REF, 3)["total_faults"]
    f = fifo(REF, 3)["total_faults"]
    l = lru(REF, 3)["total_faults"]
    assert o <= min(f, l)


def test_invalid_frame_count():
    with pytest.raises(ValueError):
        fifo(REF, 0)
    with pytest.raises(ValueError):
        lru(REF, -1)