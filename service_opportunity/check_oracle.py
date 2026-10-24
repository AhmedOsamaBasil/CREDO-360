"""Independent unpruned Cartesian audit of every exposed offline optimum."""
import argparse
from fractions import Fraction as F
import gzip
import json
from math import prod
import platform
import numpy as np
from feasibility_frontier.data import ROOT,load
from service_opportunity.model import CAPACITY,RATIOS
from reserve_recovery.run import sha


def check(output):
    with gzip.open(output/'results.json.gz','rt') as f: p=json.load(f)
    saved={r['key']:r for r in p['rows']}; paths=queries=0
    for e,periods in load():
        menu=tuple(tuple(a for a in ps if a.harm==0 and a.bytes<=CAPACITY) for ps in periods)
        shape=tuple(map(len,menu)); n=prod(shape)
        if n>3_000_000: raise ValueError('Cartesian reference too large')
        indices=np.indices(shape,dtype=np.int32).reshape(4,-1)
        gains=np.zeros(n,dtype=np.int64); costs=gains.copy()
        for t,ps in enumerate(menu):
            gains+=np.array([a.gain for a in ps],dtype=np.int64)[indices[t]]
            costs+=np.array([max(a.bytes-a.reference_bytes,0) for a in ps],dtype=np.int64)[indices[t]]
        gains=np.minimum(gains,e.loss); paths+=n
        for rho in RATIOS:
            reserve=rho*sum(ps[0].reference_bytes for ps in periods)
            mask=costs<=reserve.numerator//reserve.denominator
            best_gain=int(gains[mask].max()); best_cost=int(costs[mask & (gains==best_gain)].min())
            result=next(r for r in saved[e.key]['outcomes'] if r['policy']=='offline' and F(r['reserve_fraction'])==rho)
            assert result['delivered_units']==best_gain and result['extra_bytes']==best_cost
            queries+=1
    return {'passed':True,'unpruned_complete_paths':paths,'exact_queries':queries,'episodes':len(saved),
        'script_sha256':sha(ROOT/'service_opportunity/check_oracle.py'),
        'result_sha256':sha(output/'results.json.gz'),'python':platform.python_version(),'platform':platform.platform()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--save')
    a=parser.parse_args()
    output=ROOT/'service_opportunity/results/development_v1'
    if a.save and ('/' in a.save or '\\' in a.save or not a.save.endswith('.json')): parser.error('local JSON filename')
    r=check(output)
    if a.save:
        with (output/a.save).open('x') as f: json.dump(r,f,indent=2); f.write('\n')
    print(json.dumps(r,indent=2))
