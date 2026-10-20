"""Read-only comparison of exported assignment branches and their actual ZIPs."""

import argparse
import ast
import hashlib
import importlib.util
import io
import json
import os
import re
import shutil
import statistics
import subprocess
import sys
import tarfile
import tempfile
import textwrap
import time
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

OUT = Path(__file__).resolve().parent
COMMITS = {
    'feat-codex-generated-1': 'f4bfb542f06a90f22bec6c0ba2a8c1098043a6dc',
    'feat-codex-generated-2': '98256b48377c3ee0baea707823d7c4eb97623ac4',
}


def snapshots():
    """Re-export the pinned commits if the original disposable exports expired."""
    manifest = OUT / 'snapshots.json'
    if manifest.exists():
        saved = json.loads(manifest.read_text())
        roots = {name: Path(path) for name, path in saved['snapshots'].items()}
        if all((root / 'SWE270P_A1.ZIP').is_file() for root in roots.values()):
            return roots
    directory = Path(tempfile.mkdtemp(prefix='swe270p-branch-comparison-'))
    roots = {}
    for branch, commit in COMMITS.items():
        destination = directory / branch
        destination.mkdir()
        data = subprocess.check_output(
            ['git', 'archive', '--format=tar', commit, 'assignment/assignment1'], cwd=OUT,
        )
        with tarfile.open(fileobj=io.BytesIO(data)) as archive:
            archive.extractall(destination, filter='data')
        roots[branch] = destination / 'assignment/assignment1/SWE270P_A1'
    manifest.write_text(json.dumps({
        'directory': str(directory), 'commits': COMMITS,
        'snapshots': {name: str(root) for name, root in roots.items()},
    }, indent=2) + '\n')
    return roots


SNAPSHOTS = snapshots()


def fingerprint(node):
    return ast.dump(node) if node is not None else None


def executable_body(function):
    first = function.body[0]
    doc = first if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str) else None
    return [ast.dump(n) for n in function.body if n is not doc]


def audit():
    summary = {}
    for branch, root in SNAPSHOTS.items():
        records = [json.loads(line) for line in (root / 'results/prompts.jsonl').read_text().splitlines()]
        expected = {'results/prompts.jsonl'} | {f'results/final_patches/BUG{i:03d}.py' for i in range(10)}
        artifact = root / 'SWE270P_A1.ZIP'
        with ZipFile(artifact) as archive:
            assert set(archive.namelist()) == expected and len(archive.namelist()) == 11
            assert archive.testzip() is None
            assert all(archive.read(name) == (root / name).read_bytes() for name in expected)
        matches, helpers, imports = {}, {}, {}
        for i in range(10):
            bug = f'BUG{i:03d}'
            original = (root / f'data/{bug}/buggy.py').read_text()
            old = ast.parse(original)
            final = ast.parse((root / f'results/final_patches/{bug}.py').read_text())
            target = next(n for n in old.body if isinstance(n, ast.FunctionDef))
            repaired = next(n for n in final.body if isinstance(n, ast.FunctionDef) and n.name == target.name)
            assert fingerprint(target.args) == fingerprint(repaired.args)
            assert fingerprint(target.returns) == fingerprint(repaired.returns)
            matching = []
            for number, record in enumerate(records, 1):
                raw = record.get('completion')
                if not raw or record.get('bug_file') != bug + '.py':
                    continue
                blocks = re.findall(r'```(?:python|py)?[ \t]*\n(.*?)```', raw, re.DOTALL) or [raw]
                for block in blocks:
                    code = textwrap.dedent(block)
                    try:
                        tree = ast.parse(code)
                        functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
                        generated = next((n for n in functions if n.name == target.name), None)
                        if generated is None and not functions:
                            header = original.splitlines()[target.lineno - 1].strip()
                            wrapped = header + '\n' + textwrap.indent(code.strip('\n'), '    ') + '\n'
                            tree = ast.parse(wrapped)
                            compile(tree, 'raw-model-body', 'exec')
                            generated = tree.body[0]
                        if generated is not None and fingerprint(generated.args) == fingerprint(target.args) and executable_body(generated) == executable_body(repaired):
                            matching.append(record.get('attempt_id', f'line-{number}'))
                            break
                    except (SyntaxError, ValueError, TypeError):
                        continue
            matches[bug] = matching
            helpers[bug] = {
                n.name: any(isinstance(m, ast.FunctionDef) and m.name == n.name and ast.dump(n) == ast.dump(m) for m in final.body)
                for n in old.body if isinstance(n, ast.FunctionDef) and n.name != target.name
            }
            old_imports = {ast.dump(n) for n in old.body if isinstance(n, (ast.Import, ast.ImportFrom))}
            new_imports = {ast.dump(n) for n in final.body if isinstance(n, (ast.Import, ast.ImportFrom))}
            imports[bug] = old_imports <= new_imports
        notebook = json.loads((root / 'A1_instruction.ipynb').read_text())
        summary[branch] = {
            'archive_sha256': hashlib.sha256(artifact.read_bytes()).hexdigest(),
            'archive_exact_structure_and_matches_working_files': True,
            'prompt_records': len(records),
            'complete_raw_outputs': sum(bool(r.get('completion')) for r in records),
            'interrupted_records': sum(r.get('status') == 'interrupted' for r in records),
            'prompt_method_counts': dict(Counter(r['technique'] for r in records)),
            'final_target_bodies_matching_any_logged_raw_model_output': {bug: bool(ids) for bug, ids in matches.items()},
            'matching_attempt_ids': matches,
            'all_original_imports_retained': all(imports.values()),
            'helpers_unchanged_from_starter': helpers,
            'notebook_code_cells': sum(c['cell_type'] == 'code' for c in notebook['cells']),
            'notebook_has_saved_error_outputs': any(o.get('output_type') == 'error' for c in notebook['cells'] if c['cell_type'] == 'code' for o in c.get('outputs', [])),
        }
    roots = list(SNAPSHOTS.values())
    assert (roots[0].parent / 'requirement.txt').read_bytes() == (roots[1].parent / 'requirement.txt').read_bytes()
    for path in (roots[0] / 'data').rglob('*.py'):
        assert path.read_bytes() == (roots[1] / 'data' / path.relative_to(roots[0] / 'data')).read_bytes()
    (OUT / 'structural_audit.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


def common_tests(branch):
    root = SNAPSHOTS[branch]
    with tempfile.TemporaryDirectory(prefix='swe270p-common-tests-') as temporary:
        directory = Path(temporary)
        with ZipFile(root / 'SWE270P_A1.ZIP') as archive:
            archive.extractall(directory)
        shutil.copytree(root / 'data', directory / 'supplied', ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', '.DS_Store'))
        for i in range(10):
            bug = f'BUG{i:03d}'
            shutil.copyfile(directory / 'results/final_patches' / f'{bug}.py', directory / 'supplied' / bug / 'buggy.py')
        (directory / 'tests').mkdir()
        for name in ('test_robustness.py', 'test_review_cases.py'):
            shutil.copyfile(SNAPSHOTS['feat-codex-generated-1'] / 'tests' / name, directory / 'tests' / name)
        shutil.copyfile(SNAPSHOTS['feat-codex-generated-2'] / 'tests/test_repairs.py', directory / 'tests/test_repairs.py')
        (directory / 'pytest.ini').write_text('[pytest]\n')
        environment = os.environ.copy()
        environment['PATCH_DIR'] = str(directory / 'results/final_patches')
        xml_path = OUT / f'{branch}-common-tests.xml'
        result = subprocess.run(
            [sys.executable, '-m', 'pytest', 'supplied', 'tests', '-q', '--tb=short', '-c', str(directory / 'pytest.ini'), f'--junitxml={xml_path}'],
            cwd=directory, env=environment, capture_output=True, text=True, timeout=60,
        )
        (OUT / f'{branch}-common-tests.txt').write_text(result.stdout + result.stderr)
        cases = list(ET.parse(xml_path).iter('testcase'))
        failures = []
        for case in cases:
            error = case.find('failure')
            if error is None:
                error = case.find('error')
            if error is not None:
                failures.append({'name': case.attrib['name'], 'classname': case.attrib.get('classname'), 'message': error.attrib.get('message'), 'detail': error.text})
        supplied = [c for c in cases if c.attrib.get('classname', '').endswith('.test_bug')]
        auxiliary = [c for c in cases if c.attrib['name'] == 'test_dijkstra_helpers_restore_heap_and_handle_ties']
        summary = {
            'branch': branch, 'python': sys.executable, 'returncode': result.returncode,
            'total_cases': len(cases), 'passed': len(cases) - len(failures),
            'failed': len(failures), 'supplied_cases': len(supplied),
            'supplied_passed': sum(c.find('failure') is None and c.find('error') is None for c in supplied),
            'auxiliary_cases': len(auxiliary),
            'target_cases_excluding_auxiliary': len(cases) - len(auxiliary),
            'target_passed_excluding_auxiliary': sum(c not in auxiliary and c.find('failure') is None and c.find('error') is None for c in cases),
            'failures': failures,
        }
        (OUT / f'{branch}-common-results.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2))


def load(branch, bug):
    path = SNAPSHOTS[branch] / 'results/final_patches' / f'{bug}.py'
    spec = importlib.util.spec_from_file_location(branch.replace('-', '_') + '_' + bug, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Node:
    def __init__(self):
        self.successors = []
        self.successor = None


def focused_checks():
    summaries = {}
    for branch in SNAPSHOTS:
        shortest = load(branch, 'BUG001')
        dfs = load(branch, 'BUG006').depth_first_search
        heap = [(1, 'a'), (2, 'b'), (3, 'c')]
        shortest.insert_or_update(heap, (8, 'a'))
        actual = shortest.heappop(heap)[0]
        row = {'heap_priority_increase': {'expected_next_priority': 2, 'actual_next_priority': actual, 'passed': actual == 2}}
        heap = []
        try:
            shortest.insert_or_update(heap, (1, Node()))
            shortest.insert_or_update(heap, (1, Node()))
            row['heap_nonorderable_ties'] = {'passed': True}
        except Exception as error:
            row['heap_nonorderable_ties'] = {'passed': False, 'error': f'{type(error).__name__}: {error}'}
        a, b, c = Node(), Node(), Node()
        a.successors = {b}; b.successors = {c}; c.successors = set()
        try:
            actual = dfs(a, c)
            row['dfs_set_successors'] = {'passed': actual is True, 'actual': actual}
        except Exception as error:
            row['dfs_set_successors'] = {'passed': False, 'error': f'{type(error).__name__}: {error}'}
        summaries[branch] = row
    (OUT / 'focused_checks.json').write_text(json.dumps(summaries, indent=2) + '\n')
    print(json.dumps(summaries, indent=2))


def benchmarks():
    summaries = {}
    nodes = [Node() for _ in range(6001)]
    nodes[0].successors = nodes[1:]
    edges = {(nodes[0], node): i for i, node in enumerate(nodes[1:], 1)}
    start = Node(); start.successors = [Node() for _ in range(40000)]
    unreachable = Node()
    for branch in SNAPSHOTS:
        row = {}
        tasks = (
            ('dijkstra_6000_leaf_star', load(branch, 'BUG001').shortest_path_length, (edges, nodes[0], nodes[-1]), 6000),
            ('bfs_40000_leaf_star_unreachable', load(branch, 'BUG005').breadth_first_search, (start, unreachable), False),
        )
        for label, function, args, expected in tasks:
            times = []
            for _ in range(3):
                before = time.perf_counter()
                actual = function(*args)
                times.append(time.perf_counter() - before)
                assert actual == expected
            row[label] = {'seconds': times, 'median_seconds': statistics.median(times)}
        summaries[branch] = row
    (OUT / 'benchmarks.json').write_text(json.dumps(summaries, indent=2) + '\n')
    print(json.dumps(summaries, indent=2))


def notebooks(branch):
    """Execute each cell in a separate disposable copy with completed-run caches."""
    root = SNAPSHOTS[branch]
    with tempfile.TemporaryDirectory(prefix='swe270p-notebook-review-') as temporary:
        directory = Path(temporary) / 'assignment'
        shutil.copytree(root, directory, ignore=shutil.ignore_patterns('__pycache__', '.pytest_cache', '.DS_Store'))
        original_log = (directory / 'results/prompts.jsonl').read_bytes()
        with ZipFile(root / 'SWE270P_A1.ZIP') as archive:
            original_members = {name: archive.read(name) for name in archive.namelist()}
        script = '''import json
import time
from pathlib import Path
notebook = json.loads(Path('A1_instruction.ipynb').read_text())
namespace = {'__name__': '__main__'}
completed = []
for index, cell in enumerate(notebook['cells']):
    if cell['cell_type'] != 'code':
        continue
    before = time.perf_counter()
    exec(compile(''.join(cell['source']), f'notebook-cell-{index}', 'exec'), namespace)
    completed.append({'index': index, 'seconds': time.perf_counter() - before})
Path('comparison-notebook-execution.json').write_text(json.dumps(completed, indent=2))
'''
        runner = directory / 'comparison_run_notebook.py'
        runner.write_text(script)
        environment = os.environ.copy()
        environment.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
        before = time.perf_counter()
        result = subprocess.run(
            [sys.executable, str(runner)], cwd=directory, env=environment,
            capture_output=True, text=True, timeout=180,
        )
        elapsed = time.perf_counter() - before
        (OUT / f'{branch}-notebook.txt').write_text(result.stdout + result.stderr)
        cells_path = directory / 'comparison-notebook-execution.json'
        cells = json.loads(cells_path.read_text()) if cells_path.exists() else []
        with ZipFile(directory / 'SWE270P_A1.ZIP') as archive:
            rebuilt_members = {name: archive.read(name) for name in archive.namelist()}
        summary = {
            'branch': branch, 'python': sys.executable, 'returncode': result.returncode,
            'seconds': elapsed, 'code_cells_completed': len(cells), 'cells': cells,
            'mode': 'Resume/replay existing real outputs; not a fresh full inference sweep.',
            'prompt_log_byte_unchanged': original_log == (directory / 'results/prompts.jsonl').read_bytes(),
            'archive_member_bytes_unchanged': original_members == rebuilt_members,
        }
        (OUT / f'{branch}-notebook-results.json').write_text(json.dumps(summary, indent=2) + '\n')
        print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('audit', 'tests', 'focused', 'bench', 'notebook'))
    parser.add_argument('--branch', choices=tuple(SNAPSHOTS))
    arguments = parser.parse_args()
    if arguments.action == 'audit': audit()
    elif arguments.action == 'tests': common_tests(arguments.branch)
    elif arguments.action == 'focused': focused_checks()
    elif arguments.action == 'notebook': notebooks(arguments.branch)
    else: benchmarks()
