"""Derive scalar forecasts from causal mask prefixes; raw telemetry stays local."""
import argparse
import gzip
import json
from pathlib import Path
import numpy as np
from causal_compensation.data import ROOT
from feedback_opportunity.feedback import mask, weights
from reserve_recovery.run import canonical, sha


def forecast(maps, observed):
    """No unobserved viewport may be passed; maps are sender-known content."""
    if maps.shape != (6,60,72) or not 1 <= len(observed) <= 60:
        raise ValueError('six-rung maps and nonempty observed prefix required')
    if not np.all(np.isfinite(maps)) or np.any(maps < 0):
        raise ValueError('invalid distortion map')
    w = np.stack([weights(m) for m in observed])
    w = np.concatenate((w, np.repeat(w[-1:], 60-len(w), axis=0)))
    mse = np.sum(maps.astype(float)*w[None,:,:],axis=2).reshape(6,6,10).mean(axis=2)
    db = 10*np.log10(255**2/np.maximum(mse,1e-12))
    return np.floor(np.clip(1+(db.T-18)/6,1,5)*1000+.5).astype(int).tolist()


def derive():
    base = ROOT/'feedback_opportunity/data/maps_v1'
    meta = json.loads((base/'metadata.json').read_text())
    private = ROOT/'.external/feedback_opportunity_v1/client_events.json'
    assert sha(private) == meta['private_events_sha256']
    events = json.loads(private.read_text()); by_user = {}
    for event in events:
        cohort,scene,subject,segment = event['key'].split(':')
        key = ':'.join((cohort,scene,subject))
        by_user.setdefault(key,{})[int(segment)] = event['events']
    maps = {}
    for source in meta['sources']:
        path = base/source['map_file']; assert sha(path)==source['descriptor']
        maps[source['scene']] = np.load(path)['mse']
    rows = {}
    for key,segments in sorted(by_user.items()):
        assert set(segments)==set(range(6))
        observed = [mask(e['yaw'],e['pitch']) for t in range(6) for e in segments[t]]
        rows[key] = [forecast(maps[key.split(':')[1]], observed[:h+1]) for h in range(60)]
    assert len(rows)==168
    return {'exposed_only':True,'unit':'0.001 quality index', 'rows':rows}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--verify',action='store_true'); a=p.parse_args()
    out=ROOT/'early_commitment/data/prefix_v1'; result=derive()
    if a.verify:
        with gzip.open(out/'forecasts.json.gz','rt') as f: assert json.load(f)==result
        print('Private prefix reconstruction passed: 168 users, 10080 observed prefixes')
    else:
        out.mkdir(parents=True,exist_ok=False)
        (out/'forecasts.json.gz').write_bytes(gzip.compress(canonical(result),mtime=0))
        meta={'script_sha256':sha(Path(__file__)), 'feedback_source_sha256':sha(ROOT/'feedback_opportunity/feedback.py'),
              'map_metadata_sha256':sha(ROOT/'feedback_opportunity/data/maps_v1/metadata.json'),
              'result_sha256':sha(out/'forecasts.json.gz'), 'private_events_sha256':sha(ROOT/'.external/feedback_opportunity_v1/client_events.json')}
        (out/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
        print('Prepared 10080 scalar prefix forecasts; no raw poses published')
