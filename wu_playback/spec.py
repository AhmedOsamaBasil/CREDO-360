"""Immutable integration registration; no browser or media measurement."""
import argparse
import json
from pathlib import Path
from wu_feasibility.spec import ROOT, canonical, digest, file_hash, text_hash, verify as verify_feasibility

PACKAGE = Path(__file__).resolve().parent
REGISTRATION = PACKAGE/'registration.json'
OWN = ('__init__.py', 'core.py', 'build.py', 'spec.py', 'audit.py', 'preflight.py',
       'measure.cjs', 'synthetic.cjs', 'synthetic_audit.py', 'test_core.py', 'test_audit.py', 'test_validation.py', 'test_runner.cjs', 'PROTOCOL.md')
DEPENDENCIES = ('confirmation_protocol/design.json', 'player_timing/player.js', 'player_timing/service.cjs',
    'player_timing/core.py', 'player_timing/audit.py', 'player_timing/diagnose.py',
    'player_timing/replay.py', 'metric_contract/core.py', 'duration_contract/core.py', 'admission_contract/core.py')


def registration():
    previous = verify_feasibility()
    inputs = {str(p.relative_to(ROOT).as_posix()): file_hash(p)
              for p in sorted((ROOT/'wu_feasibility/results/attempt_01').iterdir()) if p.is_file()}
    return {'schema': 'wu-playback-integration-v1',
        'feasibility_registration_sha256': digest(previous),
        'feasibility_results_commit': '21101266e8c166ad40939aefe4b69d473886c083',
        'sources': {p: text_hash(ROOT/p) for p in ['wu_playback/'+n for n in OWN]+list(DEPENDENCIES)},
        'input_bindings': inputs, 'runtime': json.loads((PACKAGE/'runtime.json').read_text()),
        'synthetic_evidence': {p: file_hash(ROOT/p) for p in (
            'wu_pipeline/results/synthetic_v1/report.json',
            'wu_playback/results/synthetic_01/metadata.json',
            'wu_playback/results/synthetic_02/metadata.json')},
        'expected': {'registered_clips': 16, 'eligible_clips': 10, 'selected_pairs': 10,
                     'cases': 120, 'main_sessions': 360, 'controls': 6, 'sessions': 366},
        'contract_changed': False, 'new_quality_fitting': False, 'real_wu_playback_before_freeze': False,
        'activation_automatic': False, 'primary_clock': 'first recovery request on browser clock',
        'primary_credit_arithmetic': 'integer native micro-MSE times media ticks',
        'proposed_paths_not_admission_gate_actions': True}


def verify():
    saved = json.loads(REGISTRATION.read_text())
    if saved != registration(): raise ValueError('Frozen playback integration changed')
    return saved


def main():
    p = argparse.ArgumentParser(__doc__); p.add_argument('--freeze', action='store_true'); a = p.parse_args()
    if a.freeze:
        with REGISTRATION.open('xb') as stream: stream.write(canonical(registration()))
    print(json.dumps({'registration_sha256': digest(verify())}))


if __name__ == '__main__': main()
