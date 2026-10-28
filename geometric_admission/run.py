"""Complete geometric-envelope admission replay; preserve all frozen baselines."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from statistics import mean
import numpy as np
from metric_contract.data import ROOT,load
from metric_contract.core import path_arrays
from metric_contract.run import sha,canonical
from duration_contract.core import account
from duration_contract.run import media_rows,durations_for
from admission_contract.core import spatial_bounds,entry_inputs,certificate,independent,clocks,path_stats,ETA
from admission_contract.run import provenance as prior_provenance,summarize
from admission_contract.diagnose import independent_score
from geometric_admission.geometry import family,validate_family,bounds,check_extrema

OUT=ROOT/'geometric_admission/results/exposed_v1'
PRIOR=ROOT/'admission_contract/results/exposed_v1'
MAPS=ROOT/'feedback_opportunity/data/maps_v1'
OWN=('__init__.py','geometry.py','run.py','test_geometry.py','PLAN.md')
POINT=('point_planner','cost_greedy','rolling_nash','maxmin')


def provenance():
    previous=prior_provenance();saved=json.loads((PRIOR/'metadata.json').read_text())
    if any(saved[k]!=v for k,v in previous.items()):raise ValueError('Previous method/input changed')
    return {'source_sha256':{'geometric_admission/'+p:sha(ROOT/'geometric_admission'/p) for p in OWN},
            'prior_binding':previous,'prior_results_sha256':sha(PRIOR/'results.json.gz'),
            'dependency_sha256':{p:sha(ROOT/p) for p in ('feedback_opportunity/feedback.py',
                'admission_contract/core.py','admission_contract/run.py','admission_contract/diagnose.py',
                'multimedia_testbed/prepare_qoevave.py')}}


def analysis():
    records,_=load();media=media_rows();masks=family();checks=Counter(validate_family(masks))
    with gzip.open(PRIOR/'results.json.gz','rt') as f:previous=json.load(f)
    prior_rows={(r['key'],r['eta'],r['method']):r for r in previous['rows']}
    prior_bounds={(b['key'],b['eta']):b for b in previous['bounds']}
    cache={};scenes=[];rows=[];bounds_rows=[]
    metadata=json.loads((MAPS/'metadata.json').read_text());sources={s['scene']:s for s in metadata['sources']}
    for record in records:
        scene=record['scene'];base={k:record[k] for k in ('key','cohort','scene')};ds=durations_for(record,media)
        # The entry API projects only completed-event history, never future labels.
        loss=entry_inputs(record,ds)['loss']
        if scene not in cache:
            path=MAPS/sources[scene]['map_file']
            if sha(path)!=sources[scene]['descriptor']:raise ValueError('Map hash mismatch')
            maps=np.load(path)['mse'];lo,hi,witness=bounds(maps,masks);oldlo,oldhi=spatial_bounds(maps)
            if (lo<oldlo).any() or (hi>oldhi).any():raise ValueError('Envelope widened')
            validation=check_extrema(maps,masks,lo,hi,witness)
            checks.update({k:v for k,v in validation.items() if k!='passed'})
            arrays=path_arrays(record['costs'],4,record['reserve']);cache[scene]=(lo,hi,arrays)
            scenes.append({'scene':scene,'lower':lo.tolist(),'upper':hi.tolist(),'convex_lower':oldlo.tolist(),
                'convex_upper':oldhi.tolist(),'extremal_mask_witnesses':witness,'validation':validation})
        lo,hi,arrays=cache[scene];paths=arrays['choices'];costs=record['costs'];actual=record['quality'][3]
        delta=actual-actual[:,:,2:3]
        if not ((delta>=lo[:,None,:])&(delta<=hi[:,None,:])).all():raise ValueError('Actual quality outside geometry envelope')
        checks['actual_difference_checks']+=delta.size
        index={tuple(p.flat):i for i,p in enumerate(paths)}
        for eta in (0,ETA):
            mode='ideal' if eta==0 else 'half_second';ends=clocks(costs,paths,ds,eta)
            cert=certificate(lo,hi,costs,arrays,ds,loss,eta)
            scalar=independent(lo,hi,costs,ds,record['reserve'],loss,eta)
            if (cert['lower_max_credit'],cert['upper_credit'],cert['lower_safe_paths'],cert['extra_bytes']) != (scalar['lower_max'],scalar['upper_max'],scalar['safe_paths'],scalar['minimum_cost']):
                raise ValueError('Independent certificate mismatch')
            checks['scalar_certificate_queries']+=1
            old=prior_bounds[record['key'],mode];oldcert=old['certificate']
            if cert['lower_max_credit']<oldcert['lower_max_credit'] or cert['upper_credit']>oldcert['upper_credit']:
                raise ValueError('Certificate extrema not nested')
            if oldcert['status']=='admit' and cert['status']!='admit':raise ValueError('Lost previous admission')
            if oldcert['status']=='impossible' and cert['status']!='impossible':raise ValueError('Lost previous rejection')
            safe,gain=path_stats(delta,paths,ends,ds);feasible=bool(np.any(safe & (2*gain>=loss)))
            if feasible!=old['oracle_feasible'] or int(gain[safe].max())!=old['oracle_max_credit']:
                raise ValueError('Fixed-contract oracle changed')
            checks['oracle_parity_queries']+=1
            if cert['status']=='impossible' and feasible:raise ValueError('False impossibility certificate')
            bounds_rows.append({**base,'eta':mode,'loss':loss,'certificate':cert,'convex_certificate':oldcert,
                'oracle_feasible':feasible,'oracle_max_credit':old['oracle_max_credit']})
            lowsafe,lowgain=path_stats(lo,paths,ends,ds)
            def make_row(method,pid,status,credit):
                admitted=status=='admit';executed=pid if admitted else index[(2,2)*4]
                score=account(actual,ds,paths[executed].tolist(),ends[executed].tolist())
                independent_result,spent=independent_score(record,ds,paths[executed].tolist(),eta)
                if independent_result!=score or spent!=int(arrays['cost'][executed]):raise ValueError('Independent ledger mismatch')
                checks['independent_ledger_checks']+=1
                if admitted and not score['protected_half_by_deadline']:raise ValueError('Contained trajectory violates certificate')
                return {**base,'eta':mode,'method':method,'status':status,'admitted':admitted,
                    'proposed_path':paths[pid].tolist() if pid is not None else None,'executed_path':paths[executed].tolist(),
                    'extra_bytes':spent,'claimed_credit':credit,'oracle_feasible':feasible,
                    'protected_success':bool(score['protected_half_by_deadline']),'score':score}
            pid=index[tuple(np.array(cert['path']).flat)] if cert['path'] is not None else None
            rows.append(make_row('certified_planner',pid,cert['status'],cert['certified_credit']))
            for method in POINT:
                # These historical controls were causally generated from past-only
                # inputs; copy them exactly rather than retuning them after results.
                oldrow=prior_rows[record['key'],mode,method]
                independent_result,spent=independent_score(record,ds,oldrow['executed_path'],eta)
                if independent_result!=oldrow['score'] or spent!=oldrow['extra_bytes']:raise ValueError('Control ledger changed')
                checks['independent_ledger_checks']+=1;checks['unchanged_point_controls']+=1
                rows.append(oldrow)
                selected=oldrow['proposed_path'];pid=index[tuple(np.array(selected).flat)] if selected is not None else None
                admit=pid is not None and lowsafe[pid] and 2*lowgain[pid]>=loss
                rows.append(make_row(method+'_certified',pid,'admit' if admit else 'abstain',int(lowgain[pid]) if pid is not None else None))
        cert=certificate(lo,hi,costs,arrays,ds,loss,None)
        rows.append({**base,'eta':'unbounded','method':'certified_planner','status':cert['status'],'admitted':False,
            'protected_success':False,'oracle_feasible':None,'extra_bytes':0,'score':None,'certificate':cert})
    return {'exposed_only':True,'contract_changed':False,'viewport_model':'existing 100x100-degree tile-centre angular rectangle; not physical HMD',
        'family':masks,'scene_envelopes':scenes,'rows':rows,'bounds':bounds_rows,'summary':summarize(rows),'checks':dict(checks)}


def report(result):
    lines=['# Geometric viewport admission under the fixed contract','',result['viewport_model'],'',
        '| Timing | Method | Admitted | Fulfilled in replay | False promises | Precision |',
        '|---|---|---:|---:|---:|---:|']
    for r in result['summary']:
        if r['group']=='all':
            precision=f"{r['precision']:.3f}" if r['precision'] is not None else 'undefined'
            lines.append(f"| {r['eta']} | {r['method']} | {r['admitted']} | {r['success']} | {r['false_promises']} | {precision} |")
    for mode in ('ideal','half_second','unbounded'):
        summary=next(r for r in result['summary'] if r['group']=='all' and r['eta']==mode and r['method']=='certified_planner')
        lines.extend(['',f"{mode} three-way counts: {summary['status_counts']}."])
    lines.extend(['',f"Complete family: {len(result['family'])} distinct masks. All bounds, extrema and retained controls verified.",''])
    return '\n'.join(lines)


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args();prov=provenance()
    if a.verify:
        meta=json.loads((OUT/'metadata.json').read_text())
        if any(meta[k]!=v for k,v in prov.items()):raise ValueError('Frozen provenance mismatch')
    elif OUT.exists():p.error('Preserve previous results')
    result=analysis();digest=hashlib.sha256(canonical(result)).hexdigest();text=report(result)
    if a.verify:
        with gzip.open(OUT/'results.json.gz','rt') as f:saved=json.load(f)
        if result!=saved or digest!=meta['scientific_sha256'] or (OUT/'REPORT.md').read_text()!=text:raise ValueError('Scientific replay mismatch')
    else:
        OUT.mkdir(parents=True);(OUT/'results.json.gz').write_bytes(gzip.compress(canonical(result),mtime=0))
        (OUT/'REPORT.md').write_text(text);(OUT/'metadata.json').write_text(json.dumps({**prov,'scientific_sha256':digest},indent=2)+'\n')
    print(json.dumps({'verified':a.verify,'scientific_sha256':digest,'rows':len(result['rows']),'checks':result['checks']}))
