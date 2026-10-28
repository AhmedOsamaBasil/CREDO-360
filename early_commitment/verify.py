"""Source-bound replay plus independent time, resource and optimizer checks."""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import platform
from itertools import product
from early_commitment.run import ROOT,OUT,DATA,contexts,analysis,report
from causal_playback.core import menu
from service_opportunity.model import brute
from reserve_recovery.run import canonical,encode,sha


def audit(rows,records):
    records={r.key:r for r in records}; decisions=0; brute_queries=0
    for row in rows:
        record=records[row['key']]; finishes=[0.,0.]; used=0; previous=[]
        credit=0
        for rr in row['rounds']:
            t=rr['segment']; a=rr['decision']; sizes=rr['file_bytes']
            assert tuple(sizes)==tuple(record.costs[t][j] for j in a['rungs'])
            assert min(a['rungs'])>=2 and sum(sizes)<=1_500_000
            used+=max(0,sum(sizes)-2*record.costs[t][2]); assert used<=row['reserve_bytes']
            for u in (0,1):
                finish=max(finishes[u],rr['arrivals'][u])+10
                assert abs(finish-rr['play_end'][u])<1e-8
                assert rr['start']>=rr['prior_boundary'] and rr['arrivals'][u]>=rr['start']+.13
                allowed=[19]
                for prior in previous:
                    end=prior['play_end'][u]
                    if row['policy'].startswith('prefix_'):
                        count=max(0,min(10,int((rr['start']-(end-10)-row['delay']-.5+1e-10)//1)+1))
                        if count: allowed.append(prior['segment']*10+count-1)
                    elif end+row['delay']<=rr['start']+1e-10: allowed.append(prior['segment']*10+9)
                assert rr['visible_indices'][u]==max(allowed)
                finishes[u]=finish
            q=record.quality[t][0][a['rungs'][0]]; ref=record.quality[t][0][2]
            credit+=max(0,q-ref); previous.append(rr); decisions+=1
            # Independent complete Cartesian optimization for all primary decisions.
            if row['policy']=='prefix_mpc' and row['delay']==.08:
                ps=tuple(menu(q,record.costs[s]) for s,q in enumerate(rr['predicted_menus'],t))
                g,c,path=brute(ps,a['estimated_debt'],row['reserve_bytes']-(used-a['extra_bytes']))
                assert (g,c,path)==(a['planned_gain'],a['planned_extra_bytes'],tuple(tuple(x) for x in a['planned_rungs']))
                brute_queries+=1
        assert used==row['extra_bytes']
        assert row['actual_credit_units']==min(record.loss,credit)
        assert row['half_repaid']==(2*min(record.loss,credit)>=record.loss)
        assert abs(row['unpaid_fraction']-(record.loss-min(record.loss,credit))/record.loss)<1e-12
        for u in (0,1): assert abs(finishes[u]-40-row['stall_seconds'][u])<1e-8
    return {'decisions_audited':decisions,'independent_cartesian_queries':brute_queries}


def verify():
    meta=json.loads((OUT/'metadata.json').read_text())
    for field in ('source_sha256','input_sha256'):
        for n,h in meta[field].items(): assert sha(ROOT/n)==h,n
    for n,h in meta['result_sha256'].items(): assert sha(OUT/n)==h,n
    prep=json.loads((DATA/'metadata.json').read_text())
    assert prep['script_sha256']==sha(ROOT/'early_commitment/prepare.py')
    assert prep['result_sha256']==sha(DATA/'forecasts.json.gz')
    assert prep['feedback_source_sha256']==sha(ROOT/'feedback_opportunity/feedback.py')
    assert prep['map_metadata_sha256']==sha(ROOT/'feedback_opportunity/data/maps_v1/metadata.json')
    result=encode(analysis(True))
    with gzip.open(OUT/'results.json.gz','rt') as f: assert result==json.load(f)
    assert report(result)==(OUT/'REPORT.md').read_text()
    digest=hashlib.sha256(canonical(result)).hexdigest(); assert digest==meta['scientific_sha256']
    checked=audit(result['rows'],contexts()[0])
    return {'passed':True,'scientific_sha256':digest,'episode_runs':len(result['rows']),**checked,
            'practical_screen_passed':result['screen']['passed'],'python':platform.python_version(),'platform':platform.platform()}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--save'); a=p.parse_args(); result=verify()
    if a.save:
        if Path(a.save).name!=a.save or not a.save.endswith('.json'): p.error('JSON basename required')
        with (OUT/a.save).open('x') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))
