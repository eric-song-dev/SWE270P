# SWE 270P Final Project: AI Coder (multi-agent system with MCP) - BudgetMaster
# Group members (Name - Student ID):
#   Mouhamed Osman - 47083028
#   Zhenyu Song - 15305920
#   Jennifer Sun - 31687536
"""Planner agent (MCP server).

Role: software architect. Turns the user's description and requirements into
DESIGN.md, the contract that the Coder implements and the Tester tests against.
MCP tools used: workspace.write_file (to publish DESIGN.md).
"""

from mcp.server.mcpserver import Context, MCPServer

from agents.base import PROJECT_CONVENTIONS, run_task

mcp = MCPServer(
    "planner-agent",
    instructions="Planner agent: designs the application from its description and requirements.",
    log_level="WARNING",
)

SYSTEM_PROMPT = f"""\
You are the Planner agent in a three-agent software team (Planner → Coder → Tester).
Your job: turn a software description and its requirements into a short technical design. \
The Coder implements the design and the Tester writes tests against it.

{PROJECT_CONVENTIONS}

Write the design in Markdown with exactly these sections:
1. Overview - two or three sentences.
2. Files - every file and its responsibility.
3. Data model - the data structures and the format of persisted data.
4. Public API - for every class and function of the logic modules: the exact signature with \
type hints, what it returns, and which exception it raises for which invalid input.
5. User interface - the layout of main.py: its tabs or sections, the form for each kind of input, \
and the chart, table or metric that presents each result.
6. Requirement mapping - a table that maps each requirement (R1, R2, ...) to the API and the part \
of the user interface that satisfy it.
7. How to run - the commands to install the dependencies, start the application and run the tests.

The Coder and the Tester rely on the exact names and signatures, so be precise. Keep the project \
as small as the requirements allow. Do not write implementation code. Reply with the Markdown \
document only."""


def strip_code_fence(text: str) -> str:
    """Removes a ```markdown ... ``` wrapper if the LLM put one around the whole document."""
    lines = text.strip().splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        lines = lines[1:-1]
    return "\n".join(lines).strip() + "\n"


@mcp.tool()
async def create_design(description: str, requirements: str, ctx: Context) -> dict:
    """Design the application and publish the design as DESIGN.md in the workspace."""

    async def task(agent):
        """One LLM call writes the design; the agent then saves it through the workspace MCP server."""
        prompt = f"# Software description\n{description}\n\n# Requirements\n{requirements}"
        design = strip_code_fence(await agent.run_llm(SYSTEM_PROMPT, prompt))
        await agent.use_tool("write_file", path="DESIGN.md", content=design)
        return {"summary": "Design published as DESIGN.md"}

    return await run_task("planner", ctx, task)


if __name__ == "__main__":
    mcp.run("stdio")
