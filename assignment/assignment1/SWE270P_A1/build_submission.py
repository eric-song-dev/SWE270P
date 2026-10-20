"""Verify raw-model provenance, tested hashes, and the exact required ZIP tree."""

import ast
import json
import xml.etree.ElementTree as ET
from collections import Counter
from zipfile import ZIP_DEFLATED, ZipFile

from prompt_designs import TECHNIQUES
from workflow import MODEL_ID, PATCH_DIR, PROMPTS_PATH, ROOT, assemble_patch, executable_body, extract_code, original_source, sha256, signature, target_name


def main():
    records=[json.loads(line) for line in PROMPTS_PATH.read_text().splitlines()]
    by_id={record['attempt_id']:record for record in records}
    assert len(by_id)==len(records), "Duplicate attempt IDs."
    assert all(r['model']==MODEL_ID and r['prompt'].strip() for r in records)
    assert all(r.get('completion','').strip() or r.get('status')=='interrupted' for r in records)
    expected_ids={f'BUG{i:03d}_{method}_v{variant}_code-plan_primary' for i in range(10) for method in TECHNIQUES for variant in (1,2)}
    assert expected_ids<=by_id.keys(), "The full 80-attempt four-method matrix is incomplete."
    selected=json.loads((ROOT/'experiments/selected.json').read_text())
    final_results=json.loads((ROOT/'experiments/final_tests.json').read_text())
    additional_cases=list(ET.parse(ROOT/'experiments/additional_tests.xml').iter('testcase'))
    assert all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in additional_cases)
    assert sum(c.attrib.get('classname','').endswith('test_workflow') for c in additional_cases)==6
    assert set(selected)=={f'BUG{i:03d}' for i in range(10)}
    assert {p.name for p in PATCH_DIR.glob('*.py')}=={f'BUG{i:03d}.py' for i in range(10)}
    provenance={}
    for bug,choice in selected.items():
        record=by_id[choice['attempt_id']]
        final=(PATCH_DIR/f'{bug}.py').read_text()
        assert choice['model']==record['model']==MODEL_ID
        assert choice['raw_response_sha256']==sha256(record['completion'])
        assert choice['final_module_sha256']==sha256(final)
        assert assemble_patch(bug,record['completion'])==final, f'{bug}: final file cannot be reconstructed from the actual response.'
        assert final_results[bug]['all_passed']
        assert final_results[bug]['code_sha256']==sha256(final), f'{bug}: stale test evidence.'
        emitted=extract_code(record['completion'],target_name(bug),signature(bug))
        original_tree=ast.parse(original_source(bug))
        final_tree=ast.parse(final)
        emitted_tree=ast.parse(emitted)
        target=next(n for n in final_tree.body if isinstance(n,ast.FunctionDef) and n.name==target_name(bug))
        raw_target=next(n for n in emitted_tree.body if isinstance(n,ast.FunctionDef) and n.name==target_name(bug))
        assert executable_body(target)==executable_body(raw_target)
        assert all(any(ast.dump(n)==ast.dump(m) for m in final_tree.body) for n in original_tree.body if isinstance(n,(ast.Import,ast.ImportFrom)))
        compile(final,f'{bug}.py','exec')
        provenance[bug]={
            **choice,
            'representation':record.get('representation',record.get('phase')),
            'phase':record.get('phase'),
            'generated_executable_ast_sha256':sha256(json.dumps(executable_body(raw_target))),
            'final_executable_ast_sha256':sha256(json.dumps(executable_body(target))),
            'generated_logic_manually_edited':False,
            'original_signature_imports_helpers_and_documentation_preserved':True,
            'test_cases_passed':final_results[bug]['passed'],
            'guidance':'Algorithm and statement-level repair plan authored by the assistant; free Gemma sampling emitted the selected code.',
        }
    (ROOT/'experiments/provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
    members={'results/prompts.jsonl'}|{f'results/final_patches/BUG{i:03d}.py' for i in range(10)}
    archive_path=ROOT/'SWE270P_A1.ZIP'
    with ZipFile(archive_path,'w',compression=ZIP_DEFLATED) as archive:
        for member in sorted(members):
            archive.write(ROOT/member,arcname=member)
    with ZipFile(archive_path) as archive:
        assert set(archive.namelist())==members and archive.testzip() is None
        assert all(archive.read(m)==(ROOT/m).read_bytes() for m in members)

    assessments={}
    for path in [ROOT/'experiments/attempts.jsonl',ROOT/'experiments/recovered_evaluations.jsonl',*(ROOT/'experiments').glob('*probe/assessments.jsonl')]:
        if path.exists():
            for line in path.read_text().splitlines():
                rec=json.loads(line);assessments[rec['attempt_id']]=rec
    matrix_path=ROOT/'experiments/final_matrix_evaluations.jsonl'
    matrix=[json.loads(line) for line in matrix_path.read_text().splitlines()]
    assert {r['attempt_id'] for r in matrix}==expected_ids
    assert all(r['test_suite_sha256']==sha256((ROOT/'tests/test_repairs.py').read_text()) for r in matrix)
    assessments.update({r['attempt_id']:r for r in matrix})
    table=[]
    for method in TECHNIQUES:
        ids=[key for key in expected_ids if by_id[key]['technique']==method]
        counts=Counter(assessments[key]['status'] for key in ids)
        table.append(f"| {method} | {len(ids)} | {counts['passed']} | {sum(v for k,v in counts.items() if k!='passed')} |")
    environment=json.loads((ROOT/'experiments/environment.json').read_text())
    passed=sum(result['passed'] for result in final_results.values())
    report=f'''# Assignment 1: Prompting for Program Repair

## Result

All ten final target functions were emitted by the required local `{MODEL_ID}` model and selected only after passing the supplied and additional tests. The final executable statements were not manually repaired after generation. The upload is `SWE270P_A1.ZIP`, with exactly the required eleven files under `results/`.

## Environment

Python {environment['python']} in `../.venv`; local CPU float32 inference through Hugging Face Transformers; model snapshot `{environment['revision']}`. Sampling uses temperature 1.0, top-p 0.95, top-k 50, recorded seeds, and at most 768 newly generated tokens. The chat template is applied and only new tokens are decoded. No external inference API is used. Exact package versions are in `requirements.txt` and `experiments/environment.json`.

## Prompting experiment

The complete primary matrix contains 80 calls: ten bugs, all four required methods, and two designs per method. Additional pilots and feedback-based retries are also retained. The append-only prompt log currently contains {len(records)} records; {sum(r.get('status')=='interrupted' for r in records)} interrupted call is explicitly marked without an invented completion.

- Zero-shot: implementation from a contract/plan, or a maintainer checklist with acceptance checks; no worked examples of other tasks.
- One-shot: one worked loop-completion example or one worked guard/pointer example before the target.
- Chain-of-thought: request a brief high-level invariant/return-placement summary or boundary/counterexample summary before code. The model sometimes ignored the summary request; raw output is retained unchanged.
- Few-shot: multiple worked examples for counting, loop completion, and pointer state; variations include two or three examples and body-versus-function output formats.

The primary free-sampling outcomes below count a candidate as successful only if its complete assembled module passed every supplied and additional test for that bug. Rejections include invalid syntax, changed interfaces, wrong/example functions, unexpected top-level execution, and malformed nesting. Failures and timeouts remain in the experiment evidence.

All 80 saved primary responses were re-evaluated with the same finalized test suite, including mixed/None node labels. `experiments/final_matrix_evaluations.jsonl` records that consistent comparison and the test-suite hash; initial historical assessments are retained separately.

These counts are descriptive rather than a controlled ranking: some prompts include feedback from earlier candidates, and each design has one primary sampled response.

| Method | Primary attempts | Passed all local tests | Unsuccessful |
|---|---:|---:|---:|
{chr(10).join(table)}

## What improved the results

Natural-language plans and explicit nesting labels often still produced wrong attributes, omitted loops, or incorrect return placement. More explicit statement-level plans, code-body formatting, sampling with different seeds, and feedback from actual test failures produced passing outputs. An earlier natural-language sweep was interrupted when changing strategy; its completed calls and interrupted call remain recorded.

This is **strongly guided code generation**. The assistant analyzed the bugs and authored the repair algorithms, including explicit Python expressions and control-flow plans. Some prompts supply the complete corrected body as a plan for transcription. Gemma is responsible for emitting the selected implementation; this experiment does not claim that the 270M model independently discovered the bugs or algorithms. No constrained-token decoding or forced completion was used.

## Assembly and provenance

The assembler restores the original module around the emitted target function. Original imports, auxiliary functions, function signatures, and documentation are retained. An emitted body may receive the unchanged original function header and a uniform indentation shift; relative indentation and executable statements are preserved. Original docstrings may be restored. Invalid logical nesting is rejected rather than repaired. Extra imports/helpers are included only if the model emitted them.

Every final file must be exactly reconstructible from its logged raw completion. `experiments/provenance.json` stores the source attempt, seed, response/module hashes, matching generated/final executable AST hashes, and test result for all ten bugs. The package builder rejects edited code or stale test evidence. The original `data/` files and supplied tests remain the experiment baseline.

BUG001 uses Dijkstra with a dictionary frontier and compares tentative distances rather than Node objects; its original heap helpers remain included and are not called by the repaired target. BUG005 uses a list queue, which matches the generated `pop(0)` operation. Some original imports therefore remain unused as part of the preserved module scaffold.

| Bug | Selected method | Raw attempt | Tests passed |
|---|---|---|---:|
{chr(10).join(f"| {bug} | {item['technique']} | `{item['attempt_id']}` | {final_results[bug]['passed']} |" for bug,item in sorted(selected.items()))}

## Validation

Original baseline: 8/30 supplied tests passed. Final selected modules: **{passed} local target-function test cases passed**, including all 30 supplied tests and {passed-30} additional cases. The extra suite covers strict fractional distance boundaries, shortest-path ties and priority improvements, exhaustive simple-path oracles, negative-edge graphs with no negative cycles, exhaustive small spanning trees, all 512 three-node directed graphs, long searches, linked-list identities and every small cycle entry, exhaustive parentheses strings through length ten, and long/mixed inputs. Six additional assembly tests check that generated logic is preserved and malformed output is rejected.

`evaluate.py` tests temporary copies containing unchanged supplied tests. `verify_submission.py` independently extracts the actual ZIP, verifies provenance, runs supplied and extra tests against those extracted patches, and validates the exact archive tree. The completed notebook runs the workflow with resume semantics: completed attempt IDs reuse real saved results; on a fresh output directory the same cells call the local model and log new attempts.

The private Gradescope tests are not available locally, so a score cannot be guaranteed. No Gradescope upload has been performed.

## Rubric alignment

| Criterion | Submission evidence |
|---|---|
| Completeness (10 points) | All four required methods are present in the actual prompt log; all ten complete replacement modules are included and trace to model outputs. |
| Diversity of Prompts (5 points) | Contract/checklist and counterexample framing, different worked examples, two/three-example designs, natural-language/nesting/statement plans, body/function output formats, and feedback-based retries are represented in the real calls. This category remains a reviewer judgment. |
| Test Coverage (10 points) | All 30 supplied and {passed-30} additional local target checks pass. Official credit depends on the private Gradescope tests. |
'''
    (ROOT/'REPORT.md').write_text(report)
    print(f'Built {archive_path}: 11 files, {len(records)} raw prompt records, 10 model-emitted repairs.')
    print('All final modules reconstruct exactly from logged responses; executable ASTs match.')


if __name__=='__main__':
    main()
