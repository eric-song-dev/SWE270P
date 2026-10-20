def shortest_paths(source, weight_by_edge):
    """Compute Bellman-Ford distances without changing the edge dictionary."""
    nodes = {source}
    for u, v in weight_by_edge:
        nodes.update((u, v))
    weight_by_node = {node: float("inf") for node in nodes}
    weight_by_node[source] = 0

    for _ in range(len(nodes) - 1):
        changed = False
        for (u, v), weight in weight_by_edge.items():
            candidate = weight_by_node[u] + weight
            if candidate < weight_by_node[v]:
                weight_by_node[v] = candidate
                changed = True
        if not changed:
            break
    return weight_by_node
