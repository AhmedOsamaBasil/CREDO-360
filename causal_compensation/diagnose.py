"""Post-hoc opportunity/headroom diagnosis; never used to retune the frozen batch."""
import csv
from fractions import Fraction as F
import hashlib
import json
from causal_compensation.data import ROOT,SOURCES,quality_units
from causal_compensation.run import encode,sha,mean


def diagnosis(output):
    data=json.loads((output/'results.json').read_text())
    labels={}
    for cohort,folder in SOURCES.items():
        for name in ('calibration_quality.csv','heldout_quality.csv'):
            with (ROOT/folder/name).open(newline='') as f:
                for r in csv.DictReader(f):
                    labels[cohort,r['content'],int(r['subject']),int(r['segment']),int(r['ladder_index'])]=quality_units(r['vw_psnr_db'])
    episodes=[]
    for r in data['rows']:
        e=r['episode']; d=e['loss']; offers=e['offers'][2:]
        oracle_gain=max(o['gain'] for o in offers)
        menu_multi=sum(o['gain'] for o in offers)
        # Optimistic bound: discard all byte/donor/one-transfer limits, but keep
        # the declared recipient baseline and the actual encoded ladder.
        unlimited=[]
        for t in range(2,6):
            q=[labels[e['cohort'],e['scene'],e['recipient'],t,j] for j in range(6)]
            unlimited.append(max(q)-q[2])
        episodes.append({'key':r['key'],'cohort':e['cohort'],'scene':e['scene'],'D_units':d,
            'positive_offers':sum(o['gain']>0 for o in offers),'oracle_one_transfer_gain_units':oracle_gain,
            'oracle_one_transfer_unpaid':F(max(d-oracle_gain,0),d) if d else F(0),
            'menu_all_periods_gain_upper_units':menu_multi,
            'unrestricted_ladder_all_periods_gain_upper_units':sum(unlimited),
            'half_repayment_possible_one_transfer':2*oracle_gain>=d,
            'half_repayment_possible_relaxed_menu':2*menu_multi>=d,
            'half_repayment_possible_unrestricted_ladder':2*sum(unlimited)>=d,
            'all_forecast_lower_bounds_zero':all(lo==0 for lo,hi in r['forecast']['bounds']),
            'mean_forecast_width_units':mean(F(hi-lo) for lo,hi in r['forecast']['bounds']),
            'candidate_loss':F(r['outcomes']['bounded_knn']['expected']['unpaid_fraction']),
            'maxmin_loss':F(r['outcomes']['rolling_maxmin']['expected']['unpaid_fraction'])})
    groups={}
    for group in ('all','v2','v3'):
        rows=episodes if group=='all' else [r for r in episodes if r['cohort']==group]
        groups[group]={'episodes':len(rows),'positive_offers':sum(r['positive_offers'] for r in rows),'total_offers':4*len(rows),
            'mean_D_units':mean(r['D_units'] for r in rows),'min_D_units':min(r['D_units'] for r in rows),
            'max_D_units':max(r['D_units'] for r in rows),
            'max_single_gain_units':max(r['oracle_one_transfer_gain_units'] for r in rows),
            'mean_oracle_unpaid_fraction':mean(r['oracle_one_transfer_unpaid'] for r in rows),
            'one_transfer_feasible_count':sum(r['half_repayment_possible_one_transfer'] for r in rows),
            'relaxed_menu_feasible_count':sum(r['half_repayment_possible_relaxed_menu'] for r in rows),
            'unrestricted_ladder_feasible_count':sum(r['half_repayment_possible_unrestricted_ladder'] for r in rows),
            'zero_lower_envelopes':sum(r['all_forecast_lower_bounds_zero'] for r in rows),
            'mean_forecast_width_utility':mean(r['mean_forecast_width_units']/1000 for r in rows),
            'candidate_minus_maxmin_unpaid':mean(r['candidate_loss']-r['maxmin_loss'] for r in rows)}
    return encode({'posthoc':True,'used_for_tuning':False,'episodes':episodes,'groups':groups,
        'scope':'Bounds condition on the fixed recipient reference, four recovery periods and encoded catalogue. Relaxed bounds are not new controller evaluations.'})


if __name__=='__main__':
    output=ROOT/'causal_compensation/results/development_v1'
    path=output/'posthoc_opportunity_diagnosis.json'
    payload=diagnosis(output)
    if path.exists():
        assert json.loads(path.read_text())==payload
        meta=json.loads((output/'posthoc_metadata.json').read_text())
        assert meta['script_sha256']==sha(ROOT/'causal_compensation/diagnose.py')
        assert meta['result_sha256']==sha(path)
        assert meta['base_result_sha256']==sha(output/'results.json')
    else:
        path.write_text(json.dumps(payload,indent=2)+'\n',encoding='utf-8')
        meta={'posthoc':True,'used_for_tuning':False,'script_sha256':sha(ROOT/'causal_compensation/diagnose.py'),
              'base_result_sha256':sha(output/'results.json'),'result_sha256':sha(path),
              'input_sha256':json.loads((output/'metadata.json').read_text())['input_sha256']}
        (output/'posthoc_metadata.json').write_text(json.dumps(meta,indent=2)+'\n',encoding='utf-8')
    for name,digest in meta['input_sha256'].items(): assert sha(ROOT/name)==digest
    print(json.dumps(payload['groups'],indent=2))
