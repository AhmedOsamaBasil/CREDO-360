"""Post-inspection clock-only diagnosis; never revises primary eligibility."""
import argparse
import csv
import io
import json
import math
from pathlib import Path
import zipfile

from .acquire import canonical
from .clocks import HEADER, TRACE


def inspect(lines):
    rows=csv.reader(lines,strict=True)
    if next(rows,None) != HEADER: raise ValueError('Header changed')
    prefix=[]; times=[]; backsteps=[]; later_backsteps=[]; seen_zero=False
    for row in rows:
        if len(row) != 9: raise ValueError('Malformed clock row')
        t=float(row[1])
        if not math.isfinite(t) or t < 0: raise ValueError('Invalid clock')
        if not seen_zero:
            if t != 0:
                prefix.append(t); continue
            seen_zero=True
        if times and t < times[-1]:
            backsteps.append(times[-1]-t)
            if times[-1] >= .5: later_backsteps.append(times[-1]-t)
        times.append(t)
        if t >= 60: break
    return {'first_exact_zero_found':seen_zero, 'prefix_rows':len(prefix),
        'prefix_min_seconds':min(prefix) if prefix else None,
        'prefix_max_seconds':max(prefix) if prefix else None,
        'after_zero_rows':len(times), 'after_zero_backward_steps':len(backsteps),
        'maximum_after_zero_backstep_seconds':max(backsteps,default=0),
        'backsteps_from_at_least_first_target':len(later_backsteps),
        'maximum_backstep_from_at_least_first_target_seconds':max(later_backsteps,default=0),
        'reaches_60s_after_zero':bool(times) and times[-1] >= 60,
        'does_not_change_primary_eligibility':True}


def run(archive):
    result=[]
    with zipfile.ZipFile(archive) as z:
        for name in sorted(z.namelist()):
            match=TRACE.fullmatch(name)
            if not match: continue
            e,u,k=match.groups()
            with z.open(name) as raw, io.TextIOWrapper(raw,encoding='utf-8-sig',newline='') as lines:
                result.append({'experiment':int(e),'video':int(k)+1,'source_id':u,**inspect(lines)})
    return {'schema':'wu-posthoc-clock-diagnosis-v1','rows':result,
        'eligibility_revised':False,'pose_values_interpreted':False,
        'warning':'An exact-zero delimiter is a diagnostic, not proof of valid session restart or a newly approved exclusion rule.'}


def main():
    p=argparse.ArgumentParser(__doc__); p.add_argument('--archive',type=Path,required=True); p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    if a.output.exists(): raise ValueError('Refusing overwrite')
    r=run(a.archive)
    with a.output.open('xb') as f: f.write(canonical(r))
    print(json.dumps({'rows':len(r['rows']),'with_startup_prefix':sum(x['prefix_rows']>0 for x in r['rows']),
        'with_postzero_backsteps':sum(x['after_zero_backward_steps']>0 for x in r['rows'])}))


if __name__ == '__main__': main()
