"""Validate private preparation and publish only derived, path-safe evidence."""
import argparse
import json
from pathlib import Path, PurePosixPath
import numpy as np
from wu_source.acquire import canonical, sha256
from wu_pipeline.spec import RUNTIME, digest
from .spec import PACKAGE, verify
from .prepare import census


def contained(root, relative):
    path = PurePosixPath(relative)
    if path.is_absolute() or '..' in path.parts or '\\' in relative or ':' in relative:
        raise ValueError('Unsafe artifact path')
    target = (root / relative).resolve()
    if not target.is_relative_to(root.resolve()):
        raise ValueError('Artifact outside attempt')
    return target


def media_record(root, record, seconds):
    path = contained(root, record['relative_path'])
    if path.stat().st_size != record['bytes'] or sha256(path) != record['sha256']:
        raise ValueError('Media file binding differs')
    if record['frames'] != seconds * 30 or record['duration_ticks'] != seconds * 150000:
        raise ValueError('Media record timing differs')
    if not 0 < record['payload_bytes'] <= record['bytes']:
        raise ValueError('Media byte account differs')
    return record['relative_path']


def validate_labels(value, identities):
    if value['information_scope'] != 'offline_evaluation_only':
        raise ValueError('Label scope changed')
    if [r['source_id'] for r in value['rows']] != identities:
        raise ValueError('Label roster changed')
    for row in value['rows']:
        for key, unit in (('parent', 10), ('child', 2)):
            record = row[key]
            a = np.asarray(record['native_mse'], dtype=np.float64)
            micro = np.asarray(record['negative_micro_mse'])
            if a.shape != (6, 60 // unit) or micro.shape != a.shape or not np.isfinite(a).all():
                raise ValueError('Label dimensions or finite values differ')
            if np.any(a < 0) or np.any(a > 65025) or micro.dtype.kind not in 'iu':
                raise ValueError('Native quality range/type differs')
            if not np.array_equal(np.rint(-a * 1e6).astype(np.int64), micro):
                raise ValueError('Direct micro-MSE conversion differs')
            if record['duration_ticks'] != [unit * 150000] * (60 // unit):
                raise ValueError('Label durations changed')
            if record['independent_scalar_micro_exact'] is not True or record['information_scope'] != 'offline_evaluation_only':
                raise ValueError('Label validation/scope changed')


def validate_manifest(manifest, frozen):
    if manifest['schema'] != 'wu-private-preparation-v2' or manifest['registration_sha256'] != digest(frozen):
        raise ValueError('Wrong preparation method')
    if manifest['runtime'] != json.loads(RUNTIME.read_text()):
        raise ValueError('Runtime changed')
    if manifest['quality_outputs_created'] is not True or any(manifest[k] is not False for k in
            ('recovery_experiment_performed', 'controller_access_to_future_labels_allowed')):
        raise ValueError('Preparation claim scope changed')
    if len(manifest['clips']) != len(frozen['plan']['clips']):
        raise ValueError('Clip census changed')
    for actual, planned in zip(manifest['clips'], frozen['plan']['clips']):
        if any(actual[k] != v for k, v in planned.items()):
            raise ValueError('Original clip plan changed')
        expected = 'prepared_offline' if planned['eligible'] else 'retained_metadata_exclusion'
        if actual['status'] != expected:
            raise ValueError('Disposition changed')
        if not planned['eligible'] and set(actual) != set(planned) | {'status'}:
            raise ValueError('Unexpected excluded-clip outputs')
    if census(manifest['clips']) != frozen['plan']['expected'] or manifest['counts'] != frozen['plan']['expected']:
        raise ValueError('Manifest census changed')


def inspect_success(root, frozen):
    manifest = json.loads((root / 'manifest.json').read_text())
    validate_manifest(manifest, frozen)
    files, clips = [], []
    for c in manifest['clips']:
        if not c['eligible']:
            continue
        clip = c['clip']
        if [m['rung'] for m in c['media']] != list(range(6)):
            raise ValueError('Rung roster changed')
        for m in c['media']:
            files.append(media_record(root, m['rendition'], 60))
            if [p['index'] for p in m['parents']] != list(range(6)):
                raise ValueError('Parent roster changed')
            for p in m['parents']:
                files.append(media_record(root, p, 10))
                indices = list(range(5)) if m['rung'] >= 2 and p['index'] >= 2 else []
                if [ch['index'] for ch in p['children']] != indices:
                    raise ValueError('Child roster changed')
                for ch in p['children']:
                    files.append(media_record(root, ch, 2))
        map_path = contained(root, clip + '/sender_maps.npz')
        label_path = contained(root, clip + '/offline_evaluation_labels.json')
        if sha256(map_path) != c['sender_maps_sha256'] or sha256(label_path) != c['offline_labels_sha256']:
            raise ValueError('Feature/label binding differs')
        with np.load(map_path, allow_pickle=False) as bundle:
            if bundle.files != ['mse']:
                raise ValueError('Unexpected map member')
            maps = bundle['mse']
        if maps.shape != (6, 60, 6, 12) or maps.dtype != np.dtype('<f4') or not np.isfinite(maps).all() or np.any(maps < 0) or np.any(maps > 65025):
            raise ValueError('Map dimensions/range/type changed')
        labels = json.loads(label_path.read_text())
        validate_labels(labels, c['source_ids'])
        if c['trace_label_rows'] != len(labels['rows']):
            raise ValueError('Label count differs')
        phase = json.loads(contained(root, clip + '/phase.json').read_text())
        if phase != c['phase_diagnostic'] or phase['samples'] != 60 or phase['changes_primary_sampler'] is not False:
            raise ValueError('Phase evidence differs')
        clips.append({'clip': clip, 'condition': c['condition'], 'pairs': len(c['pairs']),
                      'phase_different_sample_bins': phase['different_sample_bins']})
    if len(files) != 1220 or len(set(files)) != len(files):
        raise ValueError('Unique served file census differs')
    return {'schema': 'wu-preparation-audit-v2', 'status': 'complete_offline_preparation',
        'registration_sha256': digest(frozen), 'manifest_sha256': digest(manifest),
        'counts': manifest['counts'], 'served_files_hash_checked': len(files),
        'clips': clips, 'independent_pose_reaggregation_performed': False,
        'new_media_decodes_performed_by_audit': False, 'recovery_experiment_performed': False}, manifest


def inspect_failure(root, frozen):
    if (root / 'manifest.json').exists():
        raise ValueError('Conflicting success and failure')
    failure = json.loads((root / 'failure.json').read_text())
    if failure['registration_sha256'] != digest(frozen) or failure['status'] != 'failed_incomplete' or failure['automatic_retry'] is not False:
        raise ValueError('Unexpected failure record')
    progress = [json.loads(line) for line in (root / 'progress.jsonl').read_text().splitlines()]
    if [p['sequence'] for p in progress] != list(range(len(progress))) or not progress or progress[-1] != failure['last_stage']:
        raise ValueError('Failure stage sequence differs')
    if any(set(p) - {'sequence', 'stage', 'clip', 'rung', 'parent', 'source_id'} for p in progress):
        raise ValueError('Unexpected progress fields')
    paths = sorted(p.relative_to(root).as_posix() for p in root.rglob('*') if p.is_file())
    return {'schema': 'wu-preparation-failure-audit-v2', 'registration_sha256': digest(frozen),
        'failure': failure, 'progress': progress,
        'files': [{'path': p, 'bytes': contained(root, p).stat().st_size,
                   'sha256': sha256(contained(root, p))} for p in paths],
        'completed_confirmation': False, 'recovery_experiment_performed': False}


def export(root, output):
    frozen = verify()
    if output.exists():
        raise ValueError('Preserve earlier audit')
    if (root / 'failure.json').exists():
        report = inspect_failure(root, frozen)
        manifest = None
    else:
        report, manifest = inspect_success(root, frozen)
    output.mkdir(parents=True)
    (output / 'report.json').write_bytes(canonical(report))
    if manifest is not None:
        (output / 'manifest.json').write_bytes(canonical(manifest))
        for clip in manifest['clips']:
            if clip['eligible']:
                directory = output / clip['clip']
                directory.mkdir()
                for name in ('sender_maps.npz', 'offline_evaluation_labels.json'):
                    (directory / name).write_bytes(contained(root, clip['clip'] + '/' + name).read_bytes())
    copied = sorted(p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file())
    (output / 'metadata.json').write_bytes(canonical({'registration_sha256': digest(frozen),
        'files': {p: sha256(output / p) for p in copied}}))
    return report


def verify_export(output):
    frozen = verify()
    metadata = json.loads((output / 'metadata.json').read_text())
    if metadata['registration_sha256'] != digest(frozen):
        raise ValueError('Wrong export registration')
    files = sorted(p.relative_to(output).as_posix() for p in output.rglob('*') if p.is_file() and p.name != 'metadata.json')
    if set(files) != set(metadata['files']):
        raise ValueError('Export file census changed')
    for p in files:
        if sha256(contained(output, p)) != metadata['files'][p]:
            raise ValueError('Export hash differs')
    report = json.loads((output / 'report.json').read_text())
    if report['registration_sha256'] != digest(frozen) or report['recovery_experiment_performed'] is not False:
        raise ValueError('Export scope changed')
    if report['schema'] == 'wu-preparation-audit-v2':
        manifest = json.loads((output / 'manifest.json').read_text())
        validate_manifest(manifest, frozen)
        if report['manifest_sha256'] != digest(manifest):
            raise ValueError('Manifest binding differs')
        for clip in manifest['clips']:
            if clip['eligible']:
                path = contained(output, clip['clip'] + '/offline_evaluation_labels.json')
                validate_labels(json.loads(path.read_text()), clip['source_ids'])
    elif report['schema'] != 'wu-preparation-failure-audit-v2' or report['completed_confirmation'] is not False:
        raise ValueError('Unknown export disposition')
    return {'report_sha256': digest(report), 'schema': report['schema']}


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--attempt', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    if a.attempt:
        export(a.attempt, a.output)
    print(json.dumps(verify_export(a.output)))


if __name__ == '__main__':
    main()
