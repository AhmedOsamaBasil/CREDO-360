"""Audit stored class counters, timing records, figures and their provenance."""
import argparse
import json
import math
import platform
import re
from pathlib import Path
from service_opportunity.model import ROOT
from reserve_recovery.run import sha


def check():
    root=ROOT/'service_opportunity'; result=root/'results/development_v1'
    service=json.loads((root/'results/service_v1.json').read_text())
    busy=0
    for row in service['probes']:
        blocks=re.split(r'\r?\n\r?\n',row['tc_class_after'])
        fg=next(b for b in blocks if 'class htb 1:10 ' in b)
        bg=next(b for b in blocks if 'class htb 1:20 ' in b)
        rate='1Mbit' if row['negative_control'] else '1500Kbit'
        assert f'rate {rate} ceil {rate}' in fg and 'borrowed: 0' in fg
        assert 'rate 500Kbit ceil 500Kbit' in bg and 'borrowed: 0' in bg
        if row['background']:
            assert re.search(r'backlog [1-9][0-9]*b [1-9][0-9]*p',bg)
            busy+=1
    assert busy==9 and len(service['probes'])==15
    for name in ('timing_windows.json','timing_linux.json'):
        r=json.loads((result/name).read_text()); values=sorted(x['seconds'] for x in r['timings'])
        assert r['script_sha256']==sha(root/'benchmark.py')
        assert r['result_sha256']==sha(result/'results.json.gz')
        assert len(values)==r['decisions']==672 and min(values)>=0
        assert r['max_seconds']==max(values)
        assert math.isclose(r['mean_seconds'],sum(values)/len(values),abs_tol=1e-12)
        assert r['p95_seconds']==values[(95*len(values)+99)//100-1]
        assert r['observed_budget_pass']==(max(values)<=r['decision_budget_seconds'])
    figures=result/'figures'; m=json.loads((figures/'metadata.json').read_text())
    assert m['script_sha256']==sha(root/'plot.py')
    assert m['primary_result_sha256']==sha(result/'results.json.gz')
    assert m['posthoc_result_sha256']==sha(result/'posthoc_ablation.json.gz')
    assert m['service_sha256']==sha(root/'results/service_v1.json')
    for name,digest in m['figure_sha256'].items(): assert sha(figures/name)==digest,name
    return {'passed':True,'service_class_checks':15,'backlogged_competitor_checks':busy,
        'timing_records_checked':1344,'figure_hashes_checked':len(m['figure_sha256']),
        'script_sha256':sha(Path(__file__)),'python':platform.python_version(),'platform':platform.platform()}


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__); p.add_argument('--save'); a=p.parse_args()
    if a.save and (Path(a.save).name!=a.save or not a.save.endswith('.json')): p.error('local JSON filename')
    r=check()
    if a.save:
        with (ROOT/'service_opportunity/results/development_v1'/a.save).open('x') as f: json.dump(r,f,indent=2); f.write('\n')
    print(json.dumps(r,indent=2))
