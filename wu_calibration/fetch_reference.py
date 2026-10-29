"""Fetch the pinned author projection reference privately, checking Git blob identity."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

ROOT=Path(__file__).resolve().parents[1]


def fetch(private):
    private=private.resolve()
    if private == ROOT or ROOT in private.parents: raise ValueError('Reference must stay outside repository')
    plan=json.loads((ROOT/'wu_calibration/amendment.json').read_text())['geometry_reference']
    url=f"https://raw.githubusercontent.com/wuchlei-thu/wuchlei-thu.github.io/{plan['site_commit']}/{plan['path']}"
    path=private/'author_video_3.csv'
    if path.exists(): raise ValueError('Preserve earlier reference download')
    private.mkdir(parents=True,exist_ok=True)
    with urllib.request.urlopen(url,timeout=60) as response:
        if response.status != 200: raise ValueError('Reference unavailable')
        raw=response.read(plan['bytes']+1)
    if len(raw) != plan['bytes']: raise ValueError('Reference size mismatch')
    blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    if blob != plan['git_blob_sha1']: raise ValueError('Reference Git identity differs')
    with path.open('xb') as f: f.write(raw)
    record={'url':url,'bytes':len(raw),'git_blob_sha1':blob,'sha256':hashlib.sha256(raw).hexdigest()}
    with (private/'reference_receipt.json').open('x',encoding='utf-8') as f:
        json.dump(record,f,sort_keys=True)
    return record


if __name__ == '__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--private-dir',type=Path,required=True)
    print(json.dumps(fetch(p.parse_args().private_dir)))
