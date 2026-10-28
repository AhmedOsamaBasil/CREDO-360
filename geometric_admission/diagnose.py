"""Post-outcome nesting, concentration and fixed-path worst-case diagnostics."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from statistics import mean
import numpy as np
from metric_contract.data import ROOT,load
from metric_contract.core import path_arrays
from metric_contract.run import canonical,sha
from duration_contract.run import media_rows,durations_for
from admission_contract.core import clocks,path_stats,ETA
from admission_contract.diagnose import independent_score
from geometric_admission.geometry import matrix

SOURCE=ROOT/'geometric_admission/results/exposed_v1/results.json.gz'
OUT=ROOT/'geometric_admission/results/diagnostics_v1'


def upper_on_worst(lower):
    """Five micro-MSE units cover outward guard and separate native rounding.
    Used only as a diagnostic upper bound; never relax an admission floor."""
    result=np.array(lower,dtype=np.int64)+5
    result[:,2]=0
    return result


def constructed_quality(record,maps,weights,witness,path):
    """Synthetic future masks, not observed human trajectories; past ledger fixed."""
    q=record['quality'].copy();ids=[]
    for t,pair in zip(range(2,6),path):
        selected=[witness['minimum_mask_id'][pair[0]][s] for s in range(t*10,(t+1)*10)]
        ids.append(selected)
        for u,chosen in ((0,selected),(1,[0]*10)):
            ws=weights[chosen]
            mse=np.sum(maps[:,t*10:(t+1)*10,:].astype(float)*ws[None,:,:],axis=2).mean(axis=1)
            q[3,t,u,:]=-np.floor(mse*1e6+.5).astype(np.int64)
    return {**record,'quality':q},ids


def analysis():
    with gzip.open(SOURCE,'rt') as f:result=json.load(f)
    records,_=load();lookup={r['key']:r for r in records};media=media_rows();weights=matrix(result['family'])
    scenes={r['scene']:r for r in result['scene_envelopes']};cache={};proofs=[]
    for b in result['bounds']:
        if b['eta']!='half_second':continue
        record=lookup[b['key']];ds=durations_for(record,media);scene=record['scene'];saved=scenes[scene]
        if scene not in cache:
            arrays=path_arrays(record['costs'],4,record['reserve']);ends=clocks(record['costs'],arrays['choices'],ds,ETA)
            _,upper_gain=path_stats(upper_on_worst(saved['lower']),arrays['choices'],ends,ds)
            best=int(min(range(len(upper_gain)),key=lambda i:(-int(upper_gain[i]),int(arrays['cost'][i]),i)))
            maps=np.load(ROOT/'feedback_opportunity/data/maps_v1'/f'{scene}.npz')['mse']
            cache[scene]=(arrays['choices'][best].tolist(),int(upper_gain[best]),maps)
        path,maximum,maps=cache[scene]
        artificial,ids=constructed_quality(record,maps,weights,saved['extremal_mask_witnesses'],path)
        scored,_=independent_score(artificial,ds,path,ETA)
        if scored['deadline_credit']>maximum:raise ValueError('Constructed worst-case exceeds upper bound')
        proofs.append({'key':b['key'],'scene':scene,'loss':b['loss'],
            'best_worst_case_credit_upper':maximum,'half_impossible_for_every_precommitted_path':2*maximum<b['loss'],
            'relaxed_upper_maximizing_path':path,'constructed_recipient_mask_ids':ids,
            'constructed_repayment':1-scored['deadline_unpaid'],
            'constructed_future_is_observed_human_data':False})
    summaries=[]
    for scene in sorted(scenes):
        bs=[r for r in result['bounds'] if r['scene']==scene and r['eta']=='half_second']
        ps=[p for p in proofs if p['scene']==scene];s=scenes[scene]
        # Four recovery segments, three upgraded rungs. Exclude reference zeros.
        oldwidth=np.array(s['convex_upper'])[2:,3:]-np.array(s['convex_lower'])[2:,3:]
        newwidth=np.array(s['upper'])[2:,3:]-np.array(s['lower'])[2:,3:]
        summaries.append({'scene':scene,'episodes':len(bs),'convex_status':dict(Counter(r['convex_certificate']['status'] for r in bs)),
            'geometric_status':dict(Counter(r['certificate']['status'] for r in bs)),
            'mean_convex_lower_repayment':mean(r['convex_certificate']['lower_max_credit']/r['loss'] for r in bs),
            'mean_geometric_lower_repayment':mean(r['certificate']['lower_max_credit']/r['loss'] for r in bs),
            'mean_convex_upper_repayment':mean(r['convex_certificate']['upper_credit']/r['loss'] for r in bs),
            'mean_geometric_upper_repayment':mean(r['certificate']['upper_credit']/r['loss'] for r in bs),
            'mean_actual_oracle_repayment':mean(r['oracle_max_credit']/r['loss'] for r in bs),
            'mean_relative_width_reduction':float(np.mean(1-newwidth/oldwidth)),
            'mean_upper_on_best_worst_repayment':mean(p['best_worst_case_credit_upper']/p['loss'] for p in ps)})
    bs=[b for b in result['bounds'] if b['eta']=='half_second']
    return {'posthoc':True,'method_retuned':False,'scenes':summaries,'constructed_witnesses':proofs,
        'new_impossibility_keys':[b['key'] for b in bs if b['convex_certificate']['status']!='impossible' and b['certificate']['status']=='impossible'],
        'unconditional_precommitted_half_impossible':sum(p['half_impossible_for_every_precommitted_path'] for p in proofs),
        'largest_upper_on_best_worst_repayment':max(p['best_worst_case_credit_upper']/p['loss'] for p in proofs),
        'primary_sha256':sha(SOURCE),'source_sha256':{n:sha(ROOT/'geometric_admission'/n) for n in ('diagnose.py','test_validation.py')}}


def figure(result):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(11,4.3),layout='constrained');rows=result['scenes'];x=np.arange(len(rows))
    for key,label,color in [('mean_convex_lower_repayment','All-convex lower','#97a6b8'),
                            ('mean_geometric_lower_repayment','Geometric lower','#256b8a'),
                            ('mean_actual_oracle_repayment','Actual future-known','#66774c')]:
        axes[0].plot(x,[r[key] for r in rows],'o-',label=label,color=color)
    axes[0].axhline(.5,ls='--',color='#b6513e',label='Unchanged target')
    axes[0].set_title('A. Repayment bounds on exposed scenes');axes[0].set_ylabel('Mean credit / initial debt')
    axes[0].set_xticks(x,[r['scene'] for r in rows],rotation=30,ha='right',fontsize=8);axes[0].legend(fontsize=8)
    statuses=['impossible','abstain','admit'];colors=['#b6513e','#97a6b8','#256b8a'];bottom=[0,0]
    for name,color in zip(statuses,colors):
        counts=[sum(r[key].get(name,0) for r in rows) for key in ('convex_status','geometric_status')]
        axes[1].bar(['All-convex','Geometric'],counts,bottom=bottom,label=name.capitalize(),color=color)
        for i,n in enumerate(counts):
            if n:axes[1].text(i,bottom[i]+n/2,str(n),ha='center',va='center',color='white')
        bottom=[a+b for a,b in zip(bottom,counts)]
    axes[1].set_title('B. Tighter rejection, still no admissions');axes[1].set_ylabel('Episodes (out of 168)');axes[1].legend(fontsize=8)
    fig.savefig(OUT/'geometric_bounds.png',dpi=180);fig.savefig(OUT/'geometric_bounds.svg',metadata={'Date':None});plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    result=analysis();digest=hashlib.sha256(canonical(result)).hexdigest()
    if a.verify:
        meta=json.loads((OUT/'metadata.json').read_text())
        with gzip.open(OUT/'results.json.gz','rt') as f:saved=json.load(f)
        if saved!=result or meta['scientific_sha256']!=digest:raise ValueError('Diagnostic replay mismatch')
        for name,value in meta['figures'].items():
            if sha(OUT/name)!=value:raise ValueError('Figure mismatch')
    else:
        OUT.mkdir(parents=True,exist_ok=False);(OUT/'results.json.gz').write_bytes(gzip.compress(canonical(result),mtime=0))
        figure(result);(OUT/'metadata.json').write_text(json.dumps({'scientific_sha256':digest,'figures':{p.name:sha(p) for p in OUT.glob('geometric_bounds.*')}},indent=2)+'\n')
    print(json.dumps({'verified':a.verify,'scientific_sha256':digest,'new_rejections':len(result['new_impossibility_keys']),
        'precommitted_robust_half_impossible':result['unconditional_precommitted_half_impossible'],
        'largest_robust_upper_repayment':result['largest_upper_on_best_worst_repayment']}))
