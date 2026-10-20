from heapq import deque
from typing import Tuple, List

def shortest_path_length(length_by_edge, startnode, goalnode):
    unvisited_nodes = []
    heappush(unvisited_nodes, (0, startnode))
    visited_nodes = set()

    while len(unvisited_nodes) > 0:
        distance, node = heappop(unvisited_nodes)
        if node is goalnode:
            return distance

        visited_nodes.add(node)

        for next_node in node.successors:
            if next_node in visited_nodes:
                continue

            insert_or_update(unvisited_nodes,
                (min(
                    get(unvisited_nodes, next_node) or float('inf'),
                    get(unvisited_nodes, next_node) + length_by_edge[node, next_node]
                ),
                next_node)
            )

    return float('inf')
