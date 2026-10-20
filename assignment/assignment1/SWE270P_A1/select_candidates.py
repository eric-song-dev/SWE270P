"""Adopt passing logged generations, never hand-written or edited replacements."""

import json
from pathlib import Path

from evaluate import evaluate_patch
from workflow import MODEL_ID, PROMPTS_PATH, ROOT, assemble_patch, sha256


def main():
    directory = ROOT / "experiments"
    records = [json.loads(line) for line in PROMPTS_PATH.read_text().splitlines()]
    assessments = {}
    for path in [directory/"attempts.jsonl",directory/"recovered_evaluations.jsonl",*directory.glob("*probe/assessments.jsonl")]:
        if path.exists():
            for line in path.read_text().splitlines():
                rec=json.loads(line)
                assessments[rec["attempt_id"]]=rec
    # The first pilot exposed an assembly utility error, not a successful repair.
    # Assess its actual saved responses now, retaining all original raw outputs.
    for record in records:
        if record["attempt_id"] in assessments:
            continue
        rec={"attempt_id":record["attempt_id"],"bug":record["bug_file"][:-3],"phase":record.get("phase")}
        if not record.get("completion"):
            rec["status"]="interrupted"
        else:
            try:
                final=assemble_patch(rec["bug"],record["completion"])
                rec["tests"]=evaluate_patch(rec["bug"],final)
                rec["status"]=rec["tests"]["status"]
            except (ValueError,SyntaxError) as error:
                rec.update(status="rejected",error=str(error))
        with (directory/"recovered_evaluations.jsonl").open("a") as stream:
            stream.write(json.dumps(rec)+"\n")
        assessments[rec["attempt_id"]]=rec
    path=directory/"selected.json"
    selected=json.loads(path.read_text()) if path.exists() else {}
    for record in records:
        bug=record["bug_file"][:-3]
        if bug in selected or assessments[record["attempt_id"]]["status"]!="passed":
            continue
        final=assemble_patch(bug,record["completion"])
        result=evaluate_patch(bug,final)
        if not result["all_passed"]:
            continue
        (ROOT/"results/final_patches"/f"{bug}.py").write_text(final)
        selected[bug]={
            "attempt_id":record["attempt_id"],"model":MODEL_ID,
            "technique":record["technique"],"seed":record["seed"],
            "raw_response_sha256":sha256(record["completion"]),"final_module_sha256":sha256(final),
            "assembly":"Original scaffold retained; emitted executable statements and relative nesting unchanged.",
            "tests_passed":result["passed"],
        }
        path.write_text(json.dumps(selected,indent=2)+"\n")
        print("Adopted",bug,"from",record["attempt_id"],flush=True)
    print("Selected",len(selected),"of 10:",", ".join(sorted(selected)))


if __name__=="__main__":
    main()
