"""Source/clock metadata report and offline validation; no quality labels."""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from confirmation_protocol.protocol import directed_cycle
from .acquire import ACCESS, ROOT, canonical, jobs, sha256
from .clocks import roster
from .diagnose_clocks import run as diagnose_clocks

PACKAGE = ROOT / 'wu_source'
BINDINGS = ('wu_source/PROTOCOL.md', 'wu_source/acquire.py', 'wu_source/clocks.py',
    'wu_source/geometry.py', 'wu_source/media.py', 'wu_source/audit.py',
    'wu_source/diagnose_clocks.py',
    'source_preflight/results/access_v1/wu_metadata.json', 'confirmation_protocol/design.json')


def clip_summaries(rows, media):
    summaries = []
    catalogue = json.loads(ACCESS.read_text(encoding='utf-8'))['records']
    by_id = {m['id']: m for m in media['records']}
    for record in catalogue:
        e, v = record['experiment'], record['video']
        selected = [r for r in rows if (r['experiment'], r['video']) == (e,v)]
        ids = sorted(r['source_id'] for r in selected if r['eligible'])
        m = by_id[f'e{e}v{v:02}']; stream = m['stream']
        summaries.append({'id':m['id'], 'experiment':e, 'video':v,
            'condition':'free_exploration' if e == 1 else 'content_focused_memory_test',
            'source_traces':len(selected), 'clock_eligible_source_ids':ids,
            'excluded_source_ids':sorted(r['source_id'] for r in selected if not r['eligible']),
            'exclusion_reasons':dict(sorted(Counter(reason for r in selected for reason in r['reasons']).items())),
            'candidate_directed_cycle':[list(p) for p in directed_cycle(ids)] if len(ids) >= 2 else [],
            'source_timing_pass':m['target_timing_pass'],
            'catalogue':{k:record[k] for k in ('content','nominal_seconds','frame_rate_text','frame_count_text','resolution_text')},
            'catalogue_differences':{
                'duration_seconds':float(stream['duration'])-record['nominal_seconds'],
                'average_fps':float(Fraction(stream['avg_frame_rate']))-float(record['frame_rate_text']),
                'declared_frames':int(stream['nb_frames'])-int(record['frame_count_text']),
                'dimensions_match':f"{stream['width']}*{stream['height']}" == record['resolution_text']}})
    return summaries


def collect(private, media):
    assets = []
    partials = []
    for job in jobs():
        path = private / job['name']
        receipt = json.loads((private/(job['name']+'.receipt.json')).read_text())
        if path.stat().st_size != job['bytes'] or sha256(path) != receipt['sha256'] or receipt['source_url'] != job['url']:
            raise ValueError('Private source receipt differs')
        assets.append({'id':job['id'], 'bytes':job['bytes'], 'sha256':receipt['sha256'],
            'source_url':job['url'], 'successful_attempt':receipt.get('attempt',1)})
        for part in sorted(private.glob(job['name'] + '*.part')):
            partials.append({'asset':job['id'], 'attempt_file':part.name,
                'bytes':part.stat().st_size, 'sha256':sha256(part), 'accepted_as_source':False})
    rows = roster(private / 'vr-dataset.zip')
    return {'schema':'wu-original-source-audit-v1', 'state':'blocked_before_outcomes',
        'assets':assets, 'retained_incomplete_download_attempts':partials,
        'clock_rows':rows, 'media':media, 'clips':clip_summaries(rows,media),
        'posthoc_clock_diagnosis':diagnose_clocks(private / 'vr-dataset.zip'),
        'trace_file_count':len(rows), 'clock_eligible_trace_count':sum(r['eligible'] for r in rows),
        'participant_orientations_interpreted':False, 'demographics_opened':False,
        'quality_outcomes_derived':False, 'recovery_outcomes_derived':False,
        'geometry_gate':{'quaternion_formula_synthetic_tests':True,
            'texture_wrap_sign_independently_verified':False,
            'candidate_signs':[-1,1], 'default_production_adapter':False},
        'limitations':['Source decoding is not historical HMD display-clock validation.',
            'The 864 trace files repeat 48 source identities across 18 clips and two conditions.',
            'Clock eligibility is not a quality/recovery outcome or a verified coordinate adapter.',
            'No source-freeze manifest is issued until texture mapping is independently supported.',
            'Author-linked availability is not a blanket redistribution license.']}


def validate(report):
    if report['schema'] != 'wu-original-source-audit-v1' or report['state'] != 'blocked_before_outcomes':
        raise ValueError('Source status must retain unresolved geometry gate')
    for field in ('participant_orientations_interpreted','demographics_opened','quality_outcomes_derived','recovery_outcomes_derived'):
        if report[field] is not False: raise ValueError('Source-only scope changed')
    gate=report['geometry_gate']
    if gate != {'quaternion_formula_synthetic_tests':True, 'texture_wrap_sign_independently_verified':False,
                'candidate_signs':[-1,1], 'default_production_adapter':False}:
        raise ValueError('Unverified source geometry presented as complete')
    assets={a['id']:a for a in report['assets']}
    if len(assets) != 19 or len(report['assets']) != 19: raise ValueError('Source asset count')
    for job in jobs():
        a=assets[job['id']]
        if a['bytes'] != job['bytes'] or a['source_url'] != job['url'] or len(a['sha256']) != 64:
            raise ValueError('Source asset binding')
    rows=report['clock_rows']
    expected={(e,v,str(u)) for e in (1,2) for v in range(1,10) for u in range(1,49)}
    if len(rows) != 864 or {(r['experiment'],r['video'],r['source_id']) for r in rows} != expected:
        raise ValueError('Clock roster completeness')
    for r in rows:
        if r['eligible'] != (not r['reasons']): raise ValueError('Clock exclusion inconsistency')
        if r['eligible'] and not (r['first_seconds'] <= .5 and r['last_seconds'] >= 60 and
            r['targets_covered'] == 60 and r['maximum_next_age_seconds'] <= .1+1e-9):
            raise ValueError('False clock eligibility')
    media=report['media']['records']
    if len(media) != 18 or {m['id'] for m in media} != set(assets)-{'traces'}:
        raise ValueError('Media catalogue completeness')
    for m in media:
        if m['sha256'] != assets[m['id']]['sha256']: raise ValueError('Media hash binding')
        actual=(float(m['stream']['start_time']) == 0 and float(m['stream']['duration']) >= 60
            and m['first_pts_seconds'] == 0 and m['last_pts_seconds'] >= 60
            and m['maximum_target_frame_age_seconds'] <= .1+1e-9)
        if m['target_timing_pass'] != actual: raise ValueError('False media timing flag')
    d=report['posthoc_clock_diagnosis']
    if d['eligibility_revised'] is not False or d['pose_values_interpreted'] is not False or len(d['rows']) != 864:
        raise ValueError('Clock diagnosis scope changed')
    if {(r['experiment'],r['video'],r['source_id']) for r in d['rows']} != expected:
        raise ValueError('Clock diagnosis roster differs')
    if report['clips'] != clip_summaries(rows,report['media']): raise ValueError('Clip summary differs')
    if report['trace_file_count'] != len(rows) or report['clock_eligible_trace_count'] != sum(r['eligible'] for r in rows):
        raise ValueError('Trace aggregate differs')
    return {'trace_files':len(rows), 'clock_eligible':sum(r['eligible'] for r in rows),
        'media_timing_pass':sum(m['target_timing_pass'] for m in media),
        'ready_for_outcomes':False}


def bindings():
    return {p:hashlib.sha256((ROOT/p).read_text(encoding='utf-8').replace('\r\n','\n').encode()).hexdigest() for p in BINDINGS}


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--private-dir',type=Path)
    parser.add_argument('--media-audit',type=Path)
    parser.add_argument('--output',type=Path,default=PACKAGE/'results/source_v1')
    parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.verify:
        report=json.loads((args.output/'report.json').read_text())
        metadata=json.loads((args.output/'metadata.json').read_text())
        if metadata != {'report_sha256':hashlib.sha256(canonical(report)).hexdigest(),'bindings':bindings()}:
            raise ValueError('Published source/method binding differs')
    else:
        if not args.private_dir or not args.media_audit: parser.error('Private source and media audit required')
        if args.output.exists(): raise ValueError('Refusing to replace earlier source audit')
        report=collect(args.private_dir,json.loads(args.media_audit.read_text()))
        validate(report)
        args.output.mkdir(parents=True)
        (args.output/'report.json').write_bytes(canonical(report))
        (args.output/'metadata.json').write_bytes(canonical({'report_sha256':hashlib.sha256(canonical(report)).hexdigest(),'bindings':bindings()}))
    print(json.dumps({**validate(report),'sha256':hashlib.sha256(canonical(report)).hexdigest()}))


if __name__ == '__main__': main()
