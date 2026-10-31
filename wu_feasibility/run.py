"""Guarded, checkpointed evaluation; no media, network or controller fitting."""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import json
from pathlib import Path
import numpy as np

from metric_contract.core import path_arrays, CAP, TICKS
from duration_contract.core import account
from admission_contract.core import spatial_bounds, clocks, path_stats, certificate, independent, ETA
from geometric_admission.geometry import family, validate_family, bounds, check_extrema
from adaptive_audit.core import solve, score_path
from confirmation_protocol.protocol import endpoint, summarize_endpoints, validate_design
from wu_pipeline_v2.audit import verify_export, validate_labels
from .spec import ROOT, PACKAGE, EXPORT, canonical, digest, file_hash, verify
from .core import entry, plan, scalar_paths, scalar_maximum, scalar_account, response

MODES = (('conditional_half_second', ETA), ('ideal', 0))


def unpack(clip):
    with np.load(EXPORT / clip['clip'] / 'sender_maps.npz', allow_pickle=False) as data:
        maps = data['mse']
    if maps.shape != (6, 60, 6, 12) or maps.dtype != np.dtype('<f4') or not np.isfinite(maps).all() or np.any(maps < 0) or np.any(maps > 65025):
        raise ValueError('Invalid sender map')
    labels = json.loads((EXPORT / clip['clip'] / 'offline_evaluation_labels.json').read_text())
    validate_labels(labels, clip['source_ids'])
    if [m['rung'] for m in clip['media']] != list(range(6)):
        raise ValueError('Rung census changed')
    costs = np.zeros((6, 6), dtype=np.int64)
    for m in clip['media']:
        if [p['index'] for p in m['parents']] != list(range(6)):
            raise ValueError('Parent census changed')
        for p in m['parents']:
            if p['duration_ticks'] != 10*TICKS or p['frames'] != 300 or not 0 < p['bytes'] <= 100000000:
                raise ValueError('Invalid parent size/timing')
            costs[p['index'], m['rung']] = p['bytes']
    lookup = {r['source_id']: np.array(r['parent']['negative_micro_mse'], dtype=np.int64).T for r in labels['rows']}
    if len(clip['pairs']) != len(lookup) or any(not p['usable'] or p['failed_source_ids'] or
        p['recipient'] not in lookup or p['donor'] not in lookup or p['recipient'] == p['donor'] for p in clip['pairs']):
        raise ValueError('Original directed pair census changed')
    return maps.reshape(6, 60, 72).astype(np.float64), costs, [10*TICKS]*6, lookup


def evaluate_clip(clip, masks):
    base = {k: clip[k] for k in ('clip', 'condition', 'experiment', 'eligible', 'parent_exclusion_reasons')}
    if not clip['eligible']:
        return {**base, 'disposition': 'retained_metadata_exclusion', 'pairs': [], 'checks': {}}
    maps, costs, durations, labels = unpack(clip)
    reserve = int(2*costs[2:, 2].sum())
    violations = [t for t in range(2, 6) if 2*costs[t, 2] > CAP]
    pairs = []
    for p in clip['pairs']:
        q = np.stack((labels[p['recipient']], labels[p['donor']]), axis=1)
        pairs.append((p, q, entry(q[:2].copy(), durations[:2])))
    common = {**base, 'phase_diagnostic': clip['phase_diagnostic'], 'costs': costs.tolist(),
              'durations_ticks': durations, 'reserve_bytes': reserve,
              'reference_cap_violation_parents': violations}
    if violations:
        return {**common, 'disposition': 'reference_infeasible', 'checks': {},
                'pairs': [{**p, 'loss': e['loss'], 'no_event': e['loss'] == 0,
                           'disposition': 'reference_infeasible'} for p, _, e in pairs]}
    checks = Counter()
    lower, upper, witness = bounds(maps, masks)
    convex_lower, convex_upper = spatial_bounds(maps)
    check_extrema(maps, masks, lower, upper, witness)
    checks['geometric_extrema_cells'] += 360
    if not ((lower >= convex_lower) & (upper <= convex_upper)).all():
        raise ValueError('Geometric interval does not nest within convex interval')
    reward, responses = response(maps, masks, witness)
    arrays = path_arrays(costs, 4, reserve); paths = arrays['choices']
    index = {tuple(p.flat): i for i, p in enumerate(paths)}; baseline = index[(2, 2)*4]
    contexts = {}; public_contexts = []
    for mode, eta in MODES:
        ends = clocks(costs, paths, durations, eta)
        ledger = scalar_paths(costs, durations, reserve, eta)
        if len(ledger) != len(paths):
            raise ValueError('Scalar path census differs')
        for i, (path, spent, finish) in enumerate(ledger):
            if path != tuple(map(tuple, paths[i])) or spent != int(arrays['cost'][i]) or finish != tuple(map(tuple, ends[i])):
                raise ValueError('Independent resource/clock enumeration mismatch')
        checks['independent_path_clocks'] += len(paths)
        for lo, hi in ((lower, upper), (convex_lower, convex_upper)):
            scalar = independent(lo, hi, costs, durations, reserve, 1, eta)
            cert = certificate(lo, hi, costs, arrays, durations, 1, eta)
            if (cert['lower_max_credit'], cert['upper_credit'], cert['lower_safe_paths'], cert['extra_bytes']) != (
                    scalar['lower_max'], scalar['upper_max'], scalar['safe_paths'], scalar['minimum_cost']):
                raise ValueError('Independent envelope certificate mismatch')
            checks['independent_certificate_envelopes'] += 1
        answer = solve(costs, durations, reserve, reward, eta)
        _, gains = path_stats(reward, paths, ends, durations)
        scored = score_path(answer['path'], costs, durations, reserve, reward, eta)
        if int(gains.max()) != answer['credit_upper'] or scored['credit'] != answer['credit_upper'] or scored['extra_bytes'] != answer['extra_bytes']:
            raise ValueError('Bellman/exhaustive/path response maximum mismatch')
        checks['bellman_exhaustive_queries'] += 1
        lower_safe, lower_gain = path_stats(lower, paths, ends, durations)
        good = np.flatnonzero(lower_safe)
        lower_best = int(good[np.argmax(lower_gain[good])])
        contexts[mode] = (ends, ledger, answer, lower_safe, lower_gain, lower_best)
        public_contexts.append({'execution_mode': mode, 'adaptive_bound': answer,
                                'adaptive_witness_ledger': scored})
    records = []; primary = []
    for p, q, completed in pairs:
        loss = completed['loss']; delta = q-q[:, :, 2:3]
        if not ((delta >= lower[:, None, :]) & (delta <= upper[:, None, :])).all():
            raise ValueError('Offline quality outside geometric envelope')
        checks['contained_integer_differences'] += delta.size
        row = {**p, 'loss': loss, 'no_event': loss == 0,
               'disposition': 'no_event' if loss == 0 else 'evaluated', 'modes': []}
        for mode, eta in MODES:
            ends, ledger, adaptive, lower_safe, lower_gain, lower_best = contexts[mode]
            actual_safe, actual_gain = path_stats(delta, paths, ends, durations)
            known = int(actual_gain[actual_safe].max())
            if known != scalar_maximum(delta, durations, ledger):
                raise ValueError('Independent exact observed-trace oracle mismatch')
            checks['independent_observed_oracles'] += 1
            cert = certificate(lower, upper, costs, arrays, durations, loss, eta)
            convex = certificate(convex_lower, convex_upper, costs, arrays, durations, loss, eta)
            lower_max = cert['lower_max_credit']
            if not (lower_max <= known <= cert['upper_credit'] <= convex['upper_credit'] and
                    lower_max <= adaptive['credit_upper'] <= cert['upper_credit']):
                raise ValueError('Bound soundness or information-order violation')
            def checked_score(i):
                result = account(q, durations, paths[i].tolist(), ends[i].tolist())
                scalar = scalar_account(q, durations, paths[i].tolist(), costs, reserve, eta)
                if result != scalar['score'] or int(arrays['cost'][i]) != scalar['extra_bytes'] or ends[i].tolist() != scalar['ends']:
                    raise ValueError('Independent selected-path ledger mismatch')
                checks['independent_selected_accounts'] += 1
                return scalar
            witness_score = checked_score(lower_best) if cert['status'] == 'admit' else None
            ep = {'clip': clip['clip'], 'recipient': p['recipient'], 'donor': p['donor'],
                'execution_mode': 'conditional_half_second', 'loss': loss, 'known_max': known,
                'geometric_lower': lower_max, 'geometric_upper': cert['upper_credit'],
                'convex_upper': convex['upper_credit'], 'adaptive_upper': adaptive['credit_upper'],
                'witness_credit': witness_score['raw_credit'] if witness_score else None,
                'witness_floors_ok': (not (witness_score['score']['recipient_floor_violations']+
                                          witness_score['score']['donor_floor_violations'])) if witness_score else None}
            # Use the original primary checker only on its registered timing model.
            decision = endpoint(ep) if mode == 'conditional_half_second' else None
            if decision is not None:
                primary.append(ep)
            planner = plan(maps, costs, durations, reserve, completed, arrays, ends, eta)
            controls = []
            def append(name, proposed, status, claim, certified=False):
                executed = proposed if status == 'admit' else baseline
                scored = checked_score(executed)
                if certified and status == 'admit' and not scored['score']['protected_half_by_deadline']:
                    raise ValueError('Certified admission contradicted by observed trace')
                controls.append({'method': name, 'status': status, 'claimed_credit': claim,
                    'proposed_path': paths[proposed].tolist() if proposed is not None else None,
                    'executed_path': paths[executed].tolist(), **scored})
            ci = index[tuple(np.array(cert['path']).flat)] if cert['path'] is not None else None
            append('certified_planner', ci, 'no_event' if loss == 0 else cert['status'], cert['certified_credit'], True)
            for name in ('point_planner', 'cost_greedy', 'rolling_nash', 'maxmin'):
                i = planner['selections'].get(name)
                valid = planner['status'] == 'valid'
                predicted_ok = valid and i is not None and bool(planner['safe'][i]) and 2*int(planner['gain'][i]) >= loss
                status = ('admit' if predicted_ok else 'abstain') if valid else planner['status']
                append(name, i, status, int(planner['gain'][i]) if i is not None else None)
                gated = valid and i is not None and bool(lower_safe[i]) and 2*int(lower_gain[i]) >= loss
                append(name+'_certified', i, ('admit' if gated else 'abstain') if valid else planner['status'],
                       int(lower_gain[i]) if i is not None else None, True)
            append('reject_all', None, 'no_event' if loss == 0 else 'diagnostic_reject', None)
            append('abstain_all', None, 'no_event' if loss == 0 else 'abstain', None)
            row['modes'].append({'execution_mode': mode, 'known_max': known,
                'known_trace_feasible': bool(2*known >= loss) if loss else None,
                'geometric_certificate': cert, 'convex_certificate': convex,
                'adaptive_upper': adaptive['credit_upper'], 'primary_endpoint': decision,
                'lower_max_witness_path': paths[lower_best].tolist() if witness_score else None,
                'lower_max_witness': witness_score, 'controls': controls,
                'forecast_status': planner['status'],
                'absolute_known_minus_lower': known-lower_max,
                'absolute_upper_minus_known': cert['upper_credit']-known,
                'normalized_known_minus_lower': str(Fraction(known-lower_max, loss)) if loss else None,
                'normalized_upper_minus_known': str(Fraction(cert['upper_credit']-known, loss)) if loss else None})
        row['unbounded_certificate'] = certificate(lower, upper, costs, arrays, durations, loss, None)
        records.append(row)
    keys = [(clip['clip'], p['recipient'], p['donor']) for p in clip['pairs']]
    return {**common, 'disposition': 'evaluated', 'resource_paths': len(paths),
        'lower': lower.tolist(), 'upper': upper.tolist(), 'convex_lower': convex_lower.tolist(),
        'convex_upper': convex_upper.tolist(), 'extremal_mask_witnesses': witness,
        'native_adversary_responses': responses, 'contexts': public_contexts,
        'pairs': records, 'primary_endpoint_summary': summarize_endpoints(primary, keys),
        'checks': dict(checks), 'soundness_violations': 0}


def summarize(clips):
    counts = []; conditions = []; policies = []
    for c in clips:
        rs = c['pairs']; positive = [r for r in rs if r['loss'] > 0]
        evaluated = [r for r in positive if r['disposition'] == 'evaluated']
        endpoints = [r['modes'][0]['primary_endpoint'] for r in evaluated]
        decisions = Counter(e['status'] for e in endpoints)
        n = len(endpoints)
        additional = sum(e['additional_rejection'] for e in endpoints)
        gaps = sum(e['opportunity_promise_gap'] for e in endpoints)
        normalized = {}
        for key in ('normalized_known_minus_lower', 'normalized_upper_minus_known'):
            vals = [Fraction(r['modes'][0][key]) for r in evaluated]
            normalized[key] = str(sum(vals, Fraction()) / len(vals)) if vals else None
        counts.append({'clip': c['clip'], 'condition': c['condition'], 'disposition': c['disposition'],
            'pairs': len(rs), 'positive_loss': len(positive), 'no_event': len(rs)-len(positive),
            'reference_infeasible': sum(r['disposition'] == 'reference_infeasible' for r in rs),
            'primary_denominator': n, 'decisions': dict(decisions),
            'known_trace_feasible': sum(e['known_trace_feasible'] for e in endpoints),
            'additional_rejections': additional, 'opportunity_promise_gaps': gaps,
            'additional_fraction': str(Fraction(additional, n)) if n else None,
            'gap_fraction': str(Fraction(gaps, n)) if n else None,
            'admission_fraction': str(Fraction(decisions['admit'], n)) if n else None,
            'impossible_fraction': str(Fraction(decisions['impossible'], n)) if n else None,
            'abstain_fraction': str(Fraction(decisions['abstain'], n)) if n else None,
            'known_feasible_fraction': str(Fraction(sum(e['known_trace_feasible'] for e in endpoints), n)) if n else None,
            'mean_normalized_gaps': normalized,
            'fulfilled_admission_fraction': '1' if decisions['admit'] else None})
        for mode, _ in MODES:
            group = [next(m for m in r['modes'] if m['execution_mode'] == mode) for r in evaluated]
            for method in ('certified_planner', 'point_planner', 'cost_greedy', 'rolling_nash', 'maxmin',
                           'point_planner_certified', 'cost_greedy_certified', 'rolling_nash_certified',
                           'maxmin_certified', 'reject_all', 'abstain_all'):
                selected = [next(p for p in m['controls'] if p['method'] == method) for m in group]
                admissions = [p for p in selected if p['status'] == 'admit']
                fulfilled = sum(bool(p['score']['protected_half_by_deadline']) for p in admissions)
                policies.append({'clip': c['clip'], 'condition': c['condition'], 'execution_mode': mode,
                    'method': method, 'denominator': n, 'counts': dict(Counter(p['status'] for p in selected)),
                    'admissions': len(admissions), 'fulfilled': fulfilled,
                    'false_promises': len(admissions)-fulfilled,
                    'fulfillment_fraction': str(Fraction(fulfilled, len(admissions))) if admissions else None})
    for condition in sorted({c['condition'] for c in clips}):
        group = [c for c in counts if c['condition'] == condition]
        macro = {}
        for field in ('additional_fraction', 'gap_fraction', 'admission_fraction', 'impossible_fraction',
                      'abstain_fraction', 'known_feasible_fraction'):
            values = [Fraction(c[field]) for c in group if c[field] is not None]
            macro[field] = {'value': str(sum(values, Fraction())/len(values)) if values else None,
                            'contributing_clips': len(values)}
        for field in ('normalized_known_minus_lower', 'normalized_upper_minus_known'):
            values = [Fraction(c['mean_normalized_gaps'][field]) for c in group if c['mean_normalized_gaps'][field] is not None]
            macro[field] = {'value': str(sum(values, Fraction())/len(values)) if values else None,
                            'contributing_clips': len(values)}
        conditions.append({'condition': condition, 'registered_clips': len(group),
            'eligible_clips': sum(c['disposition'] != 'retained_metadata_exclusion' for c in group),
            'secondary_pooled_counts': {k: sum(c[k] for c in group) for k in
                ('pairs', 'positive_loss', 'no_event', 'reference_infeasible', 'primary_denominator',
                 'known_trace_feasible', 'additional_rejections', 'opportunity_promise_gaps')},
            'equal_clip_macro': macro})
    equivalence = []
    for c in clips:
        for mode, _ in MODES:
            rs = [next(m for m in r['modes'] if m['execution_mode'] == mode)
                  for r in c['pairs'] if r['disposition'] == 'evaluated']
            for a, b in (('point_planner', 'cost_greedy'), ('cost_greedy', 'rolling_nash'), ('rolling_nash', 'maxmin')):
                same_path = same_decision = 0
                for m in rs:
                    p, q = (next(p for p in m['controls'] if p['method'] == name) for name in (a, b))
                    same_path += p['executed_path'] == q['executed_path']
                    same_decision += p['status'] == q['status']
                equivalence.append({'clip': c['clip'], 'execution_mode': mode, 'methods': [a, b],
                                    'denominator': len(rs), 'same_executed_path': same_path, 'same_decision': same_decision})
    return {'schema': 'wu-fixed-contract-feasibility-results-v1', 'clips': counts, 'conditions': conditions,
            'policy_counts': policies, 'control_equivalence': equivalence,
            'checks': dict(sum((Counter(c['checks']) for c in clips), Counter())),
            'soundness_violations': 0, 'quality_labels_previously_exposed': True,
            'controller_fitted': False, 'new_timing_measurements': False, 'population_inference': False,
            'manuscript_changed': False, 'contract_changed': False}


def execute(output, replay=False):
    frozen = verify()
    validate_design(json.loads((ROOT/'confirmation_protocol/design.json').read_text()))
    verify_export(EXPORT)
    manifest = json.loads((EXPORT/'manifest.json').read_text())
    masks = family(); validate_family(masks)
    if len(masks) != 216 or len(manifest['clips']) != 16 or sum(len(c['pairs']) for c in manifest['clips'] if c['eligible']) != 452:
        raise ValueError('Frozen census differs')
    if not replay:
        output.mkdir(parents=True, exist_ok=False)
    elif {p.name for p in output.iterdir()} != {c['clip']+'.json.gz' for c in manifest['clips']} | {'summary.json', 'metadata.json'}:
        raise ValueError('Saved evaluation file census differs')
    clips = []
    try:
        for c in manifest['clips']:
            value = evaluate_clip(c, masks); raw = canonical(value)
            path = output/(c['clip']+'.json.gz')
            if replay:
                if gzip.decompress(path.read_bytes()) != raw:
                    raise ValueError('Complete clip replay differs: '+c['clip'])
            else:
                with path.open('xb') as stream:
                    stream.write(gzip.compress(raw, mtime=0))
            clips.append(value)
            print(json.dumps({'clip': c['clip'], 'disposition': value['disposition'],
                              'completed_clips': len(clips), 'pairs': len(value['pairs'])}), flush=True)
        result = summarize(clips)
        metadata = {'registration_sha256': digest(frozen), 'summary_sha256': digest(result),
                    'clip_sha256': {c['clip']: digest(c) for c in clips},
                    'complete': True, 'automatic_retries': 0}
        for name, value in (('summary.json', result), ('metadata.json', metadata)):
            path = output/name
            if replay:
                if path.read_bytes() != canonical(value):
                    raise ValueError('Summary replay differs')
            else:
                with path.open('xb') as stream:
                    stream.write(canonical(value))
        print(json.dumps({'verified': replay, 'summary_sha256': digest(result), 'checks': result['checks']}), flush=True)
    except Exception as error:
        if not replay:
            with (output/'failure.json').open('xb') as stream:
                stream.write(canonical({'status': 'failed_incomplete', 'registration_sha256': digest(frozen),
                    'completed_clips': [c['clip'] for c in clips], 'error_type': type(error).__name__,
                    'message': str(error), 'automatic_retry': False}))
        raise


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, default=PACKAGE/'results/attempt_01')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--evaluate', metavar='REGISTRATION_SHA256')
    group.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.evaluate and args.evaluate != digest(verify()):
        parser.error('Explicit exact frozen registration digest required')
    execute(args.output, args.verify)


if __name__ == '__main__':
    main()
