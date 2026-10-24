"""Existing-media sender maps and private causal pose events; never downloads."""
import argparse
import json
from pathlib import Path
import time
import numpy as np
from causal_compensation.data import ROOT,SOURCES
from multimedia_testbed.prepare_qoevave import decoded_frames,tile_mse,load_traces,viewport_scores
from reserve_recovery.run import sha

EXTERNAL={'v2':'feasibility_v2','v3':'horizon_v3'}


def prepare(output,private):
    if output.exists() or private.exists(): raise FileExistsError('preserve earlier artifacts')
    output.mkdir(parents=True); private.mkdir(parents=True)
    provenance=[]; events=[]; parity=[]
    for cohort,folder in SOURCES.items():
        metadata=json.loads((ROOT/folder/'metadata.json').read_text())
        for old in metadata['sources']:
            start=time.perf_counter(); scene=old['content']; base=ROOT/'.external'/EXTERNAL[cohort]
            source=base/'media'/f'{scene}.mp4'; trace=base/'traces'/f'{scene}.zip'
            assert sha(source)==old['source_sha256'] and sha(trace)==old['trace_sha256']
            ref=decoded_frames(source,60); assert len(ref)==60
            maps=[]
            for rung in range(6):
                rendition=base/'renditions'/scene/f'rep_{rung}.mp4'
                assert sha(rendition)==old['rendition_sha256'][rung]
                dist=decoded_frames(rendition,60); assert len(dist)==60
                maps.append(tile_mse(ref,dist).reshape(60,72)); del dist
            maps=np.stack(maps).astype('<f4'); del ref
            path=output/f'{scene}.npz'; np.savez_compressed(path,mse=maps)
            descriptor=sha(path); traces=load_traces(trace)
            for sid,series in traces.items():
                assert np.all(np.diff(series['time'])>=0)
                for rung in range(6):
                    psnr,_=viewport_scores(maps[rung].reshape(60,6,12),np.zeros((60,6,12)),series,60)
                    parity.extend({'cohort':cohort,'scene':scene,'subject':sid,'segment':s,'rung':rung,'psnr_db':q}
                                  for s,q in enumerate(psnr))
                for s in range(6):
                    positions=np.arange(s*10,(s+1)*10)+.5
                    indices=np.searchsorted(series['time'],positions,side='right')-1
                    if min(indices)<0: raise ValueError('missing initial history')
                    samples=[{'mediaTime':float(t),'poseTime':float(series['time'][i]),
                              'yaw':float(series['yaw'][i]),'pitch':float(series['pitch'][i])} for t,i in zip(positions,indices)]
                    if any(e['mediaTime']-e['poseTime']>.1 for e in samples): raise ValueError('stale pose, no silent fill')
                    events.append({'key':f'{cohort}:{scene}:{sid}:{s}','descriptor':descriptor,'segment':s,
                                   'rung':0 if s<2 else 2,'sequence':s,'mediaEnd':(s+1)*10,'events':samples})
            provenance.append({'cohort':cohort,'scene':scene,'map_file':path.name,'descriptor':descriptor,
                'map_shape':list(maps.shape),'map_bytes':path.stat().st_size,'source_sha256':old['source_sha256'],
                'rendition_sha256':old['rendition_sha256'],'trace_sha256':old['trace_sha256'],
                'preparation_seconds':time.perf_counter()-start})
            print(f'Sender maps and causal events prepared: {scene}',flush=True)
    (private/'client_events.json').write_text(json.dumps(events))
    (output/'old_sampling_parity.json').write_text(json.dumps(parity,indent=2)+'\n')
    meta={'exposed_only':True,'sources':provenance,'script_sha256':sha(Path(__file__)),
          'analysis_source_sha256':sha(ROOT/'multimedia_testbed/prepare_qoevave.py'),
          'private_events_sha256':sha(private/'client_events.json'),
          'files_sha256':{p.name:sha(p) for p in output.iterdir() if p.is_file()}}
    (output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'feedback_opportunity/data/maps_v1')
    p.add_argument('--private',type=Path,default=ROOT/'.external/feedback_opportunity_v1')
    a=p.parse_args(); prepare(a.output,a.private)
