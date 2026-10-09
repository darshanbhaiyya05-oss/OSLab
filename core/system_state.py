"""Shared virtual OS state. Session-scoped (Streamlit session_state backed)."""
from __future__ import annotations
from typing import Any
from .process import Process
from .event_log import EventLog


def default_state() -> dict[str, Any]:
    return {
        "processes": [],          # list[Process]
        "resources": {},          # name -> {total, available, allocated}
        "memory": {},             # filled by memory module
        "files": {},              # virtual file tree
        "disk_requests": [],
        "event_log": EventLog(),
        "last_simulation": None,  # most recent result dict (any module)
    }


def get_state(session_state) -> dict[str, Any]:
    if "oslab" not in session_state:
        session_state["oslab"] = default_state()
    return session_state["oslab"]


def reset_state(session_state) -> None:
    session_state["oslab"] = default_state()