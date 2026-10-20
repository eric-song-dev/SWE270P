def depth_first_search(startnode, goalnode):
    if startnode is None:
        return 0
    if goalnode is None:
        return 0
    visited = set()
    while stack:
        node = stack.pop()
        if node is goalnode:
            return True
        if node not in visited:
            visited.add(node)
            stack.append(node)
    return False



"""
Depth-first Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""