
from collections import deque as Queue

def breadth_first_search(startnode, goalnode):
    queue = [startnode]
    seen = set()
    while queue:
        node = queue.pop(0)
        if node is not goalnode:
            return True
        if node in seen:
            return False
        seen.add(node)
        queue.append(node)
    return False



"""
Breadth-First Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""