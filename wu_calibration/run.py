"""Derive calibration-only scalar diagnostics from guarded private sources."""
import argparse
import hashlib
import json
from pathlib import Path
import zipfile

from wu_source.acquire import canonical,sha256
from .core import (ROOT,PACKAGE,CALIBRATION,plan,load_trace,forward,clock_summary,
    ascending_crossings,load_reference,candidate_uv,match_points,error_summary,mapping_gate,held_reference)


def derive(archive,reference):
    frozen=json.loads((ROOT/'wu_source/results/source_v1/report.json').read_text())
    expected=next(a['sha256'] for a in frozen['assets'] if a['id']=='traces')
    if sha256(archive)!=expected: raise ValueError('Private archive hash differs')
    p=plan(); points,provenance=load_reference(reference)
    geometry=p['geometry_reference']; targets=geometry['targets_seconds']; sets={}
    rows=[]
    with zipfile.ZipFile(archive) as z:
        for clip in CALIBRATION:
            for identity in map(str,range(1,49)):
                wall,t,q=load_trace(z,clip,identity); vectors,norm_error=forward(q)
                rows.append({'clip':clip,'source_id':identity,'maximum_quaternion_norm_error':norm_error,
                    **clock_summary(wall,t,vectors)})
                if clip=='e2v04':
                    for target in targets:
                        reference_row=held_reference(points,target)
                        ix=ascending_crossings(t,reference_row[0]) if reference_row else []
                        for choice,index in [('first',ix[0] if len(ix) else None),('last',ix[-1] if len(ix) else None)]:
                            sets.setdefault((target,choice),[])
                            if index is not None: sets[target,choice].append(vectors[index])
            print(json.dumps({'clip':clip,'traces':48,'quality_outcomes_derived':False}),flush=True)
    cells=[]
    for target in targets:
        ref=held_reference(points,target)
        for choice in ('first','last'):
            vectors=sets[target,choice]
            for sign in (-1,1):
                cell={'target_seconds':target,'crossing':choice,'wrap_sign':sign,
                    'source_points':len(vectors),'reference_points':len(ref[1]) if ref else 0,
                    'reference_time_seconds':ref[0] if ref else None}
                cell['target_minus_reference_seconds']=target-ref[0] if ref else None
                if ref and len(vectors)==48 and len(ref[1])==48:
                    errors=match_points(candidate_uv(vectors,sign),ref[1])
                    cell.update(error_summary(errors)); cell['errors_degrees']=sorted(float(e) for e in errors)
                else: cell['failure']='missing or unequal point count'
                cells.append(cell)
    return {'schema':'wu-two-clip-calibration-v1','amendment_sha256':hashlib.sha256(canonical(p)).hexdigest(),
        'source_archive_sha256':expected,'reference':provenance,'clock_rows':rows,'geometry_cells':cells,
        'geometry_gate':mapping_gate(cells),'calibration_clips':list(CALIBRATION),
        'confirmation_clips_accessed':[],'quality_outcomes_derived':False,'recovery_outcomes_derived':False,
        'production_adapter_frozen':False}


def bindings():
    paths=['wu_calibration/'+p for p in ('amendment.json','PROTOCOL.md','reference_alignment.json','core.py','run.py')]
    paths+=['wu_source/results/source_v1/metadata.json','confirmation_protocol/results/design_v1/metadata.json']
    return {p:hashlib.sha256((ROOT/p).read_text(encoding='utf-8').replace('\r\n','\n').encode()).hexdigest() for p in paths}


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--archive',type=Path); parser.add_argument('--reference',type=Path)
    parser.add_argument('--output',type=Path,default=PACKAGE/'results/calibration_v1'); parser.add_argument('--verify',action='store_true')
    args=parser.parse_args()
    if args.verify:
        result=json.loads((args.output/'report.json').read_text()); metadata=json.loads((args.output/'metadata.json').read_text())
        if metadata!={'sha256':hashlib.sha256(canonical(result)).hexdigest(),'bindings':bindings()}: raise ValueError('Report binding differs')
        if result['geometry_gate']!=mapping_gate(result['geometry_cells']): raise ValueError('Mapping gate differs')
        if result['confirmation_clips_accessed'] or result['quality_outcomes_derived'] or result['recovery_outcomes_derived'] or result['production_adapter_frozen']:
            raise ValueError('Calibration claim scope changed')
    else:
        if args.output.exists(): raise ValueError('Preserve earlier calibration artifact')
        if not args.archive or not args.reference: parser.error('Private inputs required')
        result=derive(args.archive,args.reference)
        args.output.mkdir(parents=True)
        (args.output/'report.json').write_bytes(canonical(result))
        (args.output/'metadata.json').write_bytes(canonical({'sha256':hashlib.sha256(canonical(result)).hexdigest(),'bindings':bindings()}))
    print(json.dumps({'sha256':hashlib.sha256(canonical(result)).hexdigest(),'traces':len(result['clock_rows']),
        'geometry':result['geometry_gate'],'confirmation_accessed':result['confirmation_clips_accessed']}))


if __name__=='__main__': main()
