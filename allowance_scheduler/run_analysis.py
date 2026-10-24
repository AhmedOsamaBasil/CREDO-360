"""Publish all exact policy mixtures, certificates, comparisons and failures."""
import argparse
from dataclasses import asdict
from fractions import Fraction as F
import hashlib
import json
import platform
from pathlib import Path
from allowance_scheduler.cases import problems, two_future
from allowance_scheduler.core import plan, expected_summary, execute
from allowance_scheduler.checks import model_checks
from recovery_objective.core import ONLINE_POLICIES, online, oracle
from recovery_objective.run_analysis import encode

ROOT = Path(__file__).resolve().parents[1]


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def analysis():
    cases = []
    for p in problems():
        planned = plan(p.scenarios, p.contract)
        weights = planned['solution']['weights']
        comparisons = {'mixed_regret': expected_summary(planned, weights)}
        for name in ('deterministic_regret', 'absolute_minimax'):
            onehot = tuple(F(int(i == planned[name])) for i in range(len(weights)))
            comparisons[name] = expected_summary(planned, onehot)
        for name in ONLINE_POLICIES:
            rows = []
            for s, benchmark in zip(p.scenarios, planned['benchmarks']):
                row = online(name, s, p.contract, p.history)
                row['regret'] = row['terminal_max_fraction']-benchmark
                row['all_recovered_probability'] = F(int(row['all_recovered']))
                rows.append(row)
            comparisons[name] = tuple(rows)
        cases.append({'problem': asdict(p), 'offline_primary_values': planned['benchmarks'],
                      'policy_paths': tuple(tuple(tuple(a.name for a in path) for path in rule.paths) for rule in planned['policies']),
                      'all_policy_outcomes': planned['outcomes'], 'regret_matrix': planned['regrets'],
                      'solution': planned['solution'], 'deterministic_regret_index': planned['deterministic_regret'],
                      'absolute_minimax_index': planned['absolute_minimax'], 'comparisons': comparisons,
                      'worst_expected_regret': {name: max(r['regret'] for r in rows) for name, rows in comparisons.items()},
                      'worst_expected_unpaid_fraction': {name: max(r['terminal_max_fraction'] for r in rows) for name, rows in comparisons.items()},
                      'pathwise_donor_maxima': tuple(max(planned['outcomes'][i][s]['donor_spent'][u]
                                                        for i, w in enumerate(weights) if w for s in range(len(p.scenarios)))
                                                     for u in range(len(p.contract.debt)))})
    # Explicitly adverse model miss: believing only the favorable later offer.
    future = two_future()
    optimistic = plan((future.scenarios[1],), future.contract)
    missed = []
    for rule, weight in zip(optimistic['policies'], optimistic['solution']['weights']):
        if weight:
            actual = execute(rule, future.contract, future.scenarios[0])
            missed.append({'weight': weight, 'actual': actual,
                           'actual_regret': actual['terminal_max_fraction']-oracle(future.scenarios[0], future.contract)['terminal_max_fraction']})
    main = plan(future.scenarios, future.contract)
    adaptive = sum((w*max(row) for w, row in zip(main['solution']['weights'], main['regrets'])), F(0))
    return encode({'analytical_only': True, 'new_empirical_data': False, 'arithmetic': 'exact rational',
                   'cases': cases, 'model_miss': {'declared_certificate': optimistic['solution']['value'], 'outcomes': missed},
                   'adaptive_adversary': {'oblivious_certificate': main['solution']['value'], 'coin_observing_expected_regret': adaptive},
                   'checks': model_checks()})


def report(payload):
    lines = ['# Exact allowance-scheduling analysis', '',
             '**Analytical constructions only. No media, HMD data or new experiments.** '
             'All expectations below are over the controller\'s own episode-level randomization, '
             'not a presumed distribution of future scenarios. The future set is supplied, '
             'not fitted or calibrated. Only an offline benchmark knows the realized future.', '',
             'The primary loss is the maximum unpaid fraction across recipients at the deadline. '
             'Regret subtracts the future-known optimum for that same scenario. Lower regret '
             'does not imply smaller worst absolute loss, higher quality, or zero unpaid debt.', '']
    for case in payload['cases']:
        p = case['problem']
        lines += ['## '+p['name'], '', p['description'], '',
                  f"Exact minimax expected-regret value: **{case['solution']['value']}**; duality gap **{case['solution']['certificate']['gap']}**.", '',
                  '| Rule | Worst expected regret | Worst expected unpaid fraction |', '|---|---:|---:|']
        for name in case['comparisons']:
            lines.append(f"| {name} | {case['worst_expected_regret'][name]} | {case['worst_expected_unpaid_fraction'][name]} |")
        lines += ['', '| Future | Rule | Expected unpaid fraction | Expected regret | Expected donor loss | Expected worst post-quality |',
                  '|---|---|---:|---:|---|---:|']
        for j, name in enumerate(p['scenario_names']):
            for policy in ('mixed_regret', 'rolling_nash', 'rolling_maxmin', 'greedy_recovery'):
                r = case['comparisons'][policy][j]
                lines.append(f"| {name} | {policy} | {r['terminal_max_fraction']} | {r['regret']} | {r['donor_spent']} | {r['worst_post_quality']} |")
        lines += ['', 'Selected policies (chosen once per episode):', '']
        for i, w in enumerate(case['solution']['weights']):
            if F(w): lines.append(f"- Policy {i}, probability {w}; actions by future: {case['policy_paths'][i]}.")
        lines += ['', 'The differently named future branches above are for reporting only. '
                  'The executor receives current observations, not those names. Shared observed '
                  'prefixes have identical actions within each selected causal policy.', '']
    lines += ['## Preserved failures and limits', '',
              '- Misspecified model: declaring only the better-later future gives a zero certificate. '
              'When the opportunity actually disappears, realized regret is 1/2 and the model-breach flag is set. '
              'The fallback respects the remaining service-loss budget but cannot recover the missed opportunity.',
              '- Coin-observing adversary: on the two-future witness it raises expected regret from the '
              'oblivious bound 1/4 to 1/2. The guarantee requires an exogenous future independent of the sampled policy.',
              '- Absolute loss trade-off: on the ambiguous witness the mixed rule has worst expected '
              'unpaid fraction 3/4; greedy/absolute-minimax have 1/2. Regret is a distinct objective.',
              '- Zero regret with no allowance/headroom still leaves all event debt unpaid.',
              '- Singletons are perfect-model illustrations, not evidence that a forecast is accurate.', '',
              '## Verification scope', '',
              f"- {len(payload['checks']['closed_form_cases'])} exact parameter cases match the two-future probability/bound formula.",
              f"- {payload['checks']['matrix_games_checked']} finite games have exact primal/dual certificates.",
              f"- {payload['checks']['causal_policy_scenario_executions']} executions cover every enumerated policy and in-set scenario in the eight constructions, not just selected winners.",
              '- No p-values, holdout claim, general superiority claim or new minimax theorem is made.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'allowance_scheduler/results/analytic_v1')
    args = parser.parse_args()
    if args.output.exists(): parser.error('output exists; preserve the saved analysis')
    payload = analysis()
    args.output.mkdir(parents=True)
    (args.output/'results.json').write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    (args.output/'REPORT.md').write_text(report(payload), encoding='utf-8')
    sources = sorted(p for p in (ROOT/'allowance_scheduler').iterdir() if p.suffix in ('.py', '.md'))
    sources += [ROOT/'recovery_objective/core.py', ROOT/'recovery_objective/run_analysis.py']
    meta = {'analytical_only': True, 'python': platform.python_version(), 'platform': platform.platform(),
            'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sources},
            'result_sha256': {p.name: sha(p) for p in args.output.iterdir() if p.is_file()},
            'scientific_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}
    (args.output/'metadata.json').write_text(json.dumps(meta, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'cases': len(payload['cases']), 'parameter_checks': len(payload['checks']['closed_form_cases']),
                      'matrix_checks': payload['checks']['matrix_games_checked'],
                      'causal_executions': payload['checks']['causal_policy_scenario_executions'],
                      'scientific_sha256': meta['scientific_sha256']}, indent=2))


if __name__ == '__main__': main()
