"""Roster-guarded selected-pose intake and independent geometry validation."""
import csv
import hashlib
import io
import json
import math
from pathlib import Path
import numpy as np

from wu_source.acquire import canonical
from wu_qualification.core import member,parse_clocks,qualify_clock
from wu_qualification.run import (validate as validate_parent,method_record as parent_method,
    METHOD as PARENT_METHOD,digest)
from wu_calibration.adapter import select_indices
from wu_calibration.core import forward,candidate_uv
from wu_calibration.check_adapter import hamilton,scalar_yaw_pitch,scalar_weights
from multimedia_testbed.prepare_qoevave import viewport_weights

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'wu_pose'
PARENT=ROOT/'wu_qualification/results/metadata_v1/report.json'
PARENT_SHA='58007f8a9264dd8318efc58bc41cd5687c0d89500ccfbc4af4d505cd1dadf6d2'
REASONS=('nonnumeric_quaternion','nonfinite_quaternion','zero_quaternion','quaternion_norm_out_of_tolerance')


def load_roster():
    if json.loads(PARENT_METHOD.read_text())!=parent_method(): raise ValueError('Parent method changed')
    report=json.loads(PARENT.read_text())
    if digest(report)!=PARENT_SHA: raise ValueError('Qualified roster changed')
    validate_parent(report)
    return report


def guard(records,clip,identity):
    record=records.get((clip,identity))
    if record is None or not record['metadata_qualified']:
        raise ValueError('Pose access outside qualified roster')
    return record


def selected_fields(raw,indices):
    """Read xyzw at selected data-row indices only; all other values stay opaque."""
    chosen=set(indices)
    if len(indices)!=60 or len(chosen)!=60 or indices!=sorted(indices) or min(indices)<0:
        raise ValueError('Selected row shape changed')
    result=[]
    reader=csv.reader(io.StringIO(raw.decode('utf-8-sig'),newline=''),strict=True)
    next(reader)
    for i,row in enumerate(reader):
        if i in chosen: result.append(row[2:6])
    if len(result)!=60 or any(len(q)!=4 for q in result): raise ValueError('Selected row count changed')
    return result


def load_selected(archive,records,clip,identity):
    record=guard(records,clip,identity)  # Guard before even getinfo/read.
    name=member(clip,identity); info=archive.getinfo(name)
    if info.file_size>20_000_000 or (info.external_attr>>16)&0o170000==0o120000:
        raise ValueError('Unexpected source member')
    raw=archive.read(name)
    if hashlib.sha256(raw).hexdigest()!=record['trace_member_sha256']:
        raise ValueError('Source member binding differs')
    wall,t= parse_clocks(raw); check=qualify_clock(wall,t)
    if any(record[k]!=v for k,v in check.items()): raise ValueError('Clock metadata differs')
    selected=select_indices(wall,t)
    if not selected['accepted'] or digest(selected['indices'])!=record['selected_row_indices_sha256']:
        raise ValueError('Frozen selected indices differ')
    return selected_fields(raw,selected['indices'])


def quaternion_checks(fields):
    counts={r:0 for r in REASONS}; valid=[]; max_error=None
    for fields_q in fields:
        try: q=[float(v) for v in fields_q]
        except (ValueError,TypeError,OverflowError):
            counts['nonnumeric_quaternion']+=1; continue
        if len(q)!=4: raise ValueError('Quaternion shape')
        if not all(math.isfinite(v) for v in q):
            counts['nonfinite_quaternion']+=1; continue
        with np.errstate(over='ignore',invalid='ignore'):
            norm=float(np.linalg.norm(q))
        if norm==0: counts['zero_quaternion']+=1; continue
        if not math.isfinite(norm) or abs(norm-1)>.01:
            counts['quaternion_norm_out_of_tolerance']+=1; continue
        error=abs(norm-1); max_error=error if max_error is None else max(error,max_error)
        valid.append(q)
    return {'selected_samples':len(fields),'invalid_samples':sum(counts.values()),
        'invalid_reason_counts':counts,'maximum_valid_selected_norm_error':max_error},valid


def scalar_vector(q):
    length=math.sqrt(sum(v*v for v in q)); x,y,z,w=(v/length for v in q)
    return hamilton(hamilton((w,x,y,z),(0,0,0,1)),(w,-x,-y,-z))[1:]


def project_selected(fields):
    if len(fields)!=60: raise ValueError('Exactly sixty selected samples required')
    checks,q=quaternion_checks(fields)
    if checks['invalid_samples']:
        return {'accepted':False,'reasons':[k for k,v in checks['invalid_reason_counts'].items() if v],
            'quaternion':checks,'geometry':None},None
    vectors,norm_error=forward(q); uv=candidate_uv(vectors,-1)
    pose=np.column_stack((360*uv[:,0]-180,90-180*uv[:,1]))
    if abs(norm_error-checks['maximum_valid_selected_norm_error'])>1e-12:
        raise ValueError('Normalization check mismatch')
    errors={'maximum_vector_component_error':0.,'maximum_circular_yaw_error_degrees':0.,
        'maximum_pitch_error_degrees':0.,'maximum_viewport_weight_error':0.}
    for quaternion,vector,angles in zip(q,vectors,pose):
        direct=scalar_vector(quaternion); yaw,pitch=scalar_yaw_pitch(quaternion)
        ve=max(abs(a-b) for a,b in zip(vector,direct))
        ye=abs((yaw-angles[0]+180)%360-180); pe=abs(pitch-angles[1])
        primary=viewport_weights(*angles); independent=np.asarray(scalar_weights(yaw,pitch))
        we=float(np.max(np.abs(primary-independent)))
        if ve>1e-12 or ye>1e-10 or pe>1e-10 or we>1e-12 or not np.array_equal(primary>0,independent>0):
            raise ValueError('Independent geometry mismatch')
        for key,value in zip(errors,(ve,ye,pe,we)): errors[key]=max(errors[key],float(value))
    return {'accepted':True,'reasons':[],'quaternion':checks,
        'geometry':{'samples_checked':60,'tile_membership_exact':True,**errors}},pose


def summarize(parent,rows):
    lookup={(r['clip'],r['source_id']):r for r in rows}; clips=[]
    for previous in parent['clips']:
        clip=previous['clip']; pairs=[]
        for recipient,donor in previous['directed_pairs']:
            failed=[i for i in (recipient,donor) if not lookup[clip,i]['pose_validated']]
            pairs.append({'recipient':recipient,'donor':donor,'usable':not failed,
                'failed_source_ids':failed})
        passed=[r['source_id'] for r in rows if r['clip']==clip and r['pose_validated']]
        clips.append({'clip':clip,'experiment':previous['experiment'],'condition':previous['condition'],
            'metadata_clip_qualified':previous['clip_qualified'],
            'parent_clip_exclusion_reasons':previous['clip_reasons'],
            'pose_validated_source_ids':sorted(passed),'candidate_pairs':pairs,
            'usable_pairs':sum(p['usable'] for p in pairs)})
    return clips
