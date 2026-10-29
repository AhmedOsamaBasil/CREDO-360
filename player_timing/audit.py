"""Independent raw-event validation and offline completion accounting."""
import argparse
from collections import Counter,defaultdict
import gzip
import hashlib
import json
from statistics import mean
from metric_contract.data import ROOT
from metric_contract.run import canonical,sha
from player_timing.core import scores,tail_witness
from player_timing.replay import provenance,OUT as REPLAY

RAW=ROOT/'player_timing/results/browser_v2'
OUT=ROOT/'player_timing/results/audit_v2'


def audit_service(server):
    transfers={t['id']:t for t in server['transfers']}
    if len(transfers)!=len(server['transfers']):raise ValueError('Duplicate transfer')
    totals=Counter();previous=-1.;fraction=0.;maximum_quantum=0
    for batch in server['batches']:
        at,start=batch['at'],batch['interval_start']
        if at<previous or start>at or at-start>.02000001:raise ValueError('Service clock')
        credit=150000*(at-start)+fraction;budget=int(credit+1e-7);fraction=credit-int(credit)
        # Unreported idle ticks reset fractional credit; allow at most one byte.
        if abs(batch['budget']-budget)>1:raise ValueError('Service rate bound')
        sent=sum(batch['sent'].values());maximum_quantum=max(maximum_quantum,sent)
        if sent>batch['budget'] or sent<0:raise ValueError('Burst beyond generated service')
        for key,n in batch['sent'].items():
            if key not in transfers or n<=0 or at+1e-8<transfers[key]['eligible']:raise ValueError('Invalid/early service')
            totals[key]+=n
        previous=at
    for key,t in transfers.items():
        if totals[key]>t['bytes']:raise ValueError('Payload duplicated')
        if t['completed'] is not None and totals[key]!=t['bytes']:raise ValueError('Premature server completion')
        if t['eligible']<t['request']+.13-1e-8:raise ValueError('Setup omitted')
    return {'payload_bytes_sent':sum(totals.values()),'max_batch_bytes':maximum_quantum,
            'transfers':len(transfers),'service_batches':len(server['batches'])}


def audit_session(raw,case):
    if raw['status']!='completed':
        return {'index':case['index'],'key':case['key'],'valid':False,'status':raw['status'],'error':raw.get('error')}
    for k in ('index','key','policy','unit_seconds','buffered','control'):
        if raw[k]!=case[k]:raise ValueError('Schedule identity changed')
    service=audit_service(raw['server']);b=raw['browser'];n=len(case['units'])
    if b['error'] or raw['pageErrors'] or len(b['receipts'])!=2*n:raise ValueError('Incomplete/error session')
    receipts={(r['j'],r['u']):r for r in b['receipts']}
    if len(receipts)!=2*n:raise ValueError('Duplicate receipt')
    for (j,u),r in receipts.items():
        f=case['units'][j]['files'][u]
        if (r['bytes'],r['sha256'])!=(f['bytes'],f['sha256']):raise ValueError('Payload identity')
        if not 0<=r['request']<=r['headers']<=r['receipt']<=r['ready']:raise ValueError('Receipt event order')
        if j:
            previous=[receipts[j-1,v] for v in (0,1)]
            # Browser requests can be submillisecond staggered; use earliest pair entry.
            earliest=min(p['request'] for p in previous)
            if r['request']+3<max(earliest+case['unit_seconds']*1000,max(p['ready'] for p in previous)):
                raise ValueError('Request cadence/receipt dependency violated')
    ends=[[None,None] for _ in range(n)];reported=[[None,None] for _ in range(n)];tails=[[None,None] for _ in range(n)]
    callbacks=missed=missing_tail=0;late=[];processing=[];dropped=0;stats=[]
    for u in (0,1):
        if len(b['segments'][u])!=n:raise ValueError('Incomplete segment reports')
        previous=0.;first=None
        for j,s in enumerate(b['segments'][u]):
            f=case['units'][j]['files'][u];r=receipts[j,u]
            if (s['j'],s['u'])!=(j,u):raise ValueError('Reordered completion')
            if not r['ready']<=s['load']<=s['playRequest']<=s['playResolved']<=s['ended']<=s['reportReady']<=s['reportAck']:
                raise ValueError('Playback event ordering')
            if s['load']<previous or abs(s['duration']-f['duration'])>.002 or abs(s['currentTime']-f['duration'])>.002:
                raise ValueError('Overlapping/wrong media playback')
            previous=s['reportAck']
            frames=[x for x in b['frames'][u] if x['j']==j];callbacks+=len(frames)
            if len(frames)!=s['frameCount']:raise ValueError('Callback count')
            if not frames:missing_tail+=1
            for k,x in enumerate(frames):
                if not s['load']<=x['at']<=s['ended']+1 or x['mediaTime']<0 or x['mediaTime']>f['duration']:
                    raise ValueError('Callback outside playback')
                if k and (x['mediaTime']<frames[k-1]['mediaTime'] or x['at']<frames[k-1]['at'] or x['presentedFrames']<=frames[k-1]['presentedFrames']):
                    raise ValueError('Regressing callback')
                if k:missed+=max(0,x['presentedFrames']-frames[k-1]['presentedFrames']-1)
                late.append(x['at']-x['expectedDisplayTime'])
                if x['processingDuration'] is not None:processing.append(x['processingDuration'])
            witnessed=tail_witness(frames,f['frames'])
            if frames and not witnessed:missing_tail+=1
            if first is None and frames:first=frames[0]['at']/1000
            ends[j][u]=s['ended']/1000;reported[j][u]=s['reportReady']/1000
            tails[j][u]=s['ended']/1000 if witnessed else None
            if s['playbackQuality']:dropped+=s['playbackQuality']['droppedVideoFrames']
        stats.append({'startup_seconds':first,'finish_seconds':ends[-1][u],
            'media_seconds':sum(x['duration'] for x in case['units']),
            'completion_overhead_seconds':ends[-1][u]-sum(x['duration'] for x in case['units'])})
    if len(raw['server']['reports'])!=2*n:raise ValueError('Missing server reports')
    if Counter((r['j'],r['u']) for r in raw['server']['reports'])!=Counter(receipts.keys()):raise ValueError('Report identities')
    gate_entries=[e for e in b['events'] if e['type']=='buffer_gate']
    if case['buffered']:
        total=0.;cut=0
        while total<4-1e-9:total+=case['units'][cut]['duration'];cut+=1
        gate=max(receipts[j,u]['ready'] for j in range(cut) for u in (0,1))
        if any(e['at']<gate for e in gate_entries):raise ValueError('Free prebuffer')
    result=scores(case,ends,case['resource']);report=scores(case,reported,case['resource']);tail=scores(case,tails,case['resource'])
    if case['control']=='late_recipient' and result['original_parent_account']['credit']!=0:raise ValueError('Late control falsely credited')
    return {**{k:case[k] for k in ('index','key','scene','policy','unit_seconds','buffered','control')},
            'valid':True,'status':'completed','callback_count':callbacks,'callback_gaps':missed,
            'missing_tail_witnesses':missing_tail,'reported_dropped_frames':dropped,
            'max_callback_lateness_ms':max(late) if late else None,
            'max_decode_processing_seconds':max(processing) if processing else None,
            'stats':stats,'ended_score':result,'report_available_score':report,'tail_witness_score':tail,
            'ideal':case['ideal'],'resource':case['resource'],**service}


def analysis():
    meta=json.loads((RAW/'metadata.json').read_text());current=provenance()
    for k,v in current.items():
        if meta['method'][k]!=v:raise ValueError('Frozen measurement dependency changed')
    if meta['schedule_sha256']!=sha(REPLAY/'schedule.json'):raise ValueError('Schedule changed')
    schedule=json.loads((REPLAY/'schedule.json').read_text())
    completion=json.loads((RAW/'completion.json').read_text())
    if [r['index'] for r in completion]!=list(range(74)):raise ValueError('Incomplete batch')
    rows=[];hashes={}
    for case in schedule:
        p=RAW/f"session_{case['index']:02}.json.gz"
        with gzip.open(p,'rt') as f:raw=json.load(f)
        try:row=audit_session(raw,case)
        except (ValueError,KeyError,TypeError) as e:
            row={'index':case['index'],'key':case['key'],'valid':False,'status':'audit_failed','error':str(e)}
        rows.append(row);hashes[p.name]=sha(p)
    groups=defaultdict(list)
    for r in rows:
        if r['valid'] and r['control']=='none':groups[r['policy'],r['unit_seconds'],r['buffered']].append(r)
    summary=[]
    for (p,u,b),rs in sorted(groups.items()):
        summary.append({'policy':p,'unit_seconds':u,'buffered':b,'sessions':len(rs),
            'parent_half':sum(r['ended_score']['original_parent_account']['resource_protected_half'] for r in rs),
            'chunk_half':sum(r['ended_score']['secondary_chunk_account']['resource_protected_half'] for r in rs),
            'mean_parent_repaid':mean(r['ended_score']['original_parent_account']['fraction_repaid'] for r in rs),
            'mean_chunk_repaid':mean(r['ended_score']['secondary_chunk_account']['fraction_repaid'] for r in rs),
            'mean_recipient_finish':mean(r['stats'][0]['finish_seconds'] for r in rs),
            'missing_tail_witnesses':sum(r['missing_tail_witnesses'] for r in rs)})
    return {'scope':'headless compositor callbacks, controlled loopback payload service; not physical display/HMD',
            'rows':rows,'summary':summary,'valid':sum(r['valid'] for r in rows),'sessions':len(rows)},hashes


def main():
    p=argparse.ArgumentParser(__doc__);p.add_argument('--verify',action='store_true');a=p.parse_args()
    result,hashes=analysis();meta={'raw_sha256':hashes,'method':provenance(),
        'scientific_sha256':hashlib.sha256(canonical(result)).hexdigest()}
    if a.verify:
        with gzip.open(OUT/'results.json.gz','rt') as f:saved=json.load(f)
        if result!=saved or meta!=json.loads((OUT/'metadata.json').read_text()):raise ValueError('Audit changed')
    else:
        OUT.mkdir(parents=True,exist_ok=False)
        (OUT/'results.json.gz').write_bytes(gzip.compress(canonical(result),mtime=0))
        (OUT/'metadata.json').write_bytes(canonical(meta))
    print(json.dumps({'valid':result['valid'],'sessions':result['sessions'],'sha256':meta['scientific_sha256'],'verified':a.verify}))


if __name__=='__main__':main()
