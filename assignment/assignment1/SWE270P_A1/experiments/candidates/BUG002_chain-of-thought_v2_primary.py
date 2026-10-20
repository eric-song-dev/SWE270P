
def shortest_paths(source, weight_by_edge):
    """
    Generates a new implementation of the shortest paths algorithm.

    Args:
        source: The source vertex of the path.
        weight_by_edge: The weight of the edge from the source vertex to the destination vertex.

    Returns:
        A function that takes a source vertex and a weight_by_edge as input
        and returns a new function that takes the source vertex and a weight_by_edge as input.
        It returns a new function that takes a source vertex and a weight_by_edge as input
        and returns a new function that takes the source vertex and a weight_by_edge as input.
    """

    # Create a new function that takes a source vertex and a weight_by_edge as input
    def shortest_paths(source, weight_by_edge):
        """
        Generates a new implementation of the shortest paths algorithm.

        Args:
            source: The source vertex of the path.
            weight_by_edge: The weight of the edge from the source vertex to the destination vertex.

        Returns:
            A function that takes a source vertex and a weight_by_edge as input
            and returns a new function that takes the source vertex and a weight_by_edge as input.
            It returns a new function that takes a source vertex and a weight_by_edge as input
            and returns a new function that takes the source vertex and a weight_by_edge as input.
        """
        return shortest_paths

    return shortest_paths


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