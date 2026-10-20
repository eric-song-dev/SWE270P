"""Independent boundary/oracle checks; PATCH_DIR can select a generated candidate."""

import importlib.util
import itertools
import os
import random
from functools import lru_cache
from pathlib import Path

import pytest

PATCH_DIR = Path(os.environ.get("PATCH_DIR", Path(__file__).resolve().parents[1] / "results/final_patches"))


@lru_cache(None)
def patch(bug):
    spec = importlib.util.spec_from_file_location(f"candidate_{bug}", PATCH_DIR / f"{bug}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Node:
    def __init__(self):
        self.successors = []
        self.successor = None


def paths(nodes, edges, source):
    """Independent simple-path enumeration, valid without negative cycles."""
    best = {n: float("inf") for n in nodes}
    adjacency = {n: [] for n in nodes}
    for (u, v), w in edges.items():
        adjacency[u].append((v, w))

    def walk(node, length, seen):
        best[node] = min(best[node], length)
        for v, w in adjacency[node]:
            if v not in seen:
                walk(v, length + w, seen | {v})

    walk(source, 0, {source})
    return best


@pytest.mark.parametrize("threshold", [-1, 0, 0.5, 2, 3, 7])
def test_BUG000_exhaustive(threshold):
    f = patch("BUG000").has_close_elements
    for size in range(5):
        for values in itertools.product((-2, 0, 3), repeat=size):
            numbers = list(values)
            expected = any(abs(a-b) < threshold for a, b in itertools.combinations(values, 2))
            assert f(numbers, threshold) is expected
            assert numbers == list(values)


def test_BUG001_ties_decreases_unreachable():
    s, a, b, c, t, isolated = [Node() for _ in range(6)]
    edges = {(s,a):9, (s,b):1, (s,c):1, (b,a):1, (a,t):2, (c,t):10}
    for u,v in edges:
        u.successors.append(v)
    f = patch("BUG001").shortest_path_length
    assert f(edges,s,t) == 4
    assert f(edges,s,isolated) == float("inf")
    assert f(edges,isolated,isolated) == 0


def test_BUG000_fractional_strict_boundary():
    f = patch("BUG000").has_close_elements
    assert f([2.0,2.25],0.25) is False
    assert f([2.0,2.25],0.5) is True
    assert f([2.0,2.0],0.0) is False
    assert f([2.0,2.0],0.125) is True


def test_BUG001_random_graphs():
    rng = random.Random(2701)
    f = patch("BUG001").shortest_path_length
    for _ in range(20):
        nodes = [Node() for _ in range(5)]
        edges = {(u,v):rng.randint(1,12) for u in nodes for v in nodes if rng.random()<0.3}
        for u,v in edges:
            u.successors.append(v)
        before = edges.copy(), [n.successors.copy() for n in nodes]
        for source in nodes:
            expected = paths(nodes,edges,source)
            for goal in nodes:
                assert f(edges,source,goal) == expected[goal]
        assert edges == before[0]
        assert [n.successors for n in nodes] == before[1]


def test_BUG001_fractional():
    a,b,c,d = [Node() for _ in range(4)]
    edges = {(a,b):0.5,(a,c):0.5,(b,c):0.25,(c,b):0.25,(b,d):2.0,(c,d):0.5}
    for u,v in edges:
        u.successors.append(v)
    assert patch("BUG001").shortest_path_length(edges,a,d) == 1.0


def test_BUG002_endpoints_and_empty():
    f = patch("BUG002").shortest_paths
    edges = {("B","C"):-2,("A","B"):4,("X","Y"):-7}
    before = edges.copy()
    assert f("A",edges) == {"A":0,"B":4,"C":2,"X":float("inf"),"Y":float("inf")}
    assert edges == before
    assert f("S",{}) == {"S":0}
    assert f("S",{("S","S"):5}) == {"S":0}
    assert f(None,{}) == {None:0}
    assert f(None,{(None,("B",1)):-2,(("B",1),42):5,("X","Y"):0}) == {None:0,("B",1):-2,42:3,"X":float("inf"),"Y":float("inf")}


def test_BUG002_negative_dags():
    rng = random.Random(2702)
    for _ in range(25):
        pairs = [(i,j) for i in range(5) for j in range(i+1,5)]
        rng.shuffle(pairs)
        edges = {p:rng.randint(-8,9) for p in pairs if rng.random()<0.5}
        for source in range(5):
            nodes = {source} | {v for edge in edges for v in edge}
            assert patch("BUG002").shortest_paths(source,edges) == paths(nodes,edges,source)


def cyclic_graphs(seed):
    rng = random.Random(seed)
    for _ in range(20):
        p = [-8,-3,0,4,7]
        rng.shuffle(p)
        costs = {(i,(i+1)%5):rng.randint(0,6) for i in range(5)}
        costs.update({(i,j):rng.randint(0,6) for i in range(5) for j in range(5) if rng.random()<0.25})
        pairs = list(costs)
        rng.shuffle(pairs)
        # Every cycle has nonnegative total weight: potential terms cancel.
        yield {(u,v):costs[u,v]+p[v]-p[u] for u,v in pairs}


@pytest.mark.parametrize("seed", [2710,2711])
def test_BUG002_legal_negative_cycles(seed):
    for edges in cyclic_graphs(seed):
        before = edges.copy()
        for source in range(6):
            nodes = {source} | {v for e in edges for v in e}
            assert patch("BUG002").shortest_paths(source,edges) == paths(nodes,edges,source)
        assert edges == before


def spanning(nodes, edges):
    if len(edges) != len(nodes)-1:
        return False
    seen = {next(iter(nodes))}
    while True:
        expanded = seen | {v for u,v in edges if u in seen} | {u for u,v in edges if v in seen}
        if expanded == seen:
            return seen == nodes
        seen = expanded


def test_BUG003_exhaustive_mst_oracle():
    rng = random.Random(2703)
    f = patch("BUG003").minimum_spanning_tree
    for _ in range(20):
        nodes = set(range(5))
        edges = {(i,i+1):rng.randint(-4,8) for i in range(4)}
        edges.update({(i,j):rng.randint(-4,8) for i in nodes for j in nodes if j>i+1 and rng.random()<0.6})
        edges[0,0] = -10
        before = edges.copy()
        result = f(edges)
        assert isinstance(result,set)
        assert spanning(nodes,result)
        optimal = min(sum(edges[e] for e in candidate) for candidate in itertools.combinations(edges,4) if spanning(nodes,candidate))
        assert sum(edges[e] for e in result) == optimal
        assert edges == before


def test_BUG003_ties():
    a,b,c = "A",2,(3,)
    assert patch("BUG003").minimum_spanning_tree({(a,b):1,(b,c):1,(a,c):1,(c,b):1}) == {(a,b),(b,c)}
    assert patch("BUG003").minimum_spanning_tree({(None,"A"):1,("A",2):1,(None,2):2}) == {(None,"A"),("A",2)}


def test_BUG003_empty_self_loop():
    f = patch("BUG003").minimum_spanning_tree
    assert f({}) == set()
    assert f({(0,0):-4}) == set()


def test_BUG004_diagonal_and_direction():
    f = patch("BUG004").shortest_path_lengths
    assert f(0,{}) == {}
    assert f(1,{(0,0):5}) == {(0,0):0}
    assert f(1,{(0,0):0}) == {(0,0):0}
    d = f(3,{(0,1):2,(1,2):-3})
    assert len(d) == 9 and d[0,2] == -1 and d[2,0] == float("inf")


def test_BUG004_negative_dags():
    rng = random.Random(2704)
    for _ in range(25):
        edges = {(i,j):rng.randint(-8,9) for i in range(5) for j in range(i+1,5) if rng.random()<0.5}
        before = edges.copy()
        result = patch("BUG004").shortest_path_lengths(5,edges)
        for source in range(5):
            assert {v:result[source,v] for v in range(5)} == paths(range(5),edges,source)
        assert edges == before


@pytest.mark.parametrize("seed", [2720,2721])
def test_BUG004_legal_negative_cycles(seed):
    for edges in cyclic_graphs(seed):
        before = edges.copy()
        result = patch("BUG004").shortest_path_lengths(6,edges)
        assert len(result) == 36
        for source in range(6):
            assert {v:result[source,v] for v in range(6)} == paths(range(6),edges,source)
        assert edges == before


@pytest.mark.parametrize("bug,name", [("BUG005","breadth_first_search"),("BUG006","depth_first_search")])
def test_search_exhaustive(bug,name):
    f = getattr(patch(bug),name)
    pairs = list(itertools.product(range(3),repeat=2))
    for bits in range(512):
        nodes = [Node() for _ in range(3)]
        edges = {}
        for bit,(i,j) in enumerate(pairs):
            if bits & (1<<bit):
                nodes[i].successors.append(nodes[j])
                edges[i,j] = 1
        before = [n.successors.copy() for n in nodes]
        for source in range(3):
            distances = paths(range(3),edges,source)
            for goal in range(3):
                assert f(nodes[source],nodes[goal]) is (distances[goal]<float("inf"))
        assert [n.successors for n in nodes] == before


@pytest.mark.parametrize("bug,name", [("BUG005","breadth_first_search"),("BUG006","depth_first_search")])
def test_search_long_path(bug,name):
    nodes = [Node() for _ in range(2500)]
    for a,b in zip(nodes,nodes[1:]):
        a.successors = [b]
    f = getattr(patch(bug),name)
    assert f(nodes[0],nodes[-1]) is True
    nodes[-1].successors = [nodes[0]]
    assert f(nodes[0],Node()) is False


@pytest.mark.parametrize("size", [0,1,2,5,1000])
def test_BUG007_reverse_identity_and_roundtrip(size):
    nodes = [Node() for _ in range(size)]
    for a,b in zip(nodes,nodes[1:]):
        a.successor = b
    f = patch("BUG007").reverse_linked_list
    head = f(nodes[0] if nodes else None)
    cursor = head
    for expected in reversed(nodes):
        assert cursor is expected
        cursor = cursor.successor
    assert cursor is None
    assert f(head) is (nodes[0] if nodes else None)
    assert [n.successor for n in nodes] == nodes[1:]+([None] if nodes else [])


@pytest.mark.parametrize("size,entry", [(size,entry) for size in range(11) for entry in [None,*range(size)]])
def test_BUG008_cycles(size,entry):
    nodes = [Node() for _ in range(size)]
    for a,b in zip(nodes,nodes[1:]):
        a.successor = b
    if entry is not None:
        nodes[-1].successor = nodes[entry]
    before = [n.successor for n in nodes]
    assert patch("BUG008").detect_cycle(nodes[0] if nodes else None) is (entry is not None)
    assert [n.successor for n in nodes] == before


def parentheses_oracle(s):
    best = 0
    for start in range(len(s)):
        balance = 0
        for end in range(start,len(s)):
            balance += 1 if s[end]=='(' else -1
            if balance<0:
                break
            if balance==0:
                best = max(best,end-start+1)
    return best


@pytest.mark.parametrize("size", range(11))
def test_BUG009_exhaustive(size):
    f = patch("BUG009").longestValidParentheses
    for chars in itertools.product('()',repeat=size):
        s = ''.join(chars)
        assert f(s) == parentheses_oracle(s),s


def test_BUG009_long():
    f = patch("BUG009").longestValidParentheses
    assert f('('*10000+')'*10000) == 20000
    assert f(')'*10000) == 0


def test_BUG009_mixed_fragments():
    f = patch("BUG009").longestValidParentheses
    for s in ('(()'*12+'())',')'*20+'()()((()))'+'('*20,'((())())())(()(()))'):
        assert f(s) == parentheses_oracle(s)
