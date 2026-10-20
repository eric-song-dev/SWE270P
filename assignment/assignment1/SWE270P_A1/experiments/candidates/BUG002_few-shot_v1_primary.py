
def shortest_paths(source, weight_by_edge):
    try:
        distances = {source: 0}.copy()
        for u,v in weight_by_edge.items():
            distances[v] = min(distances[v], distances[u] + weight_by_edge[u])
        return distances
    except Exception as e:
        print(f"Error: {e}")
        return None


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