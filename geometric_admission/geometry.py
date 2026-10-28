"""Complete geometric mask family; no measured or predicted future poses."""
from itertools import product
import math
import numpy as np
from feedback_opportunity.feedback import mask,weights
from admission_contract.core import spatial_bounds

YAW_CENTRES=tuple(range(-165,180,30))
PITCH_CENTRES=tuple(range(75,-90,-30))
HALF_FOV=50


def representatives(axis):
    """All membership boundaries and one representative per open interval."""
    if axis=='yaw':
        boundary={-180.,180.}
        boundary.update(float((x+d+180)%360-180) for x in YAW_CENTRES for d in (-50,50))
    elif axis=='pitch':
        boundary={-90.,90.}
        boundary.update(float(x+d) for x in PITCH_CENTRES for d in (-50,50) if -90<=x+d<=90)
    else:raise ValueError('Unknown axis')
    ordered=sorted(boundary)
    return sorted(boundary|{(a+b)/2 for a,b in zip(ordered,ordered[1:])})


def family():
    seen={}
    for yaw,pitch in product(representatives('yaw'),representatives('pitch')):
        value=mask(yaw,pitch)
        seen.setdefault(value,{'mask_hex':value.hex(),'yaw':yaw,'pitch':pitch})
    return [seen[k] for k in sorted(seen)]


def integer_grid_family():
    """Independent scalar exhaustive lattice: complete because boundaries are integral
    and all distinct boundary gaps in this fixed model exceed one degree."""
    horizontal=set();vertical=set()
    for yaw in range(-180,181):
        horizontal.add(tuple(i for i,y in enumerate(YAW_CENTRES) if min(abs(y-yaw),360-abs(y-yaw))<=50))
    for pitch in range(-90,91):
        vertical.add(tuple(j for j,p in enumerate(PITCH_CENTRES) if abs(p-pitch)<=50))
    return {sum(1<<(12*j+i) for j in v for i in h).to_bytes(9,'big') for h,v in product(horizontal,vertical)}


def matrix(rows):
    return np.stack([weights(bytes.fromhex(r['mask_hex'])) for r in rows])


def validate_family(rows):
    values={bytes.fromhex(r['mask_hex']) for r in rows}
    if len(values)!=len(rows) or values!=integer_grid_family():raise ValueError('Incomplete geometric family')
    for r in rows:
        if mask(r['yaw'],r['pitch'])!=bytes.fromhex(r['mask_hex']):raise ValueError('Invalid orientation witness')
    return {'unique_masks':len(rows),'integer_lattice_match':True,'orientation_witnesses':len(rows)}


def bounds(maps,rows):
    maps=np.asarray(maps,dtype=float)
    if maps.shape!=(6,60,72) or not np.isfinite(maps).all() or (maps<0).any() or (maps>65025).any():
        raise ValueError('Finite 8-bit sender distortion maps required')
    delta=maps[2:3]-maps
    scores=delta@matrix(rows).T
    minima=scores.min(axis=2);maxima=scores.max(axis=2)
    lower=np.floor(minima.reshape(6,6,10).mean(axis=2).T*1e6).astype(np.int64)-2
    upper=np.ceil(maxima.reshape(6,6,10).mean(axis=2).T*1e6).astype(np.int64)+2
    lower[:,2]=upper[:,2]=0
    old_lower,old_upper=spatial_bounds(maps)
    lower=np.maximum(lower,old_lower);upper=np.minimum(upper,old_upper)
    return lower,upper,{'minimum_mask_id':scores.argmin(axis=2).tolist(),
                        'maximum_mask_id':scores.argmax(axis=2).tolist()}


def check_extrema(maps,rows,lower,upper,witness):
    """Independent scalar-weight reduction over every mask, rung and second."""
    delta=np.asarray(maps,dtype=float)[2:3]-np.asarray(maps,dtype=float)
    area=[math.cos(math.radians(p)) for p in PITCH_CENTRES for _ in YAW_CENTRES]
    values=[]
    for r in rows:
        bits=int(r['mask_hex'],16);ids=[i for i in range(72) if bits>>i&1]
        divisor=sum(area[i] for i in ids)
        values.append(sum(delta[:,:,i]*area[i] for i in ids)/divisor)
    values=np.stack(values,axis=2);minimum=values.min(axis=2);maximum=values.max(axis=2)
    for rung in range(6):
        for second in range(60):
            lo=witness['minimum_mask_id'][rung][second];hi=witness['maximum_mask_id'][rung][second]
            if abs(values[rung,second,lo]-minimum[rung,second])>1e-8 or abs(values[rung,second,hi]-maximum[rung,second])>1e-8:
                raise ValueError('Non-extremal mask witness')
    # This tolerance checks floating evaluation only; no quality floor is relaxed.
    rawlo=minimum.reshape(6,6,10).mean(axis=2).T*1e6
    rawhi=maximum.reshape(6,6,10).mean(axis=2).T*1e6
    for rung in (0,1,3,4,5):
        if not ((lower[:,rung]<=rawlo[:,rung]+1e-4)&(upper[:,rung]>=rawhi[:,rung]-1e-4)).all():
            raise ValueError('Outward envelope failure')
    return {'extrema_checked':6*60*2,'weighted_values_checked':len(rows)*6*60,'passed':True}
