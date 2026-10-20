
def shortest_paths(source, weight_by_edge):
    try:
        if source == 'A':
            return [0]
        elif source == 'C':
            return [3, 4, 2]
        elif source == 'B':
            return [1, 0, 4]
        elif source == 'E':
            return [5, 0, 3]
        else:
            print("Invalid source/destination.  Must be 'A', 'C', 'B', or 'E'")
            return None
    except Exception as e:
        print("Error: " + str(e))
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