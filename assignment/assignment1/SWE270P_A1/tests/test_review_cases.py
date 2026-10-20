"""Review additions: legal negative-edge cycles and independent path enumeration."""

import random

import pytest

from test_robustness import PATCHES, Node


def simple_path_distances(nodes, edges, source):
    """Enumerate simple paths; with no negative cycles an optimum is simple."""
    best = {node: float("inf") for node in nodes}
    adjacency = {node: [] for node in nodes}
    for (u, v), weight in edges.items():
        adjacency[u].append((v, weight))

    def walk(node, length, visited):
        best[node] = min(best[node], length)
        for successor, weight in adjacency[node]:
            if successor not in visited:
                walk(successor, length + weight, visited | {successor})

    walk(source, 0, {source})
    return best


def legal_cyclic_graphs(seed):
    """Potential differences cancel on cycles, leaving nonnegative cycle costs."""
    rng = random.Random(seed)
    for _ in range(35):
        potentials = [-8, -3, 0, 4, 7]
        rng.shuffle(potentials)
        costs = {(i, (i + 1) % 5): rng.randint(0, 6) for i in range(5)}
        costs.update({(i, j): rng.randint(0, 6) for i in range(5) for j in range(5) if rng.random() < 0.3})
        pairs = list(costs)
        rng.shuffle(pairs)
        yield {(u, v): costs[u, v] + potentials[v] - potentials[u] for u, v in pairs}


@pytest.mark.parametrize("seed", [2710, 2711, 2712])
def test_bellman_ford_negative_edges_in_cyclic_graphs(seed):
    function = PATCHES["BUG002"].shortest_paths
    for edges in legal_cyclic_graphs(seed):
        original = edges.copy()
        for source in range(6):
            nodes = {source} | {node for edge in edges for node in edge}
            expected = simple_path_distances(nodes, edges, source)
            assert function(source, edges) == expected
        assert edges == original


@pytest.mark.parametrize("seed", [2720, 2721, 2722])
def test_floyd_warshall_negative_edges_in_cyclic_graphs(seed):
    function = PATCHES["BUG004"].shortest_path_lengths
    for edges in legal_cyclic_graphs(seed):
        original = edges.copy()
        result = function(6, edges)
        assert len(result) == 36
        for source in range(6):
            expected = simple_path_distances(range(6), edges, source)
            assert {goal: result[source, goal] for goal in range(6)} == expected
        assert edges == original


def test_dijkstra_fractional_lengths_and_directed_cycle():
    a, b, c, d = [Node() for _ in range(4)]
    edges = {(a, b): 0.5, (a, c): 0.5, (b, c): 0.25, (c, b): 0.25, (b, d): 2.0, (c, d): 0.5}
    for u, v in edges:
        u.successors.append(v)
    function = PATCHES["BUG001"].shortest_path_length
    assert function(edges, a, d) == 1.0
    assert function(edges, c, d) == 0.5
    assert function(edges, d, a) == float("inf")


def test_mst_tied_weights_and_unorderable_vertex_labels():
    a, b, c = "A", 2, (3,)
    edges = {(a, b): 1, (b, c): 1, (a, c): 1, (c, b): 1}
    assert PATCHES["BUG003"].minimum_spanning_tree(edges) == {(a, b), (b, c)}
