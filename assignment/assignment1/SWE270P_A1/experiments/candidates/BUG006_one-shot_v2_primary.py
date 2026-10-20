def depth_first_search(startnode, goalnode):
    if startnode is None:
        return None
    while startnode.successor is not None:
        startnode = startnode.successor
    return startnode



"""
Depth-first Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""