"""Complete exposed opportunity and feedback-substitution audit."""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean
from causal_playback.data import ROOT,load,pool,inputs
from causal_playback.core import POLICIES
from causal_playback.replay import reserve,screen
from causal_compensation.data import SOURCES
from feedback_opportunity.frontier import periods,enumerate_paths
from feedback_opportunity.controller import simulate
from reserve_recovery.run import canonical,encode,sha


def feedback_values():
    rows=json.loads((ROOT/'feedback_opportunity/results/wire_v1/results.json').read_text())['rows']
    return {(r['key'].split(':')[0],r['key'].split(':')[1],int(r['key'].split(':')[2]),int(r['key'].split(':')[3])):
            tuple(r['quality_units']) for r in rows}


def analysis(progress=False):
    records=load(json.loads((ROOT/'causal_playback/data/media_manifest.json').read_text()))
    with gzip.open(ROOT/'causal_playback/results/replay_v1/results.json.gz','rt') as f: old=json.load(f)
    saved={(r['key'],r['policy']):r for r in old['rows']}; feedback=feedback_values()
    frontier=[]; rows=[]
    for i,r in enumerate(records,1):
        result=enumerate_paths(periods(r),r.loss,reserve(r),saved[r.key,'rolling_nash']['worst_quality']-.02)
        frontier.append({'key':r.key,'scene':r.scene,'cohort':r.cohort,'original_loss_units':r.loss,
            'reserve_bytes':reserve(r),'nash_episode_quality_floor':saved[r.key,'rolling_nash']['worst_quality']-.02,**result})
        training=pool(records,r); rows.extend(simulate(r,training,p,feedback) for p in POLICIES)
        if progress and i%28==0: print(f'Opportunity and feedback audit {i}/168',flush=True)
    summaries={}; opportunities={}
    for group in ('all','v2','v3')+tuple(sorted({r.scene for r in records})):
        selected=[r for r in rows if group in ('all',r['cohort'],r['scene'])]
        cells=[]
        for policy in POLICIES:
            rs=[r for r in selected if r['policy']==policy]
            cells.append({'policy':policy,'episodes':len(rs),'half_repaid':sum(r['half_repaid'] for r in rs),
                **{n:mean(r[n] for r in rs) for n in ('unpaid_fraction','worst_quality','mean_quality','mean_stall_seconds')},
                'donor_floor_violations':sum(r['donor_floor_violations'] for r in rs),
                'recipient_floor_violations':sum(r['recipient_floor_violations'] for r in rs),
                'loss_estimation_mae_units':mean(abs(r['estimated_loss_units']-r['original_loss_units']) for r in rs),
                'credit_estimation_mae_units':mean(abs(r['estimated_credit_units']-r['actual_credit_units']) for r in rs),
                'action_disagreements_vs_ideal_feedback':sum(a['decision']['rungs']!=b['decision']['rungs'] for r in rs
                    for a,b in zip(r['rounds'],saved[r['key'],policy]['rounds']))})
        summaries[group]=cells
        fs=[r for r in frontier if group in ('all',r['cohort'],r['scene'])]; os=[]
        for name in ('structural','strict','quality_guard','exact_current_greedy'):
            feasible=[r for r in fs if r['bounds'][name] is not None]
            os.append({'benchmark':name,'episodes':len(fs),'feasible_episodes':len(feasible),
                'half_repaid':sum(r['bounds'][name]['half_repaid'] for r in feasible),
                'mean_unpaid_feasible':mean(r['bounds'][name]['unpaid_fraction'] for r in feasible) if feasible else None,
                'gap_vs_saved_cost_greedy_feasible':mean(saved[r['key'],'cost_greedy']['unpaid_fraction']-r['bounds'][name]['unpaid_fraction'] for r in feasible) if feasible else None})
        opportunities[group]=os
    return {'exposed_only':True,'frontier':frontier,'feedback_rows':rows,'feedback_summary':summaries,
            'opportunity_summary':opportunities,'unchanged_practical_screen':screen(summaries)}


def provenance():
    own=list((ROOT/'feedback_opportunity').glob('*.py'))+list((ROOT/'feedback_opportunity').glob('*.mjs'))+[ROOT/'feedback_opportunity/PLAN.md']
    dependencies=[ROOT/n for n in ('causal_playback/core.py','causal_playback/clock.py','causal_playback/replay.py',
        'causal_playback/data.py','live_testbed/playback_clock.py','service_opportunity/model.py','recovery_objective/core.py',
        'feasibility_frontier/core.py','causal_compensation/data.py','reserve_recovery/run.py')]
    data=list(inputs())+[ROOT/'causal_playback/results/replay_v1/results.json.gz',ROOT/'feedback_opportunity/results/wire_v1/results.json']
    return {'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in own+dependencies},
            'input_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in data}}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--output',type=Path,default=ROOT/'feedback_opportunity/results/audit_v1')
    a=p.parse_args()
    if a.output.exists(): p.error('preserve previous outcomes')
    result=encode(analysis(True)); a.output.mkdir(parents=True)
    (a.output/'results.json.gz').write_bytes(gzip.compress(canonical(result),mtime=0))
    meta={**provenance(),'scientific_sha256':hashlib.sha256(canonical(result)).hexdigest(),
          'result_sha256':sha(a.output/'results.json.gz')}
    (a.output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'opportunities':result['opportunity_summary']['all'],
                      'feedback':result['feedback_summary']['all'],'screen':result['unchanged_practical_screen']},indent=2))
