"""Conservative geometry and past-anchor cones; no future participant labels."""
from itertools import product
import math
import numpy as np
from feedback_opportunity.feedback import mask
from geometric_admission.geometry import YAW_CENTRES, PITCH_CENTRES, matrix
from metric_contract.core import TICKS

SCALE = 1000000  # integer microdegrees
GRID = (5, 15, 30, 60, 90, 180, 360)


def direction(yaw, pitch):
    yaw = np.asarray(yaw, dtype=float); pitch = np.asarray(pitch, dtype=float)
    if not np.isfinite(yaw).all() or not np.isfinite(pitch).all() or (np.abs(pitch) > 90).any():
        raise ValueError('Finite yaw and pitch in [-90,90] required')
    y = np.deg2rad(yaw); p = np.deg2rad(pitch)
    return np.stack((np.cos(p)*np.cos(y), np.cos(p)*np.sin(y), np.sin(p)), axis=-1)


def angles(a, b):
    """Stable shortest spherical forward-direction distance, in degrees."""
    a = np.asarray(a); b = np.asarray(b)
    return np.rad2deg(np.arctan2(np.linalg.norm(np.cross(a, b), axis=-1), np.sum(a*b, axis=-1)))


def orientation_cells(family):
    """Closed covers of all singleton/open-interval membership cells.

    Closing open cells can include extra boundary masks, which is conservative
    for a reachable-mask outer bound. A mask can occupy multiple rectangles.
    """
    y = sorted({-180., 180.} | {float((c+d+180)%360-180) for c in YAW_CENTRES for d in (-50, 50)})
    p = sorted({-90., 90.} | {float(c+d) for c in PITCH_CENTRES for d in (-50, 50) if -90 <= c+d <= 90})
    axis = lambda points: [(v, v) for v in points] + list(zip(points, points[1:]))
    ids = {r['mask_hex']: i for i, r in enumerate(family)}
    return [{'yaw_lo': a, 'yaw_hi': b, 'pitch_lo': c, 'pitch_hi': d,
             'mask_id': ids[mask((a+b)/2, (c+d)/2).hex()]}
            for (a, b), (c, d) in product(axis(y), axis(p))]


def distance_to_rectangle(yaw, pitch, cell):
    """Minimum great-circle distance to a closed longitude/latitude rectangle."""
    if not math.isfinite(yaw) or not math.isfinite(pitch) or not -90 <= pitch <= 90:
        raise ValueError('Invalid anchor orientation')
    yaw = (yaw+180)%360-180
    low, high = cell['yaw_lo'], cell['yaw_hi']
    if not -180 <= low <= high <= 180 or not -90 <= cell['pitch_lo'] <= cell['pitch_hi'] <= 90:
        raise ValueError('Invalid cell')
    cos_delta = max(math.cos(math.radians(low-yaw)), math.cos(math.radians(high-yaw)))
    if any(low <= yaw+shift <= high for shift in (-360, 0, 360)):
        cos_delta = 1.0
    lat = math.radians(pitch); k = math.cos(lat)*cos_delta; z = math.sin(lat)
    lo, hi = map(math.radians, (cell['pitch_lo'], cell['pitch_hi']))
    candidates = [lo, hi]
    stationary = math.atan2(z, k)
    candidates += [stationary+s for s in (-2*math.pi, 0, 2*math.pi) if lo <= stationary+s <= hi]
    dot = max(k*math.cos(p)+z*math.sin(p) for p in candidates)
    return math.degrees(math.acos(max(-1., min(1., dot))))


def mask_distances(yaw, pitch, family, cells):
    values = [180.]*len(family)
    for cell in cells:
        i = cell['mask_id']; values[i] = min(values[i], distance_to_rectangle(yaw, pitch, cell))
    # Outward microdegree guard, not a probabilistic confidence allowance.
    return np.array([max(0, math.floor(v*SCALE)-2) for v in values], dtype=np.int64)


def required_sampled_speed(times, yaw, pitch):
    times = np.asarray(times, dtype=float)
    if len(times) < 2 or not np.isfinite(times).all() or (np.diff(times) <= 0).any():
        raise ValueError('Strictly increasing finite observation timestamps required')
    positions = direction(yaw, pitch)
    if positions.shape != (len(times), 3):
        raise ValueError('Pose/timestamp shape mismatch')
    speed = angles(positions[1:], positions[:-1])/np.diff(times)
    return speed


def fit_speed(rows, scene, excluded_ids, quantile):
    """Trajectory-max speed quantile, no target scene or either target identity."""
    if not 0 < quantile <= 1:
        raise ValueError('Quantile must be in (0,1]')
    train = [r for r in rows if r['scene'] != scene and r['subject'] not in excluded_ids]
    if len(train) != 130:
        raise ValueError('Expected five scenes x26 identities')
    values = sorted(r['whole_max_speed_microdeg_s'] for r in train)
    threshold = values[math.ceil(quantile*len(values))-1]
    return threshold, [r['key'] for r in train]


def feature_table(scores, distances, age_ticks, speed, duration, segment, end_ticks, geometric_lower):
    """All-rung sampled-delta lower bounds at possible completion times.

    The pose is known at entry. For each future sample use the maximum elapsed
    wall time allowed by the specified playback envelope. Cones are nested;
    joint temporal consistency is relaxed, never assumed satisfied.
    """
    if age_ticks < 0 or speed < 0 or duration <= 0:
        raise ValueError('Nonnegative age/speed and positive duration required')
    order = np.argsort(distances, kind='stable'); ordered = distances[order]
    prefix = np.minimum.accumulate(scores[:, segment*10:(segment+1)*10, order], axis=2)
    rows = {}
    for end in sorted(set(map(int, end_ticks))):
        start = end-duration
        if start < 0:
            raise ValueError('Completion precedes duration')
        elapsed = age_ticks+start+(2*np.arange(10, dtype=np.int64)+1)*TICKS//2
        radius = np.minimum(180*SCALE, (int(speed)*elapsed+TICKS-1)//TICKS)
        ids = np.searchsorted(ordered, radius, side='right')-1
        if (ids < 0).any():
            raise ValueError('No reachable anchor mask')
        minima = prefix[:, np.arange(10), ids]
        lower = np.floor(minima.mean(axis=1)*1e6).astype(np.int64)-2
        lower = np.maximum(lower, geometric_lower[segment]); lower[2] = 0
        # Independent direct-mask reduction verifies the prefix implementation.
        direct = np.array([scores[:, segment*10+j, distances <= int(rad)].min(axis=1)
                           for j, rad in enumerate(radius)]).T
        raw = np.floor(direct.mean(axis=1)*1e6).astype(np.int64)-2
        raw = np.maximum(raw, geometric_lower[segment]); raw[2] = 0
        if not np.array_equal(raw, lower):
            raise ValueError('Direct reachable-mask score mismatch')
        rows[str(end)] = {'lower': lower[2:].tolist(),
                          'full_family_samples': int(np.sum(radius >= int(distances.max())))}
    return rows


def scores_for_maps(maps, family):
    values = np.asarray(maps, dtype=float)
    if values.shape != (6, 60, 72) or not np.isfinite(values).all():
        raise ValueError('Finite sender maps required')
    return (values[2:3]-values)@matrix(family).T
