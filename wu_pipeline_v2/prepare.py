"""Explicit v2 preparation with preserved early-stage failure evidence."""
import argparse
import json
from pathlib import Path
import zipfile
import numpy as np
from wu_source.acquire import canonical, sha256
from wu_pose.core import load_roster, load_selected, project_selected
from wu_qualification.core import validate_archive_directory
from wu_pipeline.spec import RUNTIME, digest, verify as verify_original
from wu_pipeline.prepare import authorize as authorize_original
from wu_pipeline.media import call, describe, split_verified, phase_check, sample_frames
from wu_pipeline.metrics import mse_map, aggregate_native
from wu_boundary.core import bounded_command, private_new_output
from .spec import verify


def save(path, value):
    with path.open('xb') as f:
        f.write(canonical(value))


class Journal:
    def __init__(self, handle):
        self.handle = handle
        self.last = None
        self.sequence = 0

    def emit(self, stage, **fields):
        if set(fields) - {'clip', 'rung', 'parent', 'source_id'}:
            raise ValueError('Unexpected journal field')
        value = {'sequence': self.sequence, 'stage': stage, **fields}
        self.handle.write(canonical(value) + b'\n')
        self.handle.flush()
        self.last = value
        self.sequence += 1
        print(json.dumps(value), flush=True)


def authorize(private, output, activation):
    frozen = verify()
    if activation != digest(frozen):
        raise ValueError('Exact v2 activation digest required')
    private_new_output(output)
    original = authorize_original(private, output, digest(verify_original()))
    if frozen['plan'] != original['plan']:
        raise ValueError('Original scientific plan changed')
    return frozen


def census(clips):
    return {'registered_clips': len(clips),
        'eligible_clips': sum(c['status'] == 'prepared_offline' for c in clips),
        'directed_pairs': sum(len(c['pairs']) for c in clips),
        'renditions': sum(len(c.get('media', [])) for c in clips),
        'parents': sum(len(m['parents']) for c in clips for m in c.get('media', [])),
        'recovery_children': sum(len(p['children']) for c in clips for m in c.get('media', []) for p in m['parents']),
        'trace_label_rows': sum(c.get('trace_label_rows', 0) for c in clips)}


def derive(private, output, frozen, journal):
    parent = load_roster()
    records = {(r['clip'], r['source_id']): r for r in parent['rows']}
    clips = []
    with zipfile.ZipFile(private / 'vr-dataset.zip') as archive:
        validate_archive_directory(archive)
        for selected in frozen['plan']['clips']:
            clip = selected['clip']
            if not selected['eligible']:
                clips.append({**selected, 'status': 'retained_metadata_exclusion'})
                journal.emit('metadata_exclusion_retained', clip=clip)
                continue
            directory = output / clip
            directory.mkdir()
            source = private / (clip + '.mp4')
            journal.emit('phase_start', clip=clip)
            phase = phase_check(source)
            save(directory / 'phase.json', phase)
            journal.emit('phase_saved', clip=clip)
            journal.emit('reference_sampling_start', clip=clip)
            reference = sample_frames(source)
            journal.emit('reference_sampling_complete', clip=clip)
            maps, media = [], []
            for rung in range(6):
                rendition = directory / f'r{rung}.mp4'
                journal.emit('encoding_start', clip=clip, rung=rung)
                call(bounded_command(source, rendition, rung))
                journal.emit('rendition_validation_start', clip=clip, rung=rung)
                full, _, _ = describe(rendition, 60, output)
                save(directory / f'r{rung}_rendition.json', full)
                journal.emit('parent_splitting_start', clip=clip, rung=rung)
                parents = split_verified(rendition, directory / f'r{rung}_parents', 10, 60, output)
                for item in parents:
                    item['children'] = []
                    if rung >= 2 and item['index'] >= 2:
                        journal.emit('child_splitting_start', clip=clip, rung=rung, parent=item['index'])
                        item['children'] = split_verified(output / item['relative_path'],
                            directory / f'r{rung}_s{item["index"]}_children', 2, 10, output)
                record = {'rung': rung, 'rendition': full, 'parents': parents}
                save(directory / f'r{rung}_media.json', record)
                media.append(record)
                journal.emit('map_measurement_start', clip=clip, rung=rung)
                measured = mse_map(reference, sample_frames(rendition))
                with (directory / f'r{rung}_map.npy').open('xb') as f:
                    np.save(f, measured, allow_pickle=False)
                maps.append(measured)
                journal.emit('rung_complete', clip=clip, rung=rung)
            maps = np.stack(maps)
            map_path = directory / 'sender_maps.npz'
            with map_path.open('xb') as f:
                np.savez_compressed(f, mse=maps)
            labels = []
            for identity in selected['source_ids']:
                journal.emit('trace_aggregation_start', clip=clip, source_id=identity)
                fields = load_selected(archive, records, clip, identity)
                status, poses = project_selected(fields)
                if not status['accepted']:
                    raise ValueError('Previously validated pose changed')
                row = {'source_id': identity, 'parent': aggregate_native(maps, poses, 10),
                       'child': aggregate_native(maps, poses, 2)}
                save(directory / f'label_{identity}.json', row)
                labels.append(row)
            label_path = directory / 'offline_evaluation_labels.json'
            save(label_path, {'information_scope': 'offline_evaluation_only', 'rows': labels})
            record = {**selected, 'status': 'prepared_offline', 'media': media,
                'phase_diagnostic': phase, 'sender_maps_sha256': sha256(map_path),
                'offline_labels_sha256': sha256(label_path), 'trace_label_rows': len(labels),
                'source_sha256': sha256(source)}
            save(directory / 'clip_manifest.json', record)
            clips.append(record)
            journal.emit('clip_complete', clip=clip)
    counts = census(clips)
    if counts != frozen['plan']['expected']:
        raise ValueError('Incomplete preparation census')
    return {'schema': 'wu-private-preparation-v2', 'registration_sha256': digest(frozen),
        'clips': clips, 'counts': counts, 'quality_outputs_created': True,
        'recovery_experiment_performed': False, 'controller_access_to_future_labels_allowed': False,
        'runtime': json.loads(RUNTIME.read_text())}


def execute(private, output, activation):
    frozen = authorize(private, output, activation)
    output.mkdir(parents=True)
    with (output / 'progress.jsonl').open('xb') as f:
        journal = Journal(f)
        try:
            journal.emit('authorized_inputs_verified')
            report = derive(private, output, frozen, journal)
            save(output / 'manifest.json', report)
            journal.emit('complete')
            return report
        except Exception as exc:
            save(output / 'failure.json', {'status': 'failed_incomplete', 'type': type(exc).__name__,
                'registration_sha256': digest(frozen), 'automatic_retry': False, 'last_stage': journal.last})
            raise


def main():
    p = argparse.ArgumentParser(__doc__)
    p.add_argument('--private-dir', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--activate-fresh-quality', required=True)
    a = p.parse_args()
    try:
        report = execute(a.private_dir, a.output, a.activate_fresh_quality)
    except Exception:
        raise SystemExit('Preparation failed; preserve private evidence and inspect the last stage') from None
    print(json.dumps({'manifest_sha256': digest(report), 'counts': report['counts']}))


if __name__ == '__main__':
    main()
