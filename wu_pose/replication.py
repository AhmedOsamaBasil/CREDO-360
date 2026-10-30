"""Compare separately derived reports without disguising floating differences."""
import argparse
import json
import math
from pathlib import Path
from .core import PACKAGE,digest
from .run import read_artifact,validate,method_record,DEFAULT
from wu_source.acquire import canonical


def compare(a,b):
    differences=[]
    def walk(x,y,path):
        if type(x) is not type(y): raise ValueError('Platform value type differs')
        if isinstance(x,dict):
            if x.keys()!=y.keys(): raise ValueError('Platform fields differ')
            for k in x: walk(x[k],y[k],path+'/'+k)
        elif isinstance(x,list):
            if len(x)!=len(y): raise ValueError('Platform sequence length differs')
            for i,(s,t) in enumerate(zip(x,y)): walk(s,t,path+'/'+str(i))
        elif isinstance(x,float):
            if not math.isfinite(x) or not math.isfinite(y) or abs(x-y)>1e-10:
                raise ValueError('Platform numeric tolerance exceeded')
            if x!=y: differences.append(abs(x-y))
        elif x!=y: raise ValueError('Platform discrete value differs')
    walk(a,b,'')
    return {'primary_report_sha256':digest(a),'replica_report_sha256':digest(b),
        'exact_report_match':a==b,'differing_float_values':len(differences),
        'maximum_absolute_difference':max(differences,default=0.),
        'summary_absolute_tolerance':1e-10,'discrete_values_exact':True}


def main():
    p=argparse.ArgumentParser(__doc__); p.add_argument('--candidate',type=Path)
    p.add_argument('--verify',action='store_true'); a=p.parse_args()
    output=PACKAGE/'results/replication_v1'
    primary=read_artifact(DEFAULT)
    if a.verify:
        replica=read_artifact(PACKAGE/'results/linux_v1')
        expected={'schema':'wu-pose-platform-comparison-v1','method_sha256':digest(method_record()),
            'comparison':compare(primary,replica)}
        if json.loads((output/'report.json').read_text())!=expected: raise ValueError('Comparison changed')
        if json.loads((output/'metadata.json').read_text())!={'report_sha256':digest(expected)}:
            raise ValueError('Comparison binding differs')
    else:
        if not a.candidate: p.error('Independent candidate directory required')
        replica=read_artifact(a.candidate); validate(replica)
        expected={'schema':'wu-pose-platform-comparison-v1','method_sha256':digest(method_record()),
            'comparison':compare(primary,replica)}
        if output.exists(): raise ValueError('Preserve earlier comparison')
        output.mkdir(parents=True)
        (output/'report.json').write_bytes(canonical(expected))
        (output/'metadata.json').write_bytes(canonical({'report_sha256':digest(expected)}))
    print(json.dumps(expected))


if __name__=='__main__': main()
