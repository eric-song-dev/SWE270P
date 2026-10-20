"""Execute this Python-only notebook sequentially in the assignment venv."""

import contextlib
import datetime as dt
import io
import json
import sys

import nbformat

from workflow import ROOT


def main():
    assert sys.prefix!=sys.base_prefix,'Run with ../.venv/bin/python.'
    path=ROOT/'A1_instruction.ipynb'
    notebook=nbformat.read(path,as_version=4)
    nbformat.validate(notebook)
    namespace={'__name__':'__notebook__','__file__':str(path)}
    count=0
    for index,cell in enumerate(notebook.cells):
        if cell.cell_type!='code':
            continue
        count+=1
        stdout,stderr=io.StringIO(),io.StringIO()
        with contextlib.redirect_stdout(stdout),contextlib.redirect_stderr(stderr):
            exec(compile(cell.source,f'{path.name}:cell-{index}','exec'),namespace)
        cell.execution_count=count
        cell.outputs=[]
        for name,stream in (('stdout',stdout),('stderr',stderr)):
            if stream.getvalue():
                cell.outputs.append(nbformat.v4.new_output('stream',name=name,text=stream.getvalue()))
        print(f'Notebook cell {index} passed.',flush=True)
    metadata={'method':'Sequential Python code-cell execution, without a Jupyter kernel server','python':sys.executable,'code_cells_executed':count,'status':'passed','timestamp':dt.datetime.now(dt.timezone.utc).isoformat()}
    notebook.metadata['execution']=metadata
    nbformat.validate(notebook)
    nbformat.write(notebook,path)
    (ROOT/'experiments/notebook_execution.json').write_text(json.dumps(metadata,indent=2)+'\n')
    print(f'Notebook validated and all {count} code cells executed successfully.')


if __name__=='__main__':
    main()
