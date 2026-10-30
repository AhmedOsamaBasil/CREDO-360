"""Explicit read-only audit or generated-only GPU regression; default verifies."""
import argparse
import json
from pathlib import Path
from wu_source.acquire import canonical, sha256
from wu_pipeline.media import (call, probe, fingerprint, frame_hashes, describe,
                               split_verified, encode_command)
from wu_pipeline.spec import RUNTIME, digest, verify
from .core import PACKAGE, endpoint, bounded_command, bindings, private_new_output

CASES = (('ntsc_b0', '30000/1001', 0), ('ntsc_b3', '30000/1001', 3),
         ('cfr30_b3', '30', 3), ('ffv1_25', '25', None))


def check_runtime():
    if fingerprint() != json.loads(RUNTIME.read_text()):
        raise ValueError('Frozen runtime changed')


def decoded_count(path):
    result = json.loads(call(['ffprobe', '-v', 'error', '-select_streams', 'v:0',
        '-count_frames', '-show_entries', 'stream=nb_read_frames,has_b_frames', '-of', 'json', path]))
    s = result['streams'][0]
    return {'decoded_frames': int(s['nb_read_frames']), 'has_b_frames': int(s['has_b_frames'])}


def audit(directory):
    check_runtime()
    expected = ['e1v01/r0.mp4', 'failure.json', 'progress.jsonl']
    files = sorted(p.relative_to(directory).as_posix() for p in directory.rglob('*') if p.is_file())
    if files != expected or (directory / 'progress.jsonl').stat().st_size != 0:
        raise ValueError('Unexpected failed-attempt contents')
    failure = json.loads((directory / 'failure.json').read_text())
    if failure != {'automatic_retry': False, 'registration_sha256': digest(verify()),
                   'status': 'failed_incomplete', 'type': 'ValueError'}:
        raise ValueError('Unexpected failure record')
    target = directory / expected[0]
    info = probe(target)
    return {'schema': 'wu-boundary-failure-v1', 'failure': failure,
        'files': [{'path': p, 'bytes': (directory / p).stat().st_size,
                   'sha256': sha256(directory / p)} for p in files],
        'probe': info, 'endpoint': endpoint(info), 'independent_decode': decoded_count(target),
        'completed_rungs': 0, 'completed_clips': 0, 'saved_quality_labels': 0,
        'phase_and_reference_sampled_in_memory': True, 'phase_result_saved': False,
        'real_source_retry': False, 'original_inputs_rehashed_in_this_audit': False,
        'recovery_experiment_performed': False, 'runtime': fingerprint()}


def synthetic(directory):
    directory = private_new_output(directory)
    check_runtime()
    directory.mkdir(parents=True)
    cases = []
    for name, rate, bf in CASES:
        folder = directory / name
        folder.mkdir()
        source = folder / ('source.mkv' if bf is None else 'source.mp4')
        command = ['ffmpeg', '-nostdin', '-v', 'error', '-n', '-f', 'lavfi', '-i',
                   f'testsrc2=size=320x160:rate={rate}:duration=61', '-an']
        command += ['-c:v', 'ffv1'] if bf is None else [
            '-c:v', 'libx264', '-preset', 'fast', '-crf', '18', '-g', '60', '-bf', str(bf), '-pix_fmt', 'yuv420p']
        call(command + [source])
        row = {'case': name, 'rate': rate, 'requested_max_b_frames': bf,
               'source_sha256': sha256(source), 'source_decode': decoded_count(source)}
        hashes = {}
        for label, factory in (('original', encode_command), ('bounded', bounded_command)):
            target = folder / (label + '.mp4')
            call(factory(source, target, 0, 60))
            info = probe(target)
            hashes[label] = frame_hashes(target)
            item = {'sha256': sha256(target), 'bytes': target.stat().st_size,
                    'endpoint': endpoint(info), 'decoded_frames': len(hashes[label])}
            if label == 'bounded':
                record, _, _ = describe(target, 60, directory)
                item['description'] = record
                if name == 'ntsc_b3':
                    parents = split_verified(target, folder / 'parents', 10, 60, directory)
                    children = split_verified(directory / parents[-1]['relative_path'],
                                              folder / 'tail_children', 2, 10, directory)
                    item['parents'] = parents
                    item['tail_children'] = children
            row[label] = item
        count = min(len(hashes['original']), len(hashes['bounded']))
        row['common_prefix_frames_compared'] = count
        row['different_decoded_prefix_frames'] = sum(
            a != b for a, b in zip(hashes['original'], hashes['bounded']))
        cases.append(row)
        (folder / 'case.json').write_bytes(canonical(row))
        print(json.dumps({'case': name, 'original': row['original']['endpoint'],
                          'bounded': row['bounded']['endpoint']}), flush=True)
    return {'schema': 'wu-boundary-synthetic-v1', 'cases': cases, 'runtime': fingerprint(),
            'synthetic_only': True, 'wu_media_reencoded': False, 'quality_labels_created': False,
            'real_runner_modified': False, 'all_six_rungs_exercised': False}


def validate(report):
    if report['runtime'] != json.loads(RUNTIME.read_text()):
        raise ValueError('Saved runtime changed')
    if report['schema'] == 'wu-boundary-failure-v1':
        if report['endpoint'] != endpoint(report['probe']):
            raise ValueError('Endpoint ledger mismatch')
        e = report['endpoint']
        if e['frozen_validation_pass'] or e['packets'] != report['independent_decode']['decoded_frames']:
            raise ValueError('Not independently counted failed file')
        if (report['completed_rungs'], report['completed_clips'], report['saved_quality_labels']) != (0, 0, 0):
            raise ValueError('Unexpected completed result')
        for key in ('real_source_retry', 'recovery_experiment_performed', 'phase_result_saved',
                    'original_inputs_rehashed_in_this_audit'):
            if report[key] is not False:
                raise ValueError('Audit scope changed')
        if report['phase_and_reference_sampled_in_memory'] is not True:
            raise ValueError('Exposure statement changed')
        if report['failure'] != {'automatic_retry': False, 'registration_sha256': digest(verify()),
                                'status': 'failed_incomplete', 'type': 'ValueError'}:
            raise ValueError('Failure binding changed')
    elif report['schema'] == 'wu-boundary-synthetic-v1':
        if [r['case'] for r in report['cases']] != [c[0] for c in CASES]:
            raise ValueError('Matrix census changed')
        if report['synthetic_only'] is not True or any(report[k] is not False for k in
                ('wu_media_reencoded', 'quality_labels_created', 'real_runner_modified', 'all_six_rungs_exercised')):
            raise ValueError('Synthetic scope changed')
        for row in report['cases']:
            if not row['bounded']['endpoint']['frozen_validation_pass'] or row['bounded']['decoded_frames'] != 1800:
                raise ValueError('Bounded output fails original contract')
        tail = report['cases'][1]['bounded']
        if len(tail['parents']) != 6 or len(tail['tail_children']) != 5:
            raise ValueError('Tail closure census changed')
    else:
        raise ValueError('Unknown report')
    return {'schema': report['schema'], 'report_sha256': digest(report)}


def save(report, name):
    validate(report)
    output = PACKAGE / 'results' / name
    output.mkdir(parents=True, exist_ok=False)
    (output / 'report.json').write_bytes(canonical(report))
    (output / 'metadata.json').write_bytes(canonical({'report_sha256': digest(report), 'bindings': bindings()}))


def verify_saved(name):
    output = PACKAGE / 'results' / name
    report = json.loads((output / 'report.json').read_text())
    metadata = json.loads((output / 'metadata.json').read_text())
    if metadata != {'report_sha256': digest(report), 'bindings': bindings()}:
        raise ValueError('Report/source binding differs')
    return validate(report)


def main():
    parser = argparse.ArgumentParser(__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--audit-attempt', type=Path)
    group.add_argument('--synthetic-output', type=Path)
    args = parser.parse_args()
    if args.audit_attempt or args.synthetic_output:
        name = 'attempt_01' if args.audit_attempt else 'synthetic_v1'
        if (PACKAGE / 'results' / name).exists():
            raise ValueError('Preserve prior report')
        report = audit(args.audit_attempt) if args.audit_attempt else synthetic(args.synthetic_output)
        save(report, name)
        print(json.dumps(validate(report)))
    else:
        print(json.dumps([verify_saved(name) for name in ('attempt_01', 'synthetic_v1')]))


if __name__ == '__main__':
    main()
