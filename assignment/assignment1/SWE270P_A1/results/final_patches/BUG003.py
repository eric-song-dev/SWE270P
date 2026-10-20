def minimum_spanning_tree(weight_by_edge):
    """Return Kruskal's minimum spanning tree (a forest if disconnected)."""
    group_by_node = {}
    mst_edges = set()

    for edge in sorted(weight_by_edge, key=weight_by_edge.__getitem__):
        u, v = edge
        group_u = group_by_node.setdefault(u, {u})
        group_v = group_by_node.setdefault(v, {v})
        if group_u != group_v:
            mst_edges.add(edge)
            merged = group_u | group_v
            for node in merged:
                group_by_node[node] = merged
    return mst_edges
