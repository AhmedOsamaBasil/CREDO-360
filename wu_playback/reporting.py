"""Descriptive, complete-census reporting; no experimental selection or fitting.

Post-freeze reporting addition. The registered runner and event audit are reused
unchanged. Complete-case summaries expose their missing denominator, and macro
summaries require all three repetitions of every planned cell.
"""
import argparse
from collections import Counter, defaultdict
from fractions import Fraction
import gzip
import json
from pathlib import Path
import re
import shutil

from wu_feasibility.spec import canonical, digest, file_hash, text_hash
from .audit import analyze
from .build import OUT
from .spec import verify


def fraction_stats(values):
    values = [Fraction(v) for v in values]
    return {'n': len(values), 'mean': str(sum(values, Fraction())/len(values)) if values else None,
            'min': str(min(values)) if values else None, 'max': str(max(values)) if values else None,
            'negative': sum(v < 0 for v in values), 'zero': sum(v == 0 for v in values),
            'positive': sum(v > 0 for v in values)}


def group_summary(rows):
    valid = [r for r in rows if r['valid']]
    def account(r, kind='ended', granularity='original_parent_account'):
        return r['request_aligned_accounts'][kind][granularity]
    deltas = [r['parent_fraction_minus_ideal'] for r in valid if r['parent_fraction_minus_ideal'] is not None]
    return {'scheduled': len(rows), 'valid': len(valid), 'invalid': len(rows)-len(valid),
        'invalid_indices': [r['index'] for r in rows if not r['valid']],
        'parent_fraction_minus_ideal': fraction_stats(deltas),
        'parent_credit_minus_ideal': fraction_stats([r['parent_credit_minus_ideal'] for r in valid]),
        'recipient_finish_seconds': fraction_stats([Fraction(r['ended_ticks'][-1][0])/150000 for r in valid]),
        'donor_finish_seconds': fraction_stats([Fraction(r['ended_ticks'][-1][1])/150000 for r in valid]),
        'protected_target_discordances': sum(r['protected_target_discordance'] for r in valid),
        'observed_resource_protected_half': sum(account(r)['resource_protected_half'] is True for r in valid),
        'ideal_resource_protected_half': sum(r['unperturbed_ideal']['original_parent_account']['resource_protected_half'] is True for r in valid),
        'secondary_chunk_resource_protected_half': sum(account(r, granularity='secondary_chunk_account')['resource_protected_half'] is True for r in valid),
        'resource_cap_failures': sum(not r['resource']['cap_ok'] for r in valid),
        'reserve_failures': sum(not r['resource']['reserve_ok'] for r in valid),
        'missing_tail_witnesses': sum(r['missing_tail_witnesses'] for r in valid),
        'callback_count': sum(r['callback_count'] for r in valid),
        'ended_vs_report_credit_discordance': sum(account(r)['credit'] != account(r, 'report_ready')['credit'] for r in valid),
        'ended_vs_tail_credit_discordance': sum(account(r)['credit'] != account(r, 'callback_tail')['credit'] for r in valid),
        'ended_vs_epoch_credit_discordance': sum(account(r)['credit'] != r['epoch_sensitivity']['original_parent_account']['credit'] for r in valid),
        'all_counts_descriptive': True, 'independent_people': False}


def summarize(audit, plan):
    expected = plan['sessions']; rows = audit['rows']
    if len(expected) != 366 or len(rows) != 366:
        raise ValueError('All 366 scheduled rows required, including failures')
    cases = {c['case_id']: c for c in plan['cases']}
    prepared = []
    for row, session in zip(rows, expected):
        if any(row.get(k) != session[k] for k in ('index', 'case_id', 'repetition', 'control')):
            raise ValueError('Schedule changed or rows reordered')
        c = cases[session['case_id']]
        prepared.append({**row, **{k:c[k] for k in ('clip','condition','policy','unit_seconds','buffered')}})
    groups = defaultdict(list)
    for row in prepared:
        groups[(row['case_id'], row['control'])].append(row)
    cells = []
    for (case_id, control), items in sorted(groups.items()):
        if sorted(r['repetition'] for r in items) != [0,1,2]:
            raise ValueError('Every scheduled cell must retain all three repetitions')
        c = cases[case_id]
        cells.append({'case_id':case_id, 'control':control,
                      **{k:c[k] for k in ('clip','condition','policy','unit_seconds','buffered')},
                      **group_summary(items)})
    macro = []
    for condition in sorted({c['condition'] for c in plan['cases']}):
        for policy in ('cost_greedy','rolling_nash','maxmin'):
            for unit in (10,2):
                for buffered in (False,True):
                    selected = [c for c in cells if c['condition']==condition and c['policy']==policy and
                                c['unit_seconds']==unit and c['buffered']==buffered and c['control']=='none']
                    if len(selected)!=5: raise ValueError('Exactly five clips per condition required')
                    complete = all(c['valid']==3 and c['parent_fraction_minus_ideal']['n']==3 for c in selected)
                    means = [c['parent_fraction_minus_ideal']['mean'] for c in selected] if complete else []
                    macro.append({'condition':condition,'policy':policy,'unit_seconds':unit,'buffered':buffered,
                        'planned_clips':5,'complete_clips':sum(c['valid']==3 for c in selected),
                        'equal_clip_delta':fraction_stats(means) if complete else None,
                        'incomplete_macro_not_estimated':not complete})
    return {'schema':'wu-playback-report-v1','audit_sha256':digest(audit),'plan_sha256':digest(plan),
        'all_scheduled':group_summary(prepared),'main':group_summary([r for r in prepared if r['control']=='none']),
        'controls':{name:group_summary([r for r in prepared if r['control']==name]) for name in ('late_recipient','background')},
        'status_counts':dict(sorted(Counter(r['status'] for r in prepared).items())),
        'by_cell':cells,'equal_clip_macro':macro,'statistical_inference_performed':False,
        'scope':'fixed-source software playback; not human QoE, physical-network or positive certified-admission validation'}


def export(raw, output):
    if output.exists(): raise ValueError('New output only; no overwrite or retry')
    frozen = verify()
    audit = analyze(raw)
    plan = json.loads(gzip.decompress((OUT/'cases.json.gz').read_bytes()))
    report = summarize(audit, plan)
    names = ['metadata.json','completion.json']+[f'session_{i:03}.json.gz' for i in range(366)]
    for name in names:
        content = (raw/name).read_bytes()
        if name.endswith('.gz'): content = gzip.decompress(content)
        # Only technical logs may be exported. Any unexpected sensitive-looking
        # material stops export for review; it is never silently scrubbed.
        if re.search(rb'(?i)(github_pat_|ghp_[A-Za-z0-9]|C:[/\\]+Users[/\\]|/home/|password\s*[:=])',content):
            raise ValueError('Unexpected private material requires review before export')
    output.mkdir(parents=True)
    rawout=output/'raw';rawout.mkdir()
    for name in names: shutil.copyfile(raw/name, rawout/name)
    for name,value in (('audit.json.gz',audit),('report.json',report)):
        body=canonical(value)
        (output/name).write_bytes(gzip.compress(body,mtime=0) if name.endswith('.gz') else body)
    meta={'registration_sha256':digest(frozen),'reporting_source_sha256':text_hash(Path(__file__)),
        'plan_sha256':digest(plan),'audit_sha256':digest(audit),'report_sha256':digest(report),
        'files':{str(p.relative_to(output).as_posix()):file_hash(p) for p in sorted(output.rglob('*')) if p.is_file()},
        'raw_media_included':False,'raw_poses_included':False,'automatic_retries':0}
    (output/'export_metadata.json').write_bytes(canonical(meta))
    return meta,report


def verify_export(output):
    meta=json.loads((output/'export_metadata.json').read_text())
    if meta['registration_sha256'] != digest(verify()) or meta['reporting_source_sha256'] != text_hash(Path(__file__)):
        raise ValueError('Method/reporting identity changed')
    files={str(p.relative_to(output).as_posix()) for p in output.rglob('*') if p.is_file()}
    if files != set(meta['files'])|{'export_metadata.json'}: raise ValueError('Export census changed')
    for name,sha in meta['files'].items():
        if file_hash(output/name)!=sha: raise ValueError('Export bytes changed')
    audit=analyze(output/'raw');plan=json.loads(gzip.decompress((OUT/'cases.json.gz').read_bytes()))
    report=summarize(audit,plan)
    if audit!=json.loads(gzip.decompress((output/'audit.json.gz').read_bytes())) or report!=json.loads((output/'report.json').read_text()):
        raise ValueError('Complete audit/report replay differs')
    if digest(audit)!=meta['audit_sha256'] or digest(report)!=meta['report_sha256'] or digest(plan)!=meta['plan_sha256']:
        raise ValueError('Semantic digest differs')
    return meta,report


if __name__=='__main__':
    p=argparse.ArgumentParser(__doc__);p.add_argument('--raw',type=Path);p.add_argument('--output',type=Path,required=True)
    p.add_argument('--verify',action='store_true');a=p.parse_args()
    if not a.verify and a.raw is None:p.error('--raw required for export')
    meta,report=verify_export(a.output) if a.verify else export(a.raw,a.output)
    print(json.dumps({'report_sha256':meta['report_sha256'],'valid':report['all_scheduled']['valid'],
                      'scheduled':report['all_scheduled']['scheduled'],'invalid':report['all_scheduled']['invalid']}))
