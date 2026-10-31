"""Bind first-pair proposed paths and existing parent/child labels, without media."""
import argparse
import copy
import gzip
import json
from pathlib import Path
import numpy as np
from wu_feasibility.spec import ROOT, EXPORT, canonical, digest, verify as verify_feasibility
from wu_pipeline_v2.audit import verify_export, validate_labels
from duration_contract.core import account
from admission_contract.core import clocks
from .core import POLICIES, TICKS, ideal, resource, scores, scalar_scores, schedule, player_entry

PACKAGE = Path(__file__).resolve().parent
OUT = PACKAGE/'results/plan_v1'


def clip_cases(clip, feasibility, label_data):
    if not clip['eligible']:
        return []
    validate_labels(label_data, clip['source_ids'])
    first = clip['pairs'][0]
    if not first['usable'] or first['failed_source_ids']:
        raise ValueError('Fixed first pair unusable; no replacement allowed')
    saved = next(r for r in feasibility['pairs'] if r['recipient'] == first['recipient'] and r['donor'] == first['donor'])
    if saved['disposition'] != 'evaluated':
        raise ValueError('First pair has no positive feasible reference contract; retain, do not substitute')
    mode = next(m for m in saved['modes'] if m['execution_mode'] == 'ideal')
    label = {r['source_id']: r for r in label_data['rows']}
    pair_labels = [label[first[u]] for u in ('recipient', 'donor')]
    qp = np.stack([np.array(r['parent']['negative_micro_mse'], dtype=np.int64).T for r in pair_labels], axis=1)
    qc = np.stack([np.array(r['child']['negative_micro_mse'], dtype=np.int64).T for r in pair_labels], axis=1)
    ds = pair_labels[0]['parent']['duration_ticks']
    child_ds = pair_labels[0]['child']['duration_ticks']
    costs = np.array([[clip['media'][r]['parents'][t]['bytes'] for r in range(6)] for t in range(6)], dtype=np.int64)
    reserve = int(2*costs[2:, 2].sum())
    loss = sum(max(0, int(qp[t, 0, 2])-int(qp[t, 0, 0]))*ds[t] for t in (0, 1))
    if loss != saved['loss'] or reserve != feasibility['reserve_bytes']:
        raise ValueError('Frozen entry debt/reserve changed')
    cases = []
    for policy in POLICIES:
        control = next(c for c in mode['controls'] if c['method'] == policy)
        path = control['proposed_path']
        if path is None or len(path) != 4:
            raise ValueError('Missing frozen proposed path; no fallback substitution')
        pg = [max(0, int(qp[t, 0, a])-int(qp[t, 0, 2]))*ds[t] for t, (a, b) in zip(range(2, 6), path)]
        pf = [sum(int(qp[t, u, path[t-2][u]] < qp[t, u, 2]) for t in range(2, 6)) for u in (0, 1)]
        for seconds in (10, 2):
            units = []; cg = []; cf = [0, 0]
            for parent, rungs in enumerate(path):
                t = parent+2
                for child in range(1 if seconds == 10 else 5):
                    files = []; bases = []
                    for u, rung in enumerate(rungs):
                        item = clip['media'][rung]['parents'][t]; baseline = clip['media'][2]['parents'][t]
                        if seconds == 2:
                            item = item['children'][child]; baseline = baseline['children'][child]
                        if item['duration_ticks'] != seconds*TICKS or item['frames'] != seconds*30:
                            raise ValueError('Prepared media timing changed')
                        files.append({k: item[k] for k in ('relative_path', 'sha256', 'bytes', 'frames')} |
                                     {'duration': seconds})
                        bases.append(baseline['bytes'])
                    units.append({'parent': parent, 'child': child, 'duration_ticks': seconds*TICKS,
                                  'files': files, 'baseline_bytes': bases})
                    if seconds == 10:
                        cg.append(pg[parent])
                    else:
                        j = t*5+child
                        cg.append(max(0, int(qc[j, 0, rungs[0]])-int(qc[j, 0, 2]))*child_ds[j])
                        for u in (0, 1):
                            cf[u] += int(qc[j, u, rungs[u]] < qc[j, u, 2])
            if seconds == 10:
                cf = pf.copy()
            for buffered in (False, True):
                case = {'case_id': f"{clip['clip']}:{policy}:{seconds}:{int(buffered)}",
                    'key': f"{clip['clip']}:{first['recipient']}:{first['donor']}",
                    'clip': clip['clip'], 'condition': clip['condition'],
                    'recipient': first['recipient'], 'donor': first['donor'], 'policy': policy,
                    'path': copy.deepcopy(path), 'selection': 'frozen_ideal_ungated_proposed_path',
                    'original_gate_status': control['status'], 'unit_seconds': seconds, 'buffered': buffered,
                    'units': units, 'loss': loss, 'parent_gains': pg, 'parent_floor_violations': pf,
                    'chunk_gains': cg, 'chunk_floor_violations': cf,
                    'resource': resource(units, reserve)}
                timing = ideal(units, buffered); value = scores(case, timing['end_ticks'])
                independent = scalar_scores(case, timing['end_ticks'])
                if any(independent[k][field] != value[k][field] for k in independent for field in independent[k]):
                    raise ValueError('Independent parent/chunk account mismatch')
                if seconds == 10 and not buffered:
                    previous_ends = clocks(costs, np.array([path]), ds, 0)[0]
                    if previous_ends.tolist() != timing['end_ticks']:
                        raise ValueError('Original integer completion clock changed')
                    previous = account(qp, ds, path, previous_ends)
                    if previous['deadline_credit'] != value['original_parent_account']['capped_credit'] or previous['protected_half_by_deadline'] != value['original_parent_account']['protected_half']:
                        raise ValueError('Original parent account changed')
                case['ideal'] = {**timing, **value}; cases.append(case)
    return cases


def build():
    verify_feasibility(); verify_export(EXPORT)
    manifest = json.loads((EXPORT/'manifest.json').read_text())
    meta = json.loads((ROOT/'wu_feasibility/results/attempt_01/metadata.json').read_text())
    cases = []; roster = []
    for clip in manifest['clips']:
        roster.append({'clip': clip['clip'], 'condition': clip['condition'], 'eligible': clip['eligible'],
                       'exclusion_reasons': clip['parent_exclusion_reasons'],
                       'first_pair': clip['pairs'][0] if clip['eligible'] else None})
        if not clip['eligible']:
            continue
        result = json.loads(gzip.decompress((ROOT/'wu_feasibility/results/attempt_01'/(clip['clip']+'.json.gz')).read_bytes()))
        if digest(result) != meta['clip_sha256'][clip['clip']]:
            raise ValueError('Published feasibility artifact changed')
        labels = json.loads((EXPORT/clip['clip']/'offline_evaluation_labels.json').read_text())
        cases += clip_cases(clip, result, labels)
    sessions = schedule(cases); lookup = {c['case_id']: c for c in cases}
    delivery = [player_entry(lookup[s['case_id']], s) for s in sessions]
    return {'roster': roster, 'cases': cases, 'sessions': sessions}, delivery


def main():
    from .spec import verify
    p = argparse.ArgumentParser(__doc__); p.add_argument('--verify', action='store_true'); args = p.parse_args()
    frozen = verify(); result, delivery = build()
    meta = {'registration_sha256': digest(frozen), 'cases_sha256': digest(result),
            'delivery_sha256': digest(delivery), 'sessions': 366, 'real_playback_performed': False}
    if not args.verify:
        OUT.mkdir(parents=True, exist_ok=False)
    for name, value in (('cases.json.gz', result), ('delivery.json', delivery), ('metadata.json', meta)):
        path = OUT/name; raw = canonical(value)
        if args.verify:
            saved = gzip.decompress(path.read_bytes()) if name.endswith('.gz') else path.read_bytes()
            if saved != raw: raise ValueError('Frozen plan replay differs')
        else:
            with path.open('xb') as stream:
                stream.write(gzip.compress(raw, mtime=0) if name.endswith('.gz') else raw)
    print(json.dumps(meta))


if __name__ == '__main__':
    main()
