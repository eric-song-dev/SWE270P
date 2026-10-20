from collections import defaultdict

def shortest_path_lengths(n, length_by_edge):
    """
    Calculates the shortest path lengths for a given set of edges.

    Args:
        n: The number of nodes in the graph.
        length_by_edge: A list of tuples, where each tuple represents an edge
                            from node i to node j. The list is assumed to be
                            in the same order as the edges in the `length_by_edge`
                            list.

    Returns:
        A dictionary representing the shortest path lengths.
        Keys are node indices, and values are the corresponding path lengths.
        Returns an empty dictionary if the input `length_by_edge` is empty.
    """
    distances = {}
    for i in range(n):
        if i in distances:
            distances[i] = 0
        else:
            distances[i] = float('inf')
    for edge in length_by_edge:
        if edge in distances:
            distances[edge] = min(distances[edge], distances[edge] + weight)
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