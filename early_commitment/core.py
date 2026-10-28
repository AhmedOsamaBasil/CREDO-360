"""Causal visible-prefix selectors and identical-information recovery controls."""
from fractions import Fraction as F
from itertools import product
from causal_playback.core import menu
from service_opportunity.model import CAPACITY,optimize,valid
from recovery_objective.core import Action,Step,Contract,choose

POLICIES=('prefix_mpc','completed_mpc','prefix_cost_greedy','prefix_greedy',
          'prefix_nash','prefix_maxmin','wait_mpc','slack_mpc')
MATCHED=('completed_mpc','prefix_cost_greedy','prefix_greedy','prefix_nash','prefix_maxmin')


def transfer_offsets(sizes):
    if len(sizes)!=2 or min(sizes)<=0: raise ValueError('two positive file sizes required')
    return tuple(.13+(2*n if n==min(sizes) else sum(sizes))*8/1_200_000 for n in sizes)


def visible_index(items,user,now,delay,partial):
    if delay<0: raise ValueError('negative feedback delay')
    last=19
    for item in items:
        t=item['segment']; end=item['play_end'][user]
        if partial:
            for j in range(10):
                if end-10+j+.5+delay<=now+1e-10: last=max(last,t*10+j)
        elif end+delay<=now+1e-10: last=max(last,t*10+9)
    return last


def wait_time(mode,items,now,costs,remaining,delay):
    if mode not in ('wait_mpc','slack_mpc') or not items: return now
    pending=[end+delay for item in items for end in item['play_end'] if end+delay>now+1e-10]
    if not pending: return now
    report=min(pending)
    if mode=='wait_mpc': return report
    options=[transfer_offsets((costs[a],costs[b])) for a,b in product(range(2,6),repeat=2)
             if costs[a]+costs[b]<=CAPACITY and max(0,costs[a]+costs[b]-2*costs[2])<=remaining]
    if not options: raise ValueError('baseline infeasible')
    safe=min(items[-1]['play_end'][u]-max(x[u] for x in options) for u in (0,1))
    return report if report<=safe+1e-10 else now


def decision(policy,qualities,costs,t,loss,credit,pending,history,remaining):
    """qualities contains forecasts ONLY, not target labels or future poses."""
    if policy not in POLICIES or not 2<=t<6 or not 0<=credit<=loss or remaining<0:
        raise ValueError('invalid policy or ledger')
    ps=tuple(menu(qualities[s],costs[s]) for s in range(t,6))
    debt=max(0,loss-credit-sum(pending)); current=ps[0]
    if policy.endswith('mpc') or policy=='prefix_cost_greedy':
        horizon=ps if policy.endswith('mpc') else ps[:1]
        gain,cost,path=optimize(horizon,debt,remaining)
        selected=next(a for a in current if a.rungs==path[0])
    else:
        names={'prefix_greedy':'greedy_recovery','prefix_nash':'rolling_nash','prefix_maxmin':'rolling_maxmin'}
        available=valid(current,remaining)
        step=Step(tuple(F(x,1000) for x in current[0].reference),
                  tuple(Action(f'r{a.rungs[0]}d{a.rungs[1]}',tuple(F(x,1000) for x in a.quality),a.bytes) for a in available),CAPACITY)
        a=choose(names[policy],step,Contract((F(loss,1000),0),(0,0),(0,0)),(F(debt,1000),0),(0,0),
                 tuple(tuple(F(q,1000) for q in pair) for pair in history))
        selected=next(x for x in available if f'r{x.rungs[0]}d{x.rungs[1]}'==a.name)
        gain=min(debt,selected.gain); cost=max(0,selected.bytes-selected.reference_bytes); path=(selected.rungs,)
    return {'rungs':selected.rungs,'predicted_quality':selected.quality,'predicted_gain':selected.gain,
            'extra_bytes':max(0,selected.bytes-selected.reference_bytes),'bytes':selected.bytes,
            'planned_rungs':path,'planned_gain':gain,'planned_extra_bytes':cost,'estimated_debt':debt,
            'pending_predicted_credit':sum(pending),'observed_credit':credit}
