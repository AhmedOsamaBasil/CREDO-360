"""Bind the exact v2 amendment to the immutable v1 plan and endpoint evidence."""
import argparse
import hashlib
import json
from pathlib import Path
from wu_source.acquire import canonical
from wu_pipeline.spec import verify as verify_original, digest, ROOT
from wu_boundary.run import verify_saved

PACKAGE = Path(__file__).resolve().parent
REGISTRATION = PACKAGE / 'registration.json'


def registration():
    original = verify_original()
    evidence = [verify_saved(name) for name in ('attempt_01', 'synthetic_v1')]
    paths = ['wu_pipeline_v2/' + n for n in
             ('__init__.py', 'spec.py', 'prepare.py', 'audit.py', 'test_v2.py', 'PROTOCOL.md')]
    paths += ['wu_boundary/results/' + name + '/metadata.json'
              for name in ('attempt_01', 'synthetic_v1')]
    return {'schema': 'wu-encoding-measurement-registration-v2',
        'original_registration_sha256': digest(original), 'plan': original['plan'],
        'boundary_evidence': evidence,
        'amendment': {'output_frame_limit': 1800, 'resumable': False,
                      'durable_stage_evidence': True, 'original_numeric_functions': True},
        'bindings': {p: hashlib.sha256((ROOT / p).read_text(encoding='utf-8')
                    .replace('\r\n', '\n').encode()).hexdigest() for p in paths},
        'runtime_sha256': original['runtime_sha256'], 'real_v2_outputs_present_at_freeze': False}


def verify():
    saved = json.loads(REGISTRATION.read_text())
    if saved != registration():
        raise ValueError('Frozen v2 preparation changed')
    return saved


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--freeze', action='store_true')
    a = p.parse_args()
    if a.freeze:
        with REGISTRATION.open('xb') as f:
            f.write(canonical(registration()))
    value = verify()
    print(json.dumps({'registration_sha256': digest(value), 'expected': value['plan']['expected']}))


if __name__ == '__main__':
    main()
