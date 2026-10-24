"""Locked factorial DEVELOPMENT on two already exposed catalogues."""
from __future__ import annotations
import argparse
import csv
import gzip
import io
import json
import platform
import subprocess
import time
from pathlib import Path
import numpy as np
from objective_diagnostics.core import (POLICIES,CANDIDATES,DIRECT,HORIZON,STRENGTH,
    Ledger,mode_for,contract,select,range_cap)
from horizon_recovery.run import ROOT,fit,label_array,quality_index,summarize as old_summary
from recovery_pilot.run import processor_sharing,sha256,write_csv
from live_testbed.playback_clock import advance_round

COHORTS = {'exposed_v2':ROOT/'feasibility_recovery/data/v2','exposed_v3':ROOT/'horizon_recovery/data/v3'}
SCENARIOS = ('capacity_only','fixed_ceiling','range_ceiling')
METRICS = ('worst_user_quality','worst_user_psnr_db','mean_quality','cumulative_shortfall',
           'post_restoration_shortfall','impaired_restoration_shortfall','stall_s_per_user','switch_frequency')
STATEFUL = ('floor_bank','floor_nobank','fair_bank','fair_nobank')


def model_for(cohort):
    return fit(COHORTS[cohort],development=(cohort=='exposed_v2'))


def make_plan(index,model,cohort):
    rng = np.random.default_rng(202610500+index)
    capacity = np.clip(rng.normal(3,.3,120),1,4.5)
    capacity[np.arange(120)%8 >= 5] *= .4
    names = sorted({c for c,_ in model['contexts']})
    return {'cohort':cohort,'seed':202610500+index,
            'subjects':rng.choice(model['split']['test'],5,replace=False).tolist(),
            'contents':[names[(index+u)%3] for u in range(5)],
            'capacities_mbps':capacity.tolist(),'impaired_user':index%5}


def catalogue(model,plan,epoch,scenario,periods=1):
    # The CURRENT reported profile is assumed persistent; no look-ahead transition.
    active = scenario != 'capacity_only' and 40 <= epoch < 80
    predictions,costs,caps,original = [],[],[],[]
    for offset in range(periods):
        ids = [model['contexts'].index((name,(epoch+offset)%6)) for name in plan['contents']]
        q,c = model['predicted'][ids],model['sizes'][ids]
        cap = np.full(5,5)
        if active:
            u = plan['impaired_user']
            cap[u] = 1 if scenario == 'fixed_ceiling' else range_cap(q[u])
        predictions.append(np.take_along_axis(q,np.minimum(np.arange(6),cap[:,None]),axis=1))
        costs.append(c); caps.append(cap); original.append(q)
    return np.asarray(predictions),np.asarray(costs),np.asarray(caps),np.asarray(original)


def references(model,plan,scenario):
    result,previous = {},None
    for epoch in range(120):
        active = scenario != 'capacity_only' and 40 <= epoch < 80
        if epoch%6 == 0 or active != previous:
            predicted,costs,_,_ = catalogue(model,plan,epoch,scenario,periods=6)
            forecast = float(np.mean(plan['capacities_mbps'][max(0,epoch-12):epoch])) if epoch else 3.
            result[str(epoch)] = {}
            for target,cap in (('floor',4),('fair',5)):
                start = time.perf_counter()
                entry = contract(predicted,model['radius'],costs,forecast*1e6*10/8,cap)
                entry.update({'forecast_capacity_mbps':forecast,'target_cap':cap,
                              'contract_ms':1000*(time.perf_counter()-start)})
                result[str(epoch)][target] = entry
        previous = active
    return result


def simulate(model,psnr,ssim,plan,scenario,policy,refs):
    ledger = Ledger(HORIZON,5)
    buffer,previous,elapsed = np.full(5,4.),np.ones(5,int),0.
    rows,contract_epoch = [],0
    sid = [model['split']['test'].index(s) for s in plan['subjects']]
    mode = mode_for(policy)
    target_type = 'fair' if policy.startswith('fair_') else 'floor'
    for t,capacity in enumerate(plan['capacities_mbps']):
        if str(t) in refs: contract_epoch = t
        target = np.array(refs[str(contract_epoch)][target_type]['target'])
        expired,expiry_change = ledger.begin(mode)
        balance = ledger.balance(mode)
        prediction,costs,caps,original = catalogue(model,plan,t,scenario)
        prediction,costs,cap,q_original = prediction[0],costs[0],caps[0],original[0]
        estimate = plan['capacities_mbps'][t-1] if t else 3.
        budget = estimate*1e6*10/8
        start = time.perf_counter()
        action,decision = select(policy,prediction,model['radius'],costs,budget,target,ledger)
        runtime = 1000*(time.perf_counter()-start)
        bytecount = costs[np.arange(5),action]
        completion = processor_sharing(bytecount*8,capacity)
        duration = float(completion.max())
        clock = advance_round(buffer,completion,duration)
        effective = np.minimum(action,cap)
        context = [model['contexts'].index((name,t%6)) for name in plan['contents']]
        # Full label arrays are simulation environment only, never predictor inputs.
        actual_psnr = psnr[sid,context,effective]
        actual_ssim = ssim[sid,context,effective]
        quality = quality_index(actual_psnr)
        ledger.update(target,quality)
        after = ledger.balance(mode)
        for u in range(5):
            mean = float(prediction[u,action[u]])
            quality_range = float(q_original[u].max()-q_original[u,0])
            drop = float(q_original[u].max()-q_original[u,:cap[u]+1].max())
            rows.append({'cohort':plan['cohort'],'seed':plan['seed'],'scenario':scenario,'policy':policy,
                'horizon':HORIZON,'strength':STRENGTH,'epoch':t,'user':u,'subject':plan['subjects'][u],
                'content':plan['contents'][u],'segment':t%6,'action':int(action[u]),'displayed_action':int(effective[u]),
                'nash_action':int(decision['nash_action'][u]),'quality':float(quality[u]),'vw_psnr_db':float(actual_psnr[u]),
                'vw_ssim':float(actual_ssim[u]),'predicted':mean,'lower':max(1,mean-model['radius']),
                'upper':min(5,mean+model['radius']),'target':float(target[u]),'ledger_balance_before':float(balance[u]),
                'ledger_balance_after':float(after[u]),'state_before':float(max(balance[u],0)) if policy in CANDIDATES else 0.,
                'state_after':float(max(after[u],0)) if policy in CANDIDATES else 0.,
                'expired_signed_residual':float(expired[u]),'expiry_state_change':float(expiry_change[u]),
                'signed_residual':float(target[u]-quality[u]),'predicted_terminal':float(decision['predicted_terminal'][u]),
                'fixed_shortfall':float(max(4-quality[u],0)),'contract_epoch':contract_epoch,'observed_cap':int(cap[u]),
                'sender_quality_range':quality_range,'cap_predicted_drop':drop,
                'cap_relative_drop':drop/quality_range if quality_range>1e-12 else 0.,
                'capacity_mbps':capacity,'budget_bytes':budget,'nash_bytes':decision['nash_bytes'],'bytes':int(bytecount[u]),
                'excess_bytes':float(max(0,bytecount[u]-costs[u,effective[u]])),
                'completion_s':float(completion[u]),'round_duration_s':duration,'clock_before_s':elapsed,
                'buffer_before_s':float(buffer[u]),'buffer_after_s':float(clock.buffer_s[u]),'stall_s':float(clock.stall_s[u]),
                'switched':int(action[u]!=previous[u]),'decision_ms':runtime,'candidate_count':decision['candidate_count']})
        buffer,previous,elapsed = clock.buffer_s,action,elapsed+duration
    return rows


def summarize(rows,impaired):
    result = old_summary(rows,impaired)
    result['cohort'] = rows[0]['cohort']
    psnr = np.array([r['vw_psnr_db'] for r in rows]).reshape(120,5)
    result['worst_user_psnr_db'] = float(psnr.mean(axis=0).min())
    result['quality_at_upper_cap_fraction'] = float(np.mean([r['quality']==5 for r in rows]))
    result['mean_target'] = float(np.mean([r['target'] for r in rows]))
    result['negative_balance_fraction'] = float(np.mean([r['ledger_balance_before']<0 for r in rows]))
    selected = [r for r in rows if r['user']==impaired and 40<=r['epoch']<80]
    result['mean_imposed_absolute_drop'] = float(np.mean([r['cap_predicted_drop'] for r in selected]))
    result['mean_imposed_relative_drop'] = float(np.mean([r['cap_relative_drop'] for r in selected]))
    return result


def pairs():
    result = {(p,'nash') for p in POLICIES if p != 'nash'}
    for p in STATEFUL:
        for b in ('window_maxmin','window_nash',p.split('_')[0]+'_memoryless'):
            result.add((p,b))
    for mode in ('bank','nobank','memoryless'): result.add(('fair_'+mode,'floor_'+mode))
    for target in ('fair','floor'): result.add((target+'_nobank',target+'_bank'))
    return sorted(result)


def contrasts(summaries):
    result,rng = [],np.random.default_rng(202610524)
    for cohort in COHORTS:
        for scenario in SCENARIOS:
            values = {(r['policy'],r['seed']):r for r in summaries if r['cohort']==cohort and r['scenario']==scenario}
            seeds = sorted({k[1] for k in values})
            for candidate,baseline in pairs():
                for metric in METRICS:
                    diff=np.array([values[(candidate,s)][metric]-values[(baseline,s)][metric] for s in seeds])
                    draws=rng.choice(diff,(1000,len(seeds)),replace=True).mean(axis=1)
                    result.append({'cohort':cohort,'scenario':scenario,'candidate':candidate,'baseline':baseline,
                        'metric':metric,'paired_seeds':len(seeds),'mean_delta':float(diff.mean()),
                        'ci95_low':float(np.quantile(draws,.025)),'ci95_high':float(np.quantile(draws,.975))})
    return result


def development_screen(summaries):
    result = {}
    for candidate in STATEFUL:
        checks = {}
        for cohort in COHORTS:
            rows = [r for r in summaries if r['cohort']==cohort and r['scenario']=='range_ceiling']
            means = {p:{m:float(np.mean([r[m] for r in rows if r['policy']==p])) for m in METRICS} for p in POLICIES}
            a=means[candidate]
            for baseline in ('nash',candidate.split('_')[0]+'_memoryless','window_maxmin','window_nash'):
                b=means[baseline]; prefix=cohort+':'+baseline+':'
                checks[prefix+'worst_quality_gain']=a['worst_user_quality']>b['worst_user_quality']
                checks[prefix+'mean_guard']=a['mean_quality']>=b['mean_quality']-.03
                checks[prefix+'shortfall_guard']=a['cumulative_shortfall']<=1.05*b['cumulative_shortfall']
                checks[prefix+'stall_guard']=a['stall_s_per_user']-b['stall_s_per_user'] <= (.05*b['stall_s_per_user'] if b['stall_s_per_user'] else .1)
        result[candidate]={'development_promising':all(checks.values()),'checks':checks}
    return result


def main():
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'objective_diagnostics/results/development_v1')
    args=parser.parse_args()
    if args.output.exists(): parser.error('output exists; preserve every development run')
    args.output.mkdir(parents=True)
    summaries,agreements,plans,all_refs,models = [],[],[],{},{}
    with (args.output/'measurements.csv.gz').open('wb') as binary:
        with gzip.GzipFile(fileobj=binary,mode='wb',filename='',mtime=0) as compressed:
            with io.TextIOWrapper(compressed,encoding='utf-8',newline='') as handle:
                writer=None
                for cohort,data in COHORTS.items():
                    model=model_for(cohort)
                    models[cohort]={k:(v.tolist() if isinstance(v,np.ndarray) else v) for k,v in model.items()}
                    psnr,ssim=label_array(data/'heldout_quality.csv',model['split']['test'],model['contexts'])
                    for index in range(6):
                        plan=make_plan(index,model,cohort); plans.append(plan)
                        for scenario in SCENARIOS:
                            refs=references(model,plan,scenario)
                            all_refs[f"{cohort}:{plan['seed']}:{scenario}"]=refs
                            actions={}
                            for policy in POLICIES:
                                rows=simulate(model,psnr,ssim,plan,scenario,policy,refs)
                                if writer is None:
                                    writer=csv.DictWriter(handle,fieldnames=list(rows[0]));writer.writeheader()
                                writer.writerows(rows)
                                summaries.append(summarize(rows,plan['impaired_user']))
                                actions[policy]=np.array([r['action'] for r in rows])
                            for a,b in pairs():
                                agreements.append({'cohort':cohort,'seed':plan['seed'],'scenario':scenario,'candidate':a,'baseline':b,
                                    'disagreements':int(np.sum(actions[a]!=actions[b])),'comparisons':600})
                            print(f"completed {cohort} seed={plan['seed']} {scenario}",flush=True)
    for name,payload in [('models.json',models),('plans.json',plans),('contracts.json',all_refs)]:
        (args.output/name).write_text(json.dumps(payload,indent=2)+'\n')
    write_csv(args.output/'seed_metrics.csv',summaries)
    write_csv(args.output/'paired_diagnostics.csv',contrasts(summaries))
    write_csv(args.output/'action_disagreements.csv',agreements)
    sources=['objective_diagnostics/'+n for n in ('core.py','run.py','PLAN.md')]
    sources+=['horizon_recovery/core.py','horizon_recovery/run.py','recovery_pilot/core.py','recovery_pilot/run.py',
              'feasibility_recovery/core.py','feasibility_recovery/run.py','live_testbed/playback_clock.py']
    meta={'development_only':True,'fresh_holdout':False,'rows':216000,'episodes':360,'seeds_per_cohort':6,
          'screen':development_screen(summaries),'horizon':HORIZON,'strength':STRENGTH,
          'git_head_at_run':subprocess.check_output(['git','-c',f'safe.directory={ROOT.as_posix()}','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
          'source_sha256':{n:sha256(ROOT/n) for n in sources},
          'input_sha256':{c:{p.name:sha256(p) for p in data.iterdir() if p.is_file()} for c,data in COHORTS.items()},
          'result_sha256':{p.name:sha256(p) for p in args.output.iterdir() if p.is_file()},
          'python':platform.python_version(),'numpy':np.__version__,'platform':platform.platform(),'runtime_injected':False}
    (args.output/'metadata.json').write_text(json.dumps(meta,indent=2)+'\n')
    print(json.dumps({p:r['development_promising'] for p,r in meta['screen'].items()},indent=2))


if __name__ == '__main__': main()
