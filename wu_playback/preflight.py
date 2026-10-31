"""Read-only media and method gate before any measured recovery session."""
import argparse
import gzip
import json
from pathlib import Path
from wu_feasibility.spec import EXPORT, digest, file_hash
from wu_pipeline_v2.audit import contained, verify_export
from .build import OUT
from .spec import verify


def validate(private, activation):
    frozen = verify()
    if activation != digest(frozen): raise ValueError('Exact published integration digest required')
    verify_export(EXPORT)
    meta = json.loads((OUT/'metadata.json').read_text())
    cases = json.loads(gzip.decompress((OUT/'cases.json.gz').read_bytes()))
    delivery = json.loads((OUT/'delivery.json').read_text())
    if meta['registration_sha256'] != activation or meta['cases_sha256'] != digest(cases) or meta['delivery_sha256'] != digest(delivery):
        raise ValueError('Frozen cases/delivery identity changed')
    if len(delivery) != 366 or [s['index'] for s in delivery] != list(range(366)):
        raise ValueError('Complete fixed schedule required')
    if file_hash(private/'manifest.json') != file_hash(EXPORT/'manifest.json'):
        raise ValueError('Wrong private Wu preparation')
    identities = {}
    for session in delivery:
        for unit in session['units']:
            for f in unit['files']:
                key = f['relative_path']; binding = (f['bytes'], f['sha256'])
                if key in identities and identities[key] != binding:
                    raise ValueError('Conflicting file identity')
                identities[key] = binding
    for key, (size, sha) in identities.items():
        path = contained(private, key)
        if path.stat().st_size != size or file_hash(path) != sha:
            raise ValueError('Selected media hash/size changed')
    return {'registration_sha256': activation, 'delivery_sha256': digest(delivery),
            'selected_files_hash_checked': len(identities), 'sessions': len(delivery), 'media_opened_for_hash_only': True}


if __name__ == '__main__':
    p = argparse.ArgumentParser(__doc__); p.add_argument('--private', type=Path, required=True)
    p.add_argument('--activate', required=True); a = p.parse_args()
    print(json.dumps(validate(a.private, a.activate)))
