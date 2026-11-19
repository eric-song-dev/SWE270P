# SWE 270P Final Project: AI Coder (multi-agent system with MCP) - BudgetMaster
# Group members (Name - Student ID):
#   Mouhamed Osman - 47083028
#   Zhenyu Song - 15305920
#   Jennifer Sun - 31687536
"""Web UI (Gradio) of the AI Coder. Start it with `python app.py`.

The user enters a software description and its requirements. The UI hands them
to the orchestrator and shows, while the agents work: the live agent / MCP
activity, the generated code, the generated test cases, the test results and the
LLM usage per agent. The finished project can be downloaded as a ZIP file.
"""

import asyncio
import os
import queue
import shutil
import threading
import time

import gradio as gr

from agents.base import is_test_file
from budgetmaster_spec import DESCRIPTION, REQUIREMENTS
from llm import PROJECT_ROOT
from orchestrator import GENERATED_DIR, RunState, run_pipeline, usage_by_agent

AGENT_USAGE_HEADERS = ["Agent", "API calls", "Prompt tokens", "Completion tokens", "Total tokens"]
STEP_USAGE_HEADERS = ["#", "Agent", "Step", "API calls", "Prompt tokens", "Completion tokens", "Total tokens"]
FENCE_LANGUAGES = {".py": "python", ".md": "markdown", ".json": "json"}
CSS = ".activity textarea { font-family: monospace; font-size: 12px; }"
# Keeps the newest line of the activity log visible whenever the log changes.
SCROLL_LOG_JS = """() => setTimeout(() => {
    const box = document.querySelector('.activity textarea');
    if (box) box.scrollTop = box.scrollHeight;
}, 50)"""


def read_project(workspace):
    """Reads the generated project from disk. Returns {relative path: content}, sorted by path."""
    files = {}
    if workspace and workspace.exists():
        for path in sorted(workspace.rglob("*")):
            if path.is_file() and "__pycache__" not in path.parts:
                files[path.relative_to(workspace).as_posix()] = path.read_text(encoding="utf-8", errors="replace")
    return files


def files_markdown(files, placeholder):
    """Formats files as Markdown: one heading and one syntax-highlighted code block per file."""
    if not files:
        return placeholder
    blocks = []
    for path, content in files.items():
        language = FENCE_LANGUAGES.get(os.path.splitext(path)[1], "text")
        blocks.append(f"### `{path}`\n````{language}\n{content}\n````")
    return "\n\n".join(blocks)


def status_markdown(state):
    """Builds the one-line status shown above the activity log."""
    calls = sum(record["api_calls"] for record in state.usage)
    tokens = sum(record["total_tokens"] for record in state.usage)
    usage = f"{calls} LLM API calls · {tokens:,} tokens"
    if not state.finished:
        return f"⏳ **Agents are working…** {usage} so far"
    seconds = int(time.monotonic() - state.started)
    if state.error:
        return f"❌ **Stopped:** {state.error}\n\n{usage} · {seconds}s"
    result = "✅ **Done: all tests pass.**" if state.tests_passed else "⚠️ **Done, but some tests still fail.**"
    folder = state.workspace.relative_to(PROJECT_ROOT).as_posix()
    return f"{result} {usage} · {seconds}s · saved in `{folder}/`"


def results_markdown(state):
    """Formats the Tester's latest test run for the 'Test results' tab."""
    if state.tests_passed is None:
        return "*The tests have not been run yet.*"
    verdict = "✅ All tests pass" if state.tests_passed else "❌ Some tests fail"
    return (
        f"### {verdict}\n````text\n{state.test_output}\n````\n"
        "Run the tests yourself inside the project folder with `python -m pytest`."
    )


def render(state):
    """Turns the run state into the values of all output components, in the order of OUTPUTS."""
    files = read_project(state.workspace)
    design = files.pop("DESIGN.md", "*The Planner has not published the design yet.*")
    tests = {path: content for path, content in files.items() if is_test_file(path)}
    code = {path: content for path, content in files.items() if path not in tests}

    code_view = files_markdown(code, "*No code has been generated yet.*")
    if code:
        code_view = f"Run the application inside the project folder with `streamlit run main.py`.\n\n{code_view}"

    archive = None
    if state.finished and files:
        # ZIP of the whole project folder (code, tests and DESIGN.md) for the download button.
        archive = shutil.make_archive(
            str(state.workspace), "zip", root_dir=state.workspace.parent, base_dir=state.workspace.name
        )

    step_rows = [
        [number, record["agent"], record["step"], record["api_calls"], record["prompt_tokens"],
         record["completion_tokens"], record["total_tokens"]]
        for number, record in enumerate(state.usage, start=1)
    ]
    return (
        status_markdown(state),
        "\n".join(state.log),
        code_view,
        files_markdown(tests, "*No test cases have been generated yet.*"),
        results_markdown(state),
        usage_by_agent(state.usage),
        step_rows,
        design,
        gr.update(value=archive, visible=archive is not None),
    )


def generate(description, requirements):
    """Click handler of the Generate button: runs the multi-agent pipeline and streams its progress.

    The pipeline runs in a worker thread with its own asyncio event loop (it starts the MCP
    server processes). Each state change is signalled through a queue, and this generator
    then yields a fresh rendering of the state to the browser.
    """
    if not description.strip() or not requirements.strip():
        raise gr.Error("Please enter both a software description and its requirements.")
    if not os.getenv("LLM_API_KEY"):
        raise gr.Error("LLM_API_KEY is not set. Copy .env.example to .env and add your API key.")

    state = RunState()
    updates = queue.Queue()
    worker = threading.Thread(
        target=lambda: asyncio.run(run_pipeline(description, requirements, state, lambda: updates.put(None))),
        daemon=True,
    )
    worker.start()
    while True:
        updates.get()  # wait for the next state change
        while not updates.empty():  # merge a burst of changes into one refresh
            updates.get_nowait()
        finished = state.finished
        yield render(state)
        if finished:
            break


with gr.Blocks(title="AI Coder") as demo:
    gr.Markdown(
        "# AI Coder: multi-agent code generation over MCP\n"
        "Enter a software description and its requirements. Three LLM agents "
        "(**Planner → Coder → Tester**), each running as an MCP server, build the application "
        "and its test cases; a fix loop repairs the code until the tests pass. "
        f"Model: `{os.getenv('LLM_MODEL', 'deepseek-flash')}`"
    )
    with gr.Row():
        with gr.Column(scale=5):
            description_box = gr.Textbox(label="Software description", lines=6, value=DESCRIPTION)
            requirements_box = gr.Textbox(label="Requirements (one per line)", lines=14, value=REQUIREMENTS)
            generate_button = gr.Button("Generate code and tests", variant="primary")
        with gr.Column(scale=6):
            status_view = gr.Markdown("Ready. Press **Generate code and tests** to start.")
            activity_view = gr.Textbox(
                label="Agent activity (MCP calls between orchestrator, agents and tools)",
                lines=24, max_lines=24, interactive=False, autoscroll=True, elem_classes=["activity"],
            )
    with gr.Tabs():
        with gr.Tab("Generated code"):
            download_view = gr.File(label="Download the generated project (ZIP)", interactive=False, visible=False)
            code_view = gr.Markdown("*No code has been generated yet.*")
        with gr.Tab("Test cases"):
            tests_view = gr.Markdown("*No test cases have been generated yet.*")
        with gr.Tab("Test results"):
            results_view = gr.Markdown("*The tests have not been run yet.*")
        with gr.Tab("LLM usage"):
            gr.Markdown("### Usage by agent")
            agent_usage_view = gr.Dataframe(headers=AGENT_USAGE_HEADERS, interactive=False)
            gr.Markdown("### Usage by pipeline step")
            step_usage_view = gr.Dataframe(headers=STEP_USAGE_HEADERS, interactive=False)
        with gr.Tab("Design"):
            design_view = gr.Markdown("*The Planner has not published the design yet.*")

    # The order must match the tuple returned by render().
    OUTPUTS = [
        status_view, activity_view, code_view, tests_view, results_view,
        agent_usage_view, step_usage_view, design_view, download_view,
    ]
    generate_button.click(generate, inputs=[description_box, requirements_box], outputs=OUTPUTS)
    activity_view.change(None, js=SCROLL_LOG_JS)


if __name__ == "__main__":
    demo.launch(css=CSS, allowed_paths=[str(GENERATED_DIR)])
