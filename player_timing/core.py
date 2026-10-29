"""Pure timing/resource/accounting functions; no future-quality policy inputs."""
import math

RATE = 150000
SETUP = .13
DEADLINE = 40.
CAP = 1500000


def receipt_schedule(sizes, cadence, setup=SETUP, rate=RATE):
    if cadence <= 0 or setup < 0 or rate <= 0:
        raise ValueError('Invalid service')
    start = 0.; arrivals = []; requests = []
    for pair in sizes:
        if len(pair) != 2 or any(int(n) != n or n <= 0 for n in pair):
            raise ValueError('Two positive integer payload sizes required')
        a, b = pair
        end = [start+setup+min(2*a,a+b)/rate,
               start+setup+min(2*b,a+b)/rate]
        requests.append(start); arrivals.append(end)
        start = max(start+cadence, *end)
    return requests, arrivals


def queue(arrivals, durations, buffered=False):
    if len(arrivals) != len(durations) or not durations:
        raise ValueError('Missing unit')
    if any(not math.isfinite(d) or d <= 0 for d in durations):
        raise ValueError('Invalid duration')
    gate = 0.
    if buffered:
        accumulated=0.; i=0
        while accumulated < 4-1e-9:
            if i == len(durations): raise ValueError('Cannot reach buffer threshold')
            accumulated += durations[i]; i += 1
        gate = max(max(pair) for pair in arrivals[:i])
    ends=[]; cursor=[gate,gate]
    for pair,d in zip(arrivals,durations):
        cursor=[max(cursor[u],pair[u])+d for u in (0,1)]
        ends.append(cursor)
    return ends,gate


def resources(sizes, baseline, parents, reserve):
    if not len(sizes)==len(baseline)==len(parents): raise ValueError('Resource axes')
    aggregate={}; extra=0
    for pair,base,parent in zip(sizes,baseline,parents):
        extra += max(0,sum(pair)-sum(base))
        aggregate[parent]=aggregate.get(parent,0)+sum(pair)
    return {'extra_bytes':int(extra),'reserve_bytes':int(reserve),
            'reserve_ok':bool(extra<=reserve),'parent_bytes':[aggregate[p] for p in sorted(aggregate)],
            'cap_ok':bool(all(n<=CAP for n in aggregate.values())),
            'payload_bytes':int(sum(map(sum,sizes)))}


def ledger(loss, gains, violations, ends, deadline=DEADLINE):
    if loss<=0 or not len(gains)==len(ends): raise ValueError('Invalid ledger')
    credit=sum(g for g,t in zip(gains,ends) if t is not None and t<=deadline+1e-9)
    eventual=sum(gains)
    half=2*credit>=loss
    return {'loss':float(loss),'credit':float(credit),'eventual_credit':float(eventual),
            'fraction_repaid':float(min(credit/loss,1)), 'half':bool(half),
            'protected_half':bool(half and not any(violations)),
            'floor_violations':list(map(int,violations)),
            'completed_units':sum(t is not None and t<=deadline+1e-9 for t in ends)}


def scores(case, ends, resource=None):
    """Case carries offline evaluation labels; the player receives none of them."""
    parent_ends=[]
    for parent in range(4):
        times=[ends[i][0] for i,u in enumerate(case['units']) if u['parent']==parent]
        parent_ends.append(max(times) if all(t is not None for t in times) else None)
    primary=ledger(case['loss'],case['parent_gains'],case['parent_floor_violations'],parent_ends)
    secondary=ledger(case['loss'],case['chunk_gains'],case['chunk_floor_violations'],[e[0] for e in ends])
    if resource is not None:
        for s in (primary,secondary):
            s['resource_protected_half']=bool(s['protected_half'] and resource['reserve_ok'] and resource['cap_ok'])
    return {'original_parent_account':primary,'secondary_chunk_account':secondary,
            'parent_ends':parent_ends}


def tail_witness(frames, expected_frames, fps=30):
    if not frames: return False
    return max(f['mediaTime'] for f in frames) >= (expected_frames-1)/fps-1.5/fps
