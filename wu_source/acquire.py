"""Acquire only author-linked originals into a private directory outside Git.

No archive extraction, participant parsing, quality measurement or recovery
calculation. Existing verified files are checked; partial attempts are retained
and never automatically overwritten or retried. TLS verification stays enabled.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ACCESS = ROOT / 'source_preflight/results/access_v1/wu_metadata.json'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def sha256(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 ** 2), b''):
            value.update(block)
    return value.hexdigest()


def jobs():
    access = json.loads(ACCESS.read_text(encoding='utf-8'))
    heads = {(h['experiment'], h['video']): h for h in access['video_head_checks']}
    result = [{'id': 'traces', 'name': 'vr-dataset.zip', 'url': access['source_url'],
               'bytes': access['archive_bytes'], 'kind': 'zip'}]
    for row in access['records']:
        e, v = row['experiment'], row['video']
        result.append({'id': f'e{e}v{v:02}', 'name': f'e{e}v{v:02}.mp4',
            'url': row['effective_stimulus_link'], 'bytes': heads[e, v]['bytes'], 'kind': 'mp4'})
    return result


def acquire(job, private, opener=urllib.request.urlopen, attempt=1):
    path = private / job['name']
    receipt = private / (job['name'] + '.receipt.json')
    part = private / (job['name'] + ('.part' if attempt == 1 else f'.attempt{attempt}.part'))
    if path.exists():
        if not receipt.exists():
            raise ValueError('Existing asset has no bound receipt: ' + job['id'])
        old = json.loads(receipt.read_text(encoding='utf-8'))
        if old['source_url'] != job['url'] or path.stat().st_size != job['bytes'] or sha256(path) != old['sha256']:
            raise ValueError('Existing asset differs: ' + job['id'])
        return old
    if part.exists() or receipt.exists():
        raise ValueError('Prior partial attempt retained: ' + job['id'])
    print(json.dumps({'event': 'start', 'asset': job['id'], 'expected_bytes': job['bytes']}), flush=True)
    started = time.monotonic()
    with opener(job['url'], timeout=60) as response:
        if response.status != 200 or int(response.headers.get('Content-Length', 0)) != job['bytes']:
            raise ValueError('Source size/status changed: ' + job['id'])
        total = 0
        digest = hashlib.sha256()
        with part.open('xb') as stream:
            while True:
                block = response.read(1024 ** 2)
                if not block:
                    break
                if total == 0 and ((job['kind'] == 'zip' and not block.startswith(b'PK\x03\x04'))
                        or (job['kind'] == 'mp4' and block[4:8] != b'ftyp')):
                    raise ValueError('Source signature mismatch: ' + job['id'])
                total += len(block)
                if total > job['bytes']:
                    raise ValueError('Oversized response: ' + job['id'])
                stream.write(block)
                digest.update(block)
    if total != job['bytes']:
        raise ValueError('Incomplete response retained: ' + job['id'])
    # A completed .part is atomically moved only to its previously absent name.
    if path.exists():
        raise ValueError('Destination appeared during transfer')
    part.rename(path)
    record = {'id': job['id'], 'bytes': total, 'sha256': digest.hexdigest(), 'attempt': attempt,
        'source_url': job['url'], 'kind': job['kind'], 'source_file_only': True,
        'participant_values_parsed': False, 'quality_outcomes_derived': False}
    with receipt.open('xb') as stream:
        stream.write(canonical(record))
    print(json.dumps({'event': 'complete', 'asset': job['id'], 'bytes': total,
                      'elapsed_seconds': round(time.monotonic() - started, 2)}), flush=True)
    return record


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--private-dir', type=Path, required=True)
    parser.add_argument('--workers', type=int, default=3, choices=(1, 2, 3))
    parser.add_argument('--attempt', type=int, default=1, choices=(1, 2, 3))
    args = parser.parse_args()
    private = args.private_dir.resolve()
    if private == ROOT or ROOT in private.parents:
        raise SystemExit('Raw source directory must be outside the software repository')
    private.mkdir(parents=True, exist_ok=True)
    planned = jobs()
    failures = []
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        work = {pool.submit(acquire, job, private, attempt=args.attempt): job['id'] for job in planned}
        for future in as_completed(work):
            try:
                future.result()
            except Exception as error:
                # No temporary CDN URL, private path or remote response body.
                failures.append({'asset': work[future], 'error_type': type(error).__name__})
                print(json.dumps({'event': 'failed', **failures[-1]}), flush=True)
    print(json.dumps({'planned': len(planned), 'failed': failures, 'outcomes_derived': False}))
    if failures:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
