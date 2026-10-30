"""Generated-pattern runtime smoke; no Wu media, poses or quality outcomes."""
import argparse
import json
from pathlib import Path
import numpy as np
from wu_source.acquire import canonical,sha256
from .media import (call,encode_command,describe,split_verified,phase_check,sample_frames,fingerprint)
from .metrics import mse_map
from .spec import PACKAGE,bindings,digest,RUNTIME


def derive(directory):
    if fingerprint()!=json.loads(RUNTIME.read_text()): raise ValueError('Smoke runtime differs')
    if directory.exists(): raise ValueError('Preserve synthetic attempt')
    directory.mkdir(parents=True)
    rates=('16','25','30','30000/1001'); phases=[]
    for rate in rates:
        generator=f'testsrc2=size=64x32:rate={rate}:duration=60'
        phases.append({'rate':rate,**phase_check(generator,60,lavfi=True)})
    source=directory/'generated_source.mkv'
    call(['ffmpeg','-nostdin','-v','error','-n','-f','lavfi','-i',
        'testsrc2=size=320x160:rate=25:duration=10','-an','-c:v','ffv1',source])
    target=directory/'r2.mp4'; call(encode_command(source,target,2,10))
    record,_,_=describe(target,10,directory)
    parent=split_verified(target,directory/'parents',10,10,directory)[0]
    children=split_verified(directory/parent['relative_path'],directory/'children',2,10,directory)
    reference=sample_frames(source,10); distorted=sample_frames(target,10)
    maps=mse_map(reference,distorted,10)
    if maps.shape!=(10,6,12) or not np.isfinite(maps).all(): raise ValueError('Synthetic metric shape')
    return {'schema':'wu-pipeline-synthetic-smoke-v1','synthetic_only':True,
        'wu_media_accessed':False,'wu_poses_accessed':False,'fresh_research_outcomes':False,
        'runtime':fingerprint(),'phase_checks':phases,'synthetic_source_sha256':sha256(source),
        'rendition':record,'parent':parent,'children':children,'sampled_gray_frames':10,
        'tile_map_shape':list(maps.shape),'legacy_tile_mse_shape_checked':True,
        'encoded_rungs_exercised':[2],'full_sixty_second_six_rung_campaign_executed':False}


def verify_report(report):
    if report['schema']!='wu-pipeline-synthetic-smoke-v1' or report['synthetic_only'] is not True:
        raise ValueError('Not synthetic smoke')
    if any(report[k] is not False for k in ('wu_media_accessed','wu_poses_accessed','fresh_research_outcomes','full_sixty_second_six_rung_campaign_executed')):
        raise ValueError('Smoke scope changed')
    if report['runtime']!=json.loads(RUNTIME.read_text()): raise ValueError('Saved runtime differs')
    if len(report['children'])!=5 or report['sampled_gray_frames']!=10 or report['tile_map_shape']!=[10,6,12]:
        raise ValueError('Smoke census changed')
    if [p['rate'] for p in report['phase_checks']]!=['16','25','30','30000/1001']:
        raise ValueError('Phase census changed')
    for p in report['phase_checks']:
        if p['samples']!=60 or p['changes_primary_sampler'] is not False or p['proves_same_source_frame_identity'] is not False:
            raise ValueError('Unsupported phase claim')
    return {'synthetic_only':True,'phase_different_bins':{p['rate']:p['different_sample_bins'] for p in report['phase_checks']},
        'served_parent_bytes':report['parent']['bytes'],'served_children_bytes':sum(c['bytes'] for c in report['children']),
        'fresh_research_outcomes':False}


def main():
    p=argparse.ArgumentParser(__doc__); p.add_argument('--output',type=Path)
    p.add_argument('--verify',action='store_true'); a=p.parse_args()
    public=PACKAGE/'results/synthetic_v1'
    if a.verify:
        report=json.loads((public/'report.json').read_text()); meta=json.loads((public/'metadata.json').read_text())
        if meta!={'report_sha256':digest(report),'bindings':bindings()}: raise ValueError('Synthetic artifact binding differs')
    else:
        if not a.output:p.error('Private generated-media directory required')
        if public.exists(): raise ValueError('Preserve prior smoke report')
        report=derive(a.output); verify_report(report); public.mkdir(parents=True)
        (public/'report.json').write_bytes(canonical(report))
        (public/'metadata.json').write_bytes(canonical({'report_sha256':digest(report),'bindings':bindings()}))
    print(json.dumps({'report_sha256':digest(report),**verify_report(report)}))


if __name__=='__main__':main()
