# Assignment 1: Prompting for Program Repair

## Completed submission

`SWE270P_A1.ZIP` contains exactly `results/prompts.jsonl` and the ten complete replacement modules under `results/final_patches/BUG000.py` through `BUG009.py`. The archive has the required top-level `results` directory. Original starter code and supplied tests are preserved.

## Environment and inference

- Python 3.12.14 in `assignment/assignment1/.venv`.
- Required model: [`google/gemma-3-270m-it`](https://huggingface.co/google/gemma-3-270m-it), revision `ac82b4e820549b854eebf28ce6dedaf9fdfa17b3`.
- Local Transformers inference on CPU using float32, with cached model weights and no inference API.
- Deterministic greedy decoding. Primary attempts use at most 768 new tokens; failure-guided revisions use at most 1024. Only generated tokens are decoded after applying the chat template.
- Package versions and model details: `requirements.txt` and `experiments/environment.json`.

## Prompt design

Every bug received two designs for each required method: 80 primary attempts. Zero-shot designs compare a behavioral-contract request with a maintainer review emphasizing boundaries and mutation. One-shot designs use different single worked repairs selected for each bug. Chain-of-thought designs request a brief high-level invariant summary or a counterexample-based repair summary before code. Few-shot designs compare two related worked repairs with three complementary repair reviews.

After observing failed tests, ten additional zero-shot revisions give precise edit instructions and shorter input modules. The initial model smoke test is also logged. There are 92 actual prompt/completion records in total. No synthetic or edited completion is attributed to Gemma. The notebook replays these saved records; the runners perform new inference.

Later review reproducibility checks: 1. These repeat existing prompts and are not counted as additional primary designs.

## Raw model results

The table evaluates extracted raw Gemma responses using the three unchanged supplied tests per bug. A successful attempt must pass all three tests and retain every original public function signature, including BUG001's helpers. Extraction failures contain no complete parseable function. Timeouts and missing/changed interfaces count as unsuccessful attempts.

| Method | Attempts | All tests + interface | Failed | Extraction failed |
|---|---:|---:|---:|---:|
| zero-shot | 20 | 0 | 19 | 1 |
| one-shot | 20 | 0 | 20 | 0 |
| chain-of-thought | 20 | 0 | 19 | 1 |
| few-shot | 20 | 0 | 20 | 0 |

Failure-guided revisions: 1/10 passed the supplied tests and interface check. The detailed outcomes, including failures and any timeouts, are in `experiments/candidate_evaluations.jsonl` and `experiments/refinement_evaluations.jsonl`.

In this run, the small model frequently copied defective code instead of applying the requested repair. More elaborate prompts alone did not reliably produce correct algorithms. These observations apply to this model, deterministic decoding, and these prompt designs; they do not establish a general ranking of prompting methods. A response that looks like valid Python still requires testing.

## Final repair review

The final patches were reviewed after the Gemma experiments. BUG000 uses an unedited extracted Gemma response; the other patches include assistant corrections. `experiments/final_patch_provenance.json` records each final file hash, the repair, and a diff against a raw candidate. The original imports and public function parameters are retained, and every final file is a complete replacement module.

| Bug | Reviewed repair |
|---|---|
| BUG000 | Use absolute distance between distinct list positions and a strict threshold comparison. |
| BUG001 | Accumulate the current path distance, track best distances, skip settled nodes, and break heap ties without comparing Node objects. Preserve both original helpers and repair heap updates. |
| BUG002 | Initialize both endpoints plus the source and relax node distances without changing edge weights. |
| BUG003 | Create a merged component set and associate every member with it, avoiding mutation during iteration. |
| BUG004 | Relax directed paths through (i, k) and (k, j), preserving zero-length diagonal paths with positive self edges. |
| BUG005 | Enqueue the start node, stop on queue exhaustion, and mark nodes when discovered. |
| BUG006 | Traverse successor lists with a visited set and an explicit DFS stack, including cyclic graphs and long paths. |
| BUG007 | Advance the previous-node pointer before moving to the saved successor; reverse existing nodes in place. |
| BUG008 | Move the hare twice and tortoise once, guard both fast-pointer dereferences, and return False for finite/empty lists. |
| BUG009 | Count two characters per matched pair and combine bounds/content checks with AND before indexing. |

## Validation

- Original baseline: 8/30 supplied tests passed.
- Final patches: 30/30 supplied tests passed, including all three tests for each of the ten bugs. `evaluate.py` copies unchanged tests and node definitions to temporary directories and replaces only the implementation being evaluated.
- Additional robustness suite: 109 pytest cases passed. Several cases contain exhaustive or randomized checks, so the number of input combinations exceeds the pytest case count.
- Coverage includes strict distance boundaries and input preservation; Dijkstra priority ties, fractional weights, decreased priorities, and random directed graphs; negative DAGs and endpoint-only nodes; exhaustive spanning-tree comparisons and tied weights with unorderable vertex labels; directed all-pairs distances and positive self-loops; legal negative-edge cyclic graphs checked against exhaustive simple-path enumeration; every three-node directed graph for BFS/DFS; 2500-node paths and cycles; linked-list identity and reversal round trips; all cycle entry positions for lists up to ten nodes; all 2047 parentheses strings of length 0 through 10; and long parentheses inputs.
- Evidence: `experiments/baseline_tests.json`, `experiments/final_tests.json`, and `experiments/robustness_tests.xml`.
- Packaging checks verify exactly eleven archive files, correct member paths, valid Python, preserved signatures, prompt coverage, and matching tested source hashes.

The private Gradescope tests are unavailable locally. Passing the local tests does not guarantee a particular autograder score. No submission to Gradescope has been made.
