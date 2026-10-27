from math import cos, pi, sin

from IPython.display import HTML
from networkx import DiGraph, Graph, draw, layout
from networkx import draw_networkx_edge_labels as draw_edge_labels
from networkx import draw_networkx_edges as draw_edges
from networkx import draw_networkx_labels as draw_labels
import numpy as np


def draw_graph(graph, ax=None, node_labels=None):
    n = len(graph["nodes"])
    if n == 0:
        raise ValueError("Graph has no nodes to draw.")

    # Compute layered circular layout
    m = max(1, n // 5)  # Avoid division by zero for small graphs
    pos = {
        i: (
            cos(-(i * 2 * pi * m) / n + 0.5 * pi) / (i * m // n + 1),
            sin(-(i * 2 * pi * m) / n + 0.5 * pi) / (i * m // n + 1),
        )
        for i in graph["nodes"]
    }

    # Compute normalized colors
    if node_labels is not None:
        # Convert labels to numeric codes (A=0, B=1, etc.) and normalize
        raw_colors = np.array([ord(node_labels[i].upper()) - 65 for i in graph["nodes"]])
        norm_colors = (raw_colors - raw_colors.min()) / (raw_colors.max() - raw_colors.min() + 1e-9)
    else:
        # Use evenly spaced colors if no labels provided
        norm_colors = np.linspace(0, 1, n)

    # Create a new axis if needed
    if ax is None:
        _, ax = plt.subplots(figsize=(6, 6))

    # Draw the graph with normalized color mapping
    draw(
        Graph(graph["edges"]),
        pos=pos,
        ax=ax,
        with_labels=True,
        font_color="white",
        node_color=norm_colors,
        cmap="tab10",
    )


def draw_network(network, ax=None, edge_flows=None):
    g = DiGraph(network["edges"].keys())
    pos = layout.kamada_kawai_layout(g, weight=None)

    # Draw highlights for edges with a flow
    if edge_flows is not None:
        edges = {e for e, v in edge_flows.items() if v > 0}
        draw_edges(
            g,
            pos=pos,
            ax=ax,
            edgelist=edges,
            width=10,
            edge_color="lightblue",
            style="solid",
            alpha=None,
            arrowstyle="-",
        )

    # Draw nodes and edges
    draw(g, pos=pos, ax=ax, with_labels=True, font_color="white")

    # Draw node supply / demand attribute labels
    cmap = {0: "gray", -1: "red", 1: "green"}
    shifted_pos = {i: (x, y - 0.08) for i, (x, y) in pos.items()}

    values = {i: data.get("b", 0) for i, data in network["nodes"].items()}
    labels = {i: f"b={value}" for i, value in values.items()}

    for k, color in cmap.items():
        nodes = {i for i, value in values.items() if np.sign(value) == k}

        draw_labels(
            g,
            ax=ax,
            pos={i: shifted_pos[i] for i in nodes},
            labels={i: labels[i] for i in nodes},
            font_color=color,
            font_weight="bold",
        )

    if edge_flows is None:
        draw_edge_labels(
            g,
            pos=pos,
            ax=ax,
            font_size=9,
            edge_labels={
                i: ",".join(f"{k}={v}" for k, v in data.items())
                for i, data in network["edges"].items()
            },
        )
    else:
        draw_edge_labels(
            g, pos=pos, ax=ax, font_size=11, font_weight="bold", edge_labels=edge_flows
        )


def display_side_by_side(dfs: list, captions: list):
    output = ""
    combined = dict(zip(captions, dfs))
    for caption, df in combined.items():
        output += (
            df.style.set_table_attributes("style='display:inline'")
            .set_caption(caption)
            ._repr_html_()
        )
        output += "\xa0\xa0\xa0"
    display(HTML(output))
