"""Run actual sampled Gemma repair experiments and select only tested generations."""

import argparse
import datetime as dt
import importlib.metadata
import json
import platform
from pathlib import Path

from evaluate import evaluate_patch
from prompt_designs import PLANS, TECHNIQUES, make_prompt
from structured_plans import make_code_plan_prompt, make_structured_prompt
from workflow import MODEL_ID, PROMPTS_PATH, ROOT, assemble_patch, load_model, run_prompt, sha256

DIRECTORY = ROOT / "experiments"
ASSESSMENTS = DIRECTORY / "attempts.jsonl"
SELECTION = DIRECTORY / "selected.json"


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=("primary","refinement"), default="primary")
    parser.add_argument("--format", choices=("natural-language","levels","code-plan","indented-plan","literal-plan"), default="code-plan")
    parser.add_argument("--bug", choices=[f"BUG{i:03d}" for i in range(10)])
    parser.add_argument("--method", choices=TECHNIQUES)
    parser.add_argument("--attempts", type=int, default=16)
    parser.add_argument("--round", type=int, default=1)
    parser.add_argument("--plan-file", type=Path)
    args = parser.parse_args(argv)
    DIRECTORY.mkdir(exist_ok=True)
    (DIRECTORY / "candidates").mkdir(exist_ok=True)
    (ROOT / "results/final_patches").mkdir(parents=True,exist_ok=True)
    tokenizer, model = load_model()
    environment_path = DIRECTORY / "environment.json"
    if not environment_path.exists():
        from huggingface_hub import try_to_load_from_cache
        cached = Path(try_to_load_from_cache(MODEL_ID,"config.json"))
        parts = cached.parts
        environment_path.write_text(json.dumps({
            "model":MODEL_ID,"revision":parts[parts.index("snapshots")+1],
            "python":platform.python_version(),"executable":__import__('sys').executable,
            "device":str(model.device),"dtype":str(model.dtype),
            "packages":{p:importlib.metadata.version(p) for p in ("torch","transformers","pytest","huggingface-hub","accelerate","nbformat")},
            "started_at":dt.datetime.now(dt.timezone.utc).isoformat(),
            "do_sample":True,"temperature":1.0,"top_p":0.95,"top_k":50,
        },indent=2)+"\n")
    existing = {r["attempt_id"]:r for r in read_jsonl(PROMPTS_PATH)}
    evaluated = {r["attempt_id"]:r for r in read_jsonl(ASSESSMENTS)}
    selected = json.loads(SELECTION.read_text()) if SELECTION.exists() else {}
    plans = json.loads(args.plan_file.read_text()) if args.plan_file else {}
    bugs = [args.bug] if args.bug else [f"BUG{i:03d}" for i in range(10)]
    jobs = []
    for bug in bugs:
        if args.phase == "primary":
            for method in TECHNIQUES:
                if args.method and method != args.method:
                    continue
                for variant in range(2):
                    seed = 4900+int(bug[-3:])*100+TECHNIQUES.index(method)*10+variant
                    jobs.append((bug,method,variant,seed,f"{bug}_{method}_v{variant+1}_{args.format}_primary"))
        elif bug not in selected:
            for trial in range(args.attempts):
                method = TECHNIQUES[trial % 4]
                variant = (trial//4)%2
                seed = 10000+args.round*1000+int(bug[-3:])*100+trial
                jobs.append((bug,method,variant,seed,f"{bug}_{method}_{args.format}_r{args.round}_{trial+1}"))
    last_feedback = {}
    for bug,method,variant,seed,attempt in jobs:
        if args.phase == "refinement" and bug in selected:
            continue
        if attempt in evaluated:
            continue
        prompt_builder = {"natural-language":make_prompt,"levels":make_structured_prompt}.get(args.format,make_code_plan_prompt)
        rendered_variant = variant + (2 if args.format=="indented-plan" else 4 if args.format=="literal-plan" else 0)
        prompt = prompt_builder(bug,method,rendered_variant,last_feedback.get(bug,""))
        if bug in plans:
            prompt = prompt.replace(PLANS[bug],plans[bug])
        if attempt in existing:
            completion = existing[attempt]["completion"]
        else:
            completion = run_prompt(bug,method,prompt,attempt_id=attempt,seed=seed,variant=variant,phase=args.phase,representation=args.format)
        assessment = {"attempt_id":attempt,"bug":bug,"technique":method,"variant":variant,"seed":seed,"phase":args.phase,"representation":args.format}
        try:
            final = assemble_patch(bug,completion)
            (DIRECTORY/"candidates"/f"{attempt}.py").write_text(final)
            assessment["tests"] = evaluate_patch(bug,final)
            assessment["status"] = assessment["tests"]["status"]
            last_feedback[bug] = "; ".join(assessment["tests"].get("failure_messages",[])) or assessment["status"]
            if assessment["tests"]["all_passed"] and bug not in selected:
                (ROOT/"results/final_patches"/f"{bug}.py").write_text(final)
                selected[bug] = {
                    "attempt_id":attempt,"model":MODEL_ID,"technique":method,"seed":seed,
                    "raw_response_sha256":sha256(completion),"final_module_sha256":sha256(final),
                    "assembly":"Original imports, auxiliary functions and documentation retained. Generated executable statements unchanged.",
                    "tests_passed":assessment["tests"]["passed"],
                }
                SELECTION.write_text(json.dumps(selected,indent=2)+"\n")
        except (ValueError,SyntaxError) as error:
            assessment.update(status="rejected",error=str(error))
            last_feedback[bug] = str(error)+". Use the exact signature and valid Python indentation; do not emit a docstring."
        with ASSESSMENTS.open("a") as stream:
            stream.write(json.dumps(assessment)+"\n")
        print(f"{attempt}: {assessment['status']} | selected {len(selected)}/10",flush=True)
    print("Selected bugs:",", ".join(sorted(selected)),flush=True)


if __name__ == "__main__":
    main()
