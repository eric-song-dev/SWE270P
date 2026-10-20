def reverse_linked_list(node):
    if node is None:
        return 0
    try:
        next_node = node.successor
        node.successor = prevnode
        prevnode = node
        node = next_node
        return prevnode
    except Exception as e:
        print(f"Error during reverse_linked_list: {e}")
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