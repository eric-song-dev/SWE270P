# SWE 270P Final Project: AI Coder (multi-agent system with MCP) - BudgetMaster
# Group members (Name - Student ID):
#   Mouhamed Osman - 47083028
#   Zhenyu Song - 15305920
#   Jennifer Sun - 31687536
"""Workspace MCP server: the file and test tools that the agents work with.

The server is scoped to one generated project directory (WORKSPACE_DIR). The
agents connect to it as MCP clients and call its tools to read, write and test
the project, so the workspace doubles as the team's shared memory: the Planner
publishes DESIGN.md here, the Coder the source files, the Tester the tests.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from pydantic import Field

WORKSPACE = Path(os.environ["WORKSPACE_DIR"]).resolve()
TEST_TIMEOUT_SECONDS = 60
MAX_OUTPUT_CHARS = 6000  # keeps long pytest output from inflating the LLM prompt
IGNORED_DIRS = {"__pycache__", ".pytest_cache"}

mcp = MCPServer(
    "workspace",
    instructions="File and test tools scoped to one generated project directory.",
    log_level="WARNING",
)


def resolve(path: str) -> Path:
    """Maps a project-relative path to an absolute one, refusing paths that leave the workspace."""
    target = (WORKSPACE / path).resolve()
    if target == WORKSPACE or not target.is_relative_to(WORKSPACE):
        raise ToolError(f"'{path}' is not a file path inside the project directory")
    return target


@mcp.tool()
def write_file(
    path: Annotated[str, Field(description="File path relative to the project root, e.g. 'budget.py'")],
    content: Annotated[str, Field(description="The complete content of the file")],
) -> str:
    """Create or overwrite a text file in the project."""
    target = resolve(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return f"Wrote {len(content.splitlines())} lines to {path}"


@mcp.tool()
def read_file(
    path: Annotated[str, Field(description="File path relative to the project root")],
) -> str:
    """Return the content of a text file in the project."""
    target = resolve(path)
    if not target.is_file():
        raise ToolError(f"'{path}' does not exist")
    return target.read_text(encoding="utf-8")


@mcp.tool()
def list_files() -> str:
    """List every file in the project, one relative path per line."""
    files = []
    for item in WORKSPACE.rglob("*"):
        relative = item.relative_to(WORKSPACE)
        if item.is_file() and not IGNORED_DIRS.intersection(relative.parts):
            files.append(relative.as_posix())
    return "\n".join(sorted(files))


@mcp.tool()
def run_tests() -> str:
    """Run the project's pytest suite.

    The first line of the result is 'RESULT: PASSED' or 'RESULT: FAILED' followed by
    pytest's summary; the pytest output comes after it.
    """
    command = [sys.executable, "-m", "pytest", "-q", "--tb=short", "-p", "no:cacheprovider"]
    environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        # stdin is detached so the tests can never read from this server's MCP channel.
        run = subprocess.run(
            command,
            cwd=WORKSPACE,
            env=environment,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            timeout=TEST_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return (
            f"RESULT: FAILED - the tests did not finish within {TEST_TIMEOUT_SECONDS} seconds "
            "(infinite loop, or code waiting for user input?)"
        )
    output = (run.stdout + run.stderr).strip()
    summary = output.splitlines()[-1] if output else "pytest produced no output"
    status = "PASSED" if run.returncode == 0 else "FAILED"
    return f"RESULT: {status} - {summary}\n\n{output[-MAX_OUTPUT_CHARS:]}"


if __name__ == "__main__":
    mcp.run("stdio")
