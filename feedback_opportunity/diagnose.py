"""Corrected descriptive reporting and conditional opportunity-loss decomposition.

The frozen initial summary compares Python tuples with JSON lists and reports
all actions different. Raw actions are intact. This separate diagnostic
normalizes their representation; it does not change policies or measurements.
"""
import argparse
import csv
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean,median
import numpy as np
from causal_playback.data import ROOT,load
from causal_compensation.data import SOURCES
from feedback_opportunity.frontier import periods,dp
from reserve_recovery.run import canonical,sha

D=ROOT/'feedback_opportunity/results'


def same_action(a,b): return tuple(a)==tuple(b)


def derive():
    with gzip.open(D/'audit_v1/results.json.gz','rt') as f: audit=json.load(f)
    with gzip.open(ROOT/'causal_playback/results/replay_v1/results.json.gz','rt') as f: old=json.load(f)
    saved={(r['key'],r['policy']):r for r in old['rows']}
    records={r.key:r for r in load(json.loads((ROOT/'causal_playback/data/media_manifest.json').read_text()))}
    counts={}; regrets=[]
    for row in audit['feedback_rows']:
        policy=row['policy']; other=saved[row['key'],policy]
        counts.setdefault(policy,0)
        counts[policy]+=sum(not same_action(a['decision']['rungs'],b['decision']['rungs']) for a,b in zip(row['rounds'],other['rounds']))
        if policy not in ('knn_recovery','cost_greedy','rolling_nash'): continue
        record=records[row['key']]; ps=periods(record); remaining=record.loss; budget=row['reserve_bytes']; losses=[]
        optimum=dp(ps,remaining,budget,False)[0]
        for t,step in enumerate(row['rounds']):
            a=next(a for a in ps[t] if same_action(a.rungs,step['decision']['rungs']))
            before=dp(ps[t:],remaining,budget,False)[0]
            credit=min(remaining,a.gain); remaining-=credit; budget-=a.extra
            after=credit+dp(ps[t+1:],remaining,budget,False)[0]
            assert before>=after; losses.append(before-after)
        assert sum(losses)==optimum-(record.loss-remaining)
        assert remaining==row['remaining_units']
        regrets.append({'key':row['key'],'cohort':row['cohort'],'scene':row['scene'],'policy':policy,
                        'lost_recoverable_units':losses,'lost_recoverable_fraction':[x/record.loss for x in losses]})
    old_q={}
    for cohort,folder in SOURCES.items():
        for name in ('calibration_quality.csv','heldout_quality.csv'):
            with (ROOT/folder/name).open(newline='') as f:
                for r in csv.DictReader(f): old_q[cohort,r['content'],int(r['subject']),int(r['segment']),int(r['ladder_index'])]=float(r['vw_psnr_db'])
    wire=json.loads((D/'wire_v1/results.json').read_text()); differences=[]; unit_differences=[]
    for r in wire['rows']:
        cohort,scene,sid,t=r['key'].split(':')
        for j in range(6):
            previous=old_q[cohort,scene,int(sid),int(t),j]
            differences.append(abs(r['psnr_db'][j]-previous))
            units=int(np.floor(np.clip(1+(previous-18)/6,1,5)*1000+.5))
            unit_differences.append(abs(r['quality_units'][j]-units))
    meta=json.loads((ROOT/'feedback_opportunity/data/maps_v1/metadata.json').read_text())
    feedback={'messages':len(wire['rows']),'values':len(differences),
        'payload_bytes':sum(r['payload_bytes'] for r in wire['rows']),
        'response_body_bytes':sum(r['response_body_bytes'] for r in wire['rows']),
        'median_roundtrip_ms':median(r['roundtrip_seconds'] for r in wire['rows'])*1000,
        'max_roundtrip_ms':max(r['roundtrip_seconds'] for r in wire['rows'])*1000,
        'median_reconstruction_ms':median(r['reconstruction_seconds'] for r in wire['rows'])*1000,
        'max_reconstruction_ms':max(r['reconstruction_seconds'] for r in wire['rows'])*1000,
        'mae_db':mean(differences),'max_error_db':max(differences),'mae_index':mean(unit_differences)/1000,
        'max_error_index':max(unit_differences)/1000,'exact_index_values':sum(x==0 for x in unit_differences),
        'error_units_histogram':{str(x):unit_differences.count(x) for x in sorted(set(unit_differences))},
        'sender_maps_compressed_bytes':sum(r['map_bytes'] for r in meta['sources']),
        'sender_maps_float32_bytes':6*6*60*72*4}
    sums=[]
    for policy in ('knn_recovery','cost_greedy','rolling_nash'):
        rs=[r for r in regrets if r['policy']==policy]
        sums.append({'policy':policy,'episodes_with_avoidable_loss':sum(sum(r['lost_recoverable_units'])>0 for r in rs),
                     'mean_lost_fraction_by_decision':[mean(r['lost_recoverable_fraction'][t] for r in rs) for t in range(4)]})
    return {'posthoc_diagnostic':True,'frozen_summary_type_error_corrected':True,
            'corrected_action_disagreements':counts,'decisions_per_policy':672,
            'wire_feedback':feedback,'opportunity_summary':audit['opportunity_summary'],
            'feedback_summary':[{**r,'action_disagreements_vs_ideal_feedback':counts[r['policy']]} for r in audit['feedback_summary']['all']],
            'opportunity_loss_summary':sums,'opportunity_loss_rows':regrets,
            'practical_screen':audit['unchanged_practical_screen']}


def report(d):
    lines=['# Remaining opportunity and feedback audit','',
        'Exposed data only. Future-known bounds do not certify a causal controller.',
        'The original action-disagreement summary has a tuple/list comparison bug; corrected counts below use raw actions.','',
        '| Benchmark | Half / 168 | Mean unpaid | Gap over saved cost-greedy |',
        '|---|---:|---:|---:|']
    for r in d['opportunity_summary']['all']:
        lines.append(f"| {r['benchmark']} | {r['half_repaid']} | {r['mean_unpaid_feasible']:.6f} | {r['gap_vs_saved_cost_greedy_feasible']:.6f} |")
    lines+=['','| Feedback-integrated policy | Half / 168 | Mean unpaid | Worst quality | Changed actions / 672 |',
            '|---|---:|---:|---:|---:|']
    for r in d['feedback_summary']:
        lines.append(f"| {r['policy']} | {r['half_repaid']} | {r['unpaid_fraction']:.6f} | {r['worst_quality']:.4f} | {r['action_disagreements_vs_ideal_feedback']} |")
    f=d['wire_feedback']; lines+=['',f"Practical screen passed: **{d['practical_screen']['passed']}**.",'',
        f"{f['messages']} actual HTTP messages; {f['values']} reconstructed quality values; {f['exact_index_values']} exactly match the saved rounded objective index.",
        f"Same-metric difference: mean {f['mae_db']:.9f} dB, maximum {f['max_error_db']:.6f} dB.",
        f"Client payload {f['payload_bytes']} bytes total (140/message); response bodies {f['response_body_bytes']} bytes. HTTP/TCP/TLS overhead is not included.",
        f"Loopback roundtrip median/max: {f['median_roundtrip_ms']:.3f}/{f['max_roundtrip_ms']:.3f} ms; server reconstruction {f['median_reconstruction_ms']:.3f}/{f['max_reconstruction_ms']:.3f} ms.",
        f"Sender maps: {f['sender_maps_compressed_bytes']} compressed bytes; {f['sender_maps_float32_bytes']} raw float32 bytes across six scenes.",'',
        'These are reference-assisted metric reconstruction checks, not perceptual validation or WAN/HMD performance.',
        'The controller replay retains the nominal ten-second model and 50ms control allowance, not measured end-to-end feedback timing.','']
    return '\n'.join(lines)


def plot(d,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    plt.rcParams.update({'font.size':10,'svg.hashsalt':'feedback-opportunity-v1'})
    fig,axes=plt.subplots(1,2,figsize=(11.6,4.8),layout='constrained')
    values=[d['feedback_summary'][2]['unpaid_fraction'],d['feedback_summary'][0]['unpaid_fraction'],
            d['opportunity_summary']['all'][0]['mean_unpaid_feasible'],d['opportunity_summary']['all'][2]['mean_unpaid_feasible']]
    labels=['Causal cost-greedy','Causal KNN','Future-known optimum','Future-known + quality guard']
    axes[0].barh(range(4),values,color=['#748599','#087e8b','#b57a28','#b57a28'])
    axes[0].set_yticks(range(4),labels); axes[0].invert_yaxis(); axes[0].set_xlim(0,.43)
    for i,v in enumerate(values): axes[0].text(v+.004,i,f'{v:.4f}',va='center')
    axes[0].set_xlabel('Mean unpaid fraction (lower is better)'); axes[0].set_title('Remaining opportunity: 168 exposed episodes')
    h=d['wire_feedback']['error_units_histogram']; x=[int(k) for k in h]; counts=list(h.values())
    axes[1].bar(x,counts,color='#087e8b',width=.7); axes[1].set_yscale('log')
    axes[1].set_xticks(range(0,max(x)+1,2)); axes[1].set_xlabel('Absolute rounded-index error (0.001 units)')
    axes[1].set_ylabel('Quality values (log count)'); axes[1].set_title('Feedback parity: saved same-metric labels')
    for ax in axes: ax.spines[['top','right']].set_visible(False)
    for ext in ('png','svg'): fig.savefig(out/f'opportunity_feedback.{ext}',dpi=180)
    plt.close(fig)


def run(verify=False):
    out=D/'diagnostics_v1'; result=derive()
    if verify:
        meta=json.loads((out/'metadata.json').read_text())
        assert meta['script_sha256']==sha(Path(__file__))
        for n,h in meta['input_sha256'].items(): assert sha(ROOT/n)==h,n
        for n,h in meta['result_sha256'].items(): assert sha(out/n)==h,n
        assert json.loads((out/'results.json').read_text())==result
        assert (out/'REPORT.md').read_text()==report(result)
    else:
        out.mkdir(exist_ok=False); (out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
        (out/'REPORT.md').write_text(report(result)); plot(result,out)
        paths=[D/'audit_v1/results.json.gz',D/'wire_v1/results.json',ROOT/'causal_playback/results/replay_v1/results.json.gz',ROOT/'feedback_opportunity/data/maps_v1/metadata.json']
        meta={'script_sha256':sha(Path(__file__)),'input_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in paths},
              'result_sha256':{p.name:sha(p) for p in out.iterdir()}}
        (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'verified':verify,'corrected_action_disagreements':result['corrected_action_disagreements'],
                      'wire_feedback':result['wire_feedback'],'opportunity_loss_summary':result['opportunity_loss_summary']},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--verify',action='store_true'); a=p.parse_args(); run(a.verify)
