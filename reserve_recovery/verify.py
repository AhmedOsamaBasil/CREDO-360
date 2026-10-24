"""Recompute the complete reserve artifact without modifying previous results."""
import argparse
import gzip
import hashlib
import json
import platform
from pathlib import Path
from reserve_recovery.run import ROOT,sha,lf_sha,encode,canonical,analysis,report


def verify(output):
    m=json.loads((output/'metadata.json').read_text())
    for field in ('source_sha256','input_sha256'):
        for name,digest in m[field].items():
            assert sha(ROOT/name)==digest or (name in m['canonical_lf_sha256']
                and lf_sha(ROOT/name)==m['canonical_lf_sha256'][name]),name
    for name,digest in m['result_sha256'].items(): assert sha(output/name)==digest,name
    p=encode(analysis(progress=True))
    with gzip.open(output/'results.json.gz','rt') as f: assert json.load(f)==p
    assert report(p)==(output/'REPORT.md').read_text()
    digest=hashlib.sha256(canonical(p)).hexdigest(); assert digest==m['scientific_sha256']
    return {'passed':True,'scientific_sha256':digest,'source_input_result_hashes':True,
        'episodes':len(p['catalogue']['episodes']),'analytical_cases':len(p['analytical']['cases']),
        'minimum_reserve_witnesses':p['catalogue']['minimum_reserve_witnesses'],
        'online_vs_oracle_checks':p['catalogue']['online_vs_oracle_checks'],
        'python':platform.python_version(),'platform':platform.platform()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'reserve_recovery/results/analysis_v1')
    parser.add_argument('--save')
    args=parser.parse_args()
    if args.save and (Path(args.save).name!=args.save or not args.save.endswith('.json')): parser.error('local JSON filename required')
    result=verify(args.output)
    if args.save:
        with (args.output/args.save).open('x') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))
