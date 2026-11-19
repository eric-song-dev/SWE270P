# SWE 270P Final Project: AI Coder (multi-agent system with MCP) - BudgetMaster
# Group members (Name - Student ID):
#   Mouhamed Osman - 47083028
#   Zhenyu Song - 15305920
#   Jennifer Sun - 31687536
"""Shared runtime for the Planner, Coder and Tester agents.

Each agent is an MCP *server* (the orchestrator calls its tools to hand it a
task) and at the same time an MCP *client* of the workspace tool server. This
module holds what the three agents have in common:

- run_task():    opens the LLM client and the MCP connection for one task and
                 attaches the LLM usage of that task to the reply.
- AgentRuntime:  the LLM tool-calling loop over MCP tools, plus helpers for
                 calling workspace tools and reporting progress.
"""

import json
import os
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

from llm import PROJECT_ROOT, LLMClient

WORKSPACE_SERVER = PROJECT_ROOT / "tools" / "workspace_server.py"
MAX_STEPS = int(os.getenv("AGENT_MAX_STEPS", "10"))  # LLM calls allowed per agent task

# Shared by all three system prompts so the agents agree on the shape of the project.
PROJECT_CONVENTIONS = """\
Conventions for every generated project (all agents follow them):
- Language: Python 3. The user interface is a Streamlit web app. Besides Streamlit and the \
libraries installed with it (pandas, altair), only the standard library is used.
- Layout: one flat project directory without sub-folders. `main.py` is the Streamlit entry point \
(`streamlit run main.py`); the application logic lives in one or more separate modules.
- Logic modules never import streamlit and never call input() or print(). They take arguments, \
return values and raise exceptions (ValueError for invalid input), so they can be unit-tested.
- main.py only builds the user interface and calls the logic modules. It collects input with \
Streamlit forms and widgets, shows a ValueError as an st.error message instead of crashing, and \
presents results visually with charts, tables and metrics rather than plain text.
- Code that reads or writes a file takes the file path as a parameter, so tests can use a \
temporary directory. main.py takes the path of its data file from the environment variable \
APP_DATA_FILE and falls back to a JSON file in the project directory.
- Tests are pytest files named test_*.py in the project root (`python -m pytest`)."""


def is_test_file(path: str) -> bool:
    """Tells whether a project file belongs to the Tester (test code) rather than the Coder."""
    name = Path(path).name
    return name.startswith("test_") or name.endswith("_test.py") or name == "conftest.py"


def tool_text(result) -> str:
    """Joins the text blocks of an MCP CallToolResult into one string."""
    return "\n".join(block.text for block in result.content if block.type == "text")


def workspace_server_params() -> StdioServerParameters:
    """Describes how to launch the workspace MCP server for the current project directory.

    Only WORKSPACE_DIR is passed on, so generated code and tests never see the LLM API key.
    """
    return StdioServerParameters(
        command=sys.executable,
        args=[str(WORKSPACE_SERVER)],
        env={"WORKSPACE_DIR": os.environ["WORKSPACE_DIR"]},
    )


def to_openai_tool(tool) -> dict:
    """Converts an MCP tool definition into the OpenAI function-calling format."""
    return {
        "type": "function",
        "function": {
            "name": tool.name,
            "description": tool.description or "",
            "parameters": tool.input_schema,
        },
    }


def assistant_entry(message) -> dict:
    """Converts an assistant reply into the dict that is appended to the conversation.

    `reasoning_content` is kept when present because DeepSeek's thinking mode requires it
    to be sent back on the following requests of a tool-calling conversation.
    """
    entry = {"role": "assistant", "content": message.content}
    if message.tool_calls:
        entry["tool_calls"] = [
            {
                "id": call.id,
                "type": "function",
                "function": {"name": call.function.name, "arguments": call.function.arguments},
            }
            for call in message.tool_calls
        ]
    reasoning = getattr(message, "reasoning_content", None)
    if reasoning:
        entry["reasoning_content"] = reasoning
    return entry


class AgentRuntime:
    """Everything one agent needs for one task.

    It bundles the agent's LLM client, its MCP connection to the workspace tool
    server, and the MCP request context used to report progress to the orchestrator.
    """

    def __init__(self, name, ctx, llm, workspace):
        """Stores the agent name, the MCP request context, the LLM client and the workspace MCP client."""
        self.name = name
        self.ctx = ctx
        self.llm = llm
        self.workspace = workspace
        self.progress = 0
        self.test_output = None  # output of the latest run_tests, while no file changed since

    async def notify(self, message):
        """Sends a progress notification to the orchestrator over MCP (shown live in the UI)."""
        self.progress += 1
        await self.ctx.report_progress(self.progress, None, message)

    async def call_workspace(self, tool, arguments):
        """Calls one workspace MCP tool. Returns (text output, whether the call succeeded)."""
        result = await self.workspace.call_tool(tool, arguments)
        text = tool_text(result)
        if tool == "run_tests":
            self.test_output = text
        elif tool == "write_file":
            self.test_output = None  # the files changed, so the last test run is out of date
        first_line = text.splitlines()[0] if text else ""
        outcome = f" → {first_line}" if tool in ("write_file", "run_tests") or result.is_error else ""
        await self.notify(f"MCP workspace.{tool}({arguments.get('path', '')}){outcome}")
        return text, not result.is_error

    async def use_tool(self, tool, **arguments):
        """Calls a workspace MCP tool from agent code (not chosen by the LLM) and returns its text.

        Used for steps that must always happen, such as loading context before
        the LLM is asked anything. Raises RuntimeError if the tool reports an error.
        """
        text, succeeded = await self.call_workspace(tool, arguments)
        if not succeeded:
            raise RuntimeError(text)
        return text

    async def project_files(self, include_tests=True):
        """Reads the project through the workspace MCP tools and formats it for a prompt.

        Loading the files up front costs no LLM call; letting the LLM read them one
        by one with tool calls would cost an extra round trip per file.
        """
        paths = (await self.use_tool("list_files")).splitlines()
        sections = []
        for path in paths:
            if path and (include_tests or not is_test_file(path)):
                content = await self.use_tool("read_file", path=path)
                sections.append(f"===== FILE: {path} =====\n{content}\n===== END OF {path} =====")
        return "\n\n".join(sections) or "(the project has no files yet)"

    async def execute_tool_call(self, call, allowed_tools, may_write):
        """Executes one tool call requested by the LLM. Returns (output for the LLM, success).

        Problems (invalid JSON, a tool or file outside the agent's role, a tool error) are
        returned as text instead of raised, so the LLM sees them and can correct itself.
        """
        name = call.function.name
        problem = None
        try:
            arguments = json.loads(call.function.arguments or "{}")
            if not isinstance(arguments, dict):
                raise ValueError("the arguments must be a JSON object")
        except ValueError as error:
            problem = f"the arguments of {name} were not valid JSON ({error}). Send the call again."
        else:
            if name not in allowed_tools:
                problem = f"the tool '{name}' is not available to the {self.name} agent."
            elif name == "write_file" and may_write and not may_write(str(arguments.get("path", ""))):
                problem = f"the {self.name} agent is not allowed to write '{arguments.get('path')}'."
        if problem:
            await self.notify(f"rejected tool call: {problem}")
            return f"Error: {problem}", False
        return await self.call_workspace(name, arguments)

    async def run_llm(self, system_prompt, task, tools=(), may_write=None, must_write=False):
        """Runs the agent's LLM on a task, executing the MCP tool calls it requests.

        Parameters:
            system_prompt (str): The agent's role and working rules.
            task (str): The task for this run, including all context the LLM needs.
            tools (tuple[str]): Names of the workspace MCP tools the LLM may call.
            may_write (callable | None): path -> bool; limits which files write_file may touch.
            must_write (bool): Remind the LLM once if it finishes without saving any file.

        The loop ends when the LLM answers without tool calls (that answer is returned)
        or after MAX_STEPS LLM calls.
        """
        schemas = []
        if tools:
            listed = await self.workspace.list_tools()  # tool discovery over MCP
            schemas = [to_openai_tool(tool) for tool in listed.tools if tool.name in tools]
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": task},
        ]
        wrote_file = False
        reminded = False
        for _ in range(MAX_STEPS):
            before = self.llm.usage.total_tokens
            message = await self.llm.chat(messages, schemas)
            used = self.llm.usage.total_tokens - before
            await self.notify(f"LLM call #{self.llm.usage.api_calls} ({used:,} tokens)")
            messages.append(assistant_entry(message))

            if not message.tool_calls:
                if must_write and not wrote_file and not reminded:
                    reminded = True
                    messages.append({
                        "role": "user",
                        "content": "You have not saved any file yet. Use the write_file tool to save your work.",
                    })
                    continue
                return message.content or ""

            for call in message.tool_calls:
                output, succeeded = await self.execute_tool_call(call, tools, may_write)
                if succeeded and call.function.name == "write_file":
                    wrote_file = True
                messages.append({"role": "tool", "tool_call_id": call.id, "content": output})
        return f"Stopped after {MAX_STEPS} LLM calls without finishing the task."


async def run_task(name, ctx, task):
    """Runs one agent task and returns its reply for the orchestrator.

    Parameters:
        name (str): Agent name, used in progress messages.
        ctx (Context): MCP request context of the tool call that started the task.
        task (callable): async function(AgentRuntime) -> dict holding the agent's work.

    The LLM usage of the task is always attached under "usage" - also when the task
    fails, in which case the reply carries an "error" message instead of a result.
    """
    llm = LLMClient()
    async with Client(workspace_server_params()) as workspace:
        try:
            reply = await task(AgentRuntime(name, ctx, llm, workspace))
        except Exception as error:  # reported to the orchestrator together with the usage so far
            reply = {"error": f"{type(error).__name__}: {error}"}
    reply["usage"] = llm.usage.as_dict()
    return reply
