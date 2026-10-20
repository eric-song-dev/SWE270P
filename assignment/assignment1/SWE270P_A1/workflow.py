"""Local Gemma inference, raw logging, and code-only assembly without logic edits."""

import ast
import datetime as dt
import hashlib
import json
import re
import textwrap
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
MODEL_ID = "google/gemma-3-270m-it"
PROMPTS_PATH = ROOT / "results/prompts.jsonl"
PATCH_DIR = ROOT / "results/final_patches"
TARGETS = (
    "has_close_elements", "shortest_path_length", "shortest_paths",
    "minimum_spanning_tree", "shortest_path_lengths", "breadth_first_search",
    "depth_first_search", "reverse_linked_list", "detect_cycle", "longestValidParentheses",
)
_tokenizer = _model = None


def original_source(bug):
    if not re.fullmatch(r"BUG00[0-9]", bug):
        raise ValueError("Expected BUG000 through BUG009.")
    return (ROOT / "data" / bug / "buggy.py").read_text()


def target_name(bug):
    return TARGETS[int(bug[-3:])]


def target_node(bug):
    return next(n for n in ast.parse(original_source(bug)).body if isinstance(n, ast.FunctionDef) and n.name == target_name(bug))


def signature(bug):
    node = target_node(bug)
    return original_source(bug).splitlines()[node.lineno - 1].strip()


def load_model():
    global _tokenizer, _model
    if _model is None:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
        torch.set_num_threads(4)
        _tokenizer = AutoTokenizer.from_pretrained(MODEL_ID, local_files_only=True)
        _model = AutoModelForCausalLM.from_pretrained(MODEL_ID, local_files_only=True, dtype=torch.float32)
        _model.eval()
    return _tokenizer, _model


def generate_text(prompt: str, max_new_tokens: int = 768, *, seed=2700, temperature=1.0) -> str:
    """Sample on CPU; decode only new tokens after Gemma's chat template."""
    import torch
    from transformers import set_seed
    tokenizer, model = load_model()
    set_seed(seed)
    inputs = tokenizer.apply_chat_template(
        [{"role": "user", "content": prompt}], tokenize=True,
        add_generation_prompt=True, return_dict=True, return_tensors="pt",
    ).to(model.device)
    with torch.inference_mode():
        output = model.generate(
            **inputs, max_new_tokens=max_new_tokens, do_sample=True,
            temperature=temperature, top_p=0.95, top_k=50,
            pad_token_id=tokenizer.eos_token_id,
        )
    return tokenizer.decode(output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True)


def log_prompt(technique, prompt, completion=None, bug_file=None, model=MODEL_ID, **metadata):
    record = {
        "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
        "technique": technique, "prompt": prompt, "model": model,
    }
    if completion is not None:
        record["completion"] = completion
    if bug_file is not None:
        record["bug_file"] = bug_file
    record.update(metadata)
    PROMPTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with PROMPTS_PATH.open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(record, ensure_ascii=False) + "\n")


def run_prompt(bug, technique, prompt, *, attempt_id, seed, variant, phase="primary", representation="natural-language", max_new_tokens=768):
    started = time.perf_counter()
    completion = generate_text(prompt, max_new_tokens, seed=seed)
    log_prompt(
        technique, prompt, completion, f"{bug}.py", attempt_id=attempt_id,
        seed=seed, variant=variant, phase=phase, representation=representation, temperature=1.0,
        top_p=0.95, top_k=50, do_sample=True, max_new_tokens=max_new_tokens,
        generation_seconds=round(time.perf_counter() - started, 3),
    )
    return completion


def extract_code(response, function_name=None, body_signature=None):
    """Select parseable emitted Python; reject incomplete or malformed output."""
    blocks = re.findall(r"```(?:python|py)?[ \t]*\n(.*?)```", response, re.DOTALL)
    candidates = blocks + (["\n\n".join(blocks)] if len(blocks) > 1 else []) if blocks else [response.strip()]
    for code in sorted(candidates, key=len, reverse=True):
        code = textwrap.dedent(code)
        try:
            tree = ast.parse(code)
        except SyntaxError:
            continue
        names = {n.name for n in tree.body if isinstance(n, ast.FunctionDef)}
        if (function_name in names) if function_name else bool(names):
            return code.strip() + "\n"
    if body_signature is not None:
        for body in sorted(candidates, key=len, reverse=True):
            # A uniform indentation shift only supplies the original function
            # header. Relative nesting and every generated statement are kept.
            wrapped = body_signature + "\n" + textwrap.indent(textwrap.dedent(body).strip("\n"), "    ") + "\n"
            try:
                tree = ast.parse(wrapped)
                compile(tree, "generated_body", "exec")
            except (SyntaxError, IndentationError):
                continue
            function = tree.body[0]
            if function_name is not None and function.name != function_name:
                continue
            # Do not reinterpret a complete function for the wrong target as
            # the target body, or include example/test invocations as a patch.
            if any(isinstance(n, ast.FunctionDef) for n in function.body):
                continue
            return wrapped
    raise ValueError("No complete parseable target function in the raw response.")


def _doc_node(function):
    first = function.body[0]
    return first if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str) else None


def executable_body(function):
    """An AST fingerprint that ignores docstrings, locations, and formatting."""
    return [ast.dump(n) for n in function.body if n is not _doc_node(function)]


def assemble_patch(bug, response):
    """Replace a target with emitted code, retaining original scaffold/docstrings.

    No generated statements, operators, indentation, or variable names are repaired.
    Malformed code and altered signatures are rejected and must be regenerated.
    """
    original = original_source(bug)
    old_tree = ast.parse(original)
    old = target_node(bug)
    code = extract_code(response, old.name, signature(bug))
    tree = ast.parse(code)
    matches = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == old.name]
    if len(matches) != 1:
        raise ValueError("Expected exactly one target function definition.")
    generated = matches[0]
    if generated.decorator_list:
        raise ValueError("Unexpected generated decorators.")
    annotations_match = (ast.dump(generated.returns) if generated.returns is not None else None) == (ast.dump(old.returns) if old.returns is not None else None)
    if ast.dump(generated.args) != ast.dump(old.args) or not annotations_match:
        raise ValueError("The generated function changed the original signature.")
    emitted = code.splitlines(keepends=True)[generated.lineno - 1:generated.end_lineno]
    old_doc = _doc_node(old)
    if old_doc is not None:
        new_doc = _doc_node(generated)
        doc_lines = original.splitlines(keepends=True)[old_doc.lineno - 1:old_doc.end_lineno]
        if new_doc is None:
            insertion = generated.body[0].lineno - generated.lineno
            emitted[insertion:insertion] = doc_lines
        else:
            emitted[new_doc.lineno - generated.lineno:new_doc.end_lineno - generated.lineno + 1] = doc_lines
    replacement = "".join(emitted).rstrip() + "\n"
    old_names = {n.name for n in old_tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef))}
    extras = []
    imports = []
    existing_imports = {ast.dump(n) for n in old_tree.body if isinstance(n, (ast.Import, ast.ImportFrom))}
    for node in tree.body:
        if node is generated:
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            if ast.dump(node) not in existing_imports:
                imports.append(ast.get_source_segment(code, node))
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if node.name in old_names:
                raise ValueError("The response attempts to replace an original helper.")
            extras.append(ast.get_source_segment(code, node))
        elif not (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)):
            raise ValueError("Unexpected top-level executable code in the response.")
    lines = original.splitlines(keepends=True)
    lines[old.lineno - 1:old.end_lineno] = [replacement + ("\n\n" + "\n\n".join(extras) + "\n" if extras else "")]
    final = ("\n".join(imports) + "\n\n" if imports else "") + "".join(lines)
    final_tree = ast.parse(final)
    final_target = next(n for n in final_tree.body if isinstance(n, ast.FunctionDef) and n.name == old.name)
    if executable_body(final_target) != executable_body(generated):
        raise AssertionError("Assembly changed generated executable statements.")
    # Original auxiliary functions and trailing documentation remain untouched.
    for helper in old_tree.body:
        if isinstance(helper, ast.FunctionDef) and helper.name != old.name:
            replacement_helper = next(n for n in final_tree.body if isinstance(n, ast.FunctionDef) and n.name == helper.name)
            assert ast.dump(helper) == ast.dump(replacement_helper)
    return final


def save_final_patch(bug_file, model_output):
    if not re.fullmatch(r"BUG00[0-9]\.py", bug_file):
        raise ValueError("Invalid final patch filename.")
    final = assemble_patch(bug_file[:-3], model_output)
    PATCH_DIR.mkdir(parents=True, exist_ok=True)
    path = PATCH_DIR / bug_file
    path.write_text(final, encoding="utf-8")
    return str(path)


def sha256(text):
    return hashlib.sha256(text.encode()).hexdigest()
