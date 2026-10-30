"""Freeze, derive and verify sampled-pose source validation, without outcomes."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import zipfile

from wu_source.acquire import canonical,sha256
from wu_qualification.core import validate_archive_directory
from wu_qualification.run import method_bindings as parent_bindings
from .core import (ROOT,PACKAGE,PARENT_SHA,REASONS,load_roster,load_selected,
    project_selected,summarize,digest)

METHOD=PACKAGE/'method_v1.json'
DEFAULT=PACKAGE/'results/validation_v1'
SCOPE={'selected_pose_validation_performed':True,'quality_outcomes_derived':False,
    'recovery_outcomes_derived':False,'automatic_outcome_launch':False,
    'full_experiment_ready':False,'physical_display_validated':False,
    'identity_disjoint':False,'demographics_accessed':False,'positions_interpreted':False}


def method_record():
    bindings=parent_bindings()
    paths=['wu_pose/'+s for s in ('PROTOCOL.md','core.py','run.py','replication.py','test_core.py')]
    paths+=['wu_qualification/method_v1.json','wu_qualification/results/metadata_v1/report.json',
        'wu_qualification/results/metadata_v1/metadata.json','wu_calibration/check_adapter.py',
        'multimedia_testbed/prepare_qoevave.py']
    for path in paths:
        bindings[path]=hashlib.sha256((ROOT/path).read_text(encoding='utf-8').replace('\r\n','\n').encode()).hexdigest()
    return {'schema':'wu-qualified-pose-method-v1','parent_roster_sha256':PARENT_SHA,
        'bindings':bindings,'quaternion_order':'xyzw','maximum_norm_error':.01,'wrap_sign':-1,
        'target_seconds':[i+.5 for i in range(60)],'projection_tolerance_degrees':1e-10,
        'vector_component_tolerance':1e-12,'viewport_weight_tolerance':1e-12,
        'cross_platform_summary_absolute_tolerance':1e-10,
        'pair_policy':'retain_original_directed_pairs_no_repairing',
        'access':'selected_samples_of_metadata_qualified_traces_only',
        'quality_outcomes_allowed':False,'recovery_outcomes_allowed':False}


def check_method():
    if json.loads(METHOD.read_text())!=method_record(): raise ValueError('Frozen pose method changed')


def derive(private,progress):
    check_method(); parent=load_roster(); checked=parent['private_files_checked']
    for asset in checked:
        path=private/('vr-dataset.zip' if asset['id']=='traces' else asset['id']+'.mp4')
        if path.stat().st_size!=asset['bytes'] or sha256(path)!=asset['sha256']:
            raise ValueError('Private original binding differs')
    records={(r['clip'],r['source_id']):r for r in parent['rows']}; rows=[]
    with zipfile.ZipFile(private/'vr-dataset.zip') as archive:
        validate_archive_directory(archive)
        for record in parent['rows']:
            row={'clip':record['clip'],'source_id':record['source_id'],
                'trace_member_sha256':record['trace_member_sha256'],
                'selected_row_indices_sha256':record['selected_row_indices_sha256'],
                'metadata_qualified':record['metadata_qualified'],
                'parent_exclusion_reasons':record['exclusion_reasons']}
            if record['metadata_qualified']:
                fields=load_selected(archive,records,record['clip'],record['source_id'])
                result,_=project_selected(fields)
                row.update(pose_accessed=True,pose_validated=result['accepted'],
                    pose_failure_reasons=result['reasons'],quaternion=result['quaternion'],geometry=result['geometry'])
            else:
                row.update(pose_accessed=False,pose_validated=False,pose_failure_reasons=[],
                    quaternion=None,geometry=None)
            rows.append(row)
            if record['source_id']=='48':
                status={'clip':record['clip'],'registered':48,
                    'pose_accessed':sum(r['pose_accessed'] for r in rows if r['clip']==record['clip']),
                    'pose_validated':sum(r['pose_validated'] for r in rows if r['clip']==record['clip'])}
                progress(status); print(json.dumps(status),flush=True)
    return {'schema':'wu-qualified-pose-validation-v1','state':'sampled_pose_validation_complete',
        'method_sha256':digest(method_record()),'parent_roster_sha256':PARENT_SHA,
        'private_files_checked':checked,'calibration_exclusions':parent['calibration_exclusions'],
        'rows':rows,'clips':summarize(parent,rows),'scope':SCOPE.copy()}


def finite(value,low=0,high=float('inf')):
    return type(value) in (int,float) and math.isfinite(value) and low<=value<=high


def validate(report):
    check_method(); parent=load_roster()
    if report['schema']!='wu-qualified-pose-validation-v1' or report['state']!='sampled_pose_validation_complete':
        raise ValueError('Validation status differs')
    if report['scope']!=SCOPE: raise ValueError('Unsupported scope')
    if report['method_sha256']!=digest(method_record()) or report['parent_roster_sha256']!=PARENT_SHA:
        raise ValueError('Method/roster binding differs')
    if report['private_files_checked']!=parent['private_files_checked'] or report['calibration_exclusions']!=parent['calibration_exclusions']:
        raise ValueError('Source/split binding differs')
    rows=report['rows']
    if len(rows)!=len(parent['rows']): raise ValueError('Incomplete source census')
    row_keys={'clip','source_id','trace_member_sha256','selected_row_indices_sha256',
        'metadata_qualified','parent_exclusion_reasons','pose_accessed','pose_validated',
        'pose_failure_reasons','quaternion','geometry'}
    for row,old in zip(rows,parent['rows']):
        if set(row)!=row_keys: raise ValueError('Unexpected public row fields')
        for key in ('clip','source_id','trace_member_sha256','selected_row_indices_sha256','metadata_qualified'):
            if row[key]!=old[key]: raise ValueError('Parent roster changed')
        if row['parent_exclusion_reasons']!=old['exclusion_reasons']: raise ValueError('Exclusion lost')
        if row['pose_accessed'] is not old['metadata_qualified']: raise ValueError('Access scope differs')
        if not old['metadata_qualified']:
            if row['pose_validated'] is not False or row['pose_failure_reasons'] or row['quaternion'] is not None or row['geometry'] is not None:
                raise ValueError('Excluded pose interpreted')
            continue
        q=row['quaternion']
        if set(q)!={'selected_samples','invalid_samples','invalid_reason_counts','maximum_valid_selected_norm_error'}:
            raise ValueError('Unexpected quaternion summary')
        counts=q['invalid_reason_counts']
        if set(counts)!=set(REASONS) or any(type(v) is not int or v<0 for v in counts.values()):
            raise ValueError('Invalid reason counts')
        invalid=sum(counts.values()); error=q['maximum_valid_selected_norm_error']
        if q['selected_samples']!=60 or invalid>60 or q['invalid_samples']!=invalid:
            raise ValueError('Invalid selected sample census')
        if (invalid<60 and not finite(error,0,.01)) or (invalid==60 and error is not None):
            raise ValueError('Invalid norm summary')
        if row['pose_validated'] is not (invalid==0) or row['pose_failure_reasons']!=[r for r in REASONS if counts[r]]:
            raise ValueError('Quaternion decision differs')
        geometry=row['geometry']
        if invalid:
            if geometry is not None: raise ValueError('Partial invalid pose geometry')
        else:
            limits={'maximum_vector_component_error':1e-12,'maximum_circular_yaw_error_degrees':1e-10,
                'maximum_pitch_error_degrees':1e-10,'maximum_viewport_weight_error':1e-12}
            if set(geometry)!=set(limits)|{'samples_checked','tile_membership_exact'}:
                raise ValueError('Unexpected geometry summary')
            if geometry['samples_checked']!=60 or geometry['tile_membership_exact'] is not True:
                raise ValueError('Incomplete geometry checks')
            if any(not finite(geometry[k],0,v) for k,v in limits.items()):
                raise ValueError('Independent geometry tolerance exceeded')
    if report['clips']!=summarize(parent,rows): raise ValueError('Pair roster changed')
    conditions=[]
    for experiment in (1,2):
        selected=[c for c in report['clips'] if c['experiment']==experiment]
        conditions.append({'experiment':experiment,'registered_clips':len(selected),
            'clips_with_usable_pairs':sum(c['usable_pairs']>0 for c in selected),
            'candidate_pairs':sum(len(c['candidate_pairs']) for c in selected),
            'usable_pairs':sum(c['usable_pairs'] for c in selected)})
    return {'registered_traces':len(rows),'accessed_pose_traces':sum(r['pose_accessed'] for r in rows),
        'validated_pose_traces':sum(r['pose_validated'] for r in rows),
        'selected_samples_checked':60*sum(r['pose_accessed'] for r in rows),
        'geometry_samples_checked':60*sum(r['pose_validated'] for r in rows),
        'pose_failed_traces':sum(r['pose_accessed'] and not r['pose_validated'] for r in rows),
        'conditions':conditions,'full_experiment_ready':False}


def read_artifact(directory):
    report=json.loads((directory/'report.json').read_text())
    metadata=json.loads((directory/'metadata.json').read_text())
    if metadata!={'report_sha256':digest(report),'method_sha256':digest(method_record())}:
        raise ValueError('Artifact binding differs')
    validate(report); return report


def main():
    p=argparse.ArgumentParser(__doc__); p.add_argument('--register',action='store_true')
    p.add_argument('--verify',action='store_true'); p.add_argument('--private-dir',type=Path)
    p.add_argument('--output',type=Path,default=DEFAULT); a=p.parse_args()
    if a.register:
        load_roster()
        with METHOD.open('xb') as f: f.write(canonical(method_record()))
        print(json.dumps({'method_sha256':digest(method_record()),'poses_accessed':0})); return
    check_method()
    if a.verify: report=read_artifact(a.output)
    else:
        if not a.private_dir: p.error('Private original-assets directory required')
        if a.output.exists(): raise ValueError('Preserve earlier validation attempt')
        a.output.mkdir(parents=True)
        try:
            with (a.output/'progress.jsonl').open('xb') as stream:
                def progress(value): stream.write(canonical(value)+b'\n'); stream.flush()
                report=derive(a.private_dir,progress)
            validate(report)
            (a.output/'report.json').write_bytes(canonical(report))
            (a.output/'metadata.json').write_bytes(canonical({'report_sha256':digest(report),
                'method_sha256':digest(method_record())}))
        except Exception as error:
            failure={'state':'validation_failed','exception_type':type(error).__name__,
                'reason':'source_integrity_or_independent_validation_failed',
                'method_sha256':digest(method_record()),'automatic_outcome_launch':False}
            (a.output/'failure.json').write_bytes(canonical(failure))
            raise SystemExit('Validation halted; failure and completed progress retained') from None
    print(json.dumps({'sha256':digest(report),**validate(report)}))


if __name__=='__main__': main()
