"""Compare independent platform derivations without pretending floats are bit-identical."""
import argparse
import hashlib
import json
from pathlib import Path
from wu_source.acquire import canonical
from .core import PACKAGE


def compare(a,b):
    differences=[]; floats=0
    def walk(x,y,path):
        nonlocal floats
        if type(x)!=type(y): raise ValueError('Type differs: '+path)
        if isinstance(x,dict):
            if set(x)!=set(y): raise ValueError('Keys differ: '+path)
            for k in sorted(x): walk(x[k],y[k],path+'.'+k)
        elif isinstance(x,list):
            if len(x)!=len(y): raise ValueError('Length differs: '+path)
            for i,(v,w) in enumerate(zip(x,y)): walk(v,w,f'{path}[{i}]')
        elif isinstance(x,float):
            floats+=1; error=abs(x-y); tolerance=1e-5 if 'degrees' in path else 1e-10
            if error>tolerance: raise ValueError('Numeric tolerance exceeded: '+path)
            if error: differences.append({'path':path,'absolute_difference':error,'tolerance':tolerance})
        elif x!=y: raise ValueError('Discrete result differs: '+path)
    walk(a,b,'report')
    return {'first_sha256':hashlib.sha256(canonical(a)).hexdigest(),'second_sha256':hashlib.sha256(canonical(b)).hexdigest(),
        'bit_identical':a==b,'float_values_checked':floats,'differing_float_values':len(differences),
        'maximum_difference':max(differences,key=lambda d:d['absolute_difference']) if differences else None,
        'angular_tolerance_degrees':1e-5,'other_numeric_tolerance':1e-10,'all_discrete_results_identical':True}


def main():
    p=argparse.ArgumentParser(__doc__); p.add_argument('--verify',action='store_true'); a=p.parse_args()
    first=json.loads((PACKAGE/'results/calibration_v1/report.json').read_text())
    second=json.loads((PACKAGE/'results/linux_calibration_v1/report.json').read_text())
    result=compare(first,second); path=PACKAGE/'results/replication_v1.json'
    if a.verify:
        if json.loads(path.read_text())!=result: raise ValueError('Replication comparison differs')
    else:
        with path.open('xb') as f: f.write(canonical(result))
    print(json.dumps(result))


if __name__=='__main__': main()
