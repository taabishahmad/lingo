"""Interaction networks -- the project's main experimental lever.

Who is allowed to talk to whom decides whether the whole population converges
on one global language or splits into regional dialects.
"""

from __future__ import annotations

import math
import random

import networkx as nx

# The three structures compared in the study.
NETWORK_TYPES = ("fully_connected", "grid", "small_world")


def build_network(network_type: str, num_agents: int) -> nx.Graph:
    """Return a graph whose nodes are agent ids and whose edges are the
    allowed communication channels."""
    if network_type == "fully_connected":
        return nx.complete_graph(num_agents)

    if network_type == "grid":
        # Lay agents out on the most square grid that fits the population.
        side = int(round(math.sqrt(num_agents)))
        rows = side
        cols = math.ceil(num_agents / side)
        full = nx.grid_2d_graph(rows, cols)
        # Trim spare cells and relabel (row, col) -> a single integer id.
        nodes = list(full.nodes())[:num_agents]
        sub = full.subgraph(nodes).copy()
        mapping = {node: i for i, node in enumerate(nodes)}
        return nx.relabel_nodes(sub, mapping)

    if network_type == "small_world":
        # Watts-Strogatz: mostly local links plus a few long-range bridges.
        k = min(4, num_agents - 1)
        if k % 2 == 1:  # the generator needs an even neighbour count
            k -= 1
        k = max(k, 2)
        return nx.watts_strogatz_graph(num_agents, k, 0.1, seed=random.randint(0, 10_000))

    raise ValueError(f"Unknown network type: {network_type}")


def grid_positions(num_agents: int) -> list[tuple[int, int]]:
    """(row, col) coordinates for the grid layout, handy for plotting."""
    side = int(round(math.sqrt(num_agents)))
    cols = math.ceil(num_agents / side)
    return [(i // cols, i % cols) for i in range(num_agents)]
