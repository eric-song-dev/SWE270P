def minimum_spanning_tree(weight_by_edge):
    """
    Calculates the minimum spanning tree (MST) of a given weight_by_edge
    given a set of edges.

    Args:
        weight_by_edge: A dictionary where keys are tuples of (u, v)
                         representing the edges, and values are the
                         corresponding weights.

    Returns:
        A set of tuples representing the MST edges, where each tuple
        contains the u and v of the edge.
    """
    groups = {}
    result = set()
    for edge in sorted(weight_by_edge, key=weight_by_edge.get):
     u, v = edge
     a = groups.setdefault(u, {})
     b = groups.setdefault(v, {})
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