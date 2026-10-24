"""Replay deterministic exposed results and audit stored controlled measurements."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform
from service_opportunity.run import ROOT,analysis,canonical,encode,report,sha


def verify(output):
    meta=json.loads((output/'metadata.json').read_text())
    for group in ('source_sha256','input_sha256'):
        for name,digest in meta[group].items(): assert sha(ROOT/name)==digest,name
    for name,digest in meta['result_sha256'].items(): assert sha(output/name)==digest,name
    service=json.loads((ROOT/'service_opportunity/results/service_v1.json').read_text())
    payload=encode(analysis(service,True))
    with gzip.open(output/'results.json.gz','rt') as f: assert json.load(f)==payload
    assert report(payload)==(output/'REPORT.md').read_text()
    digest=hashlib.sha256(canonical(payload)).hexdigest()
    assert digest==meta['scientific_sha256']
    return {'passed':True,'scientific_sha256':digest,'episodes':len(payload['rows']),
            'episode_policy_runs':sum(len(r['outcomes']) for r in payload['rows']),
            'service_probes_audited':len(service['probes']),'progression':payload['progression'],
            'python':platform.python_version(),'platform':platform.platform()}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'service_opportunity/results/development_v1')
    p.add_argument('--save')
    a=p.parse_args()
    if a.save and (Path(a.save).name!=a.save or not a.save.endswith('.json')): p.error('local JSON name required')
    result=verify(a.output)
    if a.save:
        with (a.output/a.save).open('x') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))
