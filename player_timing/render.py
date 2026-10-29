"""Post-outcome presentation of separately denominated replay and measurements."""
import argparse
import hashlib
import json
from pathlib import Path

from metric_contract.run import canonical, sha
from player_timing.diagnose import read
from player_timing.replay import OUT as REPLAY
from player_timing.audit import OUT as AUDIT

OUT = Path(__file__).resolve().parent / 'results/presentation_v2'
MODES = [(10, False), (10, True), (2, False), (2, True)]
POLICIES = ['cost_greedy', 'rolling_nash', 'maxmin']


def summarize():
    replay = read(REPLAY / 'results.json.gz')
    audit = read(AUDIT / 'results.json.gz')
    rows = []
    for source, summary in [('replay', replay['summary']), ('browser', audit['summary'])]:
        for policy in POLICIES:
            for unit, buffered in MODES:
                matches = [r for r in summary if r['policy'] == policy
                           and r['unit_seconds'] == unit and r['buffered'] == buffered
                           and (source != 'replay' or r['scene'] == 'all')]
                if len(matches) != 1:
                    raise ValueError('Missing/duplicate presentation cell')
                r = matches[0]
                rows.append({'source': source, 'policy': policy, 'unit_seconds': unit,
                             'buffered': buffered, 'denominator': 168 if source == 'replay' else r['sessions'],
                             'protected_parent_half': r['original_parent_account']['protected_half'] if source == 'replay' else r['parent_half'],
                             'mean_recipient_finish_seconds': r['mean_recipient_finish']})
    return {'posthoc': True, 'replay_sha256': sha(REPLAY / 'results.json.gz'),
            'audit_sha256': sha(AUDIT / 'results.json.gz'),
            'valid_browser_sessions': audit['valid'], 'scheduled_browser_sessions': audit['sessions'],
            'rows': rows}


def draw(data):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    colors = ['#176b87', '#b05e24', '#643b9f']
    markers = ['o', 's', '^']
    labels = ['Cost-greedy', 'Rolling Nash', 'Max-min']
    fig, axes = plt.subplots(2, 2, figsize=(10.5, 6.8), layout='constrained')
    for col, source in enumerate(['replay', 'browser']):
        for p, color, marker, label in zip(POLICIES, colors, markers, labels):
            rows = [r for r in data['rows'] if r['source'] == source and r['policy'] == p]
            axes[0, col].plot(range(4), [r['mean_recipient_finish_seconds'] for r in rows],
                              marker=marker, color=color, label=label, lw=1.7,
                              ls='--' if p == 'maxmin' else '-')
            axes[1, col].plot(range(4), [100*r['protected_parent_half']/r['denominator'] for r in rows],
                              marker=marker, color=color, lw=1.7,
                              ls='--' if p == 'maxmin' else '-')
        axes[0, col].axhline(40, color='#555555', ls=':', lw=1)
        axes[0, col].set_title('Analytical replay:168 exposed episodes' if source == 'replay'
                               else 'Browser:6 fixed scene pairs per cell', fontsize=11)
        axes[0, col].set_ylabel('Mean final recipient completion (s)')
        axes[1, col].set_ylabel('Protected half repayment (%)')
        axes[1, col].set_ylim(-2, 102)
        for row in range(2):
            axes[row, col].set_xticks(range(4), ['10s\ncold', '10s\nbuffered', '2s\ncold', '2s\nbuffered'])
            axes[row, col].grid(axis='y', alpha=.2)
    axes[0, 0].legend(fontsize=9, loc='upper right')
    fig.suptitle('Matched paths: completion timing and original parent repayment\n'
                 'Charged startup; unchanged debt/reserve/deadline; no physical-display measurement', fontsize=12)
    fig.savefig(OUT / 'timing_and_repayment.png', dpi=180)
    fig.savefig(OUT / 'timing_and_repayment.svg', metadata={'Date': None})
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    data = summarize()
    digest = hashlib.sha256(canonical(data)).hexdigest()
    if args.verify:
        meta = json.loads((OUT / 'metadata.json').read_text())
        if json.loads((OUT / 'summary.json').read_text()) != data or meta['summary_sha256'] != digest or meta['renderer_sha256'] != sha(Path(__file__)):
            raise ValueError('Presentation provenance changed')
        for filename, expected in meta['figures'].items():
            if sha(OUT / filename) != expected:
                raise ValueError('Figure changed')
    else:
        OUT.mkdir(parents=True, exist_ok=False)
        draw(data)
        (OUT / 'summary.json').write_bytes(canonical(data))
        (OUT / 'metadata.json').write_bytes(canonical({
            'summary_sha256': digest, 'renderer_sha256': sha(Path(__file__)),
            'figures': {p.name: sha(p) for p in sorted(OUT.glob('timing_and_repayment.*'))}}))
    print(json.dumps({'verified': args.verify, 'sha256': digest}))


if __name__ == '__main__':
    main()
