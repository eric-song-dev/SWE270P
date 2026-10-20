def depth_first_search(startnode, goalnode):
    stack = [startnode]
    visited = set()
    while stack:
        node = stack.pop()
        if node is goalnode:
            return True
        if node not in visited:
            visited.add(node)
            stack.extend(node.successors)
    return False



"""
Depth-first Search


Input:
    startnode: A digraph node
    goalnode: A digraph node

Output:
    Whether goalnode is reachable from startnode
"""