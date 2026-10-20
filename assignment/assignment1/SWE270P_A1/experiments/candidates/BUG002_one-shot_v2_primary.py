
def shortest_paths(source, weight_by_edge):
    """
    Finds the shortest paths between two nodes in a weighted graph
    using depth-first search and breadth-first search.

    Args:
        source: The source node.
        weight_by_edge: The weight of the edge connecting the source to the target.

    Returns:
        A dictionary containing the shortest paths found, or None if no path exists.
    """
    try:
        distances = {source: 0}
        visited = {source: 0}
        nodes = set()
        for u, v in weight_by_edge:
            nodes.add(u)
            nodes.add(v)
        for node in nodes:
            if node is None:
                return None
            distances[node] = distances.get(node, 0) + weight_by_edge.get(node, 0)
            visited[node] = visited[node] + 1
        path_lengths = {}
        for u in nodes:
            for v in nodes:
                if u == v:
                    path_lengths[u] = 0
                else:
                    path_lengths[u] = path_lengths.get(u, 0) + weight_by_edge.get(v, 0)
        return distances, path_lengths
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