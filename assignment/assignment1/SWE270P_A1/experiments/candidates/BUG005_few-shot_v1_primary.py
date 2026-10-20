
from collections import deque as Queue

def breadth_first_search(startnode, goalnode):
    queue = [startnode]
    seen = {}
    for child in node.successors:
        if child not in seen:
            seen[child] = 0
        queue.append(child)
    if queue:
        return True
    return False



"""
Breadth-First Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""