"""Rebuild every exposed-data outcome and check conditional risk certificates."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
from causal_compensation.run import ROOT,sha,analysis,encode,report


def verify(output):
    meta=json.loads((output/'metadata.json').read_text())
    assert meta['exposed_development_only']
    for field in ('source_sha256','input_sha256'):
        for name,digest in meta[field].items(): assert sha(ROOT/name)==digest,name
    for name,digest in meta['result_sha256'].items(): assert sha(output/name)==digest,name
    computed=encode(analysis(progress=True))
    assert computed==json.loads((output/'results.json').read_text())
    assert report(computed)==(output/'REPORT.md').read_text()
    digest=hashlib.sha256(json.dumps(computed,sort_keys=True,separators=(',',':')).encode()).hexdigest()
    assert digest==meta['scientific_sha256']
    return {'passed':True,'exposed_development_only':True,'episodes':len(computed['rows']),
            'source_input_result_hashes':True,'all_outcomes_and_certificates_recomputed':True,
            'scientific_sha256':digest,'python':platform.python_version(),'platform':platform.platform()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'causal_compensation/results/development_v1')
    parser.add_argument('--save')
    args=parser.parse_args()
    if args.save and (Path(args.save).name!=args.save or not args.save.endswith('.json')): parser.error('new local JSON filename required')
    result=verify(args.output)
    if args.save:
        with (args.output/args.save).open('x',encoding='utf-8') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))
