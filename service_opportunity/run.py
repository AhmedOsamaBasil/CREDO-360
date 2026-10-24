"""Matched exposed-development replay under a fixed absolute service cap."""
import argparse
from fractions import Fraction as F
import gzip
import hashlib
import json
from pathlib import Path
import platform
from recovery_objective.core import Action,Step,Contract,choose
from reserve_recovery.catalogue import summarize_path
from reserve_recovery.run import canonical,encode,sha
from feasibility_frontier.data import load
from service_opportunity.model import (ROOT,CAPACITY,RATIOS,CONTROLS,POLICIES,records,pool,
    forecast,sizes,predicted_periods,valid,optimize,source_paths)
from service_opportunity.service import validate as validate_service


def simulate(e,periods,record,training,rho,policy):
    reserve=rho*sum(p[0].reference_bytes for p in periods)
    debt=e.loss; spent=0; path=[]; logs=[]
    history=[tuple(F(x,1000) for x in q) for q in e.history]
    contract=Contract((F(e.loss,1000),0),(0,0),(0,0))
    oracle=optimize(periods,e.loss,reserve) if policy=='offline' else None
    for t,current in enumerate(periods):
        menu=valid(current,reserve-spent); diagnostics={}
        if policy in ('knn_mpc','persistence_mpc'):
            prefix=record.qualities[:t+1]
            if policy=='knn_mpc': predicted,neighbors=forecast(prefix,e.loss,training)
            else: predicted=(prefix[-1],)*(3-t); neighbors=()
            future=predicted_periods(predicted,tuple(sizes(p) for p in periods[t+1:]))
            gain,cost,planned=optimize((current,)+future,debt,reserve-spent)
            action=next(a for a in menu if a.rungs==planned[0])
            predicted_final=debt-gain
            diagnostics={'neighbors':neighbors,'predicted_qualities':predicted,
                         'predicted_additional_gain_units':gain,'predicted_cost_bytes':cost,
                         'predicted_half_feasible':predicted_final*2<=e.loss,
                         'planned_rungs':planned}
            # Scoring only: these labels never enter forecast/optimizer or state.
            errors=[abs(a-b) for pred,actual in zip(predicted,record.qualities[t+1:])
                    for x,y in zip(pred,actual) for a,b in zip(x,y)]
            diagnostics['future_absolute_error_units']=sum(errors)
            diagnostics['future_label_count']=len(errors)
        elif policy=='offline': action=next(a for a in menu if a.rungs==oracle[2][t])
        else:
            ref=tuple(F(x,1000) for x in current[0].reference)
            choices=tuple(Action(f'r{a.rungs[0]}d{a.rungs[1]}',tuple(F(x,1000) for x in a.quality),a.bytes) for a in menu)
            a=choose(policy,Step(ref,choices,CAPACITY),contract,(F(debt,1000),0),(0,0),history)
            action=next(x for x in menu if f'r{x.rungs[0]}d{x.rungs[1]}'==a.name)
        before=debt; credit=min(debt,action.gain); debt-=credit
        extra=max(action.bytes-action.reference_bytes,0); spent+=extra
        assert action.harm==0 and all(q>=b for q,b in zip(action.quality,action.reference))
        assert action.bytes<=CAPACITY and spent<=reserve
        path.append(action.rungs); history.append(tuple(F(x,1000) for x in action.quality))
        logs.append({'step':t,'rungs':action.rungs,'debt_before':before,'credit_units':credit,
                     'debt_after':debt,'spent_bytes':spent,'remaining_bytes':reserve-spent,**diagnostics})
    out=summarize_path(periods,tuple(path),e.loss)
    assert out['extra_bytes']==spent and out['remaining_fraction']==F(debt,e.loss)
    assert sum(x['credit_units'] for x in logs)+debt==e.loss
    return {'policy':policy,'reserve_fraction':rho,'reserve_bytes':reserve,**out,
            'half_repaid':debt*2<=e.loss,'decisions':logs}


def summarize(rows):
    groups={'all':rows}
    for field in ('scene','cohort'):
        for name in sorted({r[field] for r in rows}): groups[name]=[r for r in rows if r[field]==name]
    out={}
    for name,group in groups.items():
        cells=[]
        for rho in RATIOS:
            for policy in POLICIES:
                selected=[x for r in group for x in r['outcomes'] if x['policy']==policy and x['reserve_fraction']==rho]
                forecasts=[x for r in selected for x in r['decisions'] if x.get('future_label_count',0)>0]
                initial=[r for r in selected if r['decisions'][0].get('predicted_half_feasible',False)]
                cells.append({'reserve_fraction':rho,'policy':policy,'episodes':len(selected),
                    'half_repaid':sum(r['half_repaid'] for r in selected),
                    'mean_unpaid_fraction':sum(r['remaining_fraction'] for r in selected)/len(selected),
                    'mean_worst_quality':sum(r['worst_post_quality'] for r in selected)/len(selected),
                    'mean_quality':sum(r['mean_post_quality'] for r in selected)/len(selected),
                    'mean_extra_bytes':F(sum(r['extra_bytes'] for r in selected),len(selected)),
                    'initial_predicted_feasible':len(initial),
                    'initial_prediction_breaches':sum(not r['half_repaid'] for r in initial),
                    'forecast_mae_quality':F(sum(r['future_absolute_error_units'] for r in forecasts),
                        1000*sum(r['future_label_count'] for r in forecasts)) if forecasts else None})
        out[name]=cells
    return out


def gates(summary,service):
    checks={'nominal_service':service['controlled_contract_pass'],
            'negative_service_detected':service['negative_control_detected']}
    for cohort in ('v2','v3'):
        cells={x['policy']:x for x in summary[cohort] if x['reserve_fraction']==1}
        candidate=cells['knn_mpc']
        for policy in CONTROLS:
            checks[f'{cohort}_unpaid_better_{policy}']=candidate['mean_unpaid_fraction']<cells[policy]['mean_unpaid_fraction']
            checks[f'{cohort}_half_not_lower_{policy}']=candidate['half_repaid']>=cells[policy]['half_repaid']
        checks[f'{cohort}_oracle_gap']=cells['offline']['mean_unpaid_fraction']<min(cells[p]['mean_unpaid_fraction'] for p in CONTROLS)
    return {'passed':all(checks.values()),'checks':checks}


def analysis(service_data,progress=False):
    recs=records(); table={r.key:r for r in recs}; rows=[]
    for number,(e,periods) in enumerate(load(),1):
        record=table[e.key]; training=pool(recs,record)
        outcomes=[simulate(e,periods,record,training,rho,p) for rho in RATIOS for p in POLICIES]
        for rho in RATIOS:
            selected=[x for x in outcomes if x['reserve_fraction']==rho]
            oracle=next(x for x in selected if x['policy']=='offline')
            assert all(x['remaining_fraction']>=oracle['remaining_fraction'] for x in selected)
        rows.append({'key':e.key,'scene':e.scene,'cohort':e.cohort,'recipient':e.recipient,'donor':e.donor,
                     'loss_units':e.loss,'training_count':len(training),'outcomes':outcomes})
        if progress and number%28==0: print(f'Exposed service/model replay {number}/168',flush=True)
    summary=summarize(rows); service=validate_service(service_data)
    disagreements={}
    for policy in CONTROLS:
        count=0
        for row in rows:
            a=next(x for x in row['outcomes'] if x['policy']=='knn_mpc' and x['reserve_fraction']==1)
            b=next(x for x in row['outcomes'] if x['policy']==policy and x['reserve_fraction']==1)
            count+=sum(x['rungs']!=y['rungs'] for x,y in zip(a['decisions'],b['decisions']))
        disagreements[policy]={'different_actions':count,'total':168*4}
    return {'exposed_only':True,'fresh_holdout_used':False,'capacity_bytes':CAPACITY,'rows':rows,
            'summary':summary,'service_validation':service,'progression':gates(summary,service),
            'primary_action_disagreement':disagreements}


def report(p):
    lines=['# Controlled service and causal opportunity development','',
        'Exposed data only; oracle-current viewport qualities. No independent confirmation or human QoE claim.','',
        '## Controlled service probes','',json.dumps(p['service_validation'],indent=2),'',
        f"Development progression: **{p['progression']['passed']}**. All individual checks are in the result artifact.",'']
    for group,cells in p['summary'].items():
        lines += ['## '+group,'','| Reserve / baseline | Policy | Half-repaid / episodes | Mean unpaid | Mean worst quality | Mean quality | Forecast MAE | Predicted feasible / breaches |',
                  '|---:|---|---:|---:|---:|---:|---:|---:|']
        for r in cells:
            mae='n/a' if r['forecast_mae_quality'] is None else f"{float(F(r['forecast_mae_quality'])):.4f}"
            lines.append(f"| {r['reserve_fraction']} | {r['policy']} | {r['half_repaid']}/{r['episodes']} | "
                f"{float(F(r['mean_unpaid_fraction'])):.6f} | {float(F(r['mean_worst_quality'])):.4f} | "
                f"{float(F(r['mean_quality'])):.4f} | {mae} | {r['initial_predicted_feasible']}/{r['initial_prediction_breaches']} |")
        lines.append('')
    lines += ['## Boundaries','',
        'The network experiment tests an engineered reservation and synthetic byte transfers, not real path availability, '
        'an implemented player or new content. The point forecast is uncalibrated; predicted half-repayment is not a guarantee. '
        'All 168 pairs are retained and are dependent within six exposed scenes. No confidence claim is made from these counts.',
        '','The matched persistence controller distinguishes forecasting from lookahead optimization. '
        'Offline results use future labels explicitly and are not a deployable method. Quality tradeoffs remain visible.','']
    return '\n'.join(lines)


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'service_opportunity/results/development_v1')
    parser.add_argument('--service',type=Path,default=ROOT/'service_opportunity/results/service_v1.json')
    args=parser.parse_args()
    if args.output.exists(): parser.error('refusing to overwrite results')
    p=encode(analysis(json.loads(args.service.read_text()),True)); args.output.mkdir(parents=True)
    (args.output/'results.json.gz').write_bytes(gzip.compress(canonical(p),mtime=0))
    (args.output/'REPORT.md').write_text(report(p),encoding='utf-8')
    files=sorted(f for f in (ROOT/'service_opportunity').iterdir() if f.suffix=='.py' or f.name in ('PLAN.md','THEORY.md'))
    files += [ROOT/n for n in ('recovery_objective/core.py','reserve_recovery/catalogue.py','reserve_recovery/run.py',
        'reserve_recovery/core.py','reserve_recovery/cases.py','feasibility_frontier/core.py','feasibility_frontier/data.py',
        'causal_compensation/data.py')]
    meta={'source_sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in files},
          'input_sha256':{f.relative_to(ROOT).as_posix():sha(f) for f in (*source_paths(),args.service)},
          'result_sha256':{f.name:sha(f) for f in args.output.iterdir() if f.is_file()},
          'scientific_sha256':hashlib.sha256(canonical(p)).hexdigest(),
          'python':platform.python_version(),'exposed_only':True}
    (args.output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({'scientific_sha256':meta['scientific_sha256'],'progression':p['progression']},indent=2))


if __name__=='__main__': main()
