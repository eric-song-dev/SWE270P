
def shortest_paths(source, weight_by_edge):
    distances = {u: float('inf') for u in weight_by_edge}
    for u in weight_by_edge:
        for v in weight_by_edge:
            if u == v:
                distances[u] = 0
            else:
                distances[v] = min(distances[v], distances[u] + weight_by_edge[u])
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