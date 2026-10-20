"""Two distinct prompt designs per method, applied to all ten repair tasks."""

from repair_workflow import ROOT

CONTRACTS = {
    "BUG000": "Return whether two DISTINCT list positions have absolute difference strictly less than threshold. Do not mutate numbers. Empty/singleton lists return False; equal distance is not close.",
    "BUG001": "Return the shortest directed path length for positive edge weights, or infinity if unreachable. Nodes expose .successors and cannot be ordered. Accumulate distance from the current node; handle equal heap priorities and decreased priorities. Keep shortest_path_length, get, and insert_or_update with their existing parameters.",
    "BUG002": "Implement Bellman-Ford for all endpoint nodes plus source. Negative edges are permitted, negative cycles are excluded. Unreachable nodes have infinite distance. Update node distances, never the input edge dictionary. Include nodes appearing only as an edge source.",
    "BUG003": "Return a minimum spanning tree edge set using Kruskal's algorithm. Process equal weights in input order. Every member of a merged component must see the same membership. Avoid changing a set while iterating over it. Ignore self loops and do not mutate edge weights.",
    "BUG004": "Compute directed all-pairs shortest distances for nodes 0..n-1 using Floyd-Warshall. Relax through i -> k -> j, with zero-length empty paths and infinity for unreachable pairs. Positive self edges must not replace the zero-length empty path. Negative edges are allowed; negative cycles are excluded.",
    "BUG005": "Search forward from startnode through .successors. Return True exactly when goalnode is reachable, including startnode is goalnode. Return False when the queue empties. Mark discovered nodes to terminate on cycles; do not mutate graph links.",
    "BUG006": "Implement depth-first reachability through each node's .successors. Track visited nodes to terminate on cycles. Return a Boolean for reachable and unreachable goals; the start node reaches itself. Avoid a recursion-depth failure for long paths, and do not mutate graph links.",
    "BUG007": "Reverse an acyclic singly linked list IN PLACE using .successor. Return the original tail as the new head; original head becomes the tail with successor None. Preserve node identities and handle None and a singleton.",
    "BUG008": "Use Floyd's tortoise-and-hare algorithm on .successor: move the slow pointer once and the fast pointer twice. Return a Boolean for empty, finite, self-cycle, and tail-into-cycle lists. Check that the fast pointer and its next node exist before advancing twice. Do not mutate links.",
    "BUG009": "Return the CHARACTER LENGTH of the longest contiguous well-formed parentheses substring. Empty/unmatched inputs return zero. A matching pair adds TWO characters. Check the matching-open index before indexing and require both a valid index AND an opening parenthesis. Preserve the name longestValidParentheses(s).",
}

COUNTEREXAMPLES = {
    "BUG000": "numbers=[1.0, 3.0], threshold=0.5 must return False; numbers=[2.0,2.0], threshold=0.1 must return True.",
    "BUG001": "Edges s->a=2, a->t=3, s->t=9 must give 5. Two distinct successors at distance 2 must not cause a Node comparison TypeError.",
    "BUG002": "Edges B->C=1 then A->B=2, source A, must give A:0, B:2, C:3 without changing either edge weight; a disconnected source-only node must also be present.",
    "BUG003": "Edges (a,b):1, (c,d):2, (b,c):3, (a,d):10 must yield the first three edges without a set-size exception.",
    "BUG004": "Edges (0,1):2 and (1,2):3 give d[0,2]=5 and d[2,0]=infinity. A single positive self-loop still has d[0,0]=0.",
    "BUG005": "Two isolated different nodes must give False; start->middle->goal gives True; a reachable cycle with a disconnected goal must terminate with False.",
    "BUG006": "A node is not iterable; its .successors list is. In a two-node cycle with a disconnected goal, traversal must finish and return False.",
    "BUG007": "For a->b->None, return b and leave b.successor is a and a.successor is None. For None, return None.",
    "BUG008": "A two-node finite list must return False; a one-node self-loop must return True; None must return False, not None.",
    "BUG009": "'()' -> 2; ')()())' -> 4; '))))' -> 0; '(())()' -> 6. A leading ')' must not read a negative index as a matching opening.",
}

# These are worked repair examples, not additional target functions to submit.
EXAMPLES = {
    "absolute": ("def gap(a, b):\n    return a - b", "def gap(a, b):\n    return abs(a - b)", "Distance is nonnegative."),
    "queue": ("def drain(q):\n    while True:\n        q.popleft()", "def drain(q):\n    while q:\n        q.popleft()", "Stop when the worklist is empty."),
    "relax": ("def extend(distance, weight):\n    return weight", "def extend(distance, weight):\n    return distance + weight", "A path extension includes its prefix length."),
    "mapping": ("def improve(dist, node, candidate):\n    dist = min(dist[node], candidate)", "def improve(dist, node, candidate):\n    dist[node] = min(dist[node], candidate)", "Update the intended dictionary entry."),
    "merge": ("def merge(groups, a, b):\n    groups[a].update(groups[b])", "def merge(groups, a, b):\n    merged = groups[a] | groups[b]\n    for member in merged:\n        groups[member] = merged", "Publish merged membership to every member."),
    "direction": ("def via(d, a, b, c):\n    return d[a, b] + d[c, b]", "def via(d, a, b, c):\n    return d[a, b] + d[b, c]", "The second edge starts at the intermediate vertex."),
    "visited": ("def discover(seen, node):\n    return node not in seen", "def discover(seen, node):\n    if node in seen:\n        return False\n    seen.add(node)\n    return True", "Record discovery before revisiting a cyclic structure."),
    "pointer": ("def advance(previous, current):\n    current = current.successor\n    return previous, current", "def advance(previous, current):\n    previous, current = current, current.successor\n    return previous, current", "Preserve the current node before advancing."),
    "guard": ("def two_steps(node):\n    return node.successor.successor", "def two_steps(node):\n    if node is None or node.successor is None:\n        return None\n    return node.successor.successor", "Guard both dereferences."),
    "bounds": ("def opening_at(s, i):\n    return i >= 0 or s[i] == '('", "def opening_at(s, i):\n    return i >= 0 and s[i] == '('", "Bounds and content checks must both hold."),
    "pair": ("def add_pair(length):\n    return length + 1", "def add_pair(length):\n    return length + 2", "Count characters, not pairs."),
}

RELATED = {
    "BUG000": ("absolute", "bounds", "pair"),
    "BUG001": ("relax", "mapping", "queue"),
    "BUG002": ("mapping", "relax", "visited"),
    "BUG003": ("merge", "visited", "mapping"),
    "BUG004": ("direction", "relax", "mapping"),
    "BUG005": ("queue", "visited", "guard"),
    "BUG006": ("visited", "queue", "guard"),
    "BUG007": ("pointer", "guard", "queue"),
    "BUG008": ("guard", "pointer", "visited"),
    "BUG009": ("bounds", "pair", "guard"),
}


def worked_example(key, number):
    before, after, lesson = EXAMPLES[key]
    return (
        f"Worked repair {number}: {lesson}\n"
        f"Buggy:\n```python\n{before}\n```\n"
        f"Corrected:\n```python\n{after}\n```\n"
    )


def make_prompt(bug, technique, variant=0):
    source = (ROOT / "data" / bug / "buggy.py").read_text().strip()
    task = (
        f"Target file: {bug}/buggy.py\nContract: {CONTRACTS[bug]}\n"
        f"Original complete module:\n```python\n{source}\n```\n"
    )
    output = (
        "Keep all original function names and parameter definitions, imports, and helper "
        "functions. Return the complete replacement module in ONE Python code block. "
        "Do not include test invocations or print statements in the module.\n"
    )
    keys = RELATED[bug]
    if technique == "zero-shot":
        introduction = (
            "Repair this Python module from its behavioral contract. Inspect the implementation for all defects.\n"
            if variant == 0 else
            "Act as a maintainer reviewing a bug fix. Make a focused repair, preserving the public interface. "
            "Check empty inputs, termination, and input mutation against the contract.\n"
        )
        return introduction + task + output
    if technique == "one-shot":
        key = keys[variant]
        introduction = (
            "Follow the repair pattern in this single worked example, then fix the target.\n"
            if variant == 0 else
            "Use this single before/after review as a guide to preserving the invariant in the target.\n"
        )
        return introduction + worked_example(key, 1) + task + output
    if technique == "chain-of-thought":
        guidance = (
            "Before the code, give 2-3 brief high-level bullets naming the violated invariant, "
            "the correction, and a boundary case to verify.\n"
            if variant == 0 else
            f"Counterexample to check: {COUNTEREXAMPLES[bug]}\n"
            "Before the code, summarize in two short bullets why the current code fails "
            "this check and which repair restores the contract.\n"
        )
        return "Review this program repair task.\n" + task + guidance + output
    if technique == "few-shot":
        selected = keys[:2] if variant == 0 else keys
        introduction = (
            "Generalize the two worked repairs to the target module.\n"
            if variant == 0 else
            "Use these three small repair reviews as a checklist of state, bounds, and progress.\n"
        )
        examples = "\n".join(worked_example(key, i + 1) for i, key in enumerate(selected))
        return introduction + examples + task + output
    raise ValueError(f"Unknown prompting technique: {technique}")


TECHNIQUES = ("zero-shot", "one-shot", "chain-of-thought", "few-shot")
