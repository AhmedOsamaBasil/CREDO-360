"""Content-bound completed-viewport feedback; no per-user labels are inputs."""
import hashlib
import math
import struct
import numpy as np

HEADER=struct.Struct('!4s32sBBId')
SIZE=HEADER.size+90
MAGIC=b'VQF1'
AREA=np.repeat(np.cos(np.deg2rad(np.linspace(75,-75,6))),12)


def mask(yaw,pitch):
    if not math.isfinite(yaw) or not math.isfinite(pitch) or not -90<=pitch<=90:
        raise ValueError('finite renderer yaw/pitch in degrees required')
    y=np.linspace(-165,165,12); p=np.linspace(75,-75,6)
    cells=(np.abs((y[None,:]-yaw+180)%360-180)<=50)&(np.abs(p[:,None]-pitch)<=50)
    value=sum(1<<i for i,x in enumerate(cells.flat) if x)
    if not value: raise ValueError('empty viewport')
    return value.to_bytes(9,'big')


def weights(value):
    bits=int.from_bytes(value,'big')
    w=np.array([(bits>>i)&1 for i in range(72)],dtype=float)*AREA
    if len(value)!=9 or not w.any(): raise ValueError('invalid mask')
    return w/w.sum()


def unpack(packet,descriptor,expected_segment,expected_sequence):
    if len(packet)!=SIZE: raise ValueError('incorrect packet size')
    magic,digest,segment,rung,sequence,end=HEADER.unpack(packet[:HEADER.size])
    if magic!=MAGIC or digest.hex()!=descriptor: raise ValueError('wrong protocol/content')
    if segment!=expected_segment or sequence!=expected_sequence: raise ValueError('out-of-order or duplicate')
    if not 0<=segment<6 or not 0<=rung<6 or not math.isfinite(end) or end<(segment+1)*10-1e-9:
        raise ValueError('invalid or incomplete playback')
    ws=np.stack([weights(packet[HEADER.size+i*9:HEADER.size+(i+1)*9]) for i in range(10)])
    return segment,rung,sequence,end,ws


def reconstruct(packet,maps,descriptor,expected_segment,expected_sequence):
    segment,rung,sequence,end,ws=unpack(packet,descriptor,expected_segment,expected_sequence)
    if maps.shape!=(6,60,72) or not np.all(np.isfinite(maps)) or np.any(maps<0):
        raise ValueError('invalid sender map')
    mse=np.mean(np.sum(maps[:,segment*10:(segment+1)*10,:].astype(float)*ws[None,:,:],axis=2),axis=1)
    db=10*np.log10(255**2/np.maximum(mse,1e-12))
    units=np.floor(np.clip(1+(db-18)/6,1,5)*1000+.5).astype(int)
    return {'segment':segment,'rung':rung,'sequence':sequence,'media_end':end,
            'psnr_db':db.tolist(),'quality_units':units.tolist(),
            'selected_units':int(units[rung]),'reference_units':int(units[2]),
            'packet_sha256':hashlib.sha256(packet).hexdigest()}
