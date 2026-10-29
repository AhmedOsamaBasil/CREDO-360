"""Conservative recorded-sample adapter; ambiguous clocks return no pose series."""
import hashlib
import json
import numpy as np
from wu_source.acquire import canonical
from .core import PACKAGE,HALF_TARGETS,ascending_crossings,forward,candidate_uv,load_trace


def validate_spec():
    spec=json.loads((PACKAGE/'adapter_spec.json').read_text())
    report=json.loads((PACKAGE/'results/calibration_v1/report.json').read_text())
    if hashlib.sha256(canonical(report)).hexdigest()!=spec['calibration_report_sha256']:
        raise ValueError('Calibration evidence changed')
    if report['geometry_gate']['supported_sign']!=-1 or spec['texture']['wrap_sign']!=-1:
        raise ValueError('Unsupported texture mapping')
    if spec['confirmation_pose_access_enabled_in_this_package'] or spec['automatic_outcome_launch']:
        raise ValueError('Unapproved confirmation access')
    return spec


def select_indices(wall,playback):
    wall=np.asarray(wall,dtype=float); playback=np.asarray(playback,dtype=float)
    if wall.ndim!=1 or playback.ndim!=1 or len(wall)!=len(playback) or len(wall)<2:
        raise ValueError('Clock arrays must have matching rows')
    if not np.isfinite(wall).all() or np.any(wall<0) or np.any(np.diff(wall)<0):
        return {'accepted':False,'reasons':['invalid_or_backward_wall_clock'],'indices':[],'ambiguous_targets':[],'missing_targets':[]}
    if not np.isfinite(playback).all() or np.any(playback<0): raise ValueError('Invalid playback clock')
    missing=[]; ambiguous=[]; stale=[]; indices=[]
    for t in HALF_TARGETS:
        # Count all chronological crossings first, so an old repeated crossing
        # cannot disappear merely because its next sample missed the age limit.
        ix=np.flatnonzero((playback[:-1]<t)&(playback[1:]>=t))+1
        if len(ix)==0: missing.append(t)
        elif len(ix)>1: ambiguous.append(t)
        elif playback[ix[0]]-t>.1+1e-9: stale.append(t)
        else: indices.append(int(ix[0]))
    reasons=(['missing_target_crossing'] if missing else [])+(['ambiguous_target_crossing'] if ambiguous else [])+(['stale_target_crossing'] if stale else [])
    if playback[0]>.5: reasons.append('missing_initial_bracket')
    if np.max(playback)<60: reasons.append('missing_60s_coverage')
    return {'accepted':not reasons,'reasons':reasons,'indices':indices if not reasons else [],
        'ambiguous_targets':ambiguous,'missing_targets':missing,'stale_targets':stale}


def adapt_arrays(wall,playback,q):
    selected=select_indices(wall,playback)
    if not selected['accepted']: return selected,None
    q=np.asarray(q,dtype=float)
    if q.shape!=(len(playback),4): raise ValueError('Quaternion row count differs')
    vectors,norm_error=forward(q[selected['indices']])
    uv=candidate_uv(vectors,-1)
    yaw_pitch=np.column_stack((360*uv[:,0]-180,90-180*uv[:,1]))
    selected['maximum_selected_norm_error']=norm_error
    selected['maximum_sample_age_seconds']=float(max(np.asarray(playback)[selected['indices']]-HALF_TARGETS))
    return selected,yaw_pitch


def adapt_calibration_trace(archive,clip,identity):
    validate_spec()
    return adapt_arrays(*load_trace(archive,clip,identity))
