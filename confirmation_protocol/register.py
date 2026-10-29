"""Hash-bound design registration and evidence map; no fresh outcome access."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

from confirmation_protocol.protocol import (
    ROOT, PACKAGE, canonical, digest, exposure_inventory, load, preflight,
    require, validate_claims, validate_design,
)

OUT = PACKAGE / 'results/design_v1'
EVIDENCE = {
    'synthesis': 'feasibility_synthesis/results/synthesis_v1/summary.json',
    'timing_replay': 'player_timing/results/replay_v2/results.json.gz',
    'timing_audit': 'player_timing/results/audit_v2/results.json.gz',
    'timing_diagnostics': 'player_timing/results/diagnostics_v2/results.json.gz',
}
OWN = ('__init__.py', 'protocol.py', 'register.py', 'test_protocol.py',
       'design.json', 'claims.json', 'catalogue.json', 'README.md')


def text_hash(path):
    return hashlib.sha256(path.read_text(encoding='utf-8').replace('\r\n', '\n').encode()).hexdigest()


def read(path):
    raw = gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_bytes()
    return json.loads(raw)


def evidence():
    values = {}; hashes = {}
    for name, relative in EVIDENCE.items():
        path = ROOT / relative
        value = read(path)
        meta = read(path.with_name('metadata.json'))
        require(digest(value) == meta['scientific_sha256'], 'Existing evidence hash mismatch: ' + name)
        values[name] = value
        hashes[relative] = digest(value)
    synthesis, audit, diagnostics = (values[k] for k in ('synthesis', 'timing_audit', 'timing_diagnostics'))
    partition = [r for r in synthesis['summary'] if r['group'] == 'all']
    require(len(partition) == 2, 'Both frozen timing models required')
    require(audit['sessions'] == len(audit['rows']) == 74, 'Missing existing timing sessions')
    missed = [r for r in diagnostics['measured_versus_ideal'] if r['control'] == 'none'
              and r['parent_credit_minus_ideal'] < 0]
    return {'development_only': True, 'independent_confirmation': False,
        'sampling': synthesis['sampling'], 'feasibility_partition': partition,
        'browser_sessions': audit['sessions'], 'browser_valid': audit['valid'],
        'browser_summary': audit['summary'], 'timing_replay_cells': len(values['timing_replay']['rows']),
        'lower_measured_credit_sessions': [{'index': r['index'], 'scene': r['scene'],
            'policy': r['policy'], 'unit_seconds': r['unit_seconds'],
            'buffered': r['buffered']} for r in missed]}, hashes


def registration():
    design = validate_design(load('design.json'))
    claims = validate_claims(load('claims.json'))
    catalogue = load('catalogue.json')
    inventory = exposure_inventory(catalogue)
    current, hashes = evidence()
    bound = {}
    for claim in claims['claims']:
        for relative in claim['sources']:
            path = ROOT / relative
            require(path.is_file(), 'Missing claim source: ' + relative)
            bound[relative] = text_hash(path)
    for relative in ('player_timing/PRIOR_ART.md', 'player_timing/references.bib',
                     'feasibility_synthesis/claims.py', 'multimedia_testbed/prepare_qoevave.py',
                     'admission_contract/core.py', 'geometric_admission/geometry.py',
                     'adaptive_audit/core.py', 'adaptive_audit/run.py'):
        bound[relative] = text_hash(ROOT / relative)
    return {'schema': 'confirmation-design-registration-v1',
        'design_sha256': digest(design), 'claims_sha256': digest(claims),
        'catalogue_sha256': digest(catalogue), 'claim_ids': [r['id'] for r in claims['claims']],
        'readiness': preflight(None, design, catalogue), 'inventory': inventory,
        'exposed_evidence': current, 'evidence_scientific_sha256': hashes,
        'bound_source_sha256': bound,
        'design_source_sha256': {name: text_hash(PACKAGE / name) for name in OWN},
        'new_measurements': 0, 'fresh_outcomes_accessed': False,
        'formal_preregistration_claimed': False, 'manuscript_changed': False}


def main():
    parser = argparse.ArgumentParser(__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--freeze', action='store_true')
    group.add_argument('--verify', action='store_true')
    group.add_argument('--check-manifest', type=Path)
    args = parser.parse_args()
    if args.check_manifest:
        print(json.dumps(preflight(read(args.check_manifest)), indent=2))
        return
    result = registration()
    path = OUT / 'registration.json'
    if args.verify:
        require(read(path) == result, 'Registered design, source or evidence changed')
        require(read(OUT / 'metadata.json')['scientific_sha256'] == digest(result), 'Registration digest differs')
    else:
        OUT.mkdir(parents=True, exist_ok=False)
        path.write_bytes(canonical(result))
        (OUT / 'metadata.json').write_bytes(canonical({'scientific_sha256': digest(result)}))
    print(json.dumps({'verified': args.verify, 'sha256': digest(result),
        'claim_count': len(result['claim_ids']), 'readiness': result['readiness']['state'],
        'unused_qoevave_clips': result['inventory']['unused_clips'],
        'unused_qoevave_scene_families': result['inventory']['unused_scene_families'],
        'fresh_outcomes_accessed': False}))


if __name__ == '__main__':
    main()
