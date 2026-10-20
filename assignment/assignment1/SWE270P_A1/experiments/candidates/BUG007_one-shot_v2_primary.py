def reverse_linked_list(node):
    if node is None:
        return None
    while node.successor is not None:
        node = node.successor
    return node


"""
Reverse Linked List

Reverses a linked list and returns the new head.

Input:
    node: The head of a singly-linked list

Precondition:
    The input is acyclic

Side effect:
    Mutates the list nodes' successor pointers

Output:
    The head of the reversed linked list
"""