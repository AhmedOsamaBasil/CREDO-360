"""Post-run descriptive diagnostics and figures; no model selection or retuning."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean,median
from causal_playback.data import ROOT
from causal_playback.core import POLICIES,LIVE_POLICIES
from reserve_recovery.run import canonical,sha

DIRECTORY=ROOT/'causal_playback/results'
LABELS={'knn_recovery':'Causal KNN','greedy_recovery':'Greedy','cost_greedy':'Cost-greedy',
        'rolling_nash':'Rolling Nash','rolling_maxmin':'Rolling max-min',
        'persistence_mpc':'Persistence','unconditional_mpc':'Unconditional'}


def derive():
    with gzip.open(DIRECTORY/'replay_v1/results.json.gz','rt') as f: replay=json.load(f)
    live=json.loads((DIRECTORY/'live_v1/results.json').read_text())
    candidate={r['key']:r for r in replay['rows'] if r['policy']=='knn_recovery'}
    comparisons=[]
    for policy in POLICIES[1:]:
        other={r['key']:r for r in replay['rows'] if r['policy']==policy}
        comparisons.append({'control':policy,
            'mean_unpaid_gain':mean(other[k]['unpaid_fraction']-r['unpaid_fraction'] for k,r in candidate.items()),
            'different_actions':sum(a['decision']['rungs']!=b['decision']['rungs']
                for k,r in candidate.items() for a,b in zip(r['rounds'],other[k]['rounds'])),
            'decisions':672})
    floors=[]
    for r in candidate.values():
        for step in r['rounds']:
            for u in (0,1):
                if step['actual_quality'][u]<step['reference'][u]:
                    floors.append({'key':r['key'],'segment':step['segment'],'user':u,
                        'rungs':step['decision']['rungs'],'actual_units':step['actual_quality'][u],
                        'reference_units':step['reference'][u]})
    live_groups=[]
    for policy,rate in [(p,1500) for p in LIVE_POLICIES]+[('knn_recovery',750)]:
        rows=[r for r in live if r['policy']==policy and r['rate_kbit']==rate]
        rounds=[s for r in rows for s in r['rounds']]
        latencies=[max(s['arrivals'])-s['start'] for s in rounds]
        startup=mean(mean(r['rounds'][0]['arrivals']) for r in rows)
        stall=mean(r['mean_stall_seconds'] for r in rows)
        live_groups.append({'policy':policy,'rate_kbit':rate,'episodes':len(rows),'rounds':len(rounds),
            'deadline_misses':sum(not s['deadline_met'] for s in rounds),'latencies':latencies,
            'min_latency':min(latencies),'max_latency':max(latencies),'median_latency':median(latencies),
            'max_controller_ms':max((s['decision_end']-s['start'])*1000 for s in rounds),
            'mean_startup_stall':startup,'mean_additional_stall':stall-startup,
            **{k:mean(r[k] for r in rows) for k in ['unpaid_fraction','worst_quality','mean_quality','mean_stall_seconds','current_mae']},
            'half_repaid':sum(r['half_repaid'] for r in rows),
            'donor_floor_violations':sum(r['donor_floor_violations'] for r in rows)})
    bykey={(r['key'],r['policy']):r for r in replay['rows']}
    nominal=[r for r in live if r['rate_kbit']==1500]
    disagreements=sum(a['decision']['rungs']!=b['decision']['rungs'] for r in nominal
        for a,b in zip(r['rounds'],bykey[r['key'],r['policy']]['rounds']))
    return {'posthoc_descriptive_only':True,'replay_summary':replay['summary'],
            'frozen_screen':replay['screen'],'candidate_comparisons':comparisons,
            'candidate_floor_violations':floors,'live_summary':live_groups,
            'nominal_live_vs_fluid_action_disagreements':disagreements,
            'nominal_live_vs_fluid_decisions':96}


def report(d):
    lines=['# Selected-transfer live pilot: descriptive results','',
        'One fixed user pair per exposed scene. Six paired scenes per nominal policy; six candidate-only stress episodes.',
        'Not independent efficacy confirmation; the complete exposed replay fails its fixed practical gate.','',
        '| Policy / rate | Half / episodes | Unpaid | Worst quality | Startup stall s | Additional stall s | Deadline misses / rounds | Maximum receipt latency s |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    for r in d['live_summary']:
        lines.append(f"| {LABELS[r['policy']]} / {r['rate_kbit']} kbit/s | {r['half_repaid']}/{r['episodes']} | "
                     f"{r['unpaid_fraction']:.6f} | {r['worst_quality']:.4f} | {r['mean_startup_stall']:.4f} | "
                     f"{r['mean_additional_stall']:.4f} | {r['deadline_misses']}/{r['rounds']} | {r['max_latency']:.4f} |")
    lines += ['',f"Nominal live versus fluid-model action disagreements: {d['nominal_live_vs_fluid_action_disagreements']}/96.",
        'Timing can change feedback availability and therefore decisions; a difference is not automatically a replay error.',
        '', 'All startup waiting is counted. Final media drain is analytical, not decoded/displayed.',
        'Quality and debt feedback are reference-assisted retrospective values. No safe actual-quality floor is established.',
        'Each plotted point is a recorded round, not an independent experimental subject. No inferential confidence intervals are claimed.','']
    return '\n'.join(lines)


def plot(d,out):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    plt.rcParams.update({'font.size':10,'svg.hashsalt':'causal-playback-v1'})
    fig,axes=plt.subplots(1,2,figsize=(11,4.4),layout='constrained')
    for ax,cohort in zip(axes,['v2','v3']):
        cells=d['replay_summary'][cohort]
        ax.barh(range(7),[c['unpaid_fraction'] for c in cells],color=['#087e8b']+['#748599']*6)
        ax.set_yticks(range(7),[LABELS[c['policy']] for c in cells]); ax.invert_yaxis()
        ax.set_xlim(0,max(c['unpaid_fraction'] for c in cells)*1.20)
        for i,c in enumerate(cells): ax.text(c['unpaid_fraction']+.0015,i,f"{c['unpaid_fraction']:.4f}",va='center',fontsize=9)
        ax.set_title(f'{cohort.upper()} exposed cohort (84 episodes)'); ax.set_xlabel('Mean unpaid fraction (lower is better)')
        ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Causal quality feedback: fixed practical progression screen failed',fontsize=12)
    for ext in ['png','svg']: fig.savefig(out/f'exposed_recovery.{ext}',dpi=180)
    plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(11.5,4.8),layout='constrained')
    groups=d['live_summary']; labels=[LABELS[r['policy']] if r['rate_kbit']==1500 else 'KNN stress\n750 kbit/s' for r in groups]
    for i,r in enumerate(groups):
        # Deterministic horizontal spread, not random experimental variation.
        axes[0].scatter(i+np.linspace(-.18,.18,len(r['latencies'])),r['latencies'],s=18,
                        color='#bd581d' if i==4 else '#087e8b',alpha=.8)
    axes[0].axhline(9.5,color='#9f2424',ls='--',label='9.5 s deadline')
    axes[0].set_ylabel('Decision start to verified pair receipt (s)'); axes[0].legend(fontsize=9)
    axes[0].set_title('Recorded delivery: 96 nominal + 24 stress rounds')
    startup=[r['mean_startup_stall'] for r in groups]; later=[r['mean_additional_stall'] for r in groups]
    axes[1].bar(range(5),startup,color='#748599',label='Cold-start waiting')
    axes[1].bar(range(5),later,bottom=startup,color='#bd581d',label='Later playback starvation')
    axes[1].set_ylabel('Mean stall per user (s)'); axes[1].legend(fontsize=9)
    axes[1].set_title('Playback clock: all elapsed time charged')
    for ax in axes:
        ax.set_xticks(range(5),labels,rotation=25,ha='right'); ax.spines[['top','right']].set_visible(False)
        ax.set_ylim(bottom=0)
    for ext in ['png','svg']: fig.savefig(out/f'live_playback.{ext}',dpi=180)
    plt.close(fig)


def run(verify=False):
    out=DIRECTORY/'diagnostics_v1'; d=derive()
    if verify:
        meta=json.loads((out/'metadata.json').read_text())
        for n,h in meta['input_sha256'].items(): assert sha(ROOT/n)==h,n
        for n,h in meta['result_sha256'].items(): assert sha(out/n)==h,n
        assert json.loads((out/'diagnostics.json').read_text())==d
        assert (out/'REPORT.md').read_text()==report(d)
        assert sha(Path(__file__))==meta['script_sha256']
        assert hashlib.sha256(canonical(d)).hexdigest()==meta['scientific_sha256']
        return meta
    out.mkdir(exist_ok=False)
    (out/'diagnostics.json').write_text(json.dumps(d,indent=2)+'\n')
    (out/'REPORT.md').write_text(report(d),encoding='utf-8'); plot(d,out)
    paths=[DIRECTORY/'replay_v1/results.json.gz',DIRECTORY/'live_v1/results.json',
           DIRECTORY/'replay_v1/metadata.json',DIRECTORY/'live_v1/metadata.json']
    meta={'script_sha256':sha(Path(__file__)),'input_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in paths},
          'result_sha256':{p.name:sha(p) for p in out.iterdir()},
          'scientific_sha256':hashlib.sha256(canonical(d)).hexdigest()}
    (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    return meta


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--verify',action='store_true'); a=p.parse_args()
    meta=run(a.verify); print(json.dumps({'verified':a.verify,'scientific_sha256':meta['scientific_sha256']},indent=2))
