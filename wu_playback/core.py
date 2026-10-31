"""Exact parent/chunk accounts and transport timing; no policy selection."""
from fractions import Fraction

TICKS = 150000
DEADLINE = 6000000
POLICIES = ('cost_greedy', 'rolling_nash', 'maxmin')


def ideal(units, buffered):
    request = 0; arrivals = []; requests = []
    for unit in units:
        a, b = (f['bytes'] for f in unit['files'])
        if min(a, b) <= 0 or unit['duration_ticks'] <= 0:
            raise ValueError('Positive size and duration required')
        arrival = [request+19500+min(2*a, a+b), request+19500+min(2*b, a+b)]
        requests.append(request); arrivals.append(arrival)
        request = max(request+unit['duration_ticks'], *arrival)
    gate = 0
    if buffered:
        duration = 0; count = 0
        while duration < 4*TICKS:
            if count >= len(units):
                raise ValueError('Insufficient complete media for charged buffer')
            duration += units[count]['duration_ticks']; count += 1
        gate = max(t for a in arrivals[:count] for t in a)
    cursor = [gate, gate]; ends = []
    for arrival, unit in zip(arrivals, units):
        cursor = [max(cursor[u], arrival[u])+unit['duration_ticks'] for u in (0, 1)]
        ends.append(cursor)
    return {'request_ticks': requests, 'arrival_ticks': arrivals, 'buffer_gate_ticks': gate, 'end_ticks': ends}


def resource(units, reserve):
    groups = {i: 0 for i in range(4)}; extra = 0
    for unit in units:
        total = sum(f['bytes'] for f in unit['files'])
        groups[unit['parent']] += total
        extra += max(0, total-sum(unit['baseline_bytes']))
    return {'extra_bytes': extra, 'reserve_bytes': reserve, 'reserve_ok': extra <= reserve,
            'parent_bytes': list(groups.values()), 'cap_ok': all(n <= 1500000 for n in groups.values()),
            'payload_bytes': sum(groups.values())}


def ledger(loss, gains, floors, ends, budget):
    if type(loss) is not int or loss < 0 or len(gains) != len(ends):
        raise ValueError('Integer native ledger required')
    if any(type(g) is not int or g < 0 for g in gains):
        raise ValueError('Nonnegative integer credit required')
    credit = sum(g for g, t in zip(gains, ends) if t is not None and t <= DEADLINE)
    half = 2*credit >= loss if loss else None
    protected = bool(half and not any(floors)) if loss else None
    return {'loss': loss, 'credit': credit, 'capped_credit': min(credit, loss),
            'fraction_repaid': str(Fraction(min(credit, loss), loss)) if loss else None,
            'half': half, 'protected_half': protected,
            'resource_protected_half': bool(protected and budget['reserve_ok'] and budget['cap_ok']) if loss else None,
            'floor_violations': list(floors),
            'completed_units': sum(t is not None and t <= DEADLINE for t in ends)}


def scores(case, ends):
    if len(ends) != len(case['units']):
        raise ValueError('Missing unit completions')
    parent_ends = []
    for parent in range(4):
        times = [ends[j][0] for j, unit in enumerate(case['units']) if unit['parent'] == parent]
        parent_ends.append(max(times) if times and all(t is not None for t in times) else None)
    primary = ledger(case['loss'], case['parent_gains'], case['parent_floor_violations'], parent_ends, case['resource'])
    secondary = ledger(case['loss'], case['chunk_gains'], case['chunk_floor_violations'], [e[0] for e in ends], case['resource'])
    return {'original_parent_account': primary, 'secondary_chunk_account': secondary}


def scalar_scores(case, ends):
    """Independent explicit credit/floor accumulator for both granularities."""
    result = {}
    for chunk, key in ((False, 'original_parent_account'), (True, 'secondary_chunk_account')):
        credited = complete = 0
        for i in range(len(case['units']) if chunk else 4):
            indices = [i] if chunk else [j for j, unit in enumerate(case['units']) if unit['parent'] == i]
            good = bool(indices)
            for j in indices:
                if ends[j][0] is None or ends[j][0] > 6000000:
                    good = False
            if good:
                complete += 1
                credited += case['chunk_gains' if chunk else 'parent_gains'][i]
        floors = case['chunk_floor_violations' if chunk else 'parent_floor_violations']
        half = 2*credited >= case['loss'] if case['loss'] else None
        result[key] = {'credit': credited, 'half': half,
                       'protected_half': bool(half and sum(floors) == 0) if case['loss'] else None,
                       'completed_units': complete}
    return result


def schedule(cases):
    clips = sorted({c['clip'] for c in cases}); rows = []
    if len(clips) != 10 or len(cases) != 120:
        raise ValueError('Ten clips times twelve fixed cells required')
    for repetition in range(3):
        for i, clip in enumerate(clips):
            cells = sorted((c for c in cases if c['clip'] == clip),
                           key=lambda c: (POLICIES.index(c['policy']), c['unit_seconds'], c['buffered']))
            if len(cells) != 12 or len({(c['policy'], c['unit_seconds'], c['buffered']) for c in cells}) != 12:
                raise ValueError('Duplicate or missing fixed cell')
            rotate = (i+repetition) % 12
            for c in cells[rotate:]+cells[:rotate]:
                rows.append({'index': len(rows), 'case_id': c['case_id'], 'repetition': repetition, 'control': 'none'})
        base = next(c for c in cases if c['clip'] == clips[0] and c['policy'] == 'cost_greedy' and c['unit_seconds'] == 2 and not c['buffered'])
        for control in ('late_recipient', 'background'):
            rows.append({'index': len(rows), 'case_id': base['case_id'], 'repetition': repetition, 'control': control})
    if len(rows) != 366:
        raise ValueError('Expected 360 main sessions plus six controls')
    return rows


def player_entry(case, session):
    """Allowlist only delivery identity; never send offline quality to a player."""
    return {**session, 'clip': case['clip'], 'key': case['key'], 'policy': case['policy'],
        'unit_seconds': case['unit_seconds'], 'buffered': case['buffered'],
        'units': [{'parent': u['parent'], 'child': u['child'], 'duration': u['duration_ticks']/TICKS,
                   'files': [{k: f[k] for k in ('relative_path', 'sha256', 'bytes', 'duration', 'frames')} for f in u['files']]}
                  for u in case['units']]}
