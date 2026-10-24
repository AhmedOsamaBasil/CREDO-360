"""Exact finite resource/donor frontiers and independent dynamic programming."""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
from math import prod
import numpy as np

EPSILONS=(0,125,250,500,1000,2000,4000)
BUDGETS=(0,250,500,1000,2000,4000,8000,16000)
TRANSFERS=(1,2,4)
RESOURCES=(F(1),F(11,10),F(5,4),F(3,2),F(2),F(3),F(4))
PROFILES=(('legacy',1,500,500),('no_donor_loss',4,0,0),
          ('step025_total05',4,250,500),('step05_total1',4,500,1000),
          ('step05_total2',4,500,2000),('step1_total4',4,1000,4000))


@dataclass(frozen=True)
class Action:
    gain:int
    harm:int
    multiplier:F
    bytes:int
    rungs:tuple
    quality:tuple
    reference:tuple
    reference_bytes:int

    @property
    def count(self): return int(self.gain>0)


def actions(recipient,donor,sizes):
    if len(recipient)!=6 or len(donor)!=6 or len(sizes)!=6 or any(s<=0 for s in sizes):
        raise ValueError('six valid representations required')
    ref=(recipient[2],donor[2]); reference_bytes=2*sizes[2]
    return tuple(Action(recipient[r]-ref[0],max(ref[1]-donor[d],0),
                        max(F(1),F(sizes[r]+sizes[d],reference_bytes)),sizes[r]+sizes[d],
                        (r,d),(recipient[r],donor[d]),ref,reference_bytes)
                 for r,d in product(range(6),repeat=2) if recipient[r]>=ref[0])


def prune(options,target):
    """Dominance is valid for this target and allowance definition only."""
    signatures={}
    for a in sorted(options,key=lambda a:a.rungs):
        signature=(-min(a.gain,target),a.harm,a.multiplier,a.count)
        signatures.setdefault(signature,a)
    return tuple(a for s,a in signatures.items() if not any(t!=s and all(x<=y for x,y in zip(t,s)) for t in signatures))


def witness(path,debt):
    remaining=debt; trace=[]
    for t,a in enumerate(path):
        credit=min(remaining,a.gain); remaining-=credit
        trace.append({'period':t,'rungs':a.rungs,'quality':a.quality,'reference':a.reference,
                      'gain_units':a.gain,'harm_units':a.harm,'bytes':a.bytes,'reference_bytes':a.reference_bytes,
                      'delivered_credit_units':credit,'remaining_units':remaining})
    return {'peak_multiplier':max(a.multiplier for a in path),
            'total_byte_ratio':F(sum(a.bytes for a in path),sum(a.reference_bytes for a in path)),
            'donor_total_units':sum(a.harm for a in path),'donor_peak_units':max(a.harm for a in path),
            'recovery_actions':sum(a.count for a in path),'delivered_units':debt-remaining,
            'remaining_fraction':F(remaining,debt),'trace':trace}


def frontier(periods,debt,pruning=True):
    if not isinstance(debt,int) or debt<=0 or not 1<=len(periods)<=4 or any(not p for p in periods):
        raise ValueError('positive integer loss and one to four nonempty periods required')
    target=(debt+1)//2
    reduced=tuple(prune(p,target) if pruning else tuple(p) for p in periods)
    shape=tuple(map(len,reduced)); n=prod(shape)
    if n>3_000_000: raise ValueError('reference enumeration size exceeded')
    levels=sorted({a.multiplier for p in reduced for a in p})
    ranks={x:i for i,x in enumerate(levels)}
    indices=np.indices(shape,dtype=np.int32).reshape(len(shape),-1)
    gain=np.zeros(n,dtype=np.int64); harm=gain.copy(); peak=gain.copy(); count=gain.copy(); rank=gain.copy()
    for t,p in enumerate(reduced):
        j=indices[t]
        gain+=np.array([min(a.gain,target) for a in p],dtype=np.int64)[j]
        h=np.array([a.harm for a in p],dtype=np.int64)[j]; harm+=h; peak=np.maximum(peak,h)
        count+=np.array([a.count for a in p],dtype=np.int64)[j]
        rank=np.maximum(rank,np.array([ranks[a.multiplier] for a in p],dtype=np.int64)[j])
    eligible=np.flatnonzero(gain>=target)
    infinity=np.iinfo(np.int64).max//2
    table=np.full((5,len(EPSILONS),len(levels)),infinity,dtype=np.int64)
    ep=np.searchsorted(EPSILONS,peak[eligible])
    valid=ep<len(EPSILONS); eligible=eligible[valid]; ep=ep[valid]
    # Lexicographic (cumulative harm, stable complete-path index).
    codes=harm[eligible]*(n+1)+eligible
    if len(codes) and codes.max()>=infinity: raise ValueError('integer witness code overflow')
    np.minimum.at(table,(count[eligible],ep,rank[eligible]),codes)
    for axis in range(3): table=np.minimum.accumulate(table,axis=axis)
    frontiers={}
    for m in TRANSFERS:
        for e,epsilon in enumerate(EPSILONS):
            points=[]; best=infinity
            for r,code in enumerate(table[m,e]):
                if code==infinity: continue
                h=int(code)//(n+1)
                if h>=best: continue
                best=h; flat=int(code)%(n+1)
                path=tuple(p[int(indices[t,flat])] for t,p in enumerate(reduced))
                w=witness(path,debt)
                assert w['donor_total_units']==h and w['peak_multiplier']==levels[r]
                assert w['donor_peak_units']<=epsilon and w['recovery_actions']<=m
                assert w['delivered_units']>=target
                points.append(w)
            frontiers[f'{m}:{epsilon}']=points
    return {'target_units':target,'full_action_counts':tuple(map(len,periods)),
            'pruned_action_counts':shape,'enumerated_paths':n,'qualifying_pruned_paths':len(eligible),
            'frontiers':frontiers}


def required(frontiers,m,epsilon,budget):
    if budget<0: raise ValueError('nonnegative donor budget required')
    return next((p for p in frontiers[f'{m}:{epsilon}'] if p['donor_total_units']<=budget),None)


def feasible(frontiers,m,epsilon,budget,multiplier):
    p=required(frontiers,m,epsilon,budget)
    return p is not None and p['peak_multiplier']<=multiplier


def dp_feasible(periods,debt,m,epsilon,budget,multiplier):
    """Independent multiple-choice DP; no frontier pruning, ratio ranks or arrays."""
    target=(debt+1)//2; states={(0,0):0}
    for options in periods:
        updated={}
        for (count,harm),gain in states.items():
            for a in options:
                c,h=count+a.count,harm+a.harm
                if c<=m and a.harm<=epsilon and h<=budget and a.multiplier<=multiplier:
                    key=c,h; updated[key]=max(updated.get(key,-1),min(target,gain+a.gain))
        # For each count, remove states with no gain improvement at greater harm.
        states={}; best={}
        for (c,h),g in sorted(updated.items()):
            if g>best.get(c,-1): states[c,h]=g; best[c]=g
    return max(states.values(),default=0)>=target


def verify_witness(point,periods,debt,m,epsilon):
    path=[]
    for t,row in enumerate(point['trace']):
        a=next(a for a in periods[t] if a.rungs==tuple(row['rungs']))
        path.append(a)
    expected=witness(path,debt)
    assert expected==point
    assert point['donor_peak_units']<=epsilon and point['recovery_actions']<=m
    assert point['delivered_units']>=(debt+1)//2
    assert point['delivered_units']+point['trace'][-1]['remaining_units']==debt
    return True
