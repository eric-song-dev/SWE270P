# SWE 270P Final Project: AI Coder (multi-agent system with MCP) - BudgetMaster
# Group members (Name - Student ID):
#   Mouhamed Osman - 47083028
#   Zhenyu Song - 15305920
#   Jennifer Sun - 31687536
"""Coder agent (MCP server).

Role: software developer. Implements the application described in DESIGN.md
and repairs it when the Tester reports failing tests.
MCP tools used: workspace.list_files / read_file (to load context) and
workspace.write_file (called by the LLM to save source files).
"""

from mcp.server.mcpserver import Context, MCPServer

from agents.base import PROJECT_CONVENTIONS, is_test_file, run_task

mcp = MCPServer(
    "coder-agent",
    instructions="Coder agent: implements and fixes the application code.",
    log_level="WARNING",
)

SYSTEM_PROMPT = f"""\
You are the Coder agent in a three-agent software team (Planner → Coder → Tester).
Your job: implement the application exactly as specified in DESIGN.md so that it satisfies \
every requirement.

{PROJECT_CONVENTIONS}

How you work:
- Save every file with the write_file tool: one call per file, always with the complete file \
content. You may make several calls in one turn.
- Use the names and signatures from the design exactly; the Tester writes tests against them.
- Write complete, working code without placeholders or TODOs, and give every function a short \
docstring.
- In main.py use only current Streamlit APIs such as st.tabs, st.columns, st.form, st.metric, \
st.dataframe, st.bar_chart, st.line_chart, st.altair_chart and st.rerun. Never use st.cache or \
any st.experimental_* function; they have been removed from Streamlit.
- Every part of the page, including the sidebar, must show the new data right after a change. \
When a form changes the data: save it, store the confirmation text in st.session_state and call \
st.rerun(); show and clear that text at the top of the next run.
- Never write or change test files (test_*.py). Tests belong to the Tester.
- When all files are saved, reply with a summary of two or three sentences and no code."""


def may_write(path: str) -> bool:
    """The Coder may write any project file except test files."""
    return not is_test_file(path)


@mcp.tool()
async def implement(description: str, requirements: str, ctx: Context) -> dict:
    """Implement the application from DESIGN.md and save its source files to the workspace."""

    async def task(agent):
        """Loads the design over MCP, then lets the LLM write the source files with write_file."""
        design = await agent.use_tool("read_file", path="DESIGN.md")
        prompt = (
            f"# Software description\n{description}\n\n"
            f"# Requirements\n{requirements}\n\n"
            f"# DESIGN.md\n{design}\n\n"
            "Implement the complete application now."
        )
        summary = await agent.run_llm(
            SYSTEM_PROMPT, prompt, tools=("write_file",), may_write=may_write, must_write=True
        )
        return {"summary": summary}

    return await run_task("coder", ctx, task)


@mcp.tool()
async def fix_code(requirements: str, test_report: str, ctx: Context) -> dict:
    """Fix the application code so that the failing tests in the Tester's report pass."""

    async def task(agent):
        """Loads the current project over MCP, then lets the LLM rewrite the faulty source files."""
        files = await agent.project_files()
        prompt = (
            "The Tester ran the test suite and it FAILED. Fix the application code.\n\n"
            f"# Requirements\n{requirements}\n\n"
            f"# Test output\n{test_report}\n\n"
            f"# Current project files\n{files}\n\n"
            "Rules for this fix:\n"
            "- Rewrite every file you change with write_file (complete content).\n"
            "- Do not change test files. If a failing test contradicts the requirements or "
            "DESIGN.md, leave the code as it is for that test and explain the problem in your "
            "reply, so the Tester can correct the test.\n"
            "- Reply with a short summary of what you changed and of any test you consider wrong."
        )
        summary = await agent.run_llm(SYSTEM_PROMPT, prompt, tools=("write_file",), may_write=may_write)
        return {"summary": summary}

    return await run_task("coder", ctx, task)


if __name__ == "__main__":
    mcp.run("stdio")
