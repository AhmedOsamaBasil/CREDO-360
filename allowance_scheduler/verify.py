"""Rebuild exact outcomes and verify every published certificate and hash."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
from allowance_scheduler.run_analysis import ROOT, sha, analysis, report


def verify(output):
    meta = json.loads((output/'metadata.json').read_text())
    assert meta['analytical_only']
    for name, digest in meta['source_sha256'].items(): assert sha(ROOT/name) == digest, name
    for name, digest in meta['result_sha256'].items(): assert sha(output/name) == digest, name
    payload = analysis()
    assert payload == json.loads((output/'results.json').read_text())
    assert report(payload) == (output/'REPORT.md').read_text()
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert digest == meta['scientific_sha256']
    return {'passed': True, 'analytical_only': True, 'exact_source_result_report_checks': True,
            'cases': len(payload['cases']), 'parameter_checks': len(payload['checks']['closed_form_cases']),
            'matrix_game_certificates': payload['checks']['matrix_games_checked'],
            'causal_executions': payload['checks']['causal_policy_scenario_executions'],
            'scientific_sha256': digest, 'python': platform.python_version(), 'platform': platform.platform()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'allowance_scheduler/results/analytic_v1')
    parser.add_argument('--save', type=str)
    args = parser.parse_args()
    if args.save and (Path(args.save).name != args.save or not args.save.endswith('.json')):
        parser.error('new local JSON report name required')
    result = verify(args.output)
    if args.save:
        with (args.output/args.save).open('x', encoding='utf-8') as f: json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result, indent=2))
