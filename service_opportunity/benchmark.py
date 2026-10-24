"""Local decision-time check, separate from integrated player/network timing."""
import argparse
from fractions import Fraction as F
import gzip
import json
import platform
import time
from service_opportunity.model import ROOT,records,pool,forecast,sizes,predicted_periods,optimize
from feasibility_frontier.data import load
from reserve_recovery.run import sha


def benchmark():
    output=ROOT/'service_opportunity/results/development_v1'
    with gzip.open(output/'results.json.gz','rt') as f: payload=json.load(f)
    saved={r['key']:r for r in payload['rows']}; all_records=records(); rs={r.key:r for r in all_records}
    timings=[]
    for e,periods in load():
        record=rs[e.key]; training=pool(all_records,record)
        row=next(r for r in saved[e.key]['outcomes'] if r['policy']=='knn_mpc' and F(r['reserve_fraction'])==1)
        spent=0; reserve=F(row['reserve_bytes'])
        for t,decision in enumerate(row['decisions']):
            start=time.perf_counter()
            predicted,neighbors=forecast(record.qualities[:t+1],e.loss,training)
            future=predicted_periods(predicted,tuple(sizes(p) for p in periods[t+1:]))
            gain,cost,path=optimize((periods[t],)+future,decision['debt_before'],reserve-spent)
            elapsed=time.perf_counter()-start
            assert tuple(path[0])==tuple(decision['rungs'])
            assert gain==decision['predicted_additional_gain_units']
            timings.append({'episode':e.key,'step':t,'seconds':elapsed})
            spent=decision['spent_bytes']
    values=sorted(x['seconds'] for x in timings)
    return {'platform':platform.platform(),'python':platform.python_version(),
        'scope':'warm loaded input tables; forecast and exact optimizer only; not integrated network/player',
        'decision_budget_seconds':0.5,'observed_budget_pass':max(values)<=0.5,
        'decisions':len(values),'mean_seconds':sum(values)/len(values),'max_seconds':max(values),
        'p95_seconds':values[(95*len(values)+99)//100-1],
        'timings':timings,'script_sha256':sha(ROOT/'service_opportunity/benchmark.py'),
        'result_sha256':sha(output/'results.json.gz')}


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__); parser.add_argument('--save',required=True)
    a=parser.parse_args()
    if '/' in a.save or '\\' in a.save or not a.save.endswith('.json'): parser.error('local JSON name required')
    r=benchmark()
    with (ROOT/'service_opportunity/results/development_v1'/a.save).open('x') as f: json.dump(r,f,indent=2); f.write('\n')
    print(json.dumps({k:v for k,v in r.items() if k!='timings'},indent=2))
