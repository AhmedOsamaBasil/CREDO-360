"""Clock-only validation; all pose/position/wall-time values remain opaque."""
import csv
import io
import math
from pathlib import PurePosixPath
import re
import zipfile

HEADER = ['Timestamp', 'PlaybackTime', 'UnitQuaternion.x', 'UnitQuaternion.y',
          'UnitQuaternion.z', 'UnitQuaternion.w', 'HmdPosition.x',
          'HmdPosition.y', 'HmdPosition.z']
TARGETS = tuple(i + .5 for i in range(60))
TRACE = re.compile(r'Formated_Data/Experiment_([12])/([1-9]|[1-3][0-9]|4[0-8])/video_([0-8])\.csv')


def scan_clock(lines):
    def bounded():
        for line in lines:
            if len(line) > 4096:
                raise ValueError('Oversized trace record')
            yield line
    rows = csv.reader(bounded(), strict=True)
    if next(rows, None) != HEADER:
        raise ValueError('Unexpected trace header')
    times = []
    target = 0
    ages = []
    duplicates = 0
    reasons = []
    for row in rows:
        if len(row) != 9:
            reasons.append('row_shape'); break
        try:
            t = float(row[1])
        except ValueError:
            reasons.append('invalid_playback_time'); break
        if not math.isfinite(t) or t < 0:
            reasons.append('invalid_playback_time'); break
        if times and t < times[-1]:
            reasons.append('backward_playback_time'); break
        duplicates += int(bool(times) and t == times[-1])
        times.append(t)
        while target < len(TARGETS) and t >= TARGETS[target]:
            ages.append(t - TARGETS[target]); target += 1
        if t >= 60:
            break
    if not times or times[0] > .5:
        reasons.append('missing_start')
    if not times or times[-1] < 60:
        reasons.append('missing_60s_coverage')
    if len(ages) != 60 or max(ages, default=float('inf')) > .1 + 1e-9:
        reasons.append('missing_or_stale_sample')
    return {'eligible': not reasons, 'reasons': reasons,
        'rows_through_window': len(times), 'duplicates': duplicates,
        'first_seconds': times[0] if times else None,
        'last_seconds': times[-1] if times else None,
        'targets_covered': len(ages), 'maximum_next_age_seconds': max(ages) if ages else None}


def roster(archive):
    result = []
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        if len(names) != len(set(n.casefold() for n in names)):
            raise ValueError('Duplicate archive names')
        for name in names:
            if '\\' in name or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
                raise ValueError('Unsafe archive path')
        selected = sorted((n, TRACE.fullmatch(n).groups()) for n in names if TRACE.fullmatch(n))
        for name in names:
            if name.startswith('Formated_Data/Experiment_') and name.endswith('.csv') and not TRACE.fullmatch(name) and not name.endswith('/videoMeta.csv'):
                raise ValueError('Unexpected trace member')
        expected = {(str(e), str(u), str(k)) for e in (1, 2) for u in range(1, 49) for k in range(9)}
        if {groups for _, groups in selected} != expected:
            raise ValueError('Incomplete or unexpected 864-trace source roster')
        for name, (experiment, identity, index) in selected:
            info = z.getinfo(name)
            if info.file_size > 20_000_000 or (info.external_attr >> 16) & 0o170000 == 0o120000:
                raise ValueError('Oversized or linked trace')
            with z.open(name) as raw, io.TextIOWrapper(raw, encoding='utf-8-sig', newline='') as stream:
                # The parser never converts or emits columns 0 or 2..8.
                record = scan_clock(stream)
            result.append({'experiment': int(experiment), 'video': int(index) + 1,
                'source_id': identity, 'member_crc32': f'{info.CRC:08x}', **record})
    return result
