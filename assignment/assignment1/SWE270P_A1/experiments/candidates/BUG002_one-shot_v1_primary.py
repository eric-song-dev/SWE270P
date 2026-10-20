
def shortest_paths(source, weight_by_edge):
    """
    Finds the shortest paths between two nodes in a graph using Dijkstra's algorithm.

    Args:
        source: The starting node.
        weight_by_edge: The weight of the edge between the source and the target node.

    Returns:
        A dictionary containing the shortest paths from the source to the target node,
        or an empty dictionary if no path exists.
    """
    try:
        distances = {source: 0}
        visited = {source: 0}
        nodes = set(weight_by_edge.keys())
        for node in nodes:
            if node not in visited:
                distances[node] = 0
                visited[node] = 1
        
        if source not in distances:
            return {}

        paths = {}
        for u, v in weight_by_edge.items():
            if distances[u] == 0:
                paths[u] = []
            else:
                paths[u].append(v)
        
        return paths
    except Exception as e:
        print(f"Error: {e}")
        return {}


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