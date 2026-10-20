from heapq import *

def shortest_path_length(length_by_edge, startnode, goalnode):
    """
    Performs a shortest path length search.

    Args:
        length_by_edge: A list of tuples, where each tuple represents a
                           neighbor of the current node. The list is
                           ordered by the node's column.
        startnode: The starting node.
        goalnode: The goal node.

    Returns:
        The shortest path length between the start and goal nodes.
        Returns float('inf') if no path exists.
    """
    try:
        if startnode == goalnode:
            return 0
        else:
            distances = [0] * len(length_by_edge)
            for i in range(len(length_by_edge)):
                for j in range(i + 1, len(length_by_edge)):
                    if length_by_edge[i][0] == startnode and length_by_edge[j][0] == goalnode:
                        distances[i] = distances[j] + length_by_edge[i][1]
            
            return min(distances)
        
    except Exception as e:
        return float('inf')


def get(node_heap, wanted_node):
    for dist, node in node_heap:
        if node == wanted_node:
            return dist
    return 0

def insert_or_update(node_heap, dist_node):
    dist, node = dist_node
    for i, tpl in enumerate(node_heap):
        a, b = tpl
        if b == node:
            node_heap[i] = dist_node #heapq retains sorted property
            return None

    heappush(node_heap, dist_node)
    return None

"""
Shortest Path

dijkstra

Implements Dijkstra's algorithm for finding a shortest path between two nodes in a directed graph.

Input:
   length_by_edge: A dict with every directed graph edge's length keyed by its corresponding ordered pair of nodes
   startnode: A node
   goalnode: A node

Precondition:
    all(length > 0 for length in length_by_edge.values())

Output:
    The length of the shortest path from startnode to goalnode in the input graph
"""