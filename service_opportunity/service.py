"""Isolated Linux TCP service probes. Never modifies host network interfaces."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
import threading
import time
from service_opportunity.model import CAPACITY,ROOT

DEADLINE=9.5
ADDRESS='10.233.55.2'


def read_line(connection):
    result=bytearray()
    while not result.endswith(b'\n'):
        b=connection.recv(1)
        if not b: raise IOError('premature control EOF')
        result.extend(b)
        if len(result)>10000: raise IOError('invalid control message')
    return bytes(result)


def server():
    totals={str(p):0 for p in (9201,9202,9203)}
    lock=threading.Lock()
    def handle(c,port):
        with c:
            if port==9204:
                with lock: payload=json.dumps(totals).encode()+b'\n'
                c.sendall(payload); return
            try:
                requested=int(read_line(c)); received=0
                while received<requested:
                    chunk=c.recv(min(65536,requested-received))
                    if not chunk: break
                    received+=len(chunk)
                    with lock: totals[str(port)]+=len(chunk)
                c.sendall(json.dumps({'received':received,'requested':requested}).encode()+b'\n')
            except (OSError,ValueError): pass
    def listen(port,ready):
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
            s.bind((ADDRESS,port)); s.listen(); ready.set()
            while True:
                c,_=s.accept(); threading.Thread(target=handle,args=(c,port),daemon=True).start()
    for port in (9201,9202,9203,9204):
        ready=threading.Event()
        threading.Thread(target=listen,args=(port,ready),daemon=True).start()
        if not ready.wait(5): raise RuntimeError('listener failed')
    print('ready',flush=True)
    threading.Event().wait()


def send(port,n):
    begin=time.perf_counter()
    with socket.create_connection((ADDRESS,port),timeout=25) as c:
        c.settimeout(25); c.sendall(f'{n}\n'.encode())
        chunk=b'R'*65536; remaining=n
        while remaining:
            part=chunk[:min(len(chunk),remaining)]; c.sendall(part); remaining-=len(part)
        receipt=json.loads(read_line(c))
    return {'port':port,'payload_bytes':n,**receipt,'completion_seconds':time.perf_counter()-begin}


def client():
    begin=time.perf_counter()
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(send,p,CAPACITY//2) for p in (9201,9202)]
        flows=[j.result() for j in jobs]
    print(json.dumps({'flows':flows,'joint_completion_seconds':time.perf_counter()-begin}))


def stats():
    with socket.create_connection((ADDRESS,9204),timeout=5) as c:
        print(read_line(c).decode().strip())


def validate(data):
    rows=data['probes']; nominal=[r for r in rows if not r['negative_control']]
    negative=[r for r in rows if r['negative_control']]
    assert len(nominal)==12 and len(negative)==3
    assert sorted((r['rtt_ms'],r['background'],r['repeat']) for r in nominal)==[
        (rtt,bg,i) for rtt in (20,80) for bg in (False,True) for i in range(3)]
    for r in rows:
        assert sum(f['received'] for f in r['flows'])==CAPACITY
        assert all(f['received']==f['requested']==CAPACITY//2 for f in r['flows'])
        assert r['joint_completion_seconds']>=max(f['completion_seconds'] for f in r['flows'])
        assert r['deadline_met']==(r['joint_completion_seconds']<=DEADLINE and r['subprocess_wall_seconds']<=10)
        assert r['foreground_rate_kbit']==(1000 if r['negative_control'] else 1500)
        assert r['background_received_bytes']>0 if r['background'] else r['background_received_bytes']==0
        assert '1:10' in r['tc_class_after'] and '1:20' in r['tc_class_after']
        assert 'htb' in r['tc_qdisc_after'] and 'netem' in r['tc_qdisc_after']
    return {'controlled_contract_pass':all(r['deadline_met'] for r in nominal),
            'negative_control_detected':all(not r['deadline_met'] for r in negative),
            'nominal_pass_count':sum(r['deadline_met'] for r in nominal),
            'negative_miss_count':sum(not r['deadline_met'] for r in negative),
            'nominal_max_seconds':max(r['joint_completion_seconds'] for r in nominal),
            'nominal_min_seconds':min(r['joint_completion_seconds'] for r in nominal),
            'negative_min_seconds':min(r['joint_completion_seconds'] for r in negative),
            'field_available_capacity_validated':False}


def measure(output):
    if platform.system()!='Linux' or os.geteuid()!=0: raise RuntimeError('Linux root required')
    if output.exists(): raise FileExistsError(output)
    prefix=f'crsv{os.getpid()}'; src=prefix+'s'; dst=prefix+'d'
    left=f'cs{os.getpid()}'; right=f'cd{os.getpid()}'
    if max(map(len,(left,right)))>15: raise RuntimeError('interface name too long')
    commands=[]; created=[]; processes=[]; rows=[]
    def command(args):
        r=subprocess.run(args,text=True,capture_output=True,timeout=30)
        commands.append({'args':args,'returncode':r.returncode,'stdout':r.stdout,'stderr':r.stderr})
        if r.returncode: raise RuntimeError(f'{args}: {r.stderr}')
        return r.stdout
    def inside(ns,args): return command(['ip','netns','exec',ns]+args)
    def worker(ns,mode):
        p=subprocess.Popen(['ip','netns','exec',ns,sys.executable,'-m','service_opportunity.service','--worker',mode],
                           stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
        processes.append(p); return p
    def tc(args): return inside(src,['tc']+args)
    try:
        existing=command(['ip','netns','list'])
        if any(n in existing.split() for n in (src,dst)): raise RuntimeError('namespace already exists')
        for ns in (src,dst): command(['ip','netns','add',ns]); created.append(ns)
        command(['ip','link','add',left,'netns',src,'type','veth','peer','name',right,'netns',dst])
        for ns,dev,addr in ((src,left,'10.233.55.1/30'),(dst,right,ADDRESS+'/30')):
            inside(ns,['ip','addr','add',addr,'dev',dev])
            inside(ns,['ip','link','set','dev',dev,'up'])
            inside(ns,['ip','link','set','lo','up'])
            inside(ns,['ethtool','-K',dev,'tso','off','gso','off','gro','off'])
            inside(ns,['ethtool','-k',dev])
        s=worker(dst,'server')
        if s.stdout.readline().strip()!='ready': raise RuntimeError('server failed')
        cases=[(rtt,bg,i,False) for rtt in (20,80) for bg in (False,True) for i in range(3)]
        cases += [(80,True,i,True) for i in range(3)]
        for index,(rtt,bg,repeat,negative) in enumerate(cases):
            if index:
                tc(['qdisc','del','dev',left,'root'])
                inside(dst,['tc','qdisc','del','dev',right,'root'])
            fg=1000 if negative else 1500
            tc(['qdisc','add','dev',left,'root','handle','1:','htb','default','20'])
            tc(['class','add','dev',left,'parent','1:','classid','1:1','htb','rate','2000kbit','ceil','2000kbit'])
            for minor,rate in (('10',fg),('20',500)):
                tc(['class','add','dev',left,'parent','1:1','classid','1:'+minor,'htb',
                    'rate',f'{rate}kbit','ceil',f'{rate}kbit','burst','3000','cburst','3000','quantum','1500'])
                tc(['qdisc','add','dev',left,'parent','1:'+minor,'handle',minor+':','netem',
                    'delay',f'{rtt//2}ms','limit','1000'])
            for port in (9201,9202,9204):
                tc(['filter','add','dev',left,'protocol','ip','parent','1:','prio','1','u32',
                    'match','ip','dport',str(port),'0xffff','flowid','1:10'])
            inside(dst,['tc','qdisc','add','dev',right,'root','netem','delay',f'{rtt//2}ms'])
            b=worker(src,'background') if bg else None
            if b: time.sleep(1)
            before=json.loads(inside(src,[sys.executable,'-m','service_opportunity.service','--worker','stats']))
            begin=time.perf_counter()
            payload=json.loads(inside(src,[sys.executable,'-m','service_opportunity.service','--worker','client']))
            wall=time.perf_counter()-begin
            after=json.loads(inside(src,[sys.executable,'-m','service_opportunity.service','--worker','stats']))
            if b: b.terminate(); b.communicate(timeout=5)
            row={'rtt_ms':rtt,'background':bg,'repeat':repeat,'negative_control':negative,
                 'foreground_rate_kbit':fg,**payload,'subprocess_wall_seconds':wall,
                 'background_received_bytes':after['9203']-before['9203'],
                 'deadline_met':payload['joint_completion_seconds']<=DEADLINE and wall<=10,
                 'tc_class_after':tc(['-s','class','show','dev',left]),
                 'tc_qdisc_after':tc(['-s','qdisc','show','dev',left])}
            rows.append(row)
            print(f"Probe {index+1}/15: {payload['joint_completion_seconds']:.3f}s, deadline={row['deadline_met']}",flush=True)
    finally:
        for p in processes:
            if p.poll() is None:
                p.terminate()
                try: p.communicate(timeout=5)
                except subprocess.TimeoutExpired: p.kill(); p.communicate()
        for ns in reversed(created): command(['ip','netns','del',ns])
    data={'platform':platform.platform(),'python':platform.python_version(),
          'payload_bytes_per_slot':CAPACITY,'deadline_seconds':DEADLINE,'probes':rows,'commands':commands,
          'scope':'isolated controlled reservation; not field capacity or a video-player trial'}
    data['validation']=validate(data)
    output.parent.mkdir(parents=True,exist_ok=True)
    with output.open('x') as f: json.dump(data,f,indent=2); f.write('\n')
    print(json.dumps(data['validation'],indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--worker',choices=['server','client','background','stats'])
    p.add_argument('--output',type=Path,default=ROOT/'service_opportunity/results/service_v1.json')
    a=p.parse_args()
    if a.worker=='server': server()
    elif a.worker=='client': client()
    elif a.worker=='stats': stats()
    elif a.worker=='background': send(9203,100_000_000)
    else: measure(a.output)
