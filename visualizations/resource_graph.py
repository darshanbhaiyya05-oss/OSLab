"""Plotly directed graph for a Resource Allocation Graph (RAG)."""
from __future__ import annotations
import plotly.graph_objects as go


def build_rag(
    processes: list[str],
    resources: list[str],
    allocation: list[list[int]],   # [pid][rid] -> units held by process
    requests: list[list[int]],     # [pid][rid] -> units requested by process
) -> go.Figure:
    """Draw a bipartite graph: process circles at top, resource squares below."""
    import math

    # Node positions
    p_y, r_y = 1.0, -1.0
    p_xs = [i / max(1, len(processes) - 1) for i in range(len(processes))] \
        if len(processes) > 1 else [0.5]
    r_xs = [i / max(1, len(resources) - 1) for i in range(len(resources))] \
        if len(resources) > 1 else [0.5]

    pos: dict[str, tuple[float, float]] = {}
    for name, x in zip(processes, p_xs):
        pos[name] = (x, p_y)
    for name, x in zip(resources, r_xs):
        pos[name] = (x, r_y)

    fig = go.Figure()

    # ---- Allocation edges (resource -> process, solid blue) ----
    for i, pname in enumerate(processes):
        for j, rname in enumerate(resources):
            units = allocation[i][j]
            if units <= 0:
                continue
            x0, y0 = pos[rname]
            x1, y1 = pos[pname]
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1], mode="lines",
                line=dict(color="#3d8bfd", width=2),
                hoverinfo="text",
                text=[f"{units} unit(s) of {rname} allocated to {pname}"] * 2,
                showlegend=False,
            ))
            # Arrowhead in the middle
            mx, my = (x0 + x1) / 2, (y0 + y1) / 2
            fig.add_annotation(
                x=x1, y=y1, ax=x0, ay=y0,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2,
                arrowcolor="#3d8bfd", text="",
            )

    # ---- Request edges (process -> resource, dashed amber) ----
    for i, pname in enumerate(processes):
        for j, rname in enumerate(resources):
            units = requests[i][j]
            if units <= 0:
                continue
            x0, y0 = pos[pname]
            x1, y1 = pos[rname]
            fig.add_trace(go.Scatter(
                x=[x0, x1], y=[y0, y1], mode="lines",
                line=dict(color="#f59e0b", width=2, dash="dash"),
                hoverinfo="text",
                text=[f"{pname} requests {units} unit(s) of {rname}"] * 2,
                showlegend=False,
            ))
            fig.add_annotation(
                x=x1, y=y1, ax=x0, ay=y0,
                xref="x", yref="y", axref="x", ayref="y",
                showarrow=True, arrowhead=2, arrowsize=1.2,
                arrowcolor="#f59e0b", text="",
            )

    # ---- Nodes ----
    fig.add_trace(go.Scatter(
        x=[pos[p][0] for p in processes],
        y=[pos[p][1] for p in processes],
        mode="markers+text",
        marker=dict(symbol="circle", size=44, color="#22c55e",
                    line=dict(color="#0e1420", width=2)),
        text=processes, textposition="middle center",
        textfont=dict(color="#0e1420", size=12),
        hoverinfo="text", hovertext=processes,
        showlegend=False,
    ))
    fig.add_trace(go.Scatter(
        x=[pos[r][0] for r in resources],
        y=[pos[r][1] for r in resources],
        mode="markers+text",
        marker=dict(symbol="square", size=44, color="#a855f7",
                    line=dict(color="#0e1420", width=2)),
        text=resources, textposition="middle center",
        textfont=dict(color="#0e1420", size=12),
        hoverinfo="text", hovertext=resources,
        showlegend=False,
    ))

    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=30, b=10),
        plot_bgcolor="#0e1420",
        paper_bgcolor="#0e1420",
        font=dict(color="#e6edf3"),
        xaxis=dict(visible=False, range=[-0.15, 1.15]),
        yaxis=dict(visible=False, range=[-1.5, 1.5]),
        showlegend=False,
    )
    return fig