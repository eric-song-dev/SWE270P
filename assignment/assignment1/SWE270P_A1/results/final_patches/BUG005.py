from collections import deque as Queue


def breadth_first_search(startnode, goalnode):
    """Return whether goalnode is reachable along directed successor links."""
    queue = Queue([startnode])
    nodesseen = {startnode}

    while queue:
        node = queue.popleft()
        if node is goalnode:
            return True
        for nextnode in node.successors:
            if nextnode not in nodesseen:
                nodesseen.add(nextnode)
                queue.append(nextnode)
    return False
