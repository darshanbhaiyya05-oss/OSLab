# OSLab — Virtual Operating System Simulator

An interactive, visual laboratory for learning operating-system concepts.
Built with **Python**, **Streamlit**, **Plotly**, **Pandas**, and **Pytest**.

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![Streamlit](https://img.shields.io/badge/streamlit-1.30%2B-red)
![Tests](https://img.shields.io/badge/tests-79%20passing-brightgreen)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Overview

OSLab is a user-space simulator of operating-system mechanisms. It makes
the invisible decisions of an OS visible: process scheduling, synchronization,
deadlock avoidance, memory allocation, virtual memory, file management, and
disk scheduling — all in one connected virtual system.

It is **not** a real kernel. It is a teaching tool that models OS decisions
with deterministic, reproducible simulations.

---

## Modules

| # | Module | Highlights |
|---|--------|-----------|
| 0 | Dashboard | Virtual system overview, event log, module launcher |
| 1 | Process Management | PCB, state machine (NEW → READY → RUNNING → WAITING → TERMINATED), live table |
| 2 | CPU Scheduling | FCFS, SJF, SRTF, Priority (preemptive + non-preemptive), Round Robin with Gantt chart and comparison |
| 3 | Synchronization | Race condition vs mutex, semaphore, producer–consumer, readers–writers (deterministic step-through) |
| 4 | Deadlock Analyzer | Banker's Algorithm with step-by-step safe-sequence trace, resource-request rollback, Resource Allocation Graph |
| 5 | Memory Management | First Fit / Best Fit / Worst Fit, paging address translation, segmentation |
| 6 | Virtual Memory | FIFO / LRU / Optimal page replacement with frame tables and fault-rate comparison |
| 7 | File & Disk Management | In-memory directory tree; FCFS / SSTF / SCAN / C-SCAN disk scheduling |
| 8 | System Software | Compiler → Assembler → Linker → Loader pipeline, OS services, system-call concepts |
| – | Reports & Exports | Session summary, JSON snapshots, CSV downloads |

---

## Quick Start

### Prerequisites

- Python 3.10 or newer
- Git (for cloning)

### Setup

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/OSLab.git
cd OSLab

# 2. Create and activate a virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1        # Windows PowerShell
# source .venv/bin/activate        # macOS / Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Launch the app
streamlit run app.py