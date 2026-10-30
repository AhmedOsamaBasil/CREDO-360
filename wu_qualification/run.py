"""Freeze and reproduce complete metadata qualification; never convert poses."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import zipfile

from wu_source.acquire import canonical,sha256
from wu_calibration.core import plan
from .core import (ROOT,PACKAGE,MetadataError,clips,intake,validate_archive_directory,
    qualify_clock,media_decision,summarize,reasons_from_evidence)

SOURCE=ROOT/'wu_source/results/source_v1/report.json'
METHOD=PACKAGE/'method_v1.json'


def digest(value): return hashlib.sha256(canonical(value)).hexdigest()


def method_bindings():
    paths=['wu_qualification/'+p for p in ('PROTOCOL.md','core.py','run.py','test_core.py')]
    paths += ['wu_calibration/'+p for p in ('adapter.py','adapter_spec.json','amendment.json','core.py','results/calibration_v1/report.json')]
    paths += ['wu_source/clocks.py','wu_source/acquire.py','wu_source/results/source_v1/report.json',
              'confirmation_protocol/protocol.py','confirmation_protocol/design.json',
              'confirmation_protocol/results/design_v1/metadata.json']
    return {p:hashlib.sha256((ROOT/p).read_text(encoding='utf-8').replace('\r\n','\n').encode()).hexdigest() for p in paths}


def method_record():
    return {'schema':'wu-clock-media-qualification-method-v1','bindings':method_bindings(),
        'registered_clips':list(clips()),'registered_source_ids':[str(i) for i in range(1,49)],
        'pose_conversion_allowed':False,'quality_outcomes_allowed':False,
        'source_report_sha256':plan()['parent_source_report_sha256']}


def frozen_source():
    source=json.loads(SOURCE.read_text(encoding='utf-8'))
    if digest(source)!=plan()['parent_source_report_sha256']: raise ValueError('Frozen source audit changed')
    return source


def derive(private):
    if json.loads(METHOD.read_text())!=method_record(): raise ValueError('Qualification method not frozen or changed')
    source=frozen_source(); assets={a['id']:a for a in source['assets']}
    wanted=['traces',*clips()]; checked=[]
    for identity in wanted:
        filename='vr-dataset.zip' if identity=='traces' else identity+'.mp4'
        path=private/filename; expected=assets[identity]
        if path.stat().st_size!=expected['bytes'] or sha256(path)!=expected['sha256']:
            raise ValueError('Private original-file hash/size mismatch: '+identity)
        checked.append({'id':identity,'sha256':expected['sha256'],'bytes':expected['bytes']})
    media={m['id']:media_decision(m) for m in source['media']['records'] if m['id'] in clips()}
    rows=[]
    with zipfile.ZipFile(private/'vr-dataset.zip') as archive:
        validate_archive_directory(archive)
        for clip in clips():
            for identity in map(str,range(1,49)):
                row={'clip':clip,'source_id':identity}
                try:
                    member_sha,(wall,playback)=intake(archive,clip,identity)
                    row.update(trace_member_sha256=member_sha,metadata_error=None,**qualify_clock(wall,playback))
                except MetadataError as error:
                    row.update(trace_member_sha256=None,metadata_error=str(error),clock_qualified=False,
                        clock_reasons=[str(error)],clock_evidence=None,independent_clock_check=False,
                        selected_row_indices_sha256=None)
                row['media_qualified']=media[clip]['qualified']
                row['metadata_qualified']=row['clock_qualified'] and row['media_qualified']
                row['exclusion_reasons']=row['clock_reasons']+media[clip]['reasons']
                rows.append(row)
            print(json.dumps({'clip':clip,'registered_traces':48,
                'clock_qualified':sum(r['clock_qualified'] for r in rows if r['clip']==clip),
                'media_qualified':media[clip]['qualified']}),flush=True)
    return {'schema':'wu-reserved-clock-media-qualification-v1',
        'state':'metadata_roster_frozen_pose_validation_pending','method_sha256':digest(method_record()),
        'source_audit_sha256':digest(source),'private_files_checked':checked,
        'calibration_exclusions':[{'clip':c,'reason':'declared_calibration_clip'} for c in plan()['calibration_clips']],
        'media':media,'rows':rows,'clips':summarize(rows,media),
        'pose_values_interpreted':False,'quaternion_validity_checked':False,
        'quality_outcomes_derived':False,'recovery_outcomes_derived':False,
        'full_source_ready':False,'automatic_outcome_launch':False,'identity_disjoint':False}


def validate(report):
    if report['schema']!='wu-reserved-clock-media-qualification-v1' or report['state']!='metadata_roster_frozen_pose_validation_pending':
        raise ValueError('Qualification status changed')
    for key in ('pose_values_interpreted','quaternion_validity_checked','quality_outcomes_derived',
                'recovery_outcomes_derived','full_source_ready','automatic_outcome_launch','identity_disjoint'):
        if report[key] is not False: raise ValueError('Unsupported qualification scope')
    if report['method_sha256']!=digest(method_record()) or report['source_audit_sha256']!=digest(frozen_source()):
        raise ValueError('Frozen input binding differs')
    expected={(c,str(i)) for c in clips() for i in range(1,49)}; rows=report['rows']
    if len(rows)!=768 or {(r['clip'],r['source_id']) for r in rows}!=expected: raise ValueError('Incomplete metadata roster')
    source=frozen_source(); assets={a['id']:a for a in source['assets']}
    expected_files=[{'id':i,'sha256':assets[i]['sha256'],'bytes':assets[i]['bytes']} for i in ['traces',*clips()]]
    if report['private_files_checked']!=expected_files: raise ValueError('Source file binding differs')
    expected_media={m['id']:media_decision(m) for m in source['media']['records'] if m['id'] in clips()}
    if report['media']!=expected_media: raise ValueError('Media decisions changed')
    if report['calibration_exclusions']!=[{'clip':c,'reason':'declared_calibration_clip'} for c in plan()['calibration_clips']]:
        raise ValueError('Calibration split changed')
    permitted_errors={'oversized_metadata_row','unexpected_header','malformed_row','invalid_clock_field',
        'invalid_playback_clock','insufficient_clock_rows','invalid_csv_encoding_or_syntax',
        'missing_trace_member','oversized_trace_member','linked_trace_member'}
    for row in rows:
        e=row['clock_evidence']
        if row['metadata_error'] is None:
            if not e or not re.fullmatch('[0-9a-f]{64}',row['trace_member_sha256']): raise ValueError('Missing metadata provenance')
            counts=e['crossing_counts']; ages=e['unique_crossing_age_seconds']
            if len(counts)!=60 or len(ages)!=60 or any(type(n) is not int or n<0 for n in counts): raise ValueError('Invalid target counts')
            for n,a in zip(counts,ages):
                if (n==1 and (type(a) not in (int,float) or not 0<=a<float('inf'))) or (n!=1 and a is not None):
                    raise ValueError('Invalid unique-crossing age')
            reasons=reasons_from_evidence(e)
            if not row['independent_clock_check']: raise ValueError('Missing independent check')
            if (not reasons) != bool(row['selected_row_indices_sha256']): raise ValueError('Selected-index binding differs')
            if not reasons and not re.fullmatch('[0-9a-f]{64}',row['selected_row_indices_sha256']):
                raise ValueError('Invalid selected-index digest')
        else:
            if row['metadata_error'] not in permitted_errors or e is not None or row['independent_clock_check']:
                raise ValueError('Invalid metadata failure accounting')
            reasons=[row['metadata_error']]
        if row['clock_reasons']!=reasons or row['clock_qualified']!=(not reasons): raise ValueError('Clock decision differs')
        media=report['media'][row['clip']]
        if row['media_qualified']!=media['qualified'] or row['metadata_qualified']!=((not reasons) and media['qualified']):
            raise ValueError('Combined qualification differs')
        if row['exclusion_reasons']!=reasons+media['reasons']: raise ValueError('Missing exclusion reason')
    if report['clips']!=summarize(rows,report['media']): raise ValueError('Clip roster/pairing differs')
    by_condition=[]
    for e in (1,2):
        selected=[c for c in report['clips'] if c['experiment']==e]
        by_condition.append({'experiment':e,'registered_clips':len(selected),
            'qualified_clips':sum(c['clip_qualified'] for c in selected),
            'directed_pairs':sum(len(c['directed_pairs']) for c in selected)})
    return {'registered_clips':16,'trace_files':len(rows),
        'clock_qualified_traces':sum(r['clock_qualified'] for r in rows),
        'metadata_qualified_traces':sum(r['metadata_qualified'] for r in rows),
        'qualified_clips':sum(c['clip_qualified'] for c in report['clips']),
        'independent_target_checks':60*sum(r['independent_clock_check'] for r in rows),
        'conditions':by_condition,'full_source_ready':False}


def main():
    p=argparse.ArgumentParser(__doc__); p.add_argument('--register',action='store_true')
    p.add_argument('--verify',action='store_true'); p.add_argument('--private-dir',type=Path)
    p.add_argument('--output',type=Path,default=PACKAGE/'results/metadata_v1'); a=p.parse_args()
    if a.register:
        with METHOD.open('xb') as f: f.write(canonical(method_record()))
        print(json.dumps({'method_sha256':digest(method_record()),'batch_started':False})); return
    if json.loads(METHOD.read_text())!=method_record(): raise ValueError('Frozen method changed')
    if a.verify:
        report=json.loads((a.output/'report.json').read_text()); saved=json.loads((a.output/'metadata.json').read_text())
        if saved!={'report_sha256':digest(report),'method_sha256':digest(method_record())}: raise ValueError('Result binding differs')
    else:
        if not a.private_dir: p.error('Private input directory required')
        if a.output.exists(): raise ValueError('Preserve earlier qualification result')
        report=derive(a.private_dir); validate(report); a.output.mkdir(parents=True)
        (a.output/'report.json').write_bytes(canonical(report))
        (a.output/'metadata.json').write_bytes(canonical({'report_sha256':digest(report),'method_sha256':digest(method_record())}))
    print(json.dumps({'sha256':digest(report),**validate(report)}))


if __name__=='__main__': main()
