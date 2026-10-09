"""Plotly Gantt chart from actual execution segments."""
from __future__ import annotations
import plotly.graph_objects as go
from core.process import Process, ProcessState

STATE_COLORS = {
    "IDLE": "#2a3446",
    ProcessState.NEW.value:        "#7e8ba3",
    ProcessState.READY.value:      "#3d8bfd",
    ProcessState.RUNNING.value:    "#22c55e",
    ProcessState.WAITING.value:    "#f59e0b",
    ProcessState.TERMINATED.value: "#a855f7",
}

_PROCESS_PALETTE = [
    "#3d8bfd", "#22c55e", "#f59e0b", "#a855f7",
    "#ef4444", "#06b6d4", "#eab308", "#ec4899",
]


def _color_for(process_name: str, index_map: dict[str, int]) -> str:
    if process_name == "IDLE":
        return STATE_COLORS["IDLE"]
    idx = index_map.setdefault(process_name, len(index_map))
    return _PROCESS_PALETTE[idx % len(_PROCESS_PALETTE)]


def build_gantt(segments: list[dict], processes: list[Process]) -> go.Figure:
    index_map = {p.name: i for i, p in enumerate(sorted(processes, key=lambda x: x.pid))}
    fig = go.Figure()

    for seg in segments:
        name = seg["process"]
        color = _color_for(name, index_map)
        fig.add_trace(go.Bar(
            x=[seg["end"] - seg["start"]],
            y=["CPU"],
            base=[seg["start"]],
            orientation="h",
            marker=dict(color=color, line=dict(color="#0e1420", width=1)),
            hovertemplate=(
                f"<b>{name}</b><br>"
                f"Start: {seg['start']}<br>"
                f"End: {seg['end']}<br>"
                f"Duration: {seg['end'] - seg['start']}"
                "<extra></extra>"
            ),
            showlegend=False,
        ))
        # Label
        mid = (seg["start"] + seg["end"]) / 2
        fig.add_annotation(
            x=mid, y="CPU", text=name, showarrow=False,
            font=dict(color="white", size=12),
        )

    total = max((s["end"] for s in segments), default=0)
    fig.update_layout(
        barmode="overlay",
        height=180,
        margin=dict(l=10, r=10, t=30, b=30),
        plot_bgcolor="#0e1420",
        paper_bgcolor="#0e1420",
        font=dict(color="#e6edf3"),
        xaxis=dict(
            title="Virtual Time",
            range=[0, total],
            gridcolor="#1f2a3a",
            zerolinecolor="#1f2a3a",
            tickmode="linear",
        ),
        yaxis=dict(showticklabels=False, gridcolor="#1f2a3a"),
        showlegend=False,
    )
    return fig