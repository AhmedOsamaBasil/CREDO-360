"""Derive scalar motion/quality envelopes from existing private exposed traces.

No downloads, raw-pose publication or future labels in the entry-bound API.
"""
import argparse
import gzip
import hashlib
import json
import math
from pathlib import Path
import zipfile
import numpy as np
from metric_contract.run import canonical, sha
from metric_contract.core import path_arrays, TICKS
from admission_contract.core import clocks, ETA
from adaptive_audit.run import read_gzip, prior_artifact
from temporal_viewport.core import (GRID, SCALE, orientation_cells, mask_distances,
    required_sampled_speed, fit_speed, feature_table, scores_for_maps)

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'temporal_viewport/data/exposed_v1'
MAPS = ROOT/'feedback_opportunity/data/maps_v1'
PRIVATE = ROOT/'.external/feedback_opportunity_v1/client_events.json'
OWN = ('__init__.py', 'core.py', 'prepare.py', 'run.py', 'test_core.py', 'test_validation.py', 'PLAN.md', 'THEORY.md')
DEPS = ('metric_contract/core.py', 'metric_contract/run.py', 'admission_contract/core.py',
        'duration_contract/core.py', 'adaptive_audit/run.py', 'geometric_admission/geometry.py',
        'feedback_opportunity/feedback.py')


def private_traces(path):
    result = {}
    with zipfile.ZipFile(path) as archive:
        for name in sorted(archive.namelist()):
            if not name.endswith('.json'):
                continue
            subject = int(Path(name).name.split('_', 1)[0])
            if subject in result:
                raise ValueError('Duplicate identity files; no implicit audio-condition selection')
            records = json.loads(archive.read(name))['data'][0]['pitch_yaw_roll_data_hmd']
            times = np.array([r['sec'] for r in records], dtype=float); times -= times[0]
            yaw = np.array([r['yaw'] for r in records], dtype=float)
            pitch = np.array([r['pitch'] for r in records], dtype=float)
            keep = times <= 60; times, yaw, pitch = times[keep], yaw[keep], pitch[keep]
            if len(times) < 2 or (np.diff(times) < 0).any():
                raise ValueError('Nonmonotone or missing source observations')
            duplicate = np.flatnonzero(np.diff(times) == 0)
            if any(yaw[i] != yaw[i+1] or pitch[i] != pitch[i+1] for i in duplicate):
                raise ValueError('Conflicting poses at identical source timestamps; no finite speed inferred')
            unique = np.r_[True, np.diff(times) > 0]
            result[subject] = {'time': times[unique], 'yaw': yaw[unique], 'pitch': pitch[unique],
                               'identical_timestamp_duplicates_removed': len(duplicate)}
    if set(result) != set(range(1, 29)):
        raise ValueError('Expected 28 source identities')
    return result


def micro_speed(value):
    # Quantize away insignificant library arithmetic before outward rounding.
    return int(math.ceil(round(float(value), 8)*SCALE))


def provenance():
    return {'source_sha256': {'temporal_viewport/'+n: sha(ROOT/'temporal_viewport'/n) for n in OWN},
            'dependency_sha256': {n: sha(ROOT/n) for n in DEPS},
            'map_metadata_sha256': sha(MAPS/'metadata.json'),
            'adaptive_artifact_sha256': sha(ROOT/'adaptive_audit/results/analytic_v1/results.json.gz'),
            'geometric_artifact_sha256': sha(ROOT/'geometric_admission/results/exposed_v1/results.json.gz')}


def derive():
    meta = json.loads((MAPS/'metadata.json').read_text())
    if sha(PRIVATE) != meta['private_events_sha256']:
        raise ValueError('Private observed-prefix cache changed')
    events = json.loads(PRIVATE.read_text()); anchors = {}; sampled = {}
    for event in events:
        cohort, scene, sid, segment = event['key'].split(':'); key = ':'.join((cohort, scene, sid))
        sampled.setdefault(key, []).extend(event['events'])
        if int(segment) == 1:
            anchors[key] = event['events'][-1]
    old = prior_artifact('geometric_admission/results/exposed_v1')
    adaptive = prior_artifact('adaptive_audit/results/analytic_v1')
    family = old['family']; cells = orientation_cells(family)
    geometric = {r['scene']: np.array(r['lower']) for r in old['scene_envelopes']}
    contexts = {r['scene']: {k: r[k] for k in ('scene', 'cohort', 'costs', 'durations_ticks', 'reserve_bytes')}
                for r in adaptive['contexts'] if r['eta'] == 'half_second'}
    entries = [{k: r[k] for k in ('key', 'cohort', 'scene', 'loss')} for r in adaptive['rows'] if r['eta'] == 'half_second']
    motion = []; distance_cache = {}; map_scores = {}; sources = []
    for source in meta['sources']:
        cohort, scene = source['cohort'], source['scene']
        folder = 'feasibility_v2' if cohort == 'v2' else 'horizon_v3'
        archive = ROOT/'.external'/folder/'traces'/f'{scene}.zip'
        if sha(archive) != source['trace_sha256']:
            raise ValueError('Exposed trace archive changed')
        map_path = MAPS/source['map_file']
        if sha(map_path) != source['descriptor']:
            raise ValueError('Sender map changed')
        maps = np.load(map_path)['mse']; map_scores[scene] = scores_for_maps(maps, family)
        traces = private_traces(archive)
        sources.append({'cohort': cohort, 'scene': scene, 'trace_sha256': source['trace_sha256'],
                        'map_sha256': source['descriptor']})
        for sid, series in sorted(traces.items()):
            key = f'{cohort}:{scene}:{sid}'; anchor = anchors[key]
            index = np.searchsorted(series['time'], 19.5, side='right')-1
            if index < 0 or any(abs(float(series[k][index])-anchor[n]) > 1e-9 for k, n in (('time', 'poseTime'), ('yaw', 'yaw'), ('pitch', 'pitch'))):
                raise ValueError('Past-only anchor differs from frozen causal sampling')
            speed = required_sampled_speed(series['time'], series['yaw'], series['pitch'])
            future = speed[index:]
            samples = sorted(sampled[key], key=lambda x: x['mediaTime'])
            coarse = required_sampled_speed([x['poseTime'] for x in samples], [x['yaw'] for x in samples], [x['pitch'] for x in samples])
            age = math.ceil((20-anchor['poseTime'])*TICKS)
            distance_cache[key] = (mask_distances(anchor['yaw'], anchor['pitch'], family, cells), age)
            motion.append({'key': key, 'scene': scene, 'cohort': cohort, 'subject': sid,
                'observations': len(series['time']), 'last_observation_seconds': round(float(series['time'][-1]), 8),
                'minimum_interval_seconds': round(float(np.diff(series['time']).min()), 8),
                'median_interval_seconds': round(float(np.median(np.diff(series['time']))), 8),
                'whole_max_speed_microdeg_s': micro_speed(speed.max()),
                'after_anchor_max_speed_microdeg_s': micro_speed(future.max()),
                'one_hz_max_speed_microdeg_s': micro_speed(coarse.max()),
                'identical_timestamp_duplicates_removed': series['identical_timestamp_duplicates_removed']})
        print(f'Exposed motion descriptors: {scene}', flush=True)
    motion_by_key = {r['key']: r for r in motion}; tables = {}; configs = []; checks = 0
    for entry in entries:
        cohort, scene, recipient, donor = entry['key'].split(':')
        context = contexts[scene]; costs = np.array(context['costs']); ds = context['durations_ticks']
        arrays = path_arrays(costs, 4, context['reserve_bytes']); paths = arrays['choices']
        candidates = [(f'grid_{v}', v*SCALE, []) for v in GRID]
        for name, quantile in (('crossfit_p95', .95), ('crossfit_max', 1.)):
            speed, train = fit_speed(motion, scene, {int(recipient), int(donor)}, quantile)
            candidates.append((name, speed, train))
        for name, speed, train in candidates:
            people = [f'{cohort}:{scene}:{sid}' for sid in (recipient, donor)]
            covered = [motion_by_key[k]['after_anchor_max_speed_microdeg_s'] <= speed for k in people]
            for eta in (0, ETA):
                mode = 'ideal' if eta == 0 else 'half_second'; ends = clocks(costs, paths, ds, eta)
                refs = []
                for key in people:
                    table_key = f'{key}:{speed}:{mode}'; refs.append(table_key)
                    if table_key in tables:
                        continue
                    distances, age = distance_cache[key]
                    parts = [feature_table(map_scores[scene], distances, age, speed, ds[t], t,
                              np.unique(ends[:, j, :]), geometric[scene]) for j, t in enumerate(range(2, 6))]
                    tables[table_key] = {'parts': parts, 'speed_microdeg_s': speed,
                        'full_family_after_anchor_seconds': round(int(distances.max())/speed, 9) if speed else None}
                    checks += sum(len(p) for p in parts)
                configs.append({**entry, 'model': name, 'speed_microdeg_s': speed, 'eta': mode,
                    'training_keys': train, 'observed_source_speed_covered': covered, 'table_keys': refs})
        if len(configs) % (28*18) == 0:
            print(f'Conditional temporal tables: {len(configs)//18}/168 episodes', flush=True)
    return {'exposed_only': True, 'raw_poses_or_anchors_included': False, 'motion_statistics': motion,
            'source_archives': sources, 'private_events_sha256': meta['private_events_sha256'],
            'contexts': contexts, 'configurations': configs, 'tables': tables,
            'orientation_cell_covers': len(cells), 'direct_mask_table_checks': checks}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(__doc__); parser.add_argument('--verify', action='store_true'); args = parser.parse_args()
    prov = provenance()
    if not args.verify and OUT.exists(): parser.error('Preserve existing derived data')
    result = derive(); digest = hashlib.sha256(canonical(result)).hexdigest()
    if args.verify:
        saved = read_gzip(OUT/'features.json.gz'); meta = json.loads((OUT/'metadata.json').read_text())
        if saved != result or digest != meta['scientific_sha256'] or any(meta[k] != v for k, v in prov.items()):
            raise ValueError('Private derivation replay mismatch')
    else:
        OUT.mkdir(parents=True)
        (OUT/'features.json.gz').write_bytes(gzip.compress(canonical(result), mtime=0))
        (OUT/'metadata.json').write_text(json.dumps({**prov, 'scientific_sha256': digest}, indent=2)+'\n')
    print(json.dumps({'verified': args.verify, 'scientific_sha256': digest, 'configurations': len(result['configurations']),
                      'tables': len(result['tables']), 'direct_mask_table_checks': result['direct_mask_table_checks']}))
