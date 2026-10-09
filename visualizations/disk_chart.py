"""Plotly line chart showing disk head movement."""
from __future__ import annotations
import plotly.graph_objects as go


def build_disk_chart(result: dict) -> go.Figure:
    seq = result["sequence"]
    x = list(range(len(seq)))
    y = seq

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x, y=y,
        mode="lines+markers",
        line=dict(color="#3d8bfd", width=2),
        marker=dict(size=9, color="#22c55e",
                    line=dict(color="#0e1420", width=1)),
        hovertemplate="Step %{x}<br>Cylinder %{y}<extra></extra>",
        showlegend=False,
    ))

    # Label each request
    for i, cyl in enumerate(seq):
        fig.add_annotation(
            x=i, y=cyl, text=str(cyl), showarrow=False,
            yshift=14, font=dict(color="#e6edf3", size=10),
        )

    fig.update_layout(
        height=340,
        margin=dict(l=10, r=10, t=30, b=30),
        plot_bgcolor="#0e1420",
        paper_bgcolor="#0e1420",
        font=dict(color="#e6edf3"),
        xaxis=dict(title="Service Order",
                   gridcolor="#1f2a3a", zerolinecolor="#1f2a3a"),
        yaxis=dict(title="Cylinder",
                   gridcolor="#1f2a3a", zerolinecolor="#1f2a3a"),
    )
    return fig