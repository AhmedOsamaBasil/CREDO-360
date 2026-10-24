"""Rational-arithmetic reference model, not a deployable streaming controller."""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
from math import prod


def vector(values):
    result = tuple(F(x) for x in values)
    if not result:
        raise ValueError('empty vector')
    return result


@dataclass(frozen=True)
class Action:
    name: str
    quality: tuple
    resources: F = F(1)

    def __post_init__(self):
        object.__setattr__(self, 'quality', vector(self.quality))
        object.__setattr__(self, 'resources', F(self.resources))
        if not self.name or any(x <= 0 for x in self.quality) or self.resources < 0:
            raise ValueError('named positive-quality action with nonnegative resources required')


@dataclass(frozen=True)
class Step:
    reference: tuple
    actions: tuple
    resource_cap: F = F(1)

    def __post_init__(self):
        object.__setattr__(self, 'reference', vector(self.reference))
        object.__setattr__(self, 'actions', tuple(self.actions))
        object.__setattr__(self, 'resource_cap', F(self.resource_cap))
        if any(x <= 0 for x in self.reference) or self.resource_cap < 0:
            raise ValueError('positive reference and nonnegative resource cap required')
        if not self.actions or len({a.name for a in self.actions}) != len(self.actions):
            raise ValueError('nonempty uniquely named action set required')
        if any(len(a.quality) != len(self.reference) for a in self.actions):
            raise ValueError('quality dimensions must agree')
        if not any(a.quality == self.reference and a.resources <= self.resource_cap for a in self.actions):
            raise ValueError('a feasible reference action must be available; never silently relax it')


@dataclass(frozen=True)
class Contract:
    debt: tuple
    donor_step_allowance: tuple
    donor_total_allowance: tuple
    window: int = 24

    def __post_init__(self):
        for key in ('debt', 'donor_step_allowance', 'donor_total_allowance'):
            object.__setattr__(self, key, vector(getattr(self, key)))
        n = len(self.debt)
        if any(len(x) != n for x in (self.donor_step_allowance, self.donor_total_allowance)):
            raise ValueError('contract dimensions must agree')
        if any(x < 0 for v in (self.debt, self.donor_step_allowance, self.donor_total_allowance) for x in v):
            raise ValueError('negative loss or protection allowance')
        if not isinstance(self.window, int) or self.window < 1:
            raise ValueError('positive integer window required')
        if any(d > 0 and (s != 0 or b != 0) for d, s, b in zip(self.debt, self.donor_step_allowance, self.donor_total_allowance)):
            raise ValueError('affected users must retain their current reference floor')


def event_loss(references, observed, affected):
    """Positive shortfall within the declared event; no pre-event surplus bank."""
    references, observed, affected = tuple(references), tuple(observed), tuple(affected)
    if not references or len(references) != len(observed) or not affected:
        raise ValueError('nonempty equal-length event records and user mask required')
    if any(len(row) != len(affected) for row in references + observed):
        raise ValueError('event dimensions must agree')
    if any(F(x) <= 0 for row in references + observed for x in row):
        raise ValueError('positive reference and observed quality required')
    return tuple(sum((max(F(r[i])-F(q[i]), F(0)) for r, q in zip(references, observed)), F(0)) if yes else F(0)
                 for i, yes in enumerate(affected))


def normalized(debt, original):
    return tuple(d / initial for d, initial in zip(debt, original) if initial > 0)


def objective(debt, original):
    ratios = normalized(debt, original)
    return max(ratios, default=F(0)), sum(ratios, F(0))


def allowed(step, contract, donor_spent):
    if len(step.reference) != len(contract.debt) or len(donor_spent) != len(contract.debt):
        raise ValueError('state dimensions must agree')
    if any(x < 0 for x in donor_spent):
        raise ValueError('negative donor expenditure')
    result = []
    for action in step.actions:
        if action.resources > step.resource_cap:
            continue
        losses = tuple(max(b-q, F(0)) for b, q in zip(step.reference, action.quality))
        if all(loss <= limit and used + loss <= budget for loss, limit, used, budget in
               zip(losses, contract.donor_step_allowance, donor_spent, contract.donor_total_allowance)):
            result.append(action)
    if not result:
        raise ValueError('empty protected feasible action set')
    return tuple(result)


def feedback(step, action, contract, debt, donor_spent):
    """Credit only delivered excess; never forgive debt by expiry/feasibility."""
    if action not in allowed(step, contract, donor_spent):
        raise ValueError('unprotected or infeasible action')
    if len(debt) != len(contract.debt) or any(d < 0 or d > d0 for d, d0 in zip(debt, contract.debt)):
        raise ValueError('outstanding debt outside original event ledger')
    credits = tuple(min(d, max(q-b, F(0))) for d, q, b in zip(debt, action.quality, step.reference))
    harm = tuple(max(b-q, F(0)) for q, b in zip(action.quality, step.reference))
    return (tuple(d-c for d, c in zip(debt, credits)),
            tuple(old+x for old, x in zip(donor_spent, harm)), credits)


ONLINE_POLICIES = ('stateless_nash', 'rolling_nash', 'rolling_maxmin', 'max_weight', 'greedy_recovery')


def choose(policy, step, contract, debt, donor_spent, history):
    """Only CURRENT feasible qualities and past feedback enter online rules.

    Perfect-current-quality information is an analytical assumption. There is
    no viewport predictor, future schedule, calibrated interval or human model.
    """
    if policy not in ONLINE_POLICIES:
        raise ValueError(policy)
    history = tuple(vector(row) for row in history)
    if any(len(row) != len(contract.debt) or any(q <= 0 for q in row) for row in history):
        raise ValueError('invalid positive-quality history')
    recent = history[-(contract.window-1):] if contract.window > 1 else ()
    past = tuple(sum((row[i] for row in recent), F(0)) for i in range(len(contract.debt)))
    def key(action):
        totals = tuple(p+q for p, q in zip(past, action.quality))
        if policy == 'greedy_recovery':
            next_debt, _, _ = feedback(step, action, contract, debt, donor_spent)
            primary = objective(next_debt, contract.debt)
        elif policy == 'max_weight':
            # Known debt-weighted compensation control, not a new algorithm.
            gain = sum((d * min(d, max(q-b, F(0))) for d, q, b in zip(debt, action.quality, step.reference)), F(0))
            primary = (-gain,)
        elif policy == 'rolling_maxmin':
            primary = tuple(-q for q in sorted(totals))
        elif policy == 'rolling_nash':
            primary = (-prod(totals),)
        else:
            primary = (-prod(action.quality),)
        return primary + (-prod(action.quality), action.resources, action.name)
    return min(allowed(step, contract, donor_spent), key=key)


def evaluate(path, schedule, contract):
    if len(path) != len(schedule) or not schedule:
        raise ValueError('nonempty complete path required')
    debt, spent = contract.debt, tuple(F(0) for _ in contract.debt)
    area, trace, completion = F(0), [], 0 if not any(debt) else None
    for t, (step, action) in enumerate(zip(schedule, path), 1):
        debt, spent, credits = feedback(step, action, contract, debt, spent)
        residual = objective(debt, contract.debt)
        area += residual[1]
        if completion is None and not any(debt):
            completion = t
        trace.append({'step': t, 'action': action.name, 'quality': action.quality,
                      'debt': debt, 'delivered_credit': credits, 'donor_spent': spent})
    means = tuple(sum((a.quality[i] for a in path), F(0))/len(path) for i in range(len(debt)))
    return {'terminal_max_fraction': objective(debt, contract.debt)[0],
            'terminal_sum_fraction': objective(debt, contract.debt)[1],
            'outstanding': debt, 'delivered_compensation': tuple(d0-d for d0, d in zip(contract.debt, debt)),
            'donor_spent': spent, 'all_recovered': not any(debt), 'recovery_step': completion,
            'area_normalized_debt': area, 'worst_post_quality': min(means),
            'mean_post_quality': sum(means)/len(means), 'post_means': means,
            'resources': sum((a.resources for a in path), F(0)), 'trace': trace}


def online(policy, schedule, contract, history=()):
    debt, spent = contract.debt, tuple(F(0) for _ in contract.debt)
    history, path = list(history), []
    for step in schedule:
        action = choose(policy, step, contract, debt, spent, history)
        path.append(action)
        debt, spent, _ = feedback(step, action, contract, debt, spent)
        history.append(action.quality)
    return evaluate(tuple(path), schedule, contract)


def oracle(schedule, contract):
    """Exhaustive FUTURE-KNOWN benchmark. Never an online performance claim."""
    candidates, feasible = [], 0
    for path in product(*(step.actions for step in schedule)):
        try:
            result = evaluate(path, schedule, contract)
        except ValueError:
            continue
        feasible += 1
        key = (result['terminal_max_fraction'], result['terminal_sum_fraction'],
               result['area_normalized_debt'], -prod(result['post_means']),
               result['resources'], tuple(a.name for a in path))
        candidates.append((key, result))
    if not candidates:
        raise ValueError('no protected feasible path')
    result = min(candidates, key=lambda pair: pair[0])[1]
    return {**result, 'feasible_paths': feasible}
