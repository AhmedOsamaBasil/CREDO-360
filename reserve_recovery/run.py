"""Publish exact constructed tests and an exposed-catalogue reserve audit."""
import argparse
from dataclasses import asdict
from fractions import Fraction as F
import csv
import gzip
import hashlib
import json
import platform
from pathlib import Path
from reserve_recovery.cases import problems,bounded,offer
from reserve_recovery.core import plan,online,execute
from reserve_recovery.catalogue import analysis as catalogue_analysis,PEAKS,FRACTIONS,BASELINES
from feasibility_frontier.data import ROOT,load,source_paths


def encode(x):
    if isinstance(x,F): return str(x)
    if isinstance(x,dict): return {str(k):encode(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)): return [encode(v) for v in x]
    return x


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def lf_sha(path): return hashlib.sha256(path.read_bytes().replace(b'\r\n',b'\n')).hexdigest()
def canonical(x): return json.dumps(encode(x),sort_keys=True,separators=(',',':')).encode()


def analytical():
    cases=[]
    for p in problems():
        r=plan(p.scenarios,p.contract,p.reserve); rule=r['policies'][r['best']]
        outcomes={'causal_absolute':tuple(execute(rule,s,p.contract,p.reserve,p.history) for s in p.scenarios),
                  'offline':r['oracle']}
        for policy in BASELINES:
            outcomes[policy]=tuple(online(policy,s,p.contract,p.reserve,p.history) for s in p.scenarios)
        assert all(not x['model_breach'] for x in outcomes['causal_absolute'])
        cases.append({'problem':asdict(p),'policy_count':len(r['policies']),'selected_policy':r['best'],
            'policy_paths':tuple(tuple(tuple(a.name for a in path) for path in x['paths']) for x in r['policies']),
            'loss_matrix':tuple(tuple(x['terminal_max_fraction'] for x in q['outcomes']) for q in r['policies']),
            'admitted':r['admitted'],'worst_loss':r['worst_loss'],'independent_bellman':r['bellman_value'],
            'comparisons':outcomes})
    p=bounded(); r=plan(p.scenarios,p.contract,p.reserve)
    missed=(p.scenarios[0][0],offer(0))
    miss=execute(r['policies'][r['best']],missed,p.contract,p.reserve,p.history)
    controls={n:online(n,missed,p.contract,p.reserve,p.history) for n in BASELINES}
    assert miss['model_breach'] and miss['terminal_max_fraction']==1
    return {'cases':cases,'out_of_model_disappearance':{'candidate':miss,'controls':controls},
            'future_model_fitted_or_validated':False}


def evidence():
    trace_meta=json.loads((ROOT/'testbed/data/trace_metadata.json').read_text())
    provenance=json.loads((ROOT/'testbed/data/provenance.json').read_text())
    assert len(trace_meta)==provenance['pcap_traces']==30
    bins=0
    for m in trace_meta:
        with (ROOT/'testbed/data/traces'/m['trace']).open(newline='') as f:
            reader=csv.DictReader(f); assert reader.fieldnames==['time_s','observed_traffic_mbps']
            n=sum(1 for row in reader); assert n==m['bins']; bins+=n
    contexts={}
    for e,periods in load():
        for t,p in enumerate(periods,2): contexts[e.cohort,e.scene,t]=p[0].reference_bytes
    return {'observed_traffic_traces':len(trace_meta),'total_observed_traffic_bins':bins,
            'trace_caveat':provenance['trace_caveat'],'capacity_availability_identified':False,
            'prior_live_capacity':'configured controlled bottlenecks, not field spare-capacity samples',
            'prior_recovery_capacity':'synthetic, not passive or active path-capacity measurement',
            'baseline_payload_contexts':tuple({'cohort':k[0],'scene':k[1],'segment':k[2],
                'pair_baseline_bytes':v,'pair_baseline_mbps':F(v*8,10_000_000)} for k,v in sorted(contexts.items()))}


def analysis(progress=False):
    a=analytical(); data=catalogue_analysis(progress)
    previous=json.loads(gzip.decompress((ROOT/'feasibility_frontier/results/audit_v1/results.json.gz').read_bytes()))
    old={r['key']:r for r in previous['rows']}
    for row in data['episodes']:
        for cap in PEAKS:
            expected=any(F(p['peak_multiplier'])<=cap for p in old[row['key']]['frontiers']['4:0'])
            assert (row['minimum_reserve'][str(cap)] is not None)==expected
    return {'analytical_and_exposed_only':True,'fresh_holdout_used':False,'scientific_network_validation':False,
            'evidence':evidence(),'analytical':a,'catalogue':data,'prior_frontier_feasibility_matches':True}


def fmt(value,digits=4): return 'infeasible' if value is None else f'{float(F(value)):.{digits}f}'


def report(p):
    lines=['# Limited cumulative recovery reserve','',
        '**Constructed analytical tests and already-exposed tables only. No new holdout or validated field headroom.**','',
        '## Evidence boundary','',
        f"The {p['evidence']['observed_traffic_traces']} captured traffic traces do not identify spare path capacity. "
        'Earlier network capacities were configured or synthetic. Demand below is encoded payload, not measured supply.','',
        'The finite reserve pays only positive bytes above the unchanged baseline, with no refill or refunds. '
        'Every action must also fit contemporaneous capacity. It is an entitlement, not stored bandwidth.','',
        '## Exact analytical comparison','',
        '| Construction | Half-repayment admitted | Causal worst unpaid | Rolling Nash | Rolling max-min | Greedy | Offline worst unpaid |',
        '|---|---|---:|---:|---:|---:|---:|']
    for c in p['analytical']['cases']:
        values=[max(F(r['terminal_max_fraction']) for r in c['comparisons'][name]) for name in ('causal_absolute',)+BASELINES+('offline',)]
        lines.append('| '+c['problem']['name']+' | '+str(c['admitted'])+' | '+' | '.join(fmt(v) for v in values)+' |')
    lines += ['', 'All causal values agree with an independent robust Bellman recursion. '
        'The future scenario set is supplied, not fitted. Model-aware planning is not an information-matched improvement over myopic rules.',
        '', 'Out-of-model disappearance: candidate unpaid fraction1, versus0.6 for the three immediate controls. '
        'The reserve remains safe but the repayment guarantee fails. The causal-admission-gap example is feasible '
        'in each future offline but not guaranteed by any shared-prefix policy.','']
    for group,s in p['catalogue']['summary'].items():
        lines += ['## '+group,'',f"Episodes: {s['episodes']}.",'',
            '### Minimum additional reserve for half-repayment','',
            'Quantiles condition on feasible episodes. Peak Mbit/s belongs to the minimum-reserve witness; it is not jointly minimized.', '',
            '| Peak factor | Feasible/total | Extra MB median [min,max] | Reserve / baseline-total median | Witness peak payload Mbit/s median [min,max] |',
            '|---|---:|---:|---:|---:|']
        for d in s['minimum_reserve_demands']:
            def interval(field,scale=1):
                x=d[field]
                return 'infeasible' if x is None else f"{fmt(F(x['median'])/scale)} [{fmt(F(x['minimum'])/scale)}, {fmt(F(x['maximum'])/scale)}]"
            ratio='infeasible' if d['reserve_fraction'] is None else fmt(d['reserve_fraction']['median'])
            lines.append(f"| {d['peak']} | {d['feasible']}/{s['episodes']} | {interval('extra_bytes',1000000)} | {ratio} | {interval('peak_payload_mbps')} |")
        lines += ['', '### Fixed reserve grid','',
            'Cells are counts reaching half-repayment; all168/84/28 episode denominators are retained. '
            'All policies use the same per-slot capacity, reserve and zero-donor-loss floor.','',
            '| Peak factor | Reserve fraction | Rolling Nash | Rolling max-min | Greedy recovery | Offline oracle |',
            '|---:|---:|---:|---:|---:|---:|']
        for cap in PEAKS:
            for rho in FRACTIONS:
                vals=[next(c['half_repaid'] for c in s['cells'] if (F(c['peak']),F(c['reserve_fraction']),c['policy'])==(cap,rho,n)) for n in BASELINES+('offline',)]
                lines.append(f'| {cap} | {rho} | '+' | '.join(map(str,vals))+' |')
        lines += ['', 'Full artifact retains unpaid fractions, reserve expenditure, quality metrics and every action witness; '
                  'no causal future predictor is evaluated on these exposed tables.','']
    lines += ['## Verification','',
        f"- {p['catalogue']['minimum_reserve_witnesses']} minimum-reserve witnesses checked against original tables.",
        f"- {p['catalogue']['online_vs_oracle_checks']} matched online/oracle comparisons preserve both ledgers and zero donor loss.",
        '- Unlimited-reserve feasibility agrees with the previous exact headroom frontier.',
        '- Independent robust recursion checks every constructed scenario game.',
        '- No repayment reference, impairment loss or target was reduced.','']
    return '\n'.join(lines)


def inputs():
    base=list(source_paths())+[ROOT/'feasibility_frontier/results/audit_v1/results.json.gz',
        ROOT/'testbed/data/provenance.json',ROOT/'testbed/data/trace_metadata.json']
    base+=sorted((ROOT/'testbed/data/traces').glob('*.csv'))
    return base


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'reserve_recovery/results/analysis_v1')
    args=parser.parse_args()
    if args.output.exists(): parser.error('preserve existing output; select a new directory')
    p=encode(analysis(progress=True)); args.output.mkdir(parents=True)
    with (args.output/'results.json.gz').open('wb') as f:
        with gzip.GzipFile(fileobj=f,mode='wb',filename='',mtime=0) as g: g.write(canonical(p))
    (args.output/'REPORT.md').write_text(report(p),encoding='utf-8')
    files=sorted(f for f in (ROOT/'reserve_recovery').iterdir() if f.suffix=='.py' or f.name in ('PLAN.md','THEORY.md'))
    files += [ROOT/n for n in ('recovery_objective/core.py','feasibility_frontier/core.py','feasibility_frontier/data.py',
        'causal_compensation/data.py','horizon_recovery/run.py','feasibility_recovery/run.py','live_testbed/run_mininet_experiment.py')]
    meta={'source_sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in files},
          'input_sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in inputs()},
          'canonical_lf_sha256':{f.relative_to(ROOT).as_posix():lf_sha(f) for f in files+inputs()
              if f.relative_to(ROOT).as_posix().startswith('testbed/data/')
              or f.relative_to(ROOT).as_posix()=='live_testbed/run_mininet_experiment.py'},
          'result_sha256':{f.name:sha(f) for f in args.output.iterdir() if f.is_file()},
          'scientific_sha256':hashlib.sha256(canonical(p)).hexdigest(),'python':platform.python_version(),
          'exposed_only':True,'new_network_experiment':False}
    (args.output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'episodes':len(p['catalogue']['episodes']),'analytical_cases':len(p['analytical']['cases']),
                     'scientific_sha256':meta['scientific_sha256']},indent=2))


if __name__=='__main__': main()
