"""Fixed encoder, timestamp-audited remux, and legacy sampling primitives."""
from fractions import Fraction
import hashlib
import json
import platform
from pathlib import Path
import shutil
import subprocess
import numpy as np
from wu_source.acquire import sha256,canonical

LADDER=(.045373,.088482,.252988,.368912,.987061,3.792491)


def call(args,timeout=1800):
    return subprocess.run([str(a) for a in args],check=True,stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,timeout=timeout).stdout


def encode_command(source,target,rung,seconds=60):
    if type(rung) is not int or rung not in range(6): raise ValueError('Unknown rung')
    bitrate=max(20,int(round(1000*LADDER[rung])))
    return ['ffmpeg','-nostdin','-v','error','-n','-t',str(seconds),'-i',str(source),
        '-map','0:v:0','-an','-vf','scale=1920:960:flags=lanczos,fps=30',
        '-c:v','h264_nvenc','-preset','p5','-tune','hq','-rc','vbr',
        '-b:v',f'{bitrate}k','-maxrate',f'{2*bitrate}k','-bufsize',f'{4*bitrate}k',
        '-g','60','-keyint_min','60','-pix_fmt','yuv420p','-movflags','+faststart',str(target)]


def fingerprint():
    result={'python_version':platform.python_version(),'numpy_version':np.__version__}
    for tool in ('ffmpeg','ffprobe'):
        path=shutil.which(tool)
        if path is None: raise ValueError('Required media binary missing')
        result[tool]={'binary_sha256':sha256(Path(path)),
            'version':call([tool,'-version']).decode().strip().splitlines()}
    result['gpu']=call(['nvidia-smi','--query-gpu=name,driver_version','--format=csv,noheader']).decode().strip().splitlines()
    return result


def probe(path):
    return json.loads(call(['ffprobe','-v','error','-select_streams','v:0','-show_packets',
        '-show_streams','-show_format','-show_data_hash','sha256','-show_entries',
        'packet=pts,dts,duration,size,flags,data_hash:stream=codec_name,width,height,r_frame_rate,time_base,start_time:format=duration',
        '-of','json',path]))


def timeline(info,seconds):
    if len(info['streams'])!=1: raise ValueError('One video stream required')
    s=info['streams'][0]; packets=sorted(info['packets'],key=lambda p:int(p['pts']))
    if s['codec_name']!='h264' or (s['width'],s['height'])!=(1920,960) or Fraction(s['r_frame_rate'])!=30:
        raise ValueError('Rendition format changed')
    tb=Fraction(s['time_base'])
    if len(packets)!=seconds*30 or Fraction(s['start_time'])!=0:
        raise ValueError('Frame count or media origin differs')
    if any(int(p['pts'])*tb!=Fraction(i,30) or int(p['duration'])*tb!=Fraction(1,30)
           for i,p in enumerate(packets)): raise ValueError('Non-contiguous presentation grid')
    if abs(Fraction(info['format']['duration'])-seconds)>Fraction(1,500):
        raise ValueError('Container duration differs')
    if any('K' not in packets[i]['flags'] for i in range(0,len(packets),60)):
        raise ValueError('Required two-second keyframe absent')
    return packets


def frame_hashes(path,filters=None,seconds=None,lavfi=False):
    command=['ffmpeg','-nostdin','-v','error','-threads','1']
    if lavfi: command+=['-f','lavfi']
    if seconds is not None: command+=['-t',str(seconds)]
    command+=['-i',str(path),'-map','0:v:0','-threads:v','1','-an']
    if filters: command+=['-vf',filters]
    command+=['-f','framemd5','-']
    lines=call(command).decode().splitlines()
    return [line.split(',')[-1].strip() for line in lines if line and not line.startswith('#')]


def phase_check(path,seconds=60,lavfi=False):
    direct=frame_hashes(path,'fps=1',seconds,lavfi)
    cascaded=frame_hashes(path,'fps=30,fps=1',seconds,lavfi)
    if len(direct)!=seconds or len(cascaded)!=seconds: raise ValueError('Phase sample count differs')
    return {'samples':seconds,'different_sample_bins':[i for i,(a,b) in enumerate(zip(direct,cascaded)) if a!=b],
        'direct_pixel_hashes_sha256':hashlib.sha256(canonical(direct)).hexdigest(),
        'cascaded_pixel_hashes_sha256':hashlib.sha256(canonical(cascaded)).hexdigest(),
        'changes_primary_sampler':False,'proves_same_source_frame_identity':False}


def sample_frames(path,seconds=60):
    raw=call(['ffmpeg','-nostdin','-v','error','-t',str(seconds),'-i',path,'-map','0:v:0','-an',
        '-vf','fps=1,scale=960:480:flags=lanczos,format=gray','-f','rawvideo','-pix_fmt','gray','pipe:1'])
    expected=seconds*480*960
    if len(raw)!=expected: raise ValueError('Complete exact sampled frame stream required')
    return np.frombuffer(raw,dtype=np.uint8).reshape(seconds,480,960).astype(np.float32)


def packet_signature(packets):
    return hashlib.sha256(canonical([(int(p['size']),p['data_hash']) for p in packets])).hexdigest()


def describe(path,seconds,root):
    packets=timeline(probe(path),seconds); hashes=frame_hashes(path)
    if len(hashes)!=seconds*30: raise ValueError('Decoded frame census differs')
    return {'relative_path':path.relative_to(root).as_posix(),'bytes':path.stat().st_size,
        'sha256':sha256(path),'payload_bytes':sum(int(p['size']) for p in packets),
        'duration_ticks':seconds*150000,'frames':len(packets),
        'packet_signature':packet_signature(packets),
        'decoded_sha256':hashlib.sha256(canonical(hashes)).hexdigest()},packets,hashes


def split_verified(source,directory,unit,total,root):
    """Normalize only newly encoded/remuxed outputs, never original stimuli."""
    if total%unit or unit not in (2,10): raise ValueError('Invalid split interval')
    directory.mkdir(parents=True,exist_ok=False)
    original=timeline(probe(source),total); decoded=frame_hashes(source)
    call(['ffmpeg','-nostdin','-v','error','-n','-i',source,'-map','0:v:0','-c','copy',
        '-f','segment','-segment_time',str(unit),'-reset_timestamps','1','-segment_format','mp4',
        '-segment_format_options','movflags=+faststart',directory/'raw_%d.mp4'])
    raw=sorted(directory.glob('raw_*.mp4'))
    if len(raw)!=total//unit: raise ValueError('Split file count differs')
    records=[]; all_packets=[]; all_frames=[]
    for i in range(total//unit):
        target=directory/f'part_{i}.mp4'
        call(['ffmpeg','-nostdin','-v','error','-n','-i',directory/f'raw_{i}.mp4',
            '-map','0:v:0','-c','copy','-avoid_negative_ts','disabled','-movflags','+faststart',target])
        record,packets,frames=describe(target,unit,root)
        expected=original[i*unit*30:(i+1)*unit*30]
        if packet_signature(packets)!=packet_signature(expected) or frames!=decoded[i*unit*30:(i+1)*unit*30]:
            raise ValueError('Remux payload or pixel identity differs')
        records.append({'index':i,**record}); all_packets+=packets; all_frames+=frames
    if packet_signature(all_packets)!=packet_signature(original) or all_frames!=decoded:
        raise ValueError('Incomplete remux closure')
    return records
