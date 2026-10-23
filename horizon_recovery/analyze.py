"""Complete paired/content/expiry diagnostics, including adverse outcomes."""
import argparse
import csv
import gzip
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from horizon_recovery.run import ROOT, SCENARIOS, POLICIES, read_csv, sha256, write_csv


def analyze(output):
    target = output/'diagnostics'
    if target.exists():
        raise ValueError('diagnostics already exist; preserve the previous analysis')
    target.mkdir()
    meta = json.loads((output/'metadata.json').read_text())
    summaries = read_csv(output/'seed_metrics.csv')
    paired = read_csv(output/'paired_diagnostics.csv')
    agreement = read_csv(output/'action_disagreements.csv')
    with gzip.open(output/'measurements.csv.gz','rt',newline='',encoding='utf-8') as f:
        raw = list(csv.DictReader(f))
    epoch_groups, content_groups = {}, {}
    for row in raw:
        key = row['scenario'],row['policy'],int(row['epoch'])
        epoch_groups.setdefault(key,[]).append(row)
        key = int(row['seed']),row['scenario'],row['policy'],row['content']
        content_groups.setdefault(key,[]).append(row)
    dynamics = []
    for (scenario,policy,epoch),rows in sorted(epoch_groups.items()):
        def mean(name):
            return float(np.mean([float(r[name]) for r in rows]))
        residuals = np.array([float(r['signed_residual']) for r in rows])
        expired = np.array([float(r['expired_signed_residual']) for r in rows])
        dynamics.append({'scenario':scenario,'policy':policy,'epoch':epoch,'mean_state':mean('state_before'),
                         'active_fraction':float(np.mean([float(r['state_before'])>1e-9 for r in rows])),
                         'fixed_shortfall':mean('fixed_shortfall'),'quality':mean('quality'),'target':mean('target'),
                         'positive_expired_residual':float(np.maximum(expired,0).mean()),
                         'negative_expired_credit':float(np.maximum(-expired,0).mean()),
                         'delivered_surplus':float(np.maximum(-residuals,0).mean()),
                         'new_deficit':float(np.maximum(residuals,0).mean()),'stall_s':mean('stall_s')})
    write_csv(target/'window_dynamics.csv',dynamics)
    contents = []
    for (seed,scenario,policy,content),rows in sorted(content_groups.items()):
        contents.append({'seed':seed,'scenario':scenario,'policy':policy,'content':content,
                         'quality':float(np.mean([float(r['quality']) for r in rows])),
                         'vw_psnr_db':float(np.mean([float(r['vw_psnr_db']) for r in rows])),
                         'stall_s_per_round':float(np.mean([float(r['stall_s']) for r in rows]))})
    write_csv(target/'content_metrics.csv',contents)
    by_key = {(r['seed'],r['scenario'],r['policy'],r['content']):r for r in contents}
    content_contrasts = []
    seeds = sorted({int(r['seed']) for r in raw})
    content_names = sorted({r['content'] for r in raw})
    for scenario in SCENARIOS:
        for baseline in ('nash','memoryless_scaled','memoryless_unscaled','fixed_window'):
            for content in content_names:
                for metric in ('quality','vw_psnr_db','stall_s_per_round'):
                    delta = [by_key[(s,scenario,'window_recovery',content)][metric]-by_key[(s,scenario,baseline,content)][metric] for s in seeds]
                    content_contrasts.append({'scenario':scenario,'baseline':baseline,'content':content,'metric':metric,
                        'mean_delta':float(np.mean(delta)),'minimum_delta':float(min(delta)),'maximum_delta':float(max(delta)),
                        'positive_seeds':sum(d>0 for d in delta),'negative_seeds':sum(d<0 for d in delta),'paired_seeds':len(delta)})
    write_csv(target/'content_contrasts.csv',content_contrasts)
    agreements = []
    for scenario in SCENARIOS:
        for baseline in POLICIES:
            if baseline == 'window_recovery': continue
            rows = [r for r in agreement if r['scenario']==scenario and r['baseline']==baseline]
            count,total = sum(int(r['disagreements']) for r in rows),sum(int(r['comparisons']) for r in rows)
            agreements.append({'scenario':scenario,'baseline':baseline,'disagreements':count,'comparisons':total,'fraction':count/total})
    write_csv(target/'agreement_summary.csv',agreements)
    plt.rcParams.update({'font.size':10,'axes.spines.top':False,'axes.spines.right':False})
    fig,axes = plt.subplots(1,3,figsize=(12,4.4))
    panels = [('worst_user_quality','Worst-user quality difference\n(positive favors window)'),
              ('post_restoration_shortfall','Post-restoration shortfall difference\n(negative favors window)'),
              ('stall_s_per_user','Stall difference, s/user\n(negative favors window)')]
    for ax,(metric,title) in zip(axes,panels):
        for j,baseline in enumerate(('nash','memoryless_scaled')):
            rows = [next(r for r in paired if r['scenario']==s and r['baseline']==baseline and r['metric']==metric) for s in SCENARIOS]
            v,lo,hi = [np.array([float(r[k]) for r in rows]) for k in ('mean_delta','ci95_low','ci95_high')]
            ax.errorbar(v,np.arange(4)+(j-.5)*.19,xerr=np.array([v-lo,hi-v]),fmt='o',capsize=3,label=baseline.replace('_',' '))
        ax.axvline(0,color='gray',lw=1)
        ax.set_yticks(range(4),[s.replace('_',' ') for s in SCENARIOS] if ax is axes[0] else [])
        ax.set_title(title)
        ax.grid(axis='x',alpha=.2)
    axes[0].invert_yaxis()
    axes[-1].legend(loc='best',fontsize=8)
    fig.suptitle('Fresh-content paired-seed diagnostics; conditional 95% bootstrap intervals',fontsize=11)
    fig.tight_layout()
    for ext in ('png','pdf'): fig.savefig(target/f'paired_effects.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)
    fig,axes = plt.subplots(3,1,figsize=(9,8),sharex=True)
    for policy in ('window_recovery','memoryless_scaled','nash'):
        rows = [r for r in dynamics if r['scenario']=='known_ceiling' and r['policy']==policy]
        t = [r['epoch'] for r in rows]
        # Nash is a shadow bookkeeping state, not an active controller input.
        if policy != 'nash': axes[0].plot(t,[r['mean_state'] for r in rows],label=policy.replace('_',' '))
        axes[1].plot(t,[r['fixed_shortfall'] for r in rows],label=policy.replace('_',' '))
    rows = [r for r in dynamics if r['scenario']=='known_ceiling' and r['policy']=='window_recovery']
    for field,label in [('positive_expired_residual','Expired positive residual (not recovery)'),
                         ('delivered_surplus','Delivered surplus relative to contract')]:
        axes[2].plot([r['epoch'] for r in rows],[r[field] for r in rows],label=label)
    for ax in axes:
        ax.axvspan(40,80,color='gray',alpha=.12)
        ax.axvline(80,color='gray',ls='--',lw=1)
        ax.grid(alpha=.2); ax.legend(fontsize=8)
    axes[0].set_ylabel('Mean active-policy state')
    axes[1].set_ylabel('Fixed-target-four shortfall')
    axes[2].set_ylabel('Quality-index units/round')
    axes[2].set_xlabel('Round (six source segments repeat; display ceiling in shaded interval)')
    fig.suptitle('Known-ceiling dynamics: expiry and delivered surplus are different quantities')
    fig.tight_layout()
    for ext in ('png','pdf'): fig.savefig(target/f'window_dynamics.{ext}',dpi=180,bbox_inches='tight')
    plt.close(fig)
    lines = ['# Fresh-content window-recovery pilot','',f"Frozen progression screen: **{'PASS' if meta['progression_gate_passed'] else 'FAIL'}**.",'',
             'All deltas are window recovery minus baseline. Intervals are paired-seed bootstrap diagnostics conditional on the fixed content/participant pool, not human-population validation.','',
             '## Known-ceiling contrasts','', '| Baseline | Metric | Mean delta | Conditional 95% interval |','|---|---|---:|---|']
    for r in paired:
        if r['scenario']=='known_ceiling' and r['baseline'] in ('nash','memoryless_scaled'):
            lines.append(f"| {r['baseline']} | {r['metric']} | {float(r['mean_delta']):+.6f} | [{float(r['ci95_low']):+.6f}, {float(r['ci95_high']):+.6f}] |")
    lines += ['','## Every frozen check','']
    for k,v in meta['screen_details']['checks'].items(): lines.append(f"- {'PASS' if v else 'FAIL'}: {k}")
    lines += ['','## Mechanism and censoring','']
    for p in POLICIES:
        rows = [r for r in summaries if r['scenario']=='known_ceiling' and r['policy']==p]
        active = np.mean([float(r['active_state_fraction']) for r in rows])
        events = sum(int(r['recovery_event_observed']) for r in rows)
        lines.append(f'- {p}: active bookkeeping fraction {active:.4%}; observed recovery events {events}/{len(rows)}; remaining cases right-censored at40 rounds. Nash bookkeeping does not affect its decisions.')
    lines += ['','Expiry is not delivered recovery. See `diagnostics/window_dynamics.csv` for separate positive expiry, negative credit expiry, new deficit and delivered surplus.','',
              '## Content-specific mean-quality differences','', '| Baseline | Content | Mean delta | Positive/negative seeds |','|---|---|---:|---|']
    for r in content_contrasts:
        if r['scenario']=='known_ceiling' and r['baseline'] in ('nash','memoryless_scaled') and r['metric']=='quality':
            lines.append(f"| {r['baseline']} | {r['content']} | {r['mean_delta']:+.6f} | {r['positive_seeds']}/{r['negative_seeds']} |")
    lines += ['','No parameters were changed after opening the holdout. This is offline fluid transport and objective trace replay, not live streaming or subjective QoE. Six source segments repeat across120 rounds; panel and seed dependence must not be ignored.','']
    # This report is a deterministic generated analysis artifact, not hand-edited source.
    (output/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    manifest = {'analysis_source_sha256':sha256(Path(__file__)),
                'inputs':{n:sha256(output/n) for n in ('metadata.json','measurements.csv.gz','seed_metrics.csv','paired_diagnostics.csv','action_disagreements.csv','REPORT.md')},
                'outputs':{p.name:sha256(p) for p in target.iterdir() if p.is_file()}}
    (target/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Complete diagnostics saved: {target}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'horizon_recovery/results/v3')
    analyze(parser.parse_args().output)
