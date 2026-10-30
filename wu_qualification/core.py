"""Opaque-pose intake and independent scalar accounting of fixed clock rules."""
from bisect import bisect_right
import csv
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import re

from confirmation_protocol.protocol import directed_cycle
from wu_source.acquire import canonical
from wu_source.clocks import HEADER
from wu_calibration.core import HALF_TARGETS,plan
from wu_calibration.adapter import select_indices,validate_spec

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'wu_qualification'


class MetadataError(ValueError):
    """A sanitized, fixed reason code; never carries source field values."""


def clips():
    validate_spec()
    return tuple(plan()['confirmation_clips'])


def member(clip,identity):
    if clip not in clips(): raise ValueError('Unregistered confirmation clip')
    if not re.fullmatch(r'[1-9]|[1-3][0-9]|4[0-8]',str(identity)): raise ValueError('Invalid source ID')
    return f'Formated_Data/Experiment_{clip[1]}/{identity}/video_{int(clip[-2:])-1}.csv'


def parse_clocks(raw):
    """Columns2..8 are opaque strings, even when not parseable as numbers."""
    try:
        def bounded():
            for line in io.StringIO(raw.decode('utf-8-sig'),newline=''):
                if len(line)>4096: raise MetadataError('oversized_metadata_row')
                yield line
        reader=csv.reader(bounded(),strict=True)
        if next(reader,None)!=HEADER: raise MetadataError('unexpected_header')
        wall=[]; playback=[]; origin=None
        for row in reader:
            if len(row)!=9: raise MetadataError('malformed_row')
            try:
                stamp=datetime.fromisoformat(row[0]); t=float(row[1])
                if origin is None: origin=stamp
                elapsed=(stamp-origin).total_seconds()
            except (ValueError,TypeError,OverflowError):
                raise MetadataError('invalid_clock_field') from None
            if not math.isfinite(t) or t<0: raise MetadataError('invalid_playback_clock')
            wall.append(elapsed); playback.append(t)
        if len(wall)<2: raise MetadataError('insufficient_clock_rows')
        return wall,playback
    except (UnicodeError,csv.Error):
        raise MetadataError('invalid_csv_encoding_or_syntax') from None


def intake(archive,clip,identity):
    name=member(clip,identity)  # Guard before any archive-member read.
    try: info=archive.getinfo(name)
    except KeyError: raise MetadataError('missing_trace_member') from None
    if info.file_size>20_000_000: raise MetadataError('oversized_trace_member')
    if (info.external_attr>>16)&0o170000==0o120000: raise MetadataError('linked_trace_member')
    raw=archive.read(name)
    return hashlib.sha256(raw).hexdigest(),parse_clocks(raw)


def validate_archive_directory(archive):
    names=archive.namelist()
    if len(names)!=len(set(n.casefold() for n in names)): raise ValueError('Duplicate archive path')
    for name in names:
        if '\\' in name or PurePosixPath(name).is_absolute() or '..' in PurePosixPath(name).parts:
            raise ValueError('Unsafe archive path')


def scalar_evidence(wall,playback):
    counts=[0]*60; ages=[None]*60; indices=[None]*60
    for i,(before,after) in enumerate(zip(playback,playback[1:]),1):
        if after<=before: continue
        # Independent interval counting, not the vectorized target selector.
        for j in range(bisect_right(HALF_TARGETS,before),bisect_right(HALF_TARGETS,after)):
            counts[j]+=1
            ages[j]=after-HALF_TARGETS[j] if counts[j]==1 else None
            indices[j]=i if counts[j]==1 else None
    wall_invalid=any(not math.isfinite(t) or t<0 for t in wall)
    return {'rows':len(playback),'first_playback_seconds':playback[0],
        'maximum_playback_seconds':max(playback),'wall_invalid':wall_invalid,
        'wall_backward_steps':sum(b<a for a,b in zip(wall,wall[1:])),
        'wall_duplicate_steps':sum(b==a for a,b in zip(wall,wall[1:])),
        'crossing_counts':counts,'unique_crossing_age_seconds':ages},indices


def reasons_from_evidence(e):
    if e['wall_invalid'] or e['wall_backward_steps']:
        return ['invalid_or_backward_wall_clock']
    counts=e['crossing_counts']; ages=e['unique_crossing_age_seconds']
    reasons=[]
    if any(n==0 for n in counts): reasons.append('missing_target_crossing')
    if any(n>1 for n in counts): reasons.append('ambiguous_target_crossing')
    if any(n==1 and a>.1+1e-9 for n,a in zip(counts,ages)): reasons.append('stale_target_crossing')
    if e['first_playback_seconds']>.5: reasons.append('missing_initial_bracket')
    if e['maximum_playback_seconds']<60: reasons.append('missing_60s_coverage')
    return reasons


def qualify_clock(wall,playback):
    actual=select_indices(wall,playback)
    e,indices=scalar_evidence(wall,playback); reasons=reasons_from_evidence(e)
    selected=indices if not reasons else []
    if actual['accepted']!=(not reasons) or actual['reasons']!=reasons or actual['indices']!=selected:
        raise ValueError('Independent clock decision/index mismatch')
    return {'clock_qualified':not reasons,'clock_reasons':reasons,'clock_evidence':e,
        'independent_clock_check':True,
        'selected_row_indices_sha256':hashlib.sha256(canonical(selected)).hexdigest() if selected else None}


def media_decision(m):
    s=m['stream']; reasons=[]
    if float(s['start_time'])!=0 or m['first_pts_seconds']!=0: reasons.append('nonzero_media_origin')
    if float(s['duration'])<60 or m['last_pts_seconds']<60: reasons.append('insufficient_media_coverage')
    if m['maximum_target_frame_age_seconds']>.1+1e-9: reasons.append('stale_target_frame')
    if m['target_timing_pass']!=(not reasons): raise ValueError('Frozen media gate inconsistent')
    return {'qualified':not reasons,'reasons':reasons,'source_sha256':m['sha256'],
        'stream_start_seconds':float(s['start_time']),'first_pts_seconds':m['first_pts_seconds'],
        'available_seconds':float(s['duration'])}


def summarize(rows,media):
    summaries=[]
    for clip in clips():
        selected=[r for r in rows if r['clip']==clip]
        clock_ids=sorted(r['source_id'] for r in selected if r['clock_qualified'])
        qualified_ids=clock_ids if media[clip]['qualified'] else []
        clip_reasons=list(media[clip]['reasons'])
        if len(clock_ids)<2: clip_reasons.append('insufficient_two_user_clock_roster')
        summaries.append({'clip':clip,'experiment':int(clip[1]),
            'condition':'free_exploration' if clip[1]=='1' else 'content_focused_memory_test',
            'registered_traces':len(selected),'clock_qualified_source_ids':clock_ids,
            'metadata_qualified_source_ids':qualified_ids,'clip_qualified':not clip_reasons,
            'clip_reasons':clip_reasons,
            'directed_pairs':[list(x) for x in directed_cycle(qualified_ids)] if len(qualified_ids)>=2 else []})
    return summaries
