# Assignment 1: Prompting for Program Repair

The assignment, prompts, notebook, and report are in English. The upload is **`SWE270P_A1.ZIP`** in this directory. Read `REPORT.md` for the experiment results and the limits of the model's role.

All ten final target implementations come from actual local Gemma responses. The assistant supplied detailed repair plans, including corrected body statements in some prompts. Model outputs were selected by tests; their executable statements were not manually repaired after generation. `experiments/provenance.json` records the source attempt and matching raw/final executable AST fingerprints.

## Environment

Run commands from `assignment/assignment1/SWE270P_A1`:

```bash
source ../.venv/bin/activate
python --version
```

The completed run uses the existing Python 3.12 venv. For a new environment, use `python3.12 -m venv ../.venv`, then `../.venv/bin/python -m pip install -r requirements.txt`.

The required model is [`google/gemma-3-270m-it`](https://huggingface.co/google/gemma-3-270m-it). Accept access on the model page, authenticate locally, and cache its files before running on a fresh machine. The existing environment already has the model. No access token is included in this project. Inference uses local CPU float32, temperature 1.0, top-p 0.95, top-k 50, and recorded random seeds.

## Execute the completed notebook

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python execute_notebook.py
```

This executes all Python code cells sequentially in the venv, writes real cell outputs, and saves `experiments/notebook_execution.json`. It does not start a Jupyter server. You can also open `A1_instruction.ipynb` in Jupyter and select the assignment's venv kernel.

The notebook executes a resumable workflow, not a mock inference function. Completed attempt IDs reuse actual saved responses and test results. A fresh copy without generated `results/` and `experiments/` runs new model inference. The notebook runs all four methods, selects tested generations, retries missing repairs with more precise plans and new seeds, compares saved outputs using the finalized tests, and packages/verifies the upload.

## Individual workflow commands

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python run_experiments.py --format code-plan
python select_candidates.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python run_experiments.py --phase refinement --format literal-plan --attempts 24 --round 1
python reevaluate_matrix.py
python evaluate.py
python -m pytest tests -q --junitxml=experiments/additional_tests.xml
python build_submission.py
python verify_submission.py
```

`--method zero-shot` (or another required method) restricts a primary run to that method. `--bug BUG001` restricts a run to one bug. If a fresh run needs more retries, use another refinement `--round` with new seeds; the notebook does this automatically for missing repairs. No failed candidate is silently repaired or substituted with a hand-written solution.

## Files and evidence

| File | Purpose |
|---|---|
| `workflow.py` | Required model inference, append-only raw logging, extraction, original-scaffold assembly, and patch saving. |
| `prompt_designs.py` | English contracts, natural-language repair plans, counterexamples, and worked examples. |
| `structured_plans.py` | Explicit control-flow plans and body/function output formats. These are assistant-authored guidance. |
| `run_experiments.py` | Real sampled inference, test feedback, seed retries, and first-passing-candidate selection. |
| `select_candidates.py` | Adopts passing exploratory responses and records their provenance without editing logic. |
| `reevaluate_matrix.py` | Evaluates all 80 primary responses against the same finalized test suite. |
| `evaluate.py` | Tests final modules with unchanged supplied tests and additional cases in temporary directories. |
| `tests/test_repairs.py` | 109 additional target-function cases, including exhaustive and randomized oracle checks. |
| `tests/test_workflow.py` | Six assembly/provenance checks. |
| `build_submission.py` | Reconstructs every final file from its response, verifies tested hashes, and builds the required ZIP. |
| `verify_submission.py` | Extracts and tests the actual ZIP, then records `experiments/submission_audit.json`. |
| `experiments/provenance.json` | The exact logged source, seed, hashes, and unchanged executable AST proof for every final repair. |
| `experiments/final_matrix_evaluations.jsonl` | Consistent final comparison of the 80 primary raw responses. |
| `experiments/submission_tests.xml` | All 139 target-function tests passed against files extracted from the ZIP. |

All attempted prompts are in `results/prompts.jsonl`, including completed exploratory failures and one explicitly interrupted call with no fabricated completion. Initial exploratory outcomes and the later consistent comparison are kept separately. Original starter files under `data/` remain the baseline; final repairs are under `results/final_patches/`.

## Upload format

```text
SWE270P_A1.ZIP
└── results
    ├── prompts.jsonl
    └── final_patches
        ├── BUG000.py
        ├── ...
        └── BUG009.py
```

The archive contains exactly these eleven files. It excludes the venv, reports, tests, and cache files. No Gradescope upload or private autograder run has been performed.
