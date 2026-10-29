"""Private, hash-bound keyframe remux and exposed sampled-quality derivation."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import gzip
import json
from pathlib import Path
import subprocess
import numpy as np
from metric_contract.data import ROOT,load
from metric_contract.run import canonical,sha
from feedback_opportunity.feedback import mask,weights

OUT=ROOT/'player_timing/data/v1'
MEDIA=ROOT/'.external/causal_playback_v1'
CACHE=ROOT/'.external/player_timing_v1'
EVENTS=ROOT/'.external/feedback_opportunity_v1/client_events.json'
MAPS=ROOT/'feedback_opportunity/data/maps_v1'


def probe(path):
    return json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
        '-show_packets','-show_streams','-show_data_hash','sha256','-show_entries',
        'packet=pts,dts,duration,flags,size,data_hash:stream=time_base,width,height,r_frame_rate,codec_name',
        '-of','json',str(path)],text=True))


def decoded(path):
    text=subprocess.check_output(['ffmpeg','-nostdin','-v','error','-threads','1','-i',str(path),
        '-map','0:v:0','-threads:v','1','-f','framemd5','-'],text=True)
    return [line.split(',')[-1].strip() for line in text.splitlines() if line and not line.startswith('#')]


def one(item):
    source=MEDIA/item['relative_path']
    if sha(source)!=item['sha256'] or source.stat().st_size!=item['bytes']:raise ValueError('Source changed')
    old=probe(source); packets=sorted(old['packets'],key=lambda p:p['pts']); stream=old['streams'][0]
    a,b=map(int,stream['time_base'].split('/')); unit=a/b
    if stream['codec_name']!='h264' or stream['r_frame_rate']!='30/1':raise ValueError('Unexpected codec/timebase')
    start=packets[0]['pts']; keys=[(p['pts']-start)*unit for p in packets if 'K' in p['flags']]
    if keys != [0.,2.,4.,6.,8.]:raise ValueError(f'Not two-second keyframes: {keys}')
    target=CACHE/item['cohort']/item['scene']/f"r{item['rung']}"/f"s{item['segment']}"
    target.mkdir(parents=True,exist_ok=False)
    subprocess.run(['ffmpeg','-nostdin','-v','error','-n','-i',str(source),'-map','0:v:0','-c','copy',
        '-f','segment','-segment_time','2','-reset_timestamps','1','-segment_format','mp4',
        '-segment_format_options','movflags=+faststart',str(target/'c%d.mp4')],check=True)
    paths=sorted(target.glob('c*.mp4'))
    if len(paths)!=5:raise ValueError('Five valid children required')
    olddecoded=decoded(source); allpayload=[]; allframes=[]; children=[]
    for i,path in enumerate(paths):
        p=probe(path); ps=sorted(p['packets'],key=lambda x:x['pts']); st=p['streams'][0]
        fields=('codec_name','width','height','r_frame_rate','time_base')
        if any(st[k]!=stream[k] for k in fields) or 'K' not in ps[0]['flags']:raise ValueError('Invalid independent child')
        origin=ps[0]['pts']; pts=[(r['pts']-origin)*unit for r in ps]; ds=[r['duration']*unit for r in ps]
        if any(abs(pts[j]-j/30)>1e-8 or abs(d-1/30)>1e-8 for j,d in enumerate(ds)):
            raise ValueError('Non-contiguous child PTS')
        payload=[r['data_hash'] for r in ps]; frames=decoded(path)
        if len(frames)!=len(ps):raise ValueError('Decode count mismatch')
        allpayload.extend(payload); allframes.extend(frames)
        children.append({'index':i,'bytes':path.stat().st_size,'sha256':sha(path),
            'relative_path':path.relative_to(CACHE).as_posix(),'duration':len(ps)/30,'frames':len(ps),
            'payload_sha256':__import__('hashlib').sha256(canonical(payload)).hexdigest(),
            'decoded_sha256':__import__('hashlib').sha256(canonical(frames)).hexdigest()})
    if allpayload!=[p['data_hash'] for p in packets] or allframes!=olddecoded:
        raise ValueError('Remux changed payload or decoded pixels')
    return {**item,'duration':len(packets)/30,'keyframes':keys,'children':children,
        'decoded_sha256':__import__('hashlib').sha256(canonical(olddecoded)).hexdigest(),
        'payload_and_decoded_parity':True,'container_overhead_bytes':sum(c['bytes'] for c in children)-item['bytes']}


def features(records):
    meta=json.loads((MAPS/'metadata.json').read_text())
    if sha(EVENTS)!=meta['private_events_sha256']:raise ValueError('Private events changed')
    events={r['key']:r for r in json.loads(EVENTS.read_text())}; maps={}
    for s in meta['sources']:
        path=MAPS/s['map_file']
        if sha(path)!=s['descriptor']:raise ValueError('Map changed')
        maps[s['scene']]=np.load(path)['mse'].astype(float)
    out=[]; parity=[]
    for record in records:
        cohort,scene,sid,did=record['key'].split(':'); q=np.zeros((20,2,6),dtype=np.int64)
        for u,subject in enumerate((sid,did)):
            for parent in range(2,6):
                sample=events[f'{cohort}:{scene}:{subject}:{parent}']['events']
                ws=np.stack([weights(mask(e['yaw'],e['pitch'])) for e in sample])
                mse=np.sum(maps[scene][:,parent*10:parent*10+10]*ws[None,:,:],axis=2)
                psnr=10*np.log10(65025/np.maximum(mse.mean(axis=1),1e-12))
                error=float(np.max(np.abs(psnr-record['quality'][2,parent,u]/1e6)))
                if error>2e-6:raise ValueError('Reconstruction differs from old sample definition')
                parity.append(error)
                for c in range(5):
                    q[(parent-2)*5+c,u]=np.rint(-mse[:,c*2:c*2+2].mean(axis=1)*1e6).astype(np.int64)
        out.append({'key':record['key'],'negative_micro_mse':q.tolist()})
    return {'rows':out,'maximum_parent_psnr_error_db':max(parity),
            'parent_label_checks':len(parity),'private_events_sha256':sha(EVENTS),
            'map_metadata_sha256':sha(MAPS/'metadata.json')}


def main():
    if OUT.exists() or CACHE.exists():raise FileExistsError('Preserve preparation attempts')
    manifest=json.loads((ROOT/'causal_playback/data/media_manifest.json').read_text())
    items=[x for x in manifest['files'] if x['segment']>=2 and x['rung']>=2]
    if len(items)!=96:raise ValueError('96 exposed parent files required')
    OUT.mkdir(parents=True)
    rows=[]
    with ThreadPoolExecutor(max_workers=4) as pool:
        for i,row in enumerate(pool.map(one,items),1):
            rows.append(row)
            print(f'Remux and decoded-pixel validation {i}/96',flush=True)
    records,_=load(); quality=features(records)
    value={'rows':rows,'quality':quality,'source_manifest_sha256':sha(ROOT/'causal_playback/data/media_manifest.json'),
           'prepare_sha256':sha(Path(__file__)),
           'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0]}
    (OUT/'derived.json.gz').write_bytes(gzip.compress(canonical(value),mtime=0))
    print(json.dumps({'parents':len(rows),'children':sum(len(r['children']) for r in rows),
        'feature_rows':len(quality['rows']),'parent_psnr_error':quality['maximum_parent_psnr_error_db']}))


if __name__=='__main__':main()
