from .node import Node
from .buggy import depth_first_search
import pytest



def test1():
    """Case 1: Strongly connected graph
    Output: Path found!
    """

    station1 = Node("Westminster")
    station2 = Node("Waterloo", None, [station1])
    station3 = Node("Trafalgar Square", None, [station1, station2])
    station4 = Node("Canary Wharf", None, [station2, station3])
    station5 = Node("London Bridge", None, [station4, station3])
    station6 = Node("Tottenham Court Road", None, [station5, station4])

    path_found = depth_first_search(station6, station1)

    assert path_found


def test2():
    """Case 2: Branching graph
    Output: Path found!
    """

    nodef = Node("F")
    nodee = Node("E")
    noded = Node("D")
    nodec = Node("C", None, [nodef])
    nodeb = Node("B", None, [nodee])
    nodea = Node("A", None, [nodeb, nodec, noded])

    path_found = depth_first_search(nodea, nodee)

    assert path_found


def test3():
    """Case 3: Two unconnected nodes in graph
    Output: Path not found
    """

    nodef = Node("F")
    nodee = Node("E")

    path_found = depth_first_search(nodef, nodee)

    assert not path_found


