"""Descriptive plots and tables for a locked, already-exposed development run."""
import argparse
import csv
import gzip
import json
from collections import defaultdict
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from objective_diagnostics.run import ROOT, COHORTS, SCENARIOS, POLICIES, STATEFUL, sha256, write_csv


def read(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def main(output):
    destination = output/'diagnostics'
    destination.mkdir(exist_ok=False)
    summaries = read(output/'seed_metrics.csv')
    contrasts = read(output/'paired_diagnostics.csv')
    agreements = read(output/'action_disagreements.csv')
    meta = json.loads((output/'metadata.json').read_text())
    measures = ('worst_user_quality', 'worst_user_psnr_db', 'mean_quality',
                'cumulative_shortfall', 'post_restoration_shortfall',
                'impaired_restoration_shortfall', 'stall_s_per_user', 'switch_frequency',
                'active_state_fraction', 'mean_state', 'mean_target',
                'negative_balance_fraction', 'quality_at_upper_cap_fraction',
                'mean_imposed_absolute_drop', 'mean_imposed_relative_drop',
                'recovery_event_observed')
    grouped = {}
    for cohort in COHORTS:
        for scenario in SCENARIOS:
            for policy in POLICIES:
                rows = [r for r in summaries if (r['cohort'], r['scenario'], r['policy']) == (cohort, scenario, policy)]
                assert len(rows) == 6
                grouped[cohort, scenario, policy] = {
                    'cohort': cohort, 'scenario': scenario, 'policy': policy, 'paired_seeds': len(rows),
                    **{m: float(np.mean([float(r[m]) for r in rows])) for m in measures}}
    write_csv(destination/'policy_means.csv', list(grouped.values()))

    # These are descriptive row aggregates, NOT independent sampling units.
    accum = defaultdict(lambda: defaultdict(float))
    severity = defaultdict(lambda: defaultdict(float))
    with gzip.open(output/'measurements.csv.gz', 'rt', newline='', encoding='utf-8') as f:
        for r in csv.DictReader(f):
            key = (r['cohort'], r['scenario'], r['policy'])
            a = accum[key]; a['rows'] += 1
            for name, value in {
                'prediction_bias': float(r['predicted']) - float(r['quality']),
                'positive_residual': max(float(r['signed_residual']), 0),
                'surplus': max(-float(r['signed_residual']), 0),
                'expired_deficit': max(float(r['expired_signed_residual']), 0),
                'expired_credit': max(-float(r['expired_signed_residual']), 0),
                'expiry_increase': max(float(r['expiry_state_change']), 0),
                'expiry_decrease': max(-float(r['expiry_state_change']), 0),
                'upper_clipped': float(r['quality']) == 5,
            }.items(): a[name] += value
            # Independent of selected policy: count the manipulation once, at Nash.
            if r['policy'] == 'nash' and 40 <= int(r['epoch']) < 80 and int(r['user']) == (int(r['seed'])-202610500)%5:
                s = severity[r['cohort'], r['scenario'], r['content']]
                s['rows'] += 1
                for name in ('cap_predicted_drop', 'cap_relative_drop', 'sender_quality_range'):
                    s[name] += float(r[name])
                s['flat_range_rows'] += float(r['sender_quality_range']) <= 1e-12
    rows = []
    for (cohort, scenario, policy), a in accum.items():
        rows.append({'cohort': cohort, 'scenario': scenario, 'policy': policy, 'user_rounds': int(a['rows']),
                     **{'mean_'+k: v/a['rows'] for k, v in a.items() if k != 'rows'}})
    write_csv(destination/'window_accounting.csv', rows)
    rows = []
    for (cohort, scenario, content), a in severity.items():
        rows.append({'cohort': cohort, 'scenario': scenario, 'content': content, 'impaired_user_rounds': int(a['rows']),
                     **{'mean_'+k: v/a['rows'] for k, v in a.items() if k not in ('rows', 'flat_range_rows')},
                     'flat_range_rows': int(a['flat_range_rows'])})
    write_csv(destination/'impairment_by_content.csv', rows)
    disagreement = []
    for cohort in COHORTS:
        for scenario in SCENARIOS:
            for candidate in STATEFUL:
                for baseline in ('nash', candidate.split('_')[0]+'_memoryless', 'window_maxmin', 'window_nash'):
                    rows = [r for r in agreements if (r['cohort'], r['scenario'], r['candidate'], r['baseline']) == (cohort, scenario, candidate, baseline)]
                    n = sum(int(r['disagreements']) for r in rows)
                    total = sum(int(r['comparisons']) for r in rows)
                    disagreement.append({'cohort': cohort, 'scenario': scenario, 'candidate': candidate,
                                         'baseline': baseline, 'disagreements': n, 'comparisons': total, 'fraction': n/total})
    write_csv(destination/'action_disagreements_aggregated.csv', disagreement)
    checks = [{'candidate': p, 'check': k, 'passed': v} for p, record in meta['screen'].items() for k, v in record['checks'].items()]
    write_csv(destination/'all_development_checks.csv', checks)

    plt.rcParams.update({'font.size': 10, 'pdf.fonttype': 42, 'axes.spines.top': False, 'axes.spines.right': False})
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.8), constrained_layout=True)
    panels = []
    for cohort in COHORTS:
        matrix = []
        for candidate in STATEFUL:
            baselines = ('nash', candidate.split('_')[0]+'_memoryless', 'window_maxmin', 'window_nash')
            matrix.append([next(float(r['mean_delta']) for r in contrasts if
                                (r['cohort'], r['scenario'], r['candidate'], r['baseline'], r['metric']) ==
                                (cohort, 'range_ceiling', candidate, b, 'worst_user_quality')) for b in baselines])
        panels.append(np.array(matrix))
    bound = max(abs(p).max() for p in panels)
    for ax, cohort, matrix in zip(axes, COHORTS, panels):
        im = ax.imshow(matrix, cmap='RdBu', vmin=-bound, vmax=bound, aspect='auto')
        ax.set_xticks(range(4), ['Nash', 'Matched\nmemoryless', 'Window\nmax-min', 'Window\nNash'])
        ax.set_yticks(range(4), STATEFUL)
        ax.set_title(cohort.replace('_', ' '))
        for y in range(4):
            for x in range(4):
                ax.text(x, y, f'{matrix[y,x]:+.4f}', ha='center', va='center',
                        color='white' if abs(matrix[y,x]) > .65*bound else 'black')
    fig.colorbar(im, ax=list(axes), label='Mean worst-user quality difference (candidate - baseline)', shrink=.8)
    fig.suptitle('DEVELOPMENT: range-normalized ceiling, six paired seeds per exposed catalogue')
    for extension in ('png', 'pdf'): fig.savefig(destination/f'worst_quality_controls.{extension}', dpi=180)
    plt.close(fig)

    fig, axes = plt.subplots(2, 2, figsize=(11.5, 7), constrained_layout=True, sharey=True)
    for column, cohort in enumerate(COHORTS):
        for row, (metric, label) in enumerate((('active_state_fraction', 'Positive pre-decision state (%)'),
                                               ('mean_target', 'Mean internal contract target'))):
            ax = axes[row, column]
            values = [grouped[cohort, 'range_ceiling', p][metric] * (100 if row == 0 else 1) for p in STATEFUL]
            ax.barh(np.arange(4), values, color=['#506c8c', '#8bb7da', '#9e5243', '#e6ac8b'])
            ax.set_yticks(range(4), STATEFUL); ax.set_ylim(3.6, -.6)
            ax.set_xlabel(label)
            if row == 0: ax.set_title(cohort.replace('_', ' ')); ax.set_xlim(0, 100)
            else: ax.set_xlim(1, 5); ax.axvline(4, color='0.5', ls=':', lw=1)
    fig.suptitle('DEVELOPMENT: state activation is not evidence of improved fairness')
    for extension in ('png', 'pdf'): fig.savefig(destination/f'target_and_state.{extension}', dpi=180)
    plt.close(fig)

    lines = ['# Exposed-data diagnostic results', '',
             'Development only: both catalogues were previously inspected. Six paired seeds per catalogue; '
             '360 episodes / 216,000 user-rounds. Intervals in `paired_diagnostics.csv` are descriptive, '
             'conditional on these fixed content pools, and are not independent confirmation.', '',
             '**No candidate passed the locked development screen. No new holdout was consumed.**', '',
             '## Range-normalized ceiling: complete policy means', '',
             'The quality index is clipped to [1,5]; worst quality is the minimum of the five user time averages. '
             'Fixed shortfall uses target 4 for every policy. Stall is cumulative seconds per user. '
             'Direct rules have no active recovery state; their logged residual balances are shadow diagnostics.', '']
    for cohort in COHORTS:
        lines += [f'### {cohort}', '', '| Policy | Worst quality | Worst VW-PSNR (dB) | Mean quality | Fixed shortfall | Stall (s/user) | Active (%) |',
                  '|---|---:|---:|---:|---:|---:|---:|']
        for p in POLICIES:
            a = grouped[cohort, 'range_ceiling', p]
            lines.append(f"| {p} | {a['worst_user_quality']:.6f} | {a['worst_user_psnr_db']:.4f} | {a['mean_quality']:.6f} | {a['cumulative_shortfall']:.6f} | {a['stall_s_per_user']:.6f} | {100*a['active_state_fraction']:.3f} |")
        lines.append('')
    lines += ['## Exact failed development checks', '', 'All passing and failing checks are retained in `all_development_checks.csv`.', '']
    for p, record in meta['screen'].items():
        lines += [f'### {p}', ''] + ['- '+k for k, v in record['checks'].items() if not v] + ['']
    lines += ['## Files and interpretation boundaries', '',
              '- `policy_means.csv`: all 60 cohort/scenario/policy combinations, not just the main stress case.',
              '- `window_accounting.csv`: delivery and expiry are separate; expiry is never called recovery. Row aggregates are descriptive.',
              '- `impairment_by_content.csv`: sender-only absolute/relative severity, counted once rather than ten times across policies.',
              '- `action_disagreements_aggregated.csv`: individual rung decisions, 3,600 comparisons per cohort/scenario/pair.',
              '- Parent `paired_diagnostics.csv`: all locked matched contrasts, including target and banking factors, with descriptive seed intervals.',
              '- Two figures show primary quality comparisons and activation/targets, respectively.', '',
              'No human validation, adaptive coverage guarantee, novel queue theorem, or successful new-method claim follows from this experiment. '
              'The range ceiling is a synthetic known capability profile, not equal absolute or perceptual impairment. '
              'Runtime is measured but not charged to playback. Six source segments repeat; this is not a live player.', '']
    (destination/'REPORT.md').write_text('\n'.join(lines), encoding='utf-8')
    manifest = {'development_only': True, 'analysis_source_sha256': sha256(Path(__file__)),
                'inputs': {name: sha256(output/name) for name in ('metadata.json', 'measurements.csv.gz', 'seed_metrics.csv', 'paired_diagnostics.csv', 'action_disagreements.csv')},
                'outputs': {p.name: sha256(p) for p in destination.iterdir() if p.is_file()}}
    (destination/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'diagnostics': str(destination), 'development_promising': False}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'objective_diagnostics/results/development_v1')
    main(parser.parse_args().output)
