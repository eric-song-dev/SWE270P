def longestValidParentheses(s):
    """
    Performs a longest valid parentheses problem.
    """
    stack = [-1]
    max_len = 0
    for char in s:
        if char == '(':
            stack.append(len(stack))
        else:
            stack.append(len(stack))
        if stack:
            max_len = max(max_len, len(stack))
    return max_len


"""
Longest Valid Parentheses

Input:
    s (str): A string consisting only of '(' and ')' characters.

Precondition:
    - The string may be empty.
    - Contains no other characters besides '(' and ')'.

Output:
    int: The length of the longest valid (well-formed) parentheses substring.

"""