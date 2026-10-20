
from collections import deque as Queue

def breadth_first_search(startnode, goalnode):
    try:
        queue = [startnode]
        seen = {startnode}
        while queue:
            node = queue.pop(0)
            if node is goalnode:
                return True
            for child in node.successors:
                if child not in seen:
                    seen.add(child)
                    queue.append(child)
                else:
                    return False
        return False
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