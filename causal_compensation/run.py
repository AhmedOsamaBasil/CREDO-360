"""Locked exposed-data development, with complete forecasts and adverse outcomes."""
import argparse
from dataclasses import asdict
from fractions import Fraction as F
import hashlib
import json
import platform
from pathlib import Path
from causal_compensation.data import ROOT, load_episodes, source_paths
from causal_compensation.model import forecast, training_pool
from causal_compensation.core import plan, verify_plan
from causal_compensation.replay import replay, mixture, CONTROLS, METRICS

MODELS = ('bounded_knn','knn_alpha25','knn_alpha75','unconstrained_knn','bounded_persistence','bounded_physical')


def encode(x):
    if isinstance(x,F): return str(x)
    if isinstance(x,dict): return {k:encode(v) for k,v in x.items()}
    if isinstance(x,(tuple,list)): return [encode(v) for v in x]
    return x


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def mean(values):
    values = tuple(values)
    return sum(values,F(0))/len(values) if values else F(0)


def summaries(rows):
    groups = [('all',rows)]
    groups += [(c,[r for r in rows if r['episode']['cohort']==c]) for c in ('v2','v3')]
    groups += [(s,[r for r in rows if r['episode']['scene']==s]) for s in sorted({r['episode']['scene'] for r in rows})]
    result = {}
    for name,group in groups:
        positive = [r for r in group if r['episode']['loss']>0]
        result[name] = {'episodes':len(group),'positive_debt':len(positive),
            'raw_envelope_coverage':mean(F(int(r['forecast']['raw_covered'])) for r in positive),
            'decision_envelope_coverage':mean(F(int(r['forecast']['capped_covered'])) for r in positive),
            'gain_midpoint_mae':mean(r['forecast']['gain_midpoint_mae'] for r in positive),
            'policies':{p:{m:mean(r['outcomes'][p]['expected'][m] for r in positive) for m in METRICS} for p in MODELS+CONTROLS}}
        for p in MODELS:
            feasible = [r for r in positive if r['plans'][p]['feasible']]
            result[name]['policies'][p].update({'feasible_fraction':F(len(feasible),len(positive)) if positive else F(0),
                'feasible_episodes':len(feasible),
                'violations_among_feasible':sum((r['outcomes'][p]['expected']['cap_violation'] for r in feasible),F(0))})
    return result


def screen(summary,rows):
    main = summary['all']['policies']['bounded_knn']
    checks = {'nonempty_positive_debt':summary['all']['positive_debt']>0,
              'at_least_half_feasible':main['feasible_fraction']>=F(1,2),
              'forecast_coverage_90pct':summary['all']['decision_envelope_coverage']>=F(9,10),
              'zero_feasible_cap_violations':main['violations_among_feasible']==0,
              'all_pathwise_guards':all(r['pathwise_guards'] for r in rows)}
    for cohort in ('v2','v3'):
        a = summary[cohort]['policies']['bounded_knn']
        for p in ('rolling_nash','rolling_maxmin'):
            b = summary[cohort]['policies'][p]; key=cohort+':'+p+':'
            checks[key+'unpaid_gain'] = a['unpaid_fraction'] < b['unpaid_fraction']
            checks[key+'cap_guard'] = a['cap_violation'] <= b['cap_violation']
            checks[key+'mean_quality_guard'] = a['mean_post_quality'] >= b['mean_post_quality']-F(3,100)
    return {'passed':all(checks.values()),'checks':checks}


def analysis(progress=False):
    episodes = load_episodes(); rows=[]
    for number,e in enumerate(episodes):
        prefix = tuple(o.gain for o in e.offers[:3])
        pool = training_pool(episodes,e.scene,e.recipient,e.donor)
        prediction = forecast(prefix,e.loss,pool)
        future = tuple(o.gain for o in e.offers[3:])  # evaluation ONLY, never forecast input
        prediction['raw_covered'] = all(lo<=g<=hi for g,(lo,hi) in zip(future,prediction['bounds']))
        prediction['capped_covered'] = all(min(e.loss,lo)<=min(e.loss,g)<=min(e.loss,hi) for g,(lo,hi) in zip(future,prediction['bounds']))
        prediction['gain_midpoint_mae'] = mean(F(abs(2*g-lo-hi),2000) for g,(lo,hi) in zip(future,prediction['bounds']))
        plans,outcomes = {},{}
        for name in MODELS:
            alpha = F(1,4) if name=='knn_alpha25' else F(3,4) if name=='knn_alpha75' else F(1) if name=='unconstrained_knn' else F(1,2)
            bounds = prediction['bounds']
            if name=='bounded_persistence': bounds = ((max(0,prefix[-1]-50),min(4000,prefix[-1]+50)),)*3
            if name=='bounded_physical': bounds = ((0,e.loss),)*3
            if e.loss:
                planned = plan(e.loss,prefix[-1],bounds,alpha)
                verify_plan(planned)
                result = mixture(e,planned,alpha)
            else:
                planned = {'feasible':True,'no_debt':True,'alpha':alpha}
                base = replay(e,'baseline',alpha)
                result = {'expected':{k:base[k] for k in METRICS},'paths':({'policy':'baseline','weight':F(1),'outcome':base},)}
            plans[name],outcomes[name] = planned,result
        for name in CONTROLS:
            r = replay(e,name)
            outcomes[name] = {'expected':{k:r[k] for k in METRICS},'paths':({'policy':name,'weight':F(1),'outcome':r},)}
        for result in outcomes.values():
            for path in result['paths']:
                trace=path['outcome']['trace']
                assert sum(t['transfer'] for t in trace)<=1
                assert all(t['bytes']<=e.offers[t['period']+2].baseline_bytes for t in trace)
                assert trace[-1]['donor_loss']<=500
                assert trace[-1]['outstanding']+sum(t['credit'] for t in trace)==e.loss
        rows.append({'key':e.key,'episode':asdict(e),'forecast':prediction,'plans':plans,'outcomes':outcomes,'pathwise_guards':True})
        if progress and (number+1)%28==0: print(f'Completed {number+1}/{len(episodes)} exposed episodes',flush=True)
    summary=summaries(rows)
    return {'exposed_development_only':True,'new_holdout':False,'current_utility_oracle':True,
            'rows':rows,'summary':summary,'screen':screen(summary,rows)}


def report(payload):
    lines=['# Exposed-data bounded-loss development','',
           '**Not a fresh holdout. Exact current utilities are revealed to all controls; future opportunities are forecast causally.**','',
           'Development screen: **'+('PASS' if payload['screen']['passed'] else 'FAIL')+'**. No positive streaming-validation claim follows from this replay.','',
           'Metrics below condition on positive event loss; every zero-loss episode remains in the complete artifact. '
           'Mixture outcomes are expectations over episode-level policy randomization, not Monte Carlo estimates. '
           'Unpaid fraction is actual loss, not regret. Cap sensitivities have different specified limits and cannot be ranked by violation rate alone.','']
    for group,s in payload['summary'].items():
        lines += ['## '+group,'',f"Episodes: {s['episodes']}; positive debt: {s['positive_debt']}. "
                  f"Whole future-envelope coverage (capped gains): {float(F(s['decision_envelope_coverage'])):.3%}; "
                  f"raw gains: {float(F(s['raw_envelope_coverage'])):.3%}. "
                  f"Midpoint gain MAE: {float(F(s['gain_midpoint_mae'])):.6f} utility.", '',
                  '| Policy | Unpaid fraction | Regret | Cap violations | Mean quality | Donor loss | Feasible fraction |',
                  '|---|---:|---:|---:|---:|---:|---:|']
        for p,m in s['policies'].items():
            cells=[f"{float(F(m[k])):.6f}" for k in ('unpaid_fraction','regret','cap_violation','mean_post_quality','donor_loss')]
            cells.append(f"{float(F(m['feasible_fraction'])):.6f}" if 'feasible_fraction' in m else 'n/a')
            lines.append('| '+p+' | '+' | '.join(cells)+' |')
        lines += ['', 'Primary feasible-admission violation mass: '+str(s['policies']['bounded_knn']['violations_among_feasible'])+'. '
                  'Infeasible requests remain failures of the requested cap even when the fallback is useful.','']
    lines += ['## Frozen progression checks','']+[f"- {'PASS' if v else 'FAIL'}: {k}" for k,v in payload['screen']['checks'].items()]
    lines += ['', '## Interpretation boundary','',
              'The loss constraint is pathwise only inside its forecast envelope and within the fixed threshold-policy class. '
              'No-neighbor-future leakage is enforced, but the forecast is not calibrated. Out-of-envelope observations trigger '
              'protected greedy fallback; missed opportunities cannot be repaired retrospectively. Every actually selected path '
              'respects the byte cap, donor loss limit, recipient reference floor and single-transfer restriction. These checks '
              'are not proofs of stall protection, perceptual benefit, novel scheduling theory or performance on unseen scenes.', '']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'causal_compensation/results/development_v1')
    args=parser.parse_args()
    if args.output.exists(): parser.error('output exists; preserve prior outcomes')
    payload=encode(analysis(progress=True))
    args.output.mkdir(parents=True)
    (args.output/'results.json').write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
    (args.output/'REPORT.md').write_text(report(payload),encoding='utf-8')
    source=sorted(p for p in (ROOT/'causal_compensation').iterdir() if p.suffix=='.py' or p.name in ('PLAN.md','THEORY.md'))
    meta={'exposed_development_only':True,'python':platform.python_version(),
          'source_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in source},
          'input_sha256':{p.relative_to(ROOT).as_posix():sha(p) for p in source_paths()},
          'result_sha256':{p.name:sha(p) for p in args.output.iterdir() if p.is_file()},
          'scientific_sha256':hashlib.sha256(json.dumps(payload,sort_keys=True,separators=(',',':')).encode()).hexdigest()}
    (args.output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'episodes':len(payload['rows']),'screen':payload['screen'],'scientific_sha256':meta['scientific_sha256']},indent=2))


if __name__=='__main__': main()
