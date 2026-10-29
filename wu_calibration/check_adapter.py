"""Independent scalar accounting of the conservative adapter on calibration only."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import zipfile
import numpy as np

from wu_source.acquire import canonical,sha256
from multimedia_testbed.prepare_qoevave import viewport_weights
from .core import ROOT,PACKAGE,CALIBRATION,HALF_TARGETS,load_trace
from .adapter import adapt_arrays,validate_spec


def scalar_select(wall,playback):
    if len(wall)!=len(playback) or len(wall)<2: raise ValueError('Clock shape')
    bad_wall=any(not math.isfinite(v) or v<0 for v in wall) or any(b<a for a,b in zip(wall,wall[1:]))
    if bad_wall: return False,[]
    if any(not math.isfinite(v) or v<0 for v in playback): raise ValueError('Invalid playback')
    chosen=[]; good=playback[0]<=.5 and max(playback)>=60
    for target in HALF_TARGETS:
        crossings=[]
        for i in range(1,len(playback)):
            if playback[i-1]<target<=playback[i]: crossings.append(i)
        if len(crossings)!=1 or playback[crossings[0]]-target>.1+1e-9: good=False
        else: chosen.append(crossings[0])
    return good,chosen if good else []


def hamilton(a,b):
    w,x,y,z=a; W,X,Y,Z=b
    return (w*W-x*X-y*Y-z*Z,w*X+x*W+y*Z-z*Y,w*Y-x*Z+y*W+z*X,w*Z+x*Y-y*X+z*W)


def scalar_yaw_pitch(q):
    norm=math.sqrt(sum(v*v for v in q)); x,y,z,w=(v/norm for v in q)
    _,X,Y,Z=hamilton(hamilton((w,x,y,z),(0,0,0,1)),(w,-x,-y,-z))
    return 360*((-math.atan2(Z,X)/(2*math.pi))%1)-180,math.degrees(math.asin(max(-1,min(1,Y))))


def scalar_weights(yaw,pitch):
    result=[]
    for r in range(6):
        p=75-30*r; row=[]
        for c in range(12):
            y=-165+30*c; distance=abs((y-yaw+180)%360-180)
            row.append(math.cos(math.radians(p)) if distance<=50 and abs(p-pitch)<=50 else 0)
        result.append(row)
    total=sum(sum(row) for row in result)
    if not total: raise ValueError('Empty angular viewport')
    return [[v/total for v in row] for row in result]


def derive(archive):
    spec=validate_spec(); source=json.loads((PACKAGE/'results/calibration_v1/report.json').read_text())
    if sha256(archive)!=source['source_archive_sha256']: raise ValueError('Archive binding')
    rows=[]; samples=0
    with zipfile.ZipFile(archive) as z:
        for clip in CALIBRATION:
            for identity in map(str,range(1,49)):
                wall,t,q=load_trace(z,clip,identity); status,poses=adapt_arrays(wall,t,q)
                accepted,indices=scalar_select(wall.tolist(),t.tolist())
                if accepted!=status['accepted'] or indices!=status['indices']: raise ValueError('Independent crossing mismatch')
                if accepted:
                    for i,pose in zip(indices,poses):
                        yaw,pitch=scalar_yaw_pitch(q[i])
                        yaw_error=abs((yaw-pose[0]+180)%360-180)
                        if yaw_error>1e-10 or abs(pitch-pose[1])>1e-10: raise ValueError('Independent projection mismatch')
                        if not np.allclose(viewport_weights(*pose),scalar_weights(yaw,pitch),atol=1e-12,rtol=0):
                            raise ValueError('Original angular viewport changed')
                        samples+=1
                rows.append({'clip':clip,'source_id':identity,'accepted':accepted,'reasons':status['reasons'],
                    'ambiguous_targets':status['ambiguous_targets'],'missing_targets':status['missing_targets'],
                    'stale_targets':status.get('stale_targets',[]),'independent_indices_match':True})
    return {'schema':'wu-conservative-adapter-calibration-check-v1',
        'spec_sha256':hashlib.sha256(canonical(spec)).hexdigest(),
        'calibration_report_sha256':spec['calibration_report_sha256'],
        'source_archive_sha256':source['source_archive_sha256'],'rows':rows,
        'independent_clock_queries':len(rows)*60,'independent_projection_samples':samples,
        'independent_legacy_viewport_samples':samples,'projection_tolerance_degrees':1e-10,
        'viewport_weight_tolerance':1e-12,'confirmation_pose_files_opened':0,
        'quality_outcomes_derived':False,'full_source_qualification_complete':False}


def bindings():
    files=['adapter.py','adapter_spec.json','check_adapter.py','core.py','amendment.json','reference_alignment.json']
    result={f'wu_calibration/{p}':hashlib.sha256((PACKAGE/p).read_text().replace('\r\n','\n').encode()).hexdigest() for p in files}
    p='multimedia_testbed/prepare_qoevave.py'; result[p]=hashlib.sha256((ROOT/p).read_text().replace('\r\n','\n').encode()).hexdigest()
    return result


def main():
    p=argparse.ArgumentParser(__doc__); p.add_argument('--archive',type=Path)
    p.add_argument('--output',type=Path,default=PACKAGE/'results/adapter_v1'); p.add_argument('--verify',action='store_true')
    a=p.parse_args()
    if a.verify:
        r=json.loads((a.output/'report.json').read_text()); m=json.loads((a.output/'metadata.json').read_text())
        if m!={'sha256':hashlib.sha256(canonical(r)).hexdigest(),'bindings':bindings()}: raise ValueError('Adapter artifact binding')
    else:
        if not a.archive: p.error('Private archive required')
        if a.output.exists(): raise ValueError('Preserve earlier adapter check')
        r=derive(a.archive); a.output.mkdir(parents=True)
        (a.output/'report.json').write_bytes(canonical(r))
        (a.output/'metadata.json').write_bytes(canonical({'sha256':hashlib.sha256(canonical(r)).hexdigest(),'bindings':bindings()}))
    print(json.dumps({'sha256':hashlib.sha256(canonical(r)).hexdigest(),
        'accepted_by_clip':{c:sum(x['accepted'] for x in r['rows'] if x['clip']==c) for c in CALIBRATION},
        'scalar_clock_queries':r['independent_clock_queries'],'projection_samples':r['independent_projection_samples']}))


if __name__=='__main__': main()
