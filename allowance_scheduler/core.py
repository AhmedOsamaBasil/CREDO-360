"""Commit to a causal policy mixture; never branch on a latent future label."""
from dataclasses import dataclass
from fractions import Fraction as F
from itertools import product
from math import lcm, prod
from recovery_objective.core import allowed, feedback, evaluate, choose, oracle
from allowance_scheduler.game import minimax


def observation(step):
    return (step.reference, step.resource_cap,
            tuple(sorted((a.name, a.quality, a.resources) for a in step.actions)))


@dataclass
class Policy:
    mapping: dict
    paths: tuple


def feasible_paths(schedule, contract):
    result = []
    for path in product(*(tuple(sorted(step.actions, key=lambda a: a.name)) for step in schedule)):
        try: evaluate(path, schedule, contract)
        except ValueError: continue
        result.append(path)
    return tuple(result)


def causal_policies(scenarios, contract):
    scenarios = tuple(tuple(s) for s in scenarios)
    if not scenarios or not scenarios[0] or any(len(s) != len(scenarios[0]) for s in scenarios):
        raise ValueError('nonempty equal-horizon scenarios required')
    if any(len(step.reference) != len(contract.debt) for s in scenarios for step in s):
        raise ValueError('scenario and contract dimensions must agree')
    paths = tuple(feasible_paths(s, contract) for s in scenarios)
    if prod(map(len, paths)) > 200000:
        raise ValueError('enumeration limit; no scalability claim')
    policies = []
    for combination in product(*paths):
        mapping, consistent = {}, True
        for scenario, path in zip(scenarios, combination):
            prefix = ()
            for step, action in zip(scenario, path):
                prefix += (observation(step),)
                if prefix in mapping and mapping[prefix] != action.name:
                    consistent = False; break
                mapping[prefix] = action.name
            if not consistent: break
        if consistent: policies.append(Policy(mapping, combination))
    if not policies: raise AssertionError('reference actions should define a causal policy')
    return tuple(policies)


def plan(scenarios, contract):
    scenarios = tuple(tuple(s) for s in scenarios)
    policies = causal_policies(scenarios, contract)
    benchmarks = tuple(oracle(s, contract)['terminal_max_fraction'] for s in scenarios)
    outcomes = tuple(tuple(evaluate(path, s, contract) for path, s in zip(p.paths, scenarios)) for p in policies)
    losses = tuple(tuple(r['terminal_max_fraction'] for r in row) for row in outcomes)
    regrets = tuple(tuple(loss-b for loss, b in zip(row, benchmarks)) for row in losses)
    assert all(x >= 0 for row in regrets for x in row)
    solution = minimax(regrets)
    deterministic = min(range(len(policies)), key=lambda i: (max(regrets[i]), sum(regrets[i]), i))
    absolute = min(range(len(policies)), key=lambda i: (max(losses[i]), sum(losses[i]), i))
    return {'scenarios': scenarios, 'contract': contract, 'policies': policies,
            'benchmarks': benchmarks, 'outcomes': outcomes, 'losses': losses, 'regrets': regrets,
            'solution': solution, 'deterministic_regret': deterministic, 'absolute_minimax': absolute}


def sample_policy(weights, rng):
    """Sample ONCE per episode, independently of the unknown future scenario."""
    if not weights or any(w < 0 for w in weights) or sum(weights) != 1:
        raise ValueError('normalized nonnegative weights required')
    denominator = lcm(*(w.denominator for w in weights))
    draw = rng.randrange(denominator)
    for i, weight in enumerate(weights):
        count = int(weight*denominator)
        if draw < count: return i
        draw -= count
    raise AssertionError('invalid exact sampling partition')


class Controller:
    """Analytical current-observation executor with persistent breach fallback.

    Perfect current utilities are part of this idealized interface. Future
    realized steps/scenario IDs are never passed to advance(). The sampled
    policy is retained; re-solving a new game each period is NOT this algorithm.
    """
    def __init__(self, policy, contract):
        self.mapping, self.contract = dict(policy.mapping), contract
        self.debt, self.spent = contract.debt, tuple(F(0) for _ in contract.debt)
        self.prefix, self.history = (), []
        self.model_breach, self.records = False, []

    def advance(self, current):
        self.prefix += (observation(current),)
        name = self.mapping.get(self.prefix)
        legal = allowed(current, self.contract, self.spent)
        action = next((a for a in legal if a.name == name), None)
        if action is None: self.model_breach = True
        if self.model_breach:
            action = choose('stateless_nash', current, self.contract, self.debt, self.spent, self.history)
        self.debt, self.spent, credit = feedback(current, action, self.contract, self.debt, self.spent)
        self.history.append(action.quality)
        self.records.append({'action': action.name, 'debt': self.debt, 'donor_spent': self.spent,
                             'delivered_credit': credit, 'model_breach': self.model_breach})
        return action


def execute(policy, contract, schedule):
    controller = Controller(policy, contract)
    path = tuple(controller.advance(step) for step in schedule)
    return {**evaluate(path, schedule, contract), 'model_breach': controller.model_breach}


def expected_summary(planned, weights):
    fields = ('terminal_max_fraction', 'terminal_sum_fraction', 'area_normalized_debt',
              'worst_post_quality', 'mean_post_quality', 'resources')
    summaries = []
    for j, _ in enumerate(planned['scenarios']):
        row = {field: sum((w*planned['outcomes'][i][j][field] for i, w in enumerate(weights)), F(0)) for field in fields}
        row['regret'] = row['terminal_max_fraction']-planned['benchmarks'][j]
        row['all_recovered_probability'] = sum((w for i, w in enumerate(weights) if planned['outcomes'][i][j]['all_recovered']), F(0))
        row['donor_spent'] = tuple(sum((w*planned['outcomes'][i][j]['donor_spent'][u] for i, w in enumerate(weights)), F(0)) for u in range(len(planned['contract'].debt)))
        summaries.append(row)
    return tuple(summaries)
