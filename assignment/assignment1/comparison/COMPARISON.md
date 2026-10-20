# Assignment 1 branch comparison

Reviewed on October 19, 2026, using the assignment's Python 3.12 virtual environment.

**Subsequent Gradescope fix:** The version 2 archive in `submissions/` has now
been updated after the server reported 19/20 tests passing. BUG004's case8
requires an explicit positive self-loop to override the default zero diagonal.
A new local Gemma generation changes only `distances[edge] = weight`; its raw
prompt and output are appended to the submission log (174 records). The other
nine patches are byte-identical. The supplied case8 regression and the complete
local suite passed: 157 cases, comprising 30 supplied, 109 existing additional
cases with their BUG004 self-loop expectations corrected to the observed
contract, and 18 new regression cases. The random-graph checks use an independent
simple-path/cycle oracle for this convention. Earlier comparison results below
describe the original commits, not this revised archive. New provenance,
before/after evidence, and hashes are in [bug004_gradescope_fix.json](bug004_gradescope_fix.json).
The revised archive has not yet been rerun on Gradescope by the assistant.

Version 1's submission copy has also received the same BUG004 contract fix.
Its replacement body was emitted in a new logged local Gemma call, with the
existing module scaffold retained and the explanatory docstring clarified.
Its other nine patches are unchanged, its original 92 prompt records are
preserved, and the new record brings its log to 93. Its 30 supplied, 109 existing
additional cases (with the same BUG004 contract correction), and 18 new
regressions all passed: 157 cases. Details and its current hash are in
[bug004_gradescope_fix_v1.json](bug004_gradescope_fix_v1.json).

| Version | Reviewed commit |
|---|---|
| `feat-codex-generated-1` | `f4bfb542f06a90f22bec6c0ba2a8c1098043a6dc` |
| `feat-codex-generated-2` | `98256b48377c3ee0baea707823d7c4eb97623ac4` |

**Recommendation: choose version 2 if submitting one of the two current archives unchanged.** Its final code has stronger traceability to the required model and its notebook connects prompting, selection, testing, and packaging. Version 1 has better shortest-path and BFS implementations, and repairs an auxiliary heap function that version 2 leaves defective. Neither version deserves an unconditional claim that every possible bug has been fixed.

This recommendation weighs the assignment's prompting workflow as well as executable correctness. The literal rubric does not explicitly prohibit post-generation corrections, require independent model discovery, or award points for a high raw-generation success rate. Consequently, the evidence does not prove that version 2 will receive a higher numerical grade.

## Scope and fair comparison

Both commits were exported with `git archive` into independent temporary directories. The checked-out branch remained `main`; neither reviewed branch was modified. Their requirement text, starter Python files, and supplied tests are identical.

Checks used the **actual committed ZIPs**, extracted into clean directories. Each ZIP contains exactly the eleven required files, has a valid CRC, matches its branch's `results` files byte for byte, retains original imports and function signatures, and excludes environment/cache/report files.

The common suite combines the 30 supplied cases, version 1's 109 additional cases, and version 2's 109 additional target-function cases. This gives 248 collected pytest cases, including some overlapping coverage. One case tests auxiliary heap functions; the other 247 exercise the ten target functions. Several cases internally enumerate many inputs.

| Fresh check | Version 1 | Version 2 |
|---|---:|---:|
| Supplied tests | 30/30 | 30/30 |
| Common target-function cases, including supplied tests | 247/247 | 247/247 |
| Common auxiliary heap case | 1/1 | 0/1 |
| Common suite total | **248/248** | **247/248** |
| Additional DFS check with set-valued successors | Fails | Passes |
| Notebook code cells executed successfully | 14/14 | 17/17 |
| Final target bodies matching a logged raw completion | 1/10 | 10/10 |
| Required prompting methods present | 4/4 | 4/4 |

Notebook execution ran Python cells sequentially in disposable copies using the existing venv. This was **resume/replay verification**, not a fresh full inference sweep or a Jupyter kernel execution. Both prompt logs and all archive member contents remained byte-identical. Version 1 primarily displays saved results; version 2 also loads the local model, resumes runners, selects candidates, runs tests, and rebuilds/verifies the package.

## Findings

### 1. Version 2 retains a defective BUG001 helper

In `results/final_patches/BUG001.py`, `insert_or_update` retains the starter implementation. Replacing an existing priority does not restore the heap invariant, and equal priorities can force comparison of non-orderable Node objects.

Two independent reproductions confirmed this:

- Starting with `[(1, 'a'), (2, 'b'), (3, 'c')]`, updating `'a'` to priority 8 leaves priority 8 at the root; the next pop returns 8 instead of 2.
- Inserting two distinct Node objects with equal priority raises `TypeError`.

Version 1 fixes both behaviors. **Version 2's repaired `shortest_path_length` does not call either heap helper**: it uses a dictionary frontier. Its target function passes all common shortest-path checks. The helper finding therefore does not establish that BUG001 will fail the private autograder. Direct helper coverage there is unknown.

### 2. Version 1's DFS assumes reversible successor collections

Version 1's BUG006 calls `reversed(node.successors)`. A graph whose successors are sets raises `TypeError: 'set' object is not reversible`. Version 2's `stack.extend(node.successors)` accepts the same graph and returns the correct reachability result.

This is an additional compatibility check, outside the supplied list-based fixtures. The provided Node constructor accepts a successors argument without validating its type, while the problem describes a digraph node without explicitly requiring a list. It is a plausible hidden-input risk, not a demonstrated official-test failure.

### 3. Version 1 scales better on broad graphs

Version 1 uses heap-based Dijkstra and `deque.popleft()` for BFS. Version 2 repeatedly scans a dictionary frontier for its minimum and removes the first element of a list queue. These choices introduce quadratic work on broad sparse graphs.

Measured on this machine, with input construction outside the timer and median of three runs:

| Fixture | Version 1 | Version 2 | Relative time |
|---|---:|---:|---:|
| Dijkstra, 6,000-leaf star, farthest leaf | 2.26 ms | 226.47 ms | About 100 times slower in version 2 |
| BFS, 40,000-leaf star, unreachable goal | 2.22 ms | 97.10 ms | About 44 times slower in version 2 |

Both versions return correct results on these fixtures. The ratios are illustrative local measurements; they do not establish a Gradescope timeout. Version 1 also stops Bellman-Ford early once no distances change; version 2 always performs all scheduled passes.

### 4. Version 2 better preserves the prompt-to-final-code evidence

An independent comparison of executable ASTs, ignoring docstrings and allowing only function-header/body wrapping and uniform indentation shifts, found:

- **Version 1:** BUG000 matches a logged raw model response. The other nine final target bodies do not. Its report and provenance honestly identify assistant corrections.
- **Version 2:** all ten final target bodies match logged raw responses. Its builder reconstructs every final module from the selected response, compares generated/final executable ASTs, and checks tested source hashes.

Version 2 is still **strongly guided generation**. Its assistant-authored plans specify algorithms and Python statements; some prompts supply the complete corrected function body for transcription. This is stronger generation provenance, not evidence that Gemma independently diagnosed or solved the bugs. The report discloses that limitation.

The notebook recommends iterating prompts until generated repairs pass. Version 2 follows that process more closely. Version 1 genuinely used the required model and all four methods, so its later corrections should not be labeled an explicit rubric violation without an instructor rule saying so.

### 5. Both explore all four methods; version 2 explores more representations

Version 1 has 92 complete logged calls: 32 zero-shot and 20 each for one-shot, chain-of-thought, and few-shot. Its primary matrix uses two substantive designs per method per bug. Its examples are related to the particular defect, which is a strength.

Version 2 has 173 records: 172 completed outputs and one explicitly interrupted call. Method counts are 65 zero-shot and 36 each for the other three methods. It explores natural-language, nesting-level, statement, indented-body, and literal-transcription plans, plus feedback and seed retries. Its code-plan worked examples are more generic than version 1's defect-specific examples.

More records alone do not establish better diversity. Both show meaningful within-method variation; version 2 offers broader exploration of input/output representation and failure recovery. Its exact-body plans may also invite a stricter interpretation of what constitutes a repair experiment.

Version 1 reports 0/80 successful primary raw repairs and 1/10 successful failure-guided revisions. Version 2 reports 19/80 successful primary responses after consistent re-evaluation on its finalized suite. These are historical results under different prompts, decoding, extraction, and evaluation procedures; they are not a controlled comparison of model ability or prompting-method superiority.

## Rubric assessment

| Criterion | Version 1 | Version 2 |
|---|---|---|
| Completeness /10 | Evidence supports 10: all four methods and ten replacement modules | Evidence supports 10: same, with stronger final-output traceability |
| Diversity /5 | 3–5 provisionally: meaningful paired designs and related examples | 3–5 provisionally: broader representation/refinement exploration; more convincing case for full credit |
| Test Coverage /10 | Unverified private score; all common target checks pass | Unverified private score; all common target checks pass, but a retained helper fails |

**Conditional planning estimate: 23–25/25 for either version if all private target tests pass and the instructor accepts its workflow.** This is not a guaranteed range or lower bound. The local helper/DFS/performance findings could affect private tests, and prompt diversity is a human judgment. No private autograder run or Gradescope upload was performed.

For a stronger future revision, start with version 2, improve its frontier/queue efficiency, and address helper behavior while retaining truthful new prompt/output/test evidence. Do not silently replace its generated code with version 1's implementations and keep the old provenance claims. This comparison intentionally leaves both reviewed submissions unchanged.

## Evidence and reproduction

Use the existing venv from the repository root:

```bash
assignment/assignment1/.venv/bin/python assignment/assignment1/comparison/compare.py audit
assignment/assignment1/.venv/bin/python assignment/assignment1/comparison/compare.py tests --branch feat-codex-generated-1
assignment/assignment1/.venv/bin/python assignment/assignment1/comparison/compare.py tests --branch feat-codex-generated-2
assignment/assignment1/.venv/bin/python assignment/assignment1/comparison/compare.py focused
assignment/assignment1/.venv/bin/python assignment/assignment1/comparison/compare.py bench
assignment/assignment1/.venv/bin/python assignment/assignment1/comparison/compare.py notebook --branch feat-codex-generated-1
assignment/assignment1/.venv/bin/python assignment/assignment1/comparison/compare.py notebook --branch feat-codex-generated-2
```

`compare.py` re-exports the pinned commits if its temporary snapshots have expired. Evidence beside this report includes `structural_audit.json`, both `*-common-results.json` files and pytest XML/text, `focused_checks.json`, `benchmarks.json`, and both `*-notebook-results.json` files and cell output logs.

Submission archives are under `submissions/<branch>/`. Both are named
`SWE270P_A1.zip` and include the subsequent BUG004 fixes described above.
The lowercase extension is an upload compatibility measure:
Gradescope retained the earlier uppercase archive as a single binary file
instead of expanding its `results/` tree. The hashes below identify the original
reviewed archives; current hashes are recorded in the respective fix evidence.

| Version | Original ZIP SHA256 |
|---|---|
| 1 | `cdbe1ad68df3480ca72c4a7b79350f3503ee66672633fd84b1fff6293f0a5816` |
| 2 | `14b918c50259446a41697a7dcdd5a8eab610dac48d1286b56b2c74164294c0ba` |
