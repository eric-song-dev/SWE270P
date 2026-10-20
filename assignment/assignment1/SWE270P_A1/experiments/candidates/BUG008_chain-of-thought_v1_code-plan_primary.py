def detect_cycle(node):
    if node is None:
        return False
    if node.value is not None:
        return True
    return False



"""
Linked List Cycle Detection
tortoise-hare

Implements the tortoise-and-hare method of cycle detection.

Input:
    node: The head node of a linked list

Output:
    Whether the linked list is cyclic
"""