def longestValidParentheses(s):
    maxans = 0
    dp = [0] * len(s)
    for i in range(1, len(s)):
        if s[i] == '(':
            if s[i - 1] == '(':
                dp[i] = (dp[i - 2] if i >= 2 else 0) + 1
            elif i - dp[i - 1] > 0 or s[i - dp[i - 1] - 1] == '(':
                dp[i] = (dp[i - 1] + 1)
            maxans = max(maxans, dp[i])
    return maxans
