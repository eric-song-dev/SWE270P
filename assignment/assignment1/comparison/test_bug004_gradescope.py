"""Regression checks for the positive-self-loop contract revealed by Gradescope."""

import os
import random
from pathlib import Path
from zipfile import ZipFile

import pytest


@pytest.fixture(scope="module")
def shortest_paths():
    candidate = os.environ.get("BUG004_CANDIDATE")
    if candidate:
        code = Path(candidate).read_text()
    else:
        archive = Path(__file__).parent / "submissions/feat-codex-generated-2/SWE270P_A1.zip"
        with ZipFile(archive) as submission:
            code = submission.read("results/final_patches/BUG004.py").decode()
    namespace = {}
    exec(compile(code, "submitted-BUG004.py", "exec"), namespace)
    return namespace["shortest_path_lengths"]


def test_reported_case8(shortest_paths):
    graph = {(0, 0): 5, (0, 1): 2, (1, 2): 2}
    original = graph.copy()
    expected = {
        (0, 0): 5, (0, 1): 2, (0, 2): 4,
        (1, 0): float("inf"), (1, 1): 0, (1, 2): 2,
        (2, 0): float("inf"), (2, 1): float("inf"), (2, 2): 0,
    }
    assert shortest_paths(3, graph) == expected
    assert graph == original


def test_defaults_without_explicit_self_loops(shortest_paths):
    assert shortest_paths(0, {}) == {}
    assert shortest_paths(1, {}) == {(0, 0): 0}
    assert shortest_paths(2, {}) == {
        (0, 0): 0, (0, 1): float("inf"),
        (1, 0): float("inf"), (1, 1): 0,
    }


@pytest.mark.parametrize("n,vertex", [(1, 0), (3, 0), (3, 1), (3, 2)])
@pytest.mark.parametrize("weight", [0.25, 5, 11])
def test_explicit_self_loop_at_any_vertex(shortest_paths, n, vertex, weight):
    result = shortest_paths(n, {(vertex, vertex): weight})
    assert len(result) == n * n
    for i in range(n):
        for j in range(n):
            if i == j == vertex:
                assert result[i, j] == weight
            elif i == j:
                assert result[i, j] == 0
            else:
                assert result[i, j] == float("inf")


def test_cheaper_return_cycle_can_improve_explicit_self_loop(shortest_paths):
    graph = {(0, 0): 9, (0, 1): 2, (1, 0): 3}
    assert shortest_paths(2, graph) == {
        (0, 0): 5, (0, 1): 2, (1, 0): 3, (1, 1): 0,
    }


def simple_path_oracle(n, edges, source):
    """Enumerate simple paths/cycles, with an empty path only by default."""
    distances = {node: float("inf") for node in range(n)}
    distances[source] = edges.get((source, source), 0)

    def visit(node, visited, cost):
        for (u, v), weight in edges.items():
            if u != node:
                continue
            candidate = cost + weight
            if v == source:
                distances[source] = min(distances[source], candidate)
            elif v not in visited:
                distances[v] = min(distances[v], candidate)
                visit(v, visited | {v}, candidate)

    visit(source, {source}, 0)
    return distances


@pytest.mark.parametrize("seed", [5704, 5705, 5706])
def test_negative_edges_without_negative_cycles(shortest_paths, seed):
    rng = random.Random(seed)
    for _ in range(20):
        n = 5
        potentials = [rng.randint(-5, 5) for _ in range(n)]
        # Potential differences cancel around every cycle, leaving a
        # nonnegative sum of base weights. Negative edges remain possible.
        graph = {
            (u, v): rng.randint(0, 7) + potentials[v] - potentials[u]
            for u in range(n) for v in range(n) if rng.random() < 0.4
        }
        original = graph.copy()
        result = shortest_paths(n, graph)
        assert len(result) == n * n
        for source in range(n):
            expected = simple_path_oracle(n, graph, source)
            assert {v: result[source, v] for v in range(n)} == expected
        assert graph == original
