"""Validate completed evidence and package the exact required submission tree."""

import difflib
import hashlib
import json
import xml.etree.ElementTree as ET
from collections import Counter
from zipfile import ZIP_DEFLATED, ZipFile

from prompt_designs import TECHNIQUES
from repair_workflow import MODEL_ID, PATCH_DIR, PROMPTS_PATH, ROOT, validate_interface

REPAIRS = {
    "BUG000": "Use absolute distance between distinct list positions and a strict threshold comparison.",
    "BUG001": "Accumulate the current path distance, track best distances, skip settled nodes, and break heap ties without comparing Node objects. Preserve both original helpers and repair heap updates.",
    "BUG002": "Initialize both endpoints plus the source and relax node distances without changing edge weights.",
    "BUG003": "Create a merged component set and associate every member with it, avoiding mutation during iteration.",
    "BUG004": "Relax directed paths through (i, k) and (k, j), preserving zero-length diagonal paths with positive self edges.",
    "BUG005": "Enqueue the start node, stop on queue exhaustion, and mark nodes when discovered.",
    "BUG006": "Traverse successor lists with a visited set and an explicit DFS stack, including cyclic graphs and long paths.",
    "BUG007": "Advance the previous-node pointer before moving to the saved successor; reverse existing nodes in place.",
    "BUG008": "Move the hare twice and tortoise once, guard both fast-pointer dereferences, and return False for finite/empty lists.",
    "BUG009": "Count two characters per matched pair and combine bounds/content checks with AND before indexing.",
}


def main():
    records = [json.loads(line) for line in PROMPTS_PATH.read_text().splitlines()]
    assert all(record["prompt"].strip() and record.get("completion", "").strip() for record in records)
    assert all(record.get("model") == MODEL_ID for record in records)
    by_id = {record["attempt_id"]: record for record in records if "attempt_id" in record}
    target_records = [record for record in records if "attempt_id" in record]
    assert len(by_id) == len(target_records), "Duplicate experiment IDs."
    expected_ids = {f"BUG{i:03d}_{method}_{variant}" for i in range(10) for method in TECHNIQUES for variant in (1, 2)}
    assert expected_ids <= by_id.keys(), "Incomplete four-method experiment."
    for record in target_records:
        assert record["bug_file"] in {f"BUG{i:03d}.py" for i in range(10)}
    expected_patches = {f"BUG{i:03d}.py" for i in range(10)}
    assert {path.name for path in PATCH_DIR.glob("*.py")} == expected_patches

    final_results = json.loads((ROOT / "experiments/final_tests.json").read_text())
    provenance = {}
    diff_dir = ROOT / "experiments" / "review_diffs"
    diff_dir.mkdir(exist_ok=True)
    for bug, explanation in REPAIRS.items():
        code = (PATCH_DIR / f"{bug}.py").read_text()
        validate_interface(f"{bug}.py", code)
        compile(code, f"{bug}.py", "exec")
        digest = hashlib.sha256(code.encode()).hexdigest()
        assert final_results[bug]["all_passed"]
        assert final_results[bug]["code_sha256"] == digest, "Re-run evaluate.py after changing a final patch."
        baseline_attempt = f"{bug}_zero-shot_1"
        unedited = False
        for record in target_records:
            if record["bug_file"] != f"{bug}.py":
                continue
            candidate = ROOT / "experiments" / "candidates" / f"{record['attempt_id']}.py"
            if candidate.exists() and candidate.read_text() == code:
                baseline_attempt = record["attempt_id"]
                unedited = True
                break
        candidate_path = ROOT / "experiments" / "candidates" / f"{baseline_attempt}.py"
        original_code = candidate_path.read_text() if candidate_path.exists() else (ROOT / "data" / bug / "buggy.py").read_text()
        diff = "".join(difflib.unified_diff(
            original_code.splitlines(keepends=True), code.splitlines(keepends=True),
            fromfile=f"raw_gemma/{baseline_attempt}.py", tofile=f"final_patches/{bug}.py",
        ))
        (diff_dir / f"{bug}.diff").write_text(diff)
        provenance[bug] = {
            "source": "Unedited extracted Gemma output selected after review and tests." if unedited else "Assistant-reviewed implementation after real local Gemma prompting experiments; includes assistant corrections.",
            "raw_comparison_attempt": baseline_attempt,
            "raw_candidate_sha256": hashlib.sha256(original_code.encode()).hexdigest(),
            "final_sha256": digest,
            "repair": explanation,
            "unedited_gemma_output": unedited,
            "review_diff": f"experiments/review_diffs/{bug}.diff",
        }
    (ROOT / "experiments/final_patch_provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")

    assessments = [json.loads(line) for line in (ROOT / "experiments/candidate_evaluations.jsonl").read_text().splitlines()]
    assert {item["attempt_id"] for item in assessments} == expected_ids
    refinements_path = ROOT / "experiments/refinement_evaluations.jsonl"
    refinements = [json.loads(line) for line in refinements_path.read_text().splitlines()] if refinements_path.exists() else []
    robustness = list(ET.parse(ROOT / "experiments/robustness_tests.xml").iter("testcase"))
    assert robustness and all(case.find("failure") is None and case.find("error") is None and case.find("skipped") is None for case in robustness)

    archive_path = ROOT / "SWE270P_A1.ZIP"
    expected_members = {"results/prompts.jsonl"} | {f"results/final_patches/{name}" for name in expected_patches}
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        for relative in sorted(expected_members):
            archive.write(ROOT / relative, arcname=relative)
    with ZipFile(archive_path) as archive:
        assert set(archive.namelist()) == expected_members
        assert archive.testzip() is None
        for relative in expected_members:
            assert archive.read(relative) == (ROOT / relative).read_bytes()

    table = []
    for method in TECHNIQUES:
        group = [item for item in assessments if item["technique"] == method]
        statuses = Counter(item["status"] for item in group)
        table.append(f"| {method} | {len(group)} | {statuses['passed']} | {statuses['failed']} | {statuses['extraction_failed']} |")
    baseline = json.loads((ROOT / "experiments/baseline_tests.json").read_text())
    baseline_passed = sum(item["passed"] for item in baseline.values())
    refinement_passed = sum(item["status"] == "passed" for item in refinements)
    environment = json.loads((ROOT / "experiments/environment.json").read_text())
    revision = environment["model_revision"]
    unedited_bugs = [bug for bug, item in provenance.items() if item["unedited_gemma_output"]]
    review_rechecks = sum(record.get("purpose") == "review-reproducibility" for record in records)
    report = f'''# Assignment 1: Prompting for Program Repair

## Completed submission

`SWE270P_A1.ZIP` contains exactly `results/prompts.jsonl` and the ten complete replacement modules under `results/final_patches/BUG000.py` through `BUG009.py`. The archive has the required top-level `results` directory. Original starter code and supplied tests are preserved.

## Environment and inference

- Python {environment['python']} in `assignment/assignment1/.venv`.
- Required model: [`{MODEL_ID}`](https://huggingface.co/google/gemma-3-270m-it), revision `{revision}`.
- Local Transformers inference on CPU using float32, with cached model weights and no inference API.
- Deterministic greedy decoding. Primary attempts use at most 768 new tokens; failure-guided revisions use at most 1024. Only generated tokens are decoded after applying the chat template.
- Package versions and model details: `requirements.txt` and `experiments/environment.json`.

## Prompt design

Every bug received two designs for each required method: 80 primary attempts. Zero-shot designs compare a behavioral-contract request with a maintainer review emphasizing boundaries and mutation. One-shot designs use different single worked repairs selected for each bug. Chain-of-thought designs request a brief high-level invariant summary or a counterexample-based repair summary before code. Few-shot designs compare two related worked repairs with three complementary repair reviews.

After observing failed tests, ten additional zero-shot revisions give precise edit instructions and shorter input modules. The initial model smoke test is also logged. There are {len(records)} actual prompt/completion records in total. No synthetic or edited completion is attributed to Gemma. The notebook replays these saved records; the runners perform new inference.

Later review reproducibility checks: {review_rechecks}. These repeat existing prompts and are not counted as additional primary designs.

## Raw model results

The table evaluates extracted raw Gemma responses using the three unchanged supplied tests per bug. A successful attempt must pass all three tests and retain every original public function signature, including BUG001's helpers. Extraction failures contain no complete parseable function. Timeouts and missing/changed interfaces count as unsuccessful attempts.

| Method | Attempts | All tests + interface | Failed | Extraction failed |
|---|---:|---:|---:|---:|
{chr(10).join(table)}

Failure-guided revisions: {refinement_passed}/{len(refinements)} passed the supplied tests and interface check. The detailed outcomes, including failures and any timeouts, are in `experiments/candidate_evaluations.jsonl` and `experiments/refinement_evaluations.jsonl`.

In this run, the small model frequently copied defective code instead of applying the requested repair. More elaborate prompts alone did not reliably produce correct algorithms. These observations apply to this model, deterministic decoding, and these prompt designs; they do not establish a general ranking of prompting methods. A response that looks like valid Python still requires testing.

## Final repair review

The final patches were reviewed after the Gemma experiments. {', '.join(unedited_bugs) or 'None'} uses an unedited extracted Gemma response; the other patches include assistant corrections. `experiments/final_patch_provenance.json` records each final file hash, the repair, and a diff against a raw candidate. The original imports and public function parameters are retained, and every final file is a complete replacement module.

| Bug | Reviewed repair |
|---|---|
{chr(10).join(f'| {bug} | {explanation} |' for bug, explanation in REPAIRS.items())}

## Validation

- Original baseline: {baseline_passed}/30 supplied tests passed.
- Final patches: 30/30 supplied tests passed, including all three tests for each of the ten bugs. `evaluate.py` copies unchanged tests and node definitions to temporary directories and replaces only the implementation being evaluated.
- Additional robustness suite: {len(robustness)} pytest cases passed. Several cases contain exhaustive or randomized checks, so the number of input combinations exceeds the pytest case count.
- Coverage includes strict distance boundaries and input preservation; Dijkstra priority ties, fractional weights, decreased priorities, and random directed graphs; negative DAGs and endpoint-only nodes; exhaustive spanning-tree comparisons and tied weights with unorderable vertex labels; directed all-pairs distances and positive self-loops; legal negative-edge cyclic graphs checked against exhaustive simple-path enumeration; every three-node directed graph for BFS/DFS; 2500-node paths and cycles; linked-list identity and reversal round trips; all cycle entry positions for lists up to ten nodes; all 2047 parentheses strings of length 0 through 10; and long parentheses inputs.
- Evidence: `experiments/baseline_tests.json`, `experiments/final_tests.json`, and `experiments/robustness_tests.xml`.
- Packaging checks verify exactly eleven archive files, correct member paths, valid Python, preserved signatures, prompt coverage, and matching tested source hashes.

The private Gradescope tests are unavailable locally. Passing the local tests does not guarantee a particular autograder score. No submission to Gradescope has been made.
'''
    (ROOT / "REPORT.md").write_text(report)
    print(f"Created {archive_path}")
    print(f"Archive verified: {len(expected_members)} files; {len(records)} prompt records; 10 complete patches.")


if __name__ == "__main__":
    main()
