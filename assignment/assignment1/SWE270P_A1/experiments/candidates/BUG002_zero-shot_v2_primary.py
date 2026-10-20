
def shortest_paths(source, weight_by_edge):
    """
    Performs shortest paths from source to destination using a weighted graph.

    Args:
        source: The source node in the graph.
        weight_by_edge: A dictionary mapping source to the weight of the edge connecting source to destination.

    Returns:
        A dictionary where keys are nodes in the graph and values are the shortest paths from the source to that node.
    """
    try:
        distances = {node: float('inf') for node in weight_by_edge}
        for u, v in weight_by_edge.items():
            distances[v] = 0
        return distances
    except Exception as e:
        print(f"Error during shortest paths calculation: {e}")
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