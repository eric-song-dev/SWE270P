# SWE 270P Final Project: AI Coder (multi-agent system with MCP) - BudgetMaster
# Group members (Name - Student ID):
#   Mouhamed Osman - 47083028
#   Zhenyu Song - 15305920
#   Jennifer Sun - 31687536
"""Tester agent (MCP server).

Role: QA engineer. Writes an executable pytest suite for the requirements,
runs it, and reports the result that drives the orchestrator's fix loop.
MCP tools used: workspace.list_files / read_file (to load context),
workspace.write_file and workspace.run_tests (both called by the LLM).
"""

from mcp.server.mcpserver import Context, MCPServer

from agents.base import PROJECT_CONVENTIONS, is_test_file, run_task

mcp = MCPServer(
    "tester-agent",
    instructions="Tester agent: writes and runs the test suite for the application.",
    log_level="WARNING",
)

SYSTEM_PROMPT = f"""\
You are the Tester agent in a three-agent software team (Planner → Coder → Tester).
Your job: write an executable pytest suite that checks the application against its \
requirements, run it, and report the result.

{PROJECT_CONVENTIONS}

How you work:
- Save test files with the write_file tool (test_*.py in the project root, always the complete \
file content). You may only write test files, never application code.
- Cover every requirement with at least one test, and add the important edge cases and invalid \
inputs. Name each test after the behaviour it checks and put the requirement id in its docstring.
- Test the logic modules through their public API. Use pytest's tmp_path for every file the code \
reads or writes.
- Smoke-test the user interface with Streamlit's AppTest (from streamlit.testing.v1 import AppTest), \
once with a data file path that does not exist yet and once with a data file that holds sample \
data saved through the logic modules:
      monkeypatch.setenv("APP_DATA_FILE", str(tmp_path / "data.json"))
      at = AppTest.from_file("main.py", default_timeout=30).run()
      assert not at.exception
  Do not simulate clicks or check individual widgets.
- After saving the tests, call run_tests.
- When a test fails, check the requirements and DESIGN.md to decide which side is wrong. If the \
test is wrong, correct it and run the tests again. If the application is wrong, keep the test \
unchanged: never weaken or delete a correct test to make it pass.
- Finish with a short report: what the tests cover, the final result, and for every remaining \
failure which application behaviour is wrong."""


async def final_report(agent, summary):
    """Builds the Tester's reply for the orchestrator from a real test run.

    The pass/fail verdict comes from the output of run_tests, not from what the LLM
    claims. If files changed after the LLM's last test run (or it never ran the tests),
    the suite is run once more from agent code, which costs no LLM call.
    """
    output = agent.test_output or await agent.use_tool("run_tests")
    return {
        "summary": summary,
        "tests_passed": output.startswith("RESULT: PASSED"),
        "test_output": output,
    }


@mcp.tool()
async def write_tests(description: str, requirements: str, ctx: Context) -> dict:
    """Write a pytest suite for the application, run it, and report whether it passes."""

    async def task(agent):
        """Loads the design and source over MCP, then lets the LLM write and run the tests."""
        files = await agent.project_files(include_tests=False)
        prompt = (
            f"# Software description\n{description}\n\n"
            f"# Requirements\n{requirements}\n\n"
            f"# Project files (design and application code)\n{files}\n\n"
            "Write the test suite, run it, and report."
        )
        summary = await agent.run_llm(
            SYSTEM_PROMPT, prompt, tools=("write_file", "run_tests"), may_write=is_test_file, must_write=True
        )
        return await final_report(agent, summary)

    return await run_task("tester", ctx, task)


@mcp.tool()
async def retest(requirements: str, coder_notes: str, ctx: Context) -> dict:
    """Re-run the tests after a fix by the Coder; correct the tests only if they are the faulty side."""

    async def task(agent):
        """Re-runs the suite first; the LLM is only consulted when tests still fail."""
        output = await agent.use_tool("run_tests")
        if output.startswith("RESULT: PASSED"):
            return {
                "summary": "All tests pass after the Coder's fix.",
                "tests_passed": True,
                "test_output": output,
            }
        files = await agent.project_files()
        prompt = (
            "The Coder changed the application to fix the failures you reported, but the test "
            "suite still fails.\n\n"
            f"# Requirements\n{requirements}\n\n"
            f"# Notes from the Coder\n{coder_notes}\n\n"
            f"# Test output\n{output}\n\n"
            f"# Current project files\n{files}\n\n"
            "Decide for each failure whether the test or the application is wrong. Correct the "
            "tests that are wrong, run the tests again, and report."
        )
        summary = await agent.run_llm(
            SYSTEM_PROMPT, prompt, tools=("write_file", "run_tests"), may_write=is_test_file
        )
        return await final_report(agent, summary)

    return await run_task("tester", ctx, task)


if __name__ == "__main__":
    mcp.run("stdio")
