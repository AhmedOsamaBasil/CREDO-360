"""Reproducible analytical audit; no future participant quality/pose input."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from metric_contract.core import path_arrays, TICKS
from metric_contract.run import sha, canonical
from admission_contract.core import ETA, clocks, path_stats
from geometric_admission.geometry import validate_family, check_extrema
from geometric_admission.diagnose import upper_on_worst
from adaptive_audit.core import response_table, solve, score_path, feedback_visibility
from adaptive_audit.finite import analytic_cases

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'adaptive_audit/results/analytic_v1'
GEOMETRY = 'geometric_admission/results/exposed_v1'
DIAGNOSTIC = 'geometric_admission/results/diagnostics_v1'
MANIFEST = 'causal_playback/data/media_manifest.json'
TIMELINES = 'duration_contract/data/media_v1/timelines.json.gz'
MAPS = 'feedback_opportunity/data/maps_v1'
OWN = ('__init__.py', 'core.py', 'finite.py', 'run.py', 'test_core.py', 'test_validation.py', 'PLAN.md', 'THEORY.md')
DEPS = ('metric_contract/core.py', 'metric_contract/run.py', 'metric_contract/data.py',
        'duration_contract/core.py', 'duration_contract/run.py', 'admission_contract/core.py',
        'admission_contract/diagnose.py', 'geometric_admission/geometry.py',
        'geometric_admission/diagnose.py', 'feedback_opportunity/feedback.py')


def read_gzip(path):
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        return json.load(stream)


def prior_artifact(folder):
    result = read_gzip(ROOT/folder/'results.json.gz')
    meta = json.loads((ROOT/folder/'metadata.json').read_text())
    if hashlib.sha256(canonical(result)).hexdigest() != meta['scientific_sha256']:
        raise ValueError('Frozen predecessor scientific hash mismatch')
    return result


def provenance():
    paths = [MANIFEST, TIMELINES, MAPS+'/metadata.json']
    paths += [f'{folder}/{name}' for folder in (GEOMETRY, DIAGNOSTIC) for name in ('results.json.gz', 'metadata.json')]
    paths += [p.relative_to(ROOT).as_posix() for p in sorted((ROOT/MAPS).glob('*.npz'))]
    return {'source_sha256': {'adaptive_audit/'+n: sha(ROOT/'adaptive_audit'/n) for n in OWN},
            'dependency_sha256': {n: sha(ROOT/n) for n in DEPS},
            'input_sha256': {n: sha(ROOT/n) for n in paths}}


def scalar_response_check(maps, family, responses):
    """Independent explicit scalar cosine-weight sums; no matrix/scorer reuse."""
    area = [math.cos(math.radians(75-30*(i//12))) for i in range(72)]
    checks = 0
    for row in responses:
        native = []
        for rung in range(6):
            samples = []
            for j, mask_id in enumerate(row['mask_ids']):
                bits = int(family[mask_id]['mask_hex'], 16)
                ids = [i for i in range(72) if bits >> i & 1]
                denominator = math.fsum(area[i] for i in ids)
                samples.append(math.fsum(float(maps[rung, 10*row['segment']+j, i])*area[i]
                                         for i in ids)/denominator)
            native.append(math.floor(math.fsum(samples)/10*1e6+.5))
        if native != row['all_rung_native_mse'] or native[2]-native[row['committed_recipient_rung']] != row['signed_credit_rate']:
            raise ValueError('Independent native mask scoring mismatch')
        checks += 6
    return checks


def projected_entries(previous):
    """Project only key/content and already completed past-event debt."""
    result = [{k: b[k] for k in ('key', 'cohort', 'scene', 'loss')}
              for b in previous['bounds'] if b['eta'] == 'half_second']
    if len(result) != 168 or len({r['key'] for r in result}) != 168 or any(r['loss'] <= 0 for r in result):
        raise ValueError('Expected 168 positive past-event debts')
    return result


def analysis():
    old = prior_artifact(GEOMETRY); diagnostic = prior_artifact(DIAGNOSTIC)
    entries = projected_entries(old); masks = old['family']; checks = Counter(validate_family(masks))
    prior_bounds = {r['key']: r for r in diagnostic['constructed_witnesses']}
    files = json.loads((ROOT/MANIFEST).read_text())['files']
    sizes = {(r['cohort'], r['scene'], r['segment'], r['rung']): r['bytes'] for r in files}
    timelines = read_gzip(ROOT/TIMELINES)['rows']
    durations = {(r['cohort'], r['scene'], r['segment'], r['rung']): r['total_ticks'] for r in timelines}
    sources = {s['scene']: s for s in json.loads((ROOT/MAPS/'metadata.json').read_text())['sources']}
    envelopes = {s['scene']: s for s in old['scene_envelopes']}
    contexts = []; rows = []
    for scene, envelope in sorted(envelopes.items()):
        group = [r for r in entries if r['scene'] == scene]; cohort = group[0]['cohort']
        source = sources[scene]; path = ROOT/MAPS/source['map_file']
        if sha(path) != source['descriptor']:
            raise ValueError('Sender map hash mismatch')
        maps = np.load(path)['mse']; witness = envelope['extremal_mask_witnesses']
        check_extrema(maps, masks, np.array(envelope['lower']), np.array(envelope['upper']), witness)
        delta, responses = response_table(maps, masks, witness)
        checks['native_scalar_scores'] += scalar_response_check(maps, masks, responses)
        loose = upper_on_worst(envelope['lower'])
        if (delta[2:, 2:] > loose[2:, 2:]).any():
            raise ValueError('Native response exceeds prior rounding upper bound')
        costs = np.array([[sizes[cohort, scene, t, r] for r in range(6)] for t in range(6)], dtype=np.int64)
        ds = [durations[cohort, scene, t, 2] for t in range(6)]
        if any(durations[cohort, scene, t, r] != ds[t] for t in range(6) for r in range(6)):
            raise ValueError('Representation durations differ')
        reserve = int(2*costs[2:, 2].sum()); arrays = path_arrays(costs, 4, reserve)
        for eta in (0, ETA):
            mode = 'ideal' if eta == 0 else 'half_second'
            answer = solve(costs, ds, reserve, delta, eta)
            generous = solve(costs, ds, reserve, loose, eta)
            ends = clocks(costs, arrays['choices'], ds, eta)
            for reward, value in ((delta, answer), (loose, generous)):
                _, gain = path_stats(reward, arrays['choices'], ends, ds)
                if int(gain.max()) != value['credit_upper']:
                    raise ValueError('Independent complete-path maximum mismatch')
                checks['bellman_cartesian_queries'] += 1
                checks['complete_paths_checked'] += len(gain)
            scored = score_path(answer['path'], costs, ds, reserve, delta, eta)
            if scored['credit'] != answer['credit_upper'] or scored['extra_bytes'] != answer['extra_bytes']:
                raise ValueError('Maximizing path replay mismatch')
            if answer['credit_upper'] > generous['credit_upper']:
                raise ValueError('Response bound exceeds generous envelope')
            # Audit a fixed family of waiting choices, independent of outcomes.
            for waits in ([TICKS]*4, [40*TICKS, 0, 0, 0], [0, TICKS, 0, 0]):
                delayed = score_path(answer['path'], costs, ds, reserve, delta, eta, waits)
                if delayed['credit'] > scored['credit'] or any(a['recipient_end_ticks'] > b['recipient_end_ticks']
                         for a, b in zip(scored['steps'], delayed['steps'])):
                    raise ValueError('Waiting monotonicity failure')
                checks['waiting_checks'] += 1
            contexts.append({'scene': scene, 'cohort': cohort, 'eta': mode,
                'costs': costs.tolist(), 'durations_ticks': ds, 'reserve_bytes': reserve,
                'response_native_delta': delta.tolist(), 'action_conditioned_responses': responses,
                'best_response_game': answer, 'generous_upper_game': generous,
                'maximizing_path_ledger': scored,
                'feedback_timing': {str(delay): feedback_visibility(scored['steps'], ds, delay)
                                    for delay in (0, 12000, 75000)},
                'resource_paths': len(arrays['choices'])})
            for entry in group:
                if mode == 'half_second':
                    if generous['credit_upper'] != prior_bounds[entry['key']]['best_worst_case_credit_upper']:
                        raise ValueError('Historical fixed-plan upper bound parity failure')
                    checks['historical_bound_parity'] += 1
                rows.append({**entry, 'eta': mode, 'response_credit_upper': answer['credit_upper'],
                    'generous_credit_upper': generous['credit_upper'],
                    'adaptive_universal_half_ruled_out': 2*answer['credit_upper'] < entry['loss'],
                    'synthetic_not_observed_future': True})
        print(f'Analytical response audit: {scene}', flush=True)
    return {'exposed_only': True, 'contract_changed': False, 'future_participant_labels_used': False,
            'scope': 'deterministic causal whole-segment policies; unrestricted sampled geometric future masks',
            'quality_floors_relaxed_only_in_upper_bound': True,
            'synthetic_games': analytic_cases(), 'family': masks, 'contexts': contexts, 'rows': rows,
            'summary': [{'eta': mode, 'episodes': len(rs),
                         'universal_half_ruled_out': sum(r['adaptive_universal_half_ruled_out'] for r in rs),
                         'largest_response_credit_fraction': max(r['response_credit_upper']/r['loss'] for r in rs),
                         'largest_generous_credit_fraction': max(r['generous_credit_upper']/r['loss'] for r in rs)}
                        for mode in ('ideal', 'half_second') for rs in [[r for r in rows if r['eta'] == mode]]],
            'checks': dict(checks)}


def report(result):
    lines = ['# Adaptive-policy feasibility audit', '', result['scope'], '',
             '| Execution allowance | Episodes | Universal half promise ruled out | Largest response upper / debt |',
             '|---|---:|---:|---:|']
    for r in result['summary']:
        lines.append(f"| {r['eta']} | {r['episodes']} | {r['universal_half_ruled_out']} | {r['largest_response_credit_fraction']:.9%} |")
    lines += ['', 'These are conditional upper bounds with quality floors removed, not observed',
              'recovery rates or positive admission certificates. Synthetic response sequences',
              'are geometric model counterexamples, not measured human traces.', '',
              '## Exact information-order counterexamples', '',
              '| Constructed game | Fixed plan | Causal policy | Clairvoyant |', '|---|---:|---:|---:|']
    for name, r in result['synthetic_games']['cases'].items():
        lines.append(f"| {name} | {r['open_loop']} | {r['causal']} | {r['clairvoyant']} |")
    lines += ['', 'Causal column in the before-commit row intentionally has a different',
              'information order. It is not an allowed policy for the streaming audit.', '',
              'See THEORY.md for quantifiers, nonanticipation, waiting and scope boundaries.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(__doc__); parser.add_argument('--verify', action='store_true'); args = parser.parse_args()
    prov = provenance()
    if args.verify:
        meta = json.loads((OUT/'metadata.json').read_text())
        if any(meta[k] != v for k, v in prov.items()):
            raise ValueError('Frozen source/input provenance mismatch')
    elif OUT.exists():
        parser.error('Preserve frozen results; refusing overwrite')
    result = analysis(); digest = hashlib.sha256(canonical(result)).hexdigest(); rendered = report(result)
    if args.verify:
        if result != read_gzip(OUT/'results.json.gz') or meta['scientific_sha256'] != digest or (OUT/'REPORT.md').read_text() != rendered:
            raise ValueError('Complete analytical replay mismatch')
    else:
        OUT.mkdir(parents=True)
        (OUT/'results.json.gz').write_bytes(gzip.compress(canonical(result), mtime=0))
        (OUT/'metadata.json').write_text(json.dumps({**prov, 'scientific_sha256': digest}, indent=2)+'\n')
        (OUT/'REPORT.md').write_text(rendered)
    print(json.dumps({'verified': args.verify, 'scientific_sha256': digest, 'summary': result['summary'], 'checks': result['checks']}))


if __name__ == '__main__':
    main()
