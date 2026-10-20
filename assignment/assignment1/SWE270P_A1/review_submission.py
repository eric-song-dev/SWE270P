"""Audit the submitted ZIP, then test its extracted modules and replay the notebook."""

import ast
import contextlib
import datetime as dt
import hashlib
import io
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

import nbformat

from prompt_designs import TECHNIQUES, make_prompt
from repair_workflow import MODEL_ID, ROOT, validate_interface


def main():
    assert sys.prefix != sys.base_prefix, "Run this audit with the assignment venv."
    expected_members = {"results/prompts.jsonl"} | {
        f"results/final_patches/BUG{i:03d}.py" for i in range(10)
    }
    archive_path = ROOT / "SWE270P_A1.ZIP"
    with ZipFile(archive_path) as archive:
        assert len(archive.namelist()) == len(expected_members)
        assert set(archive.namelist()) == expected_members
        assert archive.testzip() is None
        for member in expected_members:
            assert archive.read(member) == (ROOT / member).read_bytes(), member
        records = [json.loads(line) for line in archive.read("results/prompts.jsonl").decode().splitlines()]
        by_id = {r["attempt_id"]: r for r in records if "attempt_id" in r}
        assert len(by_id) == sum("attempt_id" in r for r in records)
        assert all(r["model"] == MODEL_ID and r["prompt"].strip() and r["completion"].strip() for r in records)
        expected_examples = {"zero-shot": (0, 0), "one-shot": (1, 1), "chain-of-thought": (0, 0), "few-shot": (2, 3)}
        for i in range(10):
            bug = f"BUG{i:03d}"
            code = archive.read(f"results/final_patches/{bug}.py").decode()
            validate_interface(f"{bug}.py", code)
            compile(code, f"{bug}.py", "exec")
            original = ast.parse((ROOT / "data" / bug / "buggy.py").read_text())
            required_imports = {ast.dump(n) for n in original.body if isinstance(n, (ast.Import, ast.ImportFrom))}
            actual_imports = {ast.dump(n) for n in ast.parse(code).body if isinstance(n, (ast.Import, ast.ImportFrom))}
            assert required_imports <= actual_imports
            for method in TECHNIQUES:
                prompts = []
                for variant in range(2):
                    record = by_id[f"{bug}_{method}_{variant + 1}"]
                    assert record["technique"] == method
                    assert record["bug_file"] == f"{bug}.py"
                    assert record["prompt"] == make_prompt(bug, method, variant)
                    assert record["prompt"].count("Worked repair ") == expected_examples[method][variant]
                    prompts.append(record["prompt"])
                assert prompts[0] != prompts[1]

        # Only the checked submission members are extracted; tests load these copies.
        with tempfile.TemporaryDirectory(prefix="swe270p-a1-review-") as temp:
            temporary = Path(temp)
            archive.extractall(temporary)
            ignore = shutil.ignore_patterns("__pycache__", ".pytest_cache", ".DS_Store")
            shutil.copytree(ROOT / "data", temporary / "supplied", ignore=ignore)
            for i in range(10):
                bug = f"BUG{i:03d}"
                shutil.copyfile(
                    temporary / "results" / "final_patches" / f"{bug}.py",
                    temporary / "supplied" / bug / "buggy.py",
                )
            shutil.copytree(ROOT / "tests", temporary / "tests", ignore=ignore)
            config = temporary / "pytest.ini"
            config.write_text("[pytest]\n")
            xml_path = ROOT / "experiments" / "review_archive_tests.xml"
            result = subprocess.run(
                [sys.executable, "-m", "pytest", "supplied", "tests", "-q", "--tb=short", "-c", str(config), f"--junitxml={xml_path}"],
                cwd=temporary, capture_output=True, text=True, timeout=60,
            )
            print(result.stdout, end="")
            if result.returncode:
                print(result.stderr)
                raise RuntimeError("Tests on the extracted submission archive failed.")
            cases = list(ET.parse(xml_path).iter("testcase"))
            assert all(c.find("failure") is None and c.find("error") is None and c.find("skipped") is None for c in cases)

    notebook_path = ROOT / "A1_instruction.ipynb"
    notebook = nbformat.read(notebook_path, as_version=4)
    nbformat.validate(notebook)
    namespace = {"__name__": "__notebook_review__"}
    cell_count = 0
    for index, cell in enumerate(notebook.cells):
        if cell.cell_type != "code":
            continue
        cell_count += 1
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            exec(compile(cell.source, f"{notebook_path.name}:cell-{index}", "exec"), namespace)
        cell.execution_count = cell_count
        cell.outputs = []
        for name, stream in (("stdout", stdout), ("stderr", stderr)):
            if stream.getvalue():
                cell.outputs.append(nbformat.v4.new_output("stream", name=name, text=stream.getvalue()))
    execution = {
        "method": "Sequential execution of every code cell in the assignment venv",
        "python": sys.executable,
        "code_cells_executed": cell_count,
        "status": "passed",
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    notebook.metadata["execution"] = execution
    nbformat.validate(notebook)
    nbformat.write(notebook, notebook_path)
    (ROOT / "experiments/notebook_execution.json").write_text(json.dumps(execution, indent=2) + "\n")
    supplied_counts = {
        f"BUG{i:03d}": sum(f".BUG{i:03d}." in f".{c.attrib.get('classname', '')}." for c in cases)
        for i in range(10)
    }
    assert all(count == 3 for count in supplied_counts.values())
    audit = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(),
        "python": sys.executable,
        "archive_sha256": hashlib.sha256(archive_path.read_bytes()).hexdigest(),
        "archive_files": len(expected_members),
        "prompt_records": len(records),
        "prompt_methods": dict(Counter(r["technique"] for r in records)),
        "primary_prompt_designs_verified": 80,
        "signatures_imports_and_archive_contents": "passed",
        "supplied_tests_passed_by_bug": supplied_counts,
        "additional_cases_passed_on_extracted_archive": len(cases) - 30,
        "total_archive_test_cases_passed": len(cases),
        "notebook_code_cells_executed": cell_count,
        "status": "passed",
        "scope": "Local checks only; private Gradescope tests and instructor policy interpretation are not verified.",
    }
    (ROOT / "experiments/review_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(f"Archive review passed: {len(cases)} tests, {len(records)} prompt records, {cell_count} notebook code cells.")


if __name__ == "__main__":
    main()
