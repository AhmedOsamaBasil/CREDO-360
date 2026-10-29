"""Reconcile frozen evidence without rerunning controllers or changing contracts."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
from feasibility_synthesis.claims import make_claim

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'feasibility_synthesis/results/synthesis_v1'
INPUTS = {
    'metric': 'metric_contract/results/sensitivity_v1/results.json.gz',
    'duration': 'duration_contract/results/replay_v1/results.json.gz',
    'paced': 'duration_contract/results/measured_audit_v1/results.json',
    'geometry': 'geometric_admission/results/exposed_v1/results.json.gz',
    'adaptive': 'adaptive_audit/results/analytic_v1/results.json.gz',
    'temporal': 'temporal_viewport/results/exposed_v1/results.json.gz',
    'temporal_diagnostic': 'temporal_viewport/results/diagnostics_v1/results.json',
}
MODES = ('ideal', 'half_second')
MODELS = tuple('grid_'+str(v) for v in (5, 15, 30, 60, 90, 180, 360)) + ('crossfit_p95', 'crossfit_max')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_inputs(root=ROOT):
    data = {}
    for name, relative in INPUTS.items():
        path = root/relative
        with (gzip.open(path, 'rt', encoding='utf-8') if path.suffix == '.gz'
              else path.open(encoding='utf-8')) as stream:
            value = json.load(stream)
        meta = json.loads(path.with_name('metadata.json').read_text(encoding='utf-8'))
        require(digest(value) == meta['scientific_sha256'], 'Frozen artifact hash mismatch: '+name)
        data[name] = value
    return data


def index(rows, fields, expected=None):
    result = {}
    for row in rows:
        key = tuple(row[f] for f in fields)
        require(key not in result, 'Duplicate evidence cell: '+str(key))
        result[key] = row
    if expected is not None:
        require(set(result) == set(expected), 'Missing or unexpected evidence cells')
    return result


def summarize(data):
    geo, adaptive, temporal = (data[n] for n in ('geometry', 'adaptive', 'temporal'))
    for name in ('metric', 'geometry', 'adaptive', 'temporal'):
        require(data[name]['exposed_only'], 'Exposed-only input required')
    require(not data['metric']['fresh_holdout'] and not data['metric']['new_controller_tuned'], 'No new holdout/tuning')
    require(not geo['contract_changed'] and not adaptive['contract_changed'] and
            not temporal['service_contract_changed'], 'Fixed contract changed')
    require(not adaptive['future_participant_labels_used'] and
            adaptive['quality_floors_relaxed_only_in_upper_bound'], 'Adaptive proof scope changed')

    keys = {r['key'] for r in geo['bounds']}
    require(len(keys) == 168, 'Expected the 168 exposed directed episodes')
    expected = {(key, mode) for key in keys for mode in MODES}
    geometry = index(geo['bounds'], ('key', 'eta'), expected)
    limits = index(adaptive['rows'], ('key', 'eta'), expected)
    motion = index(temporal['rows'], ('key', 'eta', 'model'),
                   {(k, m, model) for k, m in expected for model in MODELS})
    controls = index((r for r in geo['rows'] if r['eta'] in MODES), ('key', 'eta', 'method'),
                     {(k, m, method) for k, m in expected for method in (
                         'certified_planner', 'point_planner', 'cost_greedy', 'rolling_nash', 'maxmin',
                         'point_planner_certified', 'cost_greedy_certified', 'rolling_nash_certified', 'maxmin_certified')})
    contexts = index(adaptive['contexts'], ('scene', 'eta'))
    cases = []
    for key, mode in sorted(expected):
        g, a = geometry[key, mode], limits[key, mode]
        loss = g['loss']; require(loss > 0 and loss == a['loss'], 'Loss ledger mismatch')
        c = g['certificate']; upper = c['upper_credit']
        require(c['status'] in ('admit', 'impossible', 'abstain'), 'Unknown certificate status')
        if c['status'] == 'impossible':
            require(2*upper < loss and not g['oracle_feasible'], 'Optimistic rejection contradicts known trace')
        require(g['oracle_feasible'] == (2*g['oracle_max_credit'] >= loss), 'Known-trace threshold mismatch')
        ruled_out = 2*a['response_credit_upper'] < loss
        require(a['adaptive_universal_half_ruled_out'] == ruled_out and a['synthetic_not_observed_future'], 'Universal bound scope/threshold mismatch')
        p, greedy = (controls[key, mode, method] for method in ('point_planner', 'cost_greedy'))
        equal = p['executed_path'] == greedy['executed_path']
        require(equal and p['admitted'] == greedy['admitted'] and p['score'] == greedy['score'],
                'Point planner and cost-greedy no longer equivalent in frozen replay')
        ms = [motion[key, mode, model] for model in MODELS]
        require(all(r['loss'] == loss for r in ms), 'Temporal loss ledger mismatch')
        require(all(r['conditional_certificate'] == (2*r['maximum_lower_credit'] >= loss) for r in ms),
                'Temporal certificate threshold mismatch')
        context = contexts[g['scene'], mode]
        require(context['reserve_bytes'] == sum(2*context['costs'][t][2] for t in range(2, 6)),
                'R4 reserve differs from reference entitlement')
        category = ('optimistic_infeasible' if c['status'] == 'impossible' else
                    'trace_feasible_not_guaranteed' if g['oracle_feasible'] else
                    'trace_infeasible_without_optimistic_rejection')
        cases.append({'key': key, 'eta': mode, 'scene': g['scene'], 'category': category,
            'loss_micro_mse_ticks': loss, 'geometric_status': c['status'],
            'optimistic_credit_upper': upper, 'observed_trace_credit_max': g['oracle_max_credit'],
            'observed_trace_feasible': g['oracle_feasible'],
            'unrestricted_deterministic_policy_credit_upper': a['response_credit_upper'],
            'unrestricted_universal_promise_ruled_out': ruled_out,
            'point_admitted': p['admitted'], 'point_fulfilled_in_replay': p['protected_success'],
            'point_equals_cost_greedy': equal,
            'temporal_model_certificates': {r['model']: r['conditional_certificate'] for r in ms},
            'temporal_source_speed_consistency': {r['model']: r['source_pair_speed_consistent'] for r in ms},
            'reserve_bytes': context['reserve_bytes']})

    # Exact-duration historical replay is ideal timing, not the half-second model.
    duration = data['duration']
    oracle = index((r for r in duration['bounds'] if r['mode'] == 'actual'), ('key',), {(k,) for k in keys})
    for (key,), d in oracle.items():
        g = geometry[key, 'ideal']
        require(d['loss_micro_mse_ticks'] == g['loss'] and d['deadline']['gain'] == g['oracle_max_credit'],
                'Ideal known-trace cross-artifact mismatch')
    policies = sorted({r['policy'] for r in duration['rows'] if r['mode'] == 'actual'})
    replay = index((r for r in duration['rows'] if r['mode'] == 'actual'), ('key', 'policy'),
                   {(k, p) for k in keys for p in policies})
    policy_counts = {p: sum(replay[k, p]['protected_half_by_deadline'] for k in keys) for p in policies}

    metric = data['metric']; require(metric['target_quarters'] == [1, 2, 3, 4], 'Target order changed')
    mapping = []
    for name in ('index', 'fine_index', 'psnr_db', 'negative_mse'):
        for clock in ('media', 'deadline'):
            rows = [r for r in metric['oracle_rows'] if r['impairment'] == 0 and r['horizon'] == 4
                    and r['metric'] == name and r['clock'] == clock]
            index(rows, ('key',), {(k,) for k in keys})
            count = sum(r['targets_met'][1] for r in rows)
            prior = [r for r in metric['summary'] if r['impairment'] == 0 and r['horizon'] == 4
                     and r['metric'] == name and r['clock'] == clock and r['group'] == 'all' and r['policy'] == 'offline']
            require(len(prior) == 1 and count == prior[0]['targets_met'][1], 'Metric summary mismatch')
            mapping.append({'metric': name, 'clock': clock, 'episodes': len(rows), 'half_feasible': count,
                            'contract': 'historical nominal ten-second metric-sensitivity contract'})

    paced = data['paced']; require(paced['sessions'] == len(paced['rows']) == 19, 'Paced session count changed')
    require(paced['frames_checked'] == sum(r['frames_checked'] for r in paced['rows']), 'Frame count mismatch')
    negatives = [r for r in paced['rows'] if r['negative_control']]
    require(len(negatives) == 1 and negatives[0]['deadline_credit'] == 0 and paced['negative_control_pass'], 'Negative control mismatch')
    measured = []
    for p in ('prefix_mpc', 'prefix_cost_greedy', 'baseline'):
        rows = [r for r in paced['rows'] if r['policy'] == p and not r['negative_control']]
        require(len(rows) == 6, 'Incomplete paced policy cells')
        measured.append({'policy': p, 'sessions': len(rows), 'protected_half': sum(r['protected_half_by_deadline'] for r in rows)})

    grouped = []
    scenes = sorted({r['scene'] for r in cases})
    for mode in MODES:
        for group in ['all']+scenes:
            rs = [r for r in cases if r['eta'] == mode and (group == 'all' or r['scene'] == group)]
            grouped.append({'eta': mode, 'group': group, 'episodes': len(rs),
                'categories': dict(sorted(Counter(r['category'] for r in rs).items())),
                'trace_feasible': sum(r['observed_trace_feasible'] for r in rs),
                'unrestricted_universal_ruled_out': sum(r['unrestricted_universal_promise_ruled_out'] for r in rs),
                'largest_universal_upper_fraction': max(r['unrestricted_deterministic_policy_credit_upper']/r['loss_micro_mse_ticks'] for r in rs),
                'point_promises': sum(r['point_admitted'] for r in rs),
                'point_fulfilled': sum(r['point_admitted'] and r['point_fulfilled_in_replay'] for r in rs),
                'temporal_certificates_by_model': {m: sum(r['temporal_model_certificates'][m] for r in rs) for m in MODELS}})

    claims = [make_claim(kind, statement, sources) for kind, statement, sources in (
        ('known_trace', 'Known-trace feasibility and point-prediction success do not establish a universal admission promise.', ['geometry', 'duration']),
        ('optimistic_rejection', 'An optimistic upper bound below the target rules out that finite-contract promise even before selecting a scheduler.', ['geometry']),
        ('universal_policy_limit', 'Per-policy adversarial sequences bound deterministic causal whole-segment policies under temporally unrestricted sampled viewports.', ['adaptive']),
        ('failed_temporal_certificate', 'Zero entry-cone certificates do not prove coupled-motion infeasibility; empirical source-speed consistency is not deployment coverage.', ['temporal', 'temporal_diagnostic']),
        ('paced_measurement', 'The pacing audit measures decoder and software-event timing for scripted arrivals, not physical display or network delivery.', ['paced']),
    )]
    return {'posthoc_synthesis': True, 'new_experiments': 0, 'new_controller': False,
        'contract_changed': False, 'submission_ready': False,
        'sampling': {'directed_episodes': len(keys), 'scenes': scenes,
                     'participant_identifiers': len({s for k in keys for s in k.split(':')[2:]}),
                     'independent_replication': False, 'timing_rows_not_independent_episodes': len(cases)},
        'source_json_sha256': {name: digest(value) for name, value in data.items()},
        'contract': {'target_fraction': '1/2', 'deadline_seconds': 40, 'metric': 'native micro-MSE times actual duration',
            'credit': 'completed segments only', 'reference_rung': 2, 'initial_impairment_rung': 0,
            'recovery_rungs': [2, 3, 4, 5], 'round_cap_bytes': 1500000, 'reserve': 'R4 nonrefilling extra bytes',
            'service': 'assumed 1.2Mbps payload plus 0.13s setup', 'execution_modes': list(MODES),
            'viewport': '216 angular-window tile-centre masks; not perspective frusta',
            'users_per_episode': 2, 'recovery_segments': 4},
        'cases': cases, 'summary': grouped, 'metric_sensitivity_separate_contract': mapping,
        'historical_actual_duration_ideal_replay': {'protected_half_by_policy': policy_counts, 'episodes': len(keys)},
        'paced_measurement': {'scope': paced['scope'], 'sessions': paced['sessions'],
            'frames': paced['frames_checked'], 'negative_control_zero_credit': True, 'policies': measured},
        'claims': claims}


def report(result):
    lines = ['# Feasibility evidence: what each result can establish', '',
        'Post-outcome reconciliation of frozen artifacts; no new experiment, optimization or significance test.', '',
        '## Primary conditional contract: 0.5-second execution allowance', '',
        '| Scene | Episodes | Optimistic infeasible | Trace feasible, not guaranteed | Trace infeasible without optimistic rejection |',
        '|---|---:|---:|---:|---:|']
    for r in result['summary']:
        if r['eta'] == 'half_second':
            c = r['categories']
            lines.append(f"| {r['group']} | {r['episodes']} | {c.get('optimistic_infeasible', 0)} | {c.get('trace_feasible_not_guaranteed', 0)} | {c.get('trace_infeasible_without_optimistic_rejection', 0)} |")
    lines += ['', 'The three columns partition episodes within one timing condition. They are NOT three independent experiments.',
        'All trace-feasible cases still fail the universal-policy promise under unrestricted future sampled masks.',
        'Zero temporal lower certificates are not an impossibility result for coupled motion.', '',
        '## Metric sensitivity (separate historical nominal-duration contract)', '',
        '| Metric | Clock | Known-trace half-feasible /168 |', '|---|---|---:|']
    for r in result['metric_sensitivity_separate_contract']:
        lines.append(f"| {r['metric']} | {r['clock']} | {r['half_feasible']} |")
    lines += ['', 'These metric cells are not pooled with the fixed actual-duration contract.', '', '## Claim qualifiers', '']
    for c in result['claims']:
        lines += [f"### {c['kind']}", '', c['statement'], '', 'Required qualifiers: '+', '.join(c['qualifiers'])+'.', '']
    lines += ['## Measurement boundary', '',
        f"{result['paced_measurement']['sessions']} existing paced sessions and {result['paced_measurement']['frames']} frame checks; "+result['paced_measurement']['scope']+'.',
        'The 19 sessions and 336 timing rows are not new subjects or independent replications.',
        'All original scientific artifacts remain unchanged. This report validates joins and scopes, not every original optimizer.', '']
    return '\n'.join(lines)


def provenance():
    names = ('__init__.py', 'claims.py', 'synthesize.py', 'test_synthesis.py')
    return {n: hashlib.sha256((ROOT/'feasibility_synthesis'/n).read_bytes().replace(b'\r\n', b'\n')).hexdigest() for n in names}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--episode', help='Print one verified historical case; not a deployment admission API')
    parser.add_argument('--eta', choices=MODES, default='half_second')
    args = parser.parse_args()
    result = summarize(load_inputs()); rendered = report(result)
    meta = {'scientific_sha256': digest(result), 'source_sha256': provenance(), 'inputs': INPUTS}
    if args.build:
        OUT.mkdir(parents=True, exist_ok=False)
        (OUT/'summary.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n', encoding='utf-8')
        (OUT/'REPORT.md').write_text(rendered, encoding='utf-8')
        (OUT/'metadata.json').write_text(json.dumps(meta, indent=2, sort_keys=True)+'\n', encoding='utf-8')
    else:
        require(json.loads((OUT/'summary.json').read_text()) == result, 'Saved synthesis mismatch')
        require((OUT/'REPORT.md').read_text() == rendered, 'Saved report mismatch')
        require(json.loads((OUT/'metadata.json').read_text()) == meta, 'Synthesis source/input binding mismatch')
    if args.episode:
        matches = [r for r in result['cases'] if r['key'] == args.episode and r['eta'] == args.eta]
        require(len(matches) == 1, 'Unknown historical episode')
        print(json.dumps({'case': matches[0], 'contract': result['contract'], 'claims': result['claims'],
                          'retrospective_diagnostic_only': True, 'deployment_admission': False}, indent=2))
    else:
        print(json.dumps({'verified': not args.build, 'scientific_sha256': digest(result),
                          'summary': [r for r in result['summary'] if r['group'] == 'all'], 'new_experiments': 0}))


if __name__ == '__main__':
    main()
