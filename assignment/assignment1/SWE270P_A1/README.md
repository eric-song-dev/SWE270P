# Assignment 1

The work and documentation are in English. Open `REPORT.md` for the experiment comparison, repair notes, and validation results. The submission artifact is `SWE270P_A1.ZIP` in this directory.

## Use the virtual environment

From `assignment/assignment1/SWE270P_A1`:

```bash
source ../.venv/bin/activate
python --version
```

The completed run uses the existing Python 3.12 venv. To create a fresh environment, run `python3.12 -m venv ../.venv`, then `../.venv/bin/python -m pip install -r requirements.txt`.

The required Gemma model must be cached before inference. On a fresh machine, accept the terms on the [official model page](https://huggingface.co/google/gemma-3-270m-it), run `hf auth login` locally, and download with `hf download google/gemma-3-270m-it`. No access token is included in the project.

## Reproduce experiments

```bash
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python run_experiments.py
HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 python run_refinements.py
```

Completed attempt IDs are skipped. The primary runner covers all ten bugs with two designs per each of the four required methods. The refinement runner uses observed failures to request precise edits. Raw completions are appended to `results/prompts.jsonl` before extraction or tests. Candidate code and assessments are saved under `experiments/`.

`repair_workflow.py` implements local inference, prompt logging, code extraction, interface validation, and final-patch saving. `prompt_designs.py` contains the English prompt designs. `A1_instruction.ipynb` is completed and replays actual recorded attempts; replaying it does not generate duplicate prompts.

## Verify and package

```bash
python evaluate.py --baseline
python evaluate.py
python -m pytest tests -q --junitxml=experiments/robustness_tests.xml
python build_submission.py
```

The baseline command intentionally reports failures in the untouched starter code. Final-patch evaluation tests temporary copies with the original supplied tests. Additional tests load the files in `results/final_patches` directly. The package builder validates the evidence and creates only the required submission tree:

```text
SWE270P_A1.ZIP
└── results
    ├── prompts.jsonl
    └── final_patches
        ├── BUG000.py
        ├── ...
        └── BUG009.py
```

The final files contain assistant-reviewed corrections following the Gemma experiments. Raw model outcomes and final reviewed results are documented separately in `REPORT.md` and `experiments/final_patch_provenance.json`.

## Review the actual upload

```bash
python review_submission.py
```

This validates the ZIP, extracts it to a temporary directory, runs the supplied and additional tests against the extracted patches, and executes all notebook code cells. Evidence is saved in `experiments/review_audit.json` and `experiments/review_archive_tests.xml`. See `REVIEW.md` for the English code review, provisional rubric assessment, and the question about acceptance of post-generation corrections.
