def detect_cycle(node):
    slow = node
    fast = node.parent
    while fast is None and fast.next is None:
        slow = slow.parent
        fast = fast.next

    if slow is None or fast is None:
        return False

    return slow == fast



"""
Linked List Cycle Detection
tortoise-hare

Implements the tortoise-and-hare method of cycle detection.

Input:
    node: The head node of a linked list

Output:
    Whether the linked list is cyclic
"""