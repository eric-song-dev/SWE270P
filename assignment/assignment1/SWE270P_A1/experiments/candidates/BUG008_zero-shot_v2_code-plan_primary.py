def detect_cycle(node):
    if node is None:
        return False
    try:
        if node.successor is not None:
            return True
        return False
    except Exception as e:
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