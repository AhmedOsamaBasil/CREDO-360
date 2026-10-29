"""Clip-guarded source calibration; no quality/recovery or media encoding API."""
import csv
from datetime import datetime
import hashlib
import io
import json
import math
from pathlib import Path
import re
from bisect import bisect_right

import numpy as np
from scipy.optimize import linear_sum_assignment

from wu_source.clocks import HEADER

ROOT=Path(__file__).resolve().parents[1]
PACKAGE=ROOT/'wu_calibration'
CALIBRATION=('e1v02','e2v04')
HALF_TARGETS=tuple(i+.5 for i in range(60))


def plan():
    value=json.loads((PACKAGE/'amendment.json').read_text())
    all_clips={f'e{e}v{v:02}' for e in (1,2) for v in range(1,10)}
    if tuple(value['calibration_clips']) != CALIBRATION: raise ValueError('Calibration split changed')
    remaining=value['confirmation_clips']
    if len(remaining) != 16 or set(remaining) != all_clips-set(CALIBRATION): raise ValueError('Confirmation split changed')
    for key in ('identity_disjoint','service_contract_changed','quality_or_recovery_outcomes_allowed','confirmation_pose_access_allowed'):
        if value[key] is not False: raise ValueError('Calibration scope changed')
    return value


def member(clip,identity):
    plan()
    if clip not in CALIBRATION: raise ValueError('Reserved clip pose access refused')
    if not re.fullmatch(r'[1-9]|[1-3][0-9]|4[0-8]',str(identity)): raise ValueError('Invalid source identity')
    return f'Formated_Data/Experiment_{clip[1]}/{identity}/video_{int(clip[-2:])-1}.csv'


def parse_trace(lines):
    reader=csv.reader(lines,strict=True)
    if next(reader,None) != HEADER: raise ValueError('Trace header changed')
    timestamps=[]; playback=[]; quaternions=[]
    for row in reader:
        if len(row) != 9: raise ValueError('Trace row shape')
        # Calendar dates never leave this reader. Positions are not converted.
        timestamps.append(datetime.fromisoformat(row[0]))
        playback.append(float(row[1])); quaternions.append(tuple(float(v) for v in row[2:6]))
    if not timestamps: raise ValueError('Empty trace')
    wall=np.array([(t-timestamps[0]).total_seconds() for t in timestamps])
    return wall,np.array(playback),np.array(quaternions)


def load_trace(archive,clip,identity):
    name=member(clip,identity)  # Guard runs before the only archive.open call.
    info=archive.getinfo(name)
    if info.file_size > 20_000_000: raise ValueError('Oversized calibration trace')
    with archive.open(name) as raw, io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as text:
        return parse_trace(text)


def forward(q):
    q=np.asarray(q,dtype=float)
    if q.ndim != 2 or q.shape[1] != 4 or not np.isfinite(q).all(): raise ValueError('Invalid quaternion array')
    norms=np.linalg.norm(q,axis=1)
    if np.any(norms == 0) or np.any(np.abs(norms-1) > .01): raise ValueError('Quaternion precision outside declared normalization')
    q=q/norms[:,None]
    x,y,z,w=q.T
    vectors=np.column_stack((2*x*z+2*y*w,2*y*z-2*x*w,1-2*x*x-2*y*y))
    return vectors,float(np.max(np.abs(norms-1)))


def ascending_crossings(playback,target,age=.1):
    t=np.asarray(playback)
    if len(t)<2 or not np.isfinite(t).all() or np.any(t<0): raise ValueError('Invalid playback clock')
    return np.flatnonzero((t[:-1]<target)&(t[1:]>=target)&(t[1:]-target<=age+1e-9))+1


def angular(a,b):
    return np.degrees(np.arccos(np.clip(np.sum(a*b,axis=-1),-1,1)))


def clock_summary(wall,playback,vectors):
    if len(wall)!=len(playback) or len(vectors)!=len(wall): raise ValueError('Row count differs')
    deltas=np.diff(playback); backwards=np.flatnonzero((deltas<0)&((playback[:-1]<=60)|(playback[1:]<=60)))
    multiplicities=[]; sensitivity=[]; first_ages=[]; last_ages=[]; wall_spans=[]
    for target in HALF_TARGETS:
        ix=ascending_crossings(playback,target); multiplicities.append(len(ix))
        if len(ix):
            first_ages.append(float(playback[ix[0]]-target)); last_ages.append(float(playback[ix[-1]]-target))
            sensitivity.append(float(angular(vectors[ix[0]],vectors[ix[-1]])))
            wall_spans.append(float(wall[ix[-1]]-wall[ix[0]]))
    dw=np.diff(wall)
    return {'rows':len(playback),'wall_backward_steps':int(np.sum(dw<0)),
        'wall_duplicate_steps':int(np.sum(dw==0)), 'playback_duplicate_steps':int(np.sum(deltas==0)),
        'playback_backsteps_touching_0_60':len(backwards),
        'backsteps_before_first_target':int(sum(max(playback[i],playback[i+1])<.5 for i in backwards)),
        'backsteps_at_or_after_first_target':int(sum(max(playback[i],playback[i+1])>=.5 for i in backwards)),
        'maximum_playback_backstep_seconds':float(max((-deltas[i] for i in backwards),default=0)),
        'last_backstep_wall_seconds':float(wall[backwards[-1]+1]) if len(backwards) else None,
        'last_backstep_playback_seconds':float(playback[backwards[-1]+1]) if len(backwards) else None,
        'targets_missing':sum(n==0 for n in multiplicities),'targets_unique':sum(n==1 for n in multiplicities),
        'targets_multiple':sum(n>1 for n in multiplicities),'maximum_crossings_per_target':max(multiplicities),
        'first_crossing_max_age_seconds':max(first_ages,default=None),
        'last_crossing_max_age_seconds':max(last_ages,default=None),
        'first_last_max_angular_difference_degrees':max(sensitivity,default=None),
        'first_last_max_wall_span_seconds':max(wall_spans,default=None)}


def load_reference(path):
    spec=plan()['geometry_reference']; raw=path.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if len(raw)!=spec['bytes'] or blob!=spec['git_blob_sha1']: raise ValueError('Author reference identity differs')
    points={}; rows=0; shape_counts={}
    for record in csv.reader(io.StringIO(raw.decode('utf-8-sig'))):
        if len(record)<=10: continue  # Same documented author-renderer rule.
        numbers=np.asarray([float(v) for v in record],dtype=float)
        if not np.isfinite(numbers).all(): raise ValueError('Nonfinite reference')
        coords=numbers[1:]
        if len(coords)%2: raise ValueError('Reference has incomplete coordinate pairs')
        # Renderer stores the last row per truncated decisecond bucket.
        points[int(numbers[0]*10)]=(float(numbers[0]),np.column_stack((coords[1::2]/2,np.abs(coords[0::2]-.5))))
        shape_counts[str(len(coords)//2)]=shape_counts.get(str(len(coords)//2),0)+1; rows+=1
    return points,{'sha256':hashlib.sha256(raw).hexdigest(),'git_blob_sha1':blob,'bytes':len(raw),
        'parsed_rows':rows,'decisecond_buckets':len(points),'point_count_rows':shape_counts}


def candidate_uv(vectors,sign):
    if type(sign) is not int or sign not in (-1,1): raise ValueError('Explicit sign required')
    vectors=np.asarray(vectors)
    return np.column_stack(((sign*np.arctan2(vectors[:,2],vectors[:,0])/(2*math.pi))%1,
                            np.arccos(np.clip(vectors[:,1],-1,1))/math.pi))


def held_reference(points,target):
    keys=sorted(points); index=bisect_right(keys,int(target*10))-1
    return points[keys[index]] if index>=0 else None


def uv_unit(uv):
    uv=np.asarray(uv,dtype=float)
    if uv.ndim!=2 or uv.shape[1]!=2 or not np.isfinite(uv).all() or np.any(uv<0) or np.any(uv>1):
        raise ValueError('Reference outside normalized texture')
    longitude=2*math.pi*uv[:,0]; latitude=math.pi*(.5-uv[:,1])
    return np.column_stack((np.cos(latitude)*np.cos(longitude),np.sin(latitude),np.cos(latitude)*np.sin(longitude)))


def match_points(predicted_uv,reference_uv):
    a,b=uv_unit(predicted_uv),uv_unit(reference_uv)
    if len(a)!=len(b) or not len(a): raise ValueError('Equal nonempty point sets required')
    distances=np.degrees(np.arccos(np.clip(a@b.T,-1,1)))
    rows,columns=linear_sum_assignment(distances)
    return distances[rows,columns]


def error_summary(errors):
    a=np.asarray(errors)
    return {'points':len(a),'median_degrees':float(np.median(a)),
        'p95_degrees':float(np.quantile(a,.95)), 'maximum_degrees':float(np.max(a)),
        'mean_degrees':float(np.mean(a))}


def mapping_gate(cells):
    pooled=[]
    for sign in (-1,1):
        for choice in ('first','last'):
            selected=[c for c in cells if c['wrap_sign']==sign and c['crossing']==choice]
            valid=len(selected)==5 and all(c.get('points')==48 and 'errors_degrees' in c for c in selected)
            pooled.append({'wrap_sign':sign,'crossing':choice,'complete':valid,
                **(error_summary([e for c in selected for e in c['errors_degrees']]) if valid else {})})
    accepted=[]
    for sign in (-1,1):
        good=any(c['complete'] and c.get('median_degrees',float('inf'))<=.5 and c.get('p95_degrees',float('inf'))<=2 for c in pooled if c['wrap_sign']==sign)
        alternatives=[c for c in pooled if c['wrap_sign']==-sign]
        bad=all(c['complete'] and c.get('median_degrees',0)>=5 for c in alternatives)
        if good and bad: accepted.append(sign)
    return {'pooled':pooled,'supported_sign':accepted[0] if len(accepted)==1 else None,
        'automatic_outcome_launch':False,'production_clock_adapter_frozen':False}
