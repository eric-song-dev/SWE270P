"""Use observed failures to try shorter, explicit edit instructions with Gemma."""

import ast
import json
import time

from evaluate import evaluate_patch
from prompt_designs import CONTRACTS
from repair_workflow import MODEL_ID, PROMPTS_PATH, ROOT, extract_code, generate_text, log_prompt, validate_interface

EDITS = {
    "BUG000": "Replace `distance = elem - elem2` with `distance = abs(elem - elem2)`.",
    "BUG001": "Use Dijkstra's algorithm with heap entries (distance, unique_counter, node). Store best distances in a separate dict. Set candidate = distance + length_by_edge[node, nextnode]. Push only improved candidates. Skip already visited nodes. Keep get and insert_or_update; call heapify after updating an existing heap entry.",
    "BUG002": "Initialize weight_by_node for BOTH endpoints of every edge and the source. In the relaxation loop assign weight_by_node[v], not weight_by_edge[u, v]. Keep input edge weights unchanged.",
    "BUG003": "Replace all three lines after mst_edges.add(edge) with: compute merged = group_by_node[u] | group_by_node[v], then for each node in merged assign group_by_node[node] = merged. Do not mutate either old component set.",
    "BUG004": "Replace length_by_path[j, k] with length_by_path[k, j]. When loading edges, assign min(existing distance, edge length) so a positive self-loop keeps diagonal distance zero.",
    "BUG005": "Replace queue.append(goalnode) with queue.append(startnode). Replace while True with while queue. Keep the final return False for queue exhaustion.",
    "BUG006": "Use a stack initialized with startnode. While the stack has nodes, pop one, skip visited nodes, return True for the goal, mark it visited, and push node.successors. Return False after exhaustion. Do not recurse or iterate over the Node object itself.",
    "BUG007": "Insert `prevnode = node` directly after `node.successor = prevnode` and before `node = nextnode`.",
    "BUG008": "Replace while node with while hare is not None and hare.successor is not None. Advance hare using hare = hare.successor.successor. Keep tortoise moving one step. Return False after the loop, including empty input.",
    "BUG009": "Change both pair-length increments from + 1 to + 2. Change the elif condition's `or` to `and` so the boundary check guards the indexing expression. Keep the DP recurrence otherwise unchanged.",
}


def main():
    existing = {json.loads(line).get("attempt_id") for line in PROMPTS_PATH.read_text().splitlines()}
    results = ROOT / "experiments" / "refinement_evaluations.jsonl"
    completed = {json.loads(line)["attempt_id"] for line in results.read_text().splitlines()} if results.exists() else set()
    for bug, edits in EDITS.items():
        attempt = f"{bug}_zero-shot_failure-guided"
        if attempt in completed:
            continue
        tree = ast.parse((ROOT / "data" / bug / "buggy.py").read_text())
        # Remove prose docstrings to reduce copying and keep the repair request short.
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef)):
                node.body = [statement for statement in node.body if not (isinstance(statement, ast.Expr) and isinstance(statement.value, ast.Constant) and isinstance(statement.value.value, str))]
        source = ast.unparse(tree)
        prompt = (
            f"Repair this Python code. The previous attempt failed its unit tests.\n"
            f"Apply these exact edits: {edits}\n"
            f"Expected behavior: {CONTRACTS[bug]}\n"
            f"```python\n{source}\n```\n"
            "Return ONLY the complete corrected Python module in one code block. "
            "Preserve all original function signatures and helper functions."
        )
        started = time.perf_counter()
        if attempt in existing:
            completion = next(json.loads(line)["completion"] for line in PROMPTS_PATH.read_text().splitlines() if json.loads(line).get("attempt_id") == attempt)
        else:
            completion = generate_text(prompt, max_new_tokens=1024)
            log_prompt(
                "zero-shot", prompt, completion, f"{bug}.py", MODEL_ID,
                attempt_id=attempt, variant="failure-guided-revision",
                parent_attempt=f"{bug}_zero-shot_1", max_new_tokens=1024,
                do_sample=False, elapsed_seconds=round(time.perf_counter() - started, 3),
            )
        assessment = {"attempt_id": attempt, "bug": bug, "technique": "zero-shot"}
        try:
            code = extract_code(completion)
            (ROOT / "experiments" / "candidates" / f"{attempt}.py").write_text(code)
            try:
                validate_interface(f"{bug}.py", code)
                assessment["interface_valid"] = True
            except ValueError as error:
                assessment["interface_valid"] = False
                assessment["interface_error"] = str(error)
            assessment["tests"] = evaluate_patch(bug, code)
            assessment["status"] = "passed" if assessment["interface_valid"] and assessment["tests"]["all_passed"] else "failed"
        except (ValueError, SyntaxError) as error:
            assessment.update(status="extraction_failed", error=str(error))
        with results.open("a") as stream:
            stream.write(json.dumps(assessment) + "\n")
        print(attempt, assessment["status"], flush=True)


if __name__ == "__main__":
    main()
