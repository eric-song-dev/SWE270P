def longestValidParentheses(s):
    maxans = 0
    dp = [0] * len(s)
    for i in range(1, len(s)):
        if s[i] == ")":
            if s[i - 1] == "(":
                dp[i] = (dp[i - 2] if i >= 2 else 0) + 1
            elif i - dp[i - 1] > 0 or s[i - dp[i - 1] - 1] == "(":
                dp[i] = (
                    dp[i - 1]
                    + (dp[i - dp[i - 1] - 2] if i - dp[i - 1] >= 2 else 0)
                    + 1
                )
            maxans = max(maxans, dp[i])
    return maxans


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
