def depth_first_search(startnode, goalnode):
    try:
        if startnode is None:
            return 0
        if goalnode is None:
            return goalnode
        return depth_first_search(startnode, goalnode)
    except Exception as e:
        return 0



"""
Depth-first Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""