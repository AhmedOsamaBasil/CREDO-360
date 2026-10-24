"""Verify source/result integrity and regenerate all exact analytical outcomes."""
import argparse
import hashlib
import json
import platform
from pathlib import Path
from recovery_objective.run_analysis import ROOT, sha, report, scientific_results


def verify(output):
    meta = json.loads((output/'metadata.json').read_text())
    assert meta['analytical_only'] is True
    for source, digest in meta['source_sha256'].items():
        assert sha(ROOT/source) == digest, source
    for name, digest in meta['result_sha256'].items():
        assert sha(output/name) == digest, name
    payload = scientific_results()
    assert payload == json.loads((output/'results.json').read_text())
    assert report(payload) == (output/'REPORT.md').read_text()
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert digest == meta['scientific_sha256']
    return {'passed': True, 'analytical_only': True, 'source_and_result_hashes': True,
            'exact_scientific_replay': True, 'constructed_cases': len(payload['cases']),
            'single_recipient_checks': payload['finite_checks']['single_recipient']['cases'],
            'multi_recipient_checks': payload['finite_checks']['multi_recipient']['cases'],
            'scientific_sha256': digest, 'python': platform.python_version(), 'platform': platform.platform()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, default=ROOT/'recovery_objective/results/analytic_v1')
    parser.add_argument('--save', type=str, help='new local JSON verification report name')
    args = parser.parse_args()
    if args.save and (Path(args.save).name != args.save or not args.save.endswith('.json')):
        parser.error('local JSON filename required')
    result = verify(args.output)
    if args.save:
        with (args.output/args.save).open('x', encoding='utf-8') as f:
            json.dump(result, f, indent=2); f.write('\n')
    print(json.dumps(result, indent=2))
