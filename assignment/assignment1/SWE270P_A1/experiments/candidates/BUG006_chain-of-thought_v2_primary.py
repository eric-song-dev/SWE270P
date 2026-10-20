def depth_first_search(startnode, goalnode):
    try:
        if startnode == goalnode:
            return True
        else:
            return False
    except:
        return False



"""
Depth-first Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""