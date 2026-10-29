"""Bounded, metadata-only inspection of the authors' Wu benchmark download.

Network access occurs only with --probe. Participant CSVs, demographics and
video bodies are never opened. HTTP HEAD is reachability, not media validation.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor
import csv
import hashlib
import io
import json
from pathlib import Path
import re
import urllib.error
import urllib.request
import zipfile

ARCHIVE = 'https://www.dropbox.com/s/aqk6sbwqw6jyqck/vr-dataset.zip?dl=1'
CORRECTION = 'https://www.dropbox.com/s/hp9rf9vs93in6zl/2-9-HeyVR.mp4?dl=1'
MEMBERS = tuple(f'Formated_Data/Experiment_{n}/videoMeta.csv' for n in (1, 2))
AUTHOR_PAGE = 'https://wuchlei-thu.github.io/'


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


class RemoteDirectory(io.RawIOBase):
    """Read-only exact ranges; refuse whole-body fallback or excessive requests."""
    def __init__(self, url=ARCHIVE, opener=urllib.request.urlopen):
        self.opener = opener
        with opener(urllib.request.Request(url, method='HEAD'), timeout=30) as response:
            self.size = int(response.headers['Content-Length'])
        if not 0 < self.size <= 1024 ** 3:
            raise ValueError('Unsupported archive size')
        # Fresh public redirect per request; do not retain signed CDN locations.
        self.url, self.pos, self.requests, self.fetched = url, 0, 0, 0

    def seekable(self):
        return True

    def tell(self):
        return self.pos

    def seek(self, offset, whence=0):
        if whence not in (0, 1, 2):
            raise ValueError('Unknown seek origin')
        position = offset if whence == 0 else self.pos + offset if whence == 1 else self.size + offset
        if not 0 <= position <= self.size:
            raise ValueError('Seek outside archive')
        self.pos = position
        return position

    def read(self, size=-1):
        size = self.size - self.pos if size < 0 else min(size, self.size - self.pos)
        if not size:
            return b''
        if size > 2 * 1024 ** 2 or self.requests >= 30 or self.fetched + size > 4 * 1024 ** 2:
            raise ValueError('Metadata range limit')
        end = self.pos + size - 1
        request = urllib.request.Request(self.url, headers={'Range': f'bytes={self.pos}-{end}'})
        with self.opener(request, timeout=30) as response:
            if response.status != 206 or response.headers.get('Content-Range') != f'bytes {self.pos}-{end}/{self.size}':
                raise ValueError('Exact byte range not honored')
            data = response.read(size + 1)
            if len(data) != size:
                raise ValueError('Range length mismatch')
        self.pos += size
        self.requests += 1
        self.fetched += size
        return data


def parse_video_metadata(raw, experiment):
    if experiment not in (1, 2) or len(raw) > 65536:
        raise ValueError('Invalid metadata scope')
    reader = csv.DictReader(io.StringIO(raw.decode('utf-8-sig')))
    expected = ['VideoNo', 'VideoResolution', 'VideoDuration', 'FrameRate',
                'FrameCount', 'Content', 'Category', 'Bitrate', 'VideoLink', 'DropboxLink']
    if reader.fieldnames != expected:
        raise ValueError('Unexpected metadata schema')
    records = []
    for row in reader:
        if None in row or any(v is None for v in row.values()):
            raise ValueError('Malformed metadata row')
        if not re.fullmatch(r'[1-9]', row['VideoNo']):
            raise ValueError('Invalid video number')
        if not re.fullmatch(r'[0-9]+:[0-5][0-9]', row['VideoDuration']):
            raise ValueError('Invalid duration')
        minutes, seconds = map(int, row['VideoDuration'].split(':'))
        duration = minutes * 60 + seconds
        if duration < 60:
            raise ValueError('Insufficient nominal metadata duration')
        if not re.fullmatch(r'https://www\.dropbox\.com/s/[A-Za-z0-9]+/[^\s]+\?dl=0', row['DropboxLink']):
            raise ValueError('Unexpected source link')
        records.append({'experiment': experiment, 'video': int(row['VideoNo']),
            'nominal_seconds': duration, 'resolution_text': row['VideoResolution'],
            'frame_rate_text': row['FrameRate'], 'frame_count_text': row['FrameCount'],
            'content': row['Content'], 'category': row['Category'],
            'original_stimulus_link': row['DropboxLink'],
            'effective_stimulus_link': CORRECTION if experiment == 2 and row['VideoNo'] == '9'
                else row['DropboxLink'].replace('?dl=0', '?dl=1'),
            'correction_source': AUTHOR_PAGE if experiment == 2 and row['VideoNo'] == '9' else None})
    if sorted(r['video'] for r in records) != list(range(1, 10)):
        raise ValueError('Incomplete or duplicate catalogue')
    return sorted(records, key=lambda r: r['video'])


def head_status(record, opener=urllib.request.urlopen):
    result = {'experiment': record['experiment'], 'video': record['video'],
              'method': 'HEAD', 'body_downloaded': False, 'media_verified': False}
    try:
        request = urllib.request.Request(record['effective_stimulus_link'], method='HEAD')
        with opener(request, timeout=30) as response:
            result.update(status=response.status, bytes=int(response.headers.get('Content-Length', 0)),
                          content_type=response.headers.get('Content-Type', ''))
    except urllib.error.HTTPError as error:
        result.update(status=error.code, error='HTTP error')
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        result.update(status=None, error='Network or header error')
    return result


def inspect_metadata(remote):
    with zipfile.ZipFile(remote) as archive:
        infos = archive.infolist()
        names = [i.filename for i in infos]
        if len(names) != len(set(names)) or len(names) > 20000:
            raise ValueError('Ambiguous or oversized directory')
        documents, records = [], []
        for experiment, member in enumerate(MEMBERS, 1):
            info = archive.getinfo(member)
            if info.file_size > 65536 or info.compress_size > 65536 or info.flag_bits & 1:
                raise ValueError('Unsupported metadata member')
            # Only these two exact metadata members are ever decompressed.
            raw = archive.read(info)
            records.extend(parse_video_metadata(raw, experiment))
            documents.append({'member': member, 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
        directory = [{'name': i.filename, 'size': i.file_size, 'compressed': i.compress_size,
                      'crc32': i.CRC} for i in infos]
        return {'schema': 'wu-source-metadata-probe-v1', 'source_url': ARCHIVE,
            'archive_bytes': remote.size, 'directory_entries': len(infos),
            'directory_metadata_sha256': hashlib.sha256(canonical(directory)).hexdigest(),
            'video_members': sum(bool(re.search(r'\.(mp4|mkv|webm)$', n, re.I)) for n in names),
            'readme_or_license_members': sum(bool(re.search(r'(^|/)(readme|licen[cs]e|copyright)[^/]*$', n, re.I)) for n in names),
            'metadata_documents': documents, 'records': records,
            'range_requests': remote.requests, 'range_bytes': remote.fetched,
            'trace_members_opened': 0, 'demographic_members_opened': 0,
            'video_bodies_downloaded': 0, 'fresh_quality_or_recovery_outcomes': 0,
            'state': 'source_metadata_only_not_experiment_ready'}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--probe', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise SystemExit('Refusing to replace an earlier source-access attempt')
    result = inspect_metadata(RemoteDirectory())
    with ThreadPoolExecutor(max_workers=3) as pool:
        result['video_head_checks'] = list(pool.map(head_status, result['records']))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('xb') as stream:
        stream.write(canonical(result))
    print(json.dumps({'metadata_records': len(result['records']), 'heads': result['video_head_checks'],
        'range_bytes': result['range_bytes'], 'trace_members_opened': 0}))


if __name__ == '__main__':
    main()
