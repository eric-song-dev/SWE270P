"""Run 80 real local Gemma attempts: 10 bugs x 4 methods x 2 designs."""

import argparse
import datetime as dt
import hashlib
import importlib.metadata
import json
import platform
import time

from evaluate import evaluate_patch
from prompt_designs import TECHNIQUES, make_prompt
from repair_workflow import MODEL_ID, PROMPTS_PATH, ROOT, extract_code, load_model, validate_interface


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--max-new-tokens", type=int, default=768)
    parser.add_argument("--bug", choices=[f"BUG{i:03d}" for i in range(10)])
    args = parser.parse_args()
    directory = ROOT / "experiments"
    directory.mkdir(exist_ok=True)
    candidates = directory / "candidates"
    candidates.mkdir(exist_ok=True)
    assessments_path = directory / "candidate_evaluations.jsonl"
    completed = set()
    if assessments_path.exists():
        completed = {json.loads(line)["attempt_id"] for line in assessments_path.read_text().splitlines()}
    existing = {}
    if PROMPTS_PATH.exists():
        existing = {
            record["attempt_id"]: record
            for line in PROMPTS_PATH.read_text().splitlines()
            if "attempt_id" in (record := json.loads(line))
        }
    tokenizer, model = load_model()
    from huggingface_hub import try_to_load_from_cache
    from pathlib import Path
    cached_config = try_to_load_from_cache(MODEL_ID, "config.json")
    cached_parts = Path(cached_config).parts if isinstance(cached_config, str) else ()
    cached_revision = cached_parts[cached_parts.index("snapshots") + 1] if "snapshots" in cached_parts else None
    metadata = {
        "model": MODEL_ID,
        "model_revision": getattr(model.config, "_commit_hash", None) or cached_revision,
        "device": str(model.device),
        "dtype": str(model.dtype),
        "python": platform.python_version(),
        "packages": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "pytest", "huggingface-hub", "accelerate")},
        "decoding": {"do_sample": False, "max_new_tokens": args.max_new_tokens},
        "started_at": dt.datetime.now(dt.timezone.utc).isoformat(),
    }
    (directory / "environment.json").write_text(json.dumps(metadata, indent=2) + "\n")
    bugs = [args.bug] if args.bug else [f"BUG{i:03d}" for i in range(10)]
    for bug in bugs:
        for technique in TECHNIQUES:
            for variant in range(2):
                attempt = f"{bug}_{technique}_{variant + 1}"
                if attempt in completed:
                    continue
                started = time.perf_counter()
                prompt = make_prompt(bug, technique, variant)
                if attempt in existing:
                    completion = existing[attempt]["completion"]
                else:
                    # Log the raw response immediately, before extraction or test execution.
                    from repair_workflow import generate_text, log_prompt
                    completion = generate_text(prompt, args.max_new_tokens)
                    log_prompt(
                        technique, prompt, completion, f"{bug}.py", MODEL_ID,
                        attempt_id=attempt, variant=variant + 1,
                        max_new_tokens=args.max_new_tokens, do_sample=False,
                        elapsed_seconds=round(time.perf_counter() - started, 3),
                    )
                result = {"attempt_id": attempt, "bug": bug, "technique": technique, "variant": variant + 1}
                try:
                    code = extract_code(completion)
                    path = candidates / f"{attempt}.py"
                    path.write_text(code, encoding="utf-8")
                    result["code_sha256"] = hashlib.sha256(code.encode()).hexdigest()
                    try:
                        validate_interface(f"{bug}.py", code)
                        result["interface_valid"] = True
                    except ValueError as error:
                        result["interface_valid"] = False
                        result["interface_error"] = str(error)
                    result["tests"] = evaluate_patch(bug, code)
                    result["status"] = "passed" if result["interface_valid"] and result["tests"]["all_passed"] else "failed"
                except (ValueError, SyntaxError) as error:
                    result["status"] = "extraction_failed"
                    result["error"] = str(error)
                result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
                with assessments_path.open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(result) + "\n")
                print(f"{attempt}: {result['status']} ({result['elapsed_seconds']}s)", flush=True)


if __name__ == "__main__":
    main()
