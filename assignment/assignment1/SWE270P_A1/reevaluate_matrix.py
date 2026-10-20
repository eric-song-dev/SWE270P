"""Compare all 80 primary responses using the same finalized test suite."""

import json

from evaluate import evaluate_patch
from prompt_designs import TECHNIQUES
from workflow import PROMPTS_PATH, ROOT, assemble_patch, sha256


def main():
    records={r['attempt_id']:r for r in (json.loads(line) for line in PROMPTS_PATH.read_text().splitlines())}
    suite_hash=sha256((ROOT/'tests/test_repairs.py').read_text())
    output=ROOT/'experiments/final_matrix_evaluations.jsonl'
    previous={}
    if output.exists():
        previous={r['attempt_id']:r for r in (json.loads(line) for line in output.read_text().splitlines())}
    assessments=[]
    for i in range(10):
        bug=f'BUG{i:03d}'
        for method in TECHNIQUES:
            for variant in (1,2):
                attempt=f'{bug}_{method}_v{variant}_code-plan_primary'
                raw=records[attempt]
                if attempt in previous and previous[attempt]['test_suite_sha256']==suite_hash:
                    assessments.append(previous[attempt])
                    continue
                assessment={'attempt_id':attempt,'bug':bug,'technique':method,'variant':variant,'test_suite_sha256':suite_hash,'raw_response_sha256':sha256(raw['completion'])}
                try:
                    code=assemble_patch(bug,raw['completion'])
                    assessment['tests']=evaluate_patch(bug,code)
                    assessment['status']=assessment['tests']['status']
                except (ValueError,SyntaxError) as error:
                    assessment.update(status='rejected',error=str(error))
                assessments.append(assessment)
                print(attempt,assessment['status'],flush=True)
    output.write_text(''.join(json.dumps(r)+'\n' for r in assessments))
    print('Finalized-suite primary comparison:',len(assessments),'responses.')


if __name__=='__main__':
    main()
