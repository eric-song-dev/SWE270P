
from collections import deque as Queue

def breadth_first_search(startnode, goalnode):
    queue = [startnode]
    seen = {}
    while queue:
        node = queue.pop(0)
        if node == goalnode:
            return True
        if node in seen:
            return False
        seen[node] = len(queue)
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