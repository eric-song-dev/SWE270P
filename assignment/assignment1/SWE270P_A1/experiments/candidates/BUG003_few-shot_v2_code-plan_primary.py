def minimum_spanning_tree(weight_by_edge):
    """
    Calculates the minimum spanning tree of a given weight matrix.
    """
    if weight_by_edge is None:
        return []
    try:
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
    except Exception as e:
        print(f"Error: {e}")
        return []




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