"""Boundary and independent-oracle checks on the actual submission modules."""

import importlib.util
import itertools
import random
from heapq import heappop
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load_patch(bug):
    spec = importlib.util.spec_from_file_location(
        bug, ROOT / "results" / "final_patches" / f"{bug}.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


PATCHES = {f"BUG{i:03d}": load_patch(f"BUG{i:03d}") for i in range(10)}


class Node:
    """Identity-based, intentionally non-orderable graph/list node."""

    def __init__(self):
        self.successors = []
        self.successor = None


def reference_distances(nodes, edges, source):
    """Synchronous relaxation oracle, separate from the submitted algorithms."""
    distances = {node: float("inf") for node in nodes}
    distances[source] = 0
    for _ in range(len(nodes) - 1):
        previous = distances.copy()
        for (u, v), weight in edges.items():
            distances[v] = min(distances[v], previous[u] + weight)
    return distances


@pytest.mark.parametrize("threshold", [-1, 0, 0.5, 2, 3, 7])
def test_close_elements_exhaustive(threshold):
    function = PATCHES["BUG000"].has_close_elements
    for size in range(5):
        for values in itertools.product((-2, 0, 3), repeat=size):
            numbers = list(values)
            expected = any(abs(a - b) < threshold for a, b in itertools.combinations(values, 2))
            assert function(numbers, threshold) is expected
            assert numbers == list(values)


def test_dijkstra_equal_priorities_and_decreases():
    s, a, b, c, t, isolated = [Node() for _ in range(6)]
    edges = {(s, a): 9, (s, b): 1, (s, c): 1, (b, a): 1, (a, t): 2, (c, t): 10}
    for u, v in edges:
        u.successors.append(v)
    function = PATCHES["BUG001"].shortest_path_length
    assert function(edges, s, t) == 4
    assert function(edges, s, isolated) == float("inf")
    assert function(edges, isolated, isolated) == 0


def test_dijkstra_random_graphs_against_relaxation():
    rng = random.Random(2701)
    function = PATCHES["BUG001"].shortest_path_length
    for _ in range(35):
        nodes = [Node() for _ in range(6)]
        edges = {(u, v): rng.randint(1, 12) for u in nodes for v in nodes if rng.random() < 0.25}
        for u, v in edges:
            u.successors.append(v)
        original_edges = edges.copy()
        original_links = [node.successors.copy() for node in nodes]
        for source in nodes:
            expected = reference_distances(nodes, edges, source)
            for goal in nodes:
                assert function(edges, source, goal) == expected[goal]
        assert edges == original_edges
        assert [node.successors for node in nodes] == original_links


def test_dijkstra_helpers_restore_heap_and_handle_ties():
    module = PATCHES["BUG001"]
    a, b, c = Node(), Node(), Node()
    heap = []
    for entry in ((5, a), (2, b), (2, c)):
        module.insert_or_update(heap, entry)
    module.insert_or_update(heap, (1, a))
    assert module.get(heap, a) == 1
    assert module.get(heap, Node()) == 0
    assert [heappop(heap)[0] for _ in range(3)] == [1, 2, 2]
    heap = []
    for entry in ((1, a), (2, b), (3, c)):
        module.insert_or_update(heap, entry)
    module.insert_or_update(heap, (8, a))
    assert [heappop(heap)[0] for _ in range(3)] == [2, 3, 8]


def test_bellman_ford_endpoint_initialization_and_input_preservation():
    function = PATCHES["BUG002"].shortest_paths
    edges = {("B", "C"): -2, ("A", "B"): 4, ("X", "Y"): -7}
    before = edges.copy()
    assert function("A", edges) == {"A": 0, "B": 4, "C": 2, "X": float("inf"), "Y": float("inf")}
    assert edges == before
    assert function("S", {}) == {"S": 0}
    assert function("S", {("S", "S"): 5}) == {"S": 0}


def test_bellman_ford_negative_dags_against_relaxation():
    rng = random.Random(2702)
    function = PATCHES["BUG002"].shortest_paths
    for _ in range(50):
        pairs = [(i, j) for i in range(6) for j in range(i + 1, 6)]
        rng.shuffle(pairs)
        edges = {pair: rng.randint(-8, 9) for pair in pairs if rng.random() < 0.4}
        for source in range(6):
            nodes = {source} | {node for edge in edges for node in edge}
            assert function(source, edges) == reference_distances(nodes, edges, source)


def is_spanning_tree(nodes, edges):
    if len(edges) != len(nodes) - 1:
        return False
    seen = {next(iter(nodes))}
    while True:
        expanded = seen | {v for u, v in edges if u in seen} | {u for u, v in edges if v in seen}
        if expanded == seen:
            return seen == nodes
        seen = expanded


def test_mst_against_exhaustive_spanning_trees():
    rng = random.Random(2703)
    function = PATCHES["BUG003"].minimum_spanning_tree
    assert function({}) == set()
    assert function({(0, 0): -4}) == set()
    for _ in range(30):
        nodes = set(range(5))
        edges = {(i, i + 1): rng.randint(-4, 8) for i in range(4)}
        edges.update({(i, j): rng.randint(-4, 8) for i in nodes for j in nodes if j > i + 1 and rng.random() < 0.6})
        edges[(0, 0)] = -10
        before = edges.copy()
        result = function(edges)
        assert is_spanning_tree(nodes, result)
        optimal = min(
            sum(edges[edge] for edge in candidate)
            for candidate in itertools.combinations(edges, len(nodes) - 1)
            if is_spanning_tree(nodes, candidate)
        )
        assert sum(edges[edge] for edge in result) == optimal
        assert edges == before


def test_floyd_warshall_empty_self_loops_and_direction():
    function = PATCHES["BUG004"].shortest_path_lengths
    assert function(0, {}) == {}
    assert function(1, {(0, 0): 5}) == {(0, 0): 0}
    assert function(1, {(0, 0): 0}) == {(0, 0): 0}
    result = function(3, {(0, 1): 2, (1, 2): -3})
    assert result[0, 2] == -1
    assert result[2, 0] == float("inf")
    assert len(result) == 9


def test_floyd_warshall_random_negative_dags():
    rng = random.Random(2704)
    function = PATCHES["BUG004"].shortest_path_lengths
    for _ in range(40):
        edges = {(i, j): rng.randint(-8, 9) for i in range(6) for j in range(i + 1, 6) if rng.random() < 0.5}
        before = edges.copy()
        result = function(6, edges)
        for source in range(6):
            expected = reference_distances(range(6), edges, source)
            assert {v: result[source, v] for v in range(6)} == expected
        assert edges == before


@pytest.mark.parametrize("bug,name", [("BUG005", "breadth_first_search"), ("BUG006", "depth_first_search")])
def test_search_every_three_node_directed_graph(bug, name):
    function = getattr(PATCHES[bug], name)
    pairs = list(itertools.product(range(3), repeat=2))
    for bits in range(1 << len(pairs)):
        nodes = [Node() for _ in range(3)]
        edges = {}
        for bit, (i, j) in enumerate(pairs):
            if bits & (1 << bit):
                nodes[i].successors.append(nodes[j])
                edges[i, j] = 1
        before = [node.successors.copy() for node in nodes]
        for source in range(3):
            distances = reference_distances(range(3), edges, source)
            for goal in range(3):
                assert function(nodes[source], nodes[goal]) is (distances[goal] < float("inf"))
        assert [node.successors for node in nodes] == before


@pytest.mark.parametrize("bug,name", [("BUG005", "breadth_first_search"), ("BUG006", "depth_first_search")])
def test_search_long_path_and_unreachable_cycle(bug, name):
    function = getattr(PATCHES[bug], name)
    nodes = [Node() for _ in range(2500)]
    for u, v in zip(nodes, nodes[1:]):
        u.successors = [v]
    assert function(nodes[0], nodes[-1]) is True
    nodes[-1].successors = [nodes[0]]
    assert function(nodes[0], Node()) is False


@pytest.mark.parametrize("size", [0, 1, 2, 5, 1000])
def test_reverse_preserves_identity_and_round_trip(size):
    function = PATCHES["BUG007"].reverse_linked_list
    nodes = [Node() for _ in range(size)]
    for u, v in zip(nodes, nodes[1:]):
        u.successor = v
    head = function(nodes[0] if nodes else None)
    cursor = head
    for expected in reversed(nodes):
        assert cursor is expected
        cursor = cursor.successor
    assert cursor is None
    restored = function(head)
    assert restored is (nodes[0] if nodes else None)
    assert [node.successor for node in nodes] == nodes[1:] + ([None] if nodes else [])


CYCLE_CASES = [(size, entry) for size in range(11) for entry in [None, *range(size)]]


@pytest.mark.parametrize("size,entry", CYCLE_CASES)
def test_cycle_detection_all_small_entry_positions(size, entry):
    nodes = [Node() for _ in range(size)]
    for u, v in zip(nodes, nodes[1:]):
        u.successor = v
    if entry is not None:
        nodes[-1].successor = nodes[entry]
    before = [node.successor for node in nodes]
    assert PATCHES["BUG008"].detect_cycle(nodes[0] if nodes else None) is (entry is not None)
    assert [node.successor for node in nodes] == before


def reference_parentheses(s):
    best = 0
    for start in range(len(s)):
        balance = 0
        for end in range(start, len(s)):
            balance += 1 if s[end] == "(" else -1
            if balance < 0:
                break
            if balance == 0:
                best = max(best, end - start + 1)
    return best


@pytest.mark.parametrize("size", range(11))
def test_parentheses_exhaustive(size):
    function = PATCHES["BUG009"].longestValidParentheses
    for characters in itertools.product("()", repeat=size):
        s = "".join(characters)
        assert function(s) == reference_parentheses(s), s


def test_parentheses_long_input():
    function = PATCHES["BUG009"].longestValidParentheses
    assert function("(" * 10000 + ")" * 10000) == 20000
    assert function(")" * 10000) == 0
