"""Exact four-step opportunity audit; future-known bounds, not online policy."""
from dataclasses import dataclass
from itertools import product
import numpy as np


@dataclass(frozen=True)
class Offer:
    rungs:tuple
    gain:int
    extra:int
    quality:tuple
    floor:bool


def periods(record):
    result=[]
    for t in range(2,6):
        q=record.quality[t]; c=record.costs[t]
        result.append(tuple(Offer((a,b),max(0,q[0][a]-q[0][2]),max(0,c[a]+c[b]-2*c[2]),
                                  (q[0][a],q[1][b]),q[0][a]>=q[0][2] and q[1][b]>=q[1][2])
                            for a,b in product(range(2,6),repeat=2) if c[a]+c[b]<=1_500_000))
    return tuple(result)


def dp(ps,debt,budget,strict):
    states={0:(0,())}
    for options in ps:
        new={}
        for gain,(cost,path) in states.items():
            for a in options:
                if cost+a.extra>budget or (strict and not a.floor): continue
                g=min(debt,gain+a.gain); entry=(cost+a.extra,path+(a.rungs,))
                if g not in new or entry<new[g]: new[g]=entry
        states={}; least=None
        for g in sorted(new,reverse=True):
            if least is None or new[g][0]<least: states[g]=new[g]; least=new[g][0]
    g=max(states); c,p=states[g]
    return g,c,p


def enumerate_paths(ps,debt,budget,quality_floor):
    idx=np.indices(tuple(map(len,ps)),dtype=np.int32).reshape(4,-1)
    n=idx.shape[1]; gain=np.zeros(n,np.int64); cost=gain.copy(); q0=gain.copy(); q1=gain.copy(); strict=np.ones(n,bool)
    for t,p in enumerate(ps):
        j=idx[t]; gain+=np.array([a.gain for a in p])[j]; cost+=np.array([a.extra for a in p])[j]
        q0+=np.array([a.quality[0] for a in p])[j]; q1+=np.array([a.quality[1] for a in p])[j]
        strict &= np.array([a.floor for a in p])[j]
    gain=np.minimum(gain,debt); feasible=cost<=budget
    result={}
    for name,mask in [('structural',feasible),('strict',feasible&strict),
                      ('quality_guard',feasible&strict&(np.minimum(q0,q1)/4000>=quality_floor-1e-12))]:
        eligible=np.flatnonzero(mask)
        if not len(eligible): result[name]=None; continue
        best=min(eligible,key=lambda k:(-int(gain[k]),int(cost[k]),int(k)))
        path=tuple(ps[t][int(idx[t,best])].rungs for t in range(4))
        result[name]={'gain':int(gain[best]),'extra_bytes':int(cost[best]),'path':path,
                      'unpaid_fraction':float((debt-gain[best])/debt),'half_repaid':bool(2*gain[best]>=debt),
                      'worst_quality':float(min(q0[best],q1[best])/4000),
                      'minimum_half_bytes':int(cost[mask&(2*gain>=debt)].min()) if np.any(mask&(2*gain>=debt)) else None}
    for name,flag in [('structural',False),('strict',True)]:
        g,c,path=dp(ps,debt,budget,flag)
        assert (g,c,path)==(result[name]['gain'],result[name]['extra_bytes'],result[name]['path'])
    remaining=debt; available=budget; choices=[]
    for p in ps:
        a=min((a for a in p if a.floor and a.extra<=available),key=lambda a:(-min(remaining,a.gain),a.extra,a.rungs))
        remaining-=min(remaining,a.gain); available-=a.extra; choices.append(a.rungs)
    result['exact_current_greedy']={'unpaid_fraction':remaining/debt,'half_repaid':2*remaining<=debt,
                                  'extra_bytes':budget-available,'path':tuple(choices)}
    return {'enumerated_paths':n,'feasible_paths':int(feasible.sum()),'strict_paths':int((feasible&strict).sum()),'bounds':result}
