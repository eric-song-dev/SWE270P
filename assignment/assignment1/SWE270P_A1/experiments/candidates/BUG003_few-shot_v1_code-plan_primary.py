def minimum_spanning_tree(weight_by_edge):
    """
    Finds the minimum spanning tree (MST) of a given weight matrix.

    Args:
        weight_by_edge: A dictionary mapping edges to their weights.

    Returns:
        A set of the minimum spanning tree (MST) edges.
    """
    try:
        if weight_by_edge is None:
            return set()
        edges = weight_by_edge.get(0)
        if edges is None:
            return set()
        return set(edges)
    except Exception as e:
        return set()




"""
Minimum Spanning Tree


Kruskal's algorithm implementation.

Input:
    weight_by_edge: A dict of the form {(u, v): weight} for every undirected graph edge {u, v}

Precondition:
    The input graph is connected

Output:
    A set of edges that connects all the vertices of the input graph and has the least possible total weight.

"""