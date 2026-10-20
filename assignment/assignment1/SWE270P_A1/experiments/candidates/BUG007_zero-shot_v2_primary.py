def reverse_linked_list(node):
    if node is None:
        return None
    
    if node.val == 0:
        return node
    
    try:
        reversed_node = node.next
        node.next = reversed_node
        return reversed_node
    except Exception as e:
        return None


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