"""Two isolated pilots at a time; actual causal choices, file receipts and clocks."""
import argparse
from concurrent.futures import ThreadPoolExecutor,as_completed
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time
from causal_playback.data import ROOT,load,pool
from causal_playback.core import LIVE_POLICIES
from causal_playback.clock import State
from causal_playback.replay import choose_step,reserve
from reserve_recovery.run import canonical,sha,encode


def cases(records):
    selected=sorted((r for r in records if r.recipient==1 and r.donor==2),key=lambda r:r.scene)
    result=[]
    for i,r in enumerate(selected):
        order=LIVE_POLICIES[i%4:]+LIVE_POLICIES[:i%4]
        result.extend((r,p,1500) for p in order)
    result.extend((r,'knn_recovery',750) for r in selected)
    return tuple(result)


def episode(index,record,training,policy,rate,manifest,cache,output):
    name=f'cp{os.getpid()}x{index}'; src=name+'s'; dst=name+'d'; left=f'ps{index}'; right=f'pd{index}'
    created=[]; processes=[]; commands=[]; rounds=[]; state=State(record); origin=None; result={}
    files={(r['cohort'],r['scene'],r['segment'],r['rung']):r for r in manifest['files']}
    logpath=output/f'episode_{index:02d}.jsonl'
    log=logpath.open('x',encoding='utf-8')
    def save(row): log.write(json.dumps(encode(row),sort_keys=True)+'\n'); log.flush()
    def command(args):
        r=subprocess.run(args,text=True,capture_output=True,timeout=90)
        commands.append({'args':args,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        if r.returncode: raise RuntimeError(f'{args}: {r.stderr}')
        return r.stdout
    def inside(ns,args): return command(['ip','netns','exec',ns]+args)
    def tc(args): return inside(src,['tc']+args)
    def worker(ns,mode):
        p=subprocess.Popen(['ip','netns','exec',ns,sys.executable,'-m','causal_playback.transport','--worker',mode],
                            stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        processes.append(p); return p
    try:
        existing=command(['ip','netns','list'])
        if src in existing.split() or dst in existing.split(): raise RuntimeError('namespace collision')
        for ns in (src,dst): command(['ip','netns','add',ns]); created.append(ns)
        command(['ip','link','add',left,'netns',src,'type','veth','peer','name',right,'netns',dst])
        for ns,dev,address in ((src,left,'10.233.55.1/30'),(dst,right,'10.233.55.2/30')):
            inside(ns,['ip','addr','add',address,'dev',dev]); inside(ns,['ip','link','set',dev,'up'])
            inside(ns,['ip','link','set','lo','up']); inside(ns,['ethtool','-K',dev,'tso','off','gso','off','gro','off'])
        tc(['qdisc','add','dev',left,'root','handle','1:','htb','default','20'])
        tc(['class','add','dev',left,'parent','1:','classid','1:1','htb','rate','2mbit','ceil','2mbit'])
        for minor,r in (('10',rate),('20',500)):
            tc(['class','add','dev',left,'parent','1:1','classid','1:'+minor,'htb','rate',f'{r}kbit',
                'ceil',f'{r}kbit','burst','3000','cburst','3000','quantum','1500'])
            tc(['qdisc','add','dev',left,'parent','1:'+minor,'handle',minor+':','netem','delay','40ms','limit','1000'])
        for port in (9201,9202,9204):
            tc(['filter','add','dev',left,'parent','1:','protocol','ip','prio','1','u32','match','ip',
                'dport',str(port),'0xffff','flowid','1:10'])
        inside(dst,['tc','qdisc','add','dev',right,'root','netem','delay','40ms'])
        receiver=worker(dst,'server')
        if receiver.stdout.readline().strip()!='ready': raise RuntimeError('receiver startup failure')
        background=worker(src,'background'); time.sleep(1)
        before=json.loads(inside(src,[sys.executable,'-m','causal_playback.transport','--worker','stats']))
        save({'type':'header','index':index,'key':record.key,'policy':policy,'rate_kbit':rate,
              'reserve_bytes':reserve(record),'loss_units':record.loss,'training_count':len(training)})
        origin=time.perf_counter()
        for t in range(2,6):
            start=time.perf_counter()-origin
            decision,info=choose_step(record,training,state,policy,t,start)
            decision_end=time.perf_counter()-origin
            selected=[files[record.cohort,record.scene,t,r] for r in decision['rungs']]
            paths=[str(cache/f['relative_path']) for f in selected]; hashes=[f['sha256'] for f in selected]
            payload=json.loads(inside(src,[sys.executable,'-m','causal_playback.transport','--worker','pair',
                                           '--files',*paths,'--hashes',*hashes]))
            arrivals=tuple(f['verified_at']-origin for f in payload['flows'])
            acknowledged=tuple(f['acknowledged_at']-origin for f in payload['flows'])
            payload_return=time.perf_counter()-origin
            class_state=tc(['-s','class','show','dev',left])
            qdisc=tc(['-s','qdisc','show','dev',left])
            wait=max(0,origin+start+10-time.perf_counter())
            if wait: time.sleep(wait)
            end=time.perf_counter()-origin
            metrics=state.deliver(record,t,decision,arrivals,end)
            row={'type':'round','segment':t,**info,'decision_end':decision_end,'decision':decision,
                 'file_bytes':tuple(f['bytes'] for f in selected),'file_keys':tuple(f['relative_path'] for f in selected),
                 'file_sha256':tuple(hashes),'receipts':payload['flows'],'arrivals':arrivals,'acknowledged':acknowledged,
                 'client_return':payload_return,'end':end,'tc_class':class_state,'tc_qdisc':qdisc,
                 'deadline_met':max(arrivals)-start<=9.5,**metrics}
            rounds.append(row); save(row)
        after=json.loads(inside(src,[sys.executable,'-m','causal_playback.transport','--worker','stats']))
        result={'completed':True,'index':index,'key':record.key,'scene':record.scene,'cohort':record.cohort,
                'policy':policy,'rate_kbit':rate,'reserve_bytes':reserve(record),'loss_units':record.loss,
                'origin_monotonic':origin,'rounds':rounds,'background_bytes':after['9203']-before['9203'],
                'deadline_misses':sum(not r['deadline_met'] for r in rounds),**state.final()}
    except Exception as error:
        result={'completed':False,'index':index,'key':record.key,'policy':policy,'rate_kbit':rate,
                'error':repr(error),'rounds':rounds}
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
                try: p.communicate(timeout=5)
                except subprocess.TimeoutExpired: p.kill(); p.communicate()
        for ns in reversed(created): command(['ip','netns','del',ns])
        result['commands']=commands
        save({'type':'summary',**{k:v for k,v in result.items() if k not in ('rounds','commands')},'commands':commands})
        log.close()
    return result


def run(output,cache):
    if platform.system()!='Linux' or os.geteuid()!=0: raise RuntimeError('Linux root required')
    if output.exists(): raise FileExistsError('preserve prior live results')
    manifest=json.loads((ROOT/'causal_playback/data/media_manifest.json').read_text())
    # Validate every local file before selecting/running any pilot outcome.
    for f in manifest['files']:
        path=cache/f['relative_path']; assert path.stat().st_size==f['bytes'] and sha(path)==f['sha256']
    records=load(manifest); schedule=cases(records); output.mkdir(parents=True)
    with (output/'schedule.json').open('x') as f:
        json.dump([{'index':i,'key':r.key,'policy':p,'rate_kbit':rate} for i,(r,p,rate) in enumerate(schedule)],f,indent=2)
    results=[]
    with ThreadPoolExecutor(max_workers=2) as executor:
        jobs={executor.submit(episode,i,r,pool(records,r),p,rate,manifest,cache,output):i
              for i,(r,p,rate) in enumerate(schedule)}
        for job in as_completed(jobs):
            r=job.result(); results.append(r)
            print(f"Live {len(results)}/30: {r['key']} {r['policy']} {r['rate_kbit']}kbit complete={r['completed']}",flush=True)
    results.sort(key=lambda r:r['index'])
    with (output/'results.json').open('x') as f: json.dump(encode(results),f,indent=2); f.write('\n')
    meta={'python':platform.python_version(),'platform':platform.platform(),
          'source_sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in (ROOT/'causal_playback').glob('*.py')},
          'manifest_sha256':sha(ROOT/'causal_playback/data/media_manifest.json'),
          'files_sha256':{f.name:sha(f) for f in output.iterdir() if f.is_file()},'all_completed':all(r['completed'] for r in results)}
    (output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    if not meta['all_completed']: raise RuntimeError('failed episodes retained; do not claim complete validation')


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--output',type=Path,default=ROOT/'causal_playback/results/live_v1')
    p.add_argument('--cache',type=Path,default=ROOT/'.external/causal_playback_v1')
    a=p.parse_args(); run(a.output,a.cache)
