"""Post-outcome saturation and sampling-resolution diagnostics; no retuning."""
import argparse
import hashlib
import json
from pathlib import Path
from statistics import median
import numpy as np
from metric_contract.run import sha, canonical
from adaptive_audit.run import read_gzip
from temporal_viewport.prepare import ROOT, OUT as DATA
from temporal_viewport.run import OUT as PRIMARY

OUT = ROOT/'temporal_viewport/results/diagnostics_v1'


def analysis():
    data = read_gzip(DATA/'features.json.gz'); primary = read_gzip(PRIMARY/'results.json.gz')
    source = read_gzip(ROOT/'geometric_admission/results/exposed_v1/results.json.gz')
    lower = {r['scene']: r['lower'] for r in source['scene_envelopes']}
    models = []
    for name in [r['model'] for r in primary['summary'] if r['eta'] == 'half_second']:
        configs = [c for c in data['configurations'] if c['model'] == name and c['eta'] == 'half_second']
        keys = {k for c in configs for k in c['table_keys']}; saturation = []; cells = full = equal = 0
        for key in keys:
            table = data['tables'][key]; scene = key.split(':')[1]
            saturation.append(table['full_family_after_anchor_seconds'])
            for j, part in enumerate(table['parts']):
                for row in part.values():
                    cells += 1; full += row['full_family_samples'] == 10
                    equal += row['lower'] == lower[scene][j+2][2:]
        models.append({'model': name, 'unique_user_tables': len(keys), 'timing_cells': cells,
            'all_ten_samples_full_family_cells': full, 'exact_geometric_lower_cells': equal,
            'minimum_full_family_seconds_after_anchor': min(saturation),
            'median_full_family_seconds_after_anchor': median(saturation),
            'maximum_full_family_seconds_after_anchor': max(saturation)})
    motion = data['motion_statistics']; ratios = [r['whole_max_speed_microdeg_s']/r['one_hz_max_speed_microdeg_s']
                                                 for r in motion if r['one_hz_max_speed_microdeg_s'] > 0]
    return {'posthoc': True, 'model_or_contract_changed': False, 'models': models,
            'median_high_rate_to_one_hz_max_ratio': median(ratios), 'maximum_ratio': max(ratios),
            'zero_one_hz_max_trajectories': sum(r['one_hz_max_speed_microdeg_s'] == 0 for r in motion),
            'duplicates_removed': sum(r['identical_timestamp_duplicates_removed'] for r in motion),
            'sources': {'features': sha(DATA/'features.json.gz'), 'primary': sha(PRIMARY/'results.json.gz'),
                        'geometric': sha(ROOT/'geometric_admission/results/exposed_v1/results.json.gz'),
                        'script': sha(Path(__file__))}}


def figure():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    primary = read_gzip(PRIMARY/'results.json.gz'); data = read_gzip(DATA/'features.json.gz')
    rows = [r for r in primary['summary'] if r['eta'] == 'half_second' and r['model'].startswith('grid')]
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.6), layout='constrained')
    x = [r['median_speed_deg_s'] for r in rows]
    axes[0].plot(x, [100*r['source_pair_speed_consistent']/168 for r in rows], 'o-', color='#356477', label='Recorded pair speed consistency')
    axes[0].plot(x, [100*r['full_mask_fraction_on_max_paths'] for r in rows], 's--', color='#ac5a40', label='Full-mask samples on best paths')
    for name, marker in [('crossfit_p95', '^'), ('crossfit_max', 'D')]:
        r = next(r for r in primary['summary'] if r['eta'] == 'half_second' and r['model'] == name)
        axes[0].scatter([r['median_speed_deg_s']], [100*r['source_pair_speed_consistent']/168], marker=marker, color='#66774c', label=name)
    axes[0].set_xscale('log'); axes[0].set_ylim(-4, 105); axes[0].set_ylabel('Percent')
    axes[0].set_xlabel('Speed bound (deg/s; cross-fit points at median)')
    axes[0].set_title('A. Broader envelopes lose information'); axes[0].legend(fontsize=7, loc='lower right')
    motion = data['motion_statistics']
    low = [r['one_hz_max_speed_microdeg_s']/1e6 for r in motion]
    high = [r['whole_max_speed_microdeg_s']/1e6 for r in motion]
    axes[1].scatter(low, high, s=18, alpha=.65, color='#356477')
    limits = [min(min(low), min(high))*.9, max(max(low), max(high))*1.1]
    axes[1].plot(limits, limits, '--', color='gray', label='Equal maxima')
    axes[1].set_xscale('log'); axes[1].set_yscale('log'); axes[1].set_xlim(limits); axes[1].set_ylim(limits)
    axes[1].set_xlabel('1 Hz sampled maximum (deg/s)'); axes[1].set_ylabel('High-rate sampled maximum (deg/s)')
    axes[1].set_title('B. Coarse sampling misses fast changes'); axes[1].legend(fontsize=8)
    fig.suptitle('Exposed development audit: zero conditional certificates in all nine models', fontsize=11)
    fig.savefig(OUT/'temporal_model.png', dpi=180); fig.savefig(OUT/'temporal_model.svg', metadata={'Date': None}); plt.close(fig)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__); parser.add_argument('--verify', action='store_true'); args = parser.parse_args()
    result = analysis(); digest = hashlib.sha256(canonical(result)).hexdigest()
    if args.verify:
        meta = json.loads((OUT/'metadata.json').read_text())
        if json.loads((OUT/'results.json').read_text()) != result or meta['scientific_sha256'] != digest:
            raise ValueError('Diagnostic replay mismatch')
        for name, expected in meta['figures'].items():
            if sha(OUT/name) != expected: raise ValueError('Figure hash mismatch')
    else:
        OUT.mkdir(parents=True, exist_ok=False); figure()
        (OUT/'results.json').write_text(json.dumps(result, indent=2)+'\n')
        (OUT/'metadata.json').write_text(json.dumps({'scientific_sha256': digest, 'figures': {p.name: sha(p) for p in OUT.glob('temporal_model.*')}}, indent=2)+'\n')
    print(json.dumps({'verified': args.verify, 'scientific_sha256': digest,
                     'median_alias_ratio': result['median_high_rate_to_one_hz_max_ratio'], 'models': result['models']}))
