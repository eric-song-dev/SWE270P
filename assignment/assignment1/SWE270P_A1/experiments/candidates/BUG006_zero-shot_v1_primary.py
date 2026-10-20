def depth_first_search(startnode, goalnode):
    stack = [startnode]
    visited = set()
    while stack:
        node = stack.pop()
        if node in visited:
            return True
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