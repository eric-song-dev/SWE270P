# SWE 270P Final Project: AI Coder (multi-agent system with MCP) - BudgetMaster
# Group members (Name - Student ID):
#   Mouhamed Osman - 47083028
#   Zhenyu Song - 15305920
#   Jennifer Sun - 31687536
"""Our selected software description (BudgetMaster) and the requirements our group defined for it.

These two texts are the default input of the UI; they can be edited there before generating.
"""

# Software description, as given in the project sign-up sheet.
DESCRIPTION = (
    "BudgetMaster is a budgeting software application that helps individuals effectively manage "
    "their finances by providing comprehensive budgeting features. It allows users to input their "
    "income and expenses, categorize them, and set budget goals. The software provides visual "
    "representations of budget breakdowns and generates reports to track spending patterns. With "
    "BudgetMaster, users can make informed financial decisions and stay on track to achieve their "
    "financial goals."
)

# Functional requirements defined by our group.
REQUIREMENTS = """\
R1. Income: the user can record an income entry with an amount, a source and a date (YYYY-MM-DD).
R2. Expenses: the user can record an expense entry with an amount, a category, a date (YYYY-MM-DD) and an optional note.
R3. Categories: every expense belongs to a category. The app starts with the default categories Housing, Food, Transportation, Utilities, Entertainment, Healthcare and Other, and the user can add custom categories.
R4. Budget goals: the user can set and update a monthly budget limit for each category.
R5. Budget breakdown: for a chosen month (YYYY-MM), show for each category the amount spent, the budget limit, the remaining amount and the percentage of the budget used, and flag every category that is over budget. A category that has no budget limit shows its amount spent and "no limit"; it has no remaining amount or percentage and is never flagged.
R6. Visual representation: show the budget breakdown of a chosen month as charts: a bar chart that compares the amount spent with the budget limit of each category, and a chart that shows each category's share of the month's total spending.
R7. Monthly report: for a chosen month, report the total income, the total expenses, the net savings (income minus expenses) and the three categories with the highest spending.
R8. Spending pattern: show the total expenses of every recorded month in chronological order as a chart, so the user can see how spending changes over time.
R9. Validation: reject non-positive amounts, invalid dates, unknown categories and negative budget limits with a clear error message instead of crashing.
R10. Persistence: all data is saved to a JSON file and loaded again when the app restarts.
R11. Interface: a graphical user interface in the web browser gives access to all of the features above, with forms for entering data and tables and charts for the results."""
