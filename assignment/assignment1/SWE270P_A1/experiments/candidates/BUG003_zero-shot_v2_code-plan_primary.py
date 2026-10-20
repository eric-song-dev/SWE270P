def minimum_spanning_tree(weight_by_edge):
    """
    Implements the minimum spanning tree (MST) algorithm.

    Args:
        weight_by_edge: A dictionary where keys are nodes and values are
                           the weights of the edges connected to those nodes.

    Returns:
        A set containing only the nodes that are connected to the minimum
        spanning tree.
    """
    groups = {}
    result = set()
    for edge in sorted(weight_by_edge, key=weight_by_edge.get):
        u, v = edge
        a = groups.setdefault(u, {}).get(u)
        b = groups.setdefault(v, {}).get(v)
        if a != b:
            result.add(edge)
            merged = a | b
            for member in merged:
                groups[member] = merged
    return result




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