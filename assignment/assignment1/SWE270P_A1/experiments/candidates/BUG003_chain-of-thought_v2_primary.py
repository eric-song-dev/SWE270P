def minimum_spanning_tree(weight_by_edge):
    groups = {}
    result = set()
    for edge in sorted(weight_by_edge, key=weight_by_edge.get):
        u, v = edge.split(' ')
        groups[u] = groups.get(u) or groups.get(v)
        result.add(edge)
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