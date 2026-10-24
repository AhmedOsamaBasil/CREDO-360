"""Finite exact model checks plus analytical identity checks; no statistical trials."""
from fractions import Fraction as F
from itertools import product
from recovery_objective.core import Action, Contract, Step, ONLINE_POLICIES, online, oracle


def check_single_recipient():
    count = 0
    for horizon in range(1, 5):
        for gains in product((F(0), F(1, 2), F(1)), repeat=horizon):
            schedule = tuple(Step((3, 3), (Action('baseline', (3, 3)), Action('boost', (3+g, 2)))) for g in gains)
            for debt in (F(1, 2), F(1), F(2), F(3)):
                contract = Contract((debt, 0), (0, 1), (0, horizon))
                r = online('greedy_recovery', schedule, contract)
                # Independent closed-form theorem, not reusing the solver objective.
                expected = max(F(0), debt-sum(gains))
                assert r['outstanding'] == (expected, F(0))
                bound = oracle(schedule, contract)
                assert r['terminal_max_fraction'] == bound['terminal_max_fraction'] == expected/debt
                assert r['area_normalized_debt'] == bound['area_normalized_debt']
                count += 1
    return {'cases': count, 'exact_closed_form_and_oracle_agreement': True,
            'scope': 'one recipient, exogenous independent action sets, nonbinding total donor budget'}


def check_multi_recipient():
    count = 0
    relationships = {p: {'strictly_above_terminal_oracle': 0, 'equal_terminal_oracle': 0} for p in ONLINE_POLICIES}
    for d1, d2, gain, recipient in product((1, 2), (1, 2), (F(1, 2), F(1), F(3, 2)), (0, 1)):
        base = Action('baseline', (3, 3, 3))
        first, second = Action('help_first', (3+gain, 3, 2)), Action('help_second', (3, 4, 2))
        schedule = (Step((3, 3, 3), (base, first, second)),
                    Step((3, 3, 3), (base, first if recipient == 0 else second)))
        contract = Contract((d1, d2, 0), (0, 0, 1), (0, 0, 2))
        optimal = oracle(schedule, contract)
        for policy in ONLINE_POLICIES:
            r = online(policy, schedule, contract, ((3, 3, 3),)*23)
            a, b = (r['terminal_max_fraction'], r['terminal_sum_fraction']), (optimal['terminal_max_fraction'], optimal['terminal_sum_fraction'])
            assert a >= b
            relationships[policy]['strictly_above_terminal_oracle' if a > b else 'equal_terminal_oracle'] += 1
            for initial, remaining, delivered in zip(contract.debt, r['outstanding'], r['delivered_compensation']):
                assert remaining >= 0 and remaining+delivered == initial
            assert all(x <= budget for x, budget in zip(r['donor_spent'], contract.donor_total_allowance))
        count += 1
    return {'cases': count, 'exact_conservation_and_protection': True, 'policy_relationships': relationships,
            'scope': 'constructed two-step, two-recipient opportunity family; not a probability distribution'}


def run_checks():
    return {'single_recipient': check_single_recipient(), 'multi_recipient': check_multi_recipient()}
