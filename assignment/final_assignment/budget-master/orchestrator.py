# SWE 270P Final Project: AI Coder (multi-agent system with MCP) - BudgetMaster
# Group members (Name - Student ID):
#   Mouhamed Osman - 47083028
#   Zhenyu Song - 15305920
#   Jennifer Sun - 31687536
"""Orchestrator: the MCP client that coordinates the Planner, Coder and Tester agents.

Collaboration pattern - a pipeline with a test-driven feedback loop:

    Planner.create_design -> Coder.implement -> Tester.write_tests
                                  ^                    |
                                  |   tests failed     v
                             Coder.fix_code  <->  Tester.retest   (at most MAX_FIX_ROUNDS times)

Every arrow is an MCP tool call to an agent, and every agent runs as its own MCP
server process. The orchestrator makes no LLM calls itself; it only routes tasks
and collects each agent's LLM usage.
"""

import json
import os
import sys
import time
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from mcp import Client, StdioServerParameters

from agents.base import tool_text
from llm import PROJECT_ROOT

GENERATED_DIR = PROJECT_ROOT / "generated"
AGENT_MODULES = {"planner": "agents.planner", "coder": "agents.coder", "tester": "agents.tester"}
MAX_FIX_ROUNDS = int(os.getenv("MAX_FIX_ROUNDS", "2"))
AGENT_TIMEOUT_SECONDS = 900  # upper bound for one agent task (several LLM calls)


@dataclass
class RunState:
    """Live state of one generation run; the UI re-renders from it after every update."""

    workspace: Path | None = None  # directory of the generated project
    log: list = field(default_factory=list)  # activity lines shown in the UI
    usage: list = field(default_factory=list)  # one LLM usage record per agent task
    tests_passed: bool | None = None  # None until the Tester has reported
    test_output: str = ""
    error: str | None = None
    finished: bool = False
    started: float = field(default_factory=time.monotonic)


class Orchestrator:
    """Runs the multi-agent pipeline for one request and records progress in a RunState."""

    def __init__(self, state, on_update):
        """Keeps the run state and the callback that tells the UI the state has changed."""
        self.state = state
        self.on_update = on_update
        self.agents = {}  # agent name -> connected MCP client

    def log(self, source, message):
        """Adds a time-stamped line to the activity log (also printed to the terminal)."""
        elapsed = int(time.monotonic() - self.state.started)
        line = f"[{elapsed // 60:02d}:{elapsed % 60:02d}] {source:<12} {message}"
        self.state.log.append(line)
        print(line, file=sys.stderr, flush=True)
        self.on_update()

    def agent_server(self, module):
        """Describes how to launch one agent's MCP server (stdio transport) for this run."""
        return StdioServerParameters(
            command=sys.executable,
            args=["-m", module],
            cwd=str(PROJECT_ROOT),
            env={**os.environ, "WORKSPACE_DIR": str(self.state.workspace)},
        )

    async def call_agent(self, name, tool, step, **arguments):
        """Hands a task to an agent by calling one of its MCP tools, and returns the agent's reply.

        Parameters:
            name (str): Agent to call ("planner", "coder" or "tester").
            tool (str): MCP tool of that agent, i.e. the task it should perform.
            step (str): Label of this step in the usage report.
            arguments: Arguments of the tool call.

        Progress notifications sent by the agent during the call are appended to the log,
        and the LLM usage reported in the reply is recorded for the usage breakdown.
        """
        self.log("orchestrator", f"MCP {name}.{tool}()  [{step}]")

        async def on_progress(progress, total, message):
            """Receives the agent's MCP progress notifications."""
            self.log(name, message or "")

        result = await self.agents[name].call_tool(tool, arguments, progress_callback=on_progress)
        text = tool_text(result)
        if result.is_error:
            raise RuntimeError(f"{name}.{tool} failed: {text}")
        reply = json.loads(text)
        usage = reply["usage"]
        self.state.usage.append({"agent": name, "step": step, **usage})
        if "error" in reply:
            raise RuntimeError(f"{name}.{tool} failed: {reply['error']}")
        self.log(name, f"done (LLM calls: {usage['api_calls']}, tokens: {usage['total_tokens']:,})")
        return reply

    def record_tests(self, report):
        """Stores the Tester's verdict so the UI can show the test results."""
        self.state.tests_passed = report["tests_passed"]
        self.state.test_output = report["test_output"]
        self.on_update()

    async def run(self, description, requirements):
        """Creates the project directory, starts the three agent servers and runs the pipeline."""
        GENERATED_DIR.mkdir(exist_ok=True)
        self.state.workspace = GENERATED_DIR / datetime.now().strftime("run-%Y%m%d-%H%M%S")
        self.state.workspace.mkdir()

        async with AsyncExitStack() as stack:
            for name, module in AGENT_MODULES.items():
                client = Client(self.agent_server(module), read_timeout_seconds=AGENT_TIMEOUT_SECONDS)
                self.agents[name] = await stack.enter_async_context(client)
                self.log("orchestrator", f"connected to the {name} agent (MCP server over stdio)")
            try:
                await self.pipeline(description, requirements)
            except Exception as error:
                # Caught while the MCP connections are still open: once they close, the
                # error would be wrapped in an ExceptionGroup that hides its message.
                self.state.error = f"{type(error).__name__}: {error}"
                self.log("orchestrator", f"stopped: {self.state.error}")

    async def pipeline(self, description, requirements):
        """The collaboration pattern: Planner -> Coder -> Tester, then the fix loop while tests fail."""
        await self.call_agent(
            "planner", "create_design", "design", description=description, requirements=requirements
        )
        await self.call_agent(
            "coder", "implement", "implement", description=description, requirements=requirements
        )
        report = await self.call_agent(
            "tester", "write_tests", "write tests", description=description, requirements=requirements
        )
        self.record_tests(report)

        for fix_round in range(1, MAX_FIX_ROUNDS + 1):
            if report["tests_passed"]:
                break
            self.log("orchestrator", f"tests failed, starting fix round {fix_round}/{MAX_FIX_ROUNDS}")
            fix = await self.call_agent(
                "coder", "fix_code", f"fix round {fix_round}",
                requirements=requirements, test_report=report["test_output"],
            )
            report = await self.call_agent(
                "tester", "retest", f"retest round {fix_round}",
                requirements=requirements, coder_notes=fix["summary"],
            )
            self.record_tests(report)

        verdict = "all tests pass" if report["tests_passed"] else "some tests still fail"
        self.log("orchestrator", f"finished: {verdict}")


async def run_pipeline(description, requirements, state, on_update):
    """Entry point used by the UI: runs the pipeline and never raises.

    Parameters:
        description (str): Description of the software to build.
        requirements (str): Its requirements, one per line.
        state (RunState): Updated in place while the agents work.
        on_update (callable): Called without arguments whenever `state` changed.

    A failure is stored in state.error so the UI can show it next to the partial results.
    """
    orchestrator = Orchestrator(state, on_update)
    try:
        await orchestrator.run(description, requirements)
    except Exception as error:
        state.error = f"{type(error).__name__}: {error}"
        orchestrator.log("orchestrator", f"stopped: {state.error}")
    finally:
        state.finished = True
        on_update()


def usage_by_agent(usage):
    """Sums the per-task usage records by agent and appends a TOTAL row.

    Returns table rows: [agent, API calls, prompt tokens, completion tokens, total tokens].
    """
    keys = ("api_calls", "prompt_tokens", "completion_tokens", "total_tokens")
    totals = {name: dict.fromkeys(keys, 0) for name in AGENT_MODULES}
    for record in usage:
        for key in keys:
            totals[record["agent"]][key] += record[key]
    rows = [[name, *counts.values()] for name, counts in totals.items()]
    rows.append(["TOTAL", *(sum(counts[key] for counts in totals.values()) for key in keys)])
    return rows
