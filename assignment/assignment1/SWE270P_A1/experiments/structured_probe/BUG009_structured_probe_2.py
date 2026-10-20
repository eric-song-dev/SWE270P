def longestValidParentheses(s):
    stack = [-1]
    longest = 0
    for char in s:
        if char == '(':
            stack.append(len(stack))
            longest = len(stack)
        elif char == ')':
            stack.pop()
            longest = max(longest, len(stack))
        else:
            stack.append(len(stack))
    return longest


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