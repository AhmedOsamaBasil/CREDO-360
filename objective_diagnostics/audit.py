"""Complete exposed-data replay, independent window accounting and LP checks."""
import argparse
import csv
import gzip
import itertools
import json
import platform
from pathlib import Path
import numpy as np
from objective_diagnostics.run import (ROOT,COHORTS,SCENARIOS,POLICIES,CANDIDATES,HORIZON,
    model_for,make_plan,catalogue,references,simulate,summarize,contrasts,development_screen,
    label_array,sha256,mode_for,pairs)
from horizon_recovery.audit import source_hashes,check_contract
from feasibility_recovery.audit import verify_hashes,assert_row_equal
from feasibility_recovery.run import read_csv


def balance(rows,mode,last):
    if mode=='memoryless': return HORIZON*np.maximum(last,0)
    if not rows: return np.zeros(5)
    if mode=='bank': return np.sum(rows,axis=0)
    # Enumerate suffix sums independently of the implementation's cumulative sum.
    return np.max(np.vstack([np.zeros(5)]+[np.sum(rows[k:],axis=0) for k in range(len(rows))]),axis=0)


def audit(output):
    meta=json.loads((output/'metadata.json').read_text())
    assert meta['development_only'] and not meta['fresh_holdout']
    modes=source_hashes(meta['source_sha256'])
    verify_hashes(output,meta['result_sha256'])
    models,labels={},{}
    for cohort,path in COHORTS.items():
        verify_hashes(path,meta['input_sha256'][cohort])
        models[cohort]=model_for(cohort)
        m=models[cohort]
        labels[cohort]=label_array(path/'heldout_quality.csv',m['split']['test'],m['contexts'])
    saved_models=json.loads((output/'models.json').read_text())
    for c,m in models.items():
        for field in ('predicted','sizes','scores'):
            np.testing.assert_allclose(saved_models[c][field],m[field],atol=0,rtol=0)
        assert saved_models[c]['radius']==m['radius'] and saved_models[c]['split']==m['split']
    plans=[make_plan(i,models[c],c) for c in COHORTS for i in range(6)]
    assert plans==json.loads((output/'plans.json').read_text())
    by_key={(p['cohort'],p['seed']):p for p in plans}
    saved_refs=json.loads((output/'contracts.json').read_text())
    assert set(saved_refs)=={f"{p['cohort']}:{p['seed']}:{s}" for p in plans for s in SCENARIOS}
    supports=0
    for plan in plans:
        m=models[plan['cohort']]
        for scenario in SCENARIOS:
            replay=references(m,plan,scenario)
            original=saved_refs[f"{plan['cohort']}:{plan['seed']}:{scenario}"]
            assert set(original)==set(replay)
            for epoch,variants in original.items():
                assert set(variants)=={'floor','fair'}
                q,costs,_,_=catalogue(m,plan,int(epoch),scenario,periods=6)
                for target,cap in (('floor',4),('fair',5)):
                    a,b=variants[target],replay[epoch][target]
                    assert a['target_cap']==cap
                    check_contract(a,b,q,costs,m['radius'],b['forecast_capacity_mbps']*1e6*10/8)
                    supports+=len(a['witness'])
        print(f"verified references {plan['cohort']}:{plan['seed']}",flush=True)
    expected_keys={(p['cohort'],p['seed'],s,policy) for p in plans for s in SCENARIOS for policy in POLICIES}
    seen,summaries,action_sets=set(),[],{}
    total,clock_error,byte_excess=0,0.,0.
    with gzip.open(output/'measurements.csv.gz','rt',newline='',encoding='utf-8') as f:
        for key,group in itertools.groupby(csv.DictReader(f),lambda r:(r['cohort'],int(r['seed']),r['scenario'],r['policy'])):
            assert key in expected_keys and key not in seen
            seen.add(key)
            rows=list(group); assert len(rows)==600
            cohort,seed,scenario,policy=key
            p,m=by_key[(cohort,seed)],models[cohort]
            expected=simulate(m,*labels[cohort],p,scenario,policy,saved_refs[f'{cohort}:{seed}:{scenario}'])
            history=[]; last=np.zeros(5); mode=mode_for(policy)
            for t in range(120):
                block=rows[5*t:5*t+5]
                def values(name): return np.array([float(r[name]) for r in block])
                prior=history[-HORIZON:]
                retained=history[-(HORIZON-1):]
                before=balance(prior,mode,last); after_expiry=balance(retained,mode,last)
                expired=history[-HORIZON] if t>=HORIZON else np.zeros(5)
                np.testing.assert_allclose(values('expired_signed_residual'),expired,atol=1e-9,rtol=0)
                np.testing.assert_allclose(values('expiry_state_change'),np.maximum(after_expiry,0)-np.maximum(before,0),atol=1e-9,rtol=0)
                np.testing.assert_allclose(values('ledger_balance_before'),after_expiry,atol=1e-9,rtol=0)
                np.testing.assert_allclose(values('predicted_terminal'),np.maximum(after_expiry+values('target')-values('predicted'),0),atol=1e-9,rtol=0)
                residual=values('target')-values('quality')
                np.testing.assert_allclose(values('signed_residual'),residual,atol=1e-9,rtol=0)
                history.append(residual); last=residual
                np.testing.assert_allclose(values('ledger_balance_after'),balance(history[-HORIZON:],mode,last),atol=1e-9,rtol=0)
                byte_sum=values('bytes').sum()
                byte_excess=max(byte_excess,byte_sum-values('nash_bytes')[0])
                assert byte_sum<=values('nash_bytes')[0]+1e-8<=values('budget_bytes')[0]+2e-8
                if scenario=='range_ceiling' and 40<=t<80:
                    r=block[p['impaired_user']]
                    if float(r['sender_quality_range'])>1e-12:
                        assert float(r['cap_relative_drop'])>=.5-1e-10
            for a,b in zip(rows,expected):
                assert_row_equal(a,b,ignored=('decision_ms',))
                assert np.isfinite(float(a['decision_ms'])) and float(a['decision_ms'])>=0
                clock_error=max(clock_error,abs(float(a['buffer_before_s'])+10+float(a['stall_s'])-float(a['round_duration_s'])-float(a['buffer_after_s'])))
                b['decision_ms']=float(a['decision_ms']);total+=1
            summaries.append(summarize(expected,p['impaired_user']))
            action_sets[key]=np.array([r['action'] for r in expected])
            if scenario==SCENARIOS[-1] and policy==POLICIES[-1]:
                print(f'verified records {cohort}:{seed}',flush=True)
    assert seen==expected_keys and total==meta['rows']==216000 and len(seen)==meta['episodes']==360
    assert clock_error<1e-8
    for filename,expected in [('seed_metrics.csv',summaries),('paired_diagnostics.csv',contrasts(summaries))]:
        actual=read_csv(output/filename);assert len(actual)==len(expected)
        for a,b in zip(actual,expected):assert_row_equal(a,b)
    assert development_screen(summaries)==meta['screen']
    disagreements=[]
    for p in plans:
        for s in SCENARIOS:
            key=(p['cohort'],p['seed'],s)
            for a,b in pairs():
                disagreements.append({'cohort':p['cohort'],'seed':p['seed'],'scenario':s,'candidate':a,'baseline':b,
                    'disagreements':int(np.sum(action_sets[key+(a,)]!=action_sets[key+(b,)])),'comparisons':600})
    actual=read_csv(output/'action_disagreements.csv');assert len(actual)==len(disagreements)
    for a,b in zip(actual,disagreements):assert_row_equal(a,b)
    diagnostic_path=output/'diagnostics/manifest.json'
    if diagnostic_path.exists():
        d=json.loads(diagnostic_path.read_text())
        verify_hashes(output,d['inputs']);verify_hashes(output/'diagnostics',d['outputs'])
        assert sha256(ROOT/'objective_diagnostics/analyze.py')==d['analysis_source_sha256']
    return {'passed':True,'development_only':True,'scientific_rows_replayed':total,'episodes':len(seen),
            'joint_support_witnesses_checked':supports,'maximum_clock_residual_s':clock_error,
            'maximum_bytes_above_nash':byte_excess,'independent_expiry_bank_and_suffix_checks':True,
            'normalized_impairment_checks':True,'source_data_result_hashes_verified':True,'runtime_replayed':False,
            'development_promising':{p:v['development_promising'] for p,v in meta['screen'].items()},
            'platform':platform.platform(),'python':platform.python_version(),'numpy':np.__version__,
            'audit_source_sha256':sha256(Path(__file__)),'source_verification':modes}


if __name__=='__main__':
    parser=argparse.ArgumentParser(__doc__)
    parser.add_argument('--output',type=Path,default=ROOT/'objective_diagnostics/results/development_v1')
    parser.add_argument('--save',action='store_true')
    parser.add_argument('--report-name',default='integrity_audit.json')
    args=parser.parse_args()
    if Path(args.report_name).name!=args.report_name or not args.report_name.endswith('.json'):
        parser.error('local JSON report name required')
    report=audit(args.output)
    if args.save:
        with (args.output/args.report_name).open('x',encoding='utf-8') as f:json.dump(report,f,indent=2);f.write('\n')
    print(json.dumps(report,indent=2))
