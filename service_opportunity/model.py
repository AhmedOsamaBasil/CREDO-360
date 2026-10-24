"""Prefix-only point forecasting and exact finite-reserve lookahead."""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
from causal_compensation.data import ROOT,SOURCES,source_paths,quality_units
from feasibility_frontier.data import load
from feasibility_frontier.core import actions
import csv

CAPACITY=1_500_000
RATIOS=(F(1,2),F(1),F(2))
CONTROLS=('rolling_nash','rolling_maxmin','greedy_recovery','persistence_mpc')
POLICIES=('knn_mpc',)+CONTROLS+('offline',)


@dataclass(frozen=True)
class Record:
    key:str
    scene:str
    recipient:int
    donor:int
    loss:int
    qualities:tuple


def records():
    q={}
    for cohort,folder in SOURCES.items():
        for filename in ('calibration_quality.csv','heldout_quality.csv'):
            with (ROOT/folder/filename).open(newline='') as f:
                for row in csv.DictReader(f):
                    k=cohort,row['content'],int(row['subject']),int(row['segment']),int(row['ladder_index'])
                    q[k]=quality_units(row['vw_psnr_db'])
    result=[]
    for e,periods in load():
        qualities=tuple(tuple(tuple(q[e.cohort,e.scene,u,t,r] for r in range(6))
                              for u in (e.recipient,e.donor)) for t in range(2,6))
        result.append(Record(e.key,e.scene,e.recipient,e.donor,e.loss,qualities))
    return tuple(result)


def pool(all_records,target):
    ids={target.recipient,target.donor}
    training=tuple(r for r in all_records if r.scene!=target.scene
                   and not ids.intersection((r.recipient,r.donor)))
    if len(training)!=130: raise ValueError('unexpected training shape')
    return training


def forecast(prefix,loss,training,k=8):
    """Target future and target record cannot be passed to this interface."""
    if not 1<=len(prefix)<=4 or len(training)<k or k<1 or loss<=0:
        raise ValueError('invalid prefix/training')
    def distance(r):
        return abs(loss-r.loss)+sum(abs(a-b) for current,old in zip(prefix,r.qualities)
                                   for x,y in zip(current,old) for a,b in zip(x,y))
    nearest=sorted(training,key=lambda r:(distance(r),r.key))[:k]
    future=tuple(tuple(tuple((sum(r.qualities[t][u][j] for r in nearest)*2+k)//(2*k)
                            for j in range(6)) for u in range(2))
                 for t in range(len(prefix),4))
    return future,tuple({'key':r.key,'distance':distance(r)} for r in nearest)


def sizes(options):
    # The full zero-recipient-loss menu always includes recipient rung2 and
    # every donor rung. This extracts known sender bytes, not viewport labels.
    baseline=options[0].reference_bytes//2
    return tuple(next(a.bytes-baseline for a in options if a.rungs==(2,j)) for j in range(6))


def predicted_periods(qualities,costs):
    return tuple(actions(q[0],q[1],s) for q,s in zip(qualities,costs))


def valid(options,remaining,cap=CAPACITY):
    out=tuple(a for a in options if a.harm==0 and a.bytes<=cap
              and max(a.bytes-a.reference_bytes,0)<=remaining)
    if not any(a.rungs==(2,2) for a in out): raise ValueError('baseline infeasible')
    return out


def optimize(periods,debt,reserve,cap=CAPACITY):
    """Exact capped gain -> minimum cost frontier; integral complete paths."""
    if debt<0 or reserve<0 or not periods: raise ValueError('invalid horizon/state')
    states={0:(0,())}
    for options in periods:
        updated={}
        for gain,(cost,path) in states.items():
            for a in valid(options,reserve-cost,cap):
                g=min(debt,gain+a.gain)
                candidate=cost+max(a.bytes-a.reference_bytes,0),path+(a.rungs,)
                if g not in updated or candidate<updated[g]: updated[g]=candidate
        states={}; cheapest=None
        for g in sorted(updated,reverse=True):
            if cheapest is None or updated[g][0]<cheapest:
                states[g]=updated[g]; cheapest=updated[g][0]
    gain=max(states); cost,path=states[gain]
    return gain,cost,path


def brute(periods,debt,reserve,cap=CAPACITY):
    choices=[]
    for path in product(*(valid(p,reserve,cap) for p in periods)):
        cost=sum(max(a.bytes-a.reference_bytes,0) for a in path)
        if cost<=reserve:
            choices.append((-min(debt,sum(a.gain for a in path)),cost,tuple(a.rungs for a in path)))
    g,c,p=min(choices)
    return -g,c,p
