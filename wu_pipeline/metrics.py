"""Legacy native-MSE features and explicit offline-versus-past information split."""
import math
import numpy as np
from multimedia_testbed.prepare_qoevave import tile_mse,viewport_weights


def mse_map(reference,distorted,seconds=60):
    if reference.shape!=(seconds,480,960) or distorted.shape!=reference.shape:
        raise ValueError('Exact matching sample census required; no truncation')
    if reference.dtype!=np.float32 or distorted.dtype!=np.float32:
        raise ValueError('Legacy float32 frame arithmetic required')
    if not np.isfinite(reference).all() or not np.isfinite(distorted).all() or min(reference.min(),distorted.min())<0 or max(reference.max(),distorted.max())>255:
        raise ValueError('Eight-bit grayscale range required')
    return tile_mse(reference,distorted).astype('<f4')


def aggregate_native(maps,poses,unit=10):
    if maps.shape!=(6,60,6,12) or poses.shape!=(60,2) or unit not in (2,10):
        raise ValueError('Frozen map/pose dimensions required')
    if not np.isfinite(maps).all() or np.any(maps<0) or np.any(maps>65025) or not np.isfinite(poses).all():
        raise ValueError('Finite valid distortion and poses required')
    if np.any(np.abs(poses[:,0])>180) or np.any(np.abs(poses[:,1])>90):
        raise ValueError('Pose angles outside calibrated coordinates')
    weights=np.stack([viewport_weights(*p) for p in poses])
    native=np.sum(maps.astype(np.float64)*weights[None,:,:,:],axis=(2,3))
    means=native.reshape(6,60//unit,unit).mean(axis=2)
    # Same direct native-MSE arithmetic as the frozen exposed chunk account.
    micro=np.rint(-means*1e6).astype(np.int64)
    scalar=np.empty_like(means)
    for rung in range(6):
        for segment in range(60//unit):
            samples=[]
            for i in range(segment*unit,(segment+1)*unit):
                samples.append(math.fsum(float(a)*float(w) for a,w in zip(maps[rung,i].flat,weights[i].flat)))
            scalar[rung,segment]=math.fsum(samples)/unit
    if np.max(np.abs(scalar-means))>1e-9:
        raise ValueError('Independent native-MSE aggregation differs')
    scalar_micro=np.array([[round(-float(v)*1e6) for v in row] for row in scalar],dtype=np.int64)
    if not np.array_equal(scalar_micro,micro):
        raise ValueError('Micro-MSE rounding ambiguity; preserve and version before rerun')
    return {'native_mse':means.tolist(),'negative_micro_mse':micro.tolist(),
        'duration_ticks':[unit*150000]*(60//unit),'independent_scalar_micro_exact':True,
        'information_scope':'offline_evaluation_only'}


def past_only(record,before_parent):
    """Explicit view for later integration; no current/future trace labels."""
    if type(before_parent) is not int or before_parent not in range(7): raise ValueError('Invalid decision boundary')
    a=np.asarray(record['negative_micro_mse'])
    if a.shape!=(6,6) or record['information_scope']!='offline_evaluation_only': raise ValueError('Not a parent label record')
    return {'negative_micro_mse':a[:,:before_parent].tolist(),
        'parents_visible':before_parent,'future_labels_included':False}
