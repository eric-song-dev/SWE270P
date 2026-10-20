"""English repair plans and distinct prompt strategies for all required methods."""

from workflow import signature

TECHNIQUES = ("zero-shot", "one-shot", "chain-of-thought", "few-shot")
PLANS = {
    "BUG000": "Compare every pair of DISTINCT list positions. Calculate the ABSOLUTE difference of the two values. Return True if it is strictly less than threshold. After all pairs, return False. Empty lists and singletons have no pair. Do not change numbers.",
    "BUG001": "Use Dijkstra's algorithm with a DICTIONARY frontier mapping node objects to tentative distances. Initially frontier contains startnode with distance 0. Maintain a visited set. While frontier is nonempty, choose the node with the smallest distance using min(frontier, key=frontier.get), then REMOVE that node from frontier and save its distance. If it is goalnode, return that distance. Mark it visited. For each nextnode in node.successors that is not visited, calculate candidate = current distance + length_by_edge[node, nextnode]. Set frontier[nextnode] to min(frontier.get(nextnode, infinity), candidate). Return infinity after the while loop. Node objects cannot be ordered; compare their distances only. Do not call the original heap helpers.",
    "BUG002": "Bellman-Ford: create a distance dictionary containing BOTH endpoints of every edge, initialized to infinity. Set source distance to 0, including a source absent from all edges. Repeat len(distance)-1 full passes through the edge dictionary. For each (u,v) with weight w, assign distance[v] = min(distance[v], distance[u] + w). Only the NODE distance dictionary changes; never edit weight_by_edge. Return distances AFTER all passes. Negative edges and zero/positive cycles are allowed; negative cycles are excluded.",
    "BUG003": "Kruskal with shared component sets. Initialize groups={} and result=set(). Process edges in ascending weight order with sorted(weight_by_edge, key=weight_by_edge.get); keep the original edge tuple. For each (u,v), initialize groups[u] to {u} and groups[v] to {v} if missing. If these component sets differ, add the edge to result, compute merged = groups[u] | groups[v] as a NEW set, then assign groups[member] = merged for EVERY member of merged. Never mutate a set being iterated. Return result AFTER the edge loop, not inside it. Ignore edges whose endpoints already belong to the same component.",
    "BUG004": "Floyd-Warshall: initialize a dictionary with EVERY pair (i,j) for 0<=i,j<n, using 0 for i==j and infinity otherwise. Load each input edge with the minimum of the existing value and its edge weight, preserving a zero diagonal for positive self-loops. Use three nested loops in order k, i, j. Assign distance[i,j] = min(distance[i,j], distance[i,k] + distance[k,j]). Return the COMPLETE dictionary AFTER ALL loops. Never change length_by_edge. Negative edges are valid, negative cycles are excluded.",
    "BUG005": "Breadth-first reachability: use a Python LIST queue initialized to [startnode], and a seen set containing startnode. While queue is nonempty, remove its FIRST node with queue.pop(0). If this node is goalnode, return True. For each child in node.successors, if unseen, add it to seen and append it to queue. Return False AFTER the while loop. Use a list with pop(0), not a deque. Do not change graph links.",
    "BUG006": "Depth-first reachability: use an explicit Python LIST stack initially [startnode] and an empty visited set. While stack is nonempty, pop its LAST node. If node is goalnode, return True. If node is not visited, add it to visited and extend the stack with node.successors. Return False AFTER the while loop. Do not recurse; do not iterate over the Node itself. This must terminate on cycles and work on paths longer than Python's recursion limit.",
    "BUG007": "Reverse the existing acyclic singly linked list in place. Set previous=None. While node is not None: save following=node.successor; point node.successor to previous; set previous=node; advance node=following. Return previous AFTER the while loop. An empty input returns None; a singleton returns itself. Never allocate replacement nodes.",
    "BUG008": "Floyd cycle detection: slow=node and fast=node. While fast is not None AND fast.successor is not None, advance slow by ONE successor and fast by TWO successors, then return True if fast is slow. Return False AFTER the while loop, including for node=None. Do not change any successor pointers.",
    "BUG009": "Use a stack of INDICES to compute the longest balanced parentheses substring. Initialize stack=[-1] and best=0. For each index i and character c in s: if c=='(', append i to stack. Otherwise pop one index; if stack is then empty, append i as the new unmatched boundary, else update best=max(best, i-stack[-1]). Return best AFTER the for loop. The result counts characters, not pairs. The empty string returns 0.",
}

# Explicit control-flow plans reduce ambiguity for the 270M model. These are
# authored repair guidance, not claims that the model independently found bugs.
PLANS.update({
    "BUG000": "Initialize no state. For each index i in range(len(numbers)), for each j in range(i+1, len(numbers)), if abs(numbers[i] - numbers[j]) < threshold, return True. Outside BOTH loops return False. Never change the list.",
    "BUG001": "Set frontier = {startnode: 0} and visited = set(). WHILE frontier: choose node = min(frontier, key=frontier.get); distance = frontier.pop(node). If node is goalnode, return distance. Add node to visited. FOR nextnode in node.successors: IF nextnode not in visited: candidate = distance + length_by_edge[node, nextnode]; frontier[nextnode] = min(frontier.get(nextnode, float('inf')), candidate). After the WHILE loop return float('inf'). Use exactly these attributes and variable names. Nodes themselves cannot be ordered. Use the dictionary directly, not heap helpers.",
    "BUG002": "Start distances = {source: 0}. For each u,v in weight_by_edge, call distances.setdefault(u, float('inf')) and distances.setdefault(v, float('inf')). For each pass in range(len(distances)-1): for each (u,v),weight in weight_by_edge.items(): distances[v] = min(distances[v], distances[u] + weight). AFTER both loops, return distances. Never assign to weight_by_edge.",
    "BUG003": "Set groups={} and result=set(). FOR edge in sorted(weight_by_edge, key=weight_by_edge.get): unpack u,v=edge. Initialize groups.setdefault(u,{u}) and groups.setdefault(v,{v}). IF groups[u] != groups[v]: add edge to result; create merged=groups[u] | groups[v]; FOR member in merged: assign groups[member]=merged. Return result at FUNCTION indentation AFTER all loops. The merged set is never changed during iteration.",
    "BUG004": "Initialize distances={(i,j): (0 if i==j else float('inf')) for i in range(n) for j in range(n)}. For each edge,weight in length_by_edge.items(), set distances[edge]=min(distances[edge],weight). For k in range(n), for i in range(n), for j in range(n), assign distances[i,j]=min(distances[i,j],distances[i,k]+distances[k,j]). Return distances at FUNCTION indentation AFTER all loops. Do not change length_by_edge.",
    "BUG005": "Set queue=[startnode] (a Python list), seen={startnode}. WHILE queue: set node=queue.pop(0). IF node is goalnode: return True. FOR child in node.successors: IF child not in seen: seen.add(child); queue.append(child). Return False at FUNCTION indentation AFTER the WHILE loop. Use only the .successors attribute. Do not change graph links.",
    "BUG006": "Set stack=[startnode], visited=set(). WHILE stack: node=stack.pop(). IF node is goalnode: return True. IF node not in visited: visited.add(node); stack.extend(node.successors). Return False at FUNCTION indentation AFTER the WHILE loop. No recursion. The only node attribute is .successors.",
    "BUG007": "Set prevnode=None. WHILE node is not None, perform these FOUR assignments IN ORDER: nextnode=node.successor; node.successor=prevnode; prevnode=node; node=nextnode. AFTER the WHILE loop return prevnode. Use .successor only, never .next. Do not allocate any nodes.",
    "BUG008": "Set slow=node and fast=node. WHILE fast is not None AND fast.successor is not None: slow=slow.successor; fast=fast.successor.successor; IF slow is fast: return True. AFTER the WHILE loop return False. Use .successor only, never .next. Do not change any links.",
    "BUG009": "Set stack=[-1], best=0. FOR i,char in enumerate(s): IF char=='(': stack.append(i). ELSE: stack.pop(); IF not stack: stack.append(i); ELSE: best=max(best,i-stack[-1]). Return best at FUNCTION indentation AFTER the FOR loop. The stack contains integer INDICES, never characters.",
})

CHECKS = {
    "BUG000": "[1,3] at threshold 0.5 is False; duplicate values at a positive threshold are True; an exact threshold is excluded.",
    "BUG001": "s->a=2, a->t=3, s->t=9 gives 5; an unreachable goal gives infinity; start is goal gives 0; equal distances never compare Node objects.",
    "BUG002": "Edges B->C=-2 followed by A->B=4 give A:0,B:4,C:2; disconnected endpoints have infinity; the input dictionary remains identical.",
    "BUG003": "Edges (a,b):1,(c,d):2,(b,c):3,(a,d):10 select the first three edges; empty input returns set(); ties retain input order.",
    "BUG004": "0->1=2,1->2=-3 gives distance[0,2]=-1, distance[2,0]=infinity, and all diagonal distances 0.",
    "BUG005": "Two isolated distinct nodes give False; a node reaches itself; cycles with an unreachable goal terminate.",
    "BUG006": "A path of 2500 nodes is searchable without recursion; an unreachable goal in a directed cycle returns False.",
    "BUG007": "For a->b->None return b, with b.successor is a and a.successor is None; None returns None.",
    "BUG008": "None and a finite two-node list return False; a self-loop and a tail entering a cycle return True.",
    "BUG009": "'' gives 0; '()' gives 2; ')()())' gives 4; '))))' gives 0; '(())()' gives 6.",
}

EXAMPLES = (
    ("Count characters contributed by n matched pairs.", "def pair_length(n):\n    return 2 * n"),
    ("Iterate through all work items and return the total after the loop.", "def total(items):\n    result = 0\n    for item in items:\n        result += item\n    return result"),
    ("Advance through a linked chain without replacing its nodes.", "def last_node(node):\n    if node is None:\n        return None\n    while node.successor is not None:\n        node = node.successor\n    return node"),
)


def example(index, number):
    problem, solution = EXAMPLES[index]
    return f"Worked example {number}\nProblem: {problem}\nSolution:\n```python\n{solution}\n```\n"


def make_prompt(bug, technique, variant, feedback=""):
    header = f"Write the repaired Python function with this EXACT signature:\n{signature(bug)}\n"
    task = f"Implementation plan:\n{PLANS[bug]}\n"
    if variant == 1:
        task = f"Behavioral review checklist:\n{PLANS[bug]}\nAcceptance checks: {CHECKS[bug]}\n"
    output = (
        "Return the complete function in one Python code block. Preserve the exact signature. "
        "Do not write a docstring, examples, explanations, or test calls inside the code. "
        "Use only the stated node attributes. Final fallback returns must be outside all loops. "
        "Imports and original auxiliary functions are supplied by the surrounding module.\n"
    )
    if technique == "zero-shot":
        prefix = "Implement this repair from the plan.\n" if variant == 0 else "Act as a maintainer implementing a contract. Check boundaries, progress, and mutation.\n"
    elif technique == "one-shot":
        prefix = (
            "Use this single worked example to guide the implementation.\n" + example(1, 1)
            if variant == 0 else
            "Use this single pointer-state example as an illustration of careful state updates.\n" + example(2, 1)
        )
    elif technique == "chain-of-thought":
        prefix = (
            "First give two brief high-level bullets naming the invariant and repair. Then write the code.\n"
            if variant == 0 else
            f"Acceptance check: {CHECKS[bug]}\nFirst summarize the boundary/termination requirements in two short bullets. Then write the code.\n"
        )
    elif technique == "few-shot":
        prefix = (
            "Follow these two worked examples: count the right unit and return after all work.\n" + example(0, 1) + example(1, 2)
            if variant == 0 else
            "Use these three worked examples as state, loop-completion, and pointer-safety patterns.\n" + example(2, 1) + example(1, 2) + example(0, 3)
        )
    else:
        raise ValueError(technique)
    correction = f"Feedback from the previous generated candidate: {feedback}\nGenerate a new implementation satisfying the plan.\n" if feedback else ""
    return prefix + header + task + correction + output
