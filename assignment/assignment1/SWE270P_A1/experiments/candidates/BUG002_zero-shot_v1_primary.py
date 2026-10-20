
def shortest_paths(source, weight_by_edge):
    """
    Calculates the shortest paths from source to destination in a graph
    represented by a weighted edge graph.

    Args:
        source: The source node.
        weight_by_edge: A dictionary mapping each edge to its weight.

    Returns:
        A dictionary mapping the destination node to the shortest path
        distance from the source to that destination.
    """
    distances = {u: float('inf') for u in source}
    distances[source] = 0
    paths = {}

    for u, v in weight_by_edge.items():
        if distances[u] == float('inf'):
            continue
        distances[v] = distances[u] + weight_by_edge[u]
        paths[v] = distances[v]

    return distances


"""
Minimum-Weight Paths
bellman-ford

Bellman-Ford algorithm implementation

Given a directed graph that may contain negative edges (as long as there are no negative-weight cycles), efficiently calculates the minimum path weights from a source node to every other node in the graph.

Input:
    source: A node id
    weight_by_edge: A dict containing edge weights keyed by an ordered pair of node ids

Precondition:
    The input graph contains no negative-weight cycles

Output:
   A dict mapping each node id to the minimum weight of a path from the source node to that node

"""