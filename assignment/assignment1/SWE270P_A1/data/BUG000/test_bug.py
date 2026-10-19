from .buggy import has_close_elements
import pytest



def test1():
    """Case 1: No two numbers are closer than the threshold
    Output: False
    """

    result = has_close_elements([1.0, 2.0, 3.0], 0.5)
    assert result == False


def test2():
    """Case 2: 2.8 and 3.0 are closer than the threshold
    Output: True
    """

    result = has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    assert result == True


def test3():
    """Case 3: 3.9 and 4.0 are closer than the threshold
    Output: True
    """

    result = has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3)
    assert result == True
