"""Transfer actual selected MP4 bytes with receiver SHA256 and shared-clock receipt."""
import argparse
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import socket
import threading
import time
from service_opportunity.service import ADDRESS,read_line,send as background_send


def server():
    totals={str(p):0 for p in (9201,9202,9203)}; lock=threading.Lock()
    def handle(c,port):
        with c:
            try:
                if port==9204:
                    with lock: response=json.dumps(totals).encode()+b'\n'
                    c.sendall(response); return
                head=read_line(c)
                info={'bytes':int(head)} if port==9203 else json.loads(head)
                remaining=info['bytes']; received=0; digest=hashlib.sha256()
                while remaining:
                    chunk=c.recv(min(65536,remaining))
                    if not chunk: break
                    digest.update(chunk); received+=len(chunk); remaining-=len(chunk)
                    with lock: totals[str(port)]+=len(chunk)
                response={'received':received,'sha256':digest.hexdigest(),'verified_at':time.perf_counter()}
                response['valid']=received==info['bytes'] and (port==9203 or response['sha256']==info['sha256'])
                c.sendall(json.dumps(response).encode()+b'\n')
            except (OSError,ValueError): pass
    def listen(port,ready):
        with socket.socket() as s:
            s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind((ADDRESS,port)); s.listen(); ready.set()
            while True:
                c,_=s.accept(); threading.Thread(target=handle,args=(c,port),daemon=True).start()
    for port in (9201,9202,9203,9204):
        ready=threading.Event(); threading.Thread(target=listen,args=(port,ready),daemon=True).start()
        if not ready.wait(5): raise RuntimeError('receiver listener failed')
    print('ready',flush=True); threading.Event().wait()


def transfer(port,path,expected):
    start=time.perf_counter(); n=path.stat().st_size
    with socket.create_connection((ADDRESS,port),timeout=30) as c:
        c.settimeout(30); c.sendall(json.dumps({'bytes':n,'sha256':expected}).encode()+b'\n')
        with path.open('rb') as f:
            while chunk:=f.read(65536): c.sendall(chunk)
        receipt=json.loads(read_line(c)); acknowledged=time.perf_counter()
    if not receipt['valid'] or receipt['received']!=n or receipt['sha256']!=expected: raise IOError('receipt mismatch')
    return {'port':port,'bytes':n,'start':start,'acknowledged_at':acknowledged,**receipt}


def pair(files,hashes):
    with ThreadPoolExecutor(max_workers=2) as pool:
        jobs=[pool.submit(transfer,9201+u,Path(files[u]),hashes[u]) for u in (0,1)]
        rows=[j.result() for j in jobs]
    print(json.dumps({'flows':rows,'returned_at':time.perf_counter()}))


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--worker',choices=['server','background','stats','pair'],required=True)
    p.add_argument('--files',nargs=2); p.add_argument('--hashes',nargs=2); a=p.parse_args()
    if a.worker=='server': server()
    elif a.worker=='background': background_send(9203,100_000_000)
    elif a.worker=='stats':
        with socket.create_connection((ADDRESS,9204),timeout=10) as c: print(read_line(c).decode().strip())
    else: pair(a.files,a.hashes)
