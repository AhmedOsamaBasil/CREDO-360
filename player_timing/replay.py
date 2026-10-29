"""All exposed matched paths; separate original and secondary quality accounts."""
import argparse
from collections import defaultdict
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean
from metric_contract.data import ROOT,load,INPUTS
from metric_contract.run import canonical,sha
from duration_contract.core import account,TICKS
from duration_contract.run import media_rows,durations_for
from admission_contract.core import clocks
from player_timing.core import receipt_schedule,queue,resources,scores
import numpy as np

DATA=ROOT/'player_timing/data/v1/derived.json.gz'
OUT=ROOT/'player_timing/results/replay_v1'
POLICIES=('cost_greedy','rolling_nash','maxmin')
METHOD=('PLAN.md','core.py','prepare.py','replay.py','player.js','service.cjs','measure.cjs','audit.py','test_core.py','test_service.cjs')


def provenance():
    paths=list(INPUTS)+['admission_contract/results/exposed_v1/results.json.gz',
        'duration_contract/data/media_v1/timelines.json.gz','feedback_opportunity/data/maps_v1/metadata.json']
    return {'method_sha256':{p:sha(ROOT/'player_timing'/p) for p in METHOD},
            'input_sha256':{p:sha(ROOT/p) for p in paths},'derived_sha256':sha(DATA)}


def cases():
    records,_=load(); oldmedia=media_rows()
    with gzip.open(DATA,'rt') as f:derived=json.load(f)
    with gzip.open(ROOT/'admission_contract/results/exposed_v1/results.json.gz','rt') as f:old=json.load(f)
    paths={(r['key'],r['method']):r for r in old['rows'] if r['eta']=='ideal' and r['method'] in POLICIES}
    media={(r['cohort'],r['scene'],r['segment'],r['rung']):r for r in derived['rows']}
    quality={r['key']:r['negative_micro_mse'] for r in derived['quality']['rows']}
    out=[]; parity=0; gated=0
    for record in records:
        ds=durations_for(record,oldmedia); q=record['quality'][3]
        loss=sum(max(0,int(q[t,0,2]-q[t,0,0]))*ds[t] for t in (0,1))
        for policy in POLICIES+('baseline',):
            path=paths[record['key'],policy]['proposed_path'] if policy!='baseline' else [[2,2]]*4
            if path is None:raise ValueError('Missing proposed path')
            pg=[max(0,int(q[t,0,path[t-2][0]]-q[t,0,2]))*ds[t] for t in range(2,6)]
            pf=[sum(int(q[t,u,path[t-2][u]]<q[t,u,2]) for t in range(2,6)) for u in (0,1)]
            for unit in (10,2):
                units=[]; cg=[]; cf=[0,0]; sizes=[]; bases=[]
                for parent in range(4):
                    t=parent+2; pair=path[parent]
                    for child in range(1 if unit==10 else 5):
                        selected=[]; base=[]
                        for u,rung in enumerate(pair):
                            item=media[record['cohort'],record['scene'],t,rung]
                            ref=media[record['cohort'],record['scene'],t,2]
                            if unit==2:
                                f=item['children'][child];b=ref['children'][child]
                                selected.append({**f,'cache':'split'});base.append(b['bytes'])
                            else:
                                selected.append({'bytes':item['bytes'],'sha256':item['sha256'],
                                    'relative_path':item['relative_path'],'duration':item['duration'],
                                    'frames':item['packets'],'cache':'original'})
                                base.append(ref['bytes'])
                        dur=selected[0]['duration']
                        if selected[1]['duration']!=dur:raise ValueError('Duration mismatch')
                        units.append({'parent':parent,'child':child,'duration':dur,'files':selected})
                        sizes.append([f['bytes'] for f in selected]);bases.append([base[0],base[1]])
                        if unit==10:cg.append(pg[parent])
                        else:
                            v=quality[record['key']][parent*5+child]
                            cg.append(max(0,v[0][pair[0]]-v[0][2])*round(dur*TICKS))
                            for u in (0,1):cf[u]+=int(v[u][pair[u]]<v[u][2])
                if unit==10:cf=pf.copy()
                resource=resources(sizes,bases,[u['parent'] for u in units],record['reserve'])
                for buffered in (False,True):
                    case={'key':record['key'],'scene':record['scene'],'policy':policy,'unit_seconds':unit,
                        'buffered':buffered,'path':path,'units':units,'sizes':sizes,'baseline_sizes':bases,
                        'loss':loss,'parent_gains':pg,'parent_floor_violations':pf,
                        'chunk_gains':cg,'chunk_floor_violations':cf,'resource':resource}
                    requests,arrivals=receipt_schedule(sizes,unit)
                    ends,gate=queue(arrivals,[u['duration'] for u in units],buffered)
                    result=scores(case,ends,resource)
                    if unit==10 and not buffered:
                        integer=clocks(record['costs'],np.array([path]),ds,0)[0]
                        if max(abs(a-b/TICKS) for es,ts in zip(ends,integer) for a,b in zip(es,ts))>1e-8:
                            raise ValueError('Original clock differs')
                        score=account(q,ds,path,integer)
                        if abs(result['original_parent_account']['fraction_repaid']-(1-score['deadline_unpaid']))>1e-11:
                            raise ValueError('Original score differs')
                        parity+=1
                        if policy!='baseline' and path==paths[record['key'],policy]['executed_path']:
                            if score!=paths[record['key'],policy]['score']:raise ValueError('Published gate score differs')
                            gated+=1
                    case['ideal']={'requests':requests,'arrivals':arrivals,'ends':ends,'buffer_gate':gate,**result}
                    out.append(case)
    return out,{'independent_original_clock_and_score':parity,'published_executed_score':gated}


def schedule(allcases):
    selected=[r for r in allcases if r['key'].endswith(':1:2') and r['policy'] in POLICIES]
    rows=[]
    for i,scene in enumerate(sorted({r['scene'] for r in selected})):
        cells=sorted((r for r in selected if r['scene']==scene),key=lambda r:(POLICIES.index(r['policy']),r['unit_seconds'],r['buffered']))
        cells=cells[i:]+cells[:i]
        for r in cells:rows.append({**r,'control':'none','index':len(rows)})
    base=next(r for r in selected if r['scene']=='ParkFountains01' and r['policy']=='cost_greedy' and r['unit_seconds']==2 and not r['buffered'])
    for control in ('late_recipient','background'):rows.append({**base,'control':control,'index':len(rows)})
    if len(rows)!=74:raise ValueError('Fixed 74-session schedule')
    return rows


def summary(rows):
    groups=defaultdict(list)
    for r in rows:
        for scene in ('all',r['scene']):groups[scene,r['policy'],r['unit_seconds'],r['buffered']].append(r)
    result=[]
    for (scene,p,u,b),rs in sorted(groups.items()):
        row={'scene':scene,'policy':p,'unit_seconds':u,'buffered':b,'episodes':len(rs),
             'reserve_failures':sum(not r['resource']['reserve_ok'] for r in rs),
             'cap_failures':sum(not r['resource']['cap_ok'] for r in rs),
             'mean_recipient_finish':mean(r['ideal']['ends'][-1][0] for r in rs)}
        for name in ('original_parent_account','secondary_chunk_account'):
            ss=[r['ideal'][name] for r in rs]
            row[name]={'half':sum(s['half'] for s in ss),'protected_half':sum(s['resource_protected_half'] for s in ss),
                'mean_repaid':mean(s['fraction_repaid'] for s in ss),
                'floor_violations':[sum(s['floor_violations'][v] for s in ss) for v in (0,1)]}
        result.append(row)
    return result


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    rows,checks=cases();result={'rows':rows,'checks':checks,'summary':summary(rows)}
    digest=hashlib.sha256(canonical(result)).hexdigest();meta={**provenance(),'scientific_sha256':digest}
    if a.verify:
        with gzip.open(OUT/'results.json.gz','rt') as f:saved=json.load(f)
        if result!=saved or meta!=json.loads((OUT/'metadata.json').read_text()):raise ValueError('Replay/provenance changed')
    else:
        OUT.mkdir(parents=True,exist_ok=False)
        (OUT/'results.json.gz').write_bytes(gzip.compress(canonical(result),mtime=0))
        (OUT/'schedule.json').write_bytes(canonical(schedule(rows)))
        (OUT/'metadata.json').write_bytes(canonical(meta))
    print(json.dumps({'verified':a.verify,'sha256':digest,'rows':len(rows),'checks':checks}))


if __name__=='__main__':main()
