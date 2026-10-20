def depth_first_search(startnode, goalnode):
    """Search with an explicit stack so long paths do not exhaust recursion."""
    nodesvisited = set()
    stack = [startnode]

    while stack:
        node = stack.pop()
        if node in nodesvisited:
            continue
        if node is goalnode:
            return True
        nodesvisited.add(node)
        stack.extend(reversed(node.successors))
    return False
