"""Fixed exposed-only early-commitment study; retain failures and all controls."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean
from causal_playback.data import ROOT,load,inputs
from feedback_opportunity.run import feedback_values
from early_commitment.core import POLICIES,MATCHED
from early_commitment.replay import simulate
from reserve_recovery.run import canonical,encode,sha

OUT=ROOT/'early_commitment/results/development_v1'
DATA=ROOT/'early_commitment/data/prefix_v1'


def contexts():
    records=load(json.loads((ROOT/'causal_playback/data/media_manifest.json').read_text()))
    with gzip.open(DATA/'forecasts.json.gz','rt') as f: forecasts=json.load(f)['rows']
    with gzip.open(ROOT/'feedback_opportunity/results/audit_v1/results.json.gz','rt') as f: old=json.load(f)['feedback_rows']
    return records,feedback_values(),forecasts,old


def summarize(rows):
    result={}
    for group in ('all','v2','v3')+tuple(sorted({r['scene'] for r in rows})):
        selected=[r for r in rows if group in ('all',r['cohort'],r['scene'])]
        cells=[]
        for policy,delay in [(p,.08) for p in POLICIES]+[('prefix_mpc',.5)]:
            rs=[r for r in selected if r['policy']==policy and r['delay']==delay]
            cells.append({'policy':policy,'delay':delay,'episodes':len(rs),'half_repaid':sum(r['half_repaid'] for r in rs),
                **{k:mean(r[k] for r in rs) for k in ('unpaid_fraction','worst_quality','mean_quality','mean_stall_seconds','wait_seconds','current_mae','extra_bytes','startup_seconds')},
                'donor_floor_violations':sum(r['donor_floor_violations'] for r in rs),
                'recipient_floor_violations':sum(r['recipient_floor_violations'] for r in rs)})
        result[group]=cells
    return result


def screen(rows,old):
    checks={}
    for cohort in ('v2','v3'):
        a=[r for r in rows if r['cohort']==cohort and r['policy']=='prefix_mpc' and r['delay']==.08]
        comparisons={p:[r for r in rows if r['cohort']==cohort and r['policy']==p and r['delay']==.08] for p in MATCHED}
        comparisons.update({'historical_'+p:[r for r in old if r['cohort']==cohort and r['policy']==p] for p in sorted({r['policy'] for r in old})})
        for name,b in comparisons.items():
            assert len(a)==len(b)==84
            checks[cohort+'_gain_'+name]=mean(r['unpaid_fraction'] for r in b)-mean(r['unpaid_fraction'] for r in a)>=.005
            checks[cohort+'_half_'+name]=sum(r['half_repaid'] for r in a)>=sum(r['half_repaid'] for r in b)
            checks[cohort+'_quality_'+name]=mean(r['worst_quality'] for r in a)>=mean(r['worst_quality'] for r in b)-.02
            checks[cohort+'_stall_'+name]=mean(r['mean_stall_seconds'] for r in a)<=mean(r['mean_stall_seconds'] for r in b)+.1
        for field in ('donor_floor_violations','recipient_floor_violations'):
            checks[cohort+'_'+field]=sum(r[field] for r in a)==0
    return {'passed':all(checks.values()),'checks':checks}


def analysis(progress=False):
    records,feedback,forecasts,old=contexts(); rows=[]
    for i,r in enumerate(records,1):
        rows.extend(simulate(r,p,feedback,forecasts) for p in POLICIES)
        rows.append(simulate(r,'prefix_mpc',feedback,forecasts,.5))
        if progress and i%28==0: print(f'Early commitment exposed replay {i}/168',flush=True)
    return {'exposed_only':True,'fresh_holdout_used':False,'timing':'simulated fluid; incremental telemetry not wire-tested',
            'rows':rows,'summary':summarize(rows),'screen':screen(rows,old)}


def report(result):
    lines=['# Early commitment exposed-data results','',f"Exploratory progression screen: **{result['screen']['passed']}**.",
        '', 'Incremental telemetry and playback timing are simulated. No new holdout, no HMD trial.', '']
    for group,cells in result['summary'].items():
        lines += ['## '+group,'','| Policy | Delay s | Half / episodes | Unpaid | Worst quality | Stall s | Wait s | Current MAE | Donor / recipient floor losses |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|---:|']
        for r in cells:
            lines.append(f"| {r['policy']} | {r['delay']:.2f} | {r['half_repaid']}/{r['episodes']} | {r['unpaid_fraction']:.6f} | {r['worst_quality']:.4f} | {r['mean_stall_seconds']:.4f} | {r['wait_seconds']:.4f} | {r['current_mae']:.4f} | {r['donor_floor_violations']}/{r['recipient_floor_violations']} |")
        lines.append('')
    lines+=['## Failed predeclared checks','']+[f'- {k}' for k,v in result['screen']['checks'].items() if not v]+['']
    return '\n'.join(lines)


def provenance():
    own=('__init__.py','prepare.py','core.py','replay.py','run.py','verify.py','test_core.py','PLAN.md')
    deps=('feedback_opportunity/controller.py','feedback_opportunity/feedback.py','feedback_opportunity/run.py',
          'causal_playback/data.py','causal_playback/core.py','causal_playback/clock.py','causal_playback/replay.py',
          'service_opportunity/model.py','feasibility_frontier/core.py','recovery_objective/core.py',
          'live_testbed/playback_clock.py','causal_compensation/data.py','reserve_recovery/run.py')
    paths=[ROOT/'early_commitment'/n for n in own]+[ROOT/n for n in deps]
    data=list(inputs())+[DATA/'forecasts.json.gz',DATA/'metadata.json',ROOT/'feedback_opportunity/results/wire_v1/results.json',ROOT/'feedback_opportunity/results/audit_v1/results.json.gz']
    return {'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in paths},'input_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in data}}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.parse_args(); result=encode(analysis(True))
    OUT.mkdir(parents=True,exist_ok=False)
    (OUT/'results.json.gz').write_bytes(gzip.compress(canonical(result),mtime=0)); (OUT/'REPORT.md').write_text(report(result))
    meta={**provenance(),'scientific_sha256':hashlib.sha256(canonical(result)).hexdigest(),
          'result_sha256':{n:sha(OUT/n) for n in ('results.json.gz','REPORT.md')}}
    (OUT/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'summary':result['summary'],'screen_passed':result['screen']['passed']},indent=2))
