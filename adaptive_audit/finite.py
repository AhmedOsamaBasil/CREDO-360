"""Small exact finite games; integer rewards and deterministic causal policies."""
from functools import lru_cache
from itertools import product


def values(rewards, costs, reserve, signals, reveal_before=False):
    """Observe a signal and the selected reward AFTER committing an action.

    Complete scenarios can be temporally coupled. Belief subsets retain that
    coupling instead of incorrectly replacing them by rectangular marginals.
    reveal_before is a deliberately different information model used in tests.
    """
    n = len(rewards)
    horizon = len(costs)
    actions = len(costs[0])
    if n == 0 or reserve < 0 or horizon == 0:
        raise ValueError("Nonempty finite game and nonnegative reserve required")
    if any(len(row) != actions or any(c < 0 for c in row) for row in costs):
        raise ValueError("Invalid action costs")
    if len(signals) != n or any(len(s) != horizon for s in signals):
        raise ValueError("Invalid observation table")
    if any(len(s) != horizon or any(len(r) != actions for r in s) for s in rewards):
        raise ValueError("Invalid reward table")

    @lru_cache(None)
    def solve(t, left, possible):
        if t == horizon:
            return 0
        groups = {}
        for s in possible:
            groups.setdefault(signals[s][t] if reveal_before else None, []).append(s)
        return min(choose(t, left, tuple(group)) for group in groups.values())

    def choose(t, left, possible):
        scores = []
        for a in range(actions):
            if costs[t][a] > left:
                continue
            groups = {}
            for s in possible:
                groups.setdefault((signals[s][t], rewards[s][t][a]), []).append(s)
            scores.append(min(reward + solve(t+1, left-costs[t][a], tuple(group))
                              for (_, reward), group in groups.items()))
        if not scores:
            raise ValueError("No feasible continuation")
        return max(scores)

    paths = [p for p in product(range(actions), repeat=horizon)
             if sum(costs[t][a] for t, a in enumerate(p)) <= reserve]
    if not paths:
        raise ValueError("No feasible complete path")
    totals = [[sum(rewards[s][t][a] for t, a in enumerate(p)) for s in range(n)] for p in paths]
    return {"open_loop": max(min(row) for row in totals),
            "causal": solve(0, reserve, tuple(range(n))),
            "clairvoyant": min(max(row[s] for row in totals) for s in range(n)),
            "resource_paths": len(paths)}


def enumerate_two_stage(rewards, costs, reserve, signals):
    """Independent exhaustive enumeration of second-stage observation policies."""
    if len(costs) != 2:
        raise ValueError("Two stages only")
    scores = []
    for first in range(len(costs[0])):
        left = reserve-costs[0][first]
        second = [a for a, c in enumerate(costs[1]) if c <= left]
        if not second:
            continue
        observations = sorted({(signals[s][0], rewards[s][0][first]) for s in range(len(rewards))})
        for choices in product(second, repeat=len(observations)):
            policy = dict(zip(observations, choices))
            scores.append(min(rewards[s][0][first] + rewards[s][1][policy[signals[s][0], rewards[s][0][first]]]
                              for s in range(len(rewards))))
    if not scores:
        raise ValueError("No feasible policy")
    return max(scores)


def analytic_cases():
    coupled = [[[0, 0], [1, 0]], [[0, 0], [0, 1]]]
    costs = [[0, 0], [0, 0]]
    cases = {
        "coupled_informative_past": values(coupled, costs, 0, [[0, 0], [1, 1]]),
        "coupled_uninformative_past": values(coupled, costs, 0, [[0, 0], [0, 0]]),
        "current_outcome_after_commit": values([[[1, 0]], [[0, 1]]], [[0, 0]], 0, [[0], [1]]),
        "current_outcome_before_commit": values([[[1, 0]], [[0, 1]]], [[0, 0]], 0, [[0], [1]], True),
    }
    rectangle_checks = scenario_checks = 0
    for bits in product((0, 1), repeat=8):
        # Two possible states per stage, independently selectable at each stage.
        table = [[list(bits[t*4+e*2:t*4+e*2+2]) for e in (0, 1)] for t in (0, 1)]
        states = list(product((0, 1), repeat=2))
        rewards = [[table[t][es[t]] for t in (0, 1)] for es in states]
        costs = [[0, 1], [0, 1]]
        result = values(rewards, costs, 1, states)
        brute = enumerate_two_stage(rewards, costs, 1, states)
        if result['open_loop'] != result['causal'] or brute != result['causal']:
            raise ValueError("Rectangular information theorem mismatch")
        rectangle_checks += 1
        # Also audit coupled scenario subsets, where equality need not hold.
        for subset in ((0, 3), (1, 2)):
            rs = [rewards[i] for i in subset]; ss = [states[i] for i in subset]
            value = values(rs, costs, 1, ss)
            if value['causal'] != enumerate_two_stage(rs, costs, 1, ss):
                raise ValueError("Independent causal policy enumeration mismatch")
            if not value['open_loop'] <= value['causal'] <= value['clairvoyant']:
                raise ValueError("Information ordering failure")
            scenario_checks += 1
    return {'cases': cases, 'rectangular_exact_checks': rectangle_checks,
            'coupled_exact_checks': scenario_checks}
