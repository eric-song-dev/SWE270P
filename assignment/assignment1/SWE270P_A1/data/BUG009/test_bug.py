from .buggy import longestValidParentheses
import pytest


def test1():
    s = "()"
    assert longestValidParentheses(s) == 2


def test2():
    s = "(())"
    assert longestValidParentheses(s) == 4


def test3():
    s = "()()"
    assert longestValidParentheses(s) == 4

