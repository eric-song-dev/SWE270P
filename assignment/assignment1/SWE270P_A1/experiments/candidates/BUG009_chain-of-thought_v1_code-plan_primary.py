def longestValidParentheses(s):
    stack = [-1]
    best = 0
    for i, char in enumerate(s):
        if char == '(' :
            stack.append(i)
        else:
            stack.pop()
            if not stack:
                stack.append(i)
            else:
                best = max(best, i - stack[-1])
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