"""All-exposed deterministic replay and shared live-log scientific audit."""
import argparse
from dataclasses import asdict
import gzip
import hashlib
import json
from pathlib import Path
import platform
from causal_playback.data import ROOT,load,pool,inputs
from causal_playback.core import decide,POLICIES
from causal_playback.clock import State
from reserve_recovery.run import canonical,encode,sha


def reserve(record): return sum(2*c[2] for c in record.costs[2:])


def choose_step(record,training,state,policy,t,start):
    idle_stall=state.idle(start); view,released=state.view(start)
    decision=decide(policy,record.loss,**view,sender=record.sender,costs=record.costs,
                    t=t,training=training,reserve=reserve(record)-state.spent)
    return decision,{'start':start,'idle_stall':idle_stall,'feedback_released':released,'view':view}


def simulate(record,training,policy):
    state=State(record); rounds=[]
    for t in range(2,6):
        decision,log=choose_step(record,training,state,policy,t,state.time)
        n=tuple(record.costs[t][r] for r in decision['rungs'])
        # Equal-rate fluid sharing until the shorter flow completes.
        arrivals=tuple(state.time+.05+.08+(2*x if x==min(n) else sum(n))*8/1_200_000 for x in n)
        end=max(state.time+10,max(arrivals)); metrics=state.deliver(record,t,decision,arrivals,end)
        rounds.append({**log,'segment':t,'decision':decision,'file_bytes':n,'arrivals':arrivals,'end':end,**metrics})
    return {'key':record.key,'scene':record.scene,'cohort':record.cohort,'policy':policy,
            'reserve_bytes':reserve(record),'loss_units':record.loss,'rounds':rounds,**state.final()}


def summarize(rows):
    result={}
    for group in ('all','v2','v3')+tuple(sorted({r['scene'] for r in rows})):
        selected=[r for r in rows if group in ('all',r['cohort'],r['scene'])]
        cells=[]
        for policy in POLICIES:
            rs=[r for r in selected if r['policy']==policy]
            if not rs: continue
            cells.append({'policy':policy,'episodes':len(rs),'half_repaid':sum(r['half_repaid'] for r in rs),
                **{name:sum(r[name] for r in rs)/len(rs) for name in
                   ('unpaid_fraction','mean_quality','worst_quality','mean_stall_seconds','current_mae','extra_bytes')},
                'donor_floor_violations':sum(r['donor_floor_violations'] for r in rs),
                'recipient_floor_violations':sum(r['recipient_floor_violations'] for r in rs)})
        result[group]=cells
    return result


def screen(summary):
    checks={}
    for cohort in ('v2','v3'):
        cells={r['policy']:r for r in summary[cohort]}; a=cells['knn_recovery']
        for policy,b in cells.items():
            if policy=='knn_recovery': continue
            checks[f'{cohort}_practical_gain_{policy}']=b['unpaid_fraction']-a['unpaid_fraction']>=.005
            checks[f'{cohort}_half_count_{policy}']=a['half_repaid']>=b['half_repaid']
            checks[f'{cohort}_quality_guard_{policy}']=a['worst_quality']>=b['worst_quality']-.02
        checks[f'{cohort}_donor_floor']=a['donor_floor_violations']==0
    return {'passed':all(checks.values()),'checks':checks}


def analysis(progress=False):
    manifest=json.loads((ROOT/'causal_playback/data/media_manifest.json').read_text())
    records=load(manifest); rows=[]
    for i,r in enumerate(records,1):
        training=pool(records,r)
        rows.extend(simulate(r,training,p) for p in POLICIES)
        if progress and i%28==0: print(f'Causal delayed-feedback replay {i}/168',flush=True)
    summary=summarize(rows)
    return {'exposed_only':True,'fresh_holdout_used':False,'timing':'simulated fluid service; not measured',
            'rows':rows,'summary':summary,'screen':screen(summary)}


def report(p):
    lines=['# Causal current-quality exposed replay','',
        'Completed-feedback-only estimates; simulated fluid timing; no new holdout.',
        '',f"Exploratory practical gate passed: **{p['screen']['passed']}**.",'']
    for group,cells in p['summary'].items():
        lines += ['## '+group,'','| Policy | Half / episodes | Unpaid | Worst quality | Mean quality | Mean stall s | Current MAE | Donor / recipient floor violations |',
                  '|---|---:|---:|---:|---:|---:|---:|---:|']
        for r in cells:
            lines.append(f"| {r['policy']} | {r['half_repaid']}/{r['episodes']} | {r['unpaid_fraction']:.6f} | "
                f"{r['worst_quality']:.4f} | {r['mean_quality']:.4f} | {r['mean_stall_seconds']:.4f} | "
                f"{r['current_mae']:.4f} | {r['donor_floor_violations']}/{r['recipient_floor_violations']} |")
        lines.append('')
    lines += ['Predicted floors are not certified actual-quality guarantees. Minimum rung2, actual MP4 bytes and delayed '
        'feedback differ from the prior oracle-current audit. Do not attribute a cross-study difference solely to prediction.','']
    return '\n'.join(lines)


def sources():
    paths=list((ROOT/'causal_playback').glob('*.py'))+[ROOT/'causal_playback/PLAN.md']
    paths += [ROOT/n for n in ('live_testbed/playback_clock.py','service_opportunity/model.py',
        'feasibility_frontier/core.py','feasibility_frontier/data.py','causal_compensation/data.py',
        'recovery_objective/core.py','reserve_recovery/run.py','reserve_recovery/core.py',
        'reserve_recovery/catalogue.py','reserve_recovery/cases.py')]
    return sorted(paths)


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--output',type=Path,default=ROOT/'causal_playback/results/replay_v1')
    a=p.parse_args()
    if a.output.exists(): p.error('preserve existing results')
    result=encode(analysis(True)); a.output.mkdir(parents=True)
    (a.output/'results.json.gz').write_bytes(gzip.compress(canonical(result),mtime=0))
    (a.output/'REPORT.md').write_text(report(result),encoding='utf-8')
    meta={'source_sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in sources()},
          'input_sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in inputs()},
          'result_sha256':{f.name:sha(f) for f in a.output.iterdir()},
          'scientific_sha256':hashlib.sha256(canonical(result)).hexdigest(),'python':platform.python_version()}
    (a.output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'scientific_sha256':meta['scientific_sha256'],'screen':result['screen']},indent=2))
