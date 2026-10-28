"""Post-hoc mechanism diagnosis; does not change the frozen method or screen."""
import argparse
import gzip
import json
from pathlib import Path
from statistics import mean,median
from early_commitment.run import ROOT,OUT,DATA,contexts
from feedback_opportunity.frontier import periods,dp
from reserve_recovery.run import sha

DEST=ROOT/'early_commitment/results/diagnostics_v1'


def derive():
    with gzip.open(OUT/'results.json.gz','rt') as f: raw=json.load(f)
    records,feedback,forecasts,old=contexts(); records={r.key:r for r in records}
    complete=0
    for key,table in forecasts.items():
        cohort,scene,sid=key.split(':'); assert len(table)==60
        for h,projection in enumerate(table):
            assert len(projection)==6 and all(len(q)==6 for q in projection)
            assert all(1000<=q<=5000 for row in projection for q in row)
        for t in range(6):
            assert tuple(table[(t+1)*10-1][t])==feedback[cohort,scene,int(sid),t]
            complete+=1
    assert complete==1008
    rows=raw['rows']; primary=[r for r in rows if r['policy']=='prefix_mpc' and r['delay']==.08]
    lookup={(r['key'],r['policy'],r['delay']):r for r in rows}
    contrasts=[]; regrets=[]; violations=[]; changes=[]; availability=[]
    for group in ('all','v2','v3')+tuple(sorted({r['scene'] for r in rows})):
        a=[r for r in primary if group in ('all',r['cohort'],r['scene'])]
        for policy,delay in [('completed_mpc',.08),('prefix_cost_greedy',.08),('prefix_nash',.08),('prefix_maxmin',.08),('wait_mpc',.08),('prefix_mpc',.5)]:
            bs=[lookup[r['key'],policy,delay] for r in a]
            contrasts.append({'group':group,'comparator':policy,'delay':delay,'episodes':len(a),
                **{k+'_delta':mean(r[k]-b[k] for r,b in zip(a,bs)) for k in ('unpaid_fraction','worst_quality','mean_stall_seconds','current_mae')},
                'half_count_delta':sum(r['half_repaid']-b['half_repaid'] for r,b in zip(a,bs))})
    for row in primary:
        completed=lookup[row['key'],'completed_mpc',.08]; record=records[row['key']]
        changed=[tuple(a['decision']['rungs'])!=tuple(b['decision']['rungs']) for a,b in zip(row['rounds'],completed['rounds'])]
        changes.append({'key':row['key'],'changed_by_decision':changed})
        available=[max(0,h-19) for h in row['rounds'][1]['visible_indices']]
        availability.append({'key':row['key'],'second_decision_new_samples':available})
        for rr in row['rounds']:
            for u in (0,1):
                loss=rr['reference'][u]-rr['actual_quality'][u]
                if loss>0: violations.append({'key':row['key'],'segment':rr['segment'],'user_role':u,'loss_units':loss})
    for row in rows:
        if row['delay']!=.08 or row['policy'] not in ('prefix_mpc','completed_mpc','prefix_cost_greedy'): continue
        record=records[row['key']]; ps=periods(record); remaining=record.loss; budget=row['reserve_bytes']; losses=[]
        optimum=dp(ps,remaining,budget,False)[0]
        for t,rr in enumerate(row['rounds']):
            action=next(a for a in ps[t] if a.rungs==tuple(rr['decision']['rungs']))
            before=dp(ps[t:],remaining,budget,False)[0]
            credit=min(remaining,action.gain); remaining-=credit; budget-=action.extra
            after=credit+dp(ps[t+1:],remaining,budget,False)[0]
            assert before>=after; losses.append(before-after)
        assert sum(losses)==optimum-record.loss+remaining and remaining==row['remaining_units']
        regrets.append({'key':row['key'],'policy':row['policy'],'losses_units':losses,'losses_fraction':[x/record.loss for x in losses]})
    regret_summary=[]
    for p in ('prefix_mpc','completed_mpc','prefix_cost_greedy'):
        selected=[r for r in regrets if r['policy']==p]
        regret_summary.append({'policy':p,'mean_lost_fraction_by_decision':[mean(r['losses_fraction'][t] for r in selected) for t in range(4)],
                              'episodes_with_avoidable_loss':sum(sum(r['losses_units'])>0 for r in selected)})
    samplecounts=[n for r in availability for n in r['second_decision_new_samples']]
    return {'posthoc':True,'complete_feature_parity_checks':complete,'summary':raw['summary'],
            'screen_passed':raw['screen']['passed'],'failed_checks':[k for k,v in raw['screen']['checks'].items() if not v],
            'paired_descriptive_contrasts':contrasts,'changed_actions_by_decision':[sum(r['changed_by_decision'][t] for r in changes) for t in range(4)],
            'action_changes':changes,'second_decision_prefix_samples':{'min':min(samplecounts),'median':median(samplecounts),'max':max(samplecounts),'with_any':sum(x>0 for x in samplecounts),'total':len(samplecounts)},
            'prefix_availability':availability,'primary_floor_losses':violations,
            'opportunity_loss_summary':regret_summary,'opportunity_loss_rows':regrets}


def report(d):
    lines=['# Early-commitment mechanism diagnosis','',
        'Post-hoc descriptive checks; no parameter changes or independent confirmation.',
        '',f"Exploratory progression screen: **{d['screen_passed']}**.",'',
        '| Group | Comparator (delay s) | Unpaid delta | Worst-quality delta | Stall delta s | Half-count delta |',
        '|---|---|---:|---:|---:|---:|']
    for r in d['paired_descriptive_contrasts']:
        lines.append(f"| {r['group']} | {r['comparator']} ({r['delay']}) | {r['unpaid_fraction_delta']:+.6f} | {r['worst_quality_delta']:+.6f} | {r['mean_stall_seconds_delta']:+.6f} | {r['half_count_delta']:+d} |")
    lines+=['','All deltas are primary prefix_mpc minus comparator. Lower unpaid/stall is better. These are descriptive fixed-catalogue comparisons, not independent-subject inference.','',
        f"Changed actions versus completed-only by decision: {d['changed_actions_by_decision']} (168 per decision).",
        f"Second-decision new samples: {d['second_decision_prefix_samples']}.",
        f"Actual primary floor losses (0.001 index units): {d['primary_floor_losses']}.",'',
        '| Policy | Decision 1 lost fraction | Decision 2 | Decision 3 | Decision 4 | Episodes with loss |',
        '|---|---:|---:|---:|---:|---:|']
    for r in d['opportunity_loss_summary']:
        lines.append('| '+r['policy']+' | '+' | '.join(f'{v:.6f}' for v in r['mean_lost_fraction_by_decision'])+f" | {r['episodes_with_avoidable_loss']} |")
    lines+=['','Losses are conditional future-known structural opportunity, not causally available information. Their sum telescopes to the structural-optimum repayment gap.',
            f"All {d['complete_feature_parity_checks']} completed segment projections exactly match the previous reconstructed rounded feedback.",'']
    return '\n'.join(lines)


def plot(d):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'svg.hashsalt':'early-commitment-v1'})
    names=('prefix_cost_greedy','completed_mpc','prefix_mpc','wait_mpc')
    labels=('Prefix cost-greedy','Completed-only planning','Prefix planning','Wait for completion')
    cells={r['policy']:r for r in d['summary']['all'] if r['delay']==.08}
    fig,axes=plt.subplots(1,2,figsize=(10.5,4),layout='constrained')
    colors=['#748599','#748599','#087e8b','#c37936']
    for ax,field,title,limit in zip(axes,('unpaid_fraction','mean_stall_seconds'),('Mean unpaid fraction (lower is better)','Mean simulated stall (s; lower is better)'),(.45,19)):
        values=[cells[n][field] for n in names]
        ax.barh(range(4),values,color=colors); ax.set_yticks(range(4),labels); ax.invert_yaxis(); ax.set_xlim(0,limit)
        for i,v in enumerate(values): ax.text(v+limit*.012,i,f'{v:.4f}' if field=='unpaid_fraction' else f'{v:.2f}',va='center')
        ax.set_title(title); ax.spines[['top','right']].set_visible(False)
    fig.suptitle('168 exposed episodes: earlier information helps, but not over cost-greedy')
    for ext in ('png','svg'): fig.savefig(DEST/f'early_commitment.{ext}',dpi=180)
    plt.close(fig)


def run(verify=False):
    result=derive()
    if verify:
        meta=json.loads((DEST/'metadata.json').read_text())
        for field in ('source_sha256','input_sha256'):
            for n,h in meta[field].items(): assert sha(ROOT/n)==h,n
        for n,h in meta['result_sha256'].items(): assert sha(DEST/n)==h,n
        assert json.loads((DEST/'results.json').read_text())==result
        assert (DEST/'REPORT.md').read_text()==report(result)
    else:
        DEST.mkdir(parents=True,exist_ok=False)
        (DEST/'results.json').write_text(json.dumps(result,indent=2)+'\n'); (DEST/'REPORT.md').write_text(report(result)); plot(result)
        paths=[OUT/'results.json.gz',DATA/'forecasts.json.gz',ROOT/'feedback_opportunity/results/wire_v1/results.json']
        meta={'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in (Path(__file__),ROOT/'feedback_opportunity/frontier.py')},
              'input_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in paths},'result_sha256':{p.name:sha(p) for p in DEST.iterdir()}}
        (DEST/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'verified':verify,'changed_actions_by_decision':result['changed_actions_by_decision'],
                     'second_decision_prefix_samples':result['second_decision_prefix_samples'],
                     'primary_floor_losses':result['primary_floor_losses'],'opportunity_loss_summary':result['opportunity_loss_summary']},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--verify',action='store_true'); a=p.parse_args(); run(a.verify)
