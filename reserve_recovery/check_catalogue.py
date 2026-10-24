"""Additional post-run full Cartesian check; independent of the gain/cost DP."""
import argparse
from fractions import Fraction as F
import gzip
import json
from math import prod
import platform
import numpy as np
from feasibility_frontier.data import load,ROOT
from reserve_recovery.catalogue import PEAKS,FRACTIONS
from reserve_recovery.run import sha


def check(output):
    with gzip.open(output/'results.json.gz','rt') as f: p=json.load(f)
    saved={r['key']:r for r in p['catalogue']['episodes']}
    queries=paths=0
    for number,(e,periods) in enumerate(load(),1):
        row=saved[e.key]
        for peak in PEAKS:
            menu=tuple(tuple(a for a in options if a.harm==0 and a.multiplier<=peak) for options in periods)
            shape=tuple(map(len,menu)); n=prod(shape)
            if n>3_000_000: raise ValueError('reference Cartesian limit exceeded')
            index=np.indices(shape,dtype=np.int32).reshape(4,-1)
            gains=np.zeros(n,dtype=np.int64); costs=gains.copy()
            for t,options in enumerate(menu):
                gains+=np.array([a.gain for a in options],dtype=np.int64)[index[t]]
                costs+=np.array([max(a.bytes-a.reference_bytes,0) for a in options],dtype=np.int64)[index[t]]
            paths+=n
            allowed=gains>=(e.loss+1)//2
            best=int(costs[allowed].min()) if allowed.any() else None
            witness=row['minimum_reserve'][str(peak)]
            assert best==(None if witness is None else witness['extra_bytes']),(e.key,str(peak),'minimum reserve')
            queries+=1
            for rho in FRACTIONS:
                limit=rho*row['baseline_bytes']
                budget=limit.numerator//limit.denominator
                gain=min(e.loss,int(gains[costs<=budget].max()))
                out=next(x for x in row['outcomes'] if x['policy']=='offline' and F(x['peak'])==peak and F(x['reserve_fraction'])==rho)
                assert F(out['unpaid_fraction'])==F(e.loss-gain,e.loss),(e.key,str(peak),str(rho))
                queries+=1
        if number%28==0: print(f'Cartesian verification {number}/168',flush=True)
    return {'passed':True,'post_run_additional_verification':True,'method_or_target_changed':False,
        'unpruned_complete_paths':paths,'exact_queries':queries,'episodes':len(saved),
        'script_sha256':sha(ROOT/'reserve_recovery/check_catalogue.py'),
        'results_sha256':sha(output/'results.json.gz'),'python':platform.python_version(),'platform':platform.platform()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=lambda s:ROOT/s,default=ROOT/'reserve_recovery/results/analysis_v1')
    parser.add_argument('--save')
    args=parser.parse_args()
    if args.save and ('/' in args.save or '\\' in args.save or not args.save.endswith('.json')): parser.error('local JSON filename required')
    r=check(args.output)
    if args.save:
        with (args.output/args.save).open('x') as f: json.dump(r,f,indent=2); f.write('\n')
    print(json.dumps(r,indent=2))
