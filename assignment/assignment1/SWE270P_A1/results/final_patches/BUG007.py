def reverse_linked_list(node):
    """Reverse successor pointers in place and return the new head."""
    prevnode = None
    while node is not None:
        nextnode = node.successor
        node.successor = prevnode
        prevnode = node
        node = nextnode
    return prevnode
