"""Decision API accepts sender metadata and completed feedback, never target labels."""
from fractions import Fraction as F
from math import prod
from feasibility_frontier.core import actions
from service_opportunity.model import CAPACITY,optimize
from recovery_objective.core import Action,Step,Contract,choose

POLICIES=('knn_recovery','greedy_recovery','cost_greedy','rolling_nash',
          'rolling_maxmin','persistence_mpc','unconditional_mpc')
LIVE_POLICIES=('knn_recovery','greedy_recovery','rolling_nash','rolling_maxmin')


def clip(x): return max(1000,min(5000,int(x)))
def mean(values): return (2*sum(values)+len(values))//(2*len(values))


def residuals(observations,sender):
    result=[]
    for user in (0,1):
        residual=None
        for t,u,rung,q in sorted(observations):
            if u!=user: continue
            delta=q-sender[t][rung]
            residual=delta if residual is None else mean((residual,delta))
        if residual is None: raise ValueError('completed history required')
        result.append(residual)
    return tuple(result)


def menu(quality,costs):
    # Structural rung floor is knowable without target viewport-quality labels.
    return tuple(a for a in actions(quality[0],quality[1],costs) if min(a.rungs)>=2)


def neighbors(observations,loss,training,k=8):
    if len(training)<k: raise ValueError('insufficient excluded training pool')
    def distance(r):
        return abs(loss-r.loss)+sum(abs((q-g)-(r.quality[t][u][j]-r.sender[t][j]))
                                   for t,u,j,q,g in observations)
    return tuple(sorted(training,key=lambda r:(distance(r),r.key))[:k])


def decide(policy,loss,observations,observed_credit,pending_gains,history,sender,costs,t,training,reserve):
    """Only completed selected quality observations may enter this function.

    sender/costs are public offline representation properties for all six
    segments. training excludes target scene and identities. No target Record.
    """
    if policy not in POLICIES or not 2<=t<6 or any(o[0]>=t for o in observations):
        raise ValueError('invalid policy/time or unavailable observation')
    if not 0<=observed_credit<=loss or reserve<0: raise ValueError('invalid ledger')
    rs=residuals(observations,sender)
    estimate=tuple(tuple(clip(g+r) for g in sender[t]) for r in rs)
    current=menu(estimate,costs[t]); debt=max(0,loss-observed_credit-sum(pending_gains))
    keys=(); future=[]
    if policy in ('knn_recovery','persistence_mpc','unconditional_mpc'):
        if policy!='persistence_mpc':
            obs=tuple((s,u,r,q,sender[s][r]) for s,u,r,q in observations)
            near=neighbors(obs,loss,training,8 if policy=='knn_recovery' else len(training))
            keys=tuple(r.key for r in near)
        for s in range(t+1,6):
            if policy=='persistence_mpc': q=tuple(tuple(clip(g+r) for g in sender[s]) for r in rs)
            else:
                q=tuple(tuple(clip(sender[s][j]+mean(tuple(r.quality[s][u][j]-r.sender[s][j] for r in near)))
                              for j in range(6)) for u in range(2))
            future.append(menu(q,costs[s]))
    if policy in ('knn_recovery','persistence_mpc','unconditional_mpc','cost_greedy'):
        gain,cost,path=optimize((current,)+tuple(future),debt,reserve)
        selected=next(a for a in current if a.rungs==path[0])
    else:
        ref=tuple(F(x,1000) for x in current[0].reference)
        choices=tuple(Action(f'r{a.rungs[0]}d{a.rungs[1]}',tuple(F(x,1000) for x in a.quality),a.bytes)
                      for a in current if max(a.bytes-a.reference_bytes,0)<=reserve)
        c=Contract((F(loss,1000),0),(0,0),(0,0))
        a=choose(policy,Step(ref,choices,CAPACITY),c,(F(debt,1000),0),(0,0),
                 tuple(tuple(F(q,1000) for q in pair) for pair in history))
        selected=next(x for x in current if f'r{x.rungs[0]}d{x.rungs[1]}'==a.name)
        gain=min(debt,selected.gain); cost=max(selected.bytes-selected.reference_bytes,0); path=(selected.rungs,)
    assert selected.harm==0 and selected.bytes<=CAPACITY and cost<=reserve
    return {'rungs':selected.rungs,'predicted_quality':selected.quality,'current_estimates':estimate,
            'residuals':rs,'predicted_gain':selected.gain,'estimated_debt':debt,
            'observed_credit':observed_credit,'pending_predicted_credit':sum(pending_gains),
            'bytes':selected.bytes,'extra_bytes':max(selected.bytes-selected.reference_bytes,0),
            'planned_rungs':path,'predicted_additional_gain':gain,'neighbor_keys':keys}
