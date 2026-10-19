def detect_cycle(node):
    hare = tortoise = node

    while node:
        if hare is None:
            return False

        tortoise = tortoise.successor
        hare = hare.successor

        if hare is tortoise:
            return True



"""
Linked List Cycle Detection
tortoise-hare

Implements the tortoise-and-hare method of cycle detection.

Input:
    node: The head node of a linked list

Output:
    Whether the linked list is cyclic
"""