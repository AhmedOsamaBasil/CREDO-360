"""Recompute exact frontier slices and independently verify every witness."""
import argparse
import gzip
import hashlib
import json
import platform
from pathlib import Path
from feasibility_frontier.run import ROOT,sha,analysis,encode,canonical,report


def verify(output):
    meta=json.loads((output/'metadata.json').read_text())
    assert meta['exposed_data_only'] and meta['future_known_offline_audit']
    for field in ('source_sha256','input_sha256'):
        for name,digest in meta[field].items(): assert sha(ROOT/name)==digest,name
    for name,digest in meta['result_sha256'].items(): assert sha(output/name)==digest,name
    payload=encode(analysis(progress=True))
    with gzip.open(output/'results.json.gz','rt',encoding='utf-8') as f: assert payload==json.load(f)
    assert report(payload)==(output/'REPORT.md').read_text()
    digest=hashlib.sha256(canonical(payload)).hexdigest()
    assert digest==meta['scientific_sha256']
    return {'passed':True,'episodes':len(payload['rows']),**payload['verification'],
            'source_input_result_hashes':True,'scientific_sha256':digest,
            'python':platform.python_version(),'platform':platform.platform()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'feasibility_frontier/results/audit_v1')
    parser.add_argument('--save')
    args=parser.parse_args()
    if args.save and (Path(args.save).name!=args.save or not args.save.endswith('.json')): parser.error('new local JSON name required')
    result=verify(args.output)
    if args.save:
        with (args.output/args.save).open('x',encoding='utf-8') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))
