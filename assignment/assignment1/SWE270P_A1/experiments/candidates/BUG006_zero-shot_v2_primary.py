def depth_first_search(startnode, goalnode):
    """
    Performs a depth-first search on a list of nodes.

    Args:
        startnode: The starting node.
        goalnode: The goal node.

    Returns:
        True if the goal node is found, False otherwise.
    """
    try:
        if startnode == goalnode:
            return True
        else:
            visited = set()
            stack = [startnode]
            while stack:
                node = stack.pop()
                if node in visited:
                    return False
                visited.add(node)
                stack.append(node.successors)
    except Exception as e:
        return False
    return True



"""
Depth-first Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""