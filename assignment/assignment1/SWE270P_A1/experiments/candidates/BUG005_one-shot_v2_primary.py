
from collections import deque as Queue

def breadth_first_search(startnode, goalnode):
    queue = [startnode]
    seen = set()
    for child in node.successors:
        if child in seen:
            return False
        seen.add(child)
    return True



"""
Breadth-First Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""