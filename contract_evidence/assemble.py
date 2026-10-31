"""Assemble complete, descriptive evidence without changing any evaluation.

This post-freeze presentation layer reads saved scientific summaries. It does
not fit a model, select clips, rerun a measurement or redefine an endpoint.
Exact ratios are retained in JSON; floats are used only by the plotting layer.
"""
import argparse
from collections import defaultdict
from fractions import Fraction
import json
from pathlib import Path

from wu_feasibility.spec import canonical, digest, file_hash, text_hash

ROOT = Path(__file__).resolve().parents[1]
FEASIBILITY = ROOT / 'wu_feasibility/results/attempt_01/summary.json'
PLAYBACK = ROOT / 'wu_playback/results/measured_v1'
CONDITIONS = ('free_exploration', 'content_focused_memory_test')
POLICIES = ('cost_greedy', 'rolling_nash', 'maxmin')


def mean_ratio(rows, numerator, denominator):
    """Equal-clip mean; undefined observations are not silently dropped."""
    if not rows or any(r[denominator] <= 0 for r in rows):
        return None
    return str(sum((Fraction(r[numerator], r[denominator]) for r in rows), Fraction()) / len(rows))


def feasibility_tables(summary):
    if summary['schema'] != 'wu-fixed-contract-feasibility-results-v1':
        raise ValueError('Unexpected feasibility schema')
    original = summary['clips']
    if len(original) != 16 or len({r['clip'] for r in original}) != 16:
        raise ValueError('All sixteen original registrations are required')
    rows = []
    for r in original:
        admitted = r['decisions'].get('admit', 0)
        impossible = r['decisions'].get('impossible', 0)
        abstain = r['decisions'].get('abstain', 0)
        n = r['primary_denominator']
        if admitted + impossible + abstain != n:
            raise ValueError('Decision census differs from the declared denominator')
        if not 0 <= r['additional_rejections'] <= impossible:
            raise ValueError('Geometric rejection increment is not nested')
        if not 0 <= r['opportunity_promise_gaps'] <= r['known_trace_feasible'] <= n:
            raise ValueError('Opportunity/promise census is inconsistent')
        rows.append({k: r[k] for k in ('clip', 'condition', 'disposition', 'pairs',
            'no_event', 'reference_infeasible', 'known_trace_feasible',
            'opportunity_promise_gaps', 'additional_rejections')} | {
            'denominator': n, 'admit': admitted, 'impossible': impossible,
            'abstain': abstain, 'convex_impossible': impossible-r['additional_rejections']})
    if sum(r['pairs'] for r in rows) != 452:
        raise ValueError('Original directed-pair census changed')
    conditions = []
    for condition in CONDITIONS:
        all_rows = [r for r in rows if r['condition'] == condition]
        eligible = [r for r in all_rows if r['disposition'] == 'evaluated']
        if len(all_rows) != 8 or len(eligible) != 5:
            raise ValueError('Condition-specific registration/eligibility changed')
        fields = ('pairs', 'denominator', 'no_event', 'reference_infeasible',
                  'admit', 'impossible', 'abstain', 'convex_impossible',
                  'additional_rejections', 'known_trace_feasible', 'opportunity_promise_gaps')
        counts = {k: sum(r[k] for r in eligible) for k in fields}
        macro = {k: mean_ratio(eligible, k, 'denominator') for k in
                 ('admit', 'impossible', 'abstain', 'additional_rejections',
                  'known_trace_feasible', 'opportunity_promise_gaps')}
        # Independent assembly must match the saved evaluator's primary macros.
        old = next(r for r in summary['conditions'] if r['condition'] == condition)
        names = {'admit':'admission_fraction', 'impossible':'impossible_fraction',
            'abstain':'abstain_fraction', 'additional_rejections':'additional_fraction',
            'known_trace_feasible':'known_feasible_fraction', 'opportunity_promise_gaps':'gap_fraction'}
        for field, saved in names.items():
            if macro[field] != old['equal_clip_macro'][saved]['value']:
                raise ValueError('Independent equal-clip summary differs')
        conditions.append({'condition': condition, 'registered_clips': 8, 'eligible_clips': 5,
            'pooled_episode_counts': counts, 'equal_clip_macro': macro})
    controls = []
    for condition in CONDITIONS:
        for mode in ('conditional_half_second', 'ideal'):
            selected = [r for r in summary['policy_counts'] if r['condition'] == condition
                        and r['execution_mode'] == mode]
            by_method = defaultdict(list)
            for row in selected:
                by_method[row['method']].append(row)
            for method, items in sorted(by_method.items()):
                if len(items) != 8 or len({r['clip'] for r in items}) != 8:
                    raise ValueError('Control registration census changed')
                counts = {k: sum(r[k] for r in items) for k in
                          ('denominator', 'admissions', 'fulfilled', 'false_promises')}
                if counts['admissions'] != counts['fulfilled'] + counts['false_promises']:
                    raise ValueError('Fulfilled/false promises do not partition admissions')
                controls.append({'condition': condition, 'mode': mode, 'method': method,
                    **counts, 'fulfillment_fraction': str(Fraction(counts['fulfilled'], counts['admissions']))
                    if counts['admissions'] else None})
    return {'clips': rows, 'conditions': conditions, 'controls': controls,
            'soundness_violations': summary['soundness_violations'], 'checks': summary['checks'],
            'control_equivalence': summary['control_equivalence'],
            'quality_labels_previously_exposed': summary['quality_labels_previously_exposed'],
            'independent_population_inference': False}


def timing_tables(report, audit):
    """Preserve all main cells and separate deliberately perturbed controls."""
    if report['schema'] != 'wu-playback-report-v1' or report['audit_sha256'] != digest(audit):
        raise ValueError('Playback report/audit binding differs')
    if len(audit['rows']) != 366 or report['all_scheduled']['scheduled'] != 366:
        raise ValueError('Complete playback census required')
    if [r['index'] for r in audit['rows']] != list(range(366)):
        raise ValueError('Playback order/census differs')
    cells = [r for r in report['by_cell'] if r['control'] == 'none']
    if len(cells) != 120 or len({r['case_id'] for r in cells}) != 120:
        raise ValueError('All 120 main cells required')
    if any(r['scheduled'] != 3 for r in cells):
        raise ValueError('Three retained repetitions required')
    comparisons = []
    for r in audit['rows']:
        base = {k:r[k] for k in ('index', 'case_id', 'repetition', 'control', 'valid', 'status')}
        if not r['valid']:
            comparisons.append(base | {'result': None})
            continue
        observed = r['request_aligned_accounts']['ended']['original_parent_account']
        ideal = r['unperturbed_ideal']['original_parent_account']
        secondary = r['request_aligned_accounts']['ended']['secondary_chunk_account']
        comparisons.append(base | {'result': {
            'observed_parent_fraction': observed['fraction_repaid'],
            'ideal_parent_fraction': ideal['fraction_repaid'],
            'difference': r['parent_fraction_minus_ideal'],
            'observed_protected_target': observed['resource_protected_half'],
            'ideal_protected_target': ideal['resource_protected_half'],
            'secondary_chunk_protected_target': secondary['resource_protected_half'],
            'recipient_finish_seconds': str(Fraction(r['ended_ticks'][-1][0])/150000),
            'donor_finish_seconds': str(Fraction(r['ended_ticks'][-1][1])/150000),
            'cap_ok': r['resource']['cap_ok'], 'reserve_ok': r['resource']['reserve_ok']}})
    return {'main': report['main'], 'controls': report['controls'],
        'cells': report['by_cell'], 'equal_clip_macro': report['equal_clip_macro'],
        'all_scheduled': report['all_scheduled'], 'status_counts': report['status_counts'],
        'session_comparisons': comparisons, 'inference': 'descriptive; no iid participant inference',
        'primary_account': 'original-parent, request-aligned ended-event completion',
        'secondary_account': 'actual chunk quality; distinct contract, not a parent-policy theorem test'}


def assemble(playback=PLAYBACK):
    """Require a fully audited public playback export, never private partial logs."""
    from wu_playback.reporting import verify_export
    import gzip
    meta, report = verify_export(playback)
    audit = json.loads(gzip.decompress((playback/'audit.json.gz').read_bytes()))
    summary = json.loads(FEASIBILITY.read_text())
    return {'schema':'recovery-contract-evidence-v1',
        'sources': {'feasibility_summary_sha256': file_hash(FEASIBILITY),
            'playback_export_sha256': file_hash(playback/'export_metadata.json'),
            'playback_report_sha256': meta['report_sha256'],
            'playback_audit_sha256': meta['audit_sha256']},
        'feasibility':feasibility_tables(summary), 'timing':timing_tables(report,audit),
        'fresh_quality_holdout':False, 'new_measurements_created':False,
        'subjective_qoe_validated':False, 'positive_certified_service_established':False}


def main():
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--playback',type=Path,default=PLAYBACK)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--verify',action='store_true')
    a=p.parse_args();result=assemble(a.playback)
    meta={'evidence_sha256':digest(result),'source_sha256':text_hash(Path(__file__)),
          'scope':'descriptive presentation of unchanged registered results'}
    if a.verify:
        if json.loads((a.output/'evidence.json').read_text()) != result or json.loads((a.output/'metadata.json').read_text()) != meta:
            raise ValueError('Evidence assembly differs')
    else:
        a.output.mkdir(parents=True,exist_ok=False)
        (a.output/'evidence.json').write_bytes(canonical(result))
        (a.output/'metadata.json').write_bytes(canonical(meta))
    print(json.dumps(meta))


if __name__=='__main__': main()
