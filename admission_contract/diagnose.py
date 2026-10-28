"""Post-outcome independent ledgers and concentration/abstention diagnostics."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from statistics import mean
import numpy as np
from metric_contract.data import ROOT,load
from metric_contract.core import TICKS,CAP,path_arrays
from metric_contract.run import sha,canonical
from duration_contract.run import media_rows,durations_for
from admission_contract.core import spatial_bounds,clocks,path_stats,ETA

SOURCE=ROOT/'admission_contract/results/exposed_v1/results.json.gz'
OUT=ROOT/'admission_contract/results/diagnostics_v1'


def independent_score(record,durations,path,eta):
    q=record['quality'][3];start=0;finish=[0,0];spent=credit=eventual=0;floors=[0,0];gains=[]
    loss=sum(max(0,int(q[t,0,2]-q[t,0,0]))*durations[t] for t in (0,1))
    for t,(a,b) in zip(range(2,6),path):
        if min(a,b)<2 or max(a,b)>5:raise ValueError('Rung bounds')
        sa,sb=int(record['costs'][t,a]),int(record['costs'][t,b]);total=sa+sb
        if total>CAP:raise ValueError('Cap')
        spent+=max(0,total-2*int(record['costs'][t,2]))
        if spent>record['reserve']:raise ValueError('Reserve')
        arrivals=[start+19500+min(2*n,total) for n in (sa,sb)]
        finish=[max(finish[u],arrivals[u])+durations[t]+eta for u in (0,1)]
        start=max(start+10*TICKS,*arrivals)
        gain=max(0,int(q[t,0,a]-q[t,0,2]))*durations[t];gains.append(gain);eventual+=gain
        if finish[0]<=40*TICKS:credit+=gain
        for u,r in enumerate((a,b)):floors[u]+=int(q[t,u,r]<q[t,u,2])
    half=bool(2*credit>=loss)
    return {'loss_micro_mse_ticks':loss,'segment_gain_micro_mse_ticks':gains,
        'deadline_credit':min(loss,credit),'eventual_credit':min(loss,eventual),
        'deadline_unpaid':round(max(0,loss-credit)/loss,12),'eventual_unpaid':round(max(0,loss-eventual)/loss,12),
        'half_by_deadline':half,'protected_half_by_deadline':half and not any(floors),
        'recipient_floor_violations':floors[0],'donor_floor_violations':floors[1]},spent


def analysis():
    with gzip.open(SOURCE,'rt') as f:result=json.load(f)
    records,_=load();lookup={r['key']:r for r in records};media=media_rows();audited=0;floor_db=[]
    for r in result['rows']:
        if r['eta']=='unbounded':continue
        record=lookup[r['key']];ds=durations_for(record,media)
        score,spent=independent_score(record,ds,r['executed_path'],0 if r['eta']=='ideal' else ETA)
        if score!=r['score'] or spent!=r['extra_bytes'] or score['protected_half_by_deadline']!=r['protected_success']:
            raise ValueError('Independent outcome/resource mismatch')
        audited+=1
        if r['method']=='rolling_nash' and r['eta']=='half_second' and r['admitted']:
            for t,pair in zip(range(2,6),r['executed_path']):
                for u,level in enumerate(pair):
                    q=record['quality'];loss_db=(int(q[2,t,u,2])-int(q[2,t,u,level]))/1e6
                    if loss_db>0:floor_db.append(loss_db)
    primary=[r for r in result['rows'] if r['method']=='point_planner' and r['eta']=='half_second']
    greedy={r['key']:r for r in result['rows'] if r['method']=='cost_greedy' and r['eta']=='half_second'}
    admitted=[r for r in primary if r['admitted']]
    bounds={r['key']:r for r in result['bounds'] if r['eta']=='half_second'}
    failures=[{'key':r['key'],'predicted_repayment':r['claimed_credit']/r['score']['loss_micro_mse_ticks'],
              'actual_repayment':1-r['score']['deadline_unpaid'],
              'offline_best_repayment':bounds[r['key']]['oracle_max_credit']/bounds[r['key']]['loss'],
              'floor_losses':r['score']['donor_floor_violations']+r['score']['recipient_floor_violations']}
             for r in admitted if not r['protected_success']]
    scene_rows=[]
    for scene in sorted(set(r['scene'] for r in records)):
        record=next(r for r in records if r['scene']==scene);ds=durations_for(record,media)
        maps=np.load(ROOT/'feedback_opportunity/data/maps_v1'/f'{scene}.npz')['mse'];lower,_=spatial_bounds(maps)
        arrays=path_arrays(record['costs'],4,record['reserve']);ends=clocks(record['costs'],arrays['choices'],ds,ETA)
        _,gain=path_stats(lower,arrays['choices'],ends,ds)
        entries=[b for b in bounds.values() if b['scene']==scene]
        scene_rows.append({'scene':scene,'episodes':len(entries),'oracle_feasible':sum(b['oracle_feasible'] for b in entries),
            'status_counts':dict(Counter(b['certificate']['status'] for b in entries)),
            'mean_safe_lower_repayment':mean(b['certificate']['lower_max_credit']/b['loss'] for b in entries),
            'mean_floor_relaxed_lower_repayment':mean(int(gain.max())/b['loss'] for b in entries),
            'mean_actual_offline_repayment':mean(b['oracle_max_credit']/b['loss'] for b in entries),
            'mean_optimistic_upper_repayment':mean(b['certificate']['upper_credit']/b['loss'] for b in entries)})
    return {'posthoc':True,'controller_changed':False,'independent_score_resource_checks':audited,
        'same_point_greedy_admissions':sum(r['admitted']==greedy[r['key']]['admitted'] for r in primary),
        'same_point_greedy_executed_paths':sum(r['executed_path']==greedy[r['key']]['executed_path'] for r in primary),
        'admission_scenes':dict(Counter(r['scene'] for r in admitted)),
        'unique_admitted_paths':len({tuple(np.array(r['executed_path']).flat) for r in admitted}),
        'admitted_path':admitted[0]['executed_path'] if admitted else None,'false_promises':failures,
        'rolling_nash_floor_event_count':len(floor_db),'rolling_nash_max_floor_loss_db':max(floor_db,default=0),
        'rolling_nash_mean_floor_loss_db':mean(floor_db) if floor_db else None,
        'scenes':scene_rows,'policy_summary':[r for r in result['summary'] if r['group']=='all' and r['eta']=='half_second'],
        'source_sha256':{p:sha(ROOT/'admission_contract'/p) for p in ('diagnose.py','test_validation.py')},
        'primary_result_sha256':sha(SOURCE)}


def figures(result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4.1),layout='constrained')
    names=['Certified','Point planner','Cost-greedy','Rolling Nash','Max-min']
    byname={r['method']:r for r in result['policy_summary']}
    methods=['certified_planner','point_planner','cost_greedy','rolling_nash','maxmin']
    good=[byname[n]['success'] for n in methods];bad=[byname[n]['false_promises'] for n in methods]
    axes[0].bar(names,good,label='Fulfilled',color='#256b8a')
    axes[0].bar(names,bad,bottom=good,label='False promise',color='#b6513e')
    axes[0].set_ylabel('Admitted requests (out of 168)');axes[0].tick_params(axis='x',rotation=25)
    axes[0].set_title('A. Fixed contract; 0.5 s execution allowance');axes[0].legend()
    axes[0].text(0,2,'0 admitted\nprecision undefined',ha='center',fontsize=8)
    rows=result['scenes'];x=list(range(len(rows)))
    for key,label,color in [('mean_safe_lower_repayment','Certified lower','#256b8a'),
                            ('mean_actual_offline_repayment','Actual future-known','#66774c'),
                            ('mean_optimistic_upper_repayment','Optimistic upper','#b6513e')]:
        axes[1].plot(x,[r[key] for r in rows],'o-',label=label,color=color)
    axes[1].axhline(.5,ls='--',color='gray',label='Half-repayment target')
    axes[1].set_xticks(x,[r['scene'] for r in rows],rotation=30,ha='right',fontsize=8)
    axes[1].set_ylabel('Mean credit / initial debt (uncapped)');axes[1].set_title('B. Scene-level bounds; not confidence intervals')
    axes[1].legend(fontsize=8)
    fig.savefig(OUT/'admission.png',dpi=180);fig.savefig(OUT/'admission.svg',metadata={'Date':None});plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    result=analysis();digest=hashlib.sha256(canonical(result)).hexdigest()
    if a.verify:
        meta=json.loads((OUT/'metadata.json').read_text())
        if json.loads((OUT/'results.json').read_text())!=result or meta['scientific_sha256']!=digest:raise ValueError('Diagnostics mismatch')
        for name,value in meta['figures'].items():
            if sha(OUT/name)!=value:raise ValueError('Figure mismatch')
    else:
        OUT.mkdir(parents=True,exist_ok=False);(OUT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        figures(result);(OUT/'metadata.json').write_text(json.dumps({'scientific_sha256':digest,
            'figures':{p.name:sha(p) for p in OUT.glob('admission.*')}},indent=2)+'\n')
    print(json.dumps({'verified':a.verify,'scientific_sha256':digest,'checks':result['independent_score_resource_checks'],
        'point_greedy_path_agreement':result['same_point_greedy_executed_paths'],'false_promises':result['false_promises']}))
