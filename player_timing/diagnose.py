"""Post-outcome diagnostics, independent raw ledgers, and presentation tables."""
import argparse
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from pathlib import Path
from statistics import mean,median
from metric_contract.data import ROOT
from metric_contract.run import canonical,sha
from player_timing.replay import OUT as REPLAY
from player_timing.audit import OUT as AUDIT, RAW

OUT=ROOT/'player_timing/results/diagnostics_v2'


def read(path):
    with gzip.open(path,'rt') as stream:return json.load(stream)


def scalar_score(case,ends,chunk=False):
    credit=0;complete=0
    if chunk:
        for i,u in enumerate(case['units']):
            if ends[i] is not None and ends[i]<=40+1e-9:
                credit+=case['chunk_gains'][i];complete+=1
        floors=case['chunk_floor_violations']
    else:
        for p in range(4):
            ts=[ends[i] for i,u in enumerate(case['units']) if u['parent']==p]
            if all(t is not None and t<=40+1e-9 for t in ts):
                credit+=case['parent_gains'][p];complete+=1
        floors=case['parent_floor_violations']
    return {'credit':credit,'half':2*credit>=case['loss'],
            'protected_half':2*credit>=case['loss'] and not sum(floors),
            'completed_units':complete}


def check_scalar(case,ends,saved):
    for chunk,name in ((False,'original_parent_account'),(True,'secondary_chunk_account')):
        value=scalar_score(case,ends,chunk)
        for key in value:
            if value[key]!=saved[name][key]:raise ValueError('Independent raw ledger differs')


def stats(xs):
    return {'mean':mean(xs),'median':median(xs),'minimum':min(xs),'maximum':max(xs)} if xs else None


def raw_crosschecks(raw,case):
    """Additional post-hoc conservation checks, separate from the frozen audit."""
    server=raw['server'];previous=0.
    for batch in server['batches']:
        if batch['interval_start']<previous-1e-8:
            raise ValueError('Overlapping service-credit intervals')
        previous=batch['at']
    expected={f'{j}:{u}':f['bytes'] for j,unit in enumerate(case['units'])
              for u,f in enumerate(unit['files'])}
    if case['control']=='background':expected['background']=6000000
    transfers={r['id']:r for r in server['transfers']}
    if set(expected)!=set(transfers):raise ValueError('Server payload set differs')
    for key,n in expected.items():
        r=transfers[key];extra=40 if case['control']=='late_recipient' and key=='0:0' else 0
        if r['bytes']!=n or r['completed'] is None:
            raise ValueError('Incomplete/mismatched server payload')
        if abs(r['eligible']-r['request']-.13-extra)>1e-8:
            raise ValueError('Server setup/control changed')
    segments={(r['j'],r['u']):r for user in raw['browser']['segments'] for r in user}
    for report in server['reports']:
        r=segments[report['j'],report['u']]
        if any(report[k]!=r[k] for k in ('ended','reportReady')):
            raise ValueError('Client/server report differs')
    if case['buffered']:
        gates=[e for e in raw['browser']['events'] if e['type']=='buffer_gate']
        if sorted(e['u'] for e in gates)!=[0,1]:raise ValueError('Missing shared buffer gate')
        for e in gates:
            if segments[0,e['u']]['load']<e['at']:raise ValueError('Playback precedes gate')
    return {'nonoverlapping_service_intervals':len(server['batches']),
            'server_payload_identities':len(expected),'client_server_report_matches':len(segments)}


def analysis():
    replay=read(REPLAY/'results.json.gz');audit=read(AUDIT/'results.json.gz')
    cases=json.loads((REPLAY/'schedule.json').read_text())
    checks=Counter();groups=defaultdict(list)
    for case in replay['rows']:
        check_scalar(case,[r[0] for r in case['ideal']['ends']],case['ideal']);checks['analytical_ledgers']+=2
        excess=sum(max(0,sum(a)-sum(b)) for a,b in zip(case['sizes'],case['baseline_sizes']))
        if excess!=case['resource']['extra_bytes']:raise ValueError('Independent extra-byte ledger')
        checks['resource_ledgers']+=1
        groups[case['key'],case['policy'],case['buffered']].append(case)
    effects=[]
    for (key,policy,buffered),rs in sorted(groups.items()):
        a=next(r for r in rs if r['unit_seconds']==10);b=next(r for r in rs if r['unit_seconds']==2)
        effects.append({'key':key,'policy':policy,'buffered':buffered,
            'finish_difference_seconds':b['ideal']['ends'][-1][0]-a['ideal']['ends'][-1][0],
            'parent_credit_difference':b['ideal']['original_parent_account']['credit']-a['ideal']['original_parent_account']['credit'],
            'parent_completed_difference':b['ideal']['original_parent_account']['completed_units']-a['ideal']['original_parent_account']['completed_units'],
            'chunk_vs_parent_credit_difference':b['ideal']['secondary_chunk_account']['credit']-b['ideal']['original_parent_account']['credit'],
            'protected_changed':b['ideal']['original_parent_account']['resource_protected_half']!=a['ideal']['original_parent_account']['resource_protected_half'],
            'extra_bytes_difference':b['resource']['extra_bytes']-a['resource']['extra_bytes']})
    rawhashes={};aligned=[];decoder=Counter();measured={};callbacktotal=0;tail=0;gaps=0;allservice=0
    timing=[];score_agreement=[];realized=[];dropped=0
    for result,case in zip(audit['rows'],cases):
        if not result['valid']:continue
        rawpath=RAW/f"session_{case['index']:02}.json.gz";raw=read(rawpath);rawhashes[rawpath.name]=sha(rawpath)
        checks.update(raw_crosschecks(raw,case))
        segs=raw['browser']['segments'][0];ends=[s['ended']/1000 for s in segs];reports=[s['reportReady']/1000 for s in segs]
        check_scalar(case,ends,result['ended_score']);check_scalar(case,reports,result['report_available_score']);checks['measured_ledgers']+=4
        origin=min(r['request'] for r in raw['browser']['receipts'])/1000
        shifted=scalar_score(case,[t-origin for t in ends]);unshifted=scalar_score(case,ends)
        shifted_chunk=scalar_score(case,[t-origin for t in ends],True)
        unshifted_chunk=scalar_score(case,ends,True)
        aligned.append({'index':case['index'],'first_request_offset_ms':origin*1000,
            'parent_credit_change':shifted['credit']-unshifted['credit'],'half_change':shifted['half']!=unshifted['half'],
            'chunk_credit_change':shifted_chunk['credit']-unshifted_chunk['credit'],
            'chunk_half_change':shifted_chunk['half']!=unshifted_chunk['half']})
        realized.append({'index':case['index'],'scene':case['scene'],'policy':case['policy'],
            'unit_seconds':case['unit_seconds'],'buffered':case['buffered'],'control':case['control'],
            'finish_minus_ideal_seconds':result['stats'][0]['finish_seconds']-case['ideal']['ends'][-1][0],
            'parent_credit_minus_ideal':result['ended_score']['original_parent_account']['credit']-case['ideal']['original_parent_account']['credit'],
            'parent_repaid_minus_ideal':result['ended_score']['original_parent_account']['fraction_repaid']-case['ideal']['original_parent_account']['fraction_repaid'],
            'measured_parent_ends':result['ended_score']['parent_ends'],
            'ideal_parent_ends':case['ideal']['parent_ends'],
            'measured_completed_parents':result['ended_score']['original_parent_account']['completed_units'],
            'ideal_completed_parents':case['ideal']['original_parent_account']['completed_units']})
        score_agreement.append({'index':case['index'],
            'ended_report_equal':result['ended_score']==result['report_available_score'],
            'ended_tail_equal':result['ended_score']==result['tail_witness_score'],
            'ended_report_parent_credit_equal':result['ended_score']['original_parent_account']['credit']==result['report_available_score']['original_parent_account']['credit'],
            'ended_tail_parent_credit_equal':result['ended_score']['original_parent_account']['credit']==result['tail_witness_score']['original_parent_account']['credit'],
            'ended_report_chunk_credit_equal':result['ended_score']['secondary_chunk_account']['credit']==result['report_available_score']['secondary_chunk_account']['credit'],
            'ended_tail_chunk_credit_equal':result['ended_score']['secondary_chunk_account']['credit']==result['tail_witness_score']['secondary_chunk_account']['credit']})
        for u,user in enumerate(raw['browser']['segments']):
            for j,s in enumerate(user):
                timing.append({'index':case['index'],'j':j,'u':u,
                    'load_to_end_extra_ms':s['ended']-s['load']-s['duration']*1000,
                    'report_ready_extra_ms':s['reportReady']-s['ended'],
                    'ack_extra_ms':s['reportAck']-s['reportReady'],
                    'expected_source_frames':case['units'][j]['files'][u]['frames'],
                    'observed_callbacks':s['frameCount']})
        for event in raw.get('mediaProperties',[]):
            for p in event['properties']:
                if p['name'] in ('kVideoDecoderName','kIsPlatformVideoDecoder'):decoder[p['name'],p['value']]+=1
        callbacktotal+=result['callback_count'];tail+=result['missing_tail_witnesses'];gaps+=result['callback_gaps'];allservice+=result['payload_bytes_sent']
        dropped+=result['reported_dropped_frames']
        if result['control']=='none':measured[result['scene'],result['policy'],result['unit_seconds'],result['buffered']]=result
    measured_effects=[]
    for scene,policy,u,b in sorted(measured):
        if u!=2 or (scene,policy,10,b) not in measured:continue
        a=measured[scene,policy,10,b];z=measured[scene,policy,2,b]
        measured_effects.append({'scene':scene,'policy':policy,'buffered':b,
            'finish_difference_seconds':z['stats'][0]['finish_seconds']-a['stats'][0]['finish_seconds'],
            'parent_repaid_difference':z['ended_score']['original_parent_account']['fraction_repaid']-a['ended_score']['original_parent_account']['fraction_repaid'],
            'chunk_repaid_difference':z['ended_score']['secondary_chunk_account']['fraction_repaid']-a['ended_score']['secondary_chunk_account']['fraction_repaid']})
    effect_summary=[]
    for p in ('cost_greedy','rolling_nash','maxmin','baseline'):
        rs=[r for r in effects if r['policy']==p and not r['buffered']]
        effect_summary.append({'policy':p,'episodes':len(rs),'finish_2s_minus_10s':stats([r['finish_difference_seconds'] for r in rs]),
            'changed_original_credit':sum(r['parent_credit_difference']!=0 for r in rs),
            'changed_original_completed_count':sum(r['parent_completed_difference']!=0 for r in rs),
            'changed_protected_half':sum(r['protected_changed'] for r in rs),
            'extra_bytes_difference':stats([r['extra_bytes_difference'] for r in rs])})
    return {'posthoc':True,'checks':dict(checks),'replay_effects':effects,'replay_summary':effect_summary,
        'measured_effects':measured_effects,'clock_alignment':aligned,'callbacks':callbacktotal,
        'segment_timing':timing,'score_agreement':score_agreement,'measured_versus_ideal':realized,
        'callback_gaps':gaps,'missing_tail_witnesses':tail,'payload_bytes':allservice,
        'reported_dropped_frames':dropped,
        'decoder_properties':[{'property':k,'value':v,'observations':n} for (k,v),n in sorted(decoder.items())],
        'failed_sessions':[r for r in audit['rows'] if not r['valid']]},rawhashes


def report(diag):
    rep=read(REPLAY/'results.json.gz');aud=read(AUDIT/'results.json.gz')
    lines=['# Exposed matched-path timing results','',
        'Original parent credit and the secondary chunk account remain distinct. Six scenes,',
        '28 reused identities; 168 exposed episodes, not 2,688 independent trials.','',
        '## Analytical replay','',
        '| Path | Unit | Buffered | Parent protected half /168 | Chunk protected half /168 | Recipient finish s |',
        '|---|---:|---|---:|---:|---:|']
    for r in rep['summary']:
        if r['scene']=='all':lines.append(f"| {r['policy']} | {r['unit_seconds']} | {r['buffered']} | {r['original_parent_account']['protected_half']} | {r['secondary_chunk_account']['protected_half']} | {r['mean_recipient_finish']:.3f} |")
    lines+=['','## Browser measurements','',f"Valid audited sessions: {aud['valid']}/{aud['sessions']}; failures remain in the raw artifacts.",'',
        '| Path | Unit | Buffered | Sessions | Parent protected half | Chunk protected half | Recipient finish s |',
        '|---|---:|---|---:|---:|---:|---:|']
    for r in aud['summary']:lines.append(f"| {r['policy']} | {r['unit_seconds']} | {r['buffered']} | {r['sessions']} | {r['parent_half']} | {r['chunk_half']} | {r['mean_recipient_finish']:.3f} |")
    lines+=['',f"Recorded video callbacks: {diag['callbacks']:,}. Callback sequence gaps: {diag['callback_gaps']:,}. Missing final-tail witnesses: {diag['missing_tail_witnesses']:,}.",
        f"Summed per-file browser dropped-frame counters: {diag['reported_dropped_frames']:,}. Callback gaps and these counters are different quantities, neither a physical pixel audit.",
        f"Controlled payload bytes served: {diag['payload_bytes']:,}. These are not physical link-capacity measurements.",'',
        '## Controls','']
    for r in aud['rows']:
        if r.get('valid') and r.get('control')!='none':lines.append(f"- {r['control']}: original parent repayment {100*r['ended_score']['original_parent_account']['fraction_repaid']:.3f}%; recipient finish {r['stats'][0]['finish_seconds']:.3f}s; served {r['payload_bytes_sent']} payload bytes.")
    lines+=['','## Independent checks','',f"{diag['checks']}",'',
        'The first-request offset from the browser run epoch is also retained. Realigning',
        f"the deadline changes parent credit in {sum(r['parent_credit_change']!=0 for r in diag['clock_alignment'])} sessions and half classification in {sum(r['half_change'] for r in diag['clock_alignment'])} sessions.",
        f"The secondary chunk credit changes in {sum(r['chunk_credit_change']!=0 for r in diag['clock_alignment'])} sessions and chunk half classification in {sum(r['chunk_half_change'] for r in diag['clock_alignment'])} sessions.",
        '', 'No physical pixel/HMD measurement, subjective QoE, new controller, new holdout,',
        'or general optimality for shorter-segment actions is established.']
    return '\n'.join(lines)+'\n'


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    result,raw=analysis();txt=report(result)
    meta={'script_sha256':sha(Path(__file__)),'replay_sha256':sha(REPLAY/'results.json.gz'),
        'audit_sha256':sha(AUDIT/'results.json.gz'),'raw_sha256':raw,
        'scientific_sha256':hashlib.sha256(canonical(result)).hexdigest()}
    if a.verify:
        if read(OUT/'results.json.gz')!=result or json.loads((OUT/'metadata.json').read_text())!=meta or (OUT/'REPORT.md').read_text()!=txt:raise ValueError('Diagnostic replay changed')
    else:
        OUT.mkdir(parents=True,exist_ok=False)
        (OUT/'results.json.gz').write_bytes(gzip.compress(canonical(result),mtime=0))
        (OUT/'metadata.json').write_bytes(canonical(meta));(OUT/'REPORT.md').write_text(txt,encoding='utf-8')
    print(json.dumps({'sha256':meta['scientific_sha256'],'checks':result['checks'],'verified':a.verify}))


if __name__=='__main__':main()
