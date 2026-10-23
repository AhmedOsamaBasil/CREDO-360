"""Reproduce every exposed-data summary and the six-way selection rule."""
import json
import platform
from pathlib import Path
import numpy as np
from horizon_recovery.run import (ROOT, fit, label_array, make_plan, contracts, tables, simulate,
    summarize, read_csv, sha256, SCENARIOS, POLICIES)
from horizon_recovery.audit import source_hashes, check_contract
from feasibility_recovery.audit import verify_hashes, assert_row_equal


def main():
    output = ROOT/'horizon_recovery/results/development_v1'
    data = ROOT/'feasibility_recovery/data/v2'
    meta = json.loads((output/'metadata.json').read_text())
    source_hashes({'horizon_recovery/'+n:h for n,h in meta['source_sha256'].items()})
    verify_hashes(data,meta['input_sha256'])
    verify_hashes(output,meta['result_sha256'])
    model = fit(data,development=True)
    psnr,ssim = label_array(data/'heldout_quality.csv',model['split']['test'],model['contexts'])
    plans = [make_plan(i,model,True) for i in range(6)]
    assert plans == json.loads((output/'plans.json').read_text())
    cached = json.loads((output/'contracts.json').read_text())
    for plan in plans:
        for scenario in SCENARIOS:
            reference = contracts(model,plan,scenario)
            original = cached[f"{plan['seed']}:{scenario}"]
            assert set(original) == set(reference)
            for epoch, row in original.items():
                predicted,costs = tables(model,plan,int(epoch),scenario,periods=6)
                budget = reference[epoch]['forecast_capacity_mbps']*1e6*10/8
                check_contract(row,reference[epoch],predicted,costs,model['radius'],budget)
    selection, episodes = [], 0
    for horizon in (12,24):
        for strength in (.5,2.,8.):
            actual = read_csv(output/f'metrics_h{horizon}_s{strength:g}.csv')
            expected = []
            for plan in plans:
                for scenario in SCENARIOS:
                    for policy in POLICIES:
                        rows = simulate(model,psnr,ssim,plan,scenario,policy,horizon,strength,cached[f"{plan['seed']}:{scenario}"])
                        expected.append(summarize(rows,plan['impaired_user']))
                        episodes += 1
            assert len(actual) == len(expected) == 120
            for a,b in zip(actual,expected):
                assert_row_equal(a,b,ignored=('decision_ms_median',))
            metrics = ('worst_user_quality','mean_quality','cumulative_shortfall','stall_s_per_user')
            means = {p:{m:np.mean([r[m] for r in expected if r['scenario']=='known_ceiling' and r['policy']==p]) for m in metrics} for p in POLICIES}
            candidate = means['window_recovery']
            checks = []
            diagnostic = {'horizon':horizon,'strength':strength}
            for policy in ('nash','memoryless_scaled'):
                baseline = means[policy]
                for metric in metrics:
                    diagnostic[f'delta_{policy}_{metric}'] = float(candidate[metric]-baseline[metric])
                checks += [candidate['worst_user_quality'] > baseline['worst_user_quality'],
                           candidate['mean_quality'] >= baseline['mean_quality']-.03,
                           candidate['cumulative_shortfall'] <= 1.05*baseline['cumulative_shortfall'],
                           candidate['stall_s_per_user']-baseline['stall_s_per_user'] <= (.05*baseline['stall_s_per_user'] if baseline['stall_s_per_user'] else .1)]
            diagnostic['development_screen_passed'] = all(checks)
            selection.append(diagnostic)
            print(f'verified development H={horizon}, strength={strength}',flush=True)
    saved = read_csv(output/'selection.csv')
    assert len(saved) == len(selection) == 6
    for a,b in zip(saved,selection):
        # CSV Boolean spellings are explicit, not float-convertible.
        assert a.pop('development_screen_passed') == str(b['development_screen_passed'])
        assert_row_equal(a,{k:v for k,v in b.items() if k != 'development_screen_passed'})
    eligible = [r for r in selection if r['development_screen_passed']] or selection
    best = sorted(eligible,key=lambda r:(-r['delta_nash_worst_user_quality'],r['horizon'],r['strength']))[0]
    selected = json.loads((output/'selected.json').read_text())
    assert selected == json.loads((ROOT/'horizon_recovery/frozen_config.json').read_text())
    assert all(selected[k] == best[k] for k in ('horizon','strength','development_screen_passed'))
    report = {'passed':True,'configurations':6,'episodes_replayed':episodes,'user_rounds_recomputed':episodes*600,
              'selected_horizon':best['horizon'],'selected_strength':best['strength'],
              'platform':platform.platform(),'python':platform.python_version(),'numpy':np.__version__,
              'audit_source_sha256':sha256(Path(__file__)),'runtime_replayed':False}
    with (output/'integrity_audit.json').open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2); f.write('\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
