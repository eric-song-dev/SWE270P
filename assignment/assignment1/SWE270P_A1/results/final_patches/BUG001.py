from heapq import *
from itertools import count


def shortest_path_length(length_by_edge, startnode, goalnode):
    """Return a Dijkstra distance for positive edge weights, or infinity."""
    sequence = count()
    unvisited_nodes = [(0, next(sequence), startnode)]
    distance_by_node = {startnode: 0}
    visited_nodes = set()

    while unvisited_nodes:
        distance, _, node = heappop(unvisited_nodes)
        if node in visited_nodes:
            continue
        if node is goalnode:
            return distance
        visited_nodes.add(node)

        for nextnode in node.successors:
            if nextnode in visited_nodes:
                continue
            candidate = distance + length_by_edge[node, nextnode]
            if candidate < distance_by_node.get(nextnode, float("inf")):
                distance_by_node[nextnode] = candidate
                # Unique sequence numbers prevent comparisons between Node objects.
                heappush(unvisited_nodes, (candidate, next(sequence), nextnode))
    return float("inf")


def get(node_heap, wanted_node):
    """Look up a distance in the original (distance, node) helper interface."""
    for dist, node in node_heap:
        if node == wanted_node:
            return dist
    return 0


class _DistanceEntry(tuple):
    """A pair ordered only by distance, including when node objects tie."""

    def __new__(cls, distance, node):
        return super().__new__(cls, (distance, node))

    def __lt__(self, other):
        return self[0] < other[0]


def insert_or_update(node_heap, dist_node):
    """Insert/update a pair and restore the heap after a priority change."""
    dist, node = dist_node
    # Keep the original pair representation while making equal priorities safe.
    node_heap[:] = [_DistanceEntry(d, n) for d, n in node_heap]
    for i, (_, existing_node) in enumerate(node_heap):
        if existing_node == node:
            node_heap[i] = _DistanceEntry(dist, node)
            heapify(node_heap)
            return None
    heappush(node_heap, _DistanceEntry(dist, node))
    return None
