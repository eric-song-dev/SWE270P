from collections import defaultdict

def shortest_path_lengths(n, length_by_edge):
    distances = {(i, j): (0 if i == j else float('inf')) for i in range(n) for j in range(n)}
    for edge, weight in length_by_edge.items():
        distances[edge] = min(distances[edge], weight)
    return distances


"""
All Shortest Paths
floyd-warshall

Floyd-Warshall algorithm implementation.

Calculates the length of the shortest path connecting every ordered pair of nodes in a directed graph.



Input:
    n: The number of nodes in the graph. The nodes are assumed to have ids 0..n-1
    length_by_edge: A dict containing edge length keyed by an ordered pair of node ids

Precondition:
    There are no negative-length cycles in the input graph

Output:
    A dict containing shortest path length keyed by an ordered pair of node ids
"""