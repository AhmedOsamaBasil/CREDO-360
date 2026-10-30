"""Post-preparation independent scalar replay; never changes frozen outcomes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import platform
import zipfile
import numpy as np
from wu_source.acquire import canonical, sha256
from wu_pose.core import load_roster, load_selected, quaternion_checks
from wu_calibration.check_adapter import scalar_yaw_pitch, scalar_weights
from wu_pipeline.spec import digest
from .spec import verify
from .audit import verify_export, contained


def scalar_labels(maps, fields, unit):
    if maps.shape != (6, 60, 6, 12) or maps.dtype != np.dtype('<f4') or unit not in (2, 10):
        raise ValueError('Scalar replay dimensions changed')
    if not np.isfinite(maps).all() or np.any(maps < 0) or np.any(maps > 65025):
        raise ValueError('Scalar replay maps invalid')
    checks, quaternions = quaternion_checks(fields)
    if checks['invalid_samples'] or len(quaternions) != 60:
        raise ValueError('Scalar replay quaternions invalid')
    weights = [scalar_weights(*scalar_yaw_pitch(q)) for q in quaternions]
    samples = [[math.fsum(float(maps[rung, t, r, c]) * weights[t][r][c]
                         for r in range(6) for c in range(12)) for t in range(60)] for rung in range(6)]
    means = [[math.fsum(samples[rung][start:start + unit]) / unit
              for start in range(0, 60, unit)] for rung in range(6)]
    micro = [[round(-v * 1e6) for v in row] for row in means]
    return means, micro


def compare(saved, means, micro):
    values = np.asarray(means, dtype=np.float64)
    primary = np.asarray(saved['native_mse'], dtype=np.float64)
    integers = np.asarray(micro, dtype=np.int64)
    primary_integers = np.asarray(saved['negative_micro_mse'], dtype=np.int64)
    if values.shape != primary.shape or integers.shape != primary_integers.shape or not np.isfinite(primary).all():
        raise ValueError('Replay comparison shape or values changed')
    maximum = float(np.max(np.abs(values - primary)))
    mismatches = int(np.count_nonzero(integers != primary_integers))
    return {'cells': int(values.size), 'maximum_native_mse_difference': maximum,
            'micro_mse_mismatches': mismatches, 'pass': maximum <= 1e-9 and mismatches == 0}


def bindings(export):
    package = Path(__file__).resolve().parent
    return {'registration_sha256': digest(verify()), 'export_metadata_sha256': sha256(export / 'metadata.json'),
        'sources': {name: hashlib.sha256((package / name).read_text(encoding='utf-8')
                    .replace('\r\n', '\n').encode()).hexdigest() for name in ('replay.py', 'test_replay.py')}}


def validate_report(report):
    if report['schema'] != 'wu-independent-scalar-label-replay-v1' or len(report['rows']) != 452 or report['traces'] != 452:
        raise ValueError('Replay report census changed')
    expected = {(c['clip'], identity) for c in verify()['plan']['clips'] if c['eligible'] for identity in c['source_ids']}
    if {(r['clip'], r['source_id']) for r in report['rows']} != expected:
        raise ValueError('Replay report roster changed')
    for row in report['rows']:
        for key, cells in (('parent', 36), ('child', 180)):
            result = row[key]
            error, mismatches = result['maximum_native_mse_difference'], result['micro_mse_mismatches']
            if result['cells'] != cells or not math.isfinite(error) or error < 0 or type(mismatches) is not int or not 0 <= mismatches <= cells:
                raise ValueError('Invalid replay comparison')
            if result['pass'] != (error <= 1e-9 and mismatches == 0):
                raise ValueError('Replay pass flag inconsistent')
    comparisons = [r[key] for r in report['rows'] for key in ('parent', 'child')]
    if report['passed'] != all(r['pass'] for r in comparisons) or report['micro_mse_mismatches'] != sum(r['micro_mse_mismatches'] for r in comparisons):
        raise ValueError('Replay aggregate inconsistent')
    if report['maximum_native_mse_difference'] != max(r['maximum_native_mse_difference'] for r in comparisons):
        raise ValueError('Replay maximum inconsistent')
    if report['new_encoding_or_recovery_run'] is not False or report['original_outputs_modified'] is not False:
        raise ValueError('Replay scope changed')


def derive(export, archive_path):
    verify_export(export)
    frozen = verify()
    if not (export / 'manifest.json').exists():
        raise ValueError('Only complete preparation can be replayed as a full artifact')
    manifest = json.loads((export / 'manifest.json').read_text())
    original = next(r for r in frozen['plan']['private_files_checked'] if r['id'] == 'traces')
    if archive_path.stat().st_size != original['bytes'] or sha256(archive_path) != original['sha256']:
        raise ValueError('Original trace archive changed')
    roster = load_roster()
    records = {(r['clip'], r['source_id']): r for r in roster['rows']}
    rows = []
    with zipfile.ZipFile(archive_path) as archive:
        for clip in manifest['clips']:
            if not clip['eligible']:
                continue
            with np.load(contained(export, clip['clip'] + '/sender_maps.npz'), allow_pickle=False) as bundle:
                maps = bundle['mse']
            labels = json.loads(contained(export, clip['clip'] + '/offline_evaluation_labels.json').read_text())
            for item in labels['rows']:
                fields = load_selected(archive, records, clip['clip'], item['source_id'])
                result = {'clip': clip['clip'], 'source_id': item['source_id']}
                for key, unit in (('parent', 10), ('child', 2)):
                    result[key] = compare(item[key], *scalar_labels(maps, fields, unit))
                rows.append(result)
            print(json.dumps({'clip': clip['clip'], 'traces_replayed': len(labels['rows'])}), flush=True)
    if len(rows) != 452:
        raise ValueError('Replay census differs')
    return {'schema': 'wu-independent-scalar-label-replay-v1', 'bindings': bindings(export),
        'platform': platform.system(), 'python': platform.python_version(), 'numpy': np.__version__,
        'rows': rows, 'traces': len(rows),
        'passed': all(r[key]['pass'] for r in rows for key in ('parent', 'child')),
        'maximum_native_mse_difference': max(r[key]['maximum_native_mse_difference'] for r in rows for key in ('parent', 'child')),
        'micro_mse_mismatches': sum(r[key]['micro_mse_mismatches'] for r in rows for key in ('parent', 'child')),
        'new_encoding_or_recovery_run': False, 'original_outputs_modified': False}


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--export', type=Path, required=True)
    p.add_argument('--archive', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.archive:
        if a.output.exists():
            raise ValueError('Preserve prior scalar replay')
        report = derive(a.export, a.archive)
        a.output.mkdir(parents=True)
        (a.output / 'report.json').write_bytes(canonical(report))
        (a.output / 'metadata.json').write_bytes(canonical({'report_sha256': digest(report)}))
    report = json.loads((a.output / 'report.json').read_text())
    if report['bindings'] != bindings(a.export) or json.loads((a.output / 'metadata.json').read_text()) != {'report_sha256': digest(report)}:
        raise ValueError('Replay provenance differs')
    validate_report(report)
    print(json.dumps({'report_sha256': digest(report), 'passed': report['passed'],
        'traces': report['traces'], 'micro_mse_mismatches': report['micro_mse_mismatches'],
        'maximum_native_mse_difference': report['maximum_native_mse_difference']}))


if __name__ == '__main__':
    main()
