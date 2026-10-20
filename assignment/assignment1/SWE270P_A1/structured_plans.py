"""Statement-level repair plans: explicit human guidance, implemented by Gemma.

The plan authors provide the algorithm and Python expressions. Gemma's role is
to emit a complete function with the stated control flow. Plans are not raw
model completions and are never saved as final patches by the experiment code.
"""

from workflow import signature, target_name

STATEMENTS = {
    "BUG000": [
        (0,"for i in range(len(numbers)):"),
        (1,"for j in range(i + 1, len(numbers)):"),
        (2,"if abs(numbers[i] - numbers[j]) < threshold:"),
        (3,"return True"),
        (0,"return False"),
    ],
    "BUG001": [
        (0,"frontier = {startnode: 0}"),
        (0,"visited = set()"),
        (0,"while frontier:"),
        (1,"node = min(frontier, key=frontier.get)"),
        (1,"distance = frontier.pop(node)"),
        (1,"if node is goalnode:"),
        (2,"return distance"),
        (1,"visited.add(node)"),
        (1,"for nextnode in node.successors:"),
        (2,"if nextnode not in visited:"),
        (3,"candidate = distance + length_by_edge[node, nextnode]"),
        (3,"frontier[nextnode] = min(frontier.get(nextnode, float('inf')), candidate)"),
        (0,"return float('inf')"),
    ],
    "BUG002": [
        (0,"distances = {source: 0}"),
        (0,"for u, v in weight_by_edge:"),
        (1,"distances.setdefault(u, float('inf'))"),
        (1,"distances.setdefault(v, float('inf'))"),
        (0,"for _ in range(len(distances) - 1):"),
        (1,"for (u, v), weight in weight_by_edge.items():"),
        (2,"distances[v] = min(distances[v], distances[u] + weight)"),
        (0,"return distances"),
    ],
    "BUG003": [
        (0,"groups = {}"),
        (0,"result = set()"),
        (0,"for edge in sorted(weight_by_edge, key=weight_by_edge.get):"),
        (1,"u, v = edge"),
        (1,"a = groups.setdefault(u, {u})"),
        (1,"b = groups.setdefault(v, {v})"),
        (1,"if a != b:"),
        (2,"result.add(edge)"),
        (2,"merged = a | b"),
        (2,"for member in merged:"),
        (3,"groups[member] = merged"),
        (0,"return result"),
    ],
    "BUG004": [
        (0,"distances = {(i, j): (0 if i == j else float('inf')) for i in range(n) for j in range(n)}"),
        (0,"for edge, weight in length_by_edge.items():"),
        (1,"distances[edge] = min(distances[edge], weight)"),
        (0,"for k in range(n):"),
        (1,"for i in range(n):"),
        (2,"for j in range(n):"),
        (3,"distances[i, j] = min(distances[i, j], distances[i, k] + distances[k, j])"),
        (0,"return distances"),
    ],
    "BUG005": [
        (0,"queue = [startnode]"),
        (0,"seen = {startnode}"),
        (0,"while queue:"),
        (1,"node = queue.pop(0)"),
        (1,"if node is goalnode:"),
        (2,"return True"),
        (1,"for child in node.successors:"),
        (2,"if child not in seen:"),
        (3,"seen.add(child)"),
        (3,"queue.append(child)"),
        (0,"return False"),
    ],
    "BUG006": [
        (0,"stack = [startnode]"),
        (0,"visited = set()"),
        (0,"while stack:"),
        (1,"node = stack.pop()"),
        (1,"if node is goalnode:"),
        (2,"return True"),
        (1,"if node not in visited:"),
        (2,"visited.add(node)"),
        (2,"stack.extend(node.successors)"),
        (0,"return False"),
    ],
    "BUG007": [
        (0,"prevnode = None"),
        (0,"while node is not None:"),
        (1,"nextnode = node.successor"),
        (1,"node.successor = prevnode"),
        (1,"prevnode = node"),
        (1,"node = nextnode"),
        (0,"return prevnode"),
    ],
    "BUG008": [
        (0,"slow = node"),
        (0,"fast = node"),
        (0,"while fast is not None and fast.successor is not None:"),
        (1,"slow = slow.successor"),
        (1,"fast = fast.successor.successor"),
        (1,"if slow is fast:"),
        (2,"return True"),
        (0,"return False"),
    ],
    "BUG009": [
        (0,"stack = [-1]"),
        (0,"best = 0"),
        (0,"for i, char in enumerate(s):"),
        (1,"if char == '(' :"),
        (2,"stack.append(i)"),
        (1,"else:"),
        (2,"stack.pop()"),
        (2,"if not stack:"),
        (3,"stack.append(i)"),
        (2,"else:"),
        (3,"best = max(best, i - stack[-1])"),
        (0,"return best"),
    ],
}


def small_example(number, variant=0):
    if variant == 0:
        return f"Worked example {number}:\nPlan: set answer=0; for each x in items add x to answer; after the loop return answer.\nSolution:\n```python\ndef total(items):\n    answer = 0\n    for x in items:\n        answer += x\n    return answer\n```\n"
    return f"Worked example {number}:\nPlan: if x is None return 0; otherwise return x.\nSolution:\n```python\ndef value_or_zero(x):\n    if x is None:\n        return 0\n    return x\n```\n"


def make_structured_prompt(bug, technique="zero-shot", variant=0, feedback=""):
    intro = "Implement this exact statement-level repair plan in Python. The algorithm is provided; your task is to emit its complete function correctly.\n"
    if technique == "one-shot":
        intro += small_example(1, variant)
    elif technique == "few-shot":
        intro += small_example(1, 0) + small_example(2, 1)
    elif technique == "chain-of-thought":
        intro += "Before the code, give two short high-level bullets about the loop invariant and final return placement.\n"
    intro += f"Target signature: {signature(bug)}\n"
    if variant == 0:
        intro += "Each row gives a nesting level and the exact Python statement. Level 0 is inside the function (4 spaces); level 1 is 8 spaces; level 2 is 12 spaces; level 3 is 16 spaces. Preserve row order and nesting.\n"
        intro += "\n".join(f"Level {level}: {statement}" for level, statement in STATEMENTS[bug])
    else:
        intro += "Implement these ordered body statements with the indicated indentation in spaces:\n"
        intro += "\n".join(f"{4*(level+1)} spaces | {statement}" for level, statement in STATEMENTS[bug])
    if feedback:
        intro += f"\nPrevious candidate failed: {feedback[:500]}\n"
    return intro + f"\nOutput ONLY a Python code block containing {target_name(bug)} with the exact target signature. Do not output example functions. Do not add a docstring or usage example.\n"


def make_code_plan_prompt(bug, technique="zero-shot", variant=0, feedback=""):
    """A deliberately explicit plan; success is guided emission, not discovery."""
    intro = "Implement the supplied repair plan as Python. The original function header and imports are supplied separately.\n"
    if variant >= 4:
        intro = "Transcribe the supplied corrected function-body plan exactly. Preserve every statement, loop, variable name, and relative indentation. Do not simplify the plan or invent additional behavior.\n"
    if technique == "one-shot":
        intro += small_example(1,variant)
    elif technique == "few-shot":
        intro += small_example(1,0)+small_example(2,1)
    elif technique == "chain-of-thought":
        intro += "Before the code, summarize the loop progress and return placement in two brief bullets.\n"
    intro += f"Target function signature: {signature(bug)}\n"
    if variant == 0:
        intro += "The following Python statements specify the repair plan. Emit the function body, preserving these operations, names, and relative indentation:\n"
    else:
        intro += "Review this statement-level implementation plan for the target. Output its complete function, or just its body. Preserve the plan's control flow and final return outside all loops:\n"
    offset = 1 if variant >= 2 else 0
    if offset:
        intro += "The body below is ALREADY indented for inside the function. Keep the final return at FOUR spaces, outside all loops. You may output only this body; the original header will be supplied unchanged.\n"
    intro += "```python\n"+"\n".join("    "*(level+offset)+statement for level,statement in STATEMENTS[bug])+"\n```\n"
    if feedback:
        intro += f"Previous generation failed: {feedback[:500]}\n"
    ending = f"Return only the Python implementation for {target_name(bug)} in a code block. No docstrings, example functions, or test calls.\n"
    if variant >= 4:
        ending = "Copy ALL of the supplied body statements into one Python code block, preserving their indentation. Omit the def line; the original header is supplied by the harness. Do not add a docstring.\n"
    return intro + ending
