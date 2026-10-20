# Assignment 1: Prompting for Program Repair

## Result

All ten final target functions were emitted by the required local `google/gemma-3-270m-it` model and selected only after passing the supplied and additional tests. The final executable statements were not manually repaired after generation. The upload is `SWE270P_A1.ZIP`, with exactly the required eleven files under `results/`.

## Environment

Python 3.12.14 in `../.venv`; local CPU float32 inference through Hugging Face Transformers; model snapshot `ac82b4e820549b854eebf28ce6dedaf9fdfa17b3`. Sampling uses temperature 1.0, top-p 0.95, top-k 50, recorded seeds, and at most 768 newly generated tokens. The chat template is applied and only new tokens are decoded. No external inference API is used. Exact package versions are in `requirements.txt` and `experiments/environment.json`.

## Prompting experiment

The complete primary matrix contains 80 calls: ten bugs, all four required methods, and two designs per method. Additional pilots and feedback-based retries are also retained. The append-only prompt log currently contains 173 records; 1 interrupted call is explicitly marked without an invented completion.

- Zero-shot: implementation from a contract/plan, or a maintainer checklist with acceptance checks; no worked examples of other tasks.
- One-shot: one worked loop-completion example or one worked guard/pointer example before the target.
- Chain-of-thought: request a brief high-level invariant/return-placement summary or boundary/counterexample summary before code. The model sometimes ignored the summary request; raw output is retained unchanged.
- Few-shot: multiple worked examples for counting, loop completion, and pointer state; variations include two or three examples and body-versus-function output formats.

The primary free-sampling outcomes below count a candidate as successful only if its complete assembled module passed every supplied and additional test for that bug. Rejections include invalid syntax, changed interfaces, wrong/example functions, unexpected top-level execution, and malformed nesting. Failures and timeouts remain in the experiment evidence.

All 80 saved primary responses were re-evaluated with the same finalized test suite, including mixed/None node labels. `experiments/final_matrix_evaluations.jsonl` records that consistent comparison and the test-suite hash; initial historical assessments are retained separately.

These counts are descriptive rather than a controlled ranking: some prompts include feedback from earlier candidates, and each design has one primary sampled response.

| Method | Primary attempts | Passed all local tests | Unsuccessful |
|---|---:|---:|---:|
| zero-shot | 20 | 6 | 14 |
| one-shot | 20 | 3 | 17 |
| chain-of-thought | 20 | 8 | 12 |
| few-shot | 20 | 2 | 18 |

## What improved the results

Natural-language plans and explicit nesting labels often still produced wrong attributes, omitted loops, or incorrect return placement. More explicit statement-level plans, code-body formatting, sampling with different seeds, and feedback from actual test failures produced passing outputs. An earlier natural-language sweep was interrupted when changing strategy; its completed calls and interrupted call remain recorded.

This is **strongly guided code generation**. The assistant analyzed the bugs and authored the repair algorithms, including explicit Python expressions and control-flow plans. Some prompts supply the complete corrected body as a plan for transcription. Gemma is responsible for emitting the selected implementation; this experiment does not claim that the 270M model independently discovered the bugs or algorithms. No constrained-token decoding or forced completion was used.

## Assembly and provenance

The assembler restores the original module around the emitted target function. Original imports, auxiliary functions, function signatures, and documentation are retained. An emitted body may receive the unchanged original function header and a uniform indentation shift; relative indentation and executable statements are preserved. Original docstrings may be restored. Invalid logical nesting is rejected rather than repaired. Extra imports/helpers are included only if the model emitted them.

Every final file must be exactly reconstructible from its logged raw completion. `experiments/provenance.json` stores the source attempt, seed, response/module hashes, matching generated/final executable AST hashes, and test result for all ten bugs. The package builder rejects edited code or stale test evidence. The original `data/` files and supplied tests remain the experiment baseline.

BUG001 uses Dijkstra with a dictionary frontier and compares tentative distances rather than Node objects; its original heap helpers remain included and are not called by the repaired target. BUG005 uses a list queue, which matches the generated `pop(0)` operation. Some original imports therefore remain unused as part of the preserved module scaffold.

| Bug | Selected method | Raw attempt | Tests passed |
|---|---|---|---:|
| BUG000 | chain-of-thought | `BUG000_chain-of-thought_v2_code-plan_primary` | 10 |
| BUG001 | zero-shot | `BUG001_indented_probe_2` | 6 |
| BUG002 | zero-shot | `BUG002_zero-shot_v1_code-plan_primary` | 7 |
| BUG003 | chain-of-thought | `BUG003_chain-of-thought_v1_code-plan_primary` | 6 |
| BUG004 | zero-shot | `BUG004_literal_probe_3` | 7 |
| BUG005 | zero-shot | `BUG005_zero-shot_literal-plan_r1_1` | 5 |
| BUG006 | chain-of-thought | `BUG006_chain-of-thought_v1_code-plan_primary` | 5 |
| BUG007 | zero-shot | `BUG007_zero-shot_v1_code-plan_primary` | 8 |
| BUG008 | zero-shot | `BUG008_zero-shot_literal-plan_r1_1` | 69 |
| BUG009 | zero-shot | `BUG009_zero-shot_v1_code-plan_primary` | 16 |

## Validation

Original baseline: 8/30 supplied tests passed. Final selected modules: **139 local target-function test cases passed**, including all 30 supplied tests and 109 additional cases. The extra suite covers strict fractional distance boundaries, shortest-path ties and priority improvements, exhaustive simple-path oracles, negative-edge graphs with no negative cycles, exhaustive small spanning trees, all 512 three-node directed graphs, long searches, linked-list identities and every small cycle entry, exhaustive parentheses strings through length ten, and long/mixed inputs. Six additional assembly tests check that generated logic is preserved and malformed output is rejected.

`evaluate.py` tests temporary copies containing unchanged supplied tests. `verify_submission.py` independently extracts the actual ZIP, verifies provenance, runs supplied and extra tests against those extracted patches, and validates the exact archive tree. The completed notebook runs the workflow with resume semantics: completed attempt IDs reuse real saved results; on a fresh output directory the same cells call the local model and log new attempts.

The private Gradescope tests are not available locally, so a score cannot be guaranteed. No Gradescope upload has been performed.

## Rubric alignment

| Criterion | Submission evidence |
|---|---|
| Completeness (10 points) | All four required methods are present in the actual prompt log; all ten complete replacement modules are included and trace to model outputs. |
| Diversity of Prompts (5 points) | Contract/checklist and counterexample framing, different worked examples, two/three-example designs, natural-language/nesting/statement plans, body/function output formats, and feedback-based retries are represented in the real calls. This category remains a reviewer judgment. |
| Test Coverage (10 points) | All 30 supplied and 109 additional local target checks pass. Official credit depends on the private Gradescope tests. |
