"""Descriptive diagnosis after holdout exposure; never a tuning/selection input."""
import csv
import gzip
import json
from pathlib import Path
import numpy as np
from horizon_recovery.run import ROOT, read_csv, sha256


def main():
    output = ROOT/'horizon_recovery/results/v3'
    with gzip.open(output/'measurements.csv.gz','rt',newline='',encoding='utf-8') as f:
        rows = [r for r in csv.DictReader(f) if r['scenario']=='known_ceiling' and r['policy']=='window_recovery']
    q = np.array([float(r['quality']) for r in rows])
    target = np.array([float(r['target']) for r in rows])
    metrics = [r for r in read_csv(output/'seed_metrics.csv') if r['scenario']=='known_ceiling' and r['policy']=='window_recovery']
    report = {'post_hoc':True,'changes_to_controller':False,'rows':len(rows),
              'mean_target':float(target.mean()),'quality_at_5_fraction':float((q==5).mean()),
              'quality_below_4_fraction':float((q<4).mean()),'positive_residual_fraction':float((target>q).mean()),
              'mean_delivered_surplus':float(np.maximum(q-target,0).mean()),
              'mean_new_deficit':float(np.maximum(target-q,0).mean()),
              'minimum_seed_worst_user_quality':min(float(r['worst_user_quality']) for r in metrics),
              'source_sha256':sha256(Path(__file__)),
              'input_sha256':{n:sha256(output/n) for n in ('measurements.csv.gz','seed_metrics.csv')},
              'interpretation_limit':'Associations diagnose limited activation; no isolated causal attribution to clipping or surplus banking.'}
    with (output/'posthoc_diagnostics.json').open('x',encoding='utf-8') as f:
        json.dump(report,f,indent=2); f.write('\n')
    print(json.dumps(report,indent=2))


if __name__ == '__main__':
    main()
