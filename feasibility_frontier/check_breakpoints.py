"""Additional post-run validation of exact frontier endpoints; no method changes."""
import argparse
from fractions import Fraction as F
import gzip
import json
import platform
from feasibility_frontier.data import ROOT,load
from feasibility_frontier.core import dp_feasible
from feasibility_frontier.run import sha


def check(output):
    with gzip.open(output/'results.json.gz','rt') as f: payload=json.load(f)
    catalogue={e.key:(e,p) for e,p in load()}
    checks=points=0
    for number,row in enumerate(payload['rows'],1):
        e,periods=catalogue[row['key']]
        resources=sorted({a.multiplier for p in periods for a in p})
        for key,frontier in row['frontiers'].items():
            m,epsilon=map(int,key.split(':'))
            for point in frontier:
                cap=F(point['peak_multiplier']); budget=point['donor_total_units']
                assert dp_feasible(periods,e.loss,m,epsilon,budget,cap),(e.key,key,point)
                checks+=1; points+=1
                if budget>0:
                    assert not dp_feasible(periods,e.loss,m,epsilon,budget-1,cap),(e.key,key,'harm optimum')
                    checks+=1
                if cap>1:
                    preceding=max(r for r in resources if r<cap)
                    assert not dp_feasible(periods,e.loss,m,epsilon,budget,preceding),(e.key,key,'resource optimum')
                    checks+=1
        if number%28==0: print(f'Checked exact endpoints for {number}/168 episodes',flush=True)
    return {'passed':True,'post_run_additional_validation':True,'method_or_target_changed':False,
            'episodes':len(payload['rows']),'frontier_points':points,'independent_dp_checks':checks,
            'endpoint_feasibility':True,'minimum_harm_at_endpoint':True,'minimum_resource_for_endpoint_harm':True,
            'script_sha256':sha(ROOT/'feasibility_frontier/check_breakpoints.py'),
            'results_sha256':sha(output/'results.json.gz'),'metadata_sha256':sha(output/'metadata.json'),
            'python':platform.python_version(),'platform':platform.platform()}


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=lambda s:ROOT/s,default=ROOT/'feasibility_frontier/results/audit_v1')
    parser.add_argument('--save')
    args=parser.parse_args()
    if args.save and ('/' in args.save or '\\' in args.save or not args.save.endswith('.json')):
        parser.error('local JSON filename required')
    result=check(args.output)
    if args.save:
        with (args.output/args.save).open('x',encoding='utf-8') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))
