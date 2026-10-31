"""Source-bound LaTeX rows and numbers for unchanged audited evidence.

No statistical inference or measurement is performed. All registered rows,
invalid denominators and undefined rates remain represented. Decimal rounding
is presentation only; the exact rational source is identified in every file.
"""
import argparse
from decimal import Decimal, localcontext, ROUND_HALF_EVEN
from fractions import Fraction
import hashlib
import json
from pathlib import Path

from .assemble import CONDITIONS, POLICIES, canonical, digest, text_hash


def decimal(value, places=4, scale=1, signed=False):
    if value is None:
        return '--'
    q = Fraction(value) * scale
    with localcontext() as context:
        context.prec = max(60, len(str(abs(q.numerator))) + len(str(q.denominator)) + places + 8)
        d = Decimal(q.numerator) / Decimal(q.denominator)
        d = d.quantize(Decimal(1).scaleb(-places), rounding=ROUND_HALF_EVEN)
    value = format(d, f'.{places}f')
    return ('+' if signed and q > 0 else '') + value


def escape(value):
    replacements = {'\\':r'\textbackslash{}', '&':r'\&', '%':r'\%', '$':r'\$',
                    '#':r'\#', '_':r'\_', '{':r'\{', '}':r'\}',
                    '~':r'\textasciitilde{}', '^':r'\textasciicircum{}'}
    return ''.join(replacements.get(c, c) for c in str(value))


def row(values):
    return ' & '.join(str(v) for v in values) + r' \\'


def tables(evidence):
    if evidence['schema'] != 'recovery-contract-evidence-v1':
        raise ValueError('Unexpected evidence schema')
    f, t = evidence['feasibility'], evidence['timing']
    if len(f['clips']) != 16 or len({r['clip'] for r in f['clips']}) != 16:
        raise ValueError('Every registered clip must remain represented')
    if len(t['session_comparisons']) != 366 or t['all_scheduled']['scheduled'] != 366:
        raise ValueError('Complete playback census required')
    if [r['index'] for r in t['session_comparisons']] != list(range(366)):
        raise ValueError('Playback census/order changed')
    condition = {r['condition']:r for r in f['conditions']}
    if set(condition) != set(CONDITIONS):
        raise ValueError('Both viewing conditions required')
    names = dict(zip(CONDITIONS, ('Free', 'Focused')))
    label = {'cost_greedy':'Greedy', 'rolling_nash':'Rolling Nash', 'maxmin':'Max-min'}
    output = {}
    output['feasibility_condition_rows.tex'] = [row([
        names[c], condition[c]['eligible_clips'],
        *[condition[c]['pooled_episode_counts'][k] for k in
          ('denominator','admit','impossible','abstain','additional_rejections','opportunity_promise_gaps')],
        decimal(condition[c]['equal_clip_macro']['additional_rejections'],2,100),
        decimal(condition[c]['equal_clip_macro']['opportunity_promise_gaps'],2,100)]) for c in CONDITIONS]
    output['feasibility_clip_rows.tex'] = []
    for r in f['clips']:
        values = [escape(r['clip']), names[r['condition']]]
        values += ([r[k] for k in ('denominator','admit','impossible','abstain',
                    'additional_rejections','opportunity_promise_gaps')]
                   if r['disposition']=='evaluated' else ['--']*6)
        values += ['Evaluated' if r['disposition']=='evaluated' else 'Metadata exclusion']
        output['feasibility_clip_rows.tex'].append(row(values))
    bounds={r['clip']:r for r in evidence['policy_bounds_by_clip']}
    if len(evidence['policy_bounds_by_clip'])!=16 or set(bounds)!={r['clip'] for r in f['clips']}:
        raise ValueError('Every registered clip requires a bound disposition')
    output['policy_bound_rows.tex']=[]
    primary_bounds=[]
    for clip in f['clips']:
        source=bounds[clip['clip']]
        if source['eligible'] != (clip['disposition']=='evaluated'):
            raise ValueError('Bound eligibility differs from feasibility census')
        if not source['eligible']:
            output['policy_bound_rows.tex'].append(row([escape(clip['clip'])]+['--']*5))
            continue
        modes={r['execution_mode']:r for r in source['modes']}
        primary=modes['conditional_half_second'];ideal=modes['ideal']
        if primary['positive_debt_pairs']!=clip['denominator']:
            raise ValueError('Bound denominator differs')
        primary_bounds.append(primary)
        output['policy_bound_rows.tex'].append(row([escape(clip['clip']),
            primary['positive_debt_pairs'],primary['resource_paths'],
            decimal(primary['maximum_upper_fraction'],4,100),
            decimal(ideal['maximum_upper_fraction'],4,100),
            primary['policy_upper_below_target']]))
    for mode, filename in (('conditional_half_second','control_conditional_rows.tex'),
                           ('ideal','control_ideal_rows.tex')):
        selected = {(r['condition'],r['method']):r for r in f['controls'] if r['mode']==mode}
        methods = sorted({k[1] for k in selected})
        if not methods or any((c,m) not in selected for c in CONDITIONS for m in methods):
            raise ValueError('Control condition census differs')
        output[filename] = []
        for method in methods:
            values = [escape(method)]
            for c in CONDITIONS:
                r = selected[(c,method)]
                values += [r[k] for k in ('denominator','admissions','fulfilled','false_promises')]
                values += [decimal(r['fulfillment_fraction'],3)]
            output[filename].append(row(values))
    key = lambda r:(r['condition'],r['policy'],r['unit_seconds'],r['buffered'])
    macro = {key(r):r for r in t['equal_clip_macro']}
    expected = {(c,p,u,b) for c in CONDITIONS for p in POLICIES for u in (10,2) for b in (False,True)}
    if set(macro) != expected or len(t['equal_clip_macro']) != len(expected):
        raise ValueError('All twenty-four condition-specific macro cells required')
    output['timing_macro_rows.tex'] = []
    for policy in POLICIES:
        for unit in (10,2):
            for buffered in (False,True):
                values = [label[policy],unit,'Buffered' if buffered else 'Cold']
                for c in CONDITIONS:
                    r = macro[(c,policy,unit,buffered)]
                    value = r['equal_clip_delta']
                    if (value is None) != r['incomplete_macro_not_estimated']:
                        raise ValueError('Incomplete macro must remain undefined')
                    values += [f"{r['complete_clips']}/{r['planned_clips']}",
                               decimal(value['mean'] if value else None,4,signed=True)]
                output['timing_macro_rows.tex'].append(row(values))
    output['timing_control_rows.tex'] = []
    for control in ('late_recipient','background'):
        r = t['controls'][control]
        output['timing_control_rows.tex'].append(row([
            escape(control), f"{r['valid']}/{r['scheduled']}",
            decimal(r['parent_fraction_minus_ideal']['mean'],4,signed=True),
            r['observed_resource_protected_half'],r['ideal_resource_protected_half'],
            r['resource_cap_failures'],r['reserve_failures'],
            decimal(r['recipient_finish_seconds']['mean'],3)]))
    numbers = {'PlaybackScheduled':t['all_scheduled']['scheduled'],
        'PlaybackValid':t['all_scheduled']['valid'], 'PlaybackInvalid':t['all_scheduled']['invalid'],
        'MainScheduled':t['main']['scheduled'], 'MainValid':t['main']['valid'],
        'MainInvalid':t['main']['invalid'],
        'MainCapFailuresAmongValid':t['main']['resource_cap_failures'],
        'MainReserveFailuresAmongValid':t['main']['reserve_failures'],
        'MainTargetDiscordancesAmongValid':t['main']['protected_target_discordances'],
        'MainTailMissingAmongValid':t['main']['missing_tail_witnesses'],
        'FeasibilitySoundnessViolations':f['soundness_violations'],
        'PolicyUpperBelowTarget':sum(r['policy_upper_below_target'] for r in primary_bounds)}
    maxima=[Fraction(r['maximum_upper_fraction']) for r in primary_bounds if r['maximum_upper_fraction'] is not None]
    numbers['PolicyUpperMaximumPercent']=decimal(max(maxima) if maxima else None,2,100)
    for c in CONDITIONS:
        r = condition[c]; prefix=names[c]
        for name, field in (('Pairs','denominator'),('Admissions','admit'),('Impossible','impossible'),
                            ('Abstain','abstain'),('ExtraRejections','additional_rejections'),
                            ('KnownFeasible','known_trace_feasible'),('PromiseGaps','opportunity_promise_gaps')):
            numbers[prefix+name] = r['pooled_episode_counts'][field]
        numbers[prefix+'ExtraMacroPercent'] = decimal(r['equal_clip_macro']['additional_rejections'],2,100)
        numbers[prefix+'GapMacroPercent'] = decimal(r['equal_clip_macro']['opportunity_promise_gaps'],2,100)
    output['result_numbers.tex'] = [rf'\newcommand{{\{name}}}{{{value}}}' for name,value in sorted(numbers.items())]
    prefix = '% Evidence SHA-256: '+digest(evidence)+'\n% Decimal display: half-even; exact fractions remain in evidence.json.\n'
    return {name:prefix+'\n'.join(lines)+'\n' for name,lines in output.items()}


def build(evidence_path, output, verify=False):
    evidence = json.loads((evidence_path/'evidence.json').read_text())
    source = json.loads((evidence_path/'metadata.json').read_text())
    if source['evidence_sha256'] != digest(evidence):
        raise ValueError('Evidence binding differs')
    body = tables(evidence)
    meta = {'schema':'recovery-contract-latex-tables-v1', 'evidence_sha256':digest(evidence),
        'source_sha256':text_hash(Path(__file__)),
        'files':{name:hashlib.sha256(value.encode()).hexdigest() for name,value in body.items()},
        'decimal_rounding':'half-even; presentation only', 'measurements_created':False}
    if verify:
        if {p.name for p in output.iterdir()} != set(body)|{'metadata.json'}:
            raise ValueError('Table export census changed')
        if json.loads((output/'metadata.json').read_text()) != meta:
            raise ValueError('Table metadata differs')
        for name,value in body.items():
            if (output/name).read_bytes() != value.encode():
                raise ValueError('Source-bound table differs: '+name)
    else:
        output.mkdir(parents=True,exist_ok=False)
        for name,value in body.items():
            (output/name).write_bytes(value.encode())
        (output/'metadata.json').write_bytes(canonical(meta))
    return meta


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__)
    p.add_argument('--evidence',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--verify',action='store_true')
    a=p.parse_args()
    print(json.dumps(build(a.evidence,a.output,a.verify)))
