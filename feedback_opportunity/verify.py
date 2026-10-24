"""Public scientific replay and optional private cross-language packet audit."""
import argparse
import base64
import csv
import gzip
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
from causal_compensation.data import ROOT,SOURCES
from feedback_opportunity.run import analysis
from feedback_opportunity.feedback import HEADER,MAGIC,mask,reconstruct
from reserve_recovery.run import sha,canonical,encode


def verify(private=False):
    directory=ROOT/'feedback_opportunity'; maps_dir=directory/'data/maps_v1'
    maps_meta=json.loads((maps_dir/'metadata.json').read_text())
    assert maps_meta['script_sha256']==sha(directory/'prepare.py')
    assert maps_meta['analysis_source_sha256']==sha(ROOT/'multimedia_testbed/prepare_qoevave.py')
    for n,h in maps_meta['files_sha256'].items(): assert sha(maps_dir/n)==h,n
    old={}
    for cohort,folder in SOURCES.items():
        for name in ('calibration_quality.csv','heldout_quality.csv'):
            with (ROOT/folder/name).open(newline='') as f:
                for r in csv.DictReader(f): old[cohort,r['content'],int(r['subject']),int(r['segment']),int(r['ladder_index'])]=float(r['vw_psnr_db'])
    parity=json.loads((maps_dir/'old_sampling_parity.json').read_text())
    parity_error=max(abs(r['psnr_db']-old[r['cohort'],r['scene'],r['subject'],r['segment'],r['rung']]) for r in parity)
    assert len(parity)==len(old)==6048 and parity_error<1e-8
    wire_dir=directory/'results/wire_v1'; wire_meta=json.loads((wire_dir/'metadata.json').read_text())
    assert wire_meta['map_metadata_sha256']==sha(maps_dir/'metadata.json')
    assert wire_meta['results_sha256']==sha(wire_dir/'results.json')
    for n,h in wire_meta['source_sha256'].items(): assert sha(ROOT/n)==h,n
    wire=json.loads((wire_dir/'results.json').read_text()); assert len(wire['rows'])==1008
    assert len({r['key'] for r in wire['rows']})==1008
    errors=[]; unit_errors=[]
    for r in wire['rows']:
        cohort,scene,sid,t=r['key'].split(':')
        assert r['status']==200 and r['payload_bytes']==140 and r['sequence']==r['segment']==int(t)
        assert r['selected_units']==r['quality_units'][r['rung']] and r['reference_units']==r['quality_units'][2]
        for j in range(6):
            actual=old[cohort,scene,int(sid),int(t),j]
            errors.append(abs(r['psnr_db'][j]-actual))
            expected=int(np.floor(np.clip(1+(actual-18)/6,1,5)*1000+.5))
            unit_errors.append(abs(r['quality_units'][j]-expected))
    assert all(r['status']==400 for r in wire['negative_probes'])
    checked=0
    if private:
        cache=ROOT/'.external/feedback_opportunity_v1'
        assert sha(cache/'client_events.json')==maps_meta['private_events_sha256']
        assert sha(cache/'client_packets.json')==wire_meta['packet_file_sha256']
        events=json.loads((cache/'client_events.json').read_text()); packets=json.loads((cache/'client_packets.json').read_text())
        byhash={s['descriptor']:np.load(maps_dir/s['map_file'])['mse'] for s in maps_meta['sources']}
        for event,packet,row in zip(events,packets,wire['rows']):
            assert event['key']==packet['key']==row['key']
            expected=HEADER.pack(MAGIC,bytes.fromhex(event['descriptor']),event['segment'],event['rung'],event['sequence'],event['mediaEnd'])
            expected+=b''.join(mask(e['yaw'],e['pitch']) for e in event['events'])
            actual=base64.b64decode(packet['packet']); assert expected==actual
            result=reconstruct(actual,byhash[event['descriptor']],event['descriptor'],event['segment'],event['sequence'])
            for key in result: assert result[key]==row[key]
            checked+=1
        assert checked==1008
    audit_dir=directory/'results/audit_v1'; meta=json.loads((audit_dir/'metadata.json').read_text())
    for field in ('source_sha256','input_sha256'):
        for n,h in meta[field].items(): assert sha(ROOT/n)==h,n
    assert sha(audit_dir/'results.json.gz')==meta['result_sha256']
    result=encode(analysis(True))
    with gzip.open(audit_dir/'results.json.gz','rt') as f: assert result==json.load(f)
    digest=hashlib.sha256(canonical(result)).hexdigest(); assert digest==meta['scientific_sha256']
    return {'passed':True,'private_packets_checked':checked,'public_feedback_messages':1008,
            'quality_values':6048,'old_sampling_max_error_db':parity_error,
            'causal_feedback_mae_db':float(np.mean(errors)),'causal_feedback_max_error_db':max(errors),
            'causal_feedback_mae_units':float(np.mean(unit_errors)),'causal_feedback_max_error_units':max(unit_errors),
            'enumerated_paths':sum(r['enumerated_paths'] for r in result['frontier']),
            'feedback_episode_runs':len(result['feedback_rows']),'scientific_sha256':digest,
            'practical_screen_passed':result['unchanged_practical_screen']['passed']}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--private',action='store_true'); p.add_argument('--save')
    a=p.parse_args(); result=verify(a.private); result.update({'python':platform.python_version(),'platform':platform.platform()})
    if a.save:
        if Path(a.save).name!=a.save or not a.save.endswith('.json'): p.error('local JSON name required')
        with (ROOT/'feedback_opportunity/results'/a.save).open('x') as f: json.dump(result,f,indent=2); f.write('\n')
    print(json.dumps(result,indent=2))
