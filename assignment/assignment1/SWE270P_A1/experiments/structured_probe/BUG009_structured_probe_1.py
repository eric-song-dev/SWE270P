def longestValidParentheses(s):
    stack = [-1]
    best = 0
    for char in s:
        if char == '(':
            stack.append(i)
            best = i
        elif char == ')':
            if stack:
                best = max(best, i - stack[-1])
            else:
                stack.append(i)
    return best


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