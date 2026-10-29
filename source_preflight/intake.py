"""Inspect a local original-format archive without extracting it or using poses.

Only session checksums/configuration and trace timestamps/frame IDs are parsed.
Unknown files, including participant questionnaires, are never opened. Output
is aggregate metadata and never an experiment-ready manifest. No downloads,
coordinate conversion, quality calculation or experiment launcher is included.
"""
import argparse
from collections import Counter, defaultdict
import configparser
from decimal import Decimal, InvalidOperation
from fractions import Fraction
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import tarfile

PACKAGE = Path(__file__).resolve().parent
MAX_LINE = 4096
MAX_MEMBER = 128 * 1024 * 1024
MAX_TOTAL = 2 * 1024 * 1024 * 1024
MAX_MEMBERS = 20000
MAX_ROWS = 1000000


def require(condition, code):
    if not condition:
        raise ValueError(code)


def catalogue():
    return json.loads((PACKAGE / 'source_review.json').read_text(encoding='utf-8'))['clips']


def seconds(token):
    """Bounded exact decimal parser; reject unsupported precision, not round it."""
    require(len(token) <= 64, 'timestamp_length')
    try:
        value = Decimal(token)
    except InvalidOperation:
        raise ValueError('timestamp_format') from None
    require(value.is_finite(), 'timestamp_nonfinite')
    require(abs(value) <= Decimal('1e12'), 'timestamp_range')
    require(-12 <= value.as_tuple().exponent <= 12, 'timestamp_precision')
    return Fraction(value)


def bounded_lines(stream):
    for index in range(MAX_ROWS + 1):
        raw = stream.readline(MAX_LINE + 1)
        if not raw:
            return
        require(index < MAX_ROWS, 'row_limit')
        require(len(raw) <= MAX_LINE, 'line_limit')
        yield raw


def clock_metadata(stream):
    """Synthetic-tested candidate clock check; four pose tokens stay opaque.

    Coverage is relative to the first logged sample, NOT verified media PTS.
    Repeated frame IDs are allowed; repeated timestamps or backward IDs fail.
    No source samples are sorted, interpolated, silently removed or selected
    using their quaternion values. A valid clock does not certify valid poses.
    """
    first = previous = last_frame = None
    samples = 0
    repeated_frames = 0
    targets = [Fraction(2 * i + 1, 2) for i in range(60)]
    next_index = 0
    lags = []
    first_frame = None
    for raw in bounded_lines(stream):
        fields = raw.split()
        require(len(fields) == 6, 'trace_column_count')
        t = seconds(fields[0].decode('ascii'))
        require(re.fullmatch(rb'[0-9]{1,10}', fields[1]) is not None, 'frame_format')
        frame = int(fields[1])
        require(frame < 1000000000, 'frame_range')
        if first is None:
            first, first_frame = t, frame
        else:
            require(t > previous, 'timestamp_not_strictly_increasing')
            require(frame >= last_frame, 'frame_reversal')
            repeated_frames += frame == last_frame
        elapsed = t - first
        while next_index < len(targets) and elapsed >= targets[next_index]:
            lags.append(elapsed - targets[next_index])
            next_index += 1
        previous, last_frame = t, frame
        samples += 1
    require(samples > 0, 'empty_trace')
    duration = previous - first
    maximum = max(lags) if lags else None
    return {'rows': samples, 'first_frame': first_frame, 'last_frame': last_frame,
        'repeated_frame_rows': repeated_frames, 'span_seconds': str(duration),
        'first_timestamp_seconds': str(first), 'covered_samples': len(lags),
        'maximum_next_sample_age_seconds': None if maximum is None else str(maximum),
        'candidate_clock_eligible': first_frame == 0 and duration >= 60
            and len(lags) == 60 and maximum <= Fraction(1, 10),
        'frame_mapping_verified': False, 'pose_values_parsed': False}


def test_info(stream):
    result = {}
    for raw in bounded_lines(stream):
        fields = raw.split()
        require(len(fields) == 2, 'session_column_count')
        identity, checksum = (x.decode('ascii') for x in fields)
        require(re.fullmatch(r'[A-Za-z0-9_-]+', identity) is not None, 'video_id_format')
        require(re.fullmatch(r'[0-9a-fA-F]{32}', checksum) is not None, 'md5_format')
        require(identity not in result, 'duplicate_session_video')
        result[identity] = checksum.lower()
    require(bool(result), 'empty_session')
    return result


def configuration(stream, clip):
    raw = stream.read(65537)
    require(len(raw) <= 65536, 'config_limit')
    parser = configparser.ConfigParser(interpolation=None, strict=True)
    parser.read_string(raw.decode('utf-8'))
    video = parser[parser['Config']['textureConfig']]
    projection = parser[parser['Config']['projectionConfig']]
    require(video['type'] == 'video', 'configuration_video_type')
    require(projection['type'] == 'Equirectangular', 'configuration_projection')
    require(seconds(video['startOffsetInSecond']) == clip['offset_seconds'], 'configuration_offset')
    frame_limit = video['nbFrame']
    require(re.fullmatch(r'[0-9]{1,8}', frame_limit) is not None, 'configuration_frame_limit')
    require(int(frame_limit) > 0, 'configuration_frame_limit')
    # Do not expose local paths or infer actual duration from nbFrame / nominal fps.
    return {'offset_seconds': clip['offset_seconds'], 'configured_frame_limit': int(frame_limit)}


def safe_name(member):
    name = member.name
    require(name and '\\' not in name and ':' not in name and '\x00' not in name,
            'unsafe_member_name')
    require(not name.startswith('/') and all(x not in ('', '.', '..')
            for x in name.rstrip('/').split('/')), 'unsafe_member_path')
    require(member.isdir() or member.isfile(), 'unsupported_member_type')
    require(not member.issparse(), 'sparse_member')
    require(0 <= member.size <= MAX_MEMBER, 'member_size_limit')
    return str(PurePosixPath(name))


def inspect_archive(fileobj):
    """Never extract. Do not emit names, raw rows, paths or questionnaire data."""
    clips = {c['id']: c for c in catalogue()}
    known = set(clips)
    summary = {c: Counter() for c in clips}
    checksum_sets = defaultdict(set)
    issues = Counter()
    with tarfile.open(fileobj=fileobj, mode='r:*') as archive:
        members = {}
        folded = set()
        total = 0
        for index, member in enumerate(archive):
            require(index < MAX_MEMBERS, 'archive_member_limit')
            name = safe_name(member)
            require(name.casefold() not in folded, 'duplicate_or_case_alias_member')
            folded.add(name.casefold())
            total += member.size
            require(total <= MAX_TOTAL, 'archive_total_limit')
            members[name] = member
        opened = 0
        sessions = {}
        trace_keys = []
        for name, member in members.items():
            parts = name.split('/')
            if len(parts) < 4 or parts[0] not in ('results', 'Results'):
                continue
            if not re.fullmatch(r'uid-[A-Za-z0-9-]+', parts[1]):
                continue
            if not re.fullmatch(r'test[0-9]+', parts[2]):
                continue
            if len(parts) == 4 and parts[3] == 'testInfo.txt' and member.isfile():
                with archive.extractfile(member) as stream:
                    sessions[tuple(parts[:3])] = test_info(stream)
                opened += 1
            if len(parts) == 5 and parts[3] in known and member.isfile():
                # Exactly one original run is expected. Other runs are retained
                # as a blocking metadata issue, never silently substituted.
                if parts[4] != parts[3] + '_0.txt':
                    issues['unexpected_trace_run'] += 1
                    continue
                trace_keys.append((name, tuple(parts[:3]), parts[3]))
        seen_identity_clip = Counter()
        for name, session, clip_id in sorted(trace_keys):
            seen_identity_clip[(session[1], clip_id)] += 1
            summary[clip_id]['trace_files'] += 1
            record = sessions.get(session, {})
            if clip_id not in record:
                issues['missing_session_checksum'] += 1
            else:
                checksum_sets[clip_id].add(record[clip_id])
            ini = '/'.join(session) + '/' + clip_id + '.ini'
            if ini not in members or not members[ini].isfile():
                issues['missing_configuration'] += 1
            else:
                with archive.extractfile(members[ini]) as stream:
                    configuration(stream, clips[clip_id])
                opened += 1
                summary[clip_id]['configuration_checks'] += 1
            with archive.extractfile(members[name]) as stream:
                meta = clock_metadata(stream)
            opened += 1
            summary[clip_id]['clock_candidate_eligible'] += meta['candidate_clock_eligible']
            summary[clip_id]['rows'] += meta['rows']
        issues['multiple_sessions_for_identity_clip'] = sum(v > 1 for v in seen_identity_clip.values())
        for clip_id in clips:
            count = len(checksum_sets[clip_id])
            if count != 1:
                issues['missing_or_conflicting_stimulus_checksum'] += 1
            if summary[clip_id]['trace_files'] < 2:
                issues['insufficient_clip_traces'] += 1
        return {'schema': 'corbillon-metadata-intake-v1', 'state': 'blocked_before_outcomes',
            'members': len(members), 'opened_metadata_files': opened,
            'session_files': len(sessions), 'trace_files': len(trace_keys),
            'clips': [{'id': c, **dict(summary[c]),
                'session_stimulus_md5': sorted(checksum_sets[c])} for c in sorted(clips)],
            'issues': {k: v for k, v in sorted(issues.items()) if v},
            'pose_values_parsed': False, 'frame_mapping_verified': False,
            'reuse_terms_verified': False, 'source_adapter_frozen': False,
            'raw_data_republishable': False, 'fresh_quality_or_recovery_outcomes': 0}


def file_digests(path):
    """Legacy stimulus identity check only; MD5 is not a security guarantee."""
    md5 = hashlib.md5(usedforsecurity=False)
    sha = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            md5.update(block)
            sha.update(block)
    return {'md5': md5.hexdigest(), 'sha256': sha.hexdigest()}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    args = parser.parse_args()
    try:
        with args.archive.open('rb') as stream:
            result = inspect_archive(stream)
        result['archive_sha256'] = file_digests(args.archive)['sha256']
    except (ValueError, OSError, EOFError, tarfile.TarError, configparser.Error, KeyError):
        # Do not echo path names, configuration values, raw lines or private fields.
        print(json.dumps({'state': 'invalid_metadata_archive', 'outcomes_allowed': False}))
        raise SystemExit(2) from None
    print(json.dumps(result, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
