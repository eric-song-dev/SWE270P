from .node import Node
from .buggy import detect_cycle
import pytest



node1 = Node(1)
node2 = Node(2, node1)
node3 = Node(3, node2)
node4 = Node(4, node3)
node5 = Node(5, node4)


def test1():
    """Case 1: 5-node list input with no cycle
    Expected Output: Cycle not detected!
    """

    detected = detect_cycle(node5)

    assert not detected


def test2():
    """Case 2: 5-node list input with cycle
    Expected Output: Cycle detected!
    """

    node1.successor = node5

    detected = detect_cycle(node5)

    assert detected


def test3():
    """Case 3: 2-node list with cycle
    Expected Output: Cycle detected!
    """

    node1.successor = node2

    detected = detect_cycle(node2)

    assert detected


