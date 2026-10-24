"""Post-hoc controls: cost-matched myopia and unconditional training mean.

These do not alter the frozen candidate, primary screen or experimental target.
"""
import argparse
from fractions import Fraction as F
import gzip
import hashlib
import json
from pathlib import Path
from feasibility_frontier.data import load
from service_opportunity.model import ROOT,RATIOS,records,pool,forecast,predicted_periods,sizes,optimize,valid
from reserve_recovery.catalogue import summarize_path
from reserve_recovery.run import sha,canonical,encode


def simulate(e,periods,record,training,rho,policy):
    reserve=rho*sum(p[0].reference_bytes for p in periods)
    debt=e.loss; spent=0; path=[]
    for t,current in enumerate(periods):
        future=()
        if policy=='unconditional_mpc':
            predicted,_=forecast(record.qualities[:t+1],e.loss,training,k=len(training))
            future=predicted_periods(predicted,tuple(sizes(p) for p in periods[t+1:]))
        gain,cost,plan=optimize((current,)+future,debt,reserve-spent)
        action=next(a for a in valid(current,reserve-spent) if a.rungs==plan[0])
        debt-=min(debt,action.gain); spent+=max(action.bytes-action.reference_bytes,0)
        path.append(action.rungs)
    out=summarize_path(periods,tuple(path),e.loss)
    assert out['remaining_fraction']==F(debt,e.loss) and out['extra_bytes']==spent<=reserve
    return {'policy':policy,'reserve_fraction':rho,'half_repaid':debt*2<=e.loss,**out}


def calculate():
    directory=ROOT/'service_opportunity/results/development_v1'
    with gzip.open(directory/'results.json.gz','rt') as f: primary=json.load(f)
    saved={r['key']:r for r in primary['rows']}; all_records=records(); rs={r.key:r for r in all_records}
    rows=[]
    for e,periods in load():
        record=rs[e.key]; training=pool(all_records,record)
        outcomes=[simulate(e,periods,record,training,rho,policy)
                  for rho in RATIOS for policy in ('cost_greedy','unconditional_mpc')]
        for o in outcomes:
            old=next(x for x in saved[e.key]['outcomes'] if F(x['reserve_fraction'])==o['reserve_fraction'] and x['policy']=='offline')
            assert o['remaining_fraction']>=F(old['remaining_fraction'])
        rows.append({'key':e.key,'scene':e.scene,'cohort':e.cohort,'outcomes':outcomes})
    summary={}
    for group in ('all','v2','v3')+tuple(sorted({r['scene'] for r in rows})):
        selected=[r for r in rows if group in ('all',r['scene'],r['cohort'])]
        cells=[]
        for rho in RATIOS:
            for policy in ('cost_greedy','unconditional_mpc'):
                values=[x for r in selected for x in r['outcomes'] if x['policy']==policy and x['reserve_fraction']==rho]
                cells.append({'reserve_fraction':rho,'policy':policy,'episodes':len(values),
                    'half_repaid':sum(x['half_repaid'] for x in values),
                    'mean_unpaid_fraction':sum(x['remaining_fraction'] for x in values)/len(values),
                    'mean_worst_quality':sum(x['worst_post_quality'] for x in values)/len(values),
                    'mean_quality':sum(x['mean_post_quality'] for x in values)/len(values)})
        summary[group]=cells
    return {'posthoc_diagnostic':True,'candidate_or_primary_screen_changed':False,
            'rows':rows,'summary':summary,'primary_result_sha256':sha(directory/'results.json.gz')}


def main():
    parser=argparse.ArgumentParser(__doc__); parser.add_argument('--verify',action='store_true')
    a=parser.parse_args(); directory=ROOT/'service_opportunity/results/development_v1'
    p=encode(calculate()); digest=hashlib.sha256(canonical(p)).hexdigest()
    if a.verify:
        with gzip.open(directory/'posthoc_ablation.json.gz','rt') as f: assert json.load(f)==p
        m=json.loads((directory/'posthoc_metadata.json').read_text())
        assert m['scientific_sha256']==digest and m['script_sha256']==sha(Path(__file__))
        assert m['result_sha256']==sha(directory/'posthoc_ablation.json.gz')
    else:
        with (directory/'posthoc_ablation.json.gz').open('xb') as f: f.write(gzip.compress(canonical(p),mtime=0))
        m={'scientific_sha256':digest,'script_sha256':sha(Path(__file__)),
           'result_sha256':sha(directory/'posthoc_ablation.json.gz')}
        with (directory/'posthoc_metadata.json').open('x') as f: json.dump(m,f,indent=2); f.write('\n')
    print(json.dumps({'verified':a.verify,'scientific_sha256':digest,
        'primary_comparison':{k:[x for x in p['summary'][k] if F(x['reserve_fraction'])==1] for k in ('all','v2','v3')}},indent=2))


if __name__=='__main__': main()
