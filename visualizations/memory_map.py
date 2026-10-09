"""Plotly horizontal memory map. Free blocks are green; allocated are blue."""
from __future__ import annotations
import plotly.graph_objects as go


def build_memory_map(blocks: list[dict], title: str = "") -> go.Figure:
    fig = go.Figure()

    if not blocks:
        fig.update_layout(
            height=160,
            plot_bgcolor="#0e1420", paper_bgcolor="#0e1420",
            font=dict(color="#e6edf3"),
            xaxis=dict(visible=False), yaxis=dict(visible=False),
            showlegend=False,
        )
        return fig

    for b in blocks:
        is_free = b["free"]
        color = "#22c55e" if is_free else "#3d8bfd"
        label = "FREE" if is_free else (b["name"] or f"P{b.get('pid')}")

        fig.add_trace(go.Bar(
            x=[b["size"]],
            y=["Memory"],
            base=[b["start"]],
            orientation="h",
            marker=dict(color=color, line=dict(color="#0e1420", width=1)),
            hovertemplate=(
                f"<b>{label}</b><br>"
                f"Start: {b['start']} KB<br>"
                f"Size: {b['size']} KB<br>"
                f"End: {b['start'] + b['size']} KB"
                "<extra></extra>"
            ),
            showlegend=False,
        ))

        # Only add label if block is wide enough to fit
        if b["size"] >= max(3, (blocks[-1]["start"] + blocks[-1]["size"]) * 0.02):
            mid = b["start"] + b["size"] / 2
            fig.add_annotation(
                x=mid, y="Memory", text=label, showarrow=False,
                font=dict(color="white", size=11),
            )

    total = blocks[-1]["start"] + blocks[-1]["size"]
    fig.update_layout(
        barmode="overlay",
        height=160,
        margin=dict(l=10, r=10, t=30 if title else 10, b=30),
        plot_bgcolor="#0e1420",
        paper_bgcolor="#0e1420",
        font=dict(color="#e6edf3"),
        title=dict(text=title, x=0.0, font=dict(size=13, color="#cfd8e3"))
            if title else None,
        xaxis=dict(
            title="Physical Memory (KB)",
            range=[0, total],
            gridcolor="#1f2a3a",
            zerolinecolor="#1f2a3a",
        ),
        yaxis=dict(showticklabels=False, gridcolor="#1f2a3a"),
        showlegend=False,
    )
    return fig