"""Constructed examples only; no fitted future model or network measurements."""
from dataclasses import dataclass
from fractions import Fraction as F
from recovery_objective.core import Action,Step,Contract
from reserve_recovery.core import Slot


@dataclass(frozen=True)
class Problem:
    name:str
    description:str
    scenarios:tuple
    reserve:F=F(1)
    contract:Contract=Contract((1,0),(0,0),(0,0))
    history:tuple=((F(5,2),F(3)),)*2


def offer(gain,cost=F(1),capacity=F(2)):
    actions=[Action('baseline',(3,3),1)]
    if gain: actions.append(Action('boost',(3+F(gain),3),1+F(cost)))
    return Slot(Step((3,3),tuple(actions),F(capacity)),F(1))


def bounded(a=F(2,5),low=F(3,5),high=F(9,10),reserve=F(1)):
    return Problem('bounded_better_future','Known future lower gain exceeds current gain; realized future remains unknown.',
                   ((offer(a),offer(low)),(offer(a),offer(high))),F(reserve))


def problems():
    return (bounded(),
        Problem('disappearing_opportunity','A safe immediate repayment dominates the worst vanishing future.',
                ((offer(F(3,5)),offer(0)),(offer(F(3,5)),offer(1)))),
        Problem('no_half_repayment_admission','The worst future cannot repay half even with advance knowledge.',
                ((offer(F(2,5)),offer(0)),(offer(F(2,5)),offer(F(9,10))))),
        Problem('nonbinding_reserve','Both opportunities fit; no timing advantage is needed.',bounded().scenarios,F(2)),
        Problem('zero_reserve','Capacity alone does not grant a byte entitlement.',bounded().scenarios,F(0)),
        Problem('no_instantaneous_headroom','A full reserve cannot create present physical capacity.',
                ((offer(F(2,5),capacity=1),offer(1,capacity=1)),)),
        Problem('delayed_revelation','Small early expenditure blocks a more useful later action.',
                ((offer(F(1,5),F(1,2)),offer(F(2,5)),offer(F(7,10))),
                 (offer(F(1,5),F(1,2)),offer(F(2,5)),offer(F(9,10))))),
        Problem('causal_admission_gap','Each future meets the target offline, but no shared-prefix decision can ensure it.',
                ((offer(F(3,10),F(2,5)),offer(F(3,10),F(3,5))),
                 (offer(F(3,10),F(2,5)),offer(F(3,5),1)))))
