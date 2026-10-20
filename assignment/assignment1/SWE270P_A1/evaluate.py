"""Test a model-generated complete replacement against untouched and extra tests."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from workflow import ROOT, sha256


def evaluate_patch(bug, code, timeout=8):
    with tempfile.TemporaryDirectory(prefix="swe270p-gemma-") as temp:
        directory = Path(temp)
        shutil.copytree(ROOT / "data" / bug, directory / bug, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
        (directory / bug / "buggy.py").write_text(code)
        patches = directory / "patches"
        patches.mkdir()
        (patches / f"{bug}.py").write_text(code)
        xml_path = directory / "tests.xml"
        environment = os.environ.copy()
        environment["PATCH_DIR"] = str(patches)
        command = [sys.executable,"-m","pytest",str(directory/bug/"test_bug.py"),str(ROOT/"tests/test_repairs.py"),"-k",bug,"-q","--tb=short",f"--junitxml={xml_path}"]
        try:
            result = subprocess.run(command,env=environment,capture_output=True,text=True,timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"status":"timeout","all_passed":False,"passed":0,"failed":0,"errors":0,"code_sha256":sha256(code)}
        cases = list(ET.parse(xml_path).iter("testcase")) if xml_path.exists() else []
        failed = sum(c.find("failure") is not None for c in cases)
        errors = sum(c.find("error") is not None for c in cases)
        skipped = sum(c.find("skipped") is not None for c in cases)
        passed = len(cases)-failed-errors-skipped
        all_passed = result.returncode==0 and passed>=5 and not(failed or errors or skipped)
        return {
            "status":"passed" if all_passed else "failed", "all_passed":all_passed,
            "passed":passed,"failed":failed,"errors":errors,"skipped":skipped,
            "code_sha256":sha256(code),"returncode":result.returncode,
            "failure_messages":[(c.find("failure") if c.find("failure") is not None else c.find("error")).attrib.get("message", "")[:300] for c in cases if c.find("failure") is not None or c.find("error") is not None][:4],
            "output":result.stdout+result.stderr,
        }


def main():
    results = {}
    for i in range(10):
        bug = f"BUG{i:03d}"
        results[bug] = evaluate_patch(bug,(ROOT/"results/final_patches"/f"{bug}.py").read_text())
        print(bug,results[bug]["status"],results[bug]["passed"],"passed",flush=True)
    (ROOT/"experiments/final_tests.json").write_text(json.dumps(results,indent=2)+"\n")
    assert all(r["all_passed"] for r in results.values())


if __name__ == "__main__":
    main()
