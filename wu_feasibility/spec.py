"""Hash-bind integration and already exposed preparation before evaluation."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = Path(__file__).resolve().parent
EXPORT = ROOT / 'wu_pipeline_v2/results/attempt_01'
REGISTRATION = PACKAGE / 'registration.json'
OWN = ('__init__.py', 'spec.py', 'core.py', 'run.py', 'test_core.py', 'PROTOCOL.md')
DEPS = ('confirmation_protocol/protocol.py', 'confirmation_protocol/design.json',
        'metric_contract/core.py', 'duration_contract/core.py',
        'admission_contract/core.py', 'geometric_admission/geometry.py',
        'feedback_opportunity/feedback.py', 'adaptive_audit/core.py')


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def text_hash(path):
    return hashlib.sha256(path.read_text(encoding='utf-8').replace('\r\n', '\n').encode()).hexdigest()


def registration():
    # Hash bytes only: no numerical feasibility outcome is computed here.
    files = sorted(p for p in EXPORT.rglob('*') if p.is_file())
    if len(files) != 23:
        raise ValueError('Expected complete 23-file preparation export')
    return {'schema': 'wu-fixed-contract-feasibility-v1',
        'quality_labels_already_exposed': True, 'feasibility_evaluated_before_freeze': False,
        'formal_preregistration_claimed': False, 'contract_changed': False,
        'preparation_commit': '30529f3dc1d80f69e062d020c6a440e929ed7354',
        'source_bindings': {p: text_hash(ROOT / p) for p in
                            ['wu_feasibility/' + n for n in OWN] + list(DEPS)},
        'input_bindings': {p.relative_to(ROOT).as_posix(): file_hash(p) for p in files},
        'preparation_registration_sha256': file_hash(ROOT / 'wu_pipeline_v2/registration.json'),
        'scalar_replay_bindings': {str(p.relative_to(ROOT).as_posix()): file_hash(p)
            for name in ('windows', 'linux') for p in
            sorted((ROOT / f'wu_pipeline_v2/results/replay_{name}_v1').glob('*.json'))}}


def verify():
    saved = json.loads(REGISTRATION.read_text())
    if saved != registration():
        raise ValueError('Frozen integration/input binding changed')
    return saved


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--freeze', action='store_true')
    args = parser.parse_args()
    if args.freeze:
        with REGISTRATION.open('xb') as stream:
            stream.write(canonical(registration()))
    print(json.dumps({'registration_sha256': digest(verify())}))


if __name__ == '__main__':
    main()
