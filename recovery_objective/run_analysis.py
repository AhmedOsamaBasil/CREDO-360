"""Save deterministic rational results for analytical witnesses and finite checks."""
import argparse
from dataclasses import asdict
from fractions import Fraction
import hashlib
import json
import platform
from pathlib import Path
from recovery_objective.cases import all_cases
from recovery_objective.checks import run_checks
from recovery_objective.core import ONLINE_POLICIES, online, oracle

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def encode(value):
    if isinstance(value, Fraction): return str(value)
    if isinstance(value, dict): return {k: encode(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)): return [encode(x) for x in value]
    return value


def scientific_results():
    cases = []
    for case in all_cases():
        results = {p: online(p, case.schedule, case.contract, case.history) for p in ONLINE_POLICIES}
        results['offline_oracle'] = oracle(case.schedule, case.contract)
        cases.append({'definition': asdict(case), 'results': results})
    return encode({'analytical_only': True, 'fresh_data_used': False, 'current_quality_known_exactly': True,
                   'offline_oracle_knows_future': True, 'arithmetic': 'exact rational',
                   'cases': cases, 'finite_checks': run_checks()})


def report(payload):
    lines = ['# Exact analytical results', '',
             '**Constructed witnesses and finite model checks, not experimental validation.** '
             'No content, HMD trace, new holdout or GPU experiment is used. The offline oracle '
             'knows the future; online rules do not. All values are exact rational numbers.', '',
             'The objective is the largest fraction of original event loss still unpaid at '
             'the declared deadline (smaller is better), with total unpaid fractions as '
             'a secondary criterion. Donor harm is reported, not hidden as free recovery. '
             'See `THEORY.md` for proofs, assumptions and prior art.', '']
    for case in payload['cases']:
        d = case['definition']
        lines += ['## '+d['name'], '', d['purpose'], '',
                  'Initial debt: '+str(d['contract']['debt'])+'. Total donor allowances: '+str(d['contract']['donor_total_allowance'])+'.', '',
                  '| Rule | Action sequence | Max unpaid fraction | Sum unpaid fractions | Donor loss vector | Worst post-quality | Full payment |',
                  '|---|---|---:|---:|---|---:|---|']
        for p, r in case['results'].items():
            names = ', '.join(step['action'] for step in r['trace'])
            lines.append(f"| {p} | {names} | {r['terminal_max_fraction']} | {r['terminal_sum_fraction']} | {r['donor_spent']} | {r['worst_post_quality']} | {r['all_recovered']} |")
        lines.append('')
    checks = payload['finite_checks']
    lines += ['## Finite exact checks', '',
              f"- Single-recipient family: {checks['single_recipient']['cases']} cases match the closed-form repayment bound and exhaustive oracle exactly.",
              f"- Multiple-recipient opportunity family: {checks['multi_recipient']['cases']} cases check conservation, protection and comparisons with the offline optimum.",
              '- These are enumerated mathematical instances, not independent observations or a representative workload distribution.', '',
              '| Rule | Equal terminal oracle | Strictly worse terminal oracle |', '|---|---:|---:|']
    for policy, record in checks['multi_recipient']['policy_relationships'].items():
        lines.append(f"| {policy} | {record['equal_terminal_oracle']} | {record['strictly_above_terminal_oracle']} |")
    lines += ['', '## Conclusion', '',
              'The event-local objective is distinguishable from rolling average fairness. '
              'It is not uniformly better: explicit donor sacrifice is required without spare '
              'capacity, all methods can be unable to pay, simple controls sometimes tie, and '
              'greedy recovery can lose even on its own endpoint. The conditional single-user '
              'proof does not establish general online optimality or new algorithmic novelty. '
              'No empirical campaign or manuscript update follows automatically.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'recovery_objective/results/analytic_v1')
    args = parser.parse_args()
    if args.output.exists(): parser.error('output exists; preserve the saved analysis')
    payload = scientific_results()
    args.output.mkdir(parents=True)
    (args.output/'results.json').write_text(json.dumps(payload, indent=2)+'\n', encoding='utf-8')
    (args.output/'REPORT.md').write_text(report(payload), encoding='utf-8')
    sources = sorted(p for p in (ROOT/'recovery_objective').iterdir() if p.suffix in ('.py', '.md'))
    meta = {'analytical_only': True, 'python': platform.python_version(), 'platform': platform.platform(),
            'source_sha256': {p.relative_to(ROOT).as_posix(): sha(p) for p in sources},
            'result_sha256': {p.name: sha(p) for p in args.output.iterdir() if p.is_file()},
            'scientific_sha256': hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()}
    (args.output/'metadata.json').write_text(json.dumps(meta, indent=2)+'\n', encoding='utf-8')
    print(json.dumps({'constructed_cases': len(payload['cases']), 'finite_checks': payload['finite_checks'],
                      'scientific_sha256': meta['scientific_sha256']}, indent=2))


if __name__ == '__main__': main()
