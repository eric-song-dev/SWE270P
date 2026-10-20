"""Independently test the actual upload and prove every repair's logged origin."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from zipfile import ZipFile

from workflow import ROOT, assemble_patch, sha256


def main():
    assert sys.prefix!=sys.base_prefix, 'Use the assignment venv.'
    expected={'results/prompts.jsonl'}|{f'results/final_patches/BUG{i:03d}.py' for i in range(10)}
    archive_path=ROOT/'SWE270P_A1.ZIP'
    provenance=json.loads((ROOT/'experiments/provenance.json').read_text())
    with ZipFile(archive_path) as archive:
        assert len(archive.namelist())==len(expected)
        assert set(archive.namelist())==expected and archive.testzip() is None
        assert all(archive.read(path)==(ROOT/path).read_bytes() for path in expected)
        records=[json.loads(line) for line in archive.read('results/prompts.jsonl').decode().splitlines()]
        by_id={record['attempt_id']:record for record in records}
        for i in range(10):
            bug=f'BUG{i:03d}'
            proof=provenance[bug]
            response=by_id[proof['attempt_id']]['completion']
            code=archive.read(f'results/final_patches/{bug}.py').decode()
            assert sha256(response)==proof['raw_response_sha256']
            assert sha256(code)==proof['final_module_sha256']
            assert assemble_patch(bug,response)==code
            assert proof['generated_executable_ast_sha256']==proof['final_executable_ast_sha256']
            assert proof['generated_logic_manually_edited'] is False
        with tempfile.TemporaryDirectory(prefix='swe270p-upload-') as temp:
            directory=Path(temp)
            archive.extractall(directory)
            shutil.copytree(ROOT/'data',directory/'supplied',ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','.DS_Store'))
            for i in range(10):
                bug=f'BUG{i:03d}'
                shutil.copyfile(directory/'results/final_patches'/f'{bug}.py',directory/'supplied'/bug/'buggy.py')
            (directory/'tests').mkdir()
            shutil.copyfile(ROOT/'tests/test_repairs.py',directory/'tests/test_repairs.py')
            config=directory/'pytest.ini';config.write_text('[pytest]\n')
            xml_path=ROOT/'experiments/submission_tests.xml'
            environment=os.environ.copy();environment['PATCH_DIR']=str(directory/'results/final_patches')
            result=subprocess.run(
                [sys.executable,'-m','pytest','supplied','tests','-q','--tb=short','-c',str(config),f'--junitxml={xml_path}'],
                cwd=directory,env=environment,capture_output=True,text=True,timeout=60,
            )
            print(result.stdout,end='')
            assert result.returncode==0,result.stderr+result.stdout
            cases=list(ET.parse(xml_path).iter('testcase'))
            assert all(c.find('failure') is None and c.find('error') is None and c.find('skipped') is None for c in cases)
            supplied={f'BUG{i:03d}':sum(f'.BUG{i:03d}.' in f".{c.attrib.get('classname','')}." for c in cases) for i in range(10)}
            assert all(n==3 for n in supplied.values())
    audit={
        'python':sys.executable,'archive_sha256':__import__('hashlib').sha256(archive_path.read_bytes()).hexdigest(),
        'archive_files':len(expected),'prompt_records':len(records),
        'completed_generations':sum(bool(r.get('completion')) for r in records),
        'explicitly_interrupted_calls':sum(r.get('status')=='interrupted' for r in records),
        'prompt_method_counts':dict(Counter(r['technique'] for r in records)),
        'all_ten_repairs_reconstructed_from_raw_model_outputs':True,
        'all_ten_generated_and_final_executable_asts_match':True,
        'supplied_tests_passed_by_bug':supplied,'additional_target_cases_passed':len(cases)-30,
        'total_target_cases_passed':len(cases),'status':'passed',
    }
    (ROOT/'experiments/submission_audit.json').write_text(json.dumps(audit,indent=2)+'\n')
    print(f'Upload verified: {len(cases)} target test cases, 10 raw-output provenance proofs, {len(records)} prompt records.')


if __name__=='__main__':
    main()
