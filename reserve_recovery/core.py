"""Exact reference controller with separate byte entitlement and slot capacity."""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
from math import prod
from recovery_objective.core import Step,allowed,feedback,choose,evaluate,objective


@dataclass(frozen=True)
class Slot:
    step: Step
    baseline_bytes: F

    def __post_init__(self):
        object.__setattr__(self,'baseline_bytes',F(self.baseline_bytes))
        if self.baseline_bytes<=0 or self.baseline_bytes>self.step.resource_cap:
            raise ValueError('baseline must fit contemporaneous capacity')
        if not any(a.quality==self.step.reference and a.resources==self.baseline_bytes for a in self.step.actions):
            raise ValueError('explicit original baseline action required')


def extra(slot,action): return max(action.resources-slot.baseline_bytes,F(0))


def legal(slot,contract,donor_spent,reserve,spent):
    reserve,spent=F(reserve),F(spent)
    if not 0<=spent<=reserve: raise ValueError('invalid reserve ledger')
    return tuple(a for a in allowed(slot.step,contract,donor_spent) if extra(slot,a)<=reserve-spent)


def result(path,schedule,contract,reserve):
    if len(path)!=len(schedule) or not path: raise ValueError('complete nonempty path required')
    debt=contract.debt; donor=tuple(F(0) for _ in debt); spent=F(0); ledger=[]
    for slot,action in zip(schedule,path):
        if action not in legal(slot,contract,donor,reserve,spent): raise ValueError('reserve or capacity violation')
        spent+=extra(slot,action)
        debt,donor,credits=feedback(slot.step,action,contract,debt,donor)
        ledger.append({'extra_bytes':extra(slot,action),'spent_bytes':spent,'remaining_bytes':F(reserve)-spent})
    out=evaluate(path,tuple(s.step for s in schedule),contract)
    assert out['outstanding']==debt
    return {**out,'reserve_bytes':F(reserve),'extra_bytes':spent,'remaining_reserve_bytes':F(reserve)-spent,
            'reserve_ledger':ledger,'half_repaid':out['terminal_max_fraction']<=F(1,2)}


def online(name,schedule,contract,reserve,history=()):
    debt=contract.debt; donor=tuple(F(0) for _ in debt); spent=F(0); path=[]; history=list(history)
    for slot in schedule:
        menu=legal(slot,contract,donor,reserve,spent)
        current=Step(slot.step.reference,menu,slot.step.resource_cap)
        action=choose(name,current,contract,debt,donor,history)
        path.append(action); history.append(action.quality); spent+=extra(slot,action)
        debt,donor,_=feedback(slot.step,action,contract,debt,donor)
    return result(tuple(path),schedule,contract,reserve)


def paths(schedule,contract,reserve):
    candidates=[]
    for path in product(*(tuple(sorted(s.step.actions,key=lambda a:a.name)) for s in schedule)):
        try: out=result(path,schedule,contract,reserve)
        except ValueError: continue
        candidates.append((path,out))
    return tuple(candidates)


def observation(slot):
    return (slot.baseline_bytes,slot.step.reference,slot.step.resource_cap,
            tuple(sorted((a.name,a.quality,a.resources) for a in slot.step.actions)))


def plan(scenarios,contract,reserve):
    if not scenarios or not scenarios[0] or any(len(s)!=len(scenarios[0]) for s in scenarios):
        raise ValueError('equal nonempty scenario horizons required')
    candidates=tuple(paths(s,contract,reserve) for s in scenarios)
    if any(not p for p in candidates) or prod(map(len,candidates))>200000:
        raise ValueError('infeasible problem or reference enumeration limit')
    policies=[]
    for combination in product(*candidates):
        mapping={}; consistent=True
        for schedule,(path,out) in zip(scenarios,combination):
            prefix=()
            for slot,action in zip(schedule,path):
                prefix+=(observation(slot),)
                if prefix in mapping and mapping[prefix]!=action.name:
                    consistent=False; break
                mapping[prefix]=action.name
            if not consistent: break
        if consistent:
            policies.append({'mapping':mapping,'paths':tuple(p for p,r in combination),
                             'outcomes':tuple(r for p,r in combination)})
    def key(i):
        rows=policies[i]['outcomes']; losses=[r['terminal_max_fraction'] for r in rows]
        costs=[r['extra_bytes'] for r in rows]
        return max(losses),sum(losses),max(costs),sum(costs),i
    best=min(range(len(policies)),key=key)
    oracle=tuple(min((out for path,out in c),key=lambda r:(r['terminal_max_fraction'],r['extra_bytes'])) for c in candidates)
    value=key(best)[0]
    independent=bellman(scenarios,contract,reserve)
    assert value==independent
    return {'policies':policies,'best':best,'worst_loss':value,'admitted':value<=F(1,2),
            'oracle':oracle,'bellman_value':independent}


def bellman(scenarios,contract,reserve):
    """Independent robust recursion; no path combinations or policy mappings."""
    def visit(indices,t,debt,donor,spent):
        if t==len(scenarios[0]): return objective(debt,contract.debt)[0]
        groups={}
        for j in indices: groups.setdefault(observation(scenarios[j][t]),[]).append(j)
        values=[]
        for group in groups.values():
            slot=scenarios[group[0]][t]; choices=[]
            for a in legal(slot,contract,donor,reserve,spent):
                next_debt,next_donor,_=feedback(slot.step,a,contract,debt,donor)
                choices.append(visit(group,t+1,next_debt,next_donor,spent+extra(slot,a)))
            values.append(min(choices))
        return max(values)
    return visit(tuple(range(len(scenarios))),0,contract.debt,tuple(F(0) for _ in contract.debt),F(0))


def execute(policy,schedule,contract,reserve,history=()):
    prefix=(); debt=contract.debt; donor=tuple(F(0) for _ in debt); spent=F(0)
    breach=False; path=[]; history=list(history)
    for slot in schedule:
        prefix+=(observation(slot),); menu=legal(slot,contract,donor,reserve,spent)
        a=next((a for a in menu if a.name==policy['mapping'].get(prefix)),None)
        if a is None: breach=True
        if breach:
            current=Step(slot.step.reference,menu,slot.step.resource_cap)
            a=choose('greedy_recovery',current,contract,debt,donor,history)
        path.append(a); history.append(a.quality); spent+=extra(slot,a)
        debt,donor,_=feedback(slot.step,a,contract,debt,donor)
    return {**result(tuple(path),schedule,contract,reserve),'model_breach':breach}
