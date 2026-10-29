"""Public replay of conditional temporal certificates from scalar bound tables."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from itertools import product
from statistics import mean, median
import numpy as np
from metric_contract.run import canonical, sha
from metric_contract.core import path_arrays, CAP, SLOT, SETUP
from admission_contract.core import clocks, ETA
from duration_contract.core import DEADLINE
from adaptive_audit.run import read_gzip
from temporal_viewport.core import GRID, SCALE, fit_speed
from temporal_viewport.prepare import ROOT, OUT as DATA, provenance

OUT = ROOT/'temporal_viewport/results/exposed_v1'


def score_arrays(tables, paths, ends, durations):
    safe = np.ones(len(paths), dtype=bool); credit = np.zeros(len(paths), dtype=np.int64)
    full = np.zeros(len(paths), dtype=np.int64)
    for j, t in enumerate(range(2, 6)):
        for u in (0, 1):
            values = np.empty(len(paths), dtype=np.int64)
            for e in np.unique(ends[:, j, u]):
                keep = ends[:, j, u] == e; row = tables[u]['parts'][j][str(int(e))]
                values[keep] = np.array(row['lower'])[paths[keep, j, u]-2]
                if u == 0:
                    full[keep] += row['full_family_samples']
            safe &= values >= 0
            if u == 0:
                credit += np.maximum(0, values)*durations[t]*(ends[:, j, 0] <= DEADLINE)
    return safe, credit, full


def independent(tables, costs, durations, reserve, loss, eta):
    """Independent scalar resource/clock DFS for a fixed predeclared subset."""
    maximum = 0; minimum_cost = None; count = 0
    def visit(t, spent, request, end0, end1, safe, credit):
        nonlocal maximum, minimum_cost, count
        if t == 6:
            count += 1
            if safe:
                maximum = max(maximum, credit)
                if 2*credit >= loss:
                    minimum_cost = spent if minimum_cost is None else min(spent, minimum_cost)
            return
        for a, b in product(range(2, 6), repeat=2):
            sa, sb = int(costs[t, a]), int(costs[t, b]); total = sa+sb
            extra = max(0, total-2*int(costs[t, 2]))
            if total > CAP or spent+extra > reserve:
                continue
            arrivals = (request+SETUP+min(2*sa, total), request+SETUP+min(2*sb, total))
            ends = (max(end0, arrivals[0])+durations[t]+eta, max(end1, arrivals[1])+durations[t]+eta)
            lower = [tables[u]['parts'][t-2][str(ends[u])]['lower'][r-2] for u, r in enumerate((a, b))]
            gain = max(0, lower[0])*durations[t] if ends[0] <= DEADLINE else 0
            visit(t+1, spent+extra, max(request+SLOT, *arrivals), *ends,
                  safe and min(lower) >= 0, credit+gain)
    visit(2, 0, 0, 0, 0, True, 0)
    return maximum, minimum_cost, count


def scalar_witness(tables, path, costs, ds, reserve, eta):
    request = 0; ends = [0, 0]; spent = gain = full = 0; safe = True
    for j, (a, b) in enumerate(path):
        t = j+2; sa, sb = int(costs[t, a]), int(costs[t, b]); total = sa+sb
        spent += max(0, total-2*int(costs[t, 2]))
        if total > CAP or spent > reserve: raise ValueError('Invalid resource witness')
        arrival = [request+SETUP+min(2*s, total) for s in (sa, sb)]
        ends = [max(ends[u], arrival[u])+ds[t]+eta for u in (0, 1)]
        request = max(request+SLOT, *arrival)
        values = [tables[u]['parts'][j][str(ends[u])]['lower'][r-2] for u, r in enumerate((a, b))]
        safe &= min(values) >= 0
        gain += max(0, values[0])*ds[t] if ends[0] <= DEADLINE else 0
        full += tables[0]['parts'][j][str(ends[0])]['full_family_samples']
    return bool(safe), gain, spent, full


def analysis():
    data = read_gzip(DATA/'features.json.gz'); meta = json.loads((DATA/'metadata.json').read_text())
    if hashlib.sha256(canonical(data)).hexdigest() != meta['scientific_sha256']:
        raise ValueError('Derived scalar feature hash mismatch')
    if any(meta[k] != v for k, v in provenance().items()):
        raise ValueError('Frozen preparation source changed')
    cache = {}; rows = []; checks = Counter(); first = {}
    for config in data['configurations']:
        key = config['key']; cohort, scene, recipient, donor = key.split(':'); mode = config['eta']
        first.setdefault(scene, key)
        if config['model'].startswith('crossfit'):
            q = .95 if config['model'] == 'crossfit_p95' else 1.
            speed, train = fit_speed(data['motion_statistics'], scene, {int(recipient), int(donor)}, q)
            if speed != config['speed_microdeg_s'] or train != config['training_keys']:
                raise ValueError('Cross-fit training or threshold mismatch')
            checks['crossfit_exclusion_queries'] += 1
        context = data['contexts'][scene]; ds = context['durations_ticks']; costs = np.array(context['costs'])
        eta = 0 if mode == 'ideal' else ETA
        if (scene, mode) not in cache:
            arrays = path_arrays(costs, 4, context['reserve_bytes'])
            cache[scene, mode] = arrays, clocks(costs, arrays['choices'], ds, eta)
        arrays, ends = cache[scene, mode]; paths = arrays['choices']
        tables = [data['tables'][k] for k in config['table_keys']]
        safe, credit, full = score_arrays(tables, paths, ends, ds)
        ids = np.flatnonzero(safe)
        if not len(ids): raise ValueError('Reference baseline must be safe')
        best = int(min(ids, key=lambda i: (-int(credit[i]), int(arrays['cost'][i]), int(i))))
        success = np.flatnonzero(safe & (2*credit >= config['loss']))
        admitted = int(min(success, key=lambda i: (int(arrays['cost'][i]), -int(credit[i]), int(i)))) if len(success) else None
        witness = scalar_witness(tables, paths[best].tolist(), costs, ds, context['reserve_bytes'], eta)
        if witness != (True, int(credit[best]), int(arrays['cost'][best]), int(full[best])):
            raise ValueError('Independent maximizing witness mismatch')
        checks['maximizing_witnesses'] += 1; checks['path_appearances'] += len(paths)
        if key == first[scene]:
            bound, minimum, count = independent(tables, costs, ds, context['reserve_bytes'], config['loss'], eta)
            if bound != int(credit[best]) or minimum != (int(arrays['cost'][admitted]) if admitted is not None else None) or count != len(paths):
                raise ValueError('Independent complete scalar search mismatch')
            checks['independent_full_search_queries'] += 1
        rows.append({k: config[k] for k in ('key', 'cohort', 'scene', 'model', 'eta', 'loss', 'speed_microdeg_s', 'observed_source_speed_covered')} | {
            'conditional_certificate': admitted is not None,
            'source_pair_speed_consistent': all(config['observed_source_speed_covered']),
            'maximum_lower_credit': int(credit[best]), 'maximum_path': paths[best].tolist(),
            'certificate_path': paths[admitted].tolist() if admitted is not None else None,
            'certificate_extra_bytes': int(arrays['cost'][admitted]) if admitted is not None else None,
            'recipient_full_family_samples_max_path': int(full[best])})
    # A larger speed gives a superset of masks: its best guaranteed credit cannot rise.
    lookup = {(r['key'], r['eta'], r['model']): r for r in rows}
    for key, mode in {(r['key'], r['eta']) for r in rows}:
        ordered = [lookup[key, mode, f'grid_{v}'] for v in GRID]
        for a, b in zip(ordered, ordered[1:]):
            if a['maximum_lower_credit'] < b['maximum_lower_credit']:
                raise ValueError('Velocity nesting violation')
            checks['velocity_nesting_pairs'] += 1
    summaries = []
    for mode in ('ideal', 'half_second'):
        for model in [f'grid_{v}' for v in GRID]+['crossfit_p95', 'crossfit_max']:
            rs = [r for r in rows if r['eta'] == mode and r['model'] == model]
            summaries.append({'eta': mode, 'model': model, 'episodes': len(rs),
                'source_pair_speed_consistent': sum(r['source_pair_speed_consistent'] for r in rs),
                'conditional_certificates': sum(r['conditional_certificate'] for r in rs),
                'certificates_with_source_speed_consistency': sum(r['conditional_certificate'] and r['source_pair_speed_consistent'] for r in rs),
                'mean_lower_credit_fraction': mean(r['maximum_lower_credit']/r['loss'] for r in rs),
                'full_mask_fraction_on_max_paths': sum(r['recipient_full_family_samples_max_path'] for r in rs)/(40*len(rs)),
                'minimum_speed_deg_s': min(r['speed_microdeg_s'] for r in rs)/SCALE,
                'median_speed_deg_s': median(r['speed_microdeg_s'] for r in rs)/SCALE,
                'maximum_speed_deg_s': max(r['speed_microdeg_s'] for r in rs)/SCALE})
    motion = data['motion_statistics']
    return {'exposed_only': True, 'service_contract_changed': False, 'new_controller': False,
            'bound_kind': 'conditional entry-anchor cone sufficient certificate; not exact coupled feasibility',
            'coverage_kind': 'recorded source-clock sampled-speed diagnostic; not future/deployment guarantee',
            'rows': rows, 'summary': summaries, 'checks': dict(checks),
            'motion_summary': {'trajectories': len(motion), 'source_observations': sum(r['observations'] for r in motion),
                'minimum_source_dt': min(r['minimum_interval_seconds'] for r in motion),
                'median_source_dt': median(r['median_interval_seconds'] for r in motion),
                'whole_max_speed_deg_s_range': [min(r['whole_max_speed_microdeg_s'] for r in motion)/SCALE, max(r['whole_max_speed_microdeg_s'] for r in motion)/SCALE],
                'high_rate_exceeds_one_hz': sum(r['whole_max_speed_microdeg_s'] > r['one_hz_max_speed_microdeg_s'] for r in motion)}}


def report(result):
    lines = ['# Temporal viewport model: coverage and conditional usefulness', '', result['bound_kind'], '', result['coverage_kind'], '',
             '| Model | Source-speed consistent pairs | Conditional certificates | Both | Full-mask samples on best paths |',
             '|---|---:|---:|---:|---:|']
    for r in result['summary']:
        if r['eta'] == 'half_second':
            lines.append(f"| {r['model']} | {r['source_pair_speed_consistent']}/168 | {r['conditional_certificates']}/168 | {r['certificates_with_source_speed_consistency']}/168 | {r['full_mask_fraction_on_max_paths']:.2%} |")
    lines += ['', 'Neither sampled consistency nor an empirical training maximum is a hard',
              'future-motion guarantee. Zero certificates do not prove impossibility',
              'for the temporally coupled model or for all adaptive policies.', '']
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__); parser.add_argument('--verify', action='store_true'); args = parser.parse_args()
    prov = {'prepared_features_sha256': sha(DATA/'features.json.gz'), 'preparation_metadata_sha256': sha(DATA/'metadata.json'), **provenance()}
    if not args.verify and OUT.exists(): parser.error('Preserve earlier outcomes')
    result = analysis(); digest = hashlib.sha256(canonical(result)).hexdigest(); rendered = report(result)
    if args.verify:
        meta = json.loads((OUT/'metadata.json').read_text())
        if any(meta[k] != v for k, v in prov.items()) or meta['scientific_sha256'] != digest or read_gzip(OUT/'results.json.gz') != result or (OUT/'REPORT.md').read_text() != rendered:
            raise ValueError('Public replay mismatch')
    else:
        OUT.mkdir(parents=True); (OUT/'results.json.gz').write_bytes(gzip.compress(canonical(result), mtime=0))
        (OUT/'metadata.json').write_text(json.dumps({**prov, 'scientific_sha256': digest}, indent=2)+'\n'); (OUT/'REPORT.md').write_text(rendered)
    print(json.dumps({'verified': args.verify, 'scientific_sha256': digest, 'motion_summary': result['motion_summary'],
                      'primary_summary': [r for r in result['summary'] if r['eta'] == 'half_second'], 'checks': result['checks']}))
