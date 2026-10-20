"""Local Gemma inference and honest, append-only experiment logging."""

import ast
import datetime as dt
import json
import re
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_ID = "google/gemma-3-270m-it"
PROMPTS_PATH = ROOT / "results" / "prompts.jsonl"
PATCH_DIR = ROOT / "results" / "final_patches"
_tokenizer = None
_model = None


def load_model():
    """Load the required model once, using the existing Hugging Face cache."""
    global _tokenizer, _model
    if _model is None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer

        torch.set_num_threads(4)
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
        _model = AutoModelForCausalLM.from_pretrained(
            MODEL_ID, local_files_only=True, dtype=torch.float32
        )
        _model.eval()
    return _tokenizer, _model


def generate_text(prompt: str, max_new_tokens: int = 768) -> str:
    """Apply Gemma's chat template and decode only newly generated tokens."""
    import torch

    tokenizer, model = load_model()
    inputs = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}],
        add_generation_prompt=True,
        tokenize=True,
        return_dict=True,
        return_tensors="pt",
    ).to(model.device)
    with torch.inference_mode():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(
        output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True
    )


def log_prompt(technique, prompt, completion=None, bug_file=None, model=None, **extra):
    """Append an actual attempt; never replace a completion with edited code."""
    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "technique": technique,
        "prompt": prompt,
    }
    for key, value in (
        ("completion", completion), ("bug_file", bug_file), ("model", model)
    ):
        if value is not None:
            record[key] = value
    record.update(extra)
    PROMPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROMPTS_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def extract_code(model_output: str) -> str:
    """Extract a parseable code block (or a plain Python response)."""
    blocks = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", model_output, re.DOTALL)
    candidates = blocks if blocks else [model_output.strip()]
    for candidate in sorted(candidates, key=len, reverse=True):
        candidate = candidate.strip() + "\n"
        try:
            tree = ast.parse(candidate)
        except SyntaxError:
            continue
        if any(isinstance(node, ast.FunctionDef) for node in tree.body):
            return candidate
    raise ValueError("The response contains no complete, parseable Python function.")


def validate_interface(bug_file: str, code: str):
    """Require every original public function and its original parameters."""
    if not re.fullmatch(r"BUG00[0-9]\.py", bug_file):
        raise ValueError("Expected a filename between BUG000.py and BUG009.py.")
    original = ast.parse((ROOT / "data" / bug_file[:-3] / "buggy.py").read_text())
    replacement = ast.parse(code)
    functions = {
        node.name: node for node in replacement.body if isinstance(node, ast.FunctionDef)
    }
    for node in original.body:
        if isinstance(node, ast.FunctionDef):
            other = functions.get(node.name)
            if other is None or ast.dump(node.args) != ast.dump(other.args):
                raise ValueError(f"Missing function or changed signature: {node.name}")


def save_final_patch(bug_file: str, model_output: str) -> str:
    """Save a complete, interface-compatible module after code extraction."""
    code = extract_code(model_output)
    validate_interface(bug_file, code)
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    destination = PATCH_DIR / bug_file
    destination.write_text(code, encoding="utf-8")
    return str(destination)


def run_prompt(technique, prompt, bug_file, *, variant="notebook", max_new_tokens=768):
    """Generate and log before attempting extraction or testing."""
    started = time.perf_counter()
    completion = generate_text(prompt, max_new_tokens)
    log_prompt(
        technique, prompt, completion, bug_file, MODEL_ID,
        variant=variant, max_new_tokens=max_new_tokens, do_sample=False,
        elapsed_seconds=round(time.perf_counter() - started, 3),
    )
    return completion
