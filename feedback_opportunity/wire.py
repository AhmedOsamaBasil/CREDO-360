"""Actual loopback HTTP exchange; raw pose/mask telemetry remains private."""
import argparse
import base64
from http.server import BaseHTTPRequestHandler,HTTPServer
import http.client
import json
from pathlib import Path
import platform
import threading
import time
import numpy as np
from causal_compensation.data import ROOT
from feedback_opportunity.feedback import reconstruct,SIZE
from reserve_recovery.run import sha


def run(packets_path,output):
    if output.exists(): raise FileExistsError('preserve earlier wire results')
    maps_dir=ROOT/'feedback_opportunity/data/maps_v1'
    metadata=json.loads((maps_dir/'metadata.json').read_text())
    byscene={s['scene']:s for s in metadata['sources']}
    maps={s['descriptor']:np.load(maps_dir/s['map_file'])['mse'] for s in metadata['sources']}
    packets=json.loads(packets_path.read_text()); states={}; rows=[]
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def do_POST(self):
            started=time.perf_counter()
            try:
                if self.path!='/feedback' or self.headers.get('Content-Type')!='application/octet-stream': raise ValueError('wrong endpoint/content type')
                if int(self.headers.get('Content-Length','0'))!=SIZE: raise ValueError('wrong size')
                session=self.headers['X-Session']; descriptor=self.headers['X-Descriptor']
                if descriptor not in maps or not session: raise ValueError('unknown session/content')
                key=session,descriptor; expected=states.get(key,0)
                result=reconstruct(self.rfile.read(SIZE),maps[descriptor],descriptor,expected,expected)
                states[key]=expected+1; code=200
                result['reconstruction_seconds']=time.perf_counter()-started
            except (ValueError,KeyError) as e: result={'error':str(e)}; code=400
            response=json.dumps(result,sort_keys=True).encode()
            self.send_response(code); self.send_header('Content-Type','application/json')
            self.send_header('Content-Length',str(len(response))); self.end_headers(); self.wfile.write(response)
    server=HTTPServer(('127.0.0.1',0),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True); thread.start()
    try:
        for entry in packets:
            cohort,scene,sid,segment=entry['key'].split(':'); spec=byscene[scene]
            payload=base64.b64decode(entry['packet']); started=time.perf_counter()
            connection=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
            headers={'Content-Type':'application/octet-stream','X-Session':f'{cohort}:{scene}:{sid}','X-Descriptor':spec['descriptor']}
            connection.request('POST','/feedback',payload,headers)
            response=connection.getresponse(); body=response.read(); elapsed=time.perf_counter()-started; connection.close()
            result=json.loads(body)
            if response.status!=200: raise RuntimeError((entry['key'],result))
            rows.append({'key':entry['key'],'payload_bytes':len(payload),'response_body_bytes':len(body),
                         'roundtrip_seconds':elapsed,'status':response.status,**result})
        # Negative probes are real HTTP requests, not only parser unit tests.
        bad=packets[0]; cohort,scene,sid,_=bad['key'].split(':'); spec=byscene[scene]
        negative=[]
        for name,payload,descriptor in [('duplicate',base64.b64decode(bad['packet']),spec['descriptor']),
             ('truncated',base64.b64decode(bad['packet'])[:-1],spec['descriptor']),
             ('wrong_content',base64.b64decode(bad['packet']),'00'*32)]:
            c=http.client.HTTPConnection('127.0.0.1',server.server_port,timeout=10)
            c.request('POST','/feedback',payload,{'Content-Type':'application/octet-stream',
                'X-Session':f'{cohort}:{scene}:{sid}','X-Descriptor':descriptor})
            response=c.getresponse(); body=json.loads(response.read()); c.close()
            assert response.status==400; negative.append({'case':name,'status':response.status,**body})
    finally:
        server.shutdown(); server.server_close(); thread.join()
    output.mkdir(parents=True)
    (output/'results.json').write_text(json.dumps({'rows':rows,'negative_probes':negative},indent=2)+'\n')
    meta={'transport':'actual loopback HTTP, not HMD or WAN','raw_packets_published':False,
          'python':platform.python_version(),'platform':platform.platform(),
          'packet_file_sha256':sha(packets_path),'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in
          [Path(__file__),ROOT/'feedback_opportunity/feedback.py',ROOT/'feedback_opportunity/client.mjs']},
          'map_metadata_sha256':sha(maps_dir/'metadata.json'),'results_sha256':sha(output/'results.json')}
    (output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'completed_messages':len(rows),'negative_probes':negative},indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--packets',type=Path,default=ROOT/'.external/feedback_opportunity_v1/client_packets.json')
    p.add_argument('--output',type=Path,default=ROOT/'feedback_opportunity/results/wire_v1')
    a=p.parse_args(); run(a.packets,a.output)
