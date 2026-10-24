"""Verify deterministic replay and replay measured arrival/feedback clocks."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform
from causal_playback.data import ROOT,load,pool
from causal_playback.replay import analysis,report,choose_step,reserve
from causal_playback.clock import State
from causal_playback.live import cases
from reserve_recovery.run import canonical,encode,sha


def equal(a,b):
    if isinstance(a,(float,int)) and isinstance(b,(float,int)): assert abs(a-b)<1e-7,(a,b)
    elif isinstance(a,dict):
        assert set(a)==set(b)
        for k in a: equal(a[k],b[k])
    elif isinstance(a,(tuple,list)):
        assert len(a)==len(b)
        for x,y in zip(a,b): equal(x,y)
    else: assert a==b,(a,b)


def verify_replay(directory):
    meta=json.loads((directory/'metadata.json').read_text())
    for field in ('source_sha256','input_sha256'):
        for name,digest in meta[field].items(): assert sha(ROOT/name)==digest,name
    for name,digest in meta['result_sha256'].items(): assert sha(directory/name)==digest,name
    p=encode(analysis(True))
    with gzip.open(directory/'results.json.gz','rt') as f: assert p==json.load(f)
    assert report(p)==(directory/'REPORT.md').read_text()
    digest=hashlib.sha256(canonical(p)).hexdigest(); assert digest==meta['scientific_sha256']
    return {'passed':True,'episode_policy_runs':len(p['rows']),'scientific_sha256':digest,'screen':p['screen']}


def verify_live(directory):
    meta=json.loads((directory/'metadata.json').read_text())
    for name,digest in meta['source_sha256'].items(): assert sha(ROOT/name)==digest,name
    for name,digest in meta['files_sha256'].items(): assert sha(directory/name)==digest,name
    manifest=json.loads((ROOT/'causal_playback/data/media_manifest.json').read_text())
    assert meta['manifest_sha256']==sha(ROOT/'causal_playback/data/media_manifest.json')
    files={f['relative_path']:f for f in manifest['files']}
    records=load(manifest); expected=cases(records); rows=json.loads((directory/'results.json').read_text())
    assert len(rows)==len(expected)==30
    receipts=0; nominal_misses=stress_misses=0; scientific=[]
    for row,(record,policy,rate) in zip(rows,expected):
        assert row['completed'] and row['key']==record.key and row['policy']==policy and row['rate_kbit']==rate
        assert row['reserve_bytes']==reserve(record) and row['background_bytes']>0
        training=pool(records,record); state=State(record); assert len(row['rounds'])==4
        journal=[json.loads(line) for line in (directory/f"episode_{row['index']:02d}.jsonl").read_text().splitlines()]
        assert [r for r in journal if r['type']=='round']==row['rounds']
        for step in row['rounds']:
            t=step['segment']; decision,info=choose_step(record,training,state,policy,t,step['start'])
            equal(encode(decision),step['decision'])
            for k,v in info.items(): equal(encode(v),step[k])
            assert step['start']<=step['decision_end']<=min(step['arrivals'])
            assert max(step['acknowledged'])<=step['client_return']<=step['end']
            assert step['end']-step['start']>=10-1e-7
            for u,receipt in enumerate(step['receipts']):
                f=files[step['file_keys'][u]]
                assert f['cohort']==record.cohort and f['scene']==record.scene and f['segment']==t
                assert f['rung']==decision['rungs'][u]
                assert receipt['received']==receipt['bytes']==f['bytes']==step['file_bytes'][u]
                assert receipt['sha256']==f['sha256']==step['file_sha256'][u] and receipt['valid']
                assert abs(receipt['verified_at']-row['origin_monotonic']-step['arrivals'][u])<1e-8
                assert receipt['verified_at']<=receipt['acknowledged_at']
                receipts+=1
            assert step['deadline_met']==(max(step['arrivals'])-step['start']<=9.5)
            metrics=state.deliver(record,t,decision,step['arrivals'],step['end'])
            for k,v in metrics.items(): equal(encode(v),step[k])
        final=state.final()
        for k,v in final.items(): equal(v,row[k])
        assert state.spent<=reserve(record)
        misses=sum(not r['deadline_met'] for r in row['rounds']); assert misses==row['deadline_misses']
        if rate==1500: nominal_misses+=misses
        else: stress_misses+=misses
        scientific.append({'key':row['key'],'policy':policy,'rate_kbit':rate,**final,'deadline_misses':misses})
    return {'passed':True,'episodes':len(rows),'verified_receipts':receipts,'nominal_rounds':96,'stress_rounds':24,
            'nominal_deadline_misses':nominal_misses,'stress_deadline_misses':stress_misses,
            'scientific_sha256':hashlib.sha256(canonical(scientific)).hexdigest()}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--live',action='store_true'); p.add_argument('--save')
    a=p.parse_args(); directory=ROOT/'causal_playback/results'/('live_v1' if a.live else 'replay_v1')
    if a.save and (Path(a.save).name!=a.save or not a.save.endswith('.json')): p.error('local JSON name required')
    result=(verify_live if a.live else verify_replay)(directory)
    result.update({'python':platform.python_version(),'platform':platform.platform()})
    if a.save:
        with (directory/a.save).open('x') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))
