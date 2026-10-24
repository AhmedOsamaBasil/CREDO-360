"""Final independent audit; permits the measured initial-segment PTS offset.

The first post-run checker assumed every MP4 started at zero. Segment0 has
a first-presentation timestamp of 0.1s; all recovery segments start at zero.
The frozen checker is retained for provenance; its clock_ledger recursion is
reused. No policy, outcome, media record or experiment metadata is rewritten.
"""
import argparse
import gzip
import json
from pathlib import Path
import platform
import re
from causal_playback.data import ROOT,load,pool
from causal_playback.check_support import clock_ledger
from reserve_recovery.run import sha


def audit():
    directory=ROOT/'causal_playback/results'
    manifest=json.loads((ROOT/'causal_playback/data/media_manifest.json').read_text())
    media=json.loads((directory/'media_audit.json').read_text())
    assert media['passed'] and media['manifest_sha256']==sha(ROOT/'causal_playback/data/media_manifest.json')
    assert media['auditor_sha256']==sha(ROOT/'causal_playback/media_audit.py')
    assert len(media['rows'])==len(manifest['files'])==216
    for r in media['rows']:
        assert r['frames']==(299 if r['segment']==5 and r['scene']=='River01' else 300)
        assert abs(r['duration_seconds']-r['frames']/30)<1e-6
        assert r['start_seconds']==(.1 if r['segment']==0 else 0)
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
            'initial_media_pts_offset_seconds':.1,'recovery_media_pts_offset_seconds':0,
            'duration_sensitivity':'Only River01 final duration differs: completion 1/30 second earlier, no stall/action/debt change.',
            'clock_diagnostics':clocks}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--save'); a=p.parse_args()
    result=audit(); result.update({'python':platform.python_version(),'platform':platform.platform()})
    if a.save:
        if Path(a.save).name!=a.save or not a.save.endswith('.json'): p.error('local JSON name required')
        with (ROOT/'causal_playback/results'/a.save).open('x') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps({k:v for k,v in result.items() if k!='clock_diagnostics'},indent=2))
