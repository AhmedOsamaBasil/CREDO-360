"""Actual source-file stream and decoded-PTS audit; no quality calculations."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from fractions import Fraction
import json
import math
from pathlib import Path
import subprocess

from .acquire import canonical, jobs, sha256
from .clocks import TARGETS


def evaluate_pts(pts):
    if not pts or not all(math.isfinite(t) and t >= 0 for t in pts):
        raise ValueError('Missing or invalid frame PTS')
    if any(b <= a for a, b in zip(pts, pts[1:])):
        raise ValueError('Nonincreasing decoded PTS')
    ages = []
    index = 0
    for target in TARGETS:
        while index + 1 < len(pts) and pts[index + 1] <= target + 1e-9:
            index += 1
        ages.append(target - pts[index])
    return {'first_pts_seconds': pts[0], 'last_pts_seconds': pts[-1],
        'decoded_prefix_frames': len(pts),
        'maximum_interframe_gap_seconds': max((b-a for a,b in zip(pts,pts[1:])), default=0),
        'maximum_target_frame_age_seconds': max(ages),
        'target_timing_pass': pts[0] == 0 and pts[-1] >= 60 and min(ages) >= -1e-9 and max(ages) <= .1 + 1e-9}


def probe(path, executable='ffprobe'):
    command = [executable, '-v', 'error', '-threads', '2', '-select_streams', 'v:0',
        '-read_intervals', '%61', '-show_streams', '-show_frames', '-show_entries',
        'stream=width,height,r_frame_rate,avg_frame_rate,time_base,start_time,duration,nb_frames:frame=best_effort_timestamp_time',
        '-of', 'json', str(path)]
    completed = subprocess.run(command, check=True, capture_output=True, timeout=600)
    if completed.stderr.strip():
        raise ValueError('Decoder reported errors; inspect privately')
    value = json.loads(completed.stdout)
    if len(value['streams']) != 1:
        raise ValueError('Exactly one selected video stream required')
    stream = value['streams'][0]
    for key in ('r_frame_rate', 'avg_frame_rate', 'time_base'):
        if Fraction(stream[key]) <= 0:
            raise ValueError('Invalid stream time metadata')
    timing = evaluate_pts([float(f['best_effort_timestamp_time']) for f in value['frames']])
    timing['target_timing_pass'] = timing['target_timing_pass'] and float(stream['start_time']) == 0 and float(stream['duration']) >= 60
    return {'stream': {k:stream[k] for k in ('width', 'height', 'r_frame_rate',
        'avg_frame_rate', 'time_base', 'start_time', 'duration', 'nb_frames')},
        **timing}


def run(private, executable):
    version = subprocess.run([executable, '-version'], check=True, capture_output=True,
                             text=True).stdout.splitlines()[0]
    def one(job):
        path = private / job['name']
        receipt = json.loads((private / (job['name'] + '.receipt.json')).read_text())
        if path.stat().st_size != job['bytes'] or sha256(path) != receipt['sha256']:
            raise ValueError('Private media hash differs')
        record = {'id': job['id'], 'sha256': receipt['sha256'], **probe(path, executable)}
        print(json.dumps({'id': job['id'], 'timing_pass': record['target_timing_pass']}), flush=True)
        return record
    with ThreadPoolExecutor(max_workers=2) as pool:
        records = list(pool.map(one, [j for j in jobs() if j['kind'] == 'mp4']))
    return {'schema': 'wu-source-media-v1', 'decoder': version,
            'records': records, 'quality_outcomes_derived': False}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--private-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--ffprobe', default='ffprobe')
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to overwrite earlier media audit')
    result = run(args.private_dir, args.ffprobe)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(canonical(result))


if __name__ == '__main__':
    main()
