"""Raw-event validation plus exact request-aligned native-quality accounting."""
import argparse
from collections import Counter
from fractions import Fraction
import gzip
import json
from pathlib import Path
from wu_feasibility.spec import canonical, digest, file_hash
from player_timing.audit import audit_session
from player_timing.diagnose import raw_crosschecks
from player_timing.core import tail_witness
from .core import TICKS, scores, scalar_scores
from .build import OUT
from .spec import verify


def seconds_ticks(milliseconds, origin):
    return (Fraction(str(milliseconds))-Fraction(str(origin)))*TICKS/1000


def legacy_case(case, session):
    """Only adapts validation axes; original floating score is not the new result."""
    units = [{**u, 'duration': u['duration_ticks']/TICKS} for u in case['units']]
    return {**case, **session, 'scene': case['clip'], 'units': units}


def audit(raw, case, session):
    base = {**session, 'clip': case['clip'], 'condition': case['condition'], 'policy': case['policy'],
            'unit_seconds': case['unit_seconds'], 'buffered': case['buffered']}
    for k in ('index', 'case_id', 'repetition', 'control'):
        if raw.get(k) != session[k]: raise ValueError('Scheduled measurement identity changed')
    if raw.get('status') != 'completed':
        return {**base, 'valid': False, 'status': raw.get('status', 'missing'), 'error': raw.get('error'), 'scored_as_success': False}
    adapted = legacy_case(case, session)
    old = audit_session(raw, adapted)
    if not old['valid']: raise ValueError('Original event validator rejected session')
    checks = raw_crosschecks(raw, adapted)
    b = raw['browser']; n = len(case['units'])
    requests = [e for e in b['events'] if e['type'] == 'request']
    if len(requests) != 2*n or Counter((e['j'], e['u']) for e in requests) != Counter((j, u) for j in range(n) for u in (0, 1)):
        raise ValueError('Request event census differs')
    lookup = {(e['j'], e['u']): e for e in requests}
    if any(r['request'] != lookup[r['j'], r['u']]['at'] for r in b['receipts']):
        raise ValueError('Request/receipt clock origin mismatch')
    origin = min(e['at'] for e in requests)
    ended = [[None, None] for _ in range(n)]; reported = [[None, None] for _ in range(n)]; tail = [[None, None] for _ in range(n)]
    for u in (0, 1):
        for j, segment in enumerate(b['segments'][u]):
            ended[j][u] = seconds_ticks(segment['ended'], origin)
            reported[j][u] = seconds_ticks(segment['reportReady'], origin)
            frames = [f for f in b['frames'][u] if f['j'] == j]
            if tail_witness(frames, case['units'][j]['files'][u]['frames']):
                tail[j][u] = ended[j][u]
    accounts = {}
    for label, ends in (('ended', ended), ('report_ready', reported), ('callback_tail', tail)):
        result = scores(case, ends); independent = scalar_scores(case, ends)
        if any(result[k][f] != independent[k][f] for k in independent for f in independent[k]):
            raise ValueError('Independent exact measured credit mismatch')
        accounts[label] = result
    epoch = [[seconds_ticks(s['ended'], 0) for s in pair] for pair in zip(*b['segments'])]
    epoch_score = scores(case, epoch)
    actual = accounts['ended']['original_parent_account']; reference = case['ideal']['original_parent_account']
    if session['control'] == 'late_recipient' and actual['credit'] != 0:
        raise ValueError('Late-recipient control falsely credited')
    return {**base, 'valid': True, 'status': 'completed', 'first_request_offset_ms': origin,
        'request_aligned_accounts': accounts, 'epoch_sensitivity': epoch_score,
        'ended_ticks': [[str(t) for t in pair] for pair in ended],
        'finish_seconds': [float(t/TICKS) for t in ended[-1]],
        'unperturbed_ideal': case['ideal'], 'resource': case['resource'],
        'parent_credit_minus_ideal': actual['credit']-reference['credit'],
        'parent_fraction_minus_ideal': str(Fraction(actual['fraction_repaid'])-Fraction(reference['fraction_repaid'])) if actual['fraction_repaid'] is not None else None,
        'protected_target_discordance': actual['resource_protected_half'] != reference['resource_protected_half'],
        'missing_tail_witnesses': old['missing_tail_witnesses'], 'callback_count': old['callback_count'],
        'callback_gaps': old['callback_gaps'], 'reported_dropped_frames': old['reported_dropped_frames'],
        'checks': checks, 'physical_display_validated': False}


def analyze(rawdir):
    frozen = verify(); meta = json.loads((rawdir/'metadata.json').read_text())
    planmeta = json.loads((OUT/'metadata.json').read_text())
    if meta['registration_sha256'] != digest(frozen) or meta['delivery_sha256'] != planmeta['delivery_sha256'] or meta['runtime'] != frozen['runtime']:
        raise ValueError('Raw method/schedule/runtime identity changed')
    plan = json.loads(gzip.decompress((OUT/'cases.json.gz').read_bytes())); cases = {c['case_id']: c for c in plan['cases']}
    if digest(plan) != planmeta['cases_sha256']: raise ValueError('Plan binding differs')
    completion = json.loads((rawdir/'completion.json').read_text())
    if [r['index'] for r in completion] != list(range(366)):
        raise ValueError('Incomplete fixed batch; do not summarize selected successes')
    rows = []; hashes = {}
    for session in plan['sessions']:
        path = rawdir/f"session_{session['index']:03}.json.gz"
        raw = json.loads(gzip.decompress(path.read_bytes())); hashes[path.name] = file_hash(path)
        if completion[session['index']]['status'] != raw['status']:
            raise ValueError('Completion ledger status differs')
        try:
            result = audit(raw, cases[session['case_id']], session)
        except (ValueError, KeyError, TypeError) as error:
            result = {**session, 'valid': False, 'status': 'audit_failed', 'error': str(error), 'scored_as_success': False}
        rows.append(result)
    return {'sessions': 366, 'rows': rows, 'valid': sum(r['valid'] for r in rows),
            'independent_people': False, 'raw_bindings': hashes, 'registration_sha256': digest(frozen)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(__doc__); p.add_argument('--raw', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True); p.add_argument('--verify', action='store_true'); a = p.parse_args()
    result = analyze(a.raw)
    if a.verify:
        if json.loads(gzip.decompress(a.output.read_bytes())) != result: raise ValueError('Audit changed')
    else:
        with a.output.open('xb') as stream: stream.write(gzip.compress(canonical(result), mtime=0))
    print(json.dumps({'scientific_sha256': digest(result), 'valid': result['valid'], 'sessions': result['sessions']}))
