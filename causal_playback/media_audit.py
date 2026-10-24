"""Post-run media-duration/provenance audit; does not change the frozen policy."""
import argparse
import csv
import json
from pathlib import Path
import subprocess
from causal_playback.data import ROOT
from causal_compensation.data import SOURCES
from causal_playback.prepare import probe, signature
from reserve_recovery.run import sha


def audit(cache):
    manifest=json.loads((ROOT/'causal_playback/data/media_manifest.json').read_text())
    sources={}
    sizes={}
    for cohort,folder in SOURCES.items():
        old=json.loads((ROOT/folder/'metadata.json').read_text())
        for entry in old['sources']:
            for rung,digest in enumerate(entry['rendition_sha256']):
                sources[cohort,entry['content'],rung]=digest
        with (ROOT/folder/'segment_sizes.csv').open(newline='') as f:
            for row in csv.DictReader(f):
                sizes[cohort,row['content'],int(row['segment']),int(row['ladder_index'])]=int(row['bytes'])
    for source in manifest['sources']:
        assert sources[source['cohort'],source['scene'],source['rung']]==source['sha256']
    rows=[]
    for item in manifest['files']:
        path=cache/item['relative_path']
        assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256']
        packets=probe(path)
        assert signature(packets)==item['packet_signature']
        assert sum(int(p['size']) for p in packets)==item['video_payload_bytes']
        assert item['video_payload_bytes']==sizes[item['cohort'],item['scene'],item['segment'],item['rung']]
        metadata=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0',
            '-show_entries','stream=start_time,duration,nb_frames,r_frame_rate','-of','json',str(path)],text=True))
        stream=metadata['streams'][0]
        assert int(stream['nb_frames'])==item['packets'] and stream['r_frame_rate']=='30/1'
        duration=float(stream['duration'])
        assert abs(duration-item['packets']/30)<1e-6
        rows.append({'relative_path':item['relative_path'],'scene':item['scene'],'segment':item['segment'],
                     'frames':item['packets'],'duration_seconds':duration,'start_seconds':float(stream['start_time']),
                     'file_bytes':item['bytes'],'container_overhead_bytes':item['bytes']-item['video_payload_bytes']})
    # The frozen clock uses 10 seconds. Do not silently replace that experiment.
    assert all(r['frames']==(299 if r['segment']==5 and r['scene']=='River01' else 300) for r in rows)
    return {'passed':True,'posthoc_validation_only':True,'segments':len(rows),'sources':len(sources),
            'manifest_sha256':sha(ROOT/'causal_playback/data/media_manifest.json'),
            'auditor_sha256':sha(Path(__file__)),'rows':rows,
            'finding':'River01 final segment has 299/30 seconds; all others have 10 seconds. Frozen clock uses nominal 10 seconds.'}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--cache',type=Path,default=ROOT/'.external/causal_playback_v1')
    p.add_argument('--save',type=Path,default=ROOT/'causal_playback/results/media_audit.json')
    a=p.parse_args(); result=audit(a.cache)
    with a.save.open('x') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
