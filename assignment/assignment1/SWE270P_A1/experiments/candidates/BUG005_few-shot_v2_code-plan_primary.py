
from collections import deque as Queue

def breadth_first_search(startnode, goalnode):
    """
    Performs a breadth-first search on a given node.

    Args:
        startnode: The starting node.
        goalnode: The goal node.

    Returns:
        The node that was visited in the breadth-first search.
    """
    if startnode is None:
        return goalnode
    seen = {startnode}
    while seen:
        node = seen.pop()
        if node is goalnode:
            return node
        for child in node.successors:
            if child not in seen:
                seen.add(child)
                queue.append(child)
            else:
                return node
    return startnode



"""
Breadth-First Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""