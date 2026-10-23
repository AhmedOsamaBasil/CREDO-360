"""Replay every scientific row and independently inspect contracts and ledgers."""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import itertools
import json
import platform
from pathlib import Path
import numpy as np
from feasibility_recovery.audit import verify_hashes, assert_row_equal
from horizon_recovery.core import action_table
from horizon_recovery.run import (ROOT, fit, label_array, make_plan, contracts, tables,
    simulate, summarize, comparisons, SCENARIOS, POLICIES, read_csv, sha256, quality_index)
from horizon_recovery.evaluate import screen


def source_hashes(recorded):
    modes = {}
    for name, digest in recorded.items():
        raw = (ROOT / name).read_bytes()
        raw.decode('utf-8')
        lf = raw.replace(b'\r\n', b'\n')
        if hashlib.sha256(raw).hexdigest() == digest:
            modes[name] = 'byte_exact'
        elif digest in {hashlib.sha256(lf).hexdigest(), hashlib.sha256(lf.replace(b'\n', b'\r\n')).hexdigest()}:
            modes[name] = 'LF_CRLF_only'
        else:
            raise AssertionError('source hash mismatch: '+name)
    return modes


def check_contract(saved, replay, prediction, costs, radius, budget):
    for key in ('target', 'ceiling', 'height', 'expected_quality'):
        # Degenerate LP witnesses can differ between solvers; target is unique,
        # expected-quality surplus need not be. Validate surplus via witness.
        if key != 'expected_quality':
            np.testing.assert_allclose(saved[key], replay[key], atol=1e-7, rtol=0)
    assert saved['forecast_capacity_mbps'] == replay['forecast_capacity_mbps']
    assert np.isfinite(saved['contract_ms']) and saved['contract_ms'] >= 0
    assert all(w['period'] in range(6) for w in saved['witness'])
    expected = np.zeros(5)
    for t in range(6):
        support = [w for w in saved['witness'] if w['period'] == t]
        assert abs(sum(w['probability'] for w in support)-1) <= 1e-7
        table = action_table(prediction[t], radius, costs[t], budget)
        for w in support:
            assert 0 < w['probability'] <= 1+1e-8
            action = np.asarray(w['action'])
            assert action.shape == (5,) and np.issubdtype(action.dtype, np.integer)
            assert np.all((action >= 0) & (action < 6))
            quality = prediction[t, np.arange(5), action]
            bytecount = costs[t, np.arange(5), action].sum()
            np.testing.assert_allclose(w['quality'], quality, atol=1e-10, rtol=0)
            assert abs(w['bytes']-bytecount) <= 1e-8
            assert abs(w['byte_cap']-table['nash_bytes']) <= 1e-8
            assert bytecount <= table['nash_bytes']+1e-8 <= budget+2e-8
            expected += w['probability']*quality/6
    np.testing.assert_allclose(saved['expected_quality'], expected, atol=1e-7, rtol=0)
    assert np.all(expected >= np.array(saved['target'])-1e-7)


def audit(data, output):
    meta = json.loads((output/'metadata.json').read_text())
    modes = source_hashes(meta['source_sha256'])
    verify_hashes(data, meta['input_sha256'])
    verify_hashes(output, meta['result_sha256'])
    dm = json.loads((data/'metadata.json').read_text())
    verify_hashes(data, dm['result_sha256'])
    modes.update(source_hashes(dm['preparation_sources_sha256']))
    assert sha256(ROOT/'horizon_recovery/manifest.json') == dm['manifest_sha256']
    model = fit(data)
    saved = json.loads((output/'calibration.json').read_text())
    for key in ('predicted', 'scores'):
        np.testing.assert_allclose(saved[key], model[key], atol=0, rtol=0)
    assert saved['radius'] == model['radius'] and saved['split'] == model['split']
    psnr, ssim = label_array(data/'heldout_quality.csv', model['split']['test'], model['contexts'])
    panels = json.loads((output/'panel_coverage.json').read_text())
    errors = np.max(np.abs(quality_index(psnr)-model['predicted']), axis=(1,2))
    assert panels == [{'subject': s, 'max_error': float(e), 'covered': bool(e <= model['radius']+1e-12)}
                      for s,e in zip(model['split']['test'],errors)]
    plans = [make_plan(i, model) for i in range(meta['seeds'])]
    assert plans == json.loads((output/'plans.json').read_text())
    references = json.loads((output/'contracts.json').read_text())
    assert set(references) == {f"{p['seed']}:{s}" for p in plans for s in SCENARIOS}
    witnesses = 0
    for plan in plans:
        for scenario in SCENARIOS:
            original = references[f"{plan['seed']}:{scenario}"]
            replay = contracts(model, plan, scenario)
            assert set(original) == set(replay)
            for epoch, saved_contract in original.items():
                prediction, costs = tables(model, plan, int(epoch), scenario, periods=6)
                budget = replay[epoch]['forecast_capacity_mbps']*1e6*10/8
                check_contract(saved_contract, replay[epoch], prediction, costs, model['radius'], budget)
                witnesses += len(saved_contract['witness'])
        print(f"verified contracts seed={plan['seed']}", flush=True)
    by_seed = {p['seed']: p for p in plans}
    expected_keys = {(p['seed'], s, policy) for p in plans for s in SCENARIOS for policy in POLICIES}
    seen, summaries, action_sets = set(), [], {}
    total, clock_residual, cap_excess = 0, 0., 0.
    config = json.loads((ROOT/'horizon_recovery/frozen_config.json').read_text())
    assert config == meta['config']
    with gzip.open(output/'measurements.csv.gz', 'rt', newline='', encoding='utf-8') as handle:
        for key, group in itertools.groupby(csv.DictReader(handle), lambda r: (int(r['seed']),r['scenario'],r['policy'])):
            assert key not in seen and key in expected_keys
            seen.add(key)
            rows, plan = list(group), by_seed[key[0]]
            assert len(rows) == 600
            replay = simulate(model,psnr,ssim,plan,key[1],key[2],config['horizon'],config['strength'],references[f'{key[0]}:{key[1]}'])
            history = []
            for t in range(120):
                block = rows[5*t:5*t+5]
                def values(name):
                    return np.array([float(r[name]) for r in block])
                h = config['horizon']
                if not history:
                    state = np.zeros(5)
                elif key[2] == 'memoryless_scaled':
                    state = h*np.maximum(history[-1],0)
                elif key[2] == 'memoryless_unscaled':
                    state = np.maximum(history[-1],0)
                else:
                    state = np.maximum(np.sum(history[-h:],axis=0),0)
                np.testing.assert_allclose(values('state_before'),state,atol=1e-9,rtol=0)
                expiry = history[-h] if len(history) >= h else np.zeros(5)
                np.testing.assert_allclose(values('expired_signed_residual'),expiry,atol=1e-9,rtol=0)
                residual = values('target')-values('quality')
                np.testing.assert_allclose(values('signed_residual'),residual,atol=1e-9,rtol=0)
                history.append(residual)
                byte_sum = values('bytes').sum()
                cap_excess = max(cap_excess,byte_sum-values('nash_bytes')[0])
                assert byte_sum <= values('nash_bytes')[0]+1e-8 <= values('budget_bytes')[0]+2e-8
            for actual, expected in zip(rows,replay):
                assert_row_equal(actual,expected,ignored=('decision_ms',))
                assert np.isfinite(float(actual['decision_ms'])) and float(actual['decision_ms']) >= 0
                residual = abs(float(actual['buffer_before_s'])+10+float(actual['stall_s'])-
                               float(actual['round_duration_s'])-float(actual['buffer_after_s']))
                clock_residual = max(clock_residual,residual)
                expected['decision_ms'] = float(actual['decision_ms'])
                total += 1
            summaries.append(summarize(replay,plan['impaired_user']))
            action_sets[key] = np.array([r['action'] for r in replay])
            if key[1] == SCENARIOS[-1] and key[2] == POLICIES[-1]:
                print(f'verified rows seed={key[0]}',flush=True)
    assert seen == expected_keys and total == meta['rows'] and clock_residual < 1e-8
    saved_summaries = read_csv(output/'seed_metrics.csv')
    assert len(saved_summaries) == len(summaries)
    for a,b in zip(saved_summaries,summaries):
        assert_row_equal(a,b)
    paired = comparisons(summaries)
    saved_paired = read_csv(output/'paired_diagnostics.csv')
    assert len(paired) == len(saved_paired)
    for a,b in zip(saved_paired,paired):
        assert_row_equal(a,b)
    agreement = []
    for p in plans:
        for s in SCENARIOS:
            for b in POLICIES:
                if b != 'window_recovery':
                    count = np.sum(action_sets[(p['seed'],s,b)] != action_sets[(p['seed'],s,'window_recovery')])
                    agreement.append({'seed':p['seed'],'scenario':s,'baseline':b,'disagreements':int(count),'comparisons':600})
    stored = read_csv(output/'action_disagreements.csv')
    assert len(stored) == len(agreement)
    for a,b in zip(stored,agreement):
        assert_row_equal(a,b)
    passed,detail = screen(summaries,paired,agreement)
    assert passed == meta['progression_gate_passed'] and detail == meta['screen_details']
    diagnostics = output/'diagnostics/manifest.json'
    if diagnostics.exists():
        d = json.loads(diagnostics.read_text())
        verify_hashes(output,d['inputs'])
        verify_hashes(output/'diagnostics',d['outputs'])
        assert sha256(ROOT/'horizon_recovery/analyze.py') == d['analysis_source_sha256']
    return {'passed':True,'scientific_rows_replayed':total,'episodes':len(seen),
            'joint_support_witnesses_checked':witnesses,'maximum_clock_residual_s':clock_residual,
            'maximum_bytes_above_nash':cap_excess,'progression_gate_passed':passed,
            'source_data_results_verified':True,'ledger_independently_checked':True,
            'runtime_replayed':False,'platform':platform.platform(),'python':platform.python_version(),
            'numpy':np.__version__,'audit_source_sha256':sha256(Path(__file__)), 'source_verification':modes}


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--data',type=Path,default=ROOT/'horizon_recovery/data/v3')
    parser.add_argument('--output',type=Path,default=ROOT/'horizon_recovery/results/v3')
    parser.add_argument('--save',action='store_true')
    parser.add_argument('--report-name',default='integrity_audit.json')
    args = parser.parse_args()
    if Path(args.report_name).name != args.report_name or not args.report_name.endswith('.json'):
        parser.error('local JSON report name required')
    report = audit(args.data,args.output)
    if args.save:
        with (args.output/args.report_name).open('x',encoding='utf-8') as f:
            json.dump(report,f,indent=2); f.write('\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
