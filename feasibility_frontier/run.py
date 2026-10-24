"""Exact future-known feasibility audit, not online-controller evaluation."""
import argparse
from fractions import Fraction as F
import gzip
import hashlib
import json
import platform
from pathlib import Path
from feasibility_frontier.data import ROOT,load,source_paths
from feasibility_frontier.core import (EPSILONS,BUDGETS,TRANSFERS,RESOURCES,PROFILES,
    frontier,required,feasible,verify_witness,dp_feasible)


def encode(x):
    if isinstance(x,F): return str(x)
    if isinstance(x,dict): return {str(k):encode(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)): return [encode(v) for v in x]
    return x


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(payload): return json.dumps(encode(payload),sort_keys=True,separators=(',',':')).encode()
def quantile(values,p):
    values=sorted(values)
    if not values: return None
    return values[max(0,(len(values)*p.numerator+p.denominator-1)//p.denominator-1)]


def validate_monotonicity(frontiers):
    for m in TRANSFERS:
        for e in EPSILONS:
            points=frontiers[f'{m}:{e}']
            assert all(a['peak_multiplier']<b['peak_multiplier'] and a['donor_total_units']>b['donor_total_units']
                       for a,b in zip(points,points[1:]))
    for mi,m in enumerate(TRANSFERS):
        for ei,e in enumerate(EPSILONS):
            for bi,b in enumerate(BUDGETS):
                p=required(frontiers,m,e,b)
                if p is None: continue
                relaxed=[]
                if mi+1<len(TRANSFERS): relaxed.append(required(frontiers,TRANSFERS[mi+1],e,b))
                if ei+1<len(EPSILONS): relaxed.append(required(frontiers,m,EPSILONS[ei+1],b))
                if bi+1<len(BUDGETS): relaxed.append(required(frontiers,m,e,BUDGETS[bi+1]))
                assert all(q is not None and q['peak_multiplier']<=p['peak_multiplier'] for q in relaxed)


def opportunity_counts(periods,target,epsilon,budget,resource):
    maxima=[max((a.gain for a in p if a.harm<=min(epsilon,budget) and a.multiplier<=resource),default=0) for p in periods]
    return {'positive_periods':sum(g>0 for g in maxima),'substantial_periods':sum(4*g>=target for g in maxima)}


def summary(rows):
    groups=[('all',rows)]+[(c,[r for r in rows if r['cohort']==c]) for c in ('v2','v3')]
    groups += [(s,[r for r in rows if r['scene']==s]) for s in sorted({r['scene'] for r in rows})]
    result={}
    for name,group in groups:
        requirements=[]
        for m in TRANSFERS:
            for e in EPSILONS:
                for b in BUDGETS:
                    points=[required(r['frontiers'],m,e,b) for r in group]
                    values=sorted(p['peak_multiplier'] for p in points if p is not None)
                    thresholds={}
                    for coverage in (F(1,2),F(3,4),F(9,10),F(1)):
                        k=(len(group)*coverage.numerator+coverage.denominator-1)//coverage.denominator
                        thresholds[str(coverage)]=values[k-1] if len(values)>=k else None
                    requirements.append({'max_actions':m,'step_harm_units':e,'total_harm_units':b,
                        'feasible_at_any_resource':len(values),'infeasible':len(group)-len(values),
                        'minimum_multiplier':min(values) if values else None,'median_multiplier':quantile(values,F(1,2)),
                        'p90_multiplier':quantile(values,F(9,10)),'maximum_multiplier':max(values) if values else None,
                        'coverage_thresholds':thresholds,
                        'counts_by_multiplier':{str(cap):sum(x<=cap for x in values) for cap in RESOURCES}})
        profiles=[]
        for profile,m,e,b in PROFILES:
            req=next(q for q in requirements if (q['max_actions'],q['step_harm_units'],q['total_harm_units'])==(m,e,b))
            diag={}
            for cap in RESOURCES:
                per=[r['opportunities'][profile][str(cap)] for r in group]
                diag[str(cap)]={'two_positive_periods':sum(x['positive_periods']>=2 for x in per),
                    'two_substantial_periods':sum(x['substantial_periods']>=2 for x in per),
                    'feasible_and_two_substantial':sum(x['substantial_periods']>=2 and feasible(r['frontiers'],m,e,b,cap) for r,x in zip(group,per))}
            profiles.append({'name':profile,'requirements':req,'opportunity_diagnostics':diag})
        result[name]={'episodes':len(group),'requirements':requirements,'profiles':profiles}
    return result


def analysis(progress=False):
    rows=[]; witnesses=0; dp_checks=0
    for number,(e,periods) in enumerate(load(),1):
        record=frontier(periods,e.loss)
        for key,points in record['frontiers'].items():
            m,epsilon=map(int,key.split(':'))
            for point in points:
                verify_witness(point,periods,e.loss,m,epsilon); witnesses+=1
        validate_monotonicity(record['frontiers'])
        diag={}
        for profile,m,epsilon,budget in PROFILES:
            diag[profile]={}
            for cap in RESOURCES:
                exact=feasible(record['frontiers'],m,epsilon,budget,cap)
                independent=dp_feasible(periods,e.loss,m,epsilon,budget,cap)
                assert exact==independent,(e.key,profile,str(cap))
                dp_checks+=1
                diag[profile][str(cap)]=opportunity_counts(periods,record['target_units'],epsilon,budget,cap)
        rows.append({'key':e.key,'cohort':e.cohort,'scene':e.scene,'recipient':e.recipient,'donor':e.donor,
                     'original_loss_units':e.loss,**record,'opportunities':diag})
        if progress and number%28==0: print(f'Audited {number}/168 exposed episodes',flush=True)
    aggregate=summary(rows)
    old=json.loads((ROOT/'causal_compensation/results/development_v1/posthoc_opportunity_diagnosis.json').read_text())
    unrestricted=sum(required(r['frontiers'],4,4000,16000) is not None for r in rows)
    assert unrestricted==old['groups']['all']['unrestricted_ladder_feasible_count']==157
    return {'exposed_data_only':True,'future_known_offline_audit':True,'repayment_fraction':F(1,2),
            'rows':rows,'summary':aggregate,'verification':{'witnesses':witnesses,'independent_dp_checks':dp_checks,
            'monotonicity':True,'unrestricted_matches_prior':True,'unrestricted_feasible':unrestricted}}


def fmt(value): return 'infeasible' if value is None else f'{float(F(value)):.4f}'


def report(payload):
    lines=['# Resource and donor-loss feasibility audit','',
           '**Exposed data only; exact future-known feasibility, not online performance.** '
           'Original losses and rung-2 references are unchanged. The target remains at least half of the original loss repaid.', '',
           'Lambda is a per-segment encoded-byte allocation multiplier, not aggregate bytes, measured throughput or a stall guarantee. '
           'Donor loss uses the objective index and sums only positive losses; surplus never refunds it. '
           'All action schedules are integral. Quantiles below are conditional on feasible episodes; coverage thresholds use ALL episodes.', '']
    for group,s in payload['summary'].items():
        lines += ['## '+group,'',f"Episodes: {s['episodes']}.",'',
                  '| Contract | Feasible at some resource | Median minimum lambda (feasible only) | Lambda for 75% of all episodes |',
                  '|---|---:|---:|---:|']
        for p in s['profiles']:
            q=p['requirements']
            label=f"{p['name']}: M{q['max_actions']}, step {q['step_harm_units']/1000:g}, total {q['total_harm_units']/1000:g}"
            lines.append(f"| {label} | {q['feasible_at_any_resource']}/{s['episodes']} | {fmt(q['median_multiplier'])} | {fmt(q['coverage_thresholds']['3/4'])} |")
        lines += ['', '| Contract | '+ ' | '.join(f'lambda {float(x):g}' for x in RESOURCES)+' |',
                  '|---|'+'---:|'*len(RESOURCES)]
        for p in s['profiles']:
            lines.append('| '+p['name']+' | '+' | '.join(str(p['requirements']['counts_by_multiplier'][str(x)]) for x in RESOURCES)+' |')
        lines += ['', 'Counts are episodes capable of half-repayment, not observed success rates of an online controller. '
                  'The complete artifact includes all donor slices, exact staircases, action witnesses and opportunity counts.','']
    v=payload['verification']
    lines += ['## Verification','',f"- {v['witnesses']} staircase witnesses replay against original tables.",
              f"- {v['independent_dp_checks']} independent dynamic-programming decisions match enumeration.",
              '- All tested allowance monotonicity checks pass.',
              '- Unrestricted catalogue ceiling agrees with the prior diagnosis: 157/168 episodes.', '',
              'No new holdout, new participants, human-QoE claim, causal guarantee or novel optimization theorem is implied. '
              'An acceptable donor/resource contract remains a service-design choice.','']
    return '\n'.join(lines)


def input_paths():
    return source_paths()+(ROOT/'causal_compensation/results/development_v1/posthoc_opportunity_diagnosis.json',)


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'feasibility_frontier/results/audit_v1')
    args=parser.parse_args()
    if args.output.exists(): parser.error('output exists; preserve the audit')
    payload=encode(analysis(progress=True)); args.output.mkdir(parents=True)
    with (args.output/'results.json.gz').open('wb') as f:
        with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0) as g: g.write(canonical(payload))
    (args.output/'REPORT.md').write_text(report(payload),encoding='utf-8')
    sources=sorted(p for p in (ROOT/'feasibility_frontier').iterdir()
                   if (p.suffix=='.py' and p.name!='plot.py') or p.name in ('PLAN.md','METHOD.md'))
    sources += [ROOT/'causal_compensation/data.py']
    meta={'exposed_data_only':True,'future_known_offline_audit':True,'python':platform.python_version(),
          'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in sources},
          'input_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in input_paths()},
          'result_sha256':{p.name:sha(p) for p in args.output.iterdir() if p.is_file()},
          'scientific_sha256':hashlib.sha256(canonical(payload)).hexdigest()}
    (args.output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'episodes':len(payload['rows']),**payload['verification'],'scientific_sha256':meta['scientific_sha256']},indent=2))


if __name__=='__main__': main()
