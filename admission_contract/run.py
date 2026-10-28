"""Frozen exposed admission batch and full deterministic verification."""
import argparse
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from statistics import mean
import numpy as np
from metric_contract.data import ROOT,INPUTS,load
from metric_contract.core import path_arrays,TICKS
from metric_contract.run import canonical,sha
from duration_contract.core import account
from duration_contract.run import media_rows,durations_for
from admission_contract.core import spatial_bounds,forecast,entry_inputs,clocks,path_stats,pick,certificate,control_path,independent,ETA

OUT=ROOT/'admission_contract/results/exposed_v1'
MAPS=ROOT/'feedback_opportunity/data/maps_v1'
OWN=('__init__.py','core.py','run.py','test_core.py','PLAN.md','THEORY.md')
DEPENDENCIES=('metric_contract/data.py','metric_contract/core.py','metric_contract/run.py',
              'duration_contract/core.py','duration_contract/run.py')


def provenance():
    paths=list(INPUTS)+['duration_contract/data/media_v1/timelines.json.gz',
        'duration_contract/results/replay_v1/results.json.gz','duration_contract/results/paced_v1/metadata.json']
    paths += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/'duration_contract/results/paced_v1').glob('session_*.json.gz'))]
    paths += ['feedback_opportunity/data/maps_v1/metadata.json']+[p.relative_to(ROOT).as_posix() for p in sorted(MAPS.glob('*.npz'))]
    return {'source_sha256':{'admission_contract/'+p:sha(ROOT/'admission_contract'/p) for p in OWN},
            'dependency_sha256':{p:sha(ROOT/p) for p in DEPENDENCIES},'input_sha256':{p:sha(ROOT/p) for p in paths}}


def timing_backcheck():
    rows=[]
    for path in sorted((ROOT/'duration_contract/results/paced_v1').glob('session_*.json.gz')):
        with gzip.open(path,'rt') as f:r=json.load(f)
        if r['status']!='passed':raise ValueError('Prior invalid session')
        for u in (0,1):
            prior=0
            for j,s in enumerate(r['segments'][u]):
                arrival=r['scripted_arrivals_ticks'][j][u]*1_000_000_000//TICKS
                media=s['duration_ticks']*1_000_000_000//TICKS
                residual=s['end_ns']-max(prior,arrival)-media
                rows.append({'session':r['index'],'user':u,'segment':j+2,'extra_ns':residual,
                             'within_half_second':residual<=500_000_000})
                prior=s['end_ns']
    if len(rows)!=152:raise ValueError('Prior segment count')
    return {'samples':rows,'passes':sum(r['within_half_second'] for r in rows),
            'maximum_extra_ns':max(r['extra_ns'] for r in rows),'establishes_hard_bound':False}


def summarize(rows):
    groups=defaultdict(list)
    for r in rows:
        for g in ('all',r['cohort'],r['scene']):groups[g,r['eta'],r['method']].append(r)
    out=[]
    for (group,eta,method),rs in sorted(groups.items()):
        admitted=[r for r in rs if r['admitted']];good=sum(r['protected_success'] for r in admitted)
        feasible=sum(r['oracle_feasible'] for r in rs) if eta!='unbounded' else None
        out.append({'group':group,'eta':eta,'method':method,'episodes':len(rs),'admitted':len(admitted),
            'success':good,'false_promises':len(admitted)-good,'precision':good/len(admitted) if admitted else None,
            'oracle_feasible':feasible,'feasible_capture':good/feasible if feasible else None,
            'status_counts':dict(Counter(r['status'] for r in rs)),
            'mean_admitted_unpaid':mean(r['score']['deadline_unpaid'] for r in admitted) if admitted else None,
            'extra_bytes':sum(r['extra_bytes'] for r in admitted),
            'floor_failure_admissions':sum(bool(r['score']['recipient_floor_violations']+r['score']['donor_floor_violations']) for r in admitted)})
    return out


def analysis():
    records,_=load();media=media_rows();mapmeta=json.loads((MAPS/'metadata.json').read_text())
    sources={s['scene']:s for s in mapmeta['sources']};cache={};rows=[];bounds=[];checks=Counter()
    with gzip.open(ROOT/'duration_contract/results/replay_v1/results.json.gz','rt') as f:old=json.load(f)
    oldbounds={r['key']:r for r in old['bounds'] if r['mode']=='actual'}
    for record in records:
        scene=record['scene'];ds=durations_for(record,media);entry=entry_inputs(record,ds);loss=entry['loss']
        if scene not in cache:
            path=MAPS/sources[scene]['map_file']
            if sha(path)!=sources[scene]['descriptor']:raise ValueError('Sender map identity')
            maps=np.load(path)['mse'];lower,upper=spatial_bounds(maps)
            arrays=path_arrays(record['costs'],4,record['reserve']);cache[scene]=(maps,lower,upper,arrays)
        maps,lower,upper,arrays=cache[scene];paths=arrays['choices'];costs=record['costs']
        actual=record['quality'][3];actual_delta=actual-actual[:,:,2:3]
        if not ((actual_delta>=lower[:,None,:])&(actual_delta<=upper[:,None,:])).all():
            raise ValueError('Exposed quality outside analytical sender envelope')
        checks['quality_difference_checks']+=actual_delta.size
        predicted=forecast(maps,entry['past_reference_mse']);delta=predicted-predicted[:,:,2:3]
        base={k:record[k] for k in ('key','cohort','scene')}
        for eta in (0,ETA):
            mode='ideal' if eta==0 else 'half_second'
            ends=clocks(costs,paths,ds,eta)
            actual_safe,actual_gain=path_stats(actual_delta,paths,ends,ds)
            oracle_ids=np.flatnonzero(actual_safe & (2*actual_gain>=loss))
            oracle_feasible=bool(len(oracle_ids))
            oracle_max=int(actual_gain[actual_safe].max())
            if eta==0:
                if oracle_feasible!=oldbounds[record['key']]['deadline']['half'] or oracle_max!=oldbounds[record['key']]['deadline']['gain']:
                    raise ValueError('Prior fixed-contract oracle changed')
                checks['old_oracle_parity']+=1
            cert=certificate(lower,upper,costs,arrays,ds,loss,eta)
            scalar=independent(lower,upper,costs,ds,record['reserve'],loss,eta)
            if (cert['upper_credit'],cert['lower_max_credit'],cert['lower_safe_paths'],cert['extra_bytes']) != (scalar['upper_max'],scalar['lower_max'],scalar['safe_paths'],scalar['minimum_cost']):
                raise ValueError('Independent certificate mismatch')
            checks['scalar_certificate_queries']+=1
            if cert['status']=='impossible' and oracle_feasible:raise ValueError('Invalid impossibility certificate')
            bounds.append({**base,'eta':mode,'loss':loss,'oracle_feasible':oracle_feasible,
                'oracle_max_credit':oracle_max,'certificate':cert,'resource_paths':len(paths)})
            predicted_safe,predicted_gain=path_stats(delta,paths,ends,ds)
            lower_safe,lower_gain=path_stats(lower,paths,ends,ds)
            path_index={tuple(p.flat):i for i,p in enumerate(paths)}
            chosen=pick(predicted_gain,predicted_safe,arrays['cost'],loss)
            selections={'point_planner':chosen}
            for method in ('cost_greedy','rolling_nash','maxmin'):
                selected=control_path(method,predicted,costs,ds,record['reserve'],entry['past_psnr'],loss,eta)
                selections[method]=path_index[tuple(selected.flat)]
            def append(method,index,status,claimed):
                admitted=status=='admit'; selected=index if admitted else path_index[(2,2)*4]
                score=account(actual,ds,paths[selected].tolist(),ends[selected].tolist())
                rows.append({**base,'eta':mode,'method':method,'status':status,'admitted':admitted,
                    'proposed_path':paths[index].tolist() if index is not None else None,
                    'executed_path':paths[selected].tolist(),'extra_bytes':int(arrays['cost'][selected]),
                    'claimed_credit':claimed,'oracle_feasible':oracle_feasible,
                    'protected_success':bool(score['protected_half_by_deadline']),'score':score})
                if (method=='certified_planner' or method.endswith('_certified')) and admitted and not score['protected_half_by_deadline']:
                    raise ValueError('Certificate contradicted by a contained trajectory')
            cert_index=path_index[tuple(np.array(cert['path']).flat)] if cert['path'] is not None else None
            append('certified_planner',cert_index,cert['status'],cert['certified_credit'])
            for method,index in selections.items():
                admissible=index is not None and predicted_safe[index] and 2*predicted_gain[index]>=loss
                append(method,index,'admit' if admissible else 'abstain',int(predicted_gain[index]) if index is not None else None)
                gated=index is not None and lower_safe[index] and 2*lower_gain[index]>=loss
                append(method+'_certified',index,'admit' if gated else 'abstain',int(lower_gain[index]) if index is not None else None)
        cert=certificate(lower,upper,costs,arrays,ds,loss,None)
        rows.append({**base,'eta':'unbounded','method':'certified_planner','status':cert['status'],'admitted':False,
                     'protected_success':False,'oracle_feasible':None,'extra_bytes':0,'score':None,'certificate':cert})
    return {'exposed_only':True,'contract_changed':False,'rows':rows,'bounds':bounds,'summary':summarize(rows),
            'checks':dict(checks),'execution_envelope_backcheck':timing_backcheck()}


def report(result):
    lines=['# Feasibility-based admission under the fixed contract','','Conditional engineering certificates; exposed data, not fresh confirmation.','',
           '| Timing | Method | Admit | Success | False promises | Precision | Offline feasible |',
           '|---|---|---:|---:|---:|---:|---:|']
    for r in result['summary']:
        if r['group']=='all':
            precision=f"{r['precision']:.3f}" if r['precision'] is not None else 'undefined'
            lines.append(f"| {r['eta']} | {r['method']} | {r['admitted']} | {r['success']} | {r['false_promises']} | {precision} | {r['oracle_feasible']} |")
    for mode in ('ideal','half_second','unbounded'):
        r=next(r for r in result['summary'] if r['group']=='all' and r['eta']==mode and r['method']=='certified_planner')
        lines+=['',f"{mode} three-way decisions: {r['status_counts']}."]
    b=result['execution_envelope_backcheck']
    lines+=['',f"Prior execution-envelope backcheck: {b['passes']}/152 segments within 0.5s; maximum {b['maximum_extra_ns']/1e9:.9f}s. This is not a universal upper bound.",'']
    return '\n'.join(lines)


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();prov=provenance()
    if a.verify:
        meta=json.loads((OUT/'metadata.json').read_text())
        if any(meta[k]!=v for k,v in prov.items()):raise ValueError('Frozen provenance changed')
    elif OUT.exists():p.error('Preserve prior results')
    result=analysis();digest=hashlib.sha256(canonical(result)).hexdigest();text=report(result)
    if a.verify:
        with gzip.open(OUT/'results.json.gz','rt') as f:saved=json.load(f)
        if saved!=result or meta['scientific_sha256']!=digest or (OUT/'REPORT.md').read_text()!=text:raise ValueError('Replay differs')
    else:
        OUT.mkdir(parents=True);(OUT/'results.json.gz').write_bytes(gzip.compress(canonical(result),mtime=0))
        (OUT/'REPORT.md').write_text(text);(OUT/'metadata.json').write_text(json.dumps({**prov,'scientific_sha256':digest},indent=2)+'\n')
    print(json.dumps({'verified':a.verify,'scientific_sha256':digest,'rows':len(result['rows']),'checks':result['checks']}))
