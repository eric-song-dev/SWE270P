"""Evaluate replacement modules against unchanged supplied tests in a temp tree."""

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

from repair_workflow import ROOT


def evaluate_patch(bug, code, timeout=8):
    """Return genuine pytest results without editing the original data directory."""
    with tempfile.TemporaryDirectory(prefix="swe270p-a1-") as temp:
        directory = Path(temp) / bug
        shutil.copytree(
            ROOT / "data" / bug, directory,
            ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"),
        )
        (directory / "buggy.py").write_text(code, encoding="utf-8")
        report = Path(temp) / "pytest.xml"
        command = [
            sys.executable, "-m", "pytest", str(directory / "test_bug.py"),
            "-q", "--tb=short", f"--junitxml={report}",
        ]
        try:
            result = subprocess.run(command, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            return {"passed": 0, "failed": 0, "errors": 0, "timeout": True, "all_passed": False}
        counts = {"passed": 0, "failed": 0, "errors": 0, "skipped": 0}
        if report.exists():
            for case in ET.parse(report).iter("testcase"):
                if case.find("failure") is not None:
                    counts["failed"] += 1
                elif case.find("error") is not None:
                    counts["errors"] += 1
                elif case.find("skipped") is not None:
                    counts["skipped"] += 1
                else:
                    counts["passed"] += 1
        return {
            **counts,
            "returncode": result.returncode,
            "timeout": False,
            "all_passed": result.returncode == 0 and counts["passed"] == 3,
            "output": result.stdout + result.stderr,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", action="store_true")
    args = parser.parse_args()
    summary = {}
    for i in range(10):
        bug = f"BUG{i:03d}"
        path = ROOT / "data" / bug / "buggy.py" if args.baseline else ROOT / "results" / "final_patches" / f"{bug}.py"
        code = path.read_text()
        result = evaluate_patch(bug, code)
        result["code_sha256"] = hashlib.sha256(code.encode()).hexdigest()
        summary[bug] = result
        print(f"{bug}: {result['passed']} passed, {result['failed']} failed, {result['errors']} errors")
    destination = ROOT / "experiments" / ("baseline_tests.json" if args.baseline else "final_tests.json")
    destination.parent.mkdir(exist_ok=True)
    destination.write_text(json.dumps(summary, indent=2) + "\n")
    if not args.baseline and not all(result["all_passed"] for result in summary.values()):
        sys.exit(1)


if __name__ == "__main__":
    main()
