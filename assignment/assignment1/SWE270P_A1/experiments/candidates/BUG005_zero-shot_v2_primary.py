
from collections import deque as Queue

def breadth_first_search(startnode, goalnode):
    try:
        if startnode == goalnode:
            return True
        for child in goalnode.successors:
            if child not in seen:
                return False
        return True
    except Exception as e:
        return False



"""
Breadth-First Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""