"""Remux already-exposed local media; verify packet identity before use."""
import argparse
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import subprocess
from causal_compensation.data import ROOT,SOURCES
from reserve_recovery.run import sha,canonical

EXTERNAL={'v2':'feasibility_v2','v3':'horizon_v3'}


def probe(path):
    raw=subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_packets',
        '-show_data_hash','sha256','-show_entries','packet=pts_time,size,data_hash','-of','json',str(path)],text=True)
    return json.loads(raw)['packets']


def signature(packets): return hashlib.sha256(canonical([(int(p['size']),p['data_hash']) for p in packets])).hexdigest()


def prepare(output,cache):
    if output.exists() or cache.exists(): raise FileExistsError('preserve prior manifest/cache')
    cache.mkdir(parents=True); rows=[]; sources=[]
    for cohort,folder in SOURCES.items():
        old=json.loads((ROOT/folder/'metadata.json').read_text())
        for entry in old['sources']:
            scene=entry['content']
            for rung in range(6):
                source=ROOT/'.external'/EXTERNAL[cohort]/'renditions'/scene/f'rep_{rung}.mp4'
                digest=sha(source); assert digest==entry['rendition_sha256'][rung],source
                packets=probe(source); groups=[[] for _ in range(6)]
                for p in packets:
                    t=int(Decimal(p['pts_time'])//10)
                    if 0<=t<6: groups[t].append(p)
                    else: raise ValueError('unexpected packet timestamp')
                target=cache/cohort/scene/f'r{rung}'; target.mkdir(parents=True)
                subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-i',str(source),
                    '-map','0:v:0','-c','copy','-f','segment','-segment_time','10',
                    '-reset_timestamps','1',str(target/'s%d.mp4')],check=True)
                actual=sorted(target.glob('s*.mp4')); assert len(actual)==6
                for t in range(6):
                    path=target/f's{t}.mp4'; selected=probe(path)
                    assert signature(selected)==signature(groups[t]),(cohort,scene,rung,t,'packet mismatch')
                    rows.append({'cohort':cohort,'scene':scene,'rung':rung,'segment':t,
                        'relative_path':path.relative_to(cache).as_posix(),'bytes':path.stat().st_size,
                        'sha256':sha(path),'video_payload_bytes':sum(int(p['size']) for p in selected),
                        'packets':len(selected),'packet_signature':signature(selected)})
                sources.append({'cohort':cohort,'scene':scene,'rung':rung,'sha256':digest})
            print(f'Identity-verified {scene}',flush=True)
    out={'files':rows,'sources':sources,'existing_exposed_media_only':True,'reencoded':False,
         'packet_identity_verified':True,'ffmpeg':subprocess.check_output(['ffmpeg','-version'],text=True).splitlines()[0],
         'script_sha256':sha(Path(__file__))}
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f: json.dump(out,f,indent=2); f.write('\n')
    return out


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'causal_playback/data/media_manifest.json')
    p.add_argument('--cache',type=Path,default=ROOT/'.external/causal_playback_v1')
    a=p.parse_args(); result=prepare(a.output,a.cache); print(f"Prepared {len(result['files'])} identity-verified segments")
