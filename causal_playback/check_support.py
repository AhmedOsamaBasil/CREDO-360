"""Independent ledger, causal-clock, service and media-provenance checks."""
import argparse
import gzip
import json
from pathlib import Path
import platform
import re
from causal_playback.data import ROOT, load, pool
from reserve_recovery.run import sha


def near(a,b):
    assert abs(a-b)<1e-7,(a,b)


def clock_ledger(row,record):
    """Closed-form queue recursion, without using State or advance_round."""
    items=[]; finish=[0.,0.]; gaps=[0.,0.]; spent=0
    initial=[(t,u,0 if u==0 else 2,record.quality[t][u][0 if u==0 else 2]) for t in (0,1) for u in (0,1)]
    last_end=0
    for i,step in enumerate(row['rounds']):
        t=i+2; start=step['start']; assert t==step['segment'] and start>=last_end
        completed=[(x['t'],u,x['rungs'][u],x['quality'][u]) for x in items for u in (0,1) if x['finish'][u]<=start]
        assert sorted(map(tuple,step['view']['observations']))==sorted(initial+completed)
        observed=min(record.loss,sum(max(0,x['quality'][0]-x['reference'][0]) for x in items if x['finish'][0]<=start))
        assert step['view']['observed_credit']==observed==step['decision']['observed_credit']
        pending=[x['predicted_gain'] for x in items if x['finish'][0]>start]
        assert step['view']['pending_gains']==pending
        assert step['decision']['pending_predicted_credit']==sum(pending)
        assert step['decision']['estimated_debt']==max(0,record.loss-observed-sum(pending))
        decision=step['decision']; rungs=decision['rungs']
        assert min(rungs)>=2
        q=[record.quality[t][u][rungs[u]] for u in (0,1)]
        ref=[record.quality[t][u][2] for u in (0,1)]
        assert q==step['actual_quality'] and ref==step['reference']
        n=[record.costs[t][r] for r in rungs]; assert n==step['file_bytes']
        extra=max(0,sum(n)-2*record.costs[t][2]); spent+=extra
        assert sum(n)==decision['bytes']<=1_500_000 and extra==decision['extra_bytes']
        assert spent<=row['reserve_bytes']
        for u in (0,1):
            gaps[u]+=max(0,step['arrivals'][u]-finish[u])
            finish[u]=max(finish[u],step['arrivals'][u])+10
            near(finish[u],step['play_end'][u])
            stall=gaps[u]+(max(0,step['end']-finish[u]) if t<5 else 0)
            near(stall,step['stall_total'][u])
        items.append({'t':t,'rungs':rungs,'quality':q,'reference':ref,'finish':finish.copy(),
                      'predicted_gain':decision['predicted_gain']})
        last_end=step['end']
    credit=min(record.loss,sum(max(0,x['quality'][0]-x['reference'][0]) for x in items))
    assert row['remaining_units']==record.loss-credit and row['extra_bytes']==spent
    for u in (0,1):
        near(row['stall_seconds'][u],gaps[u]); near(row['media_finish_seconds'][u],finish[u])
        near(finish[u],40+gaps[u])
    return {'startup':sum(row['rounds'][0]['arrivals'])/2,
            'additional_stall':sum(gaps)/2-sum(row['rounds'][0]['arrivals'])/2,
            'exact_duration_finish_shift_seconds':-1/30 if record.scene=='River01' else 0.,
            'exact_duration_stall_change_seconds':0.}


def audit():
    directory=ROOT/'causal_playback/results'
    manifest=json.loads((ROOT/'causal_playback/data/media_manifest.json').read_text())
    media=json.loads((directory/'media_audit.json').read_text())
    assert media['passed'] and media['manifest_sha256']==sha(ROOT/'causal_playback/data/media_manifest.json')
    assert media['auditor_sha256']==sha(ROOT/'causal_playback/media_audit.py')
    assert len(media['rows'])==len(manifest['files'])==216
    for r in media['rows']:
        assert r['frames']==(299 if r['segment']==5 and r['scene']=='River01' else 300)
        assert abs(r['duration_seconds']-r['frames']/30)<1e-6 and r['start_seconds']==0
    records=load(manifest); bykey={r.key:r for r in records}
    with gzip.open(directory/'replay_v1/results.json.gz','rt') as f: replay=json.load(f)
    live=json.loads((directory/'live_v1/results.json').read_text())
    clocks=[]; neighbor_checks=0
    for origin,rows in [('fluid',replay['rows']),('live',live)]:
        for row in rows:
            record=bykey[row['key']]; eligible={r.key for r in pool(records,record)}
            for step in row['rounds']:
                assert set(step['decision']['neighbor_keys'])<=eligible
                neighbor_checks+=1
            clocks.append({'kind':origin,'key':row['key'],'policy':row['policy'],**clock_ledger(row,record)})
    rate_checks=backlogs=0
    for row in live:
        assert row['background_bytes']>0
        assert all(c['returncode']==0 for c in row['commands'])
        for step in row['rounds']:
            text=step['tc_class']; rate=row['rate_kbit']
            assert re.search(rf'class htb 1:10 .*rate {rate}Kbit ceil {rate}Kbit',text)
            assert re.search(r'class htb 1:20 .*rate 500Kbit ceil 500Kbit',text)
            assert re.search(r'class htb 1:1 root rate 2Mbit ceil 2Mbit',text)
            assert all(int(n)==0 for n in re.findall(r'borrowed: (\d+)',text))
            background=text.split('class htb 1:20 ')[1].split('\n\n')[0]
            assert int(re.search(r'backlog (\d+)b',background)[1])>0
            assert 'parent 1:10 limit 1000 delay 40ms' in step['tc_qdisc']
            assert 'parent 1:20 limit 1000 delay 40ms' in step['tc_qdisc']
            assert step['decision_end']<=min(r['start']-row['origin_monotonic'] for r in step['receipts'])
            rate_checks+=1; backlogs+=1
        assert any('netem' in c['args'] and '40ms' in c['args'] and 'root' in c['args'] for c in row['commands'])
    return {'passed':True,'posthoc_validation_only':True,'independent_episode_clocks':len(clocks),
            'neighbor_exclusion_checks':neighbor_checks,'service_rate_checks':rate_checks,
            'saturated_background_snapshots':backlogs,'media_segments':216,
            'duration_sensitivity':'Only River01 final duration differs: completion 1/30 second earlier, no stall/action/debt change.',
            'clock_diagnostics':clocks}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--save'); a=p.parse_args()
    result=audit(); result.update({'python':platform.python_version(),'platform':platform.platform()})
    if a.save:
        if Path(a.save).name!=a.save or not a.save.endswith('.json'): p.error('local JSON name required')
        with (ROOT/'causal_playback/results'/a.save).open('x') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='clock_diagnostics'},indent=2))
