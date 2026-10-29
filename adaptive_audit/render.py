"""Post-outcome presentation only; does not change the frozen analytical audit."""
import argparse
import hashlib
import json
from pathlib import Path
from adaptive_audit.run import OUT, read_gzip
from metric_contract.run import canonical, sha

DEST = Path(__file__).resolve().parent/'results/presentation_v1'


def summarize():
    result = read_gzip(OUT/'results.json.gz')
    rows = [r for r in result['rows'] if r['eta'] == 'half_second']
    return {'primary_sha256': sha(OUT/'results.json.gz'), 'post_outcome_presentation': True,
            'scenes': [{'scene': name, 'episodes': len(rs),
                        'largest_upper_fraction': max(r['response_credit_upper']/r['loss'] for r in rs),
                        'universal_promises_ruled_out': sum(r['adaptive_universal_half_ruled_out'] for r in rs)}
                       for name in sorted({r['scene'] for r in rows})
                       for rs in [[r for r in rows if r['scene'] == name]]]}


def plot(summary):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    rows = summary['scenes']; values = [100*r['largest_upper_fraction'] for r in rows]
    fig, ax = plt.subplots(figsize=(8.6, 4.5), layout='constrained')
    ax.barh(range(len(rows)), values, color='#356477', height=.65)
    ax.set_yticks(range(len(rows)), [r['scene'] for r in rows]); ax.invert_yaxis()
    ax.axvline(50, color='#ae4c3d', ls='--', label='Unchanged 50% target')
    for i, v in enumerate(values):
        ax.text(v+.65, i, f'{v:.2f}%', va='center', fontsize=10)
    ax.set_xlim(0, 56)
    ax.set_xlabel('Largest episode-specific upper bound within scene (% of past debt)')
    ax.set_title('Adaptive universal recovery: conditional upper bounds\nWhole-segment commitments; unrestricted future geometric masks', fontsize=11)
    ax.legend(loc='lower right', fontsize=9)
    fig.savefig(DEST/'adaptive_ceiling.png', dpi=180)
    fig.savefig(DEST/'adaptive_ceiling.svg', metadata={'Date': None})
    plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__); parser.add_argument('--verify', action='store_true'); args = parser.parse_args()
    result = summarize(); digest = hashlib.sha256(canonical(result)).hexdigest()
    if args.verify:
        meta = json.loads((DEST/'metadata.json').read_text())
        if json.loads((DEST/'summary.json').read_text()) != result or digest != meta['summary_sha256'] or sha(Path(__file__)) != meta['renderer_sha256']:
            raise ValueError('Presentation provenance mismatch')
        for name, value in meta['figures'].items():
            if sha(DEST/name) != value:
                raise ValueError('Figure hash mismatch')
    else:
        DEST.mkdir(parents=True, exist_ok=False); plot(result)
        (DEST/'summary.json').write_text(json.dumps(result, indent=2)+'\n')
        (DEST/'metadata.json').write_text(json.dumps({'summary_sha256': digest, 'renderer_sha256': sha(Path(__file__)),
            'figures': {p.name: sha(p) for p in sorted(DEST.glob('adaptive_ceiling.*'))}}, indent=2)+'\n')
    print(json.dumps({'verified': args.verify, 'summary_sha256': digest, 'scenes': len(result['scenes'])}))
