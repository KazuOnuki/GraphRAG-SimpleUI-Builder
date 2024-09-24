from typing import Any

import networkx as nx
import plotly.graph_objects as go
from plotly.basedatatypes import BaseFigure


def visualize_graph(G) -> BaseFigure:

    BACKGROUND_COLOR = "#2D2A2E"
    NODE_COLOR = "#66D9EF"
    EDGE_COLOR = "#A6E22E"
    TEXT_COLOR = "#F8F8F2"

    pos: dict[Any, Any] = nx.spring_layout(G, dim=2)

    edge_x: list = []
    edge_y: list = []
    edge_texts: dict[Any, Any] = nx.get_edge_attributes(G, "description")
    to_display_edge_texts = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)
        to_display_edge_texts.append(edge_texts[edge])

    edge_trace = go.Scatter(
        x=edge_x,
        y=edge_y,
        text=to_display_edge_texts,
        line=dict(width=0.5, color=EDGE_COLOR),
        hoverinfo="text",
        mode="lines",
    )
    node_x = []
    node_y = []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_adjacencies = []
    node_text = []
    node_size = []
    for _, adjacencies in enumerate(G.adjacency()):
        degree = len(adjacencies[1])
        node_adjacencies.append(degree)
        node_text.append(adjacencies[0])
        node_size.append(
            20 if degree < 5 else (35 if degree < 10 else 65)
        )  # *Node size

    node_trace = go.Scatter(
        x=node_x,
        y=node_y,
        mode="markers+text",
        hoverinfo="text",
        text=node_text,
        marker=dict(
            showscale=True,
            colorscale=[[0, NODE_COLOR], [1, NODE_COLOR]],
            size=node_size,  # *Node size based on degree
            color=[len(list(G.adj[node])) for node in G.nodes()],
            line_width=2,
        ),
        textfont=dict(
            family="Courier New, monospace",
            size=12,  # *Text font size increased
            color=TEXT_COLOR,  # *Text color
        ),
        textposition="top center",
    )

    fig: BaseFigure = go.Figure(
        data=[edge_trace, node_trace],
        layout=go.Layout(
            showlegend=False,
            hovermode="closest",
            plot_bgcolor=BACKGROUND_COLOR,  # *Background color
            paper_bgcolor=BACKGROUND_COLOR,  # *Paper background
            font=dict(color=TEXT_COLOR),  # *Global text color
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        ),
    )
    fig.update_layout(autosize=True)
    return fig
